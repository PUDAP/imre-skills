# Dobot M1 Pro verified-motion debugging

Use this reference when a Dobot 4-axis edge reports success without visible motion, stalls after `MovJ`, or enters controller error mode.

## Evidence to preserve before recovery

Capture through the existing edge connection whenever possible:

1. Requested pose and the pose immediately before motion.
2. Arm-orientation command and raw reply.
3. Raw `MovJ` reply.
4. Raw `Sync` reply and elapsed time.
5. Measured pose immediately after `Sync`.
6. `RobotMode()` and `GetErrorID()` before `ClearError()`.

A successful controller reply is not sufficient. A blocking move should fail unless the measured final pose is within an explicit positional/rotational tolerance. A second PUDA `get_pose` run is useful as an independent confirmation.

## Known diagnostic signature

For a negative-Y target, a forced kinematic branch can accept `MovJ` and let `Sync` return quickly while the arm remains at the preceding safe-height waypoint. On the reproduced M1 Pro case:

- Target: `[131, -231, 240, -20]`
- Wrong branch result: lateral segment did not execute.
- Controller mode after mismatch: `9` (error).
- Controller error ID: `18`.
- Dobot's 4-axis controller alarm table defines ID 18 as **“Target position triggers joint limit”** with the remedy “Reselect movement points.”

This signature established that arm-orientation/kinematic branch selection was causal for that path; it did not merely indicate a generic workspace validation failure. Do not generalize a sign-to-orientation mapping to another robot or tool configuration without a controlled test.

Official alarm data used for decoding: `Dobot-Arm/TCP-IP-4Axis-Python`, `files/alarm_controller.json`.

## Safe recovery ordering

On this M1 Pro installation, the exact response `-1,{},ClearError();` means there was no existing error and the clear operation is complete. Treat `-1` as accepted **only for `ClearError()`**; continue startup to `EnableRobot()` rather than classifying it as a generic rejected command. Keep nonzero replies for other dashboard commands as failures unless separately verified.

In controller error mode, state-changing commands may be rejected. For the reproduced controller, `DisableRobot()` returned `-1` until the error was cleared. Recovery that worked was:

```text
ClearError()
wait 0.5 s
DisableRobot()
EnableRobot()
```

The settling interval mattered: disabling immediately after an accepted `ClearError()` could still be rejected while the controller transitioned out of error mode. Query `RobotMode()` and `GetErrorID()` when available rather than treating timing alone as proof of recovery.

## Post-reconnect home orientation, reset motion, and represented-R pitfalls

After recreating the M1Pro edge, the controller may reconnect with a valid Cartesian pose near configured home but a different persistent arm-orientation branch and an unnormalized equivalent wrist angle (for example, `R=330.930908°`, equivalent to `-29.069092°`). Do not infer the active kinematic branch from the Cartesian pose or from angular equivalence.

A first-class `home` can fail on its *initial safe-height lift* before any lateral/home travel: `MovJ` and `Sync()` may both return success, the measured pose may remain unchanged, `RobotMode()` may enter error mode, and error ID 18 may report a joint-limit condition. The deployed `home()` calls `_move_to_safe_height()` before opening the gripper or traversing home waypoints. Therefore an explicit `set_arm_orientation(home_branch)` immediately before `home` also changes the branch used for the initial low-pose lift. At a low negative-Y pose, selecting the destination/home branch before lifting can itself create the joint-limit fault.

Use this recovery order:

1. Preserve the target, measured pose, raw replies, mode, and error ID. Call it a no-motion false completion only when both fresh pose and edge logs prove that no segment moved.
2. Inspect the deployed reset implementation before invoking it. On this installation, `reset` runs `ClearError()`, waits, then `DisableRobot()` and `EnableRobot()`. It is **not** bookkeeping-only: disabling can permit a loaded arm to settle or swing, so a low-pose reset can materially change Cartesian pose.
3. If a reset is required, obtain an immediate fresh pose and camera frame afterward and treat that measured pose as the new source of truth. Never continue from the pre-reset endpoint or compute a relative recovery target from it.
4. Restore the **source-pose-compatible** branch first, lift to safe Z, and independently verify the lift. Only at safe Z may the home/destination branch be selected and home retried.
5. Capture a fresh broad frame before each consequential recovery leg and independently verify the final configured home pose.

A further reproduced failure boundary matters: even after a verified safe-Z recovery stage, orientation-1 home may move partway and stop before configured home with `RobotMode 9` and controller error `-2`. If the measured pose changed materially, classify the physical outcome as a partial motion—not a retryable no-motion rejection. Do not automatically reset, switch branches, or run an orientation-0 home. Stop, capture a fresh pose/image, preserve the intermediate pose and raw error evidence, and require operator/controller inspection. This is especially important when a prior disable/enable reset already caused unexpected arm motion.

After explicit onsite inspection and pendant/controller recovery, an operator may authorize a single reviewed opposite-branch home from the stable safe-Z pose. Treat that as a new monitored recovery, not as an automatic continuation. A reproduced orientation-0 attempt accepted `SetArmOrientation(0)` and `MovJ(home)`, opened the gripper, then blocked in `Sync()` for 120 seconds before the move-port connection closed. A fresh edge-mediated `get_pose` proved the Cartesian pose was exactly unchanged. For this signature:

1. Preserve the accepted orientation and `MovJ` replies, `Sync` timeout duration, connection-close error, and gripper side effect.
2. Capture a fresh image and run only a read-only pose check; do not infer motion from controller acceptance or the long wait.
3. If the pose is unchanged, classify the result as **accepted command / no physical motion / completion stall**, not partial home.
4. Do not reset, resend home, switch branches again, or restart the edge merely because the move port disconnected while dashboard `get_pose` still works.
5. Ask the onsite operator for the exact pendant mode, alarm IDs, safety-stop state, and whether motion is enabled before designing any next recovery.

After a successful operator-authorized reset/clear-error, discard every pre-reset kinematic assumption and start from fresh pose, state, queue, and image evidence. If the arm is independently verified near safe Z and the operator explicitly requests a branch, a reviewed `set_arm_orientation(branch) → slow home` protocol can be attempted as a new operation. Verify both layers afterward:

- Cartesian home with an independent `get_pose` run.
- Physical branch with fresh joint angles and imagery, because identical Cartesian home coordinates can represent opposite elbow configurations.

On the observed installation, the verified home signatures were:

```text
orientation 1: pose [200,0,240,-22.5], joints [-60,120,240,-82.5,0,0]
orientation 0: pose [200,0,240,-22.5], joints [60,-120,240,37.5,0,0]
```

Treat these joint signatures as installation evidence, not a universal Dobot mapping. A later successful home does not erase earlier partial-motion or timeout provenance; preserve each run separately.

This is a reusable recovery pattern, not a rule that all `R>180°` values are invalid. Preserve the controller-reported angle as evidence and normalize it only for explanation or cable-sweep reasoning.

## Cross-side low-pose orientation ordering

A cross-side transfer exposed a second failure mode that survives alarm clearing and edge restart:

- Source/pick pose: `[131, -231, 14, -20]`
- Destination/place pose: `[57, 275, 21, -20]`
- Safe height: `Z=240`
- Failure: selecting the destination/right-handed branch while still at the low negative-Y source made the vertical lift return apparent `MovJ`/`Sync` success without motion; measured pose stayed at the source and error ID 18 remained.
- A restart plus `ClearError()` did not restore the prior kinematic branch.

The verified ordering was:

```text
measure current/source pose
select source-compatible branch
lift vertically to safe Z and verify
select destination-compatible branch
move laterally at safe Z and verify
descend and verify
open gripper
```

This is stronger than merely moving the destination `SetArmOrientation` call after the lift: after an interrupted attempt, the wrong destination branch may already be persistent, so the driver must explicitly restore the source-compatible branch before lifting.

For recovery after a successful pick but failed place:

1. Do not rerun home or pick automatically.
2. Confirm from step logs that the pick reached the source and the close-gripper command was accepted.
3. Treat tube/labware retention as software-inferred unless a sensor, camera, or operator confirms it.
4. Clear the controller alarm and restore source-compatible orientation.
5. Resume only the place step, then verify destination pose and accepted gripper-open command.

## Dobot M1 Pro gripper polarity

Operator observation established that this installation's gripper output is active-low for opening:

```text
DOExecute(1, 0) -> open
DOExecute(1, 1) -> close
```

The previous mapping was reversed, so accepted `open_gripper` and `close_gripper` responses produced the opposite physical action. The driver correction must therefore be protected by a boundary regression test asserting the two exact output calls.

Expected high-level behavior is:

```text
pick:  physically open -> approach/grasp -> physically close
place: transport -> descend -> physically open/release
```

After changing polarity, rebuild/redeploy the edge and issue a stationary `open_gripper` command before trusting another transfer. An accepted response such as `0,{},DOExecute(1,0);` verifies controller acceptance only; retain operator/sensor confirmation as the physical evidence. Correct any prior run history that inferred release from the old command name alone. Do not generalize this polarity to another gripper wiring without a controlled test.

## Driver hardening pattern

For each blocking segment:

```text
MovJ(target)
validate raw MovJ status
Sync()
validate raw Sync status
measured = GetPose()
compare measured with target using explicit tolerances
if mismatch: query RobotMode and GetErrorID, then fail
```

Log the raw replies. Return a measured pose or clearly label a returned pose as commanded. Never report the requested target as physical success without the comparison.

When restarting an edge, remember that a shallow container health check may be green while the driver is still retrying controller initialization. Require the explicit “driver initialized / edge ready / NATS subscribed” log sequence before issuing commands.

### Dashboard single-session pitfall

This controller can retain a dashboard session after a client disconnect. A one-off direct dashboard probe—even while the edge is stopped—can consume the first responsive session after a controller power cycle; subsequent edge connections may accept TCP on port 29999 but receive no command reply until the controller is power-cycled again. Therefore:

1. Keep `dobot-edge` stopped while the controller is off or booting so it does not hammer port 29999.
2. After the controller is fully booted, use only non-session-consuming checks such as ICMP reachability and a fresh safety image. Do **not** probe dashboard port 29999 or issue a direct dashboard command.
3. Start the edge as the **first and only** dashboard client. The deployed driver accepts the exact response `-1,{},ClearError();` only for `ClearError()` and then continues through its normal enable sequence.
   - If the pre-power-cycle edge still owns stale sockets, stop the exact Compose project/service before restarting. Do not assume `docker compose stop` in the repository targets the running container: inspect the container's `com.docker.compose.project` and `com.docker.compose.service` labels, then use those values (for example, `docker compose -p edge stop dobot`). Confirm the container is exited and that privileged socket inspection shows zero connections to ports 29999/30003 before starting it again.
   - Recreate/start that same project/service once, then let it claim dashboard and motion sessions. A read-only `get_pose` timeout before recovery proves no motion only when edge logs show failure inside the initial dashboard `GetPose()` and no motion command was emitted; preserve that boundary before retrying the user's motion.
4. Require the explicit `Dobot machine initialized successfully` → NATS connected/subscribed → `Edge Service Ready` sequence. A healthy container alone is insufficient.
5. Confirm `dobot-m1pro` appears in `puda machine list`, its state is `idle`, both command consumers have zero pending/ack-pending messages, and an edge-mediated `get_pose` succeeds. The successful recovery sequence on this installation reached `idle` and returned a live pose without commanding motion.
6. If a direct dashboard probe was run after the power cycle—even with the edge stopped—and subsequent edge attempts accept TCP but receive no reply, stop the edge and request another controller power cycle. Do not keep layering retries or additional direct probes; the probe may have consumed the controller's only responsive session.

## Camera-guided M1 Pro wrist alignment

When an operator asks to center a feature by changing only `R`, preserve `X`, `Y`, and `Z` exactly and use bounded image feedback rather than a blind rotation:

1. Confirm the current pose through the existing edge and capture a fresh USB wrist-camera frame.
2. Measure the designated feature against the frame center and preserve the clean frame as evidence.
3. Apply a small `R` probe (about 3–5°), verify the reached pose, and recapture.
4. Infer the sign and approximate pixels-per-degree from observed displacement; do not assume image direction from robot-coordinate conventions.
5. Use bounded intermediate adjustments and recapture after every move. Stop if the feature leaves the frame, moves opposite expectation, or visible safety conditions change.
6. Fine-adjust near the optimum and report the final pose, frame center, measured feature centroid, residual pixel error, and image path.

`R` is one degree of freedom controlling a two-dimensional image location, so it may not be possible to drive both image-axis errors to zero. Define the centering objective and tolerance explicitly. Never call the feature exactly centered while hiding a material residual; a defensible result can be “horizontal error within tolerance and the frame center lies inside the feature,” with the vertical residual reported separately.

Use the M1 Pro `safe_move` path for each verified pose unless a separately validated direct wrist-rotation command exists. `safe_move` may lift to its configured safe height before changing `R` and descending, so each probe can be a full safe-path motion rather than an in-place wrist-only rotation.

## Tool-local planar translations

M1 Pro Cartesian commands are sent in the robot/base frame. When an operator describes a move in the current tool-local frame, first disambiguate whether “30 mm in X− and Y−” means 30 mm per axis or 30 mm total diagonally. For a total diagonal distance `d`, use local components `dx_local = dy_local = -d/sqrt(2)`. Transform at wrist angle `R`:

```text
dx_base = cos(R) * dx_local - sin(R) * dy_local
dy_base = sin(R) * dx_local + cos(R) * dy_local
```

Add those deltas to the freshly measured base-frame pose, preserve `Z` and `R`, validate the transformed target against the driver workspace, then execute through `safe_move`. Record both local and transformed deltas in protocol provenance and independently query the final pose.
