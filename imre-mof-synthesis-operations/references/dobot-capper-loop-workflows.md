# Dobot + Capper Tube-Loop Workflows

Use this reference for PUDA workflows that transfer tubes between a Dobot rack and a capper station.

## Confirmed command vocabulary

- Dobot: `pick_from`, `place_to`, `home`, `get_pose`
- Capper: `decap`, `cap`, `pick_cap_from`, `place_cap_at`, `clear_deck`, `release_bottom`, `release_top`, `home`, `get_position`
- In the deployment verified during this workflow, cap pickup is `pick_cap_from`. `pick_cap_at` passed static protocol validation but was rejected at execution as `Unknown or restricted command`; therefore validation alone does not establish that a command is exposed by the live edge.
- Before every newly authored capper workflow, run `puda machine commands capper` and copy the exact live command name and parameter schema. Treat the live registry as authoritative over old protocol examples and this reference.
- `release_bottom` takes `{}` and opens the capper bottom clamp.

Re-check `puda machine commands <machine-id>` or the current machine reference before reusing these names on another deployment.

## A1-A6 loop patterns

A decapping iteration is:

1. Dobot picks tube from tube-rack Ai.
2. Dobot places it at CAP.
3. Dobot homes.
4. Capper decaps.
5. Capper places the cap at cap-rack Ai.
6. Capper clears the deck.
7. Capper releases the bottom clamp.
8. Dobot picks the tube from CAP.
9. Dobot returns it to tube-rack Ai.

For recapping, replace steps 4-5 with:

4. Capper picks the matching cap using the exact live command (currently verified as `pick_cap_from`).
5. Capper runs `cap`.

If the user wants the Dobot to home only after the last iteration, do not put a post-return `home` inside each iteration. Generate all six 9-command iterations, then append exactly one Dobot `home` after A6.

## Generator and structural checks

For repeated loops, keep a deterministic Python generator as the source of truth. Regenerate JSON after every change; never hand-edit only the generated protocol.

After `puda protocol validate`, assert programmatically:

- expected total command count;
- exact command-name sequence per iteration;
- matching tube and cap coordinates for each position;
- sequential step numbers;
- exact final command and target machine.

## Making `safe_move` authoritative for pick/place speeds

Treat safe-path segments as independent controls, and inspect the full call chain before changing any values:

- Define separate defaults for vertical lift, lateral travel, and final descent in `safe_move`.
- Inspect `pick_from` and `place_to` for an extra `_move` after `safe_move`. If it moves to the same resolved target with an explicit speed, it is a duplicate final motion that can mask or override the intended `safe_move` descent behavior.
- When the operator wants `pick_from` and `place_to` to inherit the `safe_move` profile, remove that duplicate move and its speed override; use the pose returned by `safe_move` as the final pose, then perform the gripper action. Do not merely delete the speed argument while leaving a redundant `_move`, because that substitutes the driver's unrelated global speed.
- Add regression tests that (1) record the speed passed to each `safe_move` segment and (2) fail if `pick_from` or `place_to` calls `_move` after `safe_move`.
- Run the full driver suite, compile check, and diff check before rebuilding the edge.
- Rebuild/recreate the edge, verify its queue has no pending or unacknowledged commands, and verify controller/PUDA readiness before moving samples.
- Inspect the live container's method signature and method source after deployment. Source files and passing local tests do not prove the running edge contains the intended defaults or that another checkout/sync has not reverted them.
- Exercise the deployed change with a reviewed real protocol and independently verify final poses when physical validation is authorized.

For the validated M1 Pro workflow in this project, `safe_move` uses lateral `0.75`, upward `0.25`, and downward `0.25`; `pick_from` and `place_to` add no separate movement-speed override. Treat these values as deployment-specific and re-check both the checkout and live edge signature/source before applying them elsewhere. If values change during an active session, update the regression expectation first, confirm it fails, patch the defaults, rerun the full suite, and redeploy before any physical motion.

## Stateful range operations

Treat a request such as “decap A3” or “cap A2 to A4” as a stateful subset of the rack workflow, not as a stateless replay of a full loop.

1. Maintain a concise software ledger for each rack slot: tube location, expected capped/decapped state, and whether its matching cap is expected in the cap rack. Also track whether CAP is expected empty and the last verified machine poses.
2. Reconcile that ledger from completed command boundaries and independent pose queries before authoring the subset. Do not claim tube/cap presence as sensor-confirmed unless the deployment actually has presence sensing or operator confirmation.
3. Expand only the requested inclusive slot range, preserving the full nine-command handoff sequence for each slot and matching each tube with its same-index cap coordinate.
4. Do not append an extra final home unless the user requested it or the governing protocol specification requires it. Each iteration may still include the safety home before capper motion.
5. After execution, update the ledger from the confirmed run boundary and report the resulting tube/cap locations plus measured machine states.

## Approval-gated return

When the user asks for approval before returning the processed tube:

1. Split the workflow into two independently valid protocols.
2. Stage 1 ends after cap placement, `clear_deck`, and `release_bottom`; leave the tube at CAP.
3. Verify both machines are idle and query their measured positions.
4. State clearly that the tube remains at CAP and ask explicit approval.
5. Do not pre-queue Stage 2.
6. After approval, Stage 2 runs only Dobot `pick_from` CAP followed by `place_to` the source rack.
7. Verify final Dobot pose/state and record both runs.

## Physical-state and interruption safety

Before a full loop, reconcile tube state, tube-rack occupancy, CAP emptiness, and cap-rack occupancy. If a prior run was interrupted, never restart at command 1 blindly.

For `/stop` during a tracked run:

1. Kill the tracked CLI process immediately.
2. Pause/cancel involved queues where supported.
3. Assume an already accepted command may finish after client cancellation.
4. Inspect process logs, machine state, and edge logs to find the last physically completed command, including late responses.
5. Report concrete sample state and create a recovery subset rather than replaying completed pickups.

If a workflow stops on `Unknown or restricted command`, use the same suffix-recovery discipline: prove which earlier steps succeeded, confirm the rejected command produced no physical action, query both machines through their edges, correct the command from the live registry, and execute only the uncompleted suffix. Do not restart from the initial tube pickup when the tube is already waiting at CAP. A stale PUDA `error` state after the rejection does not by itself prove a controller fault; verify read-only commands and let a reviewed recovery run establish a fresh run state rather than guessing a reset command.

## Verification

Protocol success is not sufficient evidence of physical motion. Query through the existing edge connection:

- Dobot measured pose and PUDA state;
- capper measured gantry position and PUDA state.

Avoid a second direct controller/dashboard connection while the edge owns the robot controller.
