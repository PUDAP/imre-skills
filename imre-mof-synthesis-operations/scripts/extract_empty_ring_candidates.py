#!/usr/bin/env python3
"""Extract continuity-direction-filtered center crossings from a fresh ring-scan Hough JSON.

The input is a JSON array whose rows contain `r` and `closest=[x,y,radius]`.
This script does not replace visual same-ring QA; it rejects obvious nearest-circle
handoff crossings and enforces the expected holder count before refinement.
"""

import argparse
import csv
import json
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="Fresh-scan Hough JSON")
    ap.add_argument("--output", required=True, help="Candidate CSV to create")
    ap.add_argument("--center-x", type=float, default=320.0)
    ap.add_argument("--expected-count", type=int, default=6)
    ap.add_argument(
        "--direction",
        choices=("decreasing", "increasing"),
        default="decreasing",
        help="Expected same-ring x motion as scan R increases; establish from fresh frames",
    )
    args = ap.parse_args()

    rows = sorted(json.loads(Path(args.input).read_text()), key=lambda row: float(row["r"]))
    candidates = []
    for left, right in zip(rows, rows[1:]):
        if not left.get("closest") or not right.get("closest"):
            continue
        r0, r1 = float(left["r"]), float(right["r"])
        x0, x1 = float(left["closest"][0]), float(right["closest"][0])
        slope_ok = x1 < x0 if args.direction == "decreasing" else x1 > x0
        crosses = (x0 - args.center_x) * (x1 - args.center_x) <= 0
        if not (slope_ok and crosses and x1 != x0):
            continue
        predicted = r0 + (args.center_x - x0) * (r1 - r0) / (x1 - x0)
        candidates.append((predicted, r0, x0, r1, x1))

    if len(candidates) != args.expected_count:
        raise SystemExit(
            f"Refusing output: found {len(candidates)} direction-preserving crossings; "
            f"expected {args.expected_count}. Inspect fresh frames and detector identity handoffs."
        )

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(
            ["holder", "predicted_r", "left_angle", "left_x", "right_angle", "right_x", "derivation"]
        )
        for holder, (predicted, r0, x0, r1, x1) in enumerate(candidates, 1):
            writer.writerow(
                [
                    holder,
                    f"{predicted:.9f}",
                    f"{r0:.6f}",
                    f"{x0:.3f}",
                    f"{r1:.6f}",
                    f"{x1:.3f}",
                    f"fresh adjacent coarse-frame interpolation; {args.direction} same-ring x motion",
                ]
            )

    print(f"wrote {len(candidates)} candidates to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
