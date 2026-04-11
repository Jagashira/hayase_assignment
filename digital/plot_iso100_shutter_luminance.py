#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from pathlib import Path

import matplotlib.pyplot as plt


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Plot ISO=100 shutter values against raw luminance."
    )
    parser.add_argument(
        "--input",
        default="output/csv/non_dsc_shutter_rgb.csv",
        help="Input CSV path. Default: output/csv/non_dsc_shutter_rgb.csv",
    )
    parser.add_argument(
        "--output",
        default="output/images/iso100_shutter_vs_raw_luminance.png",
        help="Output image path. Default: output/images/iso100_shutter_vs_raw_luminance.png",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    csv_path = Path(args.input)
    output_path = Path(args.output)

    if not csv_path.exists():
        raise SystemExit(f"missing input csv: {csv_path}")

    with csv_path.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))

    rows = [row for row in rows if row["Filename ISO"] == "100"]
    if not rows:
        raise SystemExit("no ISO=100 rows found in csv")

    rows.sort(key=lambda row: float(row["Shutter Seconds"]))

    x_labels = [row["Filename Shutter"] for row in rows]
    y_values = [float(row["Raw Luminance"]) for row in rows]

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(x_labels, y_values, marker="o", linewidth=2, color="#2f5d50")
    ax.set_title("ISO 100: Column C vs Raw Luminance")
    ax.set_xlabel("Column C: Filename Shutter")
    ax.set_ylabel("Raw Luminance")
    ax.grid(True, axis="y", alpha=0.3)
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=160)
    print(f"wrote graph to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
