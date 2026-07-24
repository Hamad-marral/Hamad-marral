#!/usr/bin/env python3
"""
Cleans up a source photo so it converts to a crisp ASCII portrait instead of
mid-gray mush:
  1. Cuts the background with rembg.
  2. Evens out lighting with CLAHE (adaptive histogram equalization).
  3. Composites onto a white canvas so background falls at the light end
     of the character ramp.

Usage:
    python tools/clean_photo.py my-photo.jpg
Writes:
    assets/photo-ready.png
"""
import os
import sys

import cv2
import numpy as np
from PIL import Image
from rembg import remove

OUT_PATH = os.path.join(os.path.dirname(__file__), "..", "assets", "photo-ready.png")


def remove_background(path: str) -> Image.Image:
    with open(path, "rb") as f:
        input_bytes = f.read()
    output_bytes = remove(input_bytes)
    from io import BytesIO
    return Image.open(BytesIO(output_bytes)).convert("RGBA")


def apply_clahe(img_rgba: Image.Image) -> Image.Image:
    rgb = np.array(img_rgba.convert("RGB"))
    lab = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    l2 = clahe.apply(l)
    lab2 = cv2.merge((l2, a, b))
    rgb2 = cv2.cvtColor(lab2, cv2.COLOR_LAB2RGB)
    out = Image.fromarray(rgb2).convert("RGBA")
    out.putalpha(img_rgba.getchannel("A"))
    return out


def composite_on_white(img_rgba: Image.Image) -> Image.Image:
    white_bg = Image.new("RGBA", img_rgba.size, (255, 255, 255, 255))
    return Image.alpha_composite(white_bg, img_rgba).convert("RGB")


def main():
    if len(sys.argv) < 2:
        print("usage: python tools/clean_photo.py <path-to-photo>")
        sys.exit(1)
    src = sys.argv[1]
    img = remove_background(src)
    img = apply_clahe(img)
    img = composite_on_white(img)
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    img.save(OUT_PATH)
    print(f"wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
