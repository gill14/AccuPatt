@echo off
SET mypath=%~dp0
ECHO "ZIPPING..."
SET ISCC="C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
SET ISCC_FILE="%mypath%innoSetupScript.iss"
%ISCC% %ISCC_FILE%
ECHO "REMOVING DIST/BUILD DIRS..."
RD /S /Q "%mypath%dist", "%mypath%build"
DEL "%mypath%AccuPatt.spec"
ECHO "DONE!"