#!/usr/bin/env python3
"""
Downscales assets/photo-ready.png to a character grid and renders it as a
self-drawing ASCII SVG: each row is wrapped in its own clip rect that
animates from width 0 -> full, staggered ~40ms apart, then holds.

Requires assets/photo-ready.png (run tools/clean_photo.py first).
Writes: portrait.svg
"""
import os
from xml.sax.saxutils import escape

import numpy as np
from PIL import Image, ImageFilter

SRC = os.path.join(os.path.dirname(__file__), "..", "assets", "photo-ready.png")
OUT = os.path.join(os.path.dirname(__file__), "..", "portrait.svg")

# left = light/empty, right = dense/dark
GLYPHS = " .:-=+*#%@"
COLS = 130         # character columns — higher = sharper likeness
BG = "#0a0e1a"
CHAR_W = 6.4
CHAR_H = 11
ROW_STAGGER = 0.035  # seconds between each row starting its wipe

# dark -> bright "circuit board" gradient. Same brightness bucket drives both
# the glyph density AND the color, so the two stay consistent instead of
# looking like random speckle.
TECH_LEVELS = [
    "#0a1628", "#0f3057", "#155e8c", "#1c7ed6",
    "#3fa9f5", "#63c7ff", "#a8e2ff", "#e8f7ff",
]


def load_brightness():
    img = Image.open(SRC).convert("L")
    aspect = img.height / img.width
    rows = max(1, int(COLS * aspect * (CHAR_W / CHAR_H)))
    # slight blur before downscaling avoids single-pixel noise turning into
    # isolated stray-colored characters
    img = img.filter(ImageFilter.GaussianBlur(radius=1.2))
    small = img.resize((COLS, rows), Image.LANCZOS)
    arr = np.array(small).astype(np.float32) / 255.0  # 0 = black, 1 = white
    return arr


def level_index(brightness: float) -> int:
    # brightness 1.0 (white/background) -> lightest bucket
    idx = int((1.0 - brightness) * (len(TECH_LEVELS) - 1))
    return max(0, min(idx, len(TECH_LEVELS) - 1))


def to_glyph(brightness: float) -> str:
    idx = int((1.0 - brightness) * (len(GLYPHS) - 1))
    idx = max(0, min(idx, len(GLYPHS) - 1))
    return GLYPHS[idx]


def render(arr):
    rows, cols = arr.shape
    width = cols * CHAR_W + 20
    height = rows * CHAR_H + 20

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width:.0f}" height="{height:.0f}" '
        f'viewBox="0 0 {width:.0f} {height:.0f}" font-family="Menlo, Consolas, monospace">',
        f'<rect width="100%" height="100%" fill="{BG}" rx="10"/>',
    ]

    row_px_width = cols * CHAR_W

    for r in range(rows):
        y = 10 + (r + 1) * CHAR_H
        row_id = f"clip-row-{r}"
        begin = r * ROW_STAGGER
        parts.append(
            f'<clipPath id="{row_id}"><rect x="0" y="{y - CHAR_H:.1f}" '
            f'width="0" height="{CHAR_H + 2:.1f}">'
            f'<animate attributeName="width" from="0" to="{row_px_width:.0f}" '
            f'begin="{begin:.3f}s" dur="0.45s" fill="freeze"/>'
            f'</rect></clipPath>'
        )

        # group consecutive same-bucket cells into one tspan to keep markup lean
        tspans = []
        run_char = ""
        run_level = None
        for c in range(cols):
            b = arr[r, c]
            lvl = level_index(b)
            ch = to_glyph(b)
            display_ch = " " if lvl == len(TECH_LEVELS) - 1 and ch == " " else ch
            if lvl == run_level:
                run_char += display_ch
            else:
                if run_char:
                    tspans.append((run_level, run_char))
                run_char = display_ch
                run_level = lvl
        if run_char:
            tspans.append((run_level, run_char))

        spans_markup = "".join(
            f'<tspan fill="{TECH_LEVELS[lvl]}">{escape(text)}</tspan>'
            for lvl, text in tspans
        )
        parts.append(
            f'<g clip-path="url(#{row_id})">'
            f'<text x="10" y="{y:.1f}" font-size="{CHAR_H}px" xml:space="preserve">{spans_markup}</text>'
            f'</g>'
        )

    parts.append("</svg>")
    return "\n".join(parts)


def main():
    if not os.path.exists(SRC):
        print(f"missing {SRC} — run tools/clean_photo.py <photo> first")
        return
    arr = load_brightness()
    svg = render(arr)
    with open(OUT, "w") as f:
        f.write(svg)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
