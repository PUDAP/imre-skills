# Dobot M1Pro motion-only position probes

Use this pattern for repeated operator requests such as “move to MTP B2, Z=29” or “move to Z=27,” where no pick/place or gripper action is intended.

## Target resolution

1. Resolve the named well from the **active UUID-backed machine-scoped labware revision**. Preserve its calibrated `X`, `Y`, and `R`; apply the operator’s explicit `Z` as an override.
2. For a follow-up that names only `Z`, interpret “to Z=N” as an **absolute endpoint** and preserve the freshly measured `X/Y/R`. Interpret “by N” as relative. Ask only if the wording does not establish absolute versus relative.
3. Do not silently substitute old static machine-reference coordinates when the active project calibration differs.

## Motion semantics

- Prefer a public edge-mediated primitive that exactly matches the requested path.
- Deployed `safe_move` is **not a direct vertical primitive**: it computes `travel_z = max(configured_safe_height, current.z, target.z)`, rises to that height, performs the lateral/target-height segment, then descends. Even when only Z changes, it can lift to safe Z (for example 240 mm) and descend again.
- Therefore, report a `safe_move` result as “reached the requested endpoint via safe Z,” not “moved down 10 mm” or “performed a Z-only move.”
- If the operator requires a monotonic/direct vertical path and no such public command is exposed, stop and explain the gap. Do not bypass the edge, invoke a private driver method, or open a second controller session.
- **Low-clearance precedence:** the general permission to use `safe_move` for an absolute endpoint does not override the inspection-stage gate below. Wording such as “move down to `Z=N`” establishes an absolute endpoint, but it does **not** authorize immediate descent to a new lower Z merely because X/Y/R are unchanged or a nearby higher Z was previously cleared. When the requested low endpoint is numerically distinct, first move to the supported inspection Z, independently verify and inspect, then obtain exact-corridor confirmation if local evidence is insufficient. The numeric request authorizes the reversible stage only; it does not waive the final-descent gate.
- Before dispatching any low-Z endpoint protocol, compare the full requested `[X,Y,Z,R]` against the latest explicitly cleared endpoint in project history. If Z differs—even by only a few millimetres—classify it as a new corridor unless the complete endpoint and all clearance-reuse conditions below are identical. Do this comparison before protocol creation/execution, not retrospectively during logging.
- The protocol must contain motion only—no `open_gripper`, `close_gripper`, `pick_from`, `place_to`, or home unless explicitly requested.

## Visual-check waiver

Interpret “no visual checks” narrowly for safety:

- Skip wrist-camera alignment, fine target identification, occupancy/seating classification, and post-motion precision imagery as requested.
- Retain the mandatory fresh broad enclosure gate for people/body parts, obvious swept-path obstructions, collisions, loose/horizontal labware, and displaced equipment.
- Do not claim fine well clearance or physical alignment from that broad check.
- State this distinction briefly in the result rather than implying all safety checks were waived.

## Successive adjacent low-clearance probes

Treat every numerically distinct low-Z endpoint as a new clearance case, even when it differs from the previous verified pose by only 1–2 mm in X/Y and uses the same Z/R. Apply the same rule to a **Z-only follow-up at identical X/Y/R** (for example, verified `Z=12` followed by “move to `Z=10`”): the extra 2 mm is a new endpoint and descent corridor, not an automatically authorized continuation. A prior operator confirmation is scoped to the exact earlier endpoint; controller success, a clean broad post-frame, and absence of a visible anomaly at the earlier Z do not prove clearance at the lower Z.

The new numeric endpoint request authorizes only the reversible safety-stage operation, provided the live state/queue checks and fresh broad enclosure gate pass. Do not add a redundant confirmation before staging merely because the final corridor may later be occluded. **Hard gate:** when local evidence cannot prove the exact lower endpoint, stop at the independently verified inspection stage and obtain explicit confirmation for the complete `[X,Y,final-Z,R]` before creating or running the final-target protocol. Never execute the low endpoint first and document the visual limitation afterward. The operator's eventual confirmation is scoped to that exact `[X,Y,final-Z,R]`; any later numerically distinct endpoint starts a new stage-and-confirm cycle.

1. From the freshly verified low pose, use a separate motion-only protocol to stage at the **new requested X/Y/R** and a supported inspection Z. Audit the real `safe_move` path; the stage can still rise through configured safe Z before settling at inspection height.
2. Independently verify the stage endpoint and capture a fresh local frame. The broad overhead view can clear people and gross hazards but may leave the tool-to-fixture corridor occluded.
3. If the wrist camera is unavailable or the local corridor cannot be proved, pause at inspection height and obtain explicit operator confirmation for that exact `[X,Y,final-Z,R]` corridor. Do not infer clearance from the nearby endpoint or from the numeric size of the adjustment.
4. Author and validate a separate final-descent protocol only after confirmation. Capture a final immediate broad frame, then execute; do not combine staging and descent into one uninterrupted run because that removes the inspection/approval boundary.
5. Independently verify the final pose, inspect for broad anomalies, reconcile queue/state, and record both stage and final runs. If the operator cancels, remain at the verified inspection stage.
6. Persist the approval boundary, not just the motion: record that the operator confirmed the exact `[X,Y,final-Z,R]` corridor **after** the verified stage/local inspection, and carry that statement into the final protocol description plus project history. This makes later exact-endpoint clearance reuse auditable without depending on chat context.

### Dense micro-probe series bookkeeping

For a tuning series that explores several sub-millimetre or millimetre offsets at common `Z/R`:

- Keep each distinct `[X,Y,Z,R]` as a one-shot probe; proximity does not merge clearance scopes.
- Pair each new low endpoint with its own inspection-stage protocol and final-target protocol. Use exact coordinates in descriptions so adjacent probes cannot be confused.
- Reuse a protocol only for a byte-for-byte equivalent numeric endpoint after verifying its stored body; a similar filename or nearby coordinate is insufficient.
- Record the stage run, independent stage pose, local-evidence limitation, operator confirmation, final run, independent final pose, actual safe-height path, and final state/queue reconciliation.
- Do not promote the apparent best probe into the active calibration during the series. Wait for an explicit operator decision to save/label it, then create the UUID-backed calibration separately.

## Returning to an already cleared exact endpoint

A later request may return to a low-Z endpoint that the operator already cleared earlier in the same uninterrupted probe series. Reuse that clearance only when **all** of the following hold:

- the full endpoint is identical, including `X`, `Y`, final `Z`, and `R`;
- every intervening motion was edge-mediated, logged, and independently pose-verified;
- there was no manual enclosure access, labware/fixture change, controller restart, camera/bracket handling, or ambiguous/interrupted run;
- a fresh broad preflight frame shows no person, loose item, displacement, or new swept-path hazard; and
- the exact reusable final-target protocol still matches the requested endpoint.

When these conditions hold, reuse the validated exact-target protocol without repeating the external inspection-stage/confirmation cycle. The deployed `safe_move` still travels through safe Z, so audit and report that path. If any condition is unknown—or the endpoint differs by even 0.5 mm or by R—treat it as a new corridor and repeat stage, local inspection, and exact-endpoint confirmation. Record why prior clearance was reusable; do not merely say “nearby point was already clear.”

## Execution and verification

1. Require edge healthy/ready, PUDA `idle` with `run_id=null`, and both machine consumers at zero pending and ack-pending.
2. Obtain a fresh edge-mediated `get_pose`; use it to preserve axes for follow-up Z-only targets.
3. Create or reuse a validated one-command protocol only when the endpoint is exact. A changed Z requires a new auditable target protocol unless an existing protocol already matches exactly.
4. Run with `set -o pipefail` when using `tee`.
5. Confirm controller-accepted `MovJ` and `Sync`, then independently query `get_pose` again.
6. Report requested versus measured coordinates without rounding away controller precision, final PUDA state/run ID, empty queues, and explicit absence of gripper actuation.
7. Update `project.md` after protocol creation and every run, including read-only verification runs.
