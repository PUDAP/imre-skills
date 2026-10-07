# Centrifuge Lid Command Reconciliation

Use this when operating a PUDA-managed centrifuge around a robot, especially when a lid command reports a transport/socket error after visible motion.

## Safe sequence

1. Before closing a lid, verify no person is inside the enclosure and no loose or horizontal item obstructs the centrifuge.
2. Move the robot to a known clear/home pose outside the lid sweep. Confirm robot state is idle and its command queues are clear.
3. Issue the device-scoped lid command (`close_lid(device="1"|"2")` or `open_lid(...)`); never use a global home operation when only one centrifuge is intended. For a request to close **both** lids, close one device, reconcile its normal `50` endpoint and image, and only then close the second device. Do not dispatch two close commands as one opaque batch: the first command's late transport failure must not obscure which physical boundary was reached.
4. If the command reports a late transport error such as a closed socket or bad file descriptor, **do not immediately retry**. The physical operation may already have completed.
5. Reconcile state using independent evidence:
   - **raw edge-log telemetry**, not only the public `get_position` response. On the deployed two-lid driver, the controller publishes semicolon-delimited values such as `0;0` or `0;50`, but `get_position()` attempts `float(position)` and falls back to `0.0` when parsing fails. Thus a returned `{"position": 0}` can mean “unparseable two-lid string,” not both lids open.
   - a fresh overhead safety image showing the actual lid position and robot clearance,
   - edge logs showing reconnection, command acknowledgements such as `Homed1`, and subsequent stable position publishing.

   Interpret the raw pair as the two lid axes for the current controller epoch: `0` is open/home and `50` is the normal closed endpoint. For example, after both lids were explicitly homed, stable `0;0` plus both raised lids established both-open; one device-2 close changed this to stable `0;50` and the lowered green cover established device 2 closed. Do not hard-code a historical first-axis value such as `50;0` or `50;50`: it may reflect lid 1 being left closed rather than a universal encoding.
6. Continue only if raw telemetry and visual evidence agree. If they disagree or remain ambiguous, stop and request onsite confirmation rather than issuing another lid or spin command. In particular, treat values above the expected endpoint (for example `…;150`) as an abnormal/over-travel state that requires homing/reconciliation, not as “more closed.”
7. Before spinning, require verified lid closure and robot clearance. Use `spin(device, duration)`; deployed drivers stop automatically after the requested duration, but verify the explicit `Device N stopped` log before starting any post-spin wait.
8. Measure the requested post-stop wait from the verified stop event, then open the same device-scoped lid and confirm final idle state, raw open telemetry, and a fresh broad-safety image.

## Partial global-home recovery

Use global centrifuge home only when the operator explicitly intends **both** lids. The deployed `home()` opens device 1 and then device 2 sequentially, so a websocket race can leave a partial boundary:

1. Preserve the failed global-home run and inspect edge logs for the last accepted acknowledgement (for example `Homed1`).
2. Read the raw two-axis telemetry. A transition such as `50;150 → 0;150` proves lid 1 homed while lid 2 was not yet homed.
3. Do **not** rerun global home blindly. Issue only the remaining device-scoped `open_lid(device="2")` command after a fresh safety check.
4. Require stable `0;0`, both raised lids in a fresh overhead image, and final `idle/run_id=null` before declaring both lids homed.

## Relative-close accumulation hazard

The controller-side close command can physically advance the lid to its normal `50` endpoint and then lose the websocket reply. A repeated close can advance again, producing abnormal telemetry such as `150`. Therefore:

- after any late close error, wait for stable raw telemetry and inspect the lid image before deciding;
- if the intended axis reached `50` and the cover is visibly lowered, accept physical closure and **do not retry**;
- if the state is abnormal or over-travelled, home that device before any new close attempt;
- never treat a second identical close as harmless or idempotent.

## Audit notes

Record the original command result honestly. If a close command errored after physical closure, describe it as “PUDA reported an error; closure independently verified,” not as an unqualified successful command. Preserve protocol/run IDs, logs, telemetry, images, and hashes in `project.md`.
