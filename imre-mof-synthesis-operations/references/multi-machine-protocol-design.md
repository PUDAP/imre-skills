# Multi-machine PUDA protocol design

Use this reference when one machine transfers labware to a shared station and another machine performs a process there.

## Resolve stations per machine

Station labels are machine-scoped. `A1` on a robot tube rack and `A1` on a cap rack may use unrelated coordinate systems and parameter shapes.

Before authoring:

1. Search existing validated protocols and `project.md` for each `(machine_id, station label)` pair.
2. Confirm the exposed command with `puda machine commands <machine-id>`.
3. Reuse that command's established parameter shape; one driver may accept `position: {x,y,z,r}` while another accepts top-level `x,y,z`. A position table may list only the varying axes (for example, `[x,y]`) even though the command requires a fixed `z`; obtain omitted axes from a validated project protocol or calibrated machine configuration rather than inventing a default.
4. Put the resolved coordinates and station meaning in the protocol description or project entry.
5. Ask the user if two plausible mappings remain. Never copy coordinates across machines merely because a station label matches.

## Encode physical dependencies sequentially

Use increasing step numbers whenever a later action depends on the physical result of an earlier machine:

```text
1 robot pick source
2 robot place shared station
3 robot home or clear station
4 process machine acts on item
5 process machine returns consumable
6 process machine home
```

Do not parallelize dependent actions. Same-step parallelism is only for independent operations, and a machine may appear at most once in a parallel group.

### Capper-to-robot handoff cleanup

For a capper that decaps a tube at a shared CAP station, returning the cap is not by itself sufficient clearance for the robot to re-enter. Use the machine's explicit cleanup/clamp commands in the calibrated order. The verified A-row workflow is:

```text
capper decap
capper place_cap_at matching cap-rack position
capper clear_deck
capper release_bottom
robot pick_from CAP
```

`release_top` and `release_bottom` are distinct operations. Do not substitute one for the other: use `release_bottom` in the normal post-`clear_deck` handoff, and use `release_top` only when the user explicitly requests opening the top gripper or a reviewed recovery requires it. Keep each as its own auditable protocol command.

### Capper recapping handoff

For the inverse workflow, use the exact exposed command `pick_cap_from(x, y, z)`—not the plausible but invalid name `pick_cap_at`. A reviewed A-row recapping iteration is:

```text
robot pick_from tube-rack position N
robot place_to CAP
robot home to clear the shared station
capper pick_cap_from matching cap-rack position N
capper cap
capper clear_deck
capper release_bottom
robot pick_from CAP
robot place_to original tube-rack position N
```

The cap operation releases the top clamp and retracts the gantry, but it engages the bottom clamp; retain the explicit `release_bottom` after `clear_deck` before the robot re-enters CAP. Preflight this loop as the physical inverse of decapping: each source tube must be decapped, each matching cap-rack position must contain the intended cap, CAP must be empty, and the capper must not already hold a cap. A fully verified decapping loop can establish those prerequisites for a subsequent recapping loop, but a new chat or protocol validation alone cannot.

If the requested terminal posture is “home once after A6,” keep the nine commands above inside each iteration and append one Dobot `home` outside the loop. For six positions this yields 55 commands, with A6 return at step 54 and final home at step 55.

## Repeated workflows through a shared station

Before turning a single-item workflow into a loop, model the shared station's occupancy at the end of one iteration. A successful process step does not necessarily clear the item from the station. If the item remains, the next iteration must not place another item there.

For each iteration, require an explicit station-clearing action before advancing, such as:

```text
robot moves item from source N to shared station
process machine operates and returns any consumable to matching position N
robot removes processed item from shared station
robot returns it to source N or another confirmed destination
only then advance to source N+1
```

If clearing is manual, do not represent the workflow as an unattended loop. Ask whether to stop between iterations or use a machine-verifiable acknowledgment.

When PUDA protocols are static command lists, implement the author's loop in a deterministic generator script and emit an expanded protocol rather than inventing a loop field. Verify all of the following before validation:

- expected command count = positions × commands per iteration,
- contiguous, unique step numbers,
- source and return coordinates match within each iteration,
- process-machine consumable destination uses the same position label but its own machine-specific coordinates,
- the shared-station destination is constant,
- every iteration ends in a state suitable for the next one.

Retain the generator beside the project and link it from `project.md`, then run `puda protocol validate` on the generated JSON. Validation still does not authorize execution.

### Per-iteration terminal posture

Treat the last command of each iteration as an explicit workflow decision, not boilerplate. If the user removes a final `home`, do not silently restore it. Instead:

- verify that the next iteration's first robot primitive provides a safe lift/transit from the previous low return pose,
- recalculate commands-per-iteration, total command count, and every later step range,
- update the generator description and project entry so they no longer claim the robot homes,
- state that a loop with no final home leaves the robot at the last return position rather than home.

If the user wants the robot to home **once after the last iteration**, append that command outside the generator loop rather than putting it in each iteration. Verify:

- total commands = `(positions × commands_per_iteration) + 1`,
- the penultimate command returns the final item to its source/destination,
- the final command is the one requested `home`,
- no earlier iteration acquired an unintended terminal home.

Conversely, do not add a final home merely for convenience when a held item, clamp state, or fixture clearance makes it unsafe.

## Validation is not execution

`puda protocol validate` proves schema and command compatibility only. It does not prove coordinates are physically safe, labware is present, gripper polarity is correct, or the downstream machine can access the station.

After creation, report **created and validated, not run** unless the user also authorized execution.

### Repeated-run physical preflight

Before executing an expanded loop, reconcile the physical setup against the latest project/run history rather than assuming a new chat or a freshly validated file means the deck was reset. Obtain explicit operator confirmation for every collision-relevant condition, including:

- each requested source position contains the expected item in the expected state (for example, capped rather than already processed),
- the shared handoff station is empty,
- every consumable destination that the loop will use is empty,
- both machines are idle and any previously paused queues have been deliberately resumed,
- grippers/clamps and held consumables match the protocol's assumed starting state.

If an earlier partial run left an item at the shared station or a consumable in a destination, do not launch from step 1 until the operator confirms the physical deck was reset. A generic “run it” is execution authorization, not evidence that these prerequisites are true.

## Partial execution and recovery

Background process lifecycle is separate from the chat/tool-wait lifecycle. A timed-out or interrupted `process wait`, an assistant response interruption, or an ordinary user message does **not** stop `puda protocol run`. Keep the tracked process/session ID. When the user explicitly requests stop, issue an explicit process kill/cancellation and machine queue controls, then inspect process and edge logs; never infer cancellation from the wait call ending.

`--steps` is useful for deliberate subsets and recovery, but it does not recreate physical prerequisites. Before running a later subset:

- reconstruct which earlier steps physically completed from edge responses and logs, including commands that finished after the protocol client was interrupted,
- treat the queue-pause event and the public machine-state value as separate evidence: a delayed in-flight command response can overwrite `paused` with `idle` in the state store even though the queue remains paused; confirm pause/resume from edge queue logs before dispatching recovery work,
- if interruption occurs during a process command such as `decap`, determine whether it completed and whether the machine is still holding a cap/tool before placing, releasing, homing, or restarting,
- verify machine pose/state and gripper/tool state,
- do not repeat a pick automatically,
- resume only the safe next step,
- record the selected range and outcome in `project.md`.

For generated/expanded loops, preserve the exact protocol artifact used by each run. If the generator is later changed (for example, inserting a clamp-release command into every iteration), all downstream step numbers shift. Never apply a recovery range derived from an older run to the regenerated protocol without recalculating and reviewing the iteration boundary.

Use the interrupted-run procedure in the main skill for robot pick/place recovery.

## Audit checklist

After creating a protocol, use `puda-memory` to record its link and creation timestamp. After every run, record the timestamp, run ID, selected steps, and outcome. Distinguish command acceptance from measured pose and operator/sensor-confirmed labware state.
