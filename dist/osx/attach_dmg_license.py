"""Attach the AccuPatt EULA to the release DMG as a click-through agreement.

macOS shows an "Agree / Disagree" panel before mounting a disk image that
carries a software licence agreement (SLA). That gives the Mac build the same
accept-before-access gate the Inno Setup LicenseFile gives the Windows build,
as required by the OceanDirect API Terms (1.2(b)).

The SLA lives in classic resource-fork resources, which `hdiutil udifrez`
grafts on from an XML plist:

    LPic  5000   language table (which STR#/TEXT to show)
    STR#  5000   button labels
    TEXT  5000   the agreement itself

Usage:
    python3 attach_dmg_license.py <path-to-dmg> <path-to-eula.txt>
"""

import plistlib
import subprocess
import sys

# LPic: default language 0, one entry -> {language 0 (English), resource
# offset 0 (i.e. 5000), single-byte encoding}.
LPIC = bytes([0, 0, 0, 1, 0, 0, 0, 0, 0, 0])

# STR# 5000: a count followed by Pascal strings. Order is fixed and defined by
# the OS: language name, Agree, Disagree, Print, Save, and the prompt text.
BUTTONS = [
    b"English",
    b"Agree",
    b"Disagree",
    b"Print",
    b"Save",
    b"If you agree to the terms of this license, click Agree to access the "
    b"software. If you do not agree, click Disagree.",
]


def build_str_resource() -> bytes:
    out = len(BUTTONS).to_bytes(2, "big")
    for item in BUTTONS:
        if len(item) > 255:
            raise ValueError("Pascal strings cap at 255 bytes")
        out += bytes([len(item)]) + item
    return out


def resource(res_id: str, data: bytes) -> dict:
    return {
        "Attributes": "0x0000",
        "Data": data,
        "ID": res_id,
        "Name": "",
    }


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__)
        return 2
    dmg_path, eula_path = sys.argv[1], sys.argv[2]

    with open(eula_path, encoding="utf-8") as f:
        text = f.read()

    # Classic TEXT resources use CR line endings, and the resource is not
    # Unicode -- fold anything outside Mac Roman rather than emit mojibake.
    body = text.replace("\r\n", "\n").replace("\n", "\r")
    encoded = body.encode("mac_roman", errors="replace")

    plist = {
        "LPic": [resource("5000", LPIC)],
        "STR#": [resource("5000", build_str_resource())],
        "TEXT": [resource("5000", encoded)],
    }

    xml = plistlib.dumps(plist, fmt=plistlib.FMT_XML)
    subprocess.run(
        ["hdiutil", "udifrez", "-xml", "/dev/stdin", "", dmg_path],
        input=xml,
        check=True,
    )
    print(f"Attached license agreement to {dmg_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
