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
- Run `puda machine commands pipqubotv3` to understand available commands
- Follow constraints and sequencing in `references/pipqubotv3-machine.md`

### PipQuBot MOF Machine (`machine_id: "pipqubot_mof"`)

Use for **MOF liquid handling, deck operations, and position-dependent gantry movement**.

Capabilities:
- Pipetting workflows: aspirate, dispense, attach tip, drop tip, and blowout
- Load or remove labware in the eight-slot A1-D2 deck
- Move to a loaded labware well or move the Z axis by a signed relative distance

Use this machine when:
- The user explicitly targets the MOF PipQuBot
- A workflow uses MOF deck slots or labware wells
- A liquid-handling step requires the MOF gantry or Sartorius pipette

Before command generation:
- Refer to: [pipqubot-mof-machine](references/pipqubot_mof.md)
- Run `puda machine commands pipqubot_mof` to understand available commands
- Follow the position, movement, and tip-state constraints in `references/pipqubot_mof.md`

### PipQuBot XL Machine (`machine_id: "pipqubot-xl"`)

Use for **16-slot liquid handling and capper positioning**.

Capabilities:
- Pipetting workflows: aspirate, dispense, attach tip, drop tip, and blowout
- Load, inspect, or remove labware in the 16-slot A1-D4 deck
- Position the capper over a loaded labware well using the A axis

Use this machine when:
- The user explicitly targets the PipQuBot XL
- A workflow requires the XL 4x4 deck
- A workflow combines Sartorius pipetting with capper positioning

Before command generation:
- Refer to: [pipqubot-xl-machine](references/pipqubot_xl.md)
- Run `puda machine commands pipqubot-xl` to understand available commands and safety context
- Follow the homing, deck, tip-state, height, and capper constraints in `references/pipqubot_xl.md`

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
- Run `puda machine commands bioshake` to understand available commands


## PUDA 0.1.x edge behavior

Edges on puda SDK 0.0.18 or later (CLI 0.1.x) behave differently from older edges:

- **Commands:** an edge advertises only methods decorated `@command`. Always run `puda machine commands <machine_id>` rather than assuming a method is callable; undecorated driver methods (for example raw serial helpers) are not reachable over NATS.
- **Live readings are telemetry streams, not `tlm.pos`:** each edge publishes readings on `puda.<machine_id>.tlm.stream.<name>` (for example `status` for bioshake, `position` for centrifuge, `pose` for dobot, `pos` for the capper and pipetting gantries). Run `puda machine info <machine_id>` to list a machine's streams and `puda machine watch 'puda.<machine_id>.tlm.stream.>'` to read them. Heartbeat is every 5 s.
- **Failures raise:** a command that fails returns an error response instead of `{"result": false}`. For example, bioshake `home`, `open_clamp` and `close_clamp` now raise on timeout.
- **Safety context:** `puda machine commands` shows `@safety` notes (hazards, requirements) for motion and actuator commands; read them before generating a protocol.
- **Waiting:** a protocol step named `wait` with `params.seconds` is handled by the CLI and is not sent to a machine.

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
1. `bioshake` must not be shaking while any machine is operating on a Bioshake position.
2. `centrifuge` must not be spinning while any machine is operating on a Centrifuge position.
3. `opentrons` protocols must always end with no tip attached to any pipette.
4. `opentrons` deck slot (`location`) for every `load_labware` command must be explicitly confirmed by the user — **never assume a slot**.
5. `opentrons` `capture_image` must be its own standalone protocol — never combined with pipetting commands in the same protocol.
6. `balance` — always call `startup()` before reading and `shutdown()` after. Always tare before a dispense step. Always verify `fresh == True` before using a reading.

