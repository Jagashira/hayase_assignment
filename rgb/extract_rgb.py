#!/usr/bin/env python3

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image


def main() -> int:
    if len(sys.argv) != 2:
        print(f"Usage: {Path(sys.argv[0]).name} imagefile", file=sys.stderr)
        return 1

    image_path = Path(sys.argv[1])
    image = Image.open(image_path).convert("RGB")
    width, height = image.size
    pixels = image.load()

    for y in range(height):
        for x in range(width):
            r, g, b = pixels[x, y]
            print(f"{y} {x} {r} {g} {b} {r + g + b}")
        print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
