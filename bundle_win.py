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

if sys.platform == 'win32':
    
    shutil.copyfile("./user_manual/accupatt_2_user_manual.pdf","./resources/documents/accupatt_2_user_manual.pdf")

    PyInstaller.__main__.run([
        './accupatt/__main__.py',
        '--name=AccuPatt',
        '--windowed', # change to --nowindowed for console troubleshooting
        '--exclude-module=tkinter',
        '--exclude-module=py2app',
        '--hidden-import=matplotlib.backends.backend_svg',
        '--hidden-import=libusb',
        '--hidden-import=pyusb',
        '--hidden-import=seabreeze.pyseabreeze',
        f'--additional-hooks-dir=./hooks',
        f'--add-data=../../resources{os.pathsep}resources',
        #'--add-data=C:/Windows/System32/libusb-1.0.dll;.',
        f'--add-data=../../oceandirect/lib{os.pathsep}.',
        '--icon=../../resources/accupatt_logo.ico',
        '--distpath=./dist/win/dist',
        '--specpath=./dist/win',
        '--workpath=./dist/win/build'
        ])
    
    subprocess.call(r'"./dist/win/createInstaller.bat"')