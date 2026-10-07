# MOF affine centrifuge-tube MTP calibration

Use this when recalculating the 4×6 M1Pro centrifuge-tube MTP from measured wells.

## Do not infer an axis-aligned grid from two diagonal corners

Two opposite corners do not determine grid orientation or row drift. Prefer three measured points that span both grid basis directions, for example `A1`, `A6`, and `D6`.

For zero-based column index `c=0..5` and row index `r=0..3`:

```text
column_vector = (A6 - A1) / 5
row_vector    = (D6 - A6) / 3
well(r,c)     = A1 + c*column_vector + r*row_vector
```

Apply the formula independently to X and Y. Preserve calibrated Z and R unless the operator explicitly revises them. This is an affine/parallelogram grid and retains small measured angular/skew drift.

## Current MOF reference example

```text
A1 = [131.8,      -231.5, 9, -22.5]
A6 = [32.299999,  -231.5, 9, -22.5]
D6 = [32.5,       -170.5, 9, -22.5]

column_vector = [-19.9000002, 0]
row_vector    = [  0.0666670, 20.3333333333]
```

## Update procedure

1. Resolve the authoritative active artifact from project provenance before reading coordinates. Sibling CSV and JSON files with the same labware UUID can diverge after an approved affine revision; matching UUIDs do **not** prove matching geometry. Compare their coordinates and timestamps/hashes, follow the project record that names the deployed/current source, and never silently combine X/Y from one sibling with Z/R or labels from another.
2. Read the authoritative labware table and preserve non-grid rows such as `CAP`.
3. Create a timestamped backup before overwriting.
4. Generate all 24 wells from the affine formula; do not hand-edit individual intermediate wells.
5. Verify exact recovery of all three measured anchors.
6. Verify every adjacent column difference equals `column_vector` and every adjacent row difference equals `row_vector` within floating-point tolerance.
7. Verify 24 unique wells, constant intended Z/R, and unchanged non-grid rows.
8. After any revision, update or regenerate sibling representations deliberately and verify coordinate equality. If a stale sibling is intentionally retained for provenance, label it non-authoritative so later motion authoring cannot mistake it for the active table.

Do not move the robot merely to validate the table; perform robot moves only when separately requested and safety-gated.
