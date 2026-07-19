#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import re
import subprocess
from pathlib import Path

# RAW_LUMINANCE_COLUMN = "Raw Luminance"
RAW_LUMINANCE_COLUMN = "Sensor Raw Value"

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
            "Raw Luminance on the y-axis and a selected column on the x-axis."
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
        help="Input CSV path.",
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


def make_point_label(x_header: str, raw_label: str) -> str:
    text = raw_label.strip()
    if x_header == "Shutter":
        return text.replace(" sec", "")
    if x_header == "Aperture":
        if not text.lower().startswith("f/"):
            return f"f/{text}"
        return text
    return text


def make_label_offset(index: int, x_header: str, x_numeric: float, zoom_xmax: float | None = None) -> tuple[float, float]:
    if x_header == "ISO speed":
        if zoom_xmax == 1000.0:
            return 0.0, 0.0

        iso_offsets = {
            100.0: (-95.0, 420.0),
            200.0: (-105.0, 420.0),
            400.0: (-150.0, 380.0),
            800.0: (-150.0, -420.0),
            1600.0: (-190.0, 520.0),
            3200.0: (-190.0, -620.0),
            6400.0: (-200.0, 520.0),
        }
        for key, value in iso_offsets.items():
            if abs(x_numeric - key) < 1e-9:
                return value
        return -80.0, 220.0

    if x_header == "Shutter":
        if zoom_xmax == 0.1:
            dense_zoom_offsets = {
                1: (0.0025, 18.0),
                2: (0.0030, 22.0),
                3: (0.0030, 26.0),
                4: (0.0035, 30.0),
                5: (0.0035, 34.0),
                6: (0.0040, 38.0),
                7: (0.0040, 42.0),
            }
            return dense_zoom_offsets.get(index, (0.0030, 24.0))

        if x_numeric <= 0.1:
            shutter_normal_offsets = {
                0.0166666667: (0.010, 70.0),
                0.0333333333: (0.011, 85.0),
                0.0666666667: (0.012, 105.0),
                0.125: (-0.038, -95.0),
            }
            for key, value in shutter_normal_offsets.items():
                if abs(x_numeric - key) < 1e-6:
                    return value
            return 0.010, 36.0

        if abs(x_numeric - 0.25) < 1e-9:
            return -0.030, -120.0
        if abs(x_numeric - 0.5) < 1e-9:
            return -0.034, -120.0
        if abs(x_numeric - 1.0) < 1e-9:
            return -0.085, -110.0
        return -0.020, -100.0

    if x_header == "Aperture":
        if index <= 5:
            lower_offsets = {
                1: (-0.42, -60.0),
                2: (-0.30, -95.0),
                3: (-0.40, -65.0),
                4: (-0.42, -95.0),
                5: (-0.38, -70.0),
            }
            return lower_offsets[index]
        upper_offsets = {
            6: (-0.45, 55.0),
            7: (-0.55, 55.0),
        }
        return upper_offsets.get(index, (-0.35, 55.0))

    return 0.0, 0.0


def make_axis_step(x_header: str, zoom_xmax: float | None = None) -> float | None:
    if x_header == "Shutter":
        if zoom_xmax == 0.1:
            return 0.01
        return 0.1
    if x_header == "Aperture":
        return 1.0
    if x_header == "ISO speed":
        if zoom_xmax == 1000.0:
            return 100.0
        return 1000.0
    return None


def make_zoom_xmax(x_header: str) -> float | None:
    if x_header == "Shutter":
        return 0.1
    if x_header == "ISO speed":
        return 1000.0
    return None


def make_x_format(x_header: str, zoom_xmax: float | None = None) -> str:
    if x_header == "Shutter":
        if zoom_xmax == 0.1:
            return "%.2f"
        return "%.1f"
    if x_header == "Aperture":
        return "%.0f"
    if x_header == "ISO speed":
        return "%.0f"
    return "%g"


def write_data_file(
    data_path: Path,
    selected_rows: list[dict[str, str]],
    x_header: str,
    keep_order: bool,
    zoom_xmax: float | None = None,
) -> list[dict[str, str | float | int]]:
    plot_rows: list[dict[str, str | float | int]] = []

    for offset, row in enumerate(selected_rows, start=1):
        raw_x_label = row[x_header]
        y_label = row[RAW_LUMINANCE_COLUMN]
        x_numeric = value_to_numeric(x_header, raw_x_label)
        if x_numeric is None:
            x_numeric = float(offset)

        label_dx, label_dy = make_label_offset(offset, x_header, x_numeric, zoom_xmax=zoom_xmax)

        plot_rows.append(
            {
                "index": offset,
                "filename": row["Filename"],
                "raw_x_label": raw_x_label,
                "point_label": make_point_label(x_header, raw_x_label),
                "y_label": y_label,
                "x_sort_value": x_numeric,
                "x_numeric": x_numeric,
                "y_numeric": float(y_label),
                "label_dx": label_dx,
                "label_dy": label_dy,
            }
        )

    if not keep_order:
        plot_rows.sort(key=lambda row: (float(row["x_sort_value"]), int(row["index"])))

    data_path.parent.mkdir(parents=True, exist_ok=True)
    with data_path.open("w", encoding="utf-8", newline="") as fh:
        fh.write("# x_numeric,raw_luminance,point_label,label_dx,label_dy,filename\n")
        for row in plot_rows:
            fh.write(
                f"{float(row['x_numeric']):.10f},"
                f"{row['y_numeric']:.10f},"
                f"{csv_quote(str(row['point_label']))},"
                f"{float(row['label_dx']):.10f},"
                f"{float(row['label_dy']):.10f},"
                f"{csv_quote(str(row['filename']))}\n"
            )
    return plot_rows


def write_gnuplot_script(
    script_path: Path,
    data_path: Path,
    output_png: Path,
    x_header: str,
    axis_label: str,
    plot_rows: list[dict[str, str | float | int]],
    zoom_xmax: float | None = None,
    zoom_ymax: float | None = None,
    label_filter_expr: str | None = None,
) -> None:
    script_path.parent.mkdir(parents=True, exist_ok=True)

    x_values = [float(row["x_numeric"]) for row in plot_rows]
    x_max_data = max(x_values)

    y_values = [float(row["y_numeric"]) for row in plot_rows]
    y_max_data = max(y_values)

    axis_step = make_axis_step(x_header, zoom_xmax=zoom_xmax)

    if zoom_xmax is not None:
        xrange_min = 0.0
        xrange_max = zoom_xmax
    else:
        if axis_step is not None:
            xrange_min = 0.0
            xrange_max = max(axis_step, x_max_data + 0.05 * x_max_data)
        else:
            xrange_min = min(x_values)
            xrange_max = x_max_data

    yrange_min = 0.0
    if zoom_ymax is not None:
        yrange_max = zoom_ymax
    else:
        yrange_max = max(1.0, y_max_data * 1.12)

    xtics_cmd = "set xtics autofreq"
    if axis_step is not None:
        tic_end = xrange_max + axis_step * 0.001
        xtics_cmd = f"set xtics 0, {axis_step}, {tic_end}"

    x_format = make_x_format(x_header, zoom_xmax=zoom_xmax)

    if x_header == "Shutter":
        point_font = ",20"
    else:
        point_font = ",22"

    if label_filter_expr is None:
        labels_plot = (
            f"'' using (column(1)+column(4)):(column(2)+column(5)):(stringcolumn(3)) with labels font '{point_font}' notitle"
        )
    else:
        labels_plot = (
            f"'' using ({label_filter_expr} ? (column(1)+column(4)) : 1/0):"
            f"({label_filter_expr} ? (column(2)+column(5)) : 1/0):"
            f"(stringcolumn(3)) with labels font '{point_font}' notitle"
        )

    script = f"""set datafile separator comma
set terminal pngcairo size 1600,1000 enhanced font 'Arial,28'
set output '{gnuplot_escape(str(output_png))}'

unset title
set xlabel '{gnuplot_escape(axis_label)}' font ',30'
set ylabel 'Raw Luminance' font ',30'

set grid xtics ytics
set key off
set border lw 1.5

set xtics font ',24'
set ytics font ',24'
set format x '{x_format}'
{xtics_cmd}

set xrange [{xrange_min}:{xrange_max}]
set yrange [{yrange_min}:{yrange_max}]
set offsets 0.02,0.02,0.05,0.10

plot '{gnuplot_escape(str(data_path))}' using 1:2 with linespoints lw 3 pt 7 ps 1.8, \\
     {labels_plot}
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

    normal_plot_rows = write_data_file(data_path, selected_rows, x_header, args.keep_order)

    normal_zoom_ymax = None
    normal_label_filter_expr = "0"

    write_gnuplot_script(
        script_path,
        data_path,
        png_path,
        x_header,
        axis_label,
        normal_plot_rows,
        zoom_ymax=normal_zoom_ymax,
        label_filter_expr=normal_label_filter_expr,
    )
    subprocess.run(["gnuplot", str(script_path)], check=True)

    zoom_xmax = make_zoom_xmax(x_header)
    zoom_script_path: Path | None = None
    zoom_png_path: Path | None = None

    if zoom_xmax is not None:
        zoom_stem = sanitize_token(
            f"rows_{args.start_row}_{args.end_row}_{args.x_column.upper()}_{x_header}_x0_{str(zoom_xmax).replace('.', '_')}"
        )
        zoom_script_path = output_dir / f"{zoom_stem}.gp"
        zoom_png_path = output_dir / f"{zoom_stem}.png"

        zoom_ymax = None
        if x_header == "Shutter" and zoom_xmax == 0.1:
            zoom_ymax = 400.0
        if x_header == "ISO speed" and zoom_xmax == 1000.0:
            zoom_ymax = 15000.0

        zoom_data_path = output_dir / f"{zoom_stem}.csv"
        zoom_plot_rows = write_data_file(
            zoom_data_path,
            selected_rows,
            x_header,
            args.keep_order,
            zoom_xmax=zoom_xmax,
        )

        zoom_label_filter_expr = "0"

        write_gnuplot_script(
            zoom_script_path,
            zoom_data_path,
            zoom_png_path,
            x_header,
            axis_label,
            zoom_plot_rows,
            zoom_xmax=zoom_xmax,
            zoom_ymax=zoom_ymax,
            label_filter_expr=zoom_label_filter_expr,
        )
        subprocess.run(["gnuplot", str(zoom_script_path)], check=True)

    print(f"x-axis selector: {args.x_column.upper()}")
    print(f"x-axis column: {x_header}")
    print(f"x-axis label: {axis_label}")
    print(f"y-axis column: {RAW_LUMINANCE_COLUMN}")
    print(f"selected rows: {args.start_row}-{args.end_row}")
    print(f"wrote data to {data_path}")
    print(f"wrote gnuplot script to {script_path}")
    print(f"wrote plot to {png_path}")
    if zoom_script_path is not None and zoom_png_path is not None:
        print(f"wrote zoom data to {zoom_data_path}")
        print(f"wrote zoom gnuplot script to {zoom_script_path}")
        print(f"wrote zoom plot to {zoom_png_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())