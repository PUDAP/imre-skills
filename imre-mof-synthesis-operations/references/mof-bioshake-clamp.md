# MOF BioShake clamp operation through PUDA

Use the existing `bioshake` PUDA edge. Do not open a direct serial session while the edge owns the device.

## State query

Run a one-command PUDA protocol using:

```json
{"name":"query","machine_id":"bioshake","params":{"data":"getElmState","multi_out":false,"timeout":3}}
```

ELM state mapping from the driver:

- `0`: moving
- `1`: locked / clamp closed
- `3`: unlocked / clamp open
- `9`: error

Query before an open/close command and verify after it. Avoid redundant actuation when the requested state is already reached.

## Open clamp

The driver requires the shaker table to be at home before opening the clamp. Use a reviewed two-step protocol:

1. `home` with a suitable timeout (10 s is established)
2. `open_clamp` with a suitable timeout

Verify `getElmState == 3` and PUDA machine state `idle` afterward.

Before homing/opening, confirm any nearby robot is independently verified at a safe retreat/home pose and capture a fresh broad frame for people, tool intrusion over the shaker, clamp/table obstructions, and cable hazards. A partially occluded overhead view may be sufficient for broad people/path gating but not for fine clamp-state confirmation. Treat the fresh ELM readback as the authoritative clamp-state evidence; report visual occlusion honestly rather than claiming the open jaws were seen. Also require the BioShake command consumers to have zero pending and zero ack-pending work before and after actuation.

### Open-clamp state during later robot motion

Opening the clamp changes shared-workcell geometry and the clamp remains open until explicitly closed. Carry that state into every later nearby robot preflight rather than treating the BioShake operation as isolated history:

1. Re-query `getElmState` when the clamp state could have changed or when provenance is interrupted by manual access/restart.
2. Name the open clamp explicitly in the robot path review and fresh overhead-image prompt.
3. For low-clearance robot destinations whose exact local corridor is occluded, require operator confirmation that both the descent corridor **and the open-clamp envelope** are clear.
4. Keep stage and final descent as separate robot runs; do not infer clamp clearance from successful high-Z staging.
5. After the robot move, report clamp interference separately from fine hidden-contact limits. Broad imagery can exclude obvious displacement while still being unable to prove millimetre-scale clearance.

Do not close the clamp merely to simplify a robot move unless the operator requested closure or the reviewed workflow requires it; preserve the verified open state and gate the robot around the actual shared-workcell geometry.

## Close clamp

If the table remains stationary at home, issue one device-scoped `close_clamp` command and verify `getElmState == 1`. If home state is uncertain, home first rather than assuming.

For an operator request to **ensure the BioShake is homed and the clamp is closed before dispensing**, use this idempotent sequence:

1. Run fresh edge-mediated telemetry and require `speed == 0`; record `shake_state` and `elm_state` rather than relying on retained PUDA state.
2. Home through the existing edge (prefer the first-class `puda machine home bioshake` operation when exposed) and require the command response plus the device log acknowledgement `Stopped and is locked at home position`.
3. Query fresh telemetry again after homing. If `elm_state == 1`, the clamp is already closed: do **not** issue a redundant `close_clamp`; the post-home readback satisfies the requested closed-state interlock. If `elm_state != 1`, issue one `close_clamp` command and verify semantic success plus a fresh `elm_state == 1` readback.
4. Require final `speed == 0`, home-state telemetry, PUDA `idle` with `run_id == null`, and zero pending/ack-pending BioShake commands before allowing the dispensing workflow to begin.

Report clearly whether a close command was actuated or skipped because the requested closed state was already independently confirmed. Do not imply that dispensing itself started when only the BioShake precondition was prepared.

## Interrupted unrelated operations

A BioShake request may arrive while an M1Pro workflow is paused. Before resuming the robot workflow, inspect M1Pro state and measured pose. If its pose matches the expected composite retreat, treat the interrupted transfer as completed and do not retry it blindly.
