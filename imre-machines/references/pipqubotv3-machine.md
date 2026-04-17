---
name: pipqubotv3-machine
description: Generate commands for PipQuBotV3 liquid handling robots, including aspiration, dispensing, tip management, and deck configuration.
---

# PipQuBotV3 Machine Skills

Generate commands for PipQuBotV3 liquid handling robots.

## Purpose

This skill enables generation of commands for PipQuBotV3 liquid handling robots. These commands automate liquid handling operations including aspiration, dispensing, tip management, and deck configuration.

## When to Use

Load this skill when:
- Users describe protocols that need to be executed on liquid handling robots
- Converting manual lab protocols into automated puda protocols
- Processing natural language instructions for liquid handling operations
- Working with liquid handling workflows involving aspiration, dispensing, or tip management

## Required Resources

**IMPORTANT**: Before generating any commands, **always consult these resources**:

1. **Consult CLI**: Run `puda machine commands pipqubotv3` to review available commands and parameters
2. **Labware Help**: See [labwares](labware.md) for available labware and details

**Do not generate commands without first consulting these resources** to ensure accuracy and compatibility.

## Command Structure

Each PipQuBotV3 machine command follows the standard protocol command structure (see protocol-generator reference). Key PipQuBotV3-specific details:

- `machine_id`: Must be `"pipqubotv3"` (string)

## Rules and Restrictions

The following rules **must** be strictly followed when generating PipQuBotV3 machine commands:

### Handling Missing Information

- If any information is missing from the user's request, **do not assume or guess values**. Use a placeholder value (e.g., `"PLACEHOLDER"` or `"?"`) in the command and explicitly ask the user to provide the missing information.
- If the labware only has one well (e.g., "A1"), then it is safe to assume that well name is "A1" without asking the user

### Available Deck Slots
- **Valid deck_slots**: A1, A2, B1, B2, C1, C2, D1, D2
- Use these slots for labware placement and operations

### Command Restrictions
- **`height_from_bottom` constraint**: Must be non-negative (>= 0)

### Command Dependencies and Sequencing

**Important**: If the user's request contains invalid commands, incompatible labware, incorrect sequencing, or violates any constraints described in this document, **do not blindly follow the request**. Instead, identify the specific issue and clearly explain to the user what is wrong and why it cannot be executed.

**Critical sequencing rules:**
1. **`home`**: Must always be the **very first** PipQuBotV3 machine command in any protocol, before any other operations
2. **`load_deck`**: Must always be executed after `home` and before any other PipQuBotV3 machine commands.
3. **`attach_tip`**: May only occur before `drop_tip`; must be called before any `aspirate_from` or `dispense_to` that use the tip
4. **`drop_tip`**: May only occur after `attach_tip`; workflows must always end without a tip attached

**Labware compatibility:**
- **`aspirate_from`**: Can only be performed on `polyelectric_8_wellplate_30000ul` labware
- **`dispense_to`**: Can only be performed on:
  - `MEA_cell_MTP`
  - `polyelectric_8_wellplate_30000ul`
  - `trash_bin`
- **`attach_tip`**: Can only be performed on `tiprack` labware
- **`drop_tip`**: Can only be performed on `trash_bin` labware

## Instructions

1. **Consult Resources**: Consult the resources listed in the "Required Resources" section above before generating any commands.

2. **Verify sequencing and constraints**: **Always** verify that commands follow all rules in the "Rules and Restrictions" section, including: critical sequencing (home -> load_deck -> attach_tip -> ... -> drop_tip so the workflow ends with no tip attached), valid deck slots, labware compatibility, command restrictions, and proper handling of missing information

3. **Generate command**: Create a command object with `machine_id: "pipqubotv3"`, appropriate `name` and `params`
