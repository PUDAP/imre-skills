# Registering tabular robot labware coordinates

Use this procedure when an operator supplies a CSV/table of named robot deck positions and asks to register it as reusable labware without requesting motion.

## Registration workflow

1. Treat registration as data persistence, not implicit robot movement. Do not move the robot merely to recreate supplied coordinates.
2. Preserve the original bytes under the project with a stable UUID-backed filename and calculate SHA-256. Record the original filename and delivery source separately.
3. Parse and validate before writing the labware definition:
   - exact required headers and declared units;
   - numeric conversion for every coordinate;
   - unique, non-empty position labels;
   - expected row count and any grid naming convention;
   - exact round-trip equality between source rows and normalized JSON positions.
4. Create a UUID-backed JSON artifact under `labware/` with at least:
   - `schema_version`, `labware_id`, stable `label`, `display_name`, and `labware_type`;
   - `machine_id`, `coordinate_frame`, `coordinate_order`, and per-axis units;
   - complete named `positions` with preserved numeric precision;
   - grid wells and special/non-grid positions listed separately when applicable;
   - operator identity, recorded timestamp, source path/hash, and notes;
   - explicit verification status.
5. Mark operator-supplied coordinates as `operator_supplied_unverified` and `controller_verified: false` unless an exact independent controller measurement exists for each position. Authorization to store or later use coordinates is not controller verification.
6. Add a `## Labware` entry to `project.md` linking both JSON and preserved CSV, then append a timestamped history entry. State position count, machine/frame scope, source hash, and that no motion occurred.
7. Re-read the JSON, verify both referenced files exist, recompute the CSV hash, and assert labels/order/coordinates round-trip exactly.

## Operational use

- Resolve future named-well commands from the UUID-backed labware artifact, not chat text or a copied table.
- Treat coordinates as geometry, not occupancy evidence. Before low-Z placement, stage at a safe inspection height and verify the named destination is empty. If it is occluded or possibly occupied, pause for operator confirmation or select another well.
- Keep machine scope explicit: similarly named wells on another robot, rack, or coordinate frame are different locations.
- When a later calibration changes values, create a new UUID artifact and record supersession rather than overwriting provenance.

### Paired CSV/JSON divergence before motion

Some legacy projects may contain a CSV and JSON with the **same labware UUID** but different coordinates because an approved table revision updated only one representation. A matching UUID or filename stem does not prove the pair is synchronized. Before authoring any named-well motion:

1. Read the requested row from every live paired representation and compare all axes numerically.
2. Check `project.md`, revision notes, backups, timestamps, hashes, and explicit approval evidence to identify which artifact records the latest approved geometry; do not choose JSON merely because it is structured, or CSV merely because it is newer.
3. If the active source is unambiguous, cite that exact file and resolved coordinates in the new protocol and run history, and record that the broad image cannot independently prove fine well alignment.
4. If provenance is ambiguous, stop before motion and ask the operator which geometry is active.
5. After the immediate operation, reconcile the split by creating a fresh UUID-backed revision with synchronized CSV/JSON and an explicit supersession link. Do not silently rewrite the stale companion because that destroys evidence of the divergence.

This is a legacy-reconciliation exception, not permission to maintain two mutable sources of truth. New revisions must keep all paired representations synchronized and hash-linked.

## Calibration revision workflow

When the operator supplies an updated table for an existing label:

1. Preserve the new CSV bytes and hash independently; do not replace the prior CSV or JSON.
2. Create a fresh labware UUID with the same stable label and an explicit `supersedes_labware_id` link to the prior artifact.
3. Compare old and new positions field-by-field. Report changed labels and axes, and assert expected unchanged values—not merely the new row count.
4. In `project.md`, mark the new UUID **Active** and the prior UUID **Superseded**, with links and both source hashes. Future named-well motion must resolve from the active entry. When the operator explicitly says “use these coordinates for future picks,” also persist a compact active-geometry fact when needed to prevent a superseded low-Z pick depth from being reused; keep the UUID artifact and `project.md` as the full source of truth rather than copying the whole table into memory.
5. Keep historical protocols unchanged: their embedded coordinates are execution provenance, not live aliases that should be rewritten after recalibration. In every newly authored protocol, cite the active labware UUID and resolved source Z so review can catch stale-depth reuse.
6. Re-read both revisions and verify that the source CSV hash, labels/order, normalized coordinates, supersession link, and active/superseded project links are internally consistent.
7. Continue to mark the revision `operator_supplied_unverified` unless every updated pose was independently measured; registration alone issues no robot motion.

If a calibration correction follows a controller-successful but physically bad placement, preserve the failure evidence and do not retry with the superseded depth. Clear the physical obstruction first, then use only the new active revision for subsequent reviewed motion.

## Rebuilding a rectangular grid from revised corner probes

Use this when an operator explicitly approves two opposite grid corners (for example `A1` and `D6`) and asks to calculate the remaining wells of an `R × C` rectangular grid.

1. Confirm the geometry convention before interpolation. When the operator says **rectangular grid** and supplies only opposite corners, the determinate default is an axis-aligned grid in the robot frame: X varies by column, Y varies by row, and Z/R interpolate only if the endpoints differ and the operator requests that behavior. If a rotated or skewed grid is plausible, two corners are underdetermined; require a third corner or explicit basis vectors rather than inventing orientation.
2. Compute pitches from the approved endpoints:
   - `dx = (X_last − X_first) / (C − 1)`
   - `dy = (Y_last − Y_first) / (R − 1)`
   - `X(row, col) = X_first + col_index × dx`
   - `Y(row, col) = Y_first + row_index × dy`
   Preserve the operator-approved Z/R exactly when they are constant.
3. Treat exploratory sub-millimetre moves as probes only. Do not update the active table until the operator explicitly labels coordinates as revised/approved. The last probe is not automatically the calibration.
4. Before editing, preserve a timestamped byte-for-byte backup of the current active labware file. Keep non-grid/special rows such as `CAP` unchanged unless the operator explicitly revises them.
5. Replace the full grid deterministically rather than hand-editing individual cells. Preserve schema/header order and use enough decimal precision for repeating pitches.
6. Re-read and mechanically verify:
   - exact expected well set and count;
   - exact approved first and last corners;
   - constant pitch across every adjacent column and row;
   - constant X down each column and constant Y across each row for an axis-aligned grid;
   - preserved Z/R and untouched special rows.
7. Report the assumption, computed pitches, active file path, backup path, and verification result. Do not imply that calculated intermediate wells were individually controller-measured.
8. If the project also maintains UUID-backed JSON labware records and `project.md` active/superseded links, create a new revision and supersession record rather than leaving the edited CSV as an untracked calibration fork. Historical protocols remain unchanged provenance.

### Worked opposite-corner example (non-authoritative session evidence)

An operator approved a 4×6 M1Pro centrifuge-tube MTP revision with opposite corners:

- `A1 = [131.8, -231.5, 9, -22.5]`
- `D6 = [32.5, -170.5, 9, -22.5]`

Under the explicit axis-aligned rectangular-grid assumption, the deterministic pitches were:

- column X pitch: `(32.5 - 131.8) / 5 = -19.86 mm`
- row Y pitch: `(-170.5 - -231.5) / 3 = 20.333333333… mm`

The active CSV retained its separate `CAP` row unchanged, replaced all 24 grid wells, and passed checks for exact corner recovery, the complete `A1:D6` label set, constant X down columns, constant Y across rows, uniform pitch, and constant `Z=9`, `R=-22.5`. A timestamped byte-for-byte backup was created before replacement.

After that approved edit, the operator requested several small A6-area Cartesian moves (`X=32.0`, `31.5`, `31.2`, then back toward `32.3`) without saying that any probe superseded the approved table. Those motions remain **probe evidence only**. Do not infer a second calibration change from the last reached endpoint or silently rewrite A6. Require an explicit statement such as “these are the revised coordinates” or “update the labware file” before persisting another revision.

This example is provenance and a validation pattern, not a permanent source of live coordinates. Future motion must still resolve the currently active labware artifact.
