#!/bin/bash
#Bash file to turn AccuStain jar into app and dmg

#Set location
SCRIPT="$BASH_SOURCE"
#echo "SCRIPT = $SCRIPT"
SCRIPTPATH="$(dirname "$SCRIPT")"
#echo "SCRIPTPATH = $SCRIPTPATH"

#Remove old files
rm "$SCRIPTPATH"/*.dmg

#Create dmg
hdiutil create -volname AccuPatt -srcfolder "$SCRIPTPATH"/dist -ov -format UDZO "$SCRIPTPATH"/AccuPatt.dmg

#Remove app file
rm -r "$SCRIPTPATH"/dist/AccuPatt.app

#Remove build dir
rm -r "$SCRIPTPATH"/build
