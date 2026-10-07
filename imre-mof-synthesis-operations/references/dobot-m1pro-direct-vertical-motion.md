# Dobot M1Pro direct vertical motion

Use this reference when an operator requires a monotonic/direct absolute-Z move rather than the deployed `safe_move` path through configured safe height.

## Public edge contract

The current IMRE M1Pro edge exposes:

```python
move_vertical_to(*, z: float, speed_factor: float | None = 0.25, blocking: bool = True) -> PoseXYZR
```

Semantics:

1. Read a fresh robot-frame pose through the existing edge.
2. Preserve the measured `X`, `Y`, and `R` exactly.
3. Build target `PoseXYZR(current.x, current.y, z, current.r)`.
4. Issue exactly one controller-verified `_move(..., frame="robot")`.
5. Do not route through safe Z and do not actuate the gripper.

Treat `z` as an absolute robot-frame endpoint. A request such as “raise to Z=30” differs from “raise by 30 mm”; compute relative endpoints only from a fresh measured pose.

## Adding or restoring the primitive

If the live registry does not expose a direct vertical command, do not bypass the edge or call a private method. Add the narrow public wrapper with strict TDD:

1. Write a failing test proving fresh pose preservation and exactly one direct `_move` call.
2. Run the focused test and confirm it fails because the method is absent.
3. Add the minimal wrapper.
4. Run the focused test, then the full driver suite.
5. Inspect existing dirty changes and compare host source hashes with the running container before rebuilding. Preserve deployed local fixes rather than overwriting them.
6. Validate Compose and Python syntax, rebuild, and force-recreate using the deployed Compose project/service identity.
7. Require explicit driver initialization, `Edge Service Ready`, live registry appearance, empty queues, and a successful edge-mediated `get_pose`.
8. Verify the deployed container source hash matches the host source and confirm `puda machine commands` lists `move_vertical_to`.

Edge recreation can run `ClearError → DisableRobot → EnableRobot`, so it is not bookkeeping-only. Re-read pose immediately afterward. Even a small post-reset shift means all later direct targets must preserve the new measured X/Y/R, not pre-restart values.

## Low-Z and loaded-gripper workflow

For a distinct low endpoint:

1. Capture a fresh broad enclosure frame and require idle/run-ID-null plus empty queues.
2. Stage at the same fresh X/Y/R and a supported inspection Z using a separate direct-vertical protocol.
3. Independently verify the stage pose and inspect a fresh frame.
4. If the exact corridor, gripper contents, or contact point is occluded, obtain explicit operator confirmation for the exact `[X,Y,Z,R]` endpoint.
5. Capture one immediate broad frame, then execute a separate final protocol.
6. Apply an operator-specified place speed factor (for example `0.05`) only to the final direct descent; do not silently apply it to the inspection-stage move.
7. Independently query the final pose and reconcile state/queues.

A reverse traversal of a recently used vertical line is not automatically reusable clearance when the exact endpoint changed after a restart, reset, or measured-axis shift. Treat it as a new clearance case unless all exact-endpoint reuse conditions are proven.

## Evidence and reporting

Require edge logs showing:

- one target `MovJ(X,Y,Z,R)` for the direct leg;
- accepted raw `MovJ` response;
- successful `Sync()`;
- no safe-height waypoint;
- no unintended gripper command; and
- the requested speed factor applied to the intended leg.

Then run an independent `get_pose`, require final `idle` with `run_id=null`, and verify both command consumers have zero pending and ack-pending messages.

Distinguish controller acceptance from physical gripper/object evidence. An accepted `DOExecute(1,1)` establishes close-command acceptance; if the jaws or retained object are occluded, describe physical closure/retention as software-inferred rather than visually confirmed.
