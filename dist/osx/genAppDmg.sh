#!/bin/bash
#Bash file to turn AccuPatt app container into a .dmg for distribution

#Set location
SCRIPT="$BASH_SOURCE"
SCRIPTPATH="$(dirname "$SCRIPT")"
EULA="$SCRIPTPATH/../../resources/documents/AccuPatt_EULA.txt"

#Remove old files
rm "$SCRIPTPATH"/*.dmg

#Create dmg
hdiutil create -volname AccuPatt -srcfolder "$SCRIPTPATH"/dist -ov -format UDZO "$SCRIPTPATH"/AccuPatt.dmg

# Attach the EULA so macOS shows Agree/Disagree before mounting. Required by
# the OceanDirect API Terms (1.2(b)). Non-fatal: a release can still be cut if
# this fails, but the DMG then ships without the gate, so the warning is loud.
if [ -f "$EULA" ]; then
    python3 "$SCRIPTPATH"/attach_dmg_license.py "$SCRIPTPATH"/AccuPatt.dmg "$EULA" \
        || echo "WARNING: could not attach EULA to DMG — do not ship this image"
else
    echo "WARNING: $EULA not found — DMG has no license agreement"
fi

#Remove app file
rm -r "$SCRIPTPATH"/dist/AccuPatt.app

#Remove build dir
rm -r "$SCRIPTPATH"/build
