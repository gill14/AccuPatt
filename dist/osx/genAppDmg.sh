#!/bin/bash
#Bash file to turn AccuPatt app container into a .dmg for distribution

#Set location
SCRIPT="$BASH_SOURCE"
SCRIPTPATH="$(dirname "$SCRIPT")"

#Remove old files
rm "$SCRIPTPATH"/*.dmg

#Create dmg
hdiutil create -volname AccuPatt -srcfolder "$SCRIPTPATH"/dist -ov -format UDZO "$SCRIPTPATH"/AccuPatt.dmg

#Remove app file
rm -r "$SCRIPTPATH"/dist/AccuPatt.app

#Remove build dir
rm -r "$SCRIPTPATH"/build
