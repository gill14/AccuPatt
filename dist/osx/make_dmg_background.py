"""One-off generator for the DMG installer background image.

Not run as part of every build -- the output is a static asset committed to
the repo (dmg_background.png). Re-run and re-commit only when the design
needs to change:

    python3 dist/osx/make_dmg_background.py

Coordinates here must stay in sync with the icon positions style_dmg.sh sets
via AppleScript (both use a 660x400 logical window).
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent.parent

# Rendered at 2x and downsampled for crisp anti-aliasing on Retina displays.
SCALE = 2
W, H = 660, 400

NAVY = (14, 58, 95)
MAGENTA = (214, 59, 122)
BG = (247, 246, 243)

# Must match the icon centers set in style_dmg.sh's AppleScript.
APP_ICON_CENTER = (165, 210)
APPS_ICON_CENTER = (495, 210)


def font(name, size):
    return ImageFont.truetype(f"/System/Library/Fonts/Supplemental/{name}.ttf", size * SCALE)


def rounded_arrow(draw, x0, x1, y, color, shaft_h=14, head_w=34, head_h=44):
    shaft_h *= SCALE
    head_w *= SCALE
    head_h *= SCALE
    x0, x1, y = x0 * SCALE, x1 * SCALE, y * SCALE
    head_back = x1 - head_w
    # Extend the shaft well past the triangle's back edge so its rounded
    # right end is fully covered by the triangle instead of peeking out as
    # a stray curve where the two shapes meet.
    shaft_end = head_back + shaft_h
    draw.rounded_rectangle(
        [x0, y - shaft_h / 2, shaft_end, y + shaft_h / 2], radius=shaft_h / 2, fill=color
    )
    draw.polygon(
        [
            (head_back, y - head_h / 2),
            (x1, y),
            (head_back, y + head_h / 2),
        ],
        fill=color,
    )


def main():
    img = Image.new("RGB", (W * SCALE, H * SCALE), BG)
    draw = ImageDraw.Draw(img)

    logo = Image.open(REPO_ROOT / "resources" / "accupatt_logo.png").convert("RGBA")
    logo_w = 260 * SCALE
    logo_h = int(logo.height * (logo_w / logo.width))
    logo = logo.resize((logo_w, logo_h), Image.LANCZOS)
    img.paste(logo, ((W * SCALE - logo_w) // 2, 26 * SCALE), logo)

    arrow_y = APP_ICON_CENTER[1]
    rounded_arrow(draw, APP_ICON_CENTER[0] + 95, APPS_ICON_CENTER[0] - 95, arrow_y, MAGENTA)

    label_font = font("Arial Bold", 20)
    label = "Drag AccuPatt to Applications to install"
    bbox = draw.textbbox((0, 0), label, font=label_font)
    label_w = bbox[2] - bbox[0]
    draw.text(
        ((W * SCALE - label_w) / 2, 300 * SCALE),
        label,
        font=label_font,
        fill=NAVY,
    )

    img = img.resize((W, H), Image.LANCZOS)
    out = HERE / "dmg_background.png"
    img.save(out)
    print(f"Wrote {out} ({W}x{H})")


if __name__ == "__main__":
    main()
