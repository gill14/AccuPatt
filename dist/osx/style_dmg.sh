#!/bin/bash
# Assembles a styled, "drag to Applications" installer .dmg from a built
# AccuPatt.app: background image, Finder icon-view layout, and a fresh
# Applications symlink (created here at build time -- not a committed alias
# file, which silently rots across machines since it embeds volume/inode
# references from whoever last generated it).
#
# Usage:
#   ./dist/osx/style_dmg.sh /path/to/AccuPatt.app /path/to/output/AccuPatt.dmg

set -euo pipefail

APP_PATH="${1:?Usage: style_dmg.sh /path/to/AccuPatt.app /path/to/output.dmg}"
OUT_DMG="${2:?Usage: style_dmg.sh /path/to/AccuPatt.app /path/to/output.dmg}"
SCRIPTPATH="$(cd "$(dirname "$BASH_SOURCE")" && pwd)"
BACKGROUND="$SCRIPTPATH/dmg_background.png"
VOLNAME="AccuPatt"
MOUNTPOINT="/Volumes/$VOLNAME"

if [ ! -d "$APP_PATH" ]; then
    echo "error: $APP_PATH not found" >&2
    exit 1
fi
if [ ! -f "$BACKGROUND" ]; then
    echo "error: $BACKGROUND not found (regenerate with make_dmg_background.py)" >&2
    exit 1
fi

# A leftover mount from an earlier failed/interrupted build would shadow
# ours (macOS mounts a same-named volume as "AccuPatt 1").
if [ -d "$MOUNTPOINT" ]; then
    hdiutil detach "$MOUNTPOINT" -force >/dev/null 2>&1 || true
fi

WORK_DIR="$(mktemp -d)"
trap 'hdiutil detach "$MOUNTPOINT" -force >/dev/null 2>&1 || true; rm -rf "$WORK_DIR"' EXIT

RW_DMG="$WORK_DIR/rw.dmg"
SRC_DIR="$WORK_DIR/src"
mkdir "$SRC_DIR"
cp -R "$APP_PATH" "$SRC_DIR/"

# Pad generously: the RW image needs headroom for the .app plus the
# background image and .DS_Store Finder writes during styling.
SIZE_MB=$(($(du -sm "$SRC_DIR" | cut -f1) + 100))

echo "Creating $((SIZE_MB))MB read-write image..."
hdiutil create -volname "$VOLNAME" -srcfolder "$SRC_DIR" -fs HFS+ \
    -format UDRW -size "${SIZE_MB}m" -ov "$RW_DMG"

hdiutil attach "$RW_DMG" -readwrite -noverify -noautoopen -mountpoint "$MOUNTPOINT"

ln -s /Applications "$MOUNTPOINT/Applications"
mkdir "$MOUNTPOINT/.background"
cp "$BACKGROUND" "$MOUNTPOINT/.background/background.png"

# Finder needs a moment to notice the freshly-mounted volume before it will
# resolve `tell disk "..."`.
sleep 2

# This follows the structure of create-dmg's proven template.applescript
# (github.com/create-dmg/create-dmg/blob/master/support/template.applescript)
# rather than the many "fancy dmg" blog-post variants, which no longer fully
# work on current macOS, plus one thing beyond even that template: the whole
# styling pass is applied TWICE. On this system the first pass alone reliably
# leaves icon size at its default and the background picture unset -- not a
# timing issue fixable with longer delays, confirmed by checking the actual
# final output file directly (not a live intermediate Finder session, which
# reads back unreliably regardless of what's really been saved). A second
# full open/style/close pass is what actually makes it stick. This matches a
# workaround reported independently by others for this same Finder AppleScript
# flakiness (macscripter.net/t/cant-set-background-image-for-dmg-image-file).
#
# The background picture is set via an absolute POSIX file reference, not
# the classic HFS colon-path (`file ".background:background.png"`) most
# older tutorials use -- that legacy form fails to resolve silently (no
# script error, the picture just never appears) on current macOS.
osascript <<OSA
on applyStyling()
    tell application "Finder"
        tell disk "$VOLNAME"
            open

            -- The window is wider than the 660x400 background/icon layout
            -- (both are content-pane-relative, not window-relative): modern
            -- macOS no longer honors \`toolbar visible: false\` for hiding
            -- the sidebar (a real OS limitation, not fixable from here), so
            -- the sidebar permanently eats into the window's total width.
            -- Extra width here is just empty space to the right of the two
            -- icons, not a layout change.
            set theXOrigin to 400
            set theYOrigin to 100
            set theWidth to 1000
            set theHeight to 400
            set theBottomRightX to (theXOrigin + theWidth)
            set theBottomRightY to (theYOrigin + theHeight)

            tell container window
                set current view to icon view
                set toolbar visible to false
                set statusbar visible to false
                set the bounds to {theXOrigin, theYOrigin, theBottomRightX, theBottomRightY}
            end tell

            set opts to the icon view options of container window
            tell opts
                set icon size to 128
                set arrangement to not arranged
                set background picture to POSIX file "$MOUNTPOINT/.background/background.png"
            end tell

            set position of item "AccuPatt.app" of container window to {165, 210}
            set position of item "Applications" of container window to {495, 210}

            close
        end tell
    end tell
end applyStyling

on run
    my applyStyling()
    delay 1
    my applyStyling()

    tell application "Finder"
        tell disk "$VOLNAME"
            open
            -- Force saving of the size
            delay 1

            set theXOrigin to 400
            set theYOrigin to 100
            set theBottomRightX to 1400
            set theBottomRightY to 500

            tell container window
                set statusbar visible to false
                set the bounds to {theXOrigin, theYOrigin, theBottomRightX - 10, theBottomRightY - 10}
            end tell
        end tell

        delay 1

        tell disk "$VOLNAME"
            tell container window
                set statusbar visible to false
                set the bounds to {theXOrigin, theYOrigin, theBottomRightX, theBottomRightY}
            end tell
        end tell

        -- give the finder some time to write the .DS_Store file
        delay 3

        set dsStore to quoted form of ("$MOUNTPOINT" & "/.DS_Store")
        set waitTime to 0
        repeat
            if (do shell script "[ -f " & dsStore & " ]; echo $?") = "0" then exit repeat
            delay 1
            set waitTime to waitTime + 1
            if waitTime > 30 then exit repeat
        end repeat
        log "waited " & waitTime & " seconds for .DS_Store to be created."
    end tell
end run
OSA

chmod -Rf go-w "$MOUNTPOINT" || true
sync
hdiutil detach "$MOUNTPOINT"

echo "Converting to compressed image..."
rm -f "$OUT_DMG"
hdiutil convert "$RW_DMG" -format UDZO -ov -o "$OUT_DMG"

echo "Wrote $OUT_DMG"
