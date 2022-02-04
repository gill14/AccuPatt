"""
This script will generate the a .exe file with dependents in same dir

Usage:
    poetry run python bundle_win.py
"""

import subprocess
import os
import sys
import PyInstaller.__main__

if sys.platform == 'win32':
    
    PyInstaller.__main__.run([
        './accupatt/__main__.py',
        '--name=AccuPatt',
        '--windowed',
        '--exclude-module=tkinter',
        f'--add-data=../../resources{os.pathsep}resources',
        '--icon=../../resources/illini.ico',
        '--distpath=./dist/win/dist',
        '--specpath=./dist/win',
        '--workpath=./dist/win/build'
        ])
    
    subprocess.call(r'"./dist/win/createInstaller.bat"')