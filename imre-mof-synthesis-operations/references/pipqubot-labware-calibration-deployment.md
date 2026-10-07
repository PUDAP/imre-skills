# PipQuBot Labware Calibration Deployment

Use this pattern when an operator edits a PipQuBot labware JSON and asks to validate and deploy it.

## Validation

1. Compare source directly with the running container copy and record both SHA-256 hashes. Report exact field changes; preserve operator-entered calibration values rather than silently normalizing them.
2. Parse JSON and load it through the same runtime `StandardLabware` class used by the edge.
3. Validate the whole definition:
   - expected well count and exact ordering membership,
   - unique XY coordinates,
   - finite numeric fields,
   - positive dimensions, depth, diameter, and volume,
   - `well.z + well.depth <= zDimension`,
   - each circular well footprint remains inside the declared labware footprint (`diameter/2 <= x <= xDimension - diameter/2` and likewise for Y),
   - transformed coordinates for **every** well and both software tip states remain within configured machine limits.
4. Calculate transformed coordinates for representative first/last wells, coordinate extrema, and both software tip states. In the current driver:
   - no tip: `Z = zDimension - CEILING_HEIGHT`
   - attached tip: `Z = zDimension - CEILING_HEIGHT + TIP_LENGTH`
5. Uniform raw-well changes do not necessarily map to the same machine axis. Compute through the current `PipQuBotMOF` coordinate function rather than reasoning from the JSON alone. Under the current MOF orientation, raw X contributes to machine Y and mirrored raw Y contributes to machine X. For a **uniform translation of every well**, the observed signed mapping is:
   - raw `ΔX` → machine `ΔY` with the same sign,
   - raw `ΔY` → machine `ΔX` with the same sign, because the mirrored-axis minimum, maximum, and well coordinate translate together.
   This signed shortcut is useful for reporting the operator's calibration delta, but the driver calculation remains authoritative—especially for non-uniform edits.
6. Compare all transformed extrema against the limits reported by the instantiated controller, not copied historical limits. Check both software tip branches even when the operator currently has no physical tip.
7. If an intentional calibration change makes only a coordinate regression stale, update its expected value. Never modify production calibration merely to satisfy a stale test.
8. Treat labware identifier deletion or rename as an API migration, not merely a file change. Search source, the entire test suite, examples, project protocols, and persisted deck layouts for the old identifier. Deletion is blocking until either (a) a compatibility alias remains, or (b) every caller is deliberately migrated and historical protocols are clearly marked non-runnable. Do not make tests green by renaming only the failing fixtures while leaving runtime callers or saved protocols broken.
9. Require `insert_depth` when the definition can be used by depth-based operations such as attach, aspirate, or dispense. If a trash-only definition intentionally omits it, document and test that command-surface restriction; successful `drop_tip` loading alone does not establish general labware compatibility.
10. Run targeted orientation, identity, serial, and movement tests **and the complete driver test suite**, plus JSON parsing, compilation, `git diff --check`, and Compose validation. Labware files may be untracked, so do not rely on `git diff` as the source/live comparison; compare directly with the running container copy.
11. For a safety-sensitive calibration, wait for the independent review verdict before activation. An asynchronous review still running is an incomplete gate: do not deploy merely because focused tests passed. A reviewer blocker discovered after activation requires an immediate stop on further motion and explicit remediation or rollback before calling the calibration validated.
12. A transformed target being numerically inside the configured limits is necessary but not sufficient. Report clearance to every nearest limit; targets with only a small margin require explicit operator acceptance and fresh visual/physical clearance evidence before movement.

## Build and activation

1. Build the edge image and inspect its labware hash, runtime load, well count, coordinates, and command surface before activation. Build may proceed while review is running, but activation must wait for all review and test gates.
2. Treat recreation as physical motion: startup performs full gantry home and Sartorius initialization.
3. Before activation require idle state, no active run, empty NATS command consumers, and a fresh camera frame with no visible person, head, hands, or obvious obstruction inside the enclosure. Treat any visible body part inside the enclosure as a hard stop: do not dispatch home or recreation, confirm the machine remains idle, and require a new fresh frame after the operator clears the area. A previous clear frame is not sufficient for a retry.
4. Monitor startup through controller-acknowledged home, Sartorius initialization, NATS readiness, and idle-state publication.
5. Verify live hash and coordinates exactly match source and built image. Require running/healthy, zero restarts, idle/no run, empty queues, and expected logical-deck reset.
6. Do not perform a live well move merely to prove deployment. Record hashes, image ID, coordinate delta, tests, startup result, and final state in `project.md`.

## Post-deployment named-well moves

1. Edge recreation resets the logical deck and software tip flag. For the first named-well move after deployment, use a validated `load_labware` + `move_to_well` protocol so the slot is restored logically and coordinates are resolved dynamically from the live definition.
2. Do not insert a redundant `home` into every short positioning protocol when startup homing and Sartorius initialization were already controller-verified and the live machine is idle. For an explicit home request, use `puda machine home pipqubot_mof` directly after the same state/queue/camera preflight.
3. Reuse an existing well protocol when available. If a requested well has no protocol yet, create one class-consistent two-step protocol (`load_labware`, then existing `move_to_well`), validate it, and immediately register it in `project.md` before running.
4. Before each run, refresh state and both NATS consumers and capture a new camera frame; a clear frame from deployment or a previous move is not reusable safety evidence.
5. If the deployed definition violates a geometry invariant (for example, `well.z + depth` differs from or exceeds `zDimension`) or leaves only a small axis-limit margin, stop before motion and show the operator the exact transformed alternatives and clearances. Proceed only after the operator explicitly selects the intended deployed interpretation or chooses correction/redeployment; record that choice with the run. Do not silently choose a Z plane from the filename, display name, or well depth.
6. After each run, verify the response coordinates and controller sequence (`safe Z -> required lateral axes -> final Z`). A controller may omit an unchanged lateral axis, which is expected; report the axes actually emitted rather than inventing a full XY move.
7. Verify idle/no-run, edge health, restart count, empty queues, and logical labware slot after the run. Record the run ID, final coordinates, and post-motion image in project memory.

## Geometry and tip-state pitfalls

- `move_to_well` uses `zDimension` as its target plane. Individual `well.z + depth` can describe a lower plate-only plane; report the gap explicitly rather than guessing which is wrong.
- Startup/home/recreation can clear the software tip flag but cannot physically eject a disposable tip.
- Block named-well motion when a physical tip is attached but software says no tip: the driver will choose the no-tip Z branch and may descend dangerously. Do not recover by performing another pickup.
- After operator-confirmed manual tip removal, the no-tip branch may be used after state, queue, and camera checks.
- Use the existing `move_to_well` function. For repeated identical requests, reuse a validated `load_labware` + `move_to_well` protocol so coordinates resolve dynamically from the deployed definition. Verify logs show safe-Z, XY, then final-Z, and record every run.

## Interrupted home

If `puda machine home` is interrupted or reports an orphaned side effect, treat execution as unknown. Inspect PUDA state, NATS queues, edge logs, and controller acknowledgement before retrying. A late successful response can arrive after run completion and leave a stale run ID; establish the physical home and Sartorius outcome from logs before reset or edge recreation.
