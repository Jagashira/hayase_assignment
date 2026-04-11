#!/usr/bin/env python3
from __future__ import annotations

import argparse
import io
import subprocess
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from PIL import Image


def load_nef_preview(dcraw_path: Path, nef_path: Path) -> np.ndarray:
    proc = subprocess.run(
        [str(dcraw_path), "-e", "-c", str(nef_path)],
        check=True,
        capture_output=True,
    )
    image = Image.open(io.BytesIO(proc.stdout)).convert("RGB")
    return np.asarray(image)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Display a NEF preview and show pixel position/RGB under the cursor."
    )
    parser.add_argument("nef", help="Path to the .NEF file")
    parser.add_argument(
        "--dcraw",
        default="./dcraw",
        help="Path to dcraw executable. Default: ./dcraw",
    )
    parser.add_argument(
        "--info-only",
        action="store_true",
        help="Load the NEF preview and print image info without opening a window.",
    )
    return parser


def show_viewer(image: np.ndarray, nef_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(12, 8))
    ax.imshow(image)
    ax.set_title(f"{nef_path.name} - move cursor to inspect pixel")
    ax.set_xlabel("Column (1-based)")
    ax.set_ylabel("Row (1-based)")

    status_text = ax.text(
        0.01,
        0.99,
        "row=?, col=?, RGB=(?, ?, ?)",
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=11,
        color="white",
        bbox={"facecolor": "black", "alpha": 0.6, "pad": 6},
    )

    def on_move(event) -> None:
        if event.inaxes != ax or event.xdata is None or event.ydata is None:
            return

        col = int(round(event.xdata))
        row = int(round(event.ydata))
        if row < 0 or col < 0 or row >= image.shape[0] or col >= image.shape[1]:
            return

        r, g, b = image[row, col]
        status_text.set_text(
            f"row={row + 1}, col={col + 1}, RGB=({int(r)}, {int(g)}, {int(b)})"
        )
        fig.canvas.draw_idle()

    fig.canvas.mpl_connect("motion_notify_event", on_move)
    plt.tight_layout()
    plt.show()


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    dcraw_path = Path(args.dcraw).resolve()
    nef_path = Path(args.nef).resolve()

    if not dcraw_path.exists():
        raise SystemExit(f"dcraw not found: {dcraw_path}")
    if not nef_path.exists():
        raise SystemExit(f"NEF not found: {nef_path}")

    image = load_nef_preview(dcraw_path, nef_path)

    if args.info_only:
        print(f"file={nef_path.name}")
        print(f"width={image.shape[1]}")
        print(f"height={image.shape[0]}")
        print("mode=RGB")
        return 0

    show_viewer(image, nef_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
