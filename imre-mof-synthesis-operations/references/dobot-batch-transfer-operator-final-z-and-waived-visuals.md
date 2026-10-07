# Dobot batch transfers with operator-specified final Z and waived fine visuals

Use this note for repeated MTP-to-centrifuge transfers when the operator supplies an exact final placement `Z`, fixed `R`, and asks to skip visual placement checks.

## Occupancy boundary before repeating a batch

A prior completed batch means the same source range is presumed consumed and the destination range presumed filled. Repeating the wording of the transfer request is not enough to erase that ledger state.

Resolve each half with current evidence:

- A fresh empty-holder scan or equivalent current evidence can establish that the destination range is empty.
- Obtain explicit operator confirmation that the source range was reloaded if no current source-occupancy evidence exists.
- Ask only for the missing half instead of forcing the operator to reconfirm facts already established by fresh evidence.

## Deployed approved composite operation

When `puda machine commands dobot-m1pro` exposes `pick_and_place`, prefer one independently recoverable protocol per source/destination pair with a single `pick_and_place` command instead of emulating the motion through `safe_move`. A repeated `safe_move` cannot express the approved direct staging-to-final descent because it may route back through safe Z.

The deployed composite accepts `source`, `destination`, `safe_z`, `staging_offset`, `speed_factor_up`, `speed_factor_lateral`, `speed_factor_down`, `speed_factor_final`, and `dwell_seconds`. Approved defaults are `240 mm`, `50 mm`, `.50`, `.90`, `.50`, `.05`, and `1 s` (staging offset updated by mat-fox on 2026-09-14). It performs the approved sequence internally: conditional lift; source safe/stage/final moves; close; dwell; source withdrawal; safe/lateral transfer; destination stage/final moves; hold; open; dwell; final withdrawal; then a fresh final-stage pose readback and tolerance check. It returns the measured destination-stage pose. Keep clearance-safe travel `R=-22.5°` and use explicit source/destination R values.

Before relying on it, verify the live command surface after any edge recreate. If the command is absent, do not approximate the sequence with repeated `safe_move`; deploy/restore the composite implementation or stop and report the blocker.

## Legacy protocol shape

Use the following only when an operator explicitly requests the older immediate-release sequence rather than the approved composite:

1. `safe_move` to source pick pose.
2. `close_gripper`.
3. `safe_move` vertically to carry height.
4. `safe_move` to destination staging pose.
5. `safe_move` to the exact operator-specified final placement pose.
6. `open_gripper`.
7. `safe_move` back to destination staging/carry pose.

For destination staging, final placement, and retreat, preserve the operator's requested `R` explicitly. Do not silently replace an operator-specified final `Z` with a historical calibration value; record the override in the protocol description and run ledger.

For native Dobot `SpeedFactor(10)` on only the final descent, pass `speed_factor_down: 0.10` on step 5 only. The deployed M1Pro driver maps a factor in `(0,1]` to the controller percentage by multiplying by 100, and `safe_move` applies `speed_factor_down` to its final vertical segment while restoring the prior speed afterward.

Before execution, mechanically audit every protocol:

- exactly seven contiguous steps when release is immediate;
- correct source and destination pair;
- destination stage/final/retreat all use the requested `R`;
- final placement uses the exact requested `Z`;
- `speed_factor_down: 0.10` appears only on the final destination move;
- no zero-speed segment.

## Operator-requested dwell before gripper release

The M1Pro command surface may have no `wait`/`sleep` command. If the operator says, for example, “after placing, wait 2 seconds, then open the gripper and raise Z,” do not silently omit the dwell or delay before the descent. Implement each transfer as a recoverable paired boundary:

**Phase A — pick/place/hold (5 commands)**

1. `safe_move` to the source pick pose;
2. `close_gripper`;
3. lift vertically to carry Z;
4. stage at destination X/Y/carry-Z/operator R;
5. descend to the exact final Z with the requested final-descent speed, then stop while keeping the gripper closed.

After Phase A returns controller-complete, start a monotonic host timer, sleep for at least the requested dwell, and preserve UTC start/end plus measured elapsed seconds in a timing artifact. Then run:

**Phase B — release/retreat (2 commands)**

1. `open_gripper` at unchanged destination X/Y/final-Z/R;
2. raise vertically to the requested retreat Z at unchanged X/Y/R.

Audit the pair as one seven-command transfer: Phase A must contain the only requested final-descent speed factor; Phase B must begin with `open_gripper` and end at the exact retreat Z. Do not run a pose query, camera check, unrelated command, or lateral move between Phase A and the dwell/release boundary. If Phase A fails or its final pose is not reached, do not start the timer or release protocol. If Phase B fails after the open command, reconcile gripper and pose state before any retry; never replay Phase A merely to recover the retreat.

When timing is specified as “wait N seconds,” later tool/CLI latency before the timer only increases the safe hold. Report the measured explicit timer interval and, when available, the controller completion timestamp; do not claim sub-second exactness unsupported by the protocol transport.

## Reversing a completed centrifuge↔MTP batch

When the operator asks to reverse the immediately preceding transfer using the “same XY coordinates,” derive each new pair from the persisted result artifact rather than re-reading rounded coordinates from chat text:

1. Preserve the exact MTP and centrifuge X/Y values from the prior batch artifact, then swap source and destination roles pairwise (`B1↔cap1`, …, `B6↔cap6`).
2. Swap the validated process heights with the stations: in the active September 2026 calibration, MTP pickup is `Z=9 mm` and centrifuge placement is `Z=27 mm`. Do not swap only X/Y while leaving the old source/destination Z values attached to command roles.
3. Keep `R=-22.5°`, safe `Z=240 mm`, speed factors `.50/.90/.50/.05`, and `1 s` dwell unless the operator overrides them. For mat-fox, use the corrected `50 mm` staging offset for future composites; do not inherit `100 mm` merely because it appears in the prior run artifact.
4. The prior batch ledger can establish the reverse occupancy boundary when it directly records those exact pairwise transfers and no intervening manual access/refill is known. Treat occupancy as controller-inferred if fine visuals were waived in the prior run.
5. Create and validate one independently recoverable composite protocol per pair. Record the prior batch ID as coordinate provenance, and retain separate motion and independent pose-query run IDs.
6. A verified final retreat at destination `Z + staging_offset` proves the robot endpoint, not pickup retention or tube seating. Keep the physical result graded as controller-inferred when fine pick/place visuals are waived.

## Fresh scan-driven centrifuge → MTP batches

When a loaded centrifuge rotor is freshly scanned and the operator immediately requests `cap 1…N → MTP wells` with fine pick/place visuals waived:

1. Use the accepted current scan's transformed `tool_x_mm/tool_y_mm` rows as the source X/Y values. Preserve the scan UUID, accepted image/pose provenance, and cap-numbering convention. Do not substitute the camera-centered X/Y or historical cap coordinates.
2. Treat each scan R as a **measurement coordinate**, not the gripper orientation. On the MOF M1Pro installation, use the reviewed clearance orientation `R=-22.5°` for source and destination while retaining each cap's transformed X/Y. Never copy a large centered scan R into the pickup command without a separate lid/camera-clearance decision.
3. Attach station heights to the physical locations: for the active September 2026 calibration, centrifuge pickup is `Z=27 mm` and MTP placement is `Z=9 mm`. Keep safe `Z=240 mm`, staging `50 mm`, factors `.50/.90/.50/.05`, and dwell `1 s` unless overridden.
4. A fresh six-cap scan can establish the source range as occupied. The exact destination wells may be treated as empty from a directly preceding, persisted outbound batch only when that ledger names the same wells and no refill, manual access, or ambiguous run intervened. State both evidence grades in the new plan rather than asking for redundant confirmation.
5. When live `pick_and_place` is present, create and validate one composite protocol per cap/well pair. The composite's returned destination-stage pose should equal `destination Z + staging_offset` (for MTP `9 + 50 = 59 mm`); verify it with a separate `get_pose` run and require idle/empty queues before continuing.
6. An explicit waiver of pick/place visual checks means no wrist alignment, source-vacancy census, exact-well occupancy, or seating assessment. It does **not** waive a fresh broad overhead hard-stop check before every dispatch. Restrict that check to people/hands, loose/fallen or diagonal tubes as obvious hazards, displaced equipment, lid/path obstruction, collision, and other enclosure-level hazards. Do not upgrade the physical outcome beyond `controller-inferred` merely because a broad image incidentally looks orderly.
7. After the last verified retreat, take a final broad clearance image before homing. If it reveals an obvious source tube remaining or loose tube, record a physical discrepancy and do not issue an unplanned extra pickup. Otherwise home, independently verify `[200,0,240,-22.5]`, and preserve UUID-linked CSV/JSON plus hashes.

## Mid-batch operator override or cancellation

A new operator instruction supersedes pending members of a batch. Stop at the last independently verified retreat boundary, mark completed and unrun source/destination pairs explicitly, and do not resume remaining pairs implicitly later. Before a requested home or centrifuge lid action, take a fresh broad safety-only frame and recheck idle/queues because the prior post-transfer check may be stale or may have timed out. Preserve completed transfers as controller-inferred when fine visuals were waived.

## Waived fine visuals do not waive broad safety

When fine pickup/placement verification is waived:

- Do not perform or claim tube-centering, seating, or exact occupancy checks.
- Still capture a fresh broad overhead safety frame before every transfer and stop for people, hands, loose/fallen tubes, displaced equipment, cable hazards, or a closed/ambiguous centrifuge lid.
- A post-transfer frame may serve as the next transfer's preflight only when it was captured after the previous robot motion and no intervention or other operation occurred before the next dispatch.
- Cross-check centrifuge telemetry and edge health; for centrifuge 2, `Position: 50;0` is the expected open-lid telemetry in this deployment.

## Per-transfer and final verification

After each transfer:

- query pose independently;
- require machine state `idle` and `run_id: null`;
- inspect both immediate and queued consumers (`pending=0`, `ack_pending=0`);
- capture and assess the broad safety frame before continuing.

After the batch, write a UUID-linked CSV/JSON ledger containing source, destination, protocol ID, run ID, requested `R`, final `Z`, speed factor, command count, and controller-complete status. Record the final independent pose and queue/edge state. If fine visuals were waived, explicitly state that no fine seating or occupancy claim was made.
