# PipQuBot staged tip pickup and named-well positioning

Use this pattern when an operator explicitly asks to pick up a disposable tip and then position over named labware without aspirating or dispensing.

## Command sequence

1. Query `puda machine commands pipqubot_mof`; copy the live `home`, labware-load, `attach_tip`, and `move_to_well` schemas.
2. Confirm exact tiprack and destination `(deck_slot, well_name)` pairs. Do not reinterpret Qubot as Dobot.
3. Before motion, require idle/no active run, empty pending and unacknowledged queues, healthy edge, a fresh camera frame with no person/hand or obvious obstruction, and a known physical-tip state.
4. Home before loading the logical deck when building a self-contained protocol. Load the exact tiprack and destination labware identifiers.
5. Call the existing `attach_tip`; do not emulate pickup with raw movement commands. Then call the existing `move_to_well`; do not create a one-off movement function.
6. If the operator requested a staged pickup-and-position endpoint, stop with the tip attached. Do not add aspiration, dispensing, mixing, blowout, or automatic ejection.

## Geometry and state checks

- Resolve coordinates through the deployed runtime definition and machine transform, not by hand from the JSON alone.
- Record tiprack approach and insertion positions. Confirm the insertion uses the labware `insert_depth` and that the driver homes Z after seating the tip.
- Verify the destination twice: no-tip and attached-tip Z targets differ. The destination after successful pickup must use attached-tip Z.
- Treat software state and physical state separately. A successful `attach_tip` response plus logs proves the software transition and commanded physical sequence; use a post-motion camera or operator confirmation when physical attachment must be claimed.

## Stateful continuation: relative Z movement

A staged workflow may continue with a signed `move_z_relative` while the tip remains attached. This also covers **position-only checks at a named aspiration/dispense height** where the operator explicitly wants motion but no piston action.

1. Do **not** prepend `home` to a relative-movement continuation: homing changes the reference pose and defeats the requested displacement. The “home first” rule applies to a new self-contained workflow, not to a continuation whose meaning depends on a verified current pose.
2. Reconstruct the current X/Y/Z and attached-tip state from the immediately preceding successful response and controller logs. Recheck idle/no active run, unchanged edge start/restart state, empty queues, and a fresh clear-enclosure image immediately before dispatch.
3. Interpret “down” as a negative Z delta for this driver. Compute `final_z = current_z + distance_mm` and verify X/Y remain unchanged.
4. For “move to well X at aspiration height H, but do not aspirate,” first require a verified `move_to_well` top pose at that same slot/well. From that pose compute `distance_mm = -(labware.insert_depth - H)` and `target_z = top_z + distance_mm`. Read `insert_depth` from the deployed labware definition and require `0 <= H <= insert_depth`; never substitute an `aspirate_from` command just to obtain the positioning side effect. If the current pose is not already verified at that exact slot/well, issue and verify `move_to_well` before the descent rather than assuming X/Y continuity.
5. When descending into a named well, compare requested insertion depth with the deployed well depth and centered geometry. Refuse or ask before moving if the modeled clearance is exhausted; camera evidence cannot prove hidden bottom clearance.
6. Use the existing `move_z_relative(distance_mm=...)` command and verify the emitted controller target plus final response. Preserve and report the attached-tip state, and explicitly report that no aspiration, dispense, blowout, pickup, or ejection occurred.
7. Capture a post-move frame. If a person enters only after the command completed, record that timing, dispatch nothing further, and do not mischaracterize the completed move as having occurred with a person inside. Require a fresh clear frame before any later motion.

## Homing after a staged insertion

For an explicit operator request to home after the tip has entered a well:

1. Capture a fresh image and verify no person/hand or obvious obstruction; confirm the visible tip remains aligned in the well before retraction.
2. Use the first-class direct command `puda machine home pipqubot_mof`, not a new one-step protocol.
3. Verify full gantry-home and Sartorius-initialization logs, then capture a post-home image.
4. **Full home/Sartorius initialization clears this driver's software tip-attached state even when the physical disposable tip remains attached.** Report the resulting mismatch explicitly. Do not call `attach_tip` afterward on the assumption that it will idempotently skip: with software state cleared, it performs a real approach/insertion stroke and can reseat, bend, or damage an already attached physical tip.
5. Before any later pickup, reconcile state using fresh camera/operator evidence. If a physical tip remains after home, remove it through an explicitly authorized safe method before another `attach_tip`. If an operator enters the enclosure, dispatch no motion; capture a new frame after the enclosure clears and record whether the tip is visibly present or absent.

## Repeated-pickup hazard

When a user repeats “pick up from the same tiprack well” after a prior successful pickup:

1. Treat the rack well as consumed and the physical tip as attached until removal is independently established. A new chat, `/new`, context reset, or newly generated protocol resets conversational intent only; it does **not** remove a physical tip, replenish a consumed well, clear a live queue, or otherwise reset machine state.
2. A repeated natural-language instruction is not evidence that the previous tip disappeared. Do not create a protocol that homes and then calls `attach_tip` merely to rely on idempotency.
3. If the user wants to continue positioning with the existing tip, omit pickup and preserve the verified current tip state. If they require a new tip, require removal/ejection of the existing tip and an occupied replacement well.
4. After the operator reports manual removal and rack replenishment, do not dispatch immediately. Capture a fresh frame after hands leave the enclosure and independently check: bare permanent nozzle, no person/hand, requested rack present, and plausible occupancy of the requested well. Operator confirmation authorizes inspection but does not replace physical verification.
5. Only after physical no-tip state agrees with cleared software state may a fresh self-contained protocol home and call `attach_tip`. If the image cannot resolve the requested well's occupancy, state the uncertainty and rely on explicit operator confirmation for occupancy while still requiring the no-tip and clear-enclosure checks.
6. If a duplicate insertion stroke nevertheless occurred, inspect controller logs and fresh imagery for tip bending/alignment, stop further liquid handling, and report hidden tip integrity as uncertain even when the command returned success.

## Interrupted pickup rule

`attach_tip` may be software-idempotent, but an interrupted pickup can leave physical and software states inconsistent. Never blindly resend it. Inspect the protocol boundary, edge/controller logs, queue state, software tip state, and camera evidence. If physical attachment remains uncertain, stop and ask the operator.

## Post-run verification

Require all of:

- pickup approach, insertion, `Tip attached successfully`, and post-pickup Z-home logs;
- destination `move_to_well` logs using attached-tip Z;
- idle/no active run, healthy edge, zero pending/unacknowledged queue entries;
- logical deck records both labwares;
- post-operation image with no obvious collision, plus explicit confidence/uncertainty about visible tip attachment;
- protocol ID, run ID, exact targets, tip state, and absence of liquid handling recorded in `project.md`.
