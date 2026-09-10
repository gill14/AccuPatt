"""
This script will generate the a .app file

Usage:
    AS NEEDED: poetry install --with dev-osx
    poetry run python bundle_mac.py py2app

To also codesign (and optionally notarize) the build for distribution outside
the App Store, export these before running (see dist/osx/SIGNING.md):
    CODESIGN_IDENTITY="Developer ID Application: Your Name (TEAMID)"
    NOTARY_PROFILE="accupatt-notary"   # optional; skips notarization if unset
"""

import glob
import os
import shutil
import subprocess
import sys
from setuptools import setup
from py2app.build_app import py2app as _Py2AppBase
import accupatt.config as cfg

VERSION = f'{cfg.VERSION_MAJOR}.{cfg.VERSION_MINOR}.{cfg.VERSION_RELEASE}'


def _find_binaries(root):
    found = []
    for dirpath, _dirnames, filenames in os.walk(root):
        for name in filenames:
            if name.endswith(('.dylib', '.so')):
                found.append(os.path.join(dirpath, name))
    return found


def _repair_py2app_dylib_corruption(app_path):
    """Repair py2app's Frameworks-directory dylib merge corruption.

    When two site-packages wheels each vendor their own differently-built
    copy of a common dylib under the same filename (observed with
    libxcb.1.1.0.dylib, libfreetype.6.dylib, liblzma.5.dylib -- cv2, Pillow,
    and matplotlib all vendor several of these independently), py2app's
    Frameworks dedup can produce a file whose size matches one source copy
    but whose Mach-O load commands (segment offsets, LC_CODE_SIGNATURE) don't
    describe that file at all. The result fails strict codesign verification
    and, in the worst case tried, `codesign --remove-signature` itself
    ("internal error in Code Signing subsystem") -- the file is genuinely
    malformed, not just unsigned.

    py2app's dependency relinking (rewriting LC_ID_DYLIB / LC_LOAD_DYLIB to
    @executable_path/../Frameworks/...) is unaffected and still correct on
    these files, so the fix restores original file *content* from a
    same-name, same-size copy under site-packages, then reapplies the
    already-correct relinking captured from the corrupted file before
    overwriting it. A fresh codesign (done afterward by sign_mac.sh) then
    succeeds normally.
    """
    site_packages_matches = glob.glob('./.venv/lib/python3.*/site-packages')
    if not site_packages_matches:
        return
    site_packages = site_packages_matches[0]

    candidates = {}
    for path in _find_binaries(site_packages):
        candidates.setdefault(os.path.basename(path), []).append(path)

    unrepairable = []
    for built in _find_binaries(app_path):
        if subprocess.run(
            ['codesign', '--verify', '--strict', built], capture_output=True
        ).returncode == 0:
            continue

        name = os.path.basename(built)
        size = os.path.getsize(built)
        source = next(
            (c for c in candidates.get(name, []) if os.path.getsize(c) == size), None
        )
        if not source:
            unrepairable.append(built)
            continue

        own_id_lines = subprocess.run(
            ['otool', '-D', built], capture_output=True, text=True
        ).stdout.splitlines()
        own_id = own_id_lines[1].strip() if len(own_id_lines) > 1 else None
        deps = [
            line.strip().split(' ')[0]
            for line in subprocess.check_output(['otool', '-L', built], text=True).splitlines()[1:]
        ]

        shutil.copy2(source, built)

        if own_id:
            subprocess.check_call(['install_name_tool', '-id', own_id, built])
        source_deps = [
            line.strip().split(' ')[0]
            for line in subprocess.check_output(['otool', '-L', source], text=True).splitlines()[1:]
        ]
        for dep in deps:
            dep_name = os.path.basename(dep)
            source_dep = next((d for d in source_deps if os.path.basename(d) == dep_name), None)
            if source_dep and source_dep != dep:
                subprocess.check_call(['install_name_tool', '-change', source_dep, dep, built])

        print(f'Repaired py2app dylib-merge corruption in {built}')

    if unrepairable:
        listed = '\n  '.join(unrepairable)
        sys.exit(
            'error: the following files are structurally invalid (py2app '
            'dylib-merge corruption) and no same-size original was found '
            f'under {site_packages} to repair them from -- inspect manually:'
            f'\n  {listed}'
        )


class py2app(_Py2AppBase):
    def finalize_options(self):
        self.distribution.install_requires = []
        super().finalize_options()

OPTIONS = {
    'iconfile':'./resources/accupatt_logo.icns',
    'resources':['./resources'],
    # 'packages' forces a full, unzipped directory copy instead of flattening
    # into python3XX.zip. PIL needs this: its .dylibs/ (libjpeg, libpng, etc.)
    # are package data, not recognized extension modules, so py2app was
    # zipping them -- Apple's notary service correctly rejects dylibs inside
    # a zip since nothing on the signing side (or dyld) can reach them there.
    'packages': ['aerial_spray_nozzle_models', 'oceandirect', 'PIL'],
    'bdist_base':'./dist/osx/build',
    'dist_dir':'./dist/osx/dist',
    'plist': {'CFBundleShortVersionString':VERSION,
              'CFBundleIdentifier':'org.agaviation.accupatt',},
    'excludes': [
        # NOTE: py2app's excludes match the *import* name, not the PyPI
        # package name. "cairo" (not "pycairo") is what reportlab's optional
        # renderPM backend imports; AccuPatt doesn't need it, and bundling it
        # drags in an unused libcairo/libX11/libxcb X11 cluster that has been
        # observed corrupting duplicate-named dylibs (cv2 and PIL each vendor
        # their own differently-built libxcb.1.1.0.dylib; py2app's Frameworks
        # dedup mixed metadata from one with file content from the other,
        # producing a structurally invalid file that fails strict codesign
        # verification).
        # "freetype" (freetype-py) is only reachable through reportlab's
        # optional text-to-vector-path backend (graphics/utils.py), an
        # alternate rendering path AccuPatt never selects -- it's a
        # transitive dependency of rlPyCairo (already excluded below) that
        # py2app's static analysis still finds via a guarded `import
        # freetype` and bundles defensively. Notarization rejects its bundled
        # libfreetype.dylib (package data, never signed) regardless, so it
        # needs to go either way.
        "PyInstaller", "cairo", "freetype", "rlPyCairo",
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

# The OceanDirect SDK is staged locally, not committed (tools/sync_oceandirect.py),
# and the EULA must ship for both the DMG agreement and the first-run dialog.
for required, remedy in [
    ('./oceandirect/lib/liboceandirect.dylib',
     'Install the OceanDirect SDK, then: poetry run python tools/sync_oceandirect.py'),
    ('./resources/documents/AccuPatt_EULA.txt',
     'The AccuPatt EULA is missing from resources/documents.'),
]:
    if not os.path.isfile(required):
        sys.exit(f'error: {required} not found.\n  {remedy}')

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

    _repair_py2app_dylib_corruption('./dist/osx/dist/AccuPatt.app')

    codesign_identity = os.environ.get('CODESIGN_IDENTITY')
    if codesign_identity:
        subprocess.check_call(
            ['sh', './dist/osx/sign_mac.sh', './dist/osx/dist/AccuPatt.app']
        )
    else:
        print('CODESIGN_IDENTITY not set, skipping codesigning (unsigned dev build)')

    subprocess.call(['sh','./dist/osx/genAppDmg.sh'])

    notary_profile = os.environ.get('NOTARY_PROFILE')
    if codesign_identity and notary_profile:
        subprocess.check_call(
            ['sh', './dist/osx/notarize_mac.sh', './dist/osx/AccuPatt.dmg']
        )
    elif codesign_identity:
        print('NOTARY_PROFILE not set, skipping notarization/stapling')
