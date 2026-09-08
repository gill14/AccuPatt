"""
This script will generate the .exe file with dependents in same dir

Usage:
    AS NEEDED: poetry install --with dev-win
    poetry run python bundle_win.py
"""

import subprocess
import os
import sys
import shutil
import PyInstaller.__main__
import accupatt.config as cfg

# Update Setup Script Version
VERSION = f'{cfg.VERSION_MAJOR}.{cfg.VERSION_MINOR}.{cfg.VERSION_RELEASE}'
with open("./dist/win/innoSetupScript.iss", "r", encoding="utf-8") as file:
    data = file.readlines()
data[4] = f"#define MyAppVersion \"{VERSION}\"\n"
with open("./dist/win/innoSetupScript.iss", "w", encoding="utf-8") as file:
    file.writelines(data)

# The OceanDirect SDK is staged locally, not committed (tools/sync_oceandirect.py),
# and the EULA must ship for the Inno Setup LicenseFile page. Fail loudly rather
# than cutting a release that silently lacks either.
for required, remedy in [
    ('./oceandirect/lib/OceanDirect.dll',
     'Install the OceanDirect SDK, then: poetry run python tools/sync_oceandirect.py'),
    ('./resources/documents/AccuPatt_EULA.txt',
     'The AccuPatt EULA is missing from resources/documents.'),
]:
    if not os.path.isfile(required):
        sys.exit(f'error: {required} not found.\n  {remedy}')

if sys.platform == 'win32':
    
    shutil.copyfile("./user_manual/accupatt_2_user_manual.pdf","./resources/documents/accupatt_2_user_manual.pdf")

    PyInstaller.__main__.run([
        './accupatt/__main__.py',
        '--name=AccuPatt',
        '--windowed', # change to --nowindowed for console troubleshooting
        '--exclude-module=tkinter',
        '--exclude-module=py2app',
        '--exclude-module=pyobjc-framework-ImageCaptureCore',
        '--hidden-import=matplotlib.backends.backend_svg',
        f'--additional-hooks-dir=./hooks',
        f'--add-data=../../resources{os.pathsep}resources',
        f'--add-data=../../oceandirect/lib{os.pathsep}.',
        '--icon=../../resources/accupatt_logo.ico',
        '--distpath=./dist/win/dist',
        '--specpath=./dist/win',
        '--workpath=./dist/win/build'
        ])
    
    subprocess.call(r'"./dist/win/createInstaller.bat"')