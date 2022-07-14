"""
This script will generate the a .app file

Usage:
    poetry run python bundle_mac.py py2app
    poetry run python bundle_mac.py py2app -A
"""

import subprocess
import sys
from setuptools import setup
import accupatt.config as cfg

VERSION = f'{cfg.VERSION_MAJOR}.{cfg.VERSION_MINOR}.{cfg.VERSION_RELEASE}'

OPTIONS = {
    'iconfile':'./resources/illini.icns',
    'resources':['./resources'],
    'bdist_base':'./dist/osx/build',
    'dist_dir':'./dist/osx/dist',
    'plist': {'CFBundleShortVersionString':VERSION,
              'CFBundleIdentifier':'edu.illinois.accupatt',},
    'excludes': ["PyInstaller"],
}

if sys.platform == 'darwin':
    setup(
        setup_requires=['py2app'],
        app=['./accupatt/__main__.py'],
        options={'py2app': OPTIONS},
        name='AccuPatt',
        version=VERSION,
    )
    
    subprocess.call(['sh','./dist/osx/genAppDmg.sh'])
