#!/usr/bin/env python3
"""Shrink exported figure PNGs so docs stay light over slow links.

Downscales to MAX_WIDTH and re-encodes as an adaptive 256-colour palette PNG
(these diagrams are flat-colour art, so the visual difference is negligible while
the byte count drops by ~5-10x).

Usage: python3 optimize_png.py [files...]
"""

import os
import sys

from PIL import Image

MAX_WIDTH = 1500
COLORS = 256


def optimize(path: str) -> None:
    before = os.path.getsize(path)
    with Image.open(path) as im:
        im = im.convert("RGB")
        if im.width > MAX_WIDTH:
            height = round(im.height * MAX_WIDTH / im.width)
            im = im.resize((MAX_WIDTH, height), Image.LANCZOS)
        quantized = im.quantize(colors=COLORS, method=Image.MEDIANCUT, dither=Image.FLOYDSTEINBERG)
        quantized.save(path, optimize=True)
    after = os.path.getsize(path)
    print(f"{path}: {before // 1024} KB -> {after // 1024} KB")


def main() -> None:
    files = sys.argv[1:]
    if not files:
        d = os.path.dirname(os.path.abspath(__file__))
        files = [os.path.join(d, f) for f in sorted(os.listdir(d)) if f.endswith(".png")]
    for f in files:
        optimize(f)


if __name__ == "__main__":
    main()
