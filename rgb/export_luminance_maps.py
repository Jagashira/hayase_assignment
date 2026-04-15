#!/usr/bin/env python3

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

from PIL import Image


def normalize(value: float, min_value: float, max_value: float) -> int:
    if max_value <= min_value:
        return 0
    scaled = (value - min_value) / (max_value - min_value)
    return max(0, min(255, round(scaled * 255)))


def percentile(sorted_values: list[float], ratio: float) -> float:
    if not sorted_values:
        return 0.0
    if len(sorted_values) == 1:
        return float(sorted_values[0])
    position = ratio * (len(sorted_values) - 1)
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return float(sorted_values[lower])
    blend = position - lower
    return sorted_values[lower] * (1.0 - blend) + sorted_values[upper] * blend


def clip(value: float, low: float, high: float) -> float:
    return min(max(value, low), high)


def write_map(path: str, width: int, height: int, values: list[int]) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        for y in range(height):
            row_start = y * width
            for x in range(width):
                fh.write(f"{x} {y} {values[row_start + x]}\n")
            fh.write("\n")


def main() -> int:
    if len(sys.argv) != 9:
        print(
            "Usage: export_luminance_maps.py input_image "
            "sum_fair.dat weighted_fair.dat diff_signed.dat "
            "weighted_minmax.dat weighted_percentile.dat weighted_gamma.dat stats.json",
            file=sys.stderr,
        )
        return 1

    (
        _script,
        input_image,
        sum_fair_path,
        weighted_fair_path,
        diff_signed_path,
        weighted_minmax_path,
        weighted_percentile_path,
        weighted_gamma_path,
        stats_path,
    ) = sys.argv

    image = Image.open(input_image).convert("RGB")
    width, height = image.size
    pixels = list(image.getdata())

    sum_values = [r + g + b for r, g, b in pixels]
    weighted_values = [0.299 * r + 0.587 * g + 0.114 * b for r, g, b in pixels]

    global_min = min(min(sum_values), min(weighted_values))
    global_max = max(max(sum_values), max(weighted_values))
    sum_fair = [normalize(v, global_min, global_max) for v in sum_values]
    weighted_fair = [normalize(v, global_min, global_max) for v in weighted_values]

    diff_raw = [s - w for s, w in zip(sum_values, weighted_values)]
    diff_abs_max = max(abs(min(diff_raw)), abs(max(diff_raw)))
    if diff_abs_max == 0:
        diff_signed = [128 for _ in diff_raw]
    else:
        diff_signed = [
            max(0, min(255, round(128 + (value / diff_abs_max) * 127)))
            for value in diff_raw
        ]

    weighted_min = min(weighted_values)
    weighted_max = max(weighted_values)
    weighted_minmax = [normalize(v, weighted_min, weighted_max) for v in weighted_values]

    weighted_sorted = sorted(weighted_values)
    pct_low = percentile(weighted_sorted, 0.01)
    pct_high = percentile(weighted_sorted, 0.99)
    weighted_percentile = [
        normalize(clip(v, pct_low, pct_high), pct_low, pct_high)
        for v in weighted_values
    ]

    gamma = 2.2
    weighted_gamma = [
        max(0, min(255, round(((value / 255.0) ** (1.0 / gamma)) * 255)))
        for value in weighted_percentile
    ]

    write_map(sum_fair_path, width, height, sum_fair)
    write_map(weighted_fair_path, width, height, weighted_fair)
    write_map(diff_signed_path, width, height, diff_signed)
    write_map(weighted_minmax_path, width, height, weighted_minmax)
    write_map(weighted_percentile_path, width, height, weighted_percentile)
    write_map(weighted_gamma_path, width, height, weighted_gamma)

    stats = {
        "input_image": str(Path(input_image)),
        "width": width,
        "height": height,
        "global_min": global_min,
        "global_max": global_max,
        "weighted_min": weighted_min,
        "weighted_max": weighted_max,
        "weighted_percentile_low": pct_low,
        "weighted_percentile_high": pct_high,
        "diff_min": min(diff_raw),
        "diff_max": max(diff_raw),
        "diff_abs_max": diff_abs_max,
        "gamma": gamma,
    }
    Path(stats_path).write_text(
        json.dumps(stats, indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
