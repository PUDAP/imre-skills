---
name: imre-machines
description: Discover PUDA machine capabilities at imre and choose the right machines for protocol generation. Use when you need to know more about a machine, how to use a machine, or how to generate commands and protocols for any PUDA-connected machine.
---

# PUDA Machines

## Goal

Provide machine-selection and capability guidance for PUDA workflows, then load the correct machine reference before generating commands.

## Critical Rule

If you are unsure which machine should be used for a command, **ask the user** before proceeding.  
Do **not** assume.

## Environment-Scoped Vision Gate

Before a physical IMRE workflow whose correctness or safety depends on visible setup, load `puda-machine-vision-validation` from `PUDAP/puda-vision-validation` (install with `puda skills install pudap/puda-vision-validation` if unavailable). Confirm `puda env current` is `imre`, use the current IMRE machine reference and camera/pose, and capture fresh evidence without movement when possible. Never reuse BEARS or NTU camera calibration, workspace polygons, coordinates, or prior confirmations.

## Machine Capabilities and When to Use

### PipQuBotV3 Machine (`machine_id: "pipqubotv3"`)

Use for **liquid handling and deck operations**.

Capabilities:
- Pipetting workflows: aspirate, dispense, attach tip, drop tip
- Deck and labware workflows: load deck, position-dependent operations
- Sequenced robotic handling steps in wet-lab protocols

Use this machine when:
- The task is about moving liquids between wells/labware
- The user mentions tip usage, aspiration/dispensing, or deck slots/labware setup

Before command generation:
- Refer to: [pipqubotv3-machine](references/pipqubotv3-machine.md)
- If deck/tray occupancy, labware, tips, tools, or requested positions affect execution, apply `puda-machine-vision-validation` using an IMRE-scoped PipQuBotV3 camera/workspace profile.
- Run `puda machine commands pipqubotv3` to understand available commands
- Follow constraints and sequencing in `references/pipqubotv3-machine.md`

### Centrifuge Machine (`machine_id: "centrifuge"`)

Use for **centrifugation, spin-downs, and phase or pellet separation**.

Capabilities:
- Sample spin-downs before or after handling steps
- Separation workflows based on centrifugal force
- Pelleting, clarification, and phase-separation preparation steps

Use this machine when:
- The user asks to centrifuge, spin, spin down, pellet, or clarify samples

Before command generation:
- Refer to: [centrifuge-machine](references/centrifuge-machine.md)
- If a suitable passive camera exists, apply `puda-machine-vision-validation` to visible rotor/tube occupancy, balance pattern, lid state, and clearance; telemetry/interlocks must still prove stopped/locked state.
- Run `puda machine commands centrifuge` to understand available commands
- Follow constraints in `references/centrifuge-machine.md`

### Dobot M1Pro Machine (`machine_id: "dobot-m1pro"`)

Use for **gripper-based tube transfers between fixed positions**.

Capabilities:
- Pick-and-place tube handling with a gripper
- Moving tubes between predefined source and destination positions
- Position-based transfer steps between pipqubotv3, bioshake, centrifuge machines

Use this machine when:
- The user asks to transfer tubes with a gripper
- The workflow involves moving tubes between known hardcoded positions
- A step references Dobot M1Pro positions such as centrifuge tube or MTP coordinates

Before command generation:
- Refer to: [dobot-m1pro-machine](references/dobot-m1pro-machine.md)
- Before camera-guided transfer, apply `puda-machine-vision-validation` with the current IMRE camera pose/calibration, source and destination positions, target tube, gripper state, and keep-out zones; validation-only capture must not move the arm.
- Run `puda machine commands dobot-m1pro` to understand available commands
- Follow constraints in `references/dobot-m1pro-machine.md`

### BioShake Machine (`machine_id: "bioshake"`)

Use for **shaking, heating, and plate clamping operations**.

Capabilities:
- Shaking at a specified RPM for a given duration
- Heating (or cooling) to a target temperature and holding for a given duration
- Clamping and unclamping plates on the shaker
- Homing the shaker to its locked home position

Use this machine when:
- The user asks to shake, vortex, or mix a plate on a shaker
- The user asks to heat or incubate a plate at a specific temperature
- The user asks to clamp or unclamp a plate on the BioShake
- The workflow requires holding a plate at temperature while shaking

Before command generation:
- If visible plate placement, clamp state, or surrounding clearance matters and a suitable passive camera exists, apply `puda-machine-vision-validation`; driver telemetry must still prove stopped/temperature state.
- Run `puda machine commands bioshake` to understand available commands


## Selection Workflow

1. Parse user intent and identify the tasks.
2. Match intent to the machine capabilities above.
3. If machine selection is unclear or ambiguous, **ask the user** and wait for confirmation.
4. Load the corresponding reference file and CLI help.
5. Generate commands only after machine choice is confirmed.

## Output Guidance

When answering machine-selection questions:
- State the recommended machine and a one-line reason tied to capability.
- If uncertain, ask a direct clarification question instead of guessing.

## Critical sequencing rules
0. When execution depends on visible physical setup, run `puda-machine-vision-validation` with an **IMRE-scoped** machine/camera profile; do not reuse calibration, geometry, credentials, or confirmations from BEARS/NTU.
1. `bioshake` must not be shaking while any machine is operating on a Bioshake position.
2. `centrifuge` must not be spinning while any machine is operating on a Centrifuge position.
3. `opentrons` protocols must always end with no tip attached to any pipette.
4. `opentrons` deck slot (`location`) for every `load_labware` command must be explicitly confirmed by the user — **never assume a slot**.
5. `opentrons` `capture_image` must be its own standalone protocol — never combined with pipetting commands in the same protocol.
6. `balance` — always call `startup()` before reading and `shutdown()` after. Always tare before a dispense step. Always verify `fresh == True` before using a reading.

