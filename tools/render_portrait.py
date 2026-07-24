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
from PIL import Image

SRC = os.path.join(os.path.dirname(__file__), "..", "assets", "photo-ready.png")
OUT = os.path.join(os.path.dirname(__file__), "..", "portrait.svg")

# left = light/empty, right = dense/dark
GLYPHS = " '.,:;~+*xXO#"
COLS = 90          # character columns
BG = "#0d0d17"
CHAR_W = 7
CHAR_H = 12
ROW_STAGGER = 0.04  # seconds between each row starting its wipe
PALETTE_SIZE = 24   # quantized colors — enough to look like "you", not a rainbow


def load_grids():
    color_img = Image.open(SRC).convert("RGB")
    aspect = color_img.height / color_img.width
    # character cells are taller than they are wide, correct for that
    rows = max(1, int(COLS * aspect * (CHAR_W / CHAR_H)))
    small = color_img.resize((COLS, rows))

    # quantize so nearby pixels snap to a shared clean tone instead of noisy speckle
    quant = small.quantize(colors=PALETTE_SIZE, method=Image.MEDIANCUT).convert("RGB")

    brightness = np.array(small.convert("L")).astype(np.float32) / 255.0
    colors = np.array(quant)  # rows x cols x 3
    return brightness, colors


def to_glyph(brightness: float) -> str:
    # brightness 1.0 (white/background) -> lightest glyph (space)
    idx = int((1.0 - brightness) * (len(GLYPHS) - 1))
    idx = max(0, min(idx, len(GLYPHS) - 1))
    ch = GLYPHS[idx]
    return " " if ch == " " else ch


def to_hex(rgb) -> str:
    return "#{:02x}{:02x}{:02x}".format(*[int(c) for c in rgb])


def render(brightness, colors):
    rows, cols = brightness.shape
    width = cols * CHAR_W + 20
    height = rows * CHAR_H + 20

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" font-family="Menlo, Consolas, monospace">',
        f'<rect width="100%" height="100%" fill="{BG}" rx="10"/>',
    ]

    row_px_width = cols * CHAR_W

    for r in range(rows):
        y = 10 + (r + 1) * CHAR_H
        row_id = f"clip-row-{r}"
        begin = r * ROW_STAGGER
        parts.append(
            f'<clipPath id="{row_id}"><rect x="0" y="{y - CHAR_H}" '
            f'width="0" height="{CHAR_H + 2}">'
            f'<animate attributeName="width" from="0" to="{row_px_width}" '
            f'begin="{begin:.3f}s" dur="0.5s" fill="freeze"/>'
            f'</rect></clipPath>'
        )

        # group consecutive same-color cells into one tspan to keep markup lean
        tspans = []
        run_char = ""
        run_color = None
        for c in range(cols):
            ch = to_glyph(brightness[r, c])
            color = to_hex(colors[r, c]) if ch != " " else None
            if color == run_color:
                run_char += ch
            else:
                if run_char:
                    tspans.append((run_color, run_char))
                run_char = ch
                run_color = color
        if run_char:
            tspans.append((run_color, run_char))

        spans_markup = "".join(
            f'<tspan fill="{color or BG}">{escape(text)}</tspan>'
            for color, text in tspans
        )
        parts.append(
            f'<g clip-path="url(#{row_id})">'
            f'<text x="10" y="{y}" font-size="{CHAR_H}px" xml:space="preserve">{spans_markup}</text>'
            f'</g>'
        )

    parts.append("</svg>")
    return "\n".join(parts)


def main():
    if not os.path.exists(SRC):
        print(f"missing {SRC} — run tools/clean_photo.py <photo> first")
        return
    brightness, colors = load_grids()
    svg = render(brightness, colors)
    with open(OUT, "w") as f:
        f.write(svg)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
