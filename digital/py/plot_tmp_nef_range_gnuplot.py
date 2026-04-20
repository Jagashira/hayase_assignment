#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import math
import re
import subprocess
from pathlib import Path

RAW_LUMINANCE_COLUMN = "Raw Luminance"

COLUMN_ALIASES = {
    "E": ("ISO speed", "ISO speed"),
    "ISO": ("ISO speed", "ISO speed"),
    "ISO_SPEED": ("ISO speed", "ISO speed"),
    "F": ("Shutter", "Shutter speed"),
    "SHUTTER": ("Shutter", "Shutter speed"),
    "SHUTTER_SPEED": ("Shutter", "Shutter speed"),
    "G": ("Aperture", "Aperture"),
    "APERTURE": ("Aperture", "Aperture"),
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Plot spreadsheet-style row ranges from tmp_nef_summary.csv with "
            "Raw Luminance (column X) on the y-axis and a selected column on the x-axis."
        )
    )
    parser.add_argument("start_row", type=int, help="Start row number in spreadsheet notation.")
    parser.add_argument("end_row", type=int, help="End row number in spreadsheet notation.")
    parser.add_argument(
        "x_column",
        help="X-axis selector. Use E/F/G or ISO/SHUTTER/APERTURE.",
    )
    parser.add_argument(
        "--input",
        default="/Users/jagashira/work/github.com/Jagashira/hayase_assignment/digital/tmp_nef_summary.csv",
        help="Input CSV path. Default: digital/tmp_nef_summary.csv",
    )
    parser.add_argument(
        "--output-dir",
        default="/Users/jagashira/work/github.com/Jagashira/hayase_assignment/digital/output/gnuplot",
        help="Output directory for generated data, gnuplot script, and PNG.",
    )
    parser.add_argument(
        "--keep-order",
        action="store_true",
        help="Keep the selected row order instead of sorting by x value.",
    )
    return parser


def column_letter_to_index(column: str) -> int:
    value = 0
    normalized = column.strip().upper()
    if not normalized or not normalized.isalpha():
        raise ValueError(f"invalid column letter: {column}")
    for ch in normalized:
        value = value * 26 + (ord(ch) - ord("A") + 1)
    return value - 1


def parse_iso_speed(value: str) -> float:
    return float(value.strip())


def parse_shutter(value: str) -> float:
    text = value.strip().replace(" sec", "")
    if "/" in text:
        numerator, denominator = text.split("/", 1)
        return float(numerator) / float(denominator)
    return float(text)


def parse_aperture(value: str) -> float:
    text = value.strip()
    if text.lower().startswith("f/"):
        text = text[2:]
    return float(text)


def parse_generic_number(value: str) -> float | None:
    text = value.strip()
    try:
        return float(text)
    except ValueError:
        pass
    match = re.search(r"-?\d+(?:\.\d+)?", text)
    if match:
        return float(match.group(0))
    return None


def value_to_numeric(header: str, value: str) -> float | None:
    if header == "ISO speed":
        return parse_iso_speed(value)
    if header == "Shutter":
        return parse_shutter(value)
    if header == "Aperture":
        return parse_aperture(value)
    return parse_generic_number(value)


def gnuplot_escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("'", "\\'")


def sanitize_token(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9_-]+", "_", text.strip()).strip("_") or "plot"


def csv_quote(text: str) -> str:
    return '"' + text.replace('"', '""') + '"'


def load_selected_rows(csv_path: Path, start_row: int, end_row: int) -> tuple[list[str], list[dict[str, str]]]:
    with csv_path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        headers = reader.fieldnames
        if not headers:
            raise SystemExit(f"no CSV header found in {csv_path}")
        rows = list(reader)

    if start_row < 2:
        raise SystemExit("start_row must be 2 or greater because row 1 is the header.")
    if end_row < start_row:
        raise SystemExit("end_row must be greater than or equal to start_row.")

    start_index = start_row - 2
    end_index = end_row - 2
    if start_index >= len(rows) or end_index >= len(rows):
        raise SystemExit(
            f"requested rows {start_row}-{end_row} exceed data range 2-{len(rows) + 1}."
        )
    return headers, rows[start_index : end_index + 1]


def resolve_x_axis(selector: str, headers: list[str]) -> tuple[str, str]:
    normalized = selector.strip().upper()
    if normalized in COLUMN_ALIASES:
        header_name, axis_label = COLUMN_ALIASES[normalized]
        if header_name not in headers:
            raise SystemExit(f"missing required x-axis column: {header_name}")
        return header_name, axis_label

    x_index = column_letter_to_index(selector)
    if x_index >= len(headers):
        raise SystemExit(
            f"column {selector.upper()} is out of range. This CSV has {len(headers)} columns."
        )
    return headers[x_index], headers[x_index]


def write_data_file(
    data_path: Path,
    selected_rows: list[dict[str, str]],
    x_header: str,
    keep_order: bool,
) -> list[dict[str, str | float | int]]:
    plot_rows: list[dict[str, str | float | int]] = []

    for offset, row in enumerate(selected_rows, start=1):
        x_label = row[x_header]
        y_label = row[RAW_LUMINANCE_COLUMN]
        x_numeric = value_to_numeric(x_header, x_label)
        if x_numeric is None:
            x_numeric = float(offset)
        plot_rows.append(
            {
                "index": offset,
                "filename": row["Filename"],
                "x_label": x_label,
                "y_label": y_label,
                "x_numeric": x_numeric,
                "y_numeric": float(y_label),
            }
        )

    if not keep_order:
        plot_rows.sort(key=lambda row: (float(row["x_numeric"]), int(row["index"])))

    data_path.parent.mkdir(parents=True, exist_ok=True)
    with data_path.open("w", encoding="utf-8", newline="") as fh:
        fh.write("# x_numeric,raw_luminance,x_label,filename\n")
        for row in plot_rows:
            fh.write(
                f"{row['x_numeric']:.10f},"
                f"{row['y_numeric']:.10f},"
                f"{csv_quote(str(row['x_label']))},"
                f"{csv_quote(str(row['filename']))}\n"
            )
    return plot_rows


def write_gnuplot_script(
    script_path: Path,
    data_path: Path,
    output_png: Path,
    x_header: str,
    axis_label: str,
    start_row: int,
    end_row: int,
    plot_rows: list[dict[str, str | float | int]],
) -> None:
    script_path.parent.mkdir(parents=True, exist_ok=True)
    xtics = ", ".join(
        f"'{gnuplot_escape(str(row['x_label']))}' {float(row['x_numeric']):.10f}"
        for row in plot_rows
    )
    script = f"""set datafile separator comma
set terminal pngcairo size 1400,900 enhanced font 'Arial,16'
set output '{gnuplot_escape(str(output_png))}'
set title 'Raw Luminance vs {gnuplot_escape(axis_label)} (rows {start_row}-{end_row})'
set xlabel '{gnuplot_escape(axis_label)}'
set ylabel 'Raw Luminance'
set grid xtics ytics
set key off
set xtics rotate by -35
set xtics ({xtics})
plot '{gnuplot_escape(str(data_path))}' using 1:2 with linespoints lc rgb '#1f6f8b' lw 2 pt 7 ps 1.3
"""
    script_path.write_text(script, encoding="utf-8")


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    csv_path = Path(args.input)
    output_dir = Path(args.output_dir)

    if not csv_path.exists():
        raise SystemExit(f"missing input csv: {csv_path}")

    headers, selected_rows = load_selected_rows(csv_path, args.start_row, args.end_row)
    x_header, axis_label = resolve_x_axis(args.x_column, headers)
    if RAW_LUMINANCE_COLUMN not in headers:
        raise SystemExit(f"missing required y-axis column: {RAW_LUMINANCE_COLUMN}")

    stem = sanitize_token(
        f"rows_{args.start_row}_{args.end_row}_{args.x_column.upper()}_{x_header}"
    )
    data_path = output_dir / f"{stem}.csv"
    script_path = output_dir / f"{stem}.gp"
    png_path = output_dir / f"{stem}.png"

    plot_rows = write_data_file(data_path, selected_rows, x_header, args.keep_order)
    write_gnuplot_script(
        script_path,
        data_path,
        png_path,
        x_header,
        axis_label,
        args.start_row,
        args.end_row,
        plot_rows,
    )

    subprocess.run(["gnuplot", str(script_path)], check=True)

    print(f"x-axis selector: {args.x_column.upper()}")
    print(f"x-axis column: {x_header}")
    print(f"x-axis label: {axis_label}")
    print(f"y-axis column: X ({RAW_LUMINANCE_COLUMN})")
    print(f"selected rows: {args.start_row}-{args.end_row}")
    print(f"wrote data to {data_path}")
    print(f"wrote gnuplot script to {script_path}")
    print(f"wrote plot to {png_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
