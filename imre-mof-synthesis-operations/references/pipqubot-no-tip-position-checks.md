# PipQuBot no-tip position checks

Use this pattern when the operator asks to move the PipQuBot pipette to a named deck slot and well **without attaching a disposable tip** and without liquid handling.

## Safe execution pattern

1. Confirm the live command registry exposes `move_to_well(deck_slot, well_name)`.
2. Before every physical move, obtain fresh evidence:
   - PUDA state is `idle` with `run_id=null`;
   - the affected edge is running/healthy and its restart count/start time are recorded;
   - its command consumer has `pending=0` and `ack_pending=0`;
   - a new enclosure frame shows no person/hand, obstruction, spill, displaced labware, or collision risk;
   - the endpoint is consistent with a known bare-nozzle reference. If physical tip state is uncertain, stop rather than using no-tip geometry.
3. Reconcile the physical and software deck:
   - If the slot already contains the correct labware identifier in live state, use one `move_to_well` command.
   - If the operator has newly placed labware but the live deck slot is null or different, first call `load_labware` with the authoritative deployed labware identifier, then call `move_to_well`.
   - Registering software labware does not prove physical placement; retain the operator statement and camera evidence separately.
4. Do **not** prepend `home`, `attach_tip`, aspiration, dispensing, or ejection to a position-only request. Homing is unnecessary for an established idle gantry and can reset Sartorius software state.
5. Prefer an existing validated protocol when the target slot/well, labware model, and no-tip geometry are exactly the same. Create a new protocol when any of those differ. Revalidate immediately before each run.
6. Retain the run log. Verify that the edge used the safe sequence (lift to safe Z, lateral XY travel, then descent) and that only the intended command(s) ran.
7. After motion, require freshly idle state with no run ID, unchanged healthy edge/restart evidence, zero pending and ack-pending work, and a fresh post-move image showing no visible collision. If a person enters only after the command and `COMPLETE` boundary have already succeeded, immediately reconfirm idle/no-run state and empty queues, dispatch nothing further, and record the entry as post-completion rather than retroactively describing the clear preflight as unsafe.
8. Report coordinates as **driver-reported completion evidence** unless an independent edge-mediated position query succeeds. Do not present the `move_to_well` response as an independently measured pose. If the deployed `get_position` path has the known async dispatcher issue, do not rerun it merely to satisfy verification; state the evidence limit explicitly.
9. Update `project.md` after protocol creation and after every run, including protocol ID, run ID, target, no-tip/no-liquid scope, log link, final state, queue evidence, and camera limitations.
10. A chat, vision, or final-response interruption after dispatch does **not** imply that the motion failed. If the operator repeats the same destination request, first reconcile the latest run from command records, edge logs, PUDA state, and queue counters. When `move_to_well` and `COMPLETE` already succeeded and the machine is idle with an empty queue, report that completed run and do not redispatch. If the command boundary is indeterminate, follow the parent skill's interrupted-run procedure.

## Verified installation examples (session-specific)

For the deployed MOF labware identifier `polyelectric_8_wellplate_30000ul`, the edge reported these no-tip well-top targets during successful position checks on 2026-08-18:

| Target | Driver-reported XYZ (mm) |
|---|---:|
| `A1/A1` | `(28.2, -433.2, -151.0)` |
| `A1/A2` | `(28.2, -404.2, -151.0)` |
| `A1/A3` | `(28.2, -375.2, -151.0)` |
| `A1/A4` | `(28.2, -346.2, -151.0)` |
| `B2/A1` | `(128.2, -283.2, -151.0)` |

Treat these as audit examples, not portable calibration constants. Always resolve future moves through the active deployed labware definition and `move_to_well`.
