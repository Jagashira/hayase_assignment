#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ExposureRow:
    filename: str
    shutter_label: str
    aperture: float
    shutter_seconds: float
    relative_exposure: float
    normalized_prediction: float
    raw_luminance: float | None = None
    final_luminance: float | None = None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Export ISO=100 values used for shutter-speed graphs, including "
            "derived exposure t / F^2 values."
        )
    )
    parser.add_argument(
        "--input-dir",
        default="public/nef",
        help="Directory containing renamed NEF files. Default: public/nef",
    )
    parser.add_argument(
        "--measured-csv",
        default="output/csv/non_dsc_shutter_rgb.csv",
        help="Optional measured CSV to merge raw/final luminance. Default: output/csv/non_dsc_shutter_rgb.csv",
    )
    parser.add_argument(
        "--output",
        default="output/csv/iso100_exposure_values.csv",
        help="Output CSV path. Default: output/csv/iso100_exposure_values.csv",
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


def load_measured_map(csv_path: Path) -> dict[str, dict[str, str]]:
    if not csv_path.exists() or csv_path.stat().st_size == 0:
        return {}
    with csv_path.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    return {row["Filename"]: row for row in rows if row.get("Filename")}


def write_csv(rows: list[ExposureRow], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(
            [
                "Filename",
                "Shutter Label",
                "Shutter Seconds",
                "Aperture",
                "Relative Exposure (t/F^2)",
                "Normalized Prediction",
                "Measured Raw Luminance",
                "Measured Final Luminance",
            ]
        )
        for row in rows:
            writer.writerow(
                [
                    row.filename,
                    row.shutter_label,
                    f"{row.shutter_seconds:.6f}",
                    f"{row.aperture:.3f}",
                    f"{row.relative_exposure:.8f}",
                    f"{row.normalized_prediction:.3f}",
                    "" if row.raw_luminance is None else f"{row.raw_luminance:.3f}",
                    "" if row.final_luminance is None else f"{row.final_luminance:.3f}",
                ]
            )


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    rows = load_rows(Path(args.input_dir))
    measured_map = load_measured_map(Path(args.measured_csv))
    for row in rows:
        measured = measured_map.get(row.filename)
        if measured:
            raw_luminance = measured.get("Raw Luminance", "")
            final_luminance = measured.get("Luminance", "")
            row.raw_luminance = float(raw_luminance) if raw_luminance else None
            row.final_luminance = float(final_luminance) if final_luminance else None

    output_path = Path(args.output)
    write_csv(rows, output_path)
    print(f"wrote csv to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
