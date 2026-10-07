# BioShake serial-edge recovery

Use this when a BioShake operation fails because the device does not report its configured target speed or clamp state, especially after long edge uptime or USB re-enumeration.

## Clamp open/close verification

1. Before `open_clamp`, require fresh queue emptiness and an edge-mediated status probe proving speed 0. Because the device requires the tablar at home before opening, run or verify `home` first when current home position is not directly available.
2. Treat the outer PUDA response and the driver result as separate layers. A response with `status="success"` only proves the method returned without raising. If `open_clamp` or `close_clamp` returns `data.result=false`, the requested clamp transition is **not confirmed**.
3. `get_position` values such as `elm_state=-1` or `shake_state=-1` mean unknown/unreadable telemetry, not open, closed, stopped, or healthy. Likewise, a raw edge-mediated `getElmState` query that returns no payload is not verification.
4. Do not automatically retry an unconfirmed clamp command. Preserve the successful home boundary separately, require physical observation or recover the serial edge, then issue at most one reviewed retry.
5. For a confirmed result, require one of:
   - command result `true` plus a valid post-command ELM state matching the request; or
   - command result `true` plus direct operator/camera confirmation when ELM telemetry is unavailable.
   If the command returns false even when the clamp appears to move, report the physical observation and software failure separately.
6. If speed is 0 but both ELM and shake states remain `-1`, suspect serial-session degradation rather than treating the stationary speed alone as controller health. Follow the USB/by-id recovery procedure below before further actuation.

## Safety and retry boundary

1. Inspect edge logs before retrying.
2. In the current driver, target-speed verification occurs before `_shake_on()`:
   - `_set_shake_target_speed(target)`
   - `_get_shake_target_speed()`
   - only after a valid matching value: `_shake_on()`
3. If logs show `Setting target speed ...` followed by `BioShake did not report a target shake speed`, with no `Starting shake ...` or `_shake_on` evidence, record that no shaking started. A reviewed retry is safe after recovery.
4. If logs show `Starting shake ...`, treat physical duration/outcome as uncertain. Do not automatically retry; first verify stop/home state.

## Clamp-command recovery

Use this when `open_clamp` or `close_clamp` times out with `result=false`, especially when `get_position()` also reports `elm_state=-1` or `shake_state=-1`.

1. Treat `result=false` as a failed or unverified actuator command; never report the clamp as open/closed from the outer PUDA `status=success` alone.
2. Confirm the shaker is not moving (`speed=0`), the run is inactive, and both queue counters are zero. Capture a fresh clear enclosure frame before recovery.
3. Inspect the edge logs and stable serial mapping. The MOF BioShake uses `/dev/serial/by-id/usb-FTDI_FT232R_USB_UART_AB0NCAGV-if00-port0`; do not substitute a transient `/dev/ttyUSB<N>` path.
4. Recreate or restart only the BioShake edge to reopen the stale serial session. Verify startup logs show connection at 9600 baud, NATS readiness, and empty consumers. Edge startup must not issue physical motion.
5. Run a fresh read-only `get_position`. Require numeric telemetry rather than `-1`: `shake_state=3` means home/locked and `elm_state=1` means closed; `elm_state=3` means open for the deployed driver.
6. Capture a second fresh clear-camera gate, then retry the exact validated home-plus-clamp protocol once. Require `result=true`.
7. Verify with a post-command `get_position`, empty queues, and a post-action frame. If a person enters only after controller-confirmed completion, dispatch no more motion until a new clear-camera gate.

## USB re-enumeration recovery

1. Require the BioShake run to be inactive and both queue counters to be zero.
2. Capture a fresh enclosure frame. Hard-stop if a person/body part is inside, the plate is displaced, or another robot is operating at the BioShake position.
3. Compare the configured serial path with current `/dev/serial/by-id/*` identities. Identify the BioShake device by its stable hardware identity, not by a transient `/dev/ttyUSB<N>` number.
4. Configure Compose and the driver with the stable by-id path, e.g.:

   ```env
   BIOSHAKE_PORT=/dev/serial/by-id/usb-FTDI_FT232R_USB_UART_<SERIAL>-if00-port0
   ```

   When Compose uses `${BIOSHAKE_PORT}:${BIOSHAKE_PORT}`, the same by-id path is available inside the container.
5. Validate `docker compose config`, then recreate only the BioShake edge. Startup is expected to reconnect serial and NATS; verify the deployed image before assuming it performs no physical startup motion.
6. Require all of:
   - container running and healthy;
   - log-confirmed serial connection on the by-id path;
   - NATS subscription and fresh heartbeat;
   - fresh `idle`, `run_id=null` state;
   - command consumer `pending=0`, `ack_pending=0`;
   - a second fresh clear-camera gate.
7. Re-run the exact validated shake protocol once.

## Completion evidence

Require the command/database success plus device logs showing:

- target speed set and read back;
- `Starting shake for <duration> seconds`;
- `Stopping shaker` after the programmed interval;
- bounded deceleration;
- `Stopped and is locked at home position`;
- final PUDA `idle`, empty queue, healthy edge;
- fresh post-run camera with the plate plausibly seated.

Treat unsupported optional speed-limit queries as non-blocking only when the driver explicitly tolerates them and the target-speed readback plus shake command succeed. Target-speed verification is controller/driver evidence, not an independent tachometer measurement of actual RPM.

## Sample-event provenance

For a successful homogenization run, bind one process event to every pre-existing sample UUID rather than generating new sample IDs. Record:

- event UUID, event type `homogenization`, machine/instrument;
- source sample run ID, BioShake protocol ID and run ID;
- target RPM, programmed duration, start/stop/completion timestamps;
- command/database, final-state, queue, camera, and file-hash evidence;
- any failed pre-motion attempt and recovery context;
- explicit limits: no independent RPM measurement and no camera verification of liquid homogeneity.

Preserve pre-event provenance snapshots, update the existing per-sample JSON/CSV records, and emit a normalized one-row-per-sample homogenization CSV/JSON for inspection.

### Provenance schema compatibility

Do not assume every run-scoped provenance artifact uses the same field names. Before writing, inspect the active sample records and resolve the existing identifier/location fields (for example, `sample_id` versus `sample_uuid`, and `deck_slot`/`well` versus `destination_slot`/`destination_well`). Preserve the existing schema in the source artifact, use a stable normalized schema in the event export, and validate all of the following after read-back:

- exactly the expected number of samples;
- unique pre-existing UUIDs, with no newly generated sample UUIDs;
- every sample references the same homogenization event UUID;
- normalized CSV/JSON contains one row/object per sample;
- labels and destination wells still match the source provenance.

Create `.pre-homogenization.json` and `.pre-homogenization.csv` snapshots before mutating run-scoped provenance, and hash those snapshots as part of the event evidence.

### Post-completion operator entry

A camera frame captured after the device reports stop/home may show an operator entering the enclosure. Handle this as time-ordered evidence rather than retroactively declaring the completed shake unsafe:

1. Establish from controller logs, database records, PUDA state, and queue counters that shaking had stopped, the device was locked at home, the run was complete, and no command remained pending before the person entered.
2. Dispatch no further motion while any person/body part is visible.
3. Record the operator entry and any image occlusion explicitly. Do not describe the post-run frame as clear when it is not.
4. Preserve only what remains visually supportable (for example, no obvious spill/collision and holder plausibly in place), while stating that sample identity, homogeneity, and occluded details are unverified.
5. If another physical action is requested, require a new clear-camera safety gate after the person leaves.
