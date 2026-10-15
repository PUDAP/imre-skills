---
name: pipqubot-xl-machine
description: Generate commands for the PipQuBot XL liquid handler and capper, including its 16-slot deck, pipetting, tip management, and capper positioning.
---

# PipQuBot XL Machine

Generate commands for the PipQuBot XL liquid handler and capper (`machine_id: "pipqubot-xl"`).

## Required resources

Before generating commands:

1. Run `puda machine commands pipqubot-xl` to inspect the live command signatures and safety context.
2. Consult [labware](labware.md) for valid labware names and wells.
3. Ask the user for any missing deck slot, labware, well, volume, or height. Do not guess.

## Capabilities

- Load, inspect, and remove labware on a 16-slot deck.
- Attach and eject pipette tips.
- Aspirate, dispense, and blow out with the Sartorius pipette.
- Position the capper over a loaded labware well using the A axis.
- Publish gantry and pipette positions through the `pos` telemetry stream.

## Deck

Valid deck slots are:

- `A1`, `A2`, `A3`, `A4`
- `B1`, `B2`, `B3`, `B4`
- `C1`, `C2`, `C3`, `C4`
- `D1`, `D2`, `D3`, `D4`

Use `load_deck(layout)` to establish a complete layout or `load_labware(deck_slot, labware_name)` for one slot. Labware must be loaded before any command targets one of its wells.

## Commands

The edge currently advertises:

- Deck: `get_deck`, `load_deck`, `load_labware`, `remove_labware`
- Pipetting: `attach_tip`, `aspirate_from`, `dispense_to`, `blowout`, `drop_tip`
- Capper: `move_capper`
- Lifecycle and control: `home`, `shutdown`, `pause`, `resume`, `cancel`, `reset`

Always treat `puda machine commands pipqubot-xl` as authoritative if this list differs from the live edge.

## Rules and sequencing

1. Call `home` before the first motion command unless the machine was explicitly confirmed as homed after its latest startup or reset.
2. Load the required deck layout before targeting any well.
3. Call `attach_tip` before `aspirate_from` or `dispense_to`.
4. End liquid-handling workflows without a tip attached by calling `drop_tip`.
5. `height_from_bottom` must be non-negative for aspiration, dispensing, tip dropping, and capper positioning.
6. Volumes passed as `amount` are integers in microliters.
7. `attach_tip` is idempotent: it reports `skipped: true` when a tip is already attached.
8. The `pos` telemetry stream reports gantry axes (`x`, `y`, `z`, `a`) and the pipette position every three seconds.

## Capper safety

`move_capper(deck_slot, well_name, height_from_bottom)` moves laterally and lowers the capper on the A axis.

- Hazards: collision and pinch point.
- Required before movement: the gantry is homed, target labware is loaded, and the path is clear.
- Never assume that the selected labware, well, or capper height is safe. Ask the user when any of these are unspecified.

## Command structure

Use standard PUDA protocol steps with:

- `machine_id`: `"pipqubot-xl"`
- `name`: one of the commands advertised by the live edge
- `params`: values matching the live command signature
