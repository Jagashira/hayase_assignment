#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt


@dataclass
class ExposureRow:
    filename: str
    shutter_label: str
    aperture: float
    shutter_seconds: float
    relative_exposure: float
    normalized_prediction: float


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Plot theoretical ISO=100 raw luminance using exposure t / F^2."
    )
    parser.add_argument(
        "--input-dir",
        default="public/nef",
        help="Directory containing renamed NEF files. Default: public/nef",
    )
    parser.add_argument(
        "--output",
        default="output/images/iso100_theoretical_raw_luminance.png",
        help="Output image path. Default: output/images/iso100_theoretical_raw_luminance.png",
    )
    return parser


def parse_filename(path: Path) -> ExposureRow | None:
    if path.suffix != ".NEF" or path.name.startswith("DSC_"):
        return None

    try:
        iso_text, shutter_text, aperture_text = path.stem.split("-", 2)
        iso_value = int(iso_text)
        shutter_denominator = float(shutter_text)
        aperture = float(aperture_text)
    except ValueError:
        return None

    if iso_value != 100 or shutter_denominator <= 0.0 or aperture <= 0.0:
        return None

    shutter_seconds = 1.0 / shutter_denominator
    relative_exposure = shutter_seconds / (aperture * aperture)
    return ExposureRow(
        filename=path.name,
        shutter_label=shutter_text,
        aperture=aperture,
        shutter_seconds=shutter_seconds,
        relative_exposure=relative_exposure,
        normalized_prediction=0.0,
    )


def load_rows(input_dir: Path) -> list[ExposureRow]:
    rows = [row for row in (parse_filename(path) for path in input_dir.glob("*.NEF")) if row]
    rows.sort(key=lambda row: row.shutter_seconds)
    if not rows:
        raise SystemExit(f"no ISO=100 renamed NEF files found in {input_dir}")

    max_exposure = max(row.relative_exposure for row in rows)
    scale = 10000.0 / max_exposure if max_exposure > 0.0 else 1.0
    for row in rows:
        row.normalized_prediction = row.relative_exposure * scale
    return rows


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    output_path = Path(args.output)
    rows = load_rows(input_dir)

    x_labels = [row.shutter_label for row in rows]
    y_values = [row.normalized_prediction for row in rows]

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(x_labels, y_values, marker="o", linewidth=2, color="#8a4f2a")
    ax.set_title("ISO 100: Theoretical Raw Luminance from Exposure t / F^2")
    ax.set_xlabel("Filename Shutter (1/N sec)")
    ax.set_ylabel("Predicted Raw Luminance (normalized)")
    ax.grid(True, axis="y", alpha=0.3)
    plt.xticks(rotation=45, ha="right")

    for index, row in enumerate(rows):
        ax.annotate(
            f"f/{row.aperture:g}",
            (index, row.normalized_prediction),
            textcoords="offset points",
            xytext=(0, 6),
            ha="center",
            fontsize=8,
            color="#5a341d",
        )

    plt.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=160)
    print(f"wrote graph to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
