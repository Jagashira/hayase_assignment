#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path


COLORS = (
    "#E69F00",
    "#56B4E9",
    "#009E73",
    "#D55E00",
    "#0072B2",
    "#CC79A7",
    "#000000",
)


@dataclass
class ComsolTable:
    path: Path
    headers: list[str]
    rows: list[list[float]]


@dataclass
class PlotSeries:
    table: ComsolTable
    label: str
    data_path: Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Plot one or more COMSOL text exports with gnuplot. "
            "Columns may be selected by 1-based index or by header name."
        )
    )
    parser.add_argument("inputs", nargs="+", help="COMSOL .txt/.dat files to plot.")
    parser.add_argument("--output", "-o", help="Output PNG path.")
    parser.add_argument(
        "--script-output",
        help="Output gnuplot script path. Defaults to the PNG path with .gp suffix.",
    )
    parser.add_argument(
        "--work-dir",
        default="gnuplot/output/comsol",
        help="Directory for generated intermediate data files.",
    )
    parser.add_argument("--x", default="1", help="X column name or 1-based column number.")
    parser.add_argument("--y", default="4", help="Y column name or 1-based column number.")
    parser.add_argument("--labels", nargs="+", help="Series labels, one per input file.")
    parser.add_argument("--title", default="", help="Graph title.")
    parser.add_argument("--xlabel", help="X-axis label. Defaults to selected x column.")
    parser.add_argument("--ylabel", help="Y-axis label. Defaults to selected y column.")
    parser.add_argument("--x-scale", type=float, default=1.0, help="Multiplier applied to x values.")
    parser.add_argument("--y-scale", type=float, default=1.0, help="Multiplier applied to y values.")
    parser.add_argument("--x-offset", type=float, default=0.0, help="Value subtracted from x after scaling.")
    parser.add_argument("--y-offset", type=float, default=0.0, help="Value subtracted from y after scaling.")
    parser.add_argument(
        "--center-x",
        action="store_true",
        help="Shift each series so the midpoint of its x range becomes x=0.",
    )
    parser.add_argument(
        "--center-y",
        action="store_true",
        help="Shift each series so the midpoint of its y range becomes y=0.",
    )
    parser.add_argument(
        "--sort-x",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Sort points by x value before plotting.",
    )
    parser.add_argument(
        "--style",
        choices=("lines", "points", "linespoints"),
        default="lines",
        help="gnuplot drawing style.",
    )
    parser.add_argument("--xrange", help="gnuplot x range, e.g. -0.2:0.2.")
    parser.add_argument("--yrange", help="gnuplot y range, e.g. 0:30.")
    parser.add_argument(
        "--vline",
        action="append",
        type=float,
        default=[],
        help="Draw a vertical reference line at this x value. May be repeated.",
    )
    parser.add_argument(
        "--key",
        default="best",
        help="gnuplot key position, e.g. 'bottom right', 'top left', or 'off'.",
    )
    parser.add_argument("--width", type=int, default=1600, help="PNG width in pixels.")
    parser.add_argument("--height", type=int, default=1000, help="PNG height in pixels.")
    parser.add_argument("--font", default="Arial,30", help="gnuplot terminal font.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Write data and gnuplot script without running gnuplot.",
    )
    return parser


def gnuplot_quote(text: str) -> str:
    return text.replace("\\", "\\\\").replace("'", "\\'")


def sanitize_token(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", text.strip()).strip("_") or "series"


def split_header(line: str) -> list[str]:
    text = line.strip()
    if text.startswith("%"):
        text = text[1:].strip()
    return [part.strip() for part in re.split(r"\s{2,}", text) if part.strip()]


def parse_numeric_row(line: str) -> list[float] | None:
    text = line.strip()
    if not text:
        return None
    parts = text.split()
    try:
        return [float(part) for part in parts]
    except ValueError:
        return None


def load_comsol_table(path: Path) -> ComsolTable:
    headers: list[str] | None = None
    rows: list[list[float]] = []

    with path.open(encoding="utf-8") as fh:
        for line in fh:
            numeric_row = parse_numeric_row(line)
            if numeric_row is not None:
                rows.append(numeric_row)
                continue

            stripped = line.strip()
            if stripped.startswith("%"):
                candidate = split_header(stripped)
                if len(candidate) >= 2 and candidate[0].lower() in {"x", "r", "time"}:
                    headers = candidate

    if not rows:
        raise SystemExit(f"no numeric rows found in {path}")

    column_count = len(rows[0])
    if any(len(row) != column_count for row in rows):
        raise SystemExit(f"inconsistent numeric column count in {path}")

    if headers is None or len(headers) != column_count:
        headers = [f"col{i}" for i in range(1, column_count + 1)]

    return ComsolTable(path=path, headers=headers, rows=rows)


def resolve_column(selector: str, headers: list[str]) -> int:
    text = selector.strip()
    if text.isdigit():
        index = int(text) - 1
        if index < 0 or index >= len(headers):
            raise SystemExit(f"column index {text} is out of range 1-{len(headers)}")
        return index

    normalized = text.casefold()
    for index, header in enumerate(headers):
        if header.casefold() == normalized:
            return index

    matches = [index for index, header in enumerate(headers) if normalized in header.casefold()]
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        names = ", ".join(headers[index] for index in matches)
        raise SystemExit(f"column selector {selector!r} matched multiple columns: {names}")

    raise SystemExit(f"column selector {selector!r} was not found. Headers: {', '.join(headers)}")


def make_default_output(inputs: list[Path], y_label: str) -> Path:
    if len(inputs) == 1:
        stem = inputs[0].stem
    else:
        stem = f"{inputs[0].stem}_compare"
    return Path("gnuplot/output/comsol") / f"{sanitize_token(stem)}_{sanitize_token(y_label)}.png"


def make_series_labels(inputs: list[Path], labels: list[str] | None) -> list[str]:
    if labels is None:
        return [path.stem for path in inputs]
    if len(labels) != len(inputs):
        raise SystemExit(f"--labels needs {len(inputs)} values, got {len(labels)}")
    return labels


def write_series_data(
    table: ComsolTable,
    data_path: Path,
    x_index: int,
    y_index: int,
    x_scale: float,
    y_scale: float,
    x_offset: float,
    y_offset: float,
    center_x: bool,
    center_y: bool,
    sort_x: bool,
) -> None:
    points = [
        (row[x_index] * x_scale, row[y_index] * y_scale)
        for row in table.rows
    ]

    if center_x:
        xs = [point[0] for point in points]
        x_offset += (min(xs) + max(xs)) / 2.0
    if center_y:
        ys = [point[1] for point in points]
        y_offset += (min(ys) + max(ys)) / 2.0

    adjusted = [(x - x_offset, y - y_offset) for x, y in points]
    if sort_x:
        adjusted.sort(key=lambda point: point[0])

    data_path.parent.mkdir(parents=True, exist_ok=True)
    with data_path.open("w", encoding="utf-8") as fh:
        fh.write("# x y\n")
        for x, y in adjusted:
            fh.write(f"{x:.12g} {y:.12g}\n")


def write_gnuplot_script(
    script_path: Path,
    output_path: Path,
    series: list[PlotSeries],
    title: str,
    xlabel: str,
    ylabel: str,
    style: str,
    key: str,
    width: int,
    height: int,
    font: str,
    xrange: str | None,
    yrange: str | None,
    vlines: list[float],
) -> None:
    script_path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        f"set terminal pngcairo size {width},{height} enhanced font '{gnuplot_quote(font)}'",
        f"set output '{gnuplot_quote(str(output_path))}'",
        "set border lw 2",
        "set grid",
        "set tics font ',28'",
        f"set xlabel '{gnuplot_quote(xlabel)}' font ',38' offset 0,0.8",
        f"set ylabel '{gnuplot_quote(ylabel)}' font ',38' offset 1.5,0",
    ]

    if title:
        lines.append(f"set title '{gnuplot_quote(title)}'")
    else:
        lines.append("unset title")

    if key.casefold() == "off":
        lines.append("unset key")
    elif key.casefold() == "best":
        lines.append("set key outside right top font ',24'")
    else:
        lines.append(f"set key {key} font ',24'")

    if xrange:
        lines.append(f"set xrange [{xrange}]")
    if yrange:
        lines.append(f"set yrange [{yrange}]")

    for index, x_value in enumerate(vlines, start=1):
        lines.append(
            f"set arrow {index} from {x_value}, graph 0 to {x_value}, graph 1 "
            "nohead dt 2 lw 2 lc rgb 'black'"
        )

    plot_parts = []
    for index, item in enumerate(series):
        color = COLORS[index % len(COLORS)]
        point_options = " pt 7 ps 1.4" if style in {"points", "linespoints"} else ""
        plot_parts.append(
            f"'{gnuplot_quote(str(item.data_path))}' using 1:2 with {style} "
            f"lc rgb '{color}' lw 4{point_options} title '{gnuplot_quote(item.label)}'"
        )
    lines.append("plot " + ", \\\n     ".join(plot_parts))
    lines.append("set output")

    script_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    inputs = [Path(item) for item in args.inputs]
    for path in inputs:
        if not path.exists():
            raise SystemExit(f"missing input file: {path}")

    tables = [load_comsol_table(path) for path in inputs]
    x_index = resolve_column(args.x, tables[0].headers)
    y_index = resolve_column(args.y, tables[0].headers)
    x_label = args.xlabel or tables[0].headers[x_index]
    y_label = args.ylabel or tables[0].headers[y_index]

    for table in tables[1:]:
        if x_index >= len(table.headers) or y_index >= len(table.headers):
            raise SystemExit(f"{table.path} does not have the selected columns")

    output_path = Path(args.output) if args.output else make_default_output(inputs, y_label)
    script_path = Path(args.script_output) if args.script_output else output_path.with_suffix(".gp")
    work_dir = Path(args.work_dir)
    labels = make_series_labels(inputs, args.labels)

    plot_series: list[PlotSeries] = []
    for table, label in zip(tables, labels, strict=True):
        data_path = work_dir / f"{sanitize_token(output_path.stem)}_{sanitize_token(label)}.dat"
        write_series_data(
            table=table,
            data_path=data_path,
            x_index=x_index,
            y_index=y_index,
            x_scale=args.x_scale,
            y_scale=args.y_scale,
            x_offset=args.x_offset,
            y_offset=args.y_offset,
            center_x=args.center_x,
            center_y=args.center_y,
            sort_x=args.sort_x,
        )
        plot_series.append(PlotSeries(table=table, label=label, data_path=data_path))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    write_gnuplot_script(
        script_path=script_path,
        output_path=output_path,
        series=plot_series,
        title=args.title,
        xlabel=x_label,
        ylabel=y_label,
        style=args.style,
        key=args.key,
        width=args.width,
        height=args.height,
        font=args.font,
        xrange=args.xrange,
        yrange=args.yrange,
        vlines=args.vline,
    )

    if not args.dry_run:
        subprocess.run(["gnuplot", str(script_path)], check=True)

    print(f"x column: {tables[0].headers[x_index]}")
    print(f"y column: {tables[0].headers[y_index]}")
    print(f"wrote gnuplot script: {script_path}")
    print(f"wrote plot: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
