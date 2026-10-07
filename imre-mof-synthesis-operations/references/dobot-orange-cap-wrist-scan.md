# Dobot wrist-camera circular-cap scans and tool-offset moves

Use this procedure for circular targets arranged around a fixed center and detected by rotating the M1Pro wrist camera.

## Scan pattern

1. Query machine state and controller pose through the running PUDA edge; do not open a second controller dashboard session.
2. Capture fresh overhead and wrist images. Check people/hands, destination occupancy, displaced labware, and wrist-cable posture. A 2D frame does not prove full swept-volume clearance.
3. Hold the calibrated scan center `(Xc, Yc, Zc)` fixed. Treat the requested R interval as a hard bound.
4. Move to the lower R bound, then scan monotonically toward the upper bound. For a fresh cap census—especially when the rotor may have moved—sample the full interval uniformly and discover all candidate passages de novo. Do **not** use prior cap R values as coarse samples, refinement seeds, or evidence that a cap still occupies that angle. Prior results are provenance only; derive every candidate and every local `pixels/degree` estimate from the current sweep.
5. At every candidate angle, capture a new wrist frame and identify a *complete circular outline*. Center on the midpoint of the full left/right outline, not the orange-pixel centroid. On the observed M1Pro installation, R changes the outline's horizontal position while the cap follows a fixed vertical image track; use the horizontal frame center `x=320` as the R-centering target. Do not attempt to correct the fixed vertical track offset with R.
6. If the full-outline horizontal midpoint differs from `x=320`, estimate local `pixels/degree` from nearby fresh observations, apply a small bounded R correction, recapture, and verify. Record the vertical midpoint for provenance, but do not reject an otherwise complete outline merely because its fixed track does not cross geometric image center `(320,240)`.
7. Independently query the controller pose after each accepted center. Log the measured R, fresh image path, run ID, centering residual, and spacing to the next cap.
8. Check the overhead view and cable posture periodically across a long sweep and at both boundaries. Stop on ambiguous cable strain, person/hand entry, or displaced labware.
9. Finish at the requested upper bound, independently verify pose/state/edge health, and preserve a CSV report with circular wraparound spacing.

## De novo full-sweep refinement

For rotors whose angular stop position can change between runs:

1. Choose a uniform coarse step from the current field of view and visible cap width; do not hard-code historical cap spacing as the sampling plan. On the observed six-position rotor, `10°` samples provided overlapping complete-cap observations, but this is an installation observation rather than a universal constant.
2. Retain only complete, non-border-touching, approximately circular outlines. Color masks may nominate candidates, but full left/right outline bounds decide acceptance. It is valid for different fresh frames to use different orange masks when illumination/exposure varies; select per frame only after enforcing the same size, aspect-ratio, vertical-track, and border constraints. Never choose a fragmented mask merely because its centroid is closest to `x=320`. Preserve the winning mask name and bounding box, then require an annotated contact-sheet review of all accepted frames.
3. For each fresh passage, bracket the horizontal-center crossing with adjacent coarse observations `(R1,x1)` and `(R2,x2)`, then interpolate:

   ```text
   R_seed = R1 + (320 - x1) * (R2 - R1) / (x2 - x1)
   pixels_per_degree = (x2 - x1) / (R2 - R1)
   ```

4. Capture at `R_seed`. If horizontal residual `dx = x_mid - 320` remains above the image's quantization/noise floor, apply one bounded correction `ΔR = -dx / pixels_per_degree`, recapture, and verify. On 640×480 frames, a stable `|dx| ≤ 1 px` is normally the pixel-quantization floor; do not chase sub-pixel mask noise. If that correction crosses the image center or reveals that the coarse local sensitivity was inaccurate, do **not** repeatedly reuse the stale coarse `pixels_per_degree`. Treat the pre/post-correction observations as a fresh bracket and interpolate the center directly:

   ```text
   R_center = R1 + (320 - x1) * (R2 - R1) / (x2 - x1)
   ```

   Keep the next move within the bracket and preserve both observations. This converts an overshoot into one bounded, auditable correction rather than an oscillating sequence.
5. If refinement requires returning from the upper end to earlier candidates, do not reverse immediately and then resume the forward list; that creates cable-sensitive zig-zag. Finish all still-unmeasured candidates in the established monotonic direction first. Then choose one reviewed recovery path:
   - for multiple or widely separated corrections, unwind/home safely, restage at the lower bound, and verify the corrections monotonically in increasing R;
   - for one bounded correction that lies naturally on the single reverse-unwind path, perform it during that continuous reverse leg only after a fresh overhead/cable gate, independently verify/capture it, then continue toward home without another direction reversal.
   Preserve the initial out-of-tolerance row and correction evidence separately; build a final accepted manifest by replacing only the accepted row rather than overwriting the initial refinement dataset.
6. Number caps by an explicit current-run convention, such as increasing accepted R. Do not imply that “cap 1” retains the same physical identity across rotor motion unless separately tracked.
7. When the requested sweep includes both `-180°` and `+180°`, retain both boundary frames and run records even though they represent the same wrist orientation. Discover passages only from adjacent rows in the monotonic numeric sweep; do **not** add a synthetic `+180° → -180°` crossing, which can double-count the same physical cap. Validate the expected number of unique center crossings before refinement.
8. A generic acquisition runner may cover only the interior continuation (for example, `-170°…+180°`) after a separately safety-gated `-180°` boundary move. In that case, initialize the manifest with the lower-bound protocol/run/image row and make the runner append rather than overwrite. Preferably, update the runner's bounds check to accept `-180°` directly, stage once at fixed XYZ and `R=-180°`, and let the same run capture the first boundary row before continuing with `rotate_r` only. In either design, assert the final angle column is exactly the requested inclusive 37-angle grid before analysis.
9. Keep automation in three auditable stages: target-agnostic motion/capture manifest generation; target-specific candidate detection and interpolation; then one independently logged move/capture/pose-query per accepted refinement. If an interpolated seed already lands at the established image quantization floor (normally `|dx| ≤ 1 px` for these 640×480 frames), accept it after complete-outline and contact-sheet review rather than creating a ceremonial correction run.
10. Parameterize reusable finalizers with the scan center, radius, and final evidence paths from the active calibration or current scan metadata. Do not leave a previous run's center coordinates or timestamped evidence files hard-coded in report code. Before transforming angles to tool XY, assert that the finalizer center equals the requested and registered center for this scan.

## Audit artifacts for a de novo scan

Preserve enough evidence to prove that the result came from the current full sweep rather than historical angles:

- A coarse-sweep manifest with one row per sampled R, including protocol UUID, run ID, wrist-image path, and run-log path. Include both hard boundaries even when one uses a reusable boundary protocol.
- A final one-row-per-cap CSV containing the accepted measured R, move and independent-pose run IDs, full-outline bounding box and midpoint, horizontal residual, source image, circular spacing to the next cap, and transformed tool X/Y when calculated.
- The coarse grid and final centered frames as separate datasets; do not overwrite coarse evidence with refinement captures.
- A contact sheet with the horizontal centering guide and residual labels when visual review is useful, plus an X–Y plot when camera-to-tool coordinates were derived.
- An explicit statement that prior cap R values were not used as candidate angles or interpolation seeds. Record cap numbering semantics and the final robot/lid state.

Validate row counts, file existence, unique coarse-frame hashes, the exact inclusive R grid, accepted residual bounds, and wraparound mean spacing before reporting completion. Artifact completeness is part of proving a de novo scan, not optional presentation polish.

When reconstructing project history from PUDA logs, do **not** parse the UUID in `Protocol created by <user> (<uuid>)` as the protocol ID—that parenthetical is the user UUID. Resolve each protocol ID from the executed protocol path, a manifest row, or the protocol JSON itself, and associate it with the run ID from `Run ID:`. De-duplicate aggregate/per-step logs by run ID before writing history.

Keep critical final motion and independent pose verification separate from optional diagnostics. If a later nonessential probe fails, preserve and report the already verified home/run evidence rather than flattening the whole compound shell command into “motion failed”; rerun only the diagnostic when it is still needed. If a post-home wrist diagnostic exhausts its bounded retry after the full sweep and all accepted refinement frames already succeeded, do not invalidate the completed scan. Record the post-home diagnostic as unavailable. Do not pass a pre-home refinement frame into a metadata field named `final_wrist` unless the field explicitly means `last_validated_scan_wrist`; update the finalizer or add a reconciliation field so evidence timing is not misrepresented.

## Pickup wrist orientation is independent of scan R

Treat the R angle used to center a cap under the wrist camera as a **measurement coordinate**, not automatically as a safe gripper orientation for the subsequent pickup. On the MOF centrifuge-2 installation, approaching cap 6 with its centered scan angle near `R=+149°` caused the wrist camera to collide with the open centrifuge lid. The operator-confirmed corrected pickup kept the same fresh-scan X/Y while forcing `R=-22.5°` at a high source staging pose, throughout the vertical pick approach, gripper close, and vertical lift. This cleared the lid and the full retry completed successfully. Review lid/camera clearance independently for every pickup orientation; never copy scan R into a pick protocol without a collision-clearance decision.

## Automating sequential PUDA scan steps

Keep coarse acquisition and feature detection separate. A reviewed acquisition runner may be reused across orange-cap and empty-ring scans when it only executes the fixed R grid, captures frames, validates image usability, and writes provenance; a filename containing `ring` or `cap` does not define its semantics. Label the new manifest/capture directory with the actual target, and post-process it only with the target-specific detector. Never inherit prior candidate angles or the wrong feature model merely because the motion/capture helper was reused.

Before the first motion, preflight the acquisition or refinement runner without motion: run `--help`; verify imports, camera path, argument names, required manifest columns, output append/overwrite behavior, and output/log parent directories. Validate the complete input schema before dispatching cap 1. In particular, a refinement runner that copies `pixels_per_degree` into its result must receive that column in the protocol manifest; otherwise it can complete a move, capture, and pose query before raising `KeyError`, leaving physical progress without a result row. If this happens, reconcile current pose, per-step logs, and image artifacts before deciding whether to repeat a stationary capture or resume—never blindly rerun the full phase.

For the established `run_r_only_scan_chunk.py` helper, preflight the exact contract before staging:

- protocol-map columns: `angle,protocol_id,protocol_path` (not `r_command_deg` or a guessed alias);
- required arguments: `--protocol-map`, `--start`, `--end`, `--capture-dir`, `--log-dir`, `--manifest`, and `--failure-json`;
- create any aggregate `tee` directory before dispatch;
- assert the map contains the complete requested inclusive angle grid.

Argument/schema failures occur before motion, but verify the current controller pose before retrying the runner. A successful one-time staging move must not be repeated merely because a later helper invocation failed its argument or CSV-schema preflight.

For generated motion protocols, treat `puda protocol validate` as structural validation, not proof that parameters match the deployed Python handler. Compare each command against `puda machine commands` and a recently successful protocol for that same command. On the deployed M1Pro, `safe_move` expects `params.position = {x,y,z,r}`; flat `params.x/y/z/r` can validate but fail at runtime with an unexpected-keyword error.

Create aggregate `tee` destinations in advance because `tee` opens its file before the child runner can create per-item directories. Make this an explicit shell precondition—not something delegated to the child runner:

```bash
aggregate="logs/<scan-id>/<phase>/acquisition.log"
mkdir -p "$(dirname "$aggregate")"
python3 scripts/<runner>.py ... 2>&1 | tee "$aggregate"
runner_rc=${PIPESTATUS[0]}
tee_rc=${PIPESTATUS[1]}
```

If the pipeline is nonzero because `tee` could not open its destination while the motion runner itself completed, do **not** rerun the phase. Preserve the distinction by checking `PIPESTATUS`, the per-step logs, the result-manifest row count, image hashes, current controller pose, and PUDA state. Reconstruct only the missing aggregate diagnostic from existing per-step evidence when useful; never repeat controller-complete movements merely to recreate a convenience log. Conversely, if the runner itself failed, follow the camera/motion stop-boundary rules even when `tee` exited successfully.

When driving one-step scan protocols from a shell loop, isolate every PUDA invocation from the loop's input stream:

```bash
puda protocol run --file "$protocol" </dev/null 2>&1 | tee "$log"
```

`puda protocol run` may remain interactive after a successful command and consume later loop records as command text. This can produce parse errors while leaving only the first physical move completed. Use `set -euo pipefail`, retain one log per candidate, and capture the wrist frame only after that candidate's run exits successfully. If unexpected parse errors occur, do not assume later candidates ran: stop, query the current controller pose through the edge, reconcile the last completed run ID, and resume monotonically from the confirmed angle without repeating completed motion.

Prefer shell arrays or records already materialized in variables over feeding the loop and child processes from the same heredoc/file descriptor. Isolate **every** interactive child, not just PUDA: invoke FFmpeg with `-nostdin` (or redirect `</dev/null`) because it can otherwise consume the next manifest row as console input after a successful capture. When a Python `csv` writer produced the manifest, normalize CRLF before shell parsing (`tr -d '\r'`) or parse it with Python; a trailing `\r` can become part of a protocol path. Keep each candidate as an independently auditable move/capture pair even when orchestration is automated.

## Empty-holder ring scans

When tubes have been unloaded, treat the **black holder annulus** as the target rather than reusing an orange-cap mask:

1. Keep the same de novo full-sweep discipline: sample the full bounded R interval with fresh frames, reject historical cap angles as seeds, and number holders by an explicit current-run convention such as increasing accepted R. A freely rotated rotor can shift every holder angle while preserving roughly equal circular spacing.
2. Detect the complete **outer** holder-ring outline. Reject inner bores, neighboring partial rings, screws, glare circles, and any candidate whose fitted outer circle touches the frame boundary. For a 640×480 installation, constrain detection with physically plausible outer radius and vertical-track ranges learned from the current coarse frames, not copied universal constants.
3. Bracket each outer-ring horizontal-center crossing with adjacent fresh coarse observations, interpolate toward `x=320`, and capture a fresh refinement image. Accept only after geometric detection and visual review agree that the fitted circle follows the complete black annulus. Record center, radius, horizontal residual, image, move run ID, and independent pose run ID.
4. If contrast varies around the sweep, a strict Hough threshold may miss a visually complete ring. Relax the accumulator threshold by a small bounded amount at the **same stationary pose**, then require the same radius/track/border constraints and visual review. Never turn threshold relaxation into permission to accept an inner hole or partial neighbor.
5. Preserve an annotated refinement contact sheet with the fitted outer circle, `x=320` guide, and residual. Validate six unique accepted passages, near-equal circular spacing, image existence, and coordinate transforms before reporting.

### Bounded capture recovery

A camera timeout after a successful move is a capture failure, not a motion failure. Keep the robot stationary, independently query the pose, confirm that no stale FFmpeg process owns the device, and retry capture at that same pose. Put an explicit wall-clock timeout around **every** camera invocation—including one-off correction captures and shell commands using `-frames:v 1`; FFmpeg can remain blocked indefinitely when the V4L2 node exists but emits no packets. Do not rely on a larger compound-shell timeout, because it obscures which capture failed and can prevent the independent pose query from running. If a warm-up filter such as `select=gte(n\,15)` stalls, one immediate single-frame `-frames:v 1` retry can be used as the bounded recovery; verify dimensions, luminance range, and pixels before accepting it. Preserve the successful move log and recovery image in one manifest row so the angle is neither silently skipped nor moved twice. If the bounded retry still fails, stop the scan and unwind safely.

A successful stationary preflight capture does **not** waive this mid-sweep stop rule. If the initial attempt and sole retry later time out at a controller-complete angle, classify feedback as lost even when the by-id symlink still resolves, `/dev/video0` remains present, and no stale FFmpeg process owns the camera. Record that angle as controller-verified but uncaptured, keep it out of the captured manifest, assign zero accepted caps unless the entire fresh scan and refinement had already completed, obtain a fresh broad overhead clearance view, and home/retract without advancing to the next angle. Require physical USB/cable inspection before starting a wholly new de novo scan.

Make Python acquisition/refinement runners catch `subprocess.TimeoutExpired` inside the capture helper and convert it into an auditable nonzero result. Otherwise the exception bypasses the intended retry loop and crashes after motion but before provenance is written. Permit exactly one stationary retry. Before returning nonzero after both attempts fail, write a per-angle failure record (JSON or CSV) containing the controller-complete motion protocol/run IDs, independently measured stationary pose, attempt count, timeout/error text, device-node state, and aggregate/per-angle log paths. A successful-row-only manifest is not enough because it omits the physical stop boundary; preserve the failed angle separately and hash it with the abort report. If an older runner already crashed in that gap, independently verify the current angle, capture once at the unchanged pose, append the missing manifest row with the **original** move run ID and log, assert the angle sequence is continuous, and resume at the next unexecuted angle—never resend the completed move merely to reconstruct a row.

Bind final evidence to the current scan explicitly. Reusable finalizers must accept the final overhead and wrist paths as arguments (or derive them only from the current scan directory), verify both files exist, and write those exact paths into metadata. Never leave a previous scan's hard-coded timestamped evidence paths in reusable report code.

Before reusing an acquisition helper, inspect its capture loop and require **one initial attempt plus at most one bounded retry**. A previously successful helper can still violate the current safety policy—for example, an older loop may attempt capture three times—so prior validation does not waive this source-level check.

Before beginning any new scan attempt, inspect recent project history and scan reports for an unresolved wrist-camera abort. If the immediately preceding or recent attempt ended because the camera disappeared, produced V4L2 I/O errors, or exhausted its stationary retry, the device node merely reappearing is **not** a sufficient preflight. Require explicit operator confirmation that the camera cable/USB connection was physically inspected or reseated before dispatching the lower-bound move. A repeated workflow request alone does not establish that reconciliation. This gate prevents a second partial sweep after an already-known intermittent connection.

Treat camera-loss recurrence across the whole scan attempt, not only at one angle: if the wrist device fails during preflight, recovers once, and then disappears again after a later R move, that is a repeated disconnect. The `/dev/video*` nodes or by-id symlink reappearing afterward is not sufficient recovery evidence and must not trigger continuation. Stop further sweep motion, independently verify the stationary pose, obtain a fresh overhead-clearance image, and retract/home through the existing edge only when that broad view shows a clear path. Record the uncaptured-but-controller-verified angle separately from captured manifest rows, report zero accepted caps unless full fresh-outline refinement completed, and never fill the missing six-cap result from historical scans.

For a compound workflow such as **home → close/spin/open → fresh scan → rotor unload → MTP reload**, commit and report each phase independently. A verified spin remains completed if the subsequent scan aborts; do not re-spin, reuse pre-spin coordinates, or start any transfer merely to salvage the larger request. On scan abort, mark both transfer suffixes unexecuted, leave the centrifuge's device-scoped lid state explicit, preserve the observed rotor occupancy, and finish at a controller-verified safe robot pose with idle machines and empty queues. Resumption requires a completely new de novo scan after the camera/cable issue is physically reconciled; do not repeat the already completed spin unless the operator explicitly requests another spin.

## Image-analysis pitfall

Illumination and auto-exposure can fragment an orange color mask even when the cap is clearly visible. Multiple HSV/RGB thresholds may disagree or split one cap into several components. Do not accept a fragmented component's centroid as the cap center. Prefer the full ring/circle bounds; require a non-border-touching, approximately circular outline, and use threshold stability only as supporting evidence. If no automated mask captures the whole circle, inspect/fit the full geometric outline and label the result accordingly.

**Target-color mismatch:** Re-identify the actual cap color from the current lower-bound frame before running target-specific detection. A loaded rotor may contain blue/purple caps even when reusable artifacts and filenames say `orange-cap`. Never reinterpret “six coarse crossings” from an orange mask as proof about blue caps, and never use a prior orange-cap scan merely because the rotor still has six positions. If the current caps are blue/purple, use a reviewed blue/purple segmentation or color-independent full-circle detector, preserve the exact thresholds/model in the scan artifact, and require the same complete-outline, non-border, spacing, and refinement checks. Treat detector adaptation as analysis only; all candidate angles must still come exclusively from the current de novo sweep.

## Unusable wrist-camera frames during a scan

A syntactically valid JPEG is not necessarily usable camera feedback. Before accepting the lower boundary or first cap candidate:

1. Inspect the pixels and calculate basic luminance range/mean. A nearly black frame with only single-digit values on a `0–255` scale cannot support target identification, even if the device node, dimensions, and FFmpeg exit status are valid.
2. Make at most one bounded stabilized recapture at the same independently verified pose. Do not continue the R sweep hoping later angles will fix absent visual feedback.
3. Do not actuate a neighboring mechanism merely because it *could* be occluding the camera. First compare known-good camera geometry or obtain positive image/mechanical evidence that the mechanism blocks the view. If opening a centrifuge lid is genuinely required for the scan, retract the robot to a verified safe pose, obtain a fresh lid-path clearance check, and operate the lid only through its PUDA edge.
4. Re-stage and recapture once after any independently justified correction. If the frame remains unusable, classify this as camera/illumination failure, not “no caps found,” and do not try additional machine-state changes as speculative camera troubleshooting.
5. Abort the scan without accepting prior seed angles as fresh detections, reverse safely to home, independently verify final pose, and record the attempted angles, images, luminance evidence, and accepted-cap count (usually zero).
6. Leave neighboring machine state explicit—for example, whether a lid was left open for troubleshooting—and request physical inspection of lens obstruction, illumination, cable seating, or camera exposure before retrying.

## R-relative camera-to-tool transform

For a camera-centered point found at angle `R`, rotate the calibrated reference offset rather than adding a fixed base-frame translation:

```text
theta = radians(R - R_ref)
dx = dx_ref*cos(theta) - dy_ref*sin(theta)
dy = dx_ref*sin(theta) + dy_ref*cos(theta)
X_tool = X_camera_center + dx
Y_tool = Y_camera_center + dy
R_tool = R
```

Always use the currently approved calibration values and retain full precision until command serialization. Validate the transformed target against workspace bounds before motion.

### Exact-radius transformed coordinates

When the operator asks for transformed coordinates **exactly** a stated distance from the centrifuge center (for example, “30 mm from centrifuge 2 center”), do not merely rotate the raw calibrated vector and relabel its measured magnitude. Preserve the calibrated vector's angular phase/cross-axis component while normalizing its magnitude first:

```text
rho0 = hypot(dx_ref, dy_ref)
s = rho_requested / rho0
dx_rho = s * dx_ref
dy_rho = s * dy_ref

theta = radians(R - R_ref)
X = X_center + dx_rho*cos(theta) - dy_rho*sin(theta)
Y = Y_center + dx_rho*sin(theta) + dy_rho*cos(theta)
```

Verify `hypot(X-X_center, Y-Y_center) == rho_requested` numerically for every cap and record both the raw and normalized vectors. On the IMRE-MOF calibration `[30.5, 1.0] mm`, an exact 30 mm radius uses normalized `[29.983888291, 0.983078305] mm`; using `[30, 0]` would discard the calibrated phase.

For mat-fox's centrifuge transformed-XY plots, use the established 90° clockwise view: plot robot `Y` horizontally and robot `X` vertically with the vertical axis inverted so increasing `X` goes downward. Keep labels in canonical `(X, Y)` order, state the orientation in the title/axes, and visually check that all six labels are legible and unclipped.

A move to `(X_tool, Y_tool)` intentionally relocates the tool over the target. The wrist-camera frame should therefore **not** be expected to keep the cap centered afterward; use controller pose plus overhead/tool-clearance evidence for post-move verification.

## Low-Z transformed tool moves

Treat the camera-centered scan pose and the transformed tool pose as different physical landmarks. For each transformed cap target near occupied labware:

1. Start from a fresh independently measured pose and recompute or retrieve the transformed `X/Y/R` with full precision.
2. Create an inspection-stage move to that transformed `X/Y/R` at the installation's supported safe Z. Validate and run it through the existing edge.
3. Independently verify the staged pose, then capture fresh overhead and local camera evidence at the destination. The source wrist frame generally cannot prove destination clearance because the camera-to-tool transform intentionally shifts the view.
4. Only after the local destination is clear, run a separately validated low-Z step that preserves the freshly measured staged `X/Y/R` and changes only the requested endpoint Z. Prefer an exposed direct-Z primitive when one exists. Do **not** call the path “vertical-only” merely because X/Y/R are unchanged: inspect the deployed primitive. On the observed M1Pro, `safe_move` can first rise to configured safe height and then descend to the final Z, so disclose that route and treat the separate step as an externally gated descent—not proof of a direct vertical trajectory.
5. Independently verify the final pose and machine state; inspect for displaced tubes, collision, or abnormal cable posture.
6. Repeat this gate for every cap in a sequence. Do not infer that cap 2 is clear merely because cap 1 completed successfully.

Do not treat the internal rise/lateral/descent behavior of one `safe_move` as equivalent to an externally inspectable stage. If the destination was not directly verified before descent, completion of that command proves controller execution but not that the preferred low-clearance safety gate was followed.

## Multi-cap transformed-position series

For a sequence of transformed cap targets, derive every row from the **same fixed camera-center anchor and calibration epoch**. Do not apply the camera-to-tool vector to the previous transformed cap pose, and do not recompute the next cap from the robot's current tool pose; that chains the offset and produces the wrong geometry.

1. Build one provenance table before motion with cap index, fresh scan-measured `R`, `R-R_ref`, rotated `dx/dy`, transformed `X/Y`, source image, and scan/pose run IDs. Use `scripts/rotate_camera_tool_offset.py` for the deterministic geometry and retain full precision until protocol serialization.
2. Treat the table as a set of independent absolute targets. Compare each command against its table row and independently measured result; do not let small controller readback differences become the origin for the next cap.
3. Even when an operator requests caps sequentially, repeat the externally visible safe-Z stage, destination inspection, and separate vertical descent for every cap. A successful neighboring cap and a fresh source image do not prove the next transformed destination is clear.
4. After the transformed tool move, loss of the cap from the wrist-camera center is expected. Verify the tool target with independent controller pose and destination-local overhead/tool-clearance evidence; do not steer back toward the cap using the post-transform wrist image.
5. Report commanded versus measured `X/Y/Z/R` separately and preserve the shared transform artifact so the full ring can be audited without reconstructing coordinates from chat text.

## Picking from a transformed cap pose

When the tool has been moved from the camera-centered landmark to a transformed cap pose, treat **gripper actuation**, **lift-path semantics**, and **physical retention** as separate facts.

1. Reconfirm the exact transformed `X/Y/Z/R` through the edge and capture fresh overhead plus wrist frames before closing. The post-transform wrist image may not show the cap because the camera-to-tool offset intentionally moved the camera away; use the overhead view to assess tool/cap alignment and adjacent interference.
2. Query `puda machine commands <machine-id>` and inspect the deployed driver implementation before choosing a convenience primitive. Do not trust a method summary alone for post-grasp motion. On the observed M1Pro driver, `pick_from` was described as “lift 30 mm,” but its implementation only called `safe_move(position)`, opened, closed, and returned the pick pose—there was no post-close lift. Therefore, do not use `pick_from` when the operator explicitly requires a lift unless the running implementation and regression tests prove that lift exists.
3. For an explicit “close here, then finish at Z” request, a protocol may sequence `close_gripper` followed by the exposed motion primitive to the same `X/Y/R` and requested final Z. Preserve the close response and movement response separately so a partial failure leaves an auditable boundary.
4. Inspect the exact motion primitive before describing the path. The observed M1Pro `safe_move` computes `travel_z=max(configured_safe_height,current_z,target_z)`. Even when `X/Y/R` are unchanged and the requested endpoint is higher, it may rise above the requested Z to safe height and then descend to the final Z. Report that behavior before execution. If the operator forbids overshoot or requires a direct vertical lift, do not claim `safe_move` is vertical-only; require an exposed/tested direct-Z primitive or operator-approved driver change.
5. Treat an accepted `close_gripper`/`DOExecute` response as controller intent, not physical retention. After the lift, independently verify pose and compare fresh overhead imagery against the pre-pick frame. Strong visual evidence combines (a) the tube body visibly held beneath the gripper and (b) the corresponding rotor slot visibly vacated. If only one cue is visible or either is occluded, report pickup as unconfirmed rather than inferring it from the output command.
6. The wrist camera may remain unhelpful after pickup because of its offset and view direction. Prefer the camera that directly resolves the held tube and source slot; do not downgrade clear overhead evidence merely because the wrist frame shows only the vessel rim or background.
7. Once retention is visually established, carry that held-object state into subsequent safety checks. Do not invoke `home` or any other operation known to open the gripper, and do not repeat the pick after an interrupted run unless logs prove the close never executed and physical state is reconciled.
8. When picking a different cap from a raised, empty-gripper pose, make the transition explicit: `safe_move` to that cap's independently calculated absolute transformed pose at pick Z, then `close_gripper`, then a separately logged lift to the requested endpoint. Before running, use a fresh overhead frame to confirm the destination cap is occupied and the gripper is empty; after lifting, require both a held-tube cue and the newly vacated source slot.

## Placing back into a transformed cap slot

Treat descent, release, retreat, and reseating as separately auditable outcomes:

1. Before descent, independently verify the raised pose and use fresh overhead imagery to confirm the tube is still held and the intended rotor slot is empty. Reconcile the slot identity against the same fixed cap table used for the pick; do not infer it only from whichever opening is easiest to see.
2. Prefer `place_to(position=...)` only after inspecting its deployed implementation. On the observed M1Pro edge, it calls `safe_move` to the supplied pose and then `open_gripper`; it does **not** retreat afterward. Add a separate exposed motion command to the requested retreat Z.
3. Preserve the `place_to` response and retreat response as distinct protocol steps. If the retreat fails after release, do not repeat the full placement—the tube may already be seated and the gripper open.
4. Remember that a subsequent `safe_move` to a higher final Z may route through configured safe height and then descend. Disclose this path when relevant, as for post-pick lifts.
5. Verify placement physically by comparing pre/post overhead views. Strong evidence combines: the previously empty slot is now occupied, the gripper no longer holds the tube, neighboring tubes remain seated, and no tube is visible elsewhere. For a complete six-position rotor, counting all six expected caps is a useful cross-check. If the target slot or gripper is occluded, report placement as unconfirmed rather than using command success alone.
6. Independently verify the final retreat pose, PUDA idle state, edge health, and restart count. Carry the gripper-open/tube-seated state forward only when the physical evidence supports it.

## Transferring a scanned rotor tube to registered deck labware

When the destination is a named well in a registered holder rather than the source rotor, keep source identification, labware provenance, destination occupancy, release, and retreat as separate evidence layers:

1. Resolve the source from the latest accepted de novo cap-scan row and compute its transformed tool pose from the same fixed camera-center anchor/calibration epoch. Do not use stale cap numbering or R values after the rotor has moved.
2. Resolve the destination from the UUID-backed labware artifact, retaining labware ID, well name, coordinate frame, units, source hash, and verification status. An operator-supplied coordinate is authorized geometry, not proof that the well is empty or controller-verified.
3. At the source, use separate pick-approach and close/lift boundaries. If only the vacated source slot is visible after lifting, mark retention uncertain; move only to a safe destination inspection height if that move is safe with either a held or absent tube. Do not descend or release until a later view positively confirms retention.
4. Stage at the destination X/Y/R at safe inspection Z and independently query pose. By default, use fresh overhead plus offset-wrist views to seek both (a) the held-tube silhouette and (b) the exact destination opening. Crops/enlargements may help, but do not mistake nearby occupied wells for the named well.
5. Treat an explicit operator request to skip wrist-camera checks as a **camera-specific verification waiver**, not a general safety or occupancy waiver. Do not capture or analyze wrist frames for those pick/place moves. Preserve fresh overhead hard-stop checks, independent controller-pose verification at each safe-Z source/destination stage, command/result logging, and before/after source-slot and destination-row censuses. Record the waiver in protocol descriptions, manifests, project history, and the final report.
6. If the named well is occluded or possibly occupied, pause with the robot idle at safe Z while holding the tube unless a fresh, auditable occupancy ledger positively establishes that exact well as empty. When relying on such a ledger, name its source/revision and verify that no intervening operation could have refilled the well. Otherwise ask the operator to confirm emptiness or choose another well; never infer occupancy merely from neighboring wells or command success.
7. After empty-well clearance is established, run only the reviewed placement suffix: `place_to` at the registered well pose followed by a separately logged retreat. Do not repeat the pick or high-Z stage. Preserve the place/open response independently from retreat completion.
8. Verify placement with a before/after destination comparison. Strong evidence is: the formerly empty opening now contains the transferred tube, the held-tube cue is gone, the source rotor slot remains vacant, neighboring wells/tubes are unchanged, and the final retreat pose is independently measured. Under a wrist-camera waiver, classify physical verification explicitly as **overhead-only** and avoid claiming wrist-confirmed retention or alignment. If the exact named well remains unresolved, report placement as ledger/operator-supported rather than visually confirmed.
9. Do not home while a tube may be held because M1Pro home opens the gripper. Leave neighboring equipment state explicit, including centrifuge-lid position.

## Repeated scanned-rotor → registered-MTP transfer series

Use the three-boundary pattern below when fine source/destination visual verification is required or retained. If the operator explicitly waives fine pick/place visuals and the deployed M1Pro exposes the approved `pick_and_place` composite, follow `references/dobot-batch-transfer-operator-final-z-and-waived-visuals.md` instead: one independently recoverable composite per pair, broad safety-only gates, independent retreat-pose verification, and `controller-inferred` physical outcomes. Do not mix the three-boundary visual census requirements into a fine-visual waiver, and do not weaken broad enclosure safety under either workflow.

For an ordered series such as fresh scan caps `1…N` into registered wells `B1…BN`, use a three-boundary protocol pattern for **each** tube rather than one monolithic pick/place run:

1. **Source stage:** move to the cap's independently calculated transformed X/Y/R at safe Z; independently verify pose and inspect that the intended source is occupied and the gripper is empty.
2. **Pick and destination stage:** descend to the calibrated pick Z, close, lift back to safe Z, then move to the named destination at safe Z. Stop and inspect before any destination descent.
3. **Place and retreat:** descend to the registered well Z, open, and retreat to safe Z. Verify the source vacancy persists and the destination row gained exactly one upright tube before starting the next source stage.

Pre-create and validate all stage/suffix protocols and a manifest before motion so each external camera gate has a reviewed, resumable boundary. Record one distinct run ID per boundary; after an interruption, run only the unexecuted suffix after reconciling held-object state.

Resolve every destination well independently from the active UUID-backed labware artifact. Do **not** generate a `B1…BN` series by assuming uniform pitch or extrapolating neighboring coordinates: verified/calibrated well coordinates can contain local corrections, so even one well may differ from the apparent arithmetic pattern. Preserve the exact artifact value through protocol serialization and compare the independently measured safe-stage pose against that row.

Treat exact-well visibility and occupancy provenance separately. If the gripper or robot body occludes the named destination, a **current-operation occupancy ledger** can establish emptiness only when it contains a directly verified outbound transfer from that exact UUID-backed well and no intervening refill, manual access, or ambiguous run occurred. Combine that ledger with the operator's explicit destination instruction, verified destination-stage pose, neighboring-well geometry, and broad images showing no obstruction. If any link is missing—or the well is merely assumed empty—pause for operator confirmation rather than descending. Label final occupancy as coordinate/ledger-supported when the exact opening remains visually unresolved.

Use count conservation as a physical cross-check throughout the series:

- after pick `k`, the rotor must show exactly `k` new vacancies and `N-k` fewer source tubes;
- after place `k`, the destination sequence must show exactly `k` newly upright tubes in the expected progression;
- no tube may appear loose, horizontal, diagonal, or outside the two tracked locations;
- the final source decrease must equal the final destination increase.

Before homing, require the final release command, safe retreat, fresh broad safety image, and no possibility that a tube remains held; M1Pro home opens the gripper. Preserve the final home run, independent pose query, machine state, edge health, centrifuge state, transfer CSV, and final overhead evidence.

## Session example (2026-09-08)

At centrifuge-2 camera center `(240.5, -77.5)`, reference `R_ref=-17.049999°`, and reference offset `(dx_ref,dy_ref)=(30.5,1.0) mm`, six freshly verified cap centers were:

```text
-139.169998, -77.430000, -17.200001,
  41.549999, 100.349998, 160.949997 degrees
```

The circular spacings averaged exactly `60°`; the maximum deviation was about `1.74°`. Applying the same fixed-anchor transform produced these independent absolute tool targets:

| Cap | Camera-centered R (deg) | Tool X (mm) | Tool Y (mm) |
|---:|---:|---:|---:|
| 1 | -139.169998 | 225.130262 | -103.863254 |
| 2 | -77.430000 | 256.443805 | -103.520090 |
| 3 | -17.200001 | 271.002514 | -76.579853 |
| 4 | 41.549999 | 255.537244 | -50.945692 |
| 5 | 100.349998 | 225.576093 | -50.881830 |
| 6 | 160.949997 | 209.983680 | -77.434954 |

These numbers are provenance/example data, not universal calibration constants. Recompute from the active calibration epoch and fresh scan rather than copying them into another installation.

The same session exposed a convenience-method mismatch during the cap-6 pick. At the independently verified transformed pose `(209.983673,-77.434952,27,160.949997)`, a two-command protocol closed the gripper and used `safe_move` to finish at `Z=100`. The controller accepted `DOExecute(1,1)`, and independent readback measured `(209.983673,-77.434952,100,160.949997)`. The overhead comparison showed the tube held below the gripper and its rotor slot vacated; the offset wrist view did not resolve the held tube. Inspection of the deployed driver showed why the explicit lift was necessary: `pick_from` contained no post-close lift despite its live summary claiming 30 mm, while `safe_move` routed through configured safe height before settling at `Z=100`.

Cap-5 and cap-6 return operations used `place_to` at transformed `Z=27` followed by a separate `safe_move` retreat to `Z=100`. Pre-place evidence showed the held tube and one empty slot; post-place evidence showed the gripper empty and all six orange caps present. This before/after slot census is the preferred physical verification when the wrist camera cannot see the gripper jaws.

### Observed speed semantics

On this deployed M1Pro implementation, `place_to` delegates its motion to `safe_move` and then opens the gripper. Unless overridden, the safe path uses controller `SpeedFactor` values of **25% for the initial vertical rise**, **75% for safe-height lateral/X-Y-R travel**, and **25% for final descent**. A separately requested post-place raise implemented with `safe_move` also uses 25% on vertical segments, but can route through configured safe height before settling at the requested final Z. These are global Dobot `MovJ` scaling percentages, not guaranteed Cartesian velocities in mm/s; do not invent an absolute mm/s value without controller trajectory telemetry or an explicit velocity configuration.
