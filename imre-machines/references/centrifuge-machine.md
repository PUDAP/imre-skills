---
name: centrifuge-machine
description: Generate commands for centrifuge workflows, including sample spin-downs, pelleting, clarification, and separation steps.
---

# Centrifuge Machine Skills

Generate commands for centrifuge workflows.

## Purpose

This reference helps generate commands for centrifuge operations used to spin down samples, pellet material, clarify suspensions, or separate phases before downstream processing.

## When to Use

Load this reference when:
- Users ask to centrifuge or spin down samples
- A workflow requires pelleting, clarification, or phase separation
- The user specifies centrifuge conditions such as RPM, RCF or duration

## Required Resources

Before generating commands, consult the puda CLI:
- **Machine Help**: Use `puda machine commands centrifuge` to see available commands, parameters, and options

Do not invent command names or parameters. If the CLI output does not expose a requested operation, explain that gap to the user instead of guessing.

## Command Structure

Each centrifuge machine command follows the standard protocol command structure (see protocol-generator reference). Key centrifuge-specific details:

- `machine_id`: Must be `"centrifuge"` (string)
- `name`: Must be a valid centrifuge command returned by `puda machine commands centrifuge`
- `params`: Use only parameters supported by the CLI for that command

## Required Information

Before generating a centrifuge command, confirm the run conditions the user cares about, such as:

- Duration
- Device

If required information is missing, do not assume it. Ask the user, or use an explicit placeholder only when the surrounding workflow requires drafting an incomplete command for review.

## Rules and Restrictions

Apply these rules when preparing centrifuge commands:

- Always run the `home` command before any operations
- Always run `close_lid` before `spin` command for the device
- Always ask which device if user did not specify, do not assume

## Instructions

1. **Consult CLI**: Run `puda machine commands centrifuge` to review available commands and parameters.
2. **Match the operation**: Choose the centrifuge command that best matches the requested.
4. **Generate command**: Create a command object with `machine_id: "centrifuge"`, a valid `name`, and supported `params`.

## Best Practices

- Keep centrifuge steps explicit about duration.
- Ask for missing run conditions instead of guessing.
