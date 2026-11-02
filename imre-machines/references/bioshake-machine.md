---
name: bioshake-machine
description: Generate commands for the BioShake plate shaker, including shaking, heating, combined heat-and-shake holds, clamping, and homing.
---

# BioShake Machine

Generate commands for the BioShake plate shaker (`machine_id: "bioshake"`).

## Required resources

Before generating commands:

1. Run `puda machine commands bioshake` to inspect the live command signatures, docstrings, and safety context. The `heat_shake` docstring lists its tolerances and abort conditions.
2. Ask the user for any missing temperature, speed, or duration. Do not guess.

## Capabilities

- `shake`: shake at a target RPM for a duration, then stop.
- `set_temp`: heat or cool to a target temperature and hold it for a duration.
- `heat_shake`: heat and shake together as one blocking, measured operation.
- `close_clamp`, `open_clamp`, `home`: secure the plate and return the table to its locked home position.
- Publish speed, temperature, shake state, and clamp state through the `state` telemetry stream.

## Combined heating and shaking

Use `heat_shake` whenever a step needs the plate held at temperature while shaking. Do not overlap `set_temp` and `shake`, or dispatch any other BioShake commands while it runs.

```json
{
  "machine_id": "bioshake",
  "name": "heat_shake",
  "params": {
    "temperature": 40,
    "speed": 600,
    "duration": 300,
    "plate_seated": true
  }
}
```

- `duration`, `heatup_timeout` (default 600), and `speed_timeout` (default 60) are in seconds. `temperature` uses 0.1 °C increments; `speed` is an integer RPM.
- `plate_seated: true` is an operator attestation; the BioShake has no plate sensor. Set it only after the user confirms the plate is seated.
- The command refuses to start unless the clamp is closed and the shaker is stopped at home with zero RPM, so run `close_clamp` (and `home` if needed) first.
- The `duration` timer starts only after the temperature is stable and the speed is within ±2% of target, so the step takes longer than `duration`.
- The response reports hold time, temperature and speed extrema, and `shutdown_verified`. Record it as run evidence. Plate temperature is not liquid temperature.

## Rules and restrictions

- Keep every other machine away from BioShake positions for the whole `shake` or `heat_shake` step.
- Open the clamp only after the table is homed. For clamp-state checks and serial recovery, see the `imre-mof-synthesis-operations` skill.
