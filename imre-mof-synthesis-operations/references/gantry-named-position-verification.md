# Gantry Named-Position Verification

Use this pattern when a PUDA gantry or capper must move to a named rack coordinate without manipulating labware.

## Motion pattern

1. Run `puda machine commands <machine-id>` and confirm the safe transit and read-only position commands actually exposed by the edge.
2. Resolve `(machine_id, station)` from validated project protocols or `project.md`; never borrow coordinates from another machine's station with the same label.
3. Confirm `puda machine state <machine-id>` is `idle`.
4. Run a one-command protocol using the safe transit primitive and only X/Y/Z parameters. Do not use `pick_*`, `place_*`, clamp, cap, or decap commands for a motion-only request.
5. Save the movement output in its own timestamped log and capture the run ID.
6. Once the machine returns to `idle`, run a separate edge-mediated position query protocol and save a second log.
7. Compare measured X/Y/Z with the named target and report any additional axis independently.
8. Append creation and run entries to `project.md` using timestamps from protocol files and run logs.

## Worked capper example

A project may define capper-rack A1 as `x=7, y=-62, z=-78.5`. A safe motion-only command is then:

```json
{
  "name": "safe_move_to",
  "machine_id": "capper",
  "params": {"x": 7, "y": -62, "z": -78.5}
}
```

Verification should use the capper's exposed read-only command:

```json
{
  "name": "get_position",
  "machine_id": "capper",
  "params": {}
}
```

A response such as `{x: 7, y: -62, z: -78.5, a: 14736}` verifies the named XYZ station while preserving `a` as an independently reported machine axis. The numeric values above are an example from one project and must be re-resolved before future execution.

## Audit checklist

- Machine state checked before movement
- Named coordinates resolved for the correct machine
- Safe transit primitive used
- No unintended pick/place/clamp/process command
- Movement run ID and log retained
- Independent measured-position run completed
- Final PUDA state is `idle`
- `project.md` records protocol creation and both runs
