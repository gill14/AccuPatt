"""Copy the OceanDirect Python bindings from an installed SDK into ./oceandirect.

AccuPatt does not keep the OceanDirect SDK in source control. The OceanDirect
API Terms permit distributing the APIs only as an integrated part of an
application (1.2), and require us to take reasonable measures against their
unauthorised distribution (3.3) -- a public repository from which the SDK could
be cloned on its own is neither. Release installers still bundle the SDK, which
1.2 does allow.

So each developer installs the SDK themselves (they each accept the API Terms
by doing so -- it cannot be accepted on their behalf) and runs this script to
stage it where AccuPatt and the bundlers expect it.

    Download: https://www.oceanoptics.com/products/software/
    Then:     poetry run python tools/sync_oceandirect.py

Set OCEANDIRECT_HOME to override SDK discovery.
"""

import ctypes
import datetime
import os
import re
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEST = REPO_ROOT / "oceandirect"

# Where the vendor installer puts things, per platform.
SEARCH_PATHS = {
    "darwin": [
        Path("/Applications/OceanInsight/OceanDirect"),
        Path("/Applications/Ocean Insight/OceanDirect"),
        Path("/Applications/OceanOptics/OceanDirect"),
    ],
    "win32": [
        Path(r"C:\Program Files\Ocean Insight\OceanDirect"),
        Path(r"C:\Program Files\Ocean Optics\OceanDirect SDK"),
        Path(r"C:\Program Files\Ocean Insight\OceanDirect SDK"),
        Path(r"C:\Program Files (x86)\Ocean Optics\OceanDirect SDK"),
    ],
    "linux": [
        Path("/usr/local/OceanDirect"),
        Path("/opt/OceanDirect"),
    ],
}

LIB_NAMES = {
    "darwin": "liboceandirect.dylib",
    "win32": "OceanDirect.dll",
    "linux": "liboceandirect.so",
}


def find_sdk() -> Path:
    override = os.environ.get("OCEANDIRECT_HOME")
    if override:
        path = Path(override)
        if not (path / "python" / "oceandirect").is_dir():
            sys.exit(
                f"error: OCEANDIRECT_HOME={override} does not contain "
                f"python/oceandirect"
            )
        return path

    for candidate in SEARCH_PATHS.get(sys.platform, []):
        if (candidate / "python" / "oceandirect").is_dir():
            return candidate

    searched = "\n  ".join(str(p) for p in SEARCH_PATHS.get(sys.platform, []))
    sys.exit(
        "error: no OceanDirect SDK found. Install it from\n"
        "  https://www.oceanoptics.com/products/software/\n"
        "or set OCEANDIRECT_HOME to its install directory.\n\n"
        f"Searched:\n  {searched}"
    )


def sdk_version(sdk: Path, lib_path: Path) -> str:
    """Ask the library itself what version it is.

    Do not trust include/private/OceanDirectProductVersion.h: the 3.3.0
    installer does not replace it when upgrading over an older SDK, so on an
    upgraded machine it still reports the version that was there before.
    odapi_get_api_version_numbers() comes from the binary actually being
    shipped, so it cannot drift.
    """
    try:
        lib = ctypes.cdll.LoadLibrary(str(lib_path))
        major, minor, point = ctypes.c_uint(), ctypes.c_uint(), ctypes.c_uint()
        lib.odapi_get_api_version_numbers.argtypes = [ctypes.POINTER(ctypes.c_uint)] * 3
        lib.odapi_get_api_version_numbers(
            ctypes.byref(major), ctypes.byref(minor), ctypes.byref(point)
        )
        return f"{major.value}.{minor.value}.{point.value}"
    except Exception:
        pass

    # Fall back to the header, flagged, since it may be stale.
    headers = list(sdk.glob("include/**/OceanDirectProductVersion.h"))
    if not headers:
        return "unknown"
    try:
        text = headers[0].read_text(errors="replace")
    except OSError:
        return "unknown"

    parts = {}
    for key in ("Major", "Minor", "Point"):
        match = re.search(rf"oceandirect{key}Version\s*=\s*(\d+)", text)
        if not match:
            return "unknown"
        parts[key] = match.group(1)

    return (
        f"{parts['Major']}.{parts['Minor']}.{parts['Point']} "
        "(from version header — may be stale)"
    )


def main() -> int:
    lib_name = LIB_NAMES.get(sys.platform)
    if lib_name is None:
        sys.exit(f"error: unsupported platform {sys.platform}")

    sdk = find_sdk()
    source = sdk / "python" / "oceandirect"
    print(f"Found OceanDirect SDK: {sdk}")

    # The library ships inside the Python package, but fall back to the SDK's
    # top-level lib/ if a given installer only populates one of them.
    lib_source = source / "lib" / lib_name
    if not lib_source.is_file():
        lib_source = sdk / "lib" / lib_name
    if not lib_source.is_file():
        sys.exit(f"error: {lib_name} not found under {sdk}")

    (DEST / "lib").mkdir(parents=True, exist_ok=True)

    # Replace this platform's files only. The Windows build runs against the
    # same working tree over a shared folder, so wiping the directory here
    # would delete the .dll that build needs.
    for stale in DEST.glob("*.py"):
        stale.unlink()
    shutil.rmtree(DEST / "__pycache__", ignore_errors=True)

    copied = []
    for py_file in sorted(source.glob("*.py")):
        shutil.copy2(py_file, DEST / py_file.name)
        copied.append(py_file.name)
    if not copied:
        sys.exit(f"error: no Python modules found in {source}")

    shutil.copy2(lib_source, DEST / "lib" / lib_name)
    copied.append(f"lib/{lib_name}")

    other_libs = sorted(p.name for p in (DEST / "lib").iterdir() if p.name != lib_name)

    (DEST / "VENDOR_INFO.txt").write_text(
        "OceanDirect SDK - vendored, not under source control\n"
        "===================================================\n\n"
        f"Synced:   {datetime.date.today().isoformat()}\n"
        f"Source:   {sdk}\n"
        f"Version:  {sdk_version(sdk, DEST / 'lib' / lib_name)}\n"
        f"Platform: {sys.platform}\n\n"
        "Files synced for this platform:\n"
        + "".join(f"  {name}\n" for name in copied)
        + (
            "\nOther platform libraries left in place (synced elsewhere):\n"
            + "".join(f"  lib/{name}\n" for name in other_libs)
            if other_libs
            else ""
        )
        + "\n"
        "Regenerate with: python tools/sync_oceandirect.py\n"
        "Do not modify these files and do not commit them. They belong to\n"
        "Ocean Optics, Inc. and are used under the OceanDirect API Terms.\n"
    )

    print(f"Staged {len(copied)} files into {DEST}")
    for name in copied:
        print(f"  {name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
