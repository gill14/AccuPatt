#!/bin/bash
# Submits an AccuPatt.dmg to Apple's notary service, waits for the result, and
# staples the notarization ticket so Gatekeeper can verify it offline.
#
# One-time setup (run yourself, not via this script):
#   xcrun notarytool store-credentials "accupatt-notary" \
#       --apple-id "you@example.com" --team-id "TEAMID"
#   (it will prompt for an app-specific password from appleid.apple.com)
#
# Usage:
#   NOTARY_PROFILE="accupatt-notary" ./dist/osx/notarize_mac.sh ./dist/osx/AccuPatt.dmg

set -euo pipefail

DMG_PATH="${1:?Usage: notarize_mac.sh /path/to/AccuPatt.dmg}"

if [ -z "${NOTARY_PROFILE:-}" ]; then
    echo "error: NOTARY_PROFILE is not set (see header of this script for setup)" >&2
    exit 1
fi

if [ ! -f "$DMG_PATH" ]; then
    echo "error: $DMG_PATH not found" >&2
    exit 1
fi

echo "Submitting $DMG_PATH for notarization (this can take a few minutes)..."
xcrun notarytool submit "$DMG_PATH" --keychain-profile "$NOTARY_PROFILE" --wait

echo "Stapling notarization ticket..."
xcrun stapler staple "$DMG_PATH"

echo "Verifying..."
spctl --assess --type open --context context:primary-signature --verbose=4 "$DMG_PATH"

echo "Done. $DMG_PATH is signed, notarized, and stapled."
