#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from pathlib import Path

import matplotlib.pyplot as plt


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Adjust ISO=100 measured raw luminance values to a reference aperture "
            "and plot them against shutter speed."
        )
    )
    parser.add_argument(
        "--input",
        default="output/csv/iso100_exposure_values.csv",
        help="Input CSV path. Default: output/csv/iso100_exposure_values.csv",
    )
    parser.add_argument(
        "--output-image",
        default="output/images/iso100_adjusted_to_f1_8.png",
        help="Output image path. Default: output/images/iso100_adjusted_to_f1_8.png",
    )
    parser.add_argument(
        "--output-csv",
        default="output/csv/iso100_adjusted_to_f1_8.csv",
        help="Adjusted CSV path. Default: output/csv/iso100_adjusted_to_f1_8.csv",
    )
    parser.add_argument(
        "--reference-aperture",
        type=float,
        default=1.8,
        help="Reference aperture to normalize to. Default: 1.8",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    input_path = Path(args.input)
    output_image = Path(args.output_image)
    output_csv = Path(args.output_csv)
    reference_aperture = args.reference_aperture

    with input_path.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))

    if not rows:
        raise SystemExit(f"no rows found in {input_path}")

    rows.sort(key=lambda row: float(row["Shutter Seconds"]))

    adjusted_rows: list[dict[str, str]] = []
    x_labels: list[str] = []
    y_values: list[float] = []

    for row in rows:
        aperture = float(row["Aperture"])
        raw_luminance = float(row["Measured Raw Luminance"])
        adjust_factor = (aperture / reference_aperture) ** 2
        adjusted_raw_luminance = raw_luminance * adjust_factor

        merged = dict(row)
        merged["Reference Aperture"] = f"{reference_aperture:.3f}"
        merged["Adjustment Factor"] = f"{adjust_factor:.6f}"
        merged["Adjusted Raw Luminance"] = f"{adjusted_raw_luminance:.3f}"
        adjusted_rows.append(merged)

        x_labels.append(row["Shutter Label"])
        y_values.append(adjusted_raw_luminance)

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with output_csv.open("w", newline="", encoding="utf-8") as fh:
        fieldnames = list(adjusted_rows[0].keys())
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(adjusted_rows)

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(x_labels, y_values, marker="o", linewidth=2, color="#345c9c")
    ax.set_title(f"ISO 100: Raw Luminance Adjusted to f/{reference_aperture:g}")
    ax.set_xlabel("Shutter Speed (1/N sec)")
    ax.set_ylabel("Adjusted Raw Luminance")
    ax.grid(True, axis="y", alpha=0.3)
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()

    output_image.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_image, dpi=160)

    print(f"wrote adjusted csv to {output_csv}")
    print(f"wrote graph to {output_image}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
