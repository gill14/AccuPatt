"""
This script will generate the a .app file

Usage:
    python bundle_mac.py py2app
    python bundle_mac.py py2app -A
"""

import subprocess
import sys
from setuptools import setup

DATA_FILES = [('resources',['resources/AgAircraftData.xlsx','resources/edit-alt-512.webp','resources/editCardList.ui','resources/editSpectrometer.ui','resources/editSpreadFactors.ui','resources/editStringDrive.ui','resources/editThreshold.ui','resources/loadCards.ui','resources/mainWindow.ui','resources/passManager.ui','resources/readString.ui','resources/refresh.png','resources/seriesInfo.ui','resources/schema.sql','resources/illini.icns'])]
#DATA_FILES = [('resources',['resources'])]

OPTIONS = {
    'iconfile':'./resources/illini.icns',
    'bdist_base':'./dist/osx/build',
    'dist_dir':'./dist/osx/dist',
    'plist': {'CFBundleShortVersionString':'2.0.1',
              'CFBundleIdentifier':'edu.illinois.accupatt',}
}

if sys.platform == 'darwin':
    extra_options = dict(
        setup_requires=['py2app'],
        app=['./accupatt/__main__.py'],
        options={'py2app': OPTIONS}
    )
    
    setup(
        name='AccuPatt',
        version='2.0.0',
        data_files=DATA_FILES,
        **extra_options
    )
    
    subprocess.call(['sh','./dist/osx/genAppDmg.sh'])
