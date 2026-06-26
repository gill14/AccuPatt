"""
This script will generate the a .app file

Usage:
    AS NEEDED: poetry install --with dev-osx
    poetry run python bundle_mac.py py2app
"""

import shutil
import subprocess
import sys
from setuptools import setup
from py2app.build_app import py2app as _Py2AppBase
import accupatt.config as cfg

VERSION = f'{cfg.VERSION_MAJOR}.{cfg.VERSION_MINOR}.{cfg.VERSION_RELEASE}'


class py2app(_Py2AppBase):
    def finalize_options(self):
        self.distribution.install_requires = []
        super().finalize_options()

OPTIONS = {
    'iconfile':'./resources/accupatt_logo.icns',
    'resources':['./resources'],
    'bdist_base':'./dist/osx/build',
    'dist_dir':'./dist/osx/dist',
    'plist': {'CFBundleShortVersionString':VERSION,
              'CFBundleIdentifier':'org.agaviation.accupatt',},
    'excludes': [
        "PyInstaller", "pycairo", "rlPyCairo",
        "pip", "setuptools", "py2app", "black", "blib2to3",
        "PyQt6.QtBluetooth", "PyQt6.QtDBus", "PyQt6.QtDesigner",
        "PyQt6.QtHelp", "PyQt6.QtMultimedia", "PyQt6.QtMultimediaWidgets",
        "PyQt6.QtNfc", "PyQt6.QtOpenGL", "PyQt6.QtOpenGLWidgets",
        "PyQt6.QtPdf", "PyQt6.QtPdfWidgets", "PyQt6.QtPositioning",
        "PyQt6.QtQml", "PyQt6.QtQuick", "PyQt6.QtQuick3D",
        "PyQt6.QtQuickWidgets", "PyQt6.QtRemoteObjects", "PyQt6.QtSensors",
        "PyQt6.QtSerialPort", "PyQt6.QtSpatialAudio", "PyQt6.QtSql",
        "PyQt6.QtStateMachine", "PyQt6.QtTest", "PyQt6.QtTextToSpeech",
        "PyQt6.QtWebChannel", "PyQt6.QtWebSockets",
    ],
    'includes': ["objc", "Foundation", "ImageCaptureCore"],
}

if sys.platform == 'darwin':
    shutil.rmtree('./dist/osx/dist/AccuPatt.app', ignore_errors=True)
    shutil.rmtree('./dist/osx/build', ignore_errors=True)

    subprocess.call(["cp","./user_manual/accupatt_2_user_manual.pdf","./resources/documents/accupatt_2_user_manual.pdf"])

    setup(
        app=['./accupatt/__main__.py'],
        options={'py2app': OPTIONS},
        name='AccuPatt',
        version=VERSION,
        cmdclass={'py2app': py2app},
    )
    
    subprocess.call(['sh','./dist/osx/genAppDmg.sh'])
