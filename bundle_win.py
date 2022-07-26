"""
This script will generate the .exe file with dependents in same dir

Usage:
    poetry run python bundle_win.py
"""

import subprocess
import os
import sys
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
    
    PyInstaller.__main__.run([
        './accupatt/__main__.py',
        '--name=AccuPatt',
        '--windowed', # change to --nowindowed for console troubleshooting
        '--exclude-module=tkinter',
        '--hidden-import=matplotlib.backends.backend_svg',
        f'--additional-hooks-dir=./hooks',
        f'--add-data=../../resources{os.pathsep}resources',
        '--icon=../../resources/illini.ico',
        '--distpath=./dist/win/dist',
        '--specpath=./dist/win',
        '--workpath=./dist/win/build'
        ])
    
    subprocess.call(r'"./dist/win/createInstaller.bat"')