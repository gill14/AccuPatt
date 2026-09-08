#!/bin/bash
# Codesigns an AccuPatt.app bundle with a Developer ID Application identity and
# Hardened Runtime, so it can pass notarization.
#
# Usage:
#   CODESIGN_IDENTITY="Developer ID Application: Your Name (TEAMID)" \
#       ./dist/osx/sign_mac.sh ./dist/osx/dist/AccuPatt.app
#
# Find your identity string with:
#   security find-identity -v -p codesigning

set -euo pipefail

APP_PATH="${1:?Usage: sign_mac.sh /path/to/AccuPatt.app}"
SCRIPT="$BASH_SOURCE"
SCRIPTPATH="$(cd "$(dirname "$SCRIPT")" && pwd)"
ENTITLEMENTS="$SCRIPTPATH/entitlements.plist"

if [ -z "${CODESIGN_IDENTITY:-}" ]; then
    echo "error: CODESIGN_IDENTITY is not set" >&2
    exit 1
fi

if [ ! -d "$APP_PATH" ]; then
    echo "error: $APP_PATH not found" >&2
    exit 1
fi

echo "Signing $APP_PATH with identity: $CODESIGN_IDENTITY"

# py2app bundles nested Mach-O binaries (dylibs, .so extension modules,
# vendored SDK libs like liboceandirect.dylib) that `codesign --deep` does not
# always reach reliably. Sign every Mach-O file bottom-up first, then sign the
# app bundle itself last.
find "$APP_PATH" \
    \( -name "*.dylib" -o -name "*.so" \) \
    -type f -print0 |
while IFS= read -r -d '' lib; do
    codesign --force --timestamp --options runtime \
        --entitlements "$ENTITLEMENTS" \
        --sign "$CODESIGN_IDENTITY" \
        "$lib"
done

# Sign any embedded executables inside Contents/MacOS and Contents/Resources
find "$APP_PATH/Contents/MacOS" "$APP_PATH/Contents/Resources" \
    -type f -perm -111 ! -name "*.dylib" ! -name "*.so" -print0 2>/dev/null |
while IFS= read -r -d '' bin; do
    codesign --force --timestamp --options runtime \
        --entitlements "$ENTITLEMENTS" \
        --sign "$CODESIGN_IDENTITY" \
        "$bin"
done

# Finally sign the app bundle itself
codesign --force --timestamp --options runtime \
    --entitlements "$ENTITLEMENTS" \
    --sign "$CODESIGN_IDENTITY" \
    "$APP_PATH"

echo "Verifying signature..."
codesign --verify --deep --strict --verbose=2 "$APP_PATH"
spctl --assess --type execute --verbose=4 "$APP_PATH" || true

echo "Done."
