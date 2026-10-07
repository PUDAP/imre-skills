#!/usr/bin/env python3
"""Rotate a calibrated 2-D camera-to-tool offset for one or more robot R values.

Example:
  python rotate_camera_tool_offset.py \
    --center-x 240.5 --center-y -77.5 --r-ref -17.049999 \
    --dx-ref 30.5 --dy-ref 1.0 \
    --r-values -139.169998 -77.43 -17.200001 \
    --csv transformed.csv
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--center-x", type=float, required=True)
    p.add_argument("--center-y", type=float, required=True)
    p.add_argument("--r-ref", type=float, required=True)
    p.add_argument("--dx-ref", type=float, required=True)
    p.add_argument("--dy-ref", type=float, required=True)
    p.add_argument("--r-values", type=float, nargs="+", required=True)
    p.add_argument("--csv", type=Path)
    return p.parse_args()


def transform(a: argparse.Namespace, r: float) -> dict[str, float]:
    theta_deg = r - a.r_ref
    theta = math.radians(theta_deg)
    dx = a.dx_ref * math.cos(theta) - a.dy_ref * math.sin(theta)
    dy = a.dx_ref * math.sin(theta) + a.dy_ref * math.cos(theta)
    return {
        "r_degrees": r,
        "theta_from_reference_degrees": theta_deg,
        "delta_x": dx,
        "delta_y": dy,
        "x": a.center_x + dx,
        "y": a.center_y + dy,
    }


def main() -> None:
    a = parse_args()
    rows = [{"index": i, **transform(a, r)} for i, r in enumerate(a.r_values, 1)]
    result = {
        "calibration": {
            "center_x": a.center_x,
            "center_y": a.center_y,
            "r_ref": a.r_ref,
            "dx_ref": a.dx_ref,
            "dy_ref": a.dy_ref,
        },
        "positions": rows,
    }
    if a.csv:
        a.csv.parent.mkdir(parents=True, exist_ok=True)
        fields = ["index", "r_degrees", "theta_from_reference_degrees", "delta_x", "delta_y", "x", "y"]
        with a.csv.open("w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            for row in rows:
                writer.writerow({k: row[k] if k == "index" else f"{row[k]:.6f}" for k in fields})
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
