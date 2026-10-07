# Dobot M1Pro explicit arm-orientation changes

Use when an operator requests a controller arm-orientation value such as `SetArmOrientation(1)` rather than a Cartesian move.

## Safe edge-mediated workflow

1. Discover live commands with `puda machine commands dobot-m1pro`. Do not open a second dashboard/controller session while the edge owns the connection.
2. If no orientation command is exposed, add a narrow public driver method such as `set_arm_orientation(orientation: int) -> str` that:
   - accepts only `0` or `1`;
   - calls the existing edge-owned `DobotClient.SetArmOrientation(right_handed=bool(orientation))`;
   - returns the raw controller response;
   - raises if the dashboard API is unavailable.
3. Add tests first: verify `1` becomes `right_handed=True`, verify invalid values are rejected, observe RED, implement, then run the full driver suite and syntax/Compose checks.
4. Before rebuilding a dirty deployment checkout, compare host source with the live container. Proceed only when unrelated dirty changes are already deployed or otherwise reconciled. Preserve the current Compose project identity: inspect `com.docker.compose.project` on the running container and invoke `docker compose -p <existing-project> up -d --build --force-recreate`. A mismatched default project can build successfully and then fail with a container-name conflict.
5. Require edge-ready logs, live registration, the new command in `puda machine commands`, matching deployed/host source hashes, fresh `idle` with `run_id=null`, empty queues, and a successful edge-mediated pose query.
6. Capture a fresh broad safety frame, then execute a one-command PUDA protocol with the exact requested orientation. Preserve the raw accepted reply, for example `0,{},SetArmOrientation(1);`.
7. Verify the Cartesian pose before and after, final PUDA state, queues, edge health, and a fresh broad image. Report that orientation changed without Cartesian motion only when the pose remains unchanged within tolerance and no motion command was emitted.

## Important state semantics

- `SetArmOrientation` changes the controller's kinematic branch setting; it does not itself prove that a future Cartesian move is reachable or safe in that branch.
- The deployed edge may expose `set_arm_orientation` without an orientation getter. In that case, do **not** equate the last explicit setting with the current branch: inspect all intervening motion logs for automatic `SetArmOrientation(...)` calls and obtain fresh joint angles when available. Compare those angles with installation-specific branch signatures and corroborate with a fresh broad image. If neither joint evidence nor an unambiguous current-operation command chain establishes the branch, ask the operator for the desired explicit target (`0` or `1`) rather than guessing what “change orientation” means.
- Inspect the deployed movement implementation before assuming the setting persists. On the current M1Pro driver, `safe_move` and `pick_and_place` automatically call `SetArmOrientation` from source/target Y and can overwrite an explicit operator setting during the next movement.
- After any subsequent Cartesian move, report that an earlier explicit branch was **requested previously**, not that it was preserved, unless raw edge logs or fresh joint-angle evidence prove the active branch after that move.
- If the operator intends orientation `1` to remain authoritative for a subsequent move, do not rely on a separate earlier setting alone. Review or extend the movement primitive so branch selection is explicit at the safe-height boundary, then test and verify that exact call order.
- Never switch to a destination-compatible branch while still at a low source pose. Lift and verify at safe height first, then change branch and continue.

## Physically changing posture at the same Cartesian home

A successful `SetArmOrientation(0|1)` reply changes branch selection but does **not** physically reconfigure a stationary arm. If the operator expects the elbow posture itself to change while preserving the same Cartesian home endpoint:

1. Capture fresh Cartesian pose, joint angles, and a broad enclosure frame before motion. Treat fingers or any other body part visible inside or intruding at the enclosure boundary as a hard stop; verify the robot remains idle and use a new frame after the person clears.
2. Verify the gripper is empty because M1Pro `home()` opens it. Review the full alternate-elbow sweep even though `[X,Y,Z,R]` will remain unchanged; branch change can swing the elbow through a large arc.
3. Execute one ordered protocol containing `set_arm_orientation(n)` immediately followed by a reviewed slow `home(...)`. Keeping them together prevents an intervening automatic branch selection from overriding the request.
4. Preserve the exact `SetArmOrientation(n)` reply and home `MovJ`/`Sync` evidence.
5. Independently query both final Cartesian pose and joint angles, then capture a fresh broad image and recheck idle/null-run plus queue emptiness.
6. Prove physical branch change from **before/after joint angles and imagery**, not Cartesian pose alone; both elbow branches can share exactly the same `[X,Y,Z,R]`.

Installation-specific evidence from the IMRE M1Pro at home `[200,0,240,-22.5]`:

- Orientation `0`: joints approximately `[60,-120,240,37.5,0,0]`.
- Orientation `1`: joints approximately `[-60,120,240,-82.5,0,0]`.

Treat these as local verification signatures, not universal Dobot constants.
