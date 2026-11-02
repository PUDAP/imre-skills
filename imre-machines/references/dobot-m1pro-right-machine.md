---
name: dobot-m1pro-right-machine
description: Generate safe PUDA commands for the right Dobot M1 Pro Cartesian robot and gripper.
---

# Dobot M1Pro Right Machine Skills

Generate commands for right Dobot M1Pro gripper workflows.

## Purpose

This reference helps generate commands for the right Dobot M1Pro using
Cartesian motion and gripper operations.

## When to Use

Load this reference when:
- The user explicitly requests the right Dobot
- A workflow assigns a transfer or Cartesian move to the right arm
- The right arm's pose, gripper, or motion commands are needed

## Required Resources

Before generating commands, consult the PUDA CLI:
- **Machine Help**: Run `puda machine commands dobot-right`
- **Machine Status**: Run `puda machine info dobot-right`

Do not invent commands or parameters. The live catalog is authoritative.

## Command Structure

Each command follows the standard PUDA protocol structure:

- `machine_id`: Must be `"dobot-right"`
- `name`: Must be returned by `puda machine commands dobot-right`
- `params`: Use only parameters supported by that live command
- `safety`: Copy the complete live safety object unchanged when advertised

## Positions

Positions use `[x, y, z, r]`. Commands that support `frame` accept `"robot"` or
`"work"`; set it explicitly.

The right edge currently configures this robot-frame home:

| Position | Coordinates |
| -------- | ----------- |
| HOME | `[200.223, 0.172, 238.248, -419.522]` |

Verify the deployed edge before relying on this value.

### Tube Positions

No calibrated right-arm tube-position table is currently recorded. Do not copy
the legacy `dobot-m1pro` or left-arm table. Ask for the exact right-arm pose.

### Centrifuge

No calibrated right-arm centrifuge-position table is currently recorded. Ask
for the centrifuge number, slot, and exact right-arm pose.

### BioShake Positions

No calibrated right-arm BioShake-position table is currently recorded. Ask for
the well and exact right-arm pose.

## Required Information

Before generating a right Dobot command, confirm:
- The source and destination
- The exact calibrated pose for each named position
- Whether each pose is in the robot or work frame
- Whether the gripper holds an object
- That the workspace and swept path are clear

If required information is missing, do not assume it.

## Rules and Restrictions

- Never reuse coordinates from `dobot-left` or legacy `dobot-m1pro` unless the
  operator explicitly confirms they were calibrated for `dobot-right`
- Use `pick_from` for a pick and `place_to` for a place
- Prefer `safe_move` for general positioning
- `home` opens the gripper and can release a held object
- Do not operate at a BioShake position while it is shaking
- Do not operate at a centrifuge position while it is spinning
- Pose telemetry proves communication, not servo enablement
- Use `reset` only with operator approval to clear errors and enable the arm;
  it does not home

## Instructions

1. **Consult CLI**: Run `puda machine info dobot-right` and
   `puda machine commands dobot-right`.
2. **Match the operation**: Select a live command that implements the request.
3. **Resolve positions**: Confirm exact right-arm poses and coordinate frames.
4. **Check safety**: Ensure the workspace and full path are clear.
5. **Generate command**: Use `machine_id: "dobot-right"`, supported parameters,
   and the exact live safety metadata.

## Best Practices

- Prefer named positions only after their right-arm coordinates are calibrated
- Keep source, destination, and frame explicit
- Read pose telemetry from the subject advertised by `puda machine info`
- Ask for missing transfer details instead of guessing
