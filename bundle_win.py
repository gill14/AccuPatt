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
        # sdk_properties.py (vendored, not ours) locates the DLL as
        # os.path.dirname(__file__) + "/lib/OceanDirect.dll" -- i.e. it
        # expects lib/ nested under the oceandirect package directory.
        # PyInstaller's --add-data destination is taken literally, so it
        # must match that nesting; a destination of "." previously flattened
        # the DLL to the bundle root, where the SDK could never find it.
        f'--add-data=../../oceandirect/lib{os.pathsep}oceandirect/lib',
        '--icon=../../resources/accupatt_logo.ico',
        '--distpath=./dist/win/dist',
        '--specpath=./dist/win',
        '--workpath=./dist/win/build'
        ])

    # Confirm PyInstaller actually placed the DLL where sdk_properties.py
    # will look for it at runtime. This has silently broken before (a
    # destination of "." landed it at the bundle root instead) with no
    # error at build time -- only a SpectrometerError once installed.
    bundled_dll = './dist/win/dist/AccuPatt/_internal/oceandirect/lib/OceanDirect.dll'
    if not os.path.isfile(bundled_dll):
        sys.exit(
            f'error: {bundled_dll} not found after build.\n'
            '  OceanDirect.dll was not bundled where the SDK expects it '
            '(oceandirect/lib/ next to the oceandirect package) -- the '
            'spectrometer will fail to load in the installed app.'
        )

    subprocess.call(r'"./dist/win/createInstaller.bat"')