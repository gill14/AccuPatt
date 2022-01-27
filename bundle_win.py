import os
import sys
import PyInstaller.__main__

if sys.platform == 'win32':
    PyInstaller.__main__.run([
        './accupatt/__main__.py',
        '--name=AccuPatt',
        '--windowed',
        f'--add-data=./resources{os.pathsep}resources'
        ])