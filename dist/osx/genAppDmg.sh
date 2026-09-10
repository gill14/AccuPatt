#!/bin/bash
#Bash file to turn AccuPatt app container into a .dmg for distribution

#Set location
SCRIPT="$BASH_SOURCE"
SCRIPTPATH="$(dirname "$SCRIPT")"
APP="$SCRIPTPATH/dist/AccuPatt.app"
EULA="$SCRIPTPATH/../../resources/documents/AccuPatt_EULA.txt"
DMG="$SCRIPTPATH/AccuPatt.dmg"

#Remove old files
rm -f "$SCRIPTPATH"/*.dmg

# Build the styled, "drag AccuPatt to Applications" installer image: sets up
# a background image, Finder icon layout, and a fresh Applications symlink
# (see style_dmg.sh -- no committed alias file to rot across machines).
sh "$SCRIPTPATH/style_dmg.sh" "$APP" "$DMG"

# Attach the EULA so macOS shows Agree/Disagree before mounting. Required by
# the OceanDirect API Terms (1.2(b)). Non-fatal: a release can still be cut if
# this fails, but the DMG then ships without the gate, so the warning is loud.
if [ -f "$EULA" ]; then
    python3 "$SCRIPTPATH"/attach_dmg_license.py "$DMG" "$EULA" \
        || echo "WARNING: could not attach EULA to DMG — do not ship this image"
else
    echo "WARNING: $EULA not found — DMG has no license agreement"
fi

#Remove app file
rm -r "$APP"

#Remove build dir
rm -rf "$SCRIPTPATH"/build
