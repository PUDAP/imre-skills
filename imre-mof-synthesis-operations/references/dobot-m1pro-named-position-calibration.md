# Dobot M1 Pro named-position calibration

Use this pattern when an operator says “go to this pose and label it …” or otherwise defines a reusable physical landmark.

## Required sequence

1. Treat movement and naming as two linked but separately verified outcomes. Do not persist a label merely because a motion command echoed its target.
2. Before motion, require a fresh edge-mediated pose, idle/no-run state, healthy edge, zero pending and ack-pending queue work, workspace validation, and fresh enclosure imagery. Use the wrist camera as well when the endpoint is near a vessel, rotor, rack, rim, or cap.
3. Move with the validated safe primitive, then independently query the controller pose through the existing edge.
4. Persist the **measured** pose. Retain the requested pose separately if controller precision differs. For this 4-axis M1 Pro, store coordinate order `x,y,z,r,a,b`; mark `a` and `b` as recorded zero/non-actuated fields rather than pretending they were independently controlled.
5. Create a UUID-backed calibration artifact under `calibrations/` rather than relying only on prose memory. Recommended fields:
   - `schema_version`, `calibration_id`, stable machine-readable `label`, and human `display_name`;
   - `machine_id`, `coordinate_frame`, and `coordinate_order`;
   - requested pose, measured pose, controller-verification timestamp, and calibration-recorded timestamp;
   - operator identity;
   - motion protocol/run ID, independent verification run ID, and relative paths to protocol/run logs;
   - fresh post-motion overhead and wrist image paths plus SHA-256 hashes;
   - notes describing non-actuated axes and camera limitations.
6. Ensure the updated label has a clean reusable movement protocol whose description names the landmark and whose target equals the measured pose. If motion used an older, generic, or differently described protocol, keep that actual motion provenance **and** create a fresh reusable protocol for the updated label. Record both separately (for example, `motion_protocol_id` versus `reusable_protocol_id`) and mark the reusable protocol `executed: false` unless it was actually run; never imply it produced the verification evidence.
7. Add the current reusable protocol to the `## Protocols` section of `project.md`, retain the old protocol as superseded provenance, and append a chronological created/ran/calibrated history entry linking the fresh calibration artifact. Re-read the written JSON, validate the reusable protocol, recompute/compare evidence hashes, verify every referenced path exists, and search `project.md` to confirm both links are present.
8. Report the stable label, measured pose, motion run ID, verification run ID, calibration ID, reusable protocol ID, final machine/edge/queue state, and visible safety result.

## Saving an explicitly supplied pose without moving

When the operator says “save this position as …” and supplies coordinates that differ from the robot’s current live pose, treat this as a **recording request**, not an implicit movement request. A “re-set the current position as <label>” request is the same class: no coordinates are supplied and the robot's current pose *is* the target. Do not issue a redundant confirmation move, and do not persist the label from a motion-command response echo alone — a fresh independent `get_pose` through the existing edge must measure the pose before the calibration artifact is written, and the **measured** pose is what gets recorded. The reusable named-move protocol is still created for future use with `executed: false`.

1. Do not move the robot merely to recreate the supplied pose. State that no motion was issued and that the robot remains at its current pose.
2. Search project artifacts for a prior independent controller verification of the exact supplied X/Y/Z/R pose. Use that measured run as provenance only when the coordinates match exactly; do not substitute a requested target or motion-command response for independent `get_pose` evidence.
3. Create a fresh UUID-backed calibration artifact and a reusable named-move protocol. Mark the new protocol `executed: false` in calibration provenance if it was created only for future use.
4. Link the historical source motion protocol/run, independent verification run/log, and available hashed camera evidence. Represent unavailable evidence explicitly (for example, `wrist_image: null`) and explain why rather than inventing or reusing an unrelated frame.
5. Record both `controller_verified_at` and `calibration_recorded_at`; they may legitimately differ. Note that the saved pose is historical/defined and is not the current robot pose.
6. If no exact prior controller verification exists, save the coordinates as operator-supplied/unverified, clearly mark verification status, and do not claim controller verification. Offer a separately safety-gated move-and-verify operation if needed.

## Label hygiene

- Use a lowercase snake-case machine label such as `centrifuge_2_center`; retain the operator’s wording separately as `display_name`.
- A name like “center” is an operator-defined process landmark, not a metrology claim. Camera appearance supports alignment evidence but does not independently establish geometric center.
- Keep machine scope explicit. `centrifuge_2_center` on `dobot-m1pro` must not be silently reused by another robot or coordinate frame.
- When updating an existing label, create a fresh calibration UUID, preserve the previous artifact, and record supersession rather than overwriting provenance.

## Worked IMRE-MOF examples

### Centrifuge process landmark

An operator-defined `centrifuge_2_center` was controller-verified at `[239.5, -77.5, 50, -43.5, 0, 0]`. The durable record used a UUID calibration JSON and linked the motion protocol/run, independent pose-query run, overhead image, wrist image, and both image hashes. The wrist frame showed the designated orange cap near frame center, but the record did not elevate this camera observation into an independent geometric-center measurement.

### Position established by incremental probes

After a sequence of operator-directed relative M1Pro probes, the operator explicitly said to save the current pose as `MT balance load`. The live edge independently measured `[-145, 300, 80, -22.5]`; only then was a fresh calibration UUID created, together with a separate reusable `safe_move` protocol targeting that measured pose. The calibration retained arm-orientation branch metadata, the source motion run, independent pose-query run/log hash, and a fresh overhead-image hash. The reusable protocol was marked `executed: false` because creating it did not authorize another move. `project.md` linked both artifacts and recorded the real creation timestamp. The preceding incremental probes remained one-shot motions and were not silently promoted into calibration revisions before the explicit save request.
