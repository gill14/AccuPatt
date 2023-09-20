"""
This script will generate the a .app file

Usage:
    AS NEEDED: poetry install --with dev-osx
    poetry run python bundle_mac.py py2app
"""

import subprocess
import sys
from setuptools import setup
import accupatt.config as cfg

VERSION = f'{cfg.VERSION_MAJOR}.{cfg.VERSION_MINOR}.{cfg.VERSION_RELEASE}'

OPTIONS = {
    'iconfile':'./resources/accupatt_logo.icns',
    'resources':['./resources'],
    'bdist_base':'./dist/osx/build',
    'dist_dir':'./dist/osx/dist',
    'plist': {'CFBundleShortVersionString':VERSION,
              'CFBundleIdentifier':'org.agaviation.accupatt',},
    'excludes': ["PyInstaller"],
    'includes': ["PyWavelets", "pywt", "imageio", "networkx"],
}

if sys.platform == 'darwin':
    
    subprocess.call(["cp","./user_manual/accupatt_2_user_manual.pdf","./resources/documents/accupatt_2_user_manual.pdf"])

    setup(
        setup_requires=['py2app'],
        app=['./accupatt/__main__.py'],
        options={'py2app': OPTIONS},
        name='AccuPatt',
        version=VERSION,
    )
    
    subprocess.call(['sh','./dist/osx/genAppDmg.sh'])
