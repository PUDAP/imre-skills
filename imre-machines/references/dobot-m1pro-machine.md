---
name: dobot-m1pro-machine
description: Generate commands for Dobot M1Pro gripper workflows that transfer tubes between fixed hardcoded positions.
---

# Dobot M1Pro Machine Skills

Generate commands for Dobot M1Pro gripper-based tube transfer workflows.

## Purpose

This reference helps generate commands for Dobot M1Pro operations that use a gripper to pick up and move tubes between known positions in the workspace.

## When to Use

Load this reference when:
- Users ask to transfer tubes with a gripper
- A workflow needs pick-and-place tube movement between fixed positions

## Required Resources

Before generating commands, consult the puda CLI:
- **Machine Help**: Use `puda machine commands dobot-m1pro` to see available commands, parameters, and options

Do not invent command names or parameters. If the CLI output does not expose a requested operation, explain that gap to the user instead of guessing.

## Command Structure

Each Dobot M1Pro machine command follows the standard protocol command structure (see protocol-generator reference). Key Dobot M1Pro details:

- `machine_id`: Must be `"dobot-m1pro"` (string)
- `name`: Must be a valid Dobot M1Pro command returned by `puda machine commands dobot-m1pro`
- `params`: Use only parameters supported by the CLI for that command

## Positions

If the user requests a position that is not listed here, verify the requested location before generating a command. Ask for the exact position or confirm whether one of the hardcoded positions should be used. Positions are always in `[x, y, z, r]` coordinates.

### Centrifuge

There are 2 centrifuges, both have 6 slots in a circular formation. Slots are evenly spaced at 60° intervals.

**Centrifuge 2 Positions**
| Slot | Coordinates            |
| ---- | ---------------------- |
| 1    | `[214, -77, 82, 20]`   |
| 2    | `[228, -54, 82, -40]`  |
| 3    | `[254, -54, 82, -100]` |
| 4    | `[268, -77, 82, 20]`   |
| 5    | `[254, -100, 82, 140]` |
| 6    | `[228, -100, 82, 80]`  |

**Centrifuge 1 Positions**
| Slot | Coordinates           |
| ---- | --------------------- |
| 1    | `[214, 73, 82, 20]`   |
| 2    | `[228, 96, 82, -40]`  |
| 3    | `[254, 96, 82, -100]` |
| 4    | `[268, 73, 82, 20]`   |
| 5    | `[254, 50, 82, 140]`  |
| 6    | `[228, 50, 82, 80]`   |

### BioShake Positions

The BioShake is a 4-row (A-D) x 6-column (1-6) grid.

| Position | Coordinates            |
| -------- | ---------------------- |
| A1       | `[283, -177, 57, -70]` |
| A2       | `[263, -176.8, 57, -70]` |
| A3       | `[243, -176.6, 57, -70]` |
| A4       | `[223, -176.4, 57, -70]` |
| A5       | `[203, -176.2, 57, -70]` |
| A6       | `[183, -176, 57, -70]` |
| B1       | `[283, -196.83, 57, -70]` |
| B2       | `[263, -196.63, 57, -70]` |
| B3       | `[243, -196.43, 57, -70]` |
| B4       | `[223, -196.23, 57, -70]` |
| B5       | `[203, -196.03, 57, -70]` |
| B6       | `[183, -195.83, 57, -70]` |
| C1       | `[283, -216.67, 57, -70]` |
| C2       | `[263, -216.47, 57, -70]` |
| C3       | `[243, -216.27, 57, -70]` |
| C4       | `[223, -216.07, 57, -70]` |
| C5       | `[203, -215.87, 57, -70]` |
| C6       | `[183, -215.67, 57, -70]` |
| D1       | `[283, -236.5, 57, -70]` |
| D2       | `[263, -236.3, 57, -70]` |
| D3       | `[243, -236.1, 57, -70]` |
| D4       | `[223, -235.9, 57, -70]` |
| D5       | `[203, -235.7, 57, -70]` |
| D6       | `[183, -235.5, 57, -70]` |

## Required Information

Before generating a Dobot M1Pro command, confirm:
- Which tube should be moved

If required information is missing, do not assume it. Ask the user, or use an explicit placeholder only when the surrounding workflow requires drafting an incomplete command for review.

## Rules and Restrictions

Apply these rules when preparing Dobot M1Pro commands:
- Use only the hardcoded positions listed in this document unless the user provides another exact position
- Use `pick_from` when picking tubes, it will automatically close the gripper
- Use `place_to` when placing tubes, it will automatically open the gripper
- Ask for missing source or destination details instead of guessing

## Instructions

1. **Consult CLI**: Run `puda machine commands dobot-m1pro` to review available commands and parameters.
2. **Match the operation**: Choose the Dobot M1Pro command that best matches the requested tube transfer.
3. **Resolve positions**: Use the positions information from this document when applicable.
4. **Generate command**: Create a command object with `machine_id: "dobot-m1pro"`, a valid `name`, and supported `params`.

## Best Practices

- Prefer named positions (e.g. BioShake A1, Centrifuge 2 Slot 3) over repeating raw coordinates in explanations.
- Keep source and destination positions explicit in every transfer step.
- Ask for missing transfer details instead of guessing.