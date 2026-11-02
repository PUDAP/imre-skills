---
name: dobot-m1pro-left-machine
description: Generate safe PUDA commands for the left Dobot M1 Pro Cartesian robot and gripper.
---

# Dobot M1Pro Left Machine Skills

Generate commands for left Dobot M1Pro gripper workflows.

## Purpose

This reference helps generate commands for the left Dobot M1Pro using Cartesian
motion and gripper operations.

## When to Use

Load this reference when:
- The user explicitly requests the left Dobot
- A workflow assigns a transfer or Cartesian move to the left arm
- The left arm's pose, gripper, or motion commands are needed

## Required Resources

Before generating commands, consult the PUDA CLI:
- **Machine Help**: Run `puda machine commands dobot-left`
- **Machine Status**: Run `puda machine info dobot-left`

Do not invent commands or parameters. The live catalog is authoritative.

## Command Structure

Each command follows the standard PUDA protocol structure:

- `machine_id`: Must be `"dobot-left"`
- `name`: Must be returned by `puda machine commands dobot-left`
- `params`: Use only parameters supported by that live command
- `safety`: Copy the complete live safety object unchanged when advertised

## Positions

Positions use `[x, y, z, r]`. Commands that support `frame` accept `"robot"` or
`"work"`; set it explicitly.

The left edge currently configures this robot-frame home:

| Position | Coordinates |
| -------- | ----------- |
| HOME | `[200, 0, 240, -22.5]` |

Verify the deployed edge before relying on this value.

### Tube Positions

No calibrated left-arm tube-position table is currently recorded. Do not copy
the legacy `dobot-m1pro` or right-arm table. Ask for the exact left-arm pose.

### Centrifuge

No calibrated left-arm centrifuge-position table is currently recorded. Ask
for the centrifuge number, slot, and exact left-arm pose.

### BioShake Positions

No calibrated left-arm BioShake-position table is currently recorded. Ask for
the well and exact left-arm pose.

## Required Information

Before generating a left Dobot command, confirm:
- The source and destination
- The exact calibrated pose for each named position
- Whether each pose is in the robot or work frame
- Whether the gripper holds an object
- That the workspace and swept path are clear

If required information is missing, do not assume it.

## Rules and Restrictions

- Never reuse coordinates from `dobot-right` or legacy `dobot-m1pro` unless the
  operator explicitly confirms they were calibrated for `dobot-left`
- Use `pick_from` for a pick and `place_to` for a place
- Prefer `safe_move` for general positioning
- `home` opens the gripper and can release a held object
- Do not operate at a BioShake position while it is shaking
- Do not operate at a centrifuge position while it is spinning
- Pose telemetry proves communication, not servo enablement
- Use `reset` only with operator approval to clear errors and enable the arm;
  it does not home

## Instructions

1. **Consult CLI**: Run `puda machine info dobot-left` and
   `puda machine commands dobot-left`.
2. **Match the operation**: Select a live command that implements the request.
3. **Resolve positions**: Confirm exact left-arm poses and coordinate frames.
4. **Check safety**: Ensure the workspace and full path are clear.
5. **Generate command**: Use `machine_id: "dobot-left"`, supported parameters,
   and the exact live safety metadata.

## Best Practices

- Prefer named positions only after their left-arm coordinates are calibrated
- Keep source, destination, and frame explicit
- Read pose telemetry from the subject advertised by `puda machine info`
- Ask for missing transfer details instead of guessing
