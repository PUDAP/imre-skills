---
name: qbot-cap-machine
description: Generate commands for QBot cap workflows that use fixed cap MTP positions.
---

# QBot Cap Machine Skills

Generate commands for QBot cap-based workflows.

## Purpose

This reference helps generate commands for QBot cap operations that use known cap MTP positions in the workspace.

## When to Use

Load this reference when:
- Users ask to work with caps using QBot
- A workflow needs cap movement or positioning using fixed MTP positions

## Required Resources

Before generating commands, consult the puda CLI:
- **Machine Help**: Use `puda machine commands capper` to see available commands, parameters, and options

Do not invent command names or parameters. If the CLI output does not expose a requested operation, explain that gap to the user instead of guessing.

## Command Structure

Each QBot cap machine command follows the standard protocol command structure (see protocol-generator reference). Key QBot cap details:

- `machine_id`: Must be `"capper"` (string)
- `name`: Must be a valid QBot cap command returned by `puda machine commands capper`
- `params`: Use only parameters supported by the CLI for that command

## Positions

If the user requests a position that is not listed here, verify the requested location before generating a command. Ask for the exact position or confirm whether one of the hardcoded positions should be used. Cap MTP positions are always in `[x, y]` coordinates.

### Cap MTP Positions

The cap MTP is a 4-row (A-D) x 6-column (1-6) grid.

| Well | Coordinates |
| ---- | ----------- |
| A1   | `[7, -62]` |
| A2   | `[27, -62]` |
| A3   | `[47, -62]` |
| A4   | `[67, -62]` |
| A5   | `[87, -62]` |
| A6   | `[107, -62]` |
| B1   | `[7, -82]` |
| B2   | `[27, -82]` |
| B3   | `[47, -82]` |
| B4   | `[67, -82]` |
| B5   | `[87, -82]` |
| B6   | `[107, -82]` |
| C1   | `[7, -102]` |
| C2   | `[27, -102]` |
| C3   | `[47, -102]` |
| C4   | `[67, -102]` |
| C5   | `[87, -102]` |
| C6   | `[107, -102]` |
| D1   | `[7, -122]` |
| D2   | `[27, -122]` |
| D3   | `[47, -122]` |
| D4   | `[67, -122]` |
| D5   | `[87, -122]` |
| D6   | `[107, -122]` |

## Required Information

Before generating a QBot cap command, confirm:
- Which cap MTP well should be used

If required information is missing, do not assume it. Ask the user, or use an explicit placeholder only when the surrounding workflow requires drafting an incomplete command for review.

## Rules and Restrictions

Apply these rules when preparing QBot cap commands:
- Use only the hardcoded positions listed in this document unless the user provides another exact position
- Ask for missing cap or position details instead of guessing

## Instructions

1. **Consult CLI**: Run `puda machine commands capper` to review available commands and parameters.
2. **Match the operation**: Choose the QBot cap command that best matches the requested cap operation.
3. **Resolve positions**: Use the positions information from this document when applicable.
4. **Generate command**: Create a command object with `machine_id: "capper"`, a valid `name`, and supported `params`.

## Best Practices

- Prefer named positions (e.g. Cap MTP A1) over repeating raw coordinates in explanations.
- Keep cap MTP positions explicit in every workflow step.
- Ask for missing cap operation details instead of guessing.
