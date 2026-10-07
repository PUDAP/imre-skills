# PipQuBot named-well position-check series

Use this pattern for repeated operator requests to move the PipQuBot endpoint among named wells, either bare or with a staged disposable tip.

## Per-move safety gate

1. Recheck fresh PUDA state, edge health/restart count, and motion-queue pending/ack-pending counters before every move; an earlier idle result is not current clearance.
2. Capture a fresh enclosure frame. Any person, head, arm, hand, or fingers inside or crossing the enclosure is a hard stop. Dispatch nothing, confirm the machine remains idle and the queue empty, then capture a new frame only after the operator reports clearance.
3. Treat physical and software tip state separately. For a bare-endpoint move, compare the fresh endpoint against a known bare reference when visibility is ambiguous. For an attached-tip move, preserve the verified logical/physical attachment and do not home.
4. Confirm the named labware is logically loaded. If the operator newly placed labware in a previously empty slot, include `load_labware` before `move_to_well`; loading the logical deck does not itself prove physical placement.

## Protocol shape

- Bare position check on already-loaded labware: one `move_to_well(deck_slot, well_name)` command. No home, attach, aspiration, dispense, blowout, or ejection.
- Newly placed destination labware: `load_labware`, then `move_to_well`.
- Fresh tip pickup and positioning: follow `pipqubot-staged-tip-pickup.md`; use home, load exact tiprack/destination definitions, `attach_tip`, then `move_to_well`, and stop with the tip attached.
- Reuse an existing validated protocol only when target slot, well, labware, and tip-state assumptions match exactly. Give each execution a unique run-log filename so a repeated run does not overwrite prior evidence.

## Stateful attached-tip continuation evidence

When a later position check says the tip is still attached, do not rely on conversational continuity alone. Before omitting home or pickup, establish one uninterrupted machine-state chain:

1. Identify the immediately preceding successful `attach_tip` or attached-tip movement and its COMPLETE boundary.
2. Confirm the edge start time and restart count are unchanged, the machine is idle with no active run, and pending/ack-pending queue counters are zero.
3. Inspect logs since that boundary for any full home/Sartorius `RZ`, `RE30`/tip-ejection, `drop_tip`, new `attach_tip`, aspiration, dispense, or blowout event. Any such event can invalidate the inherited state.
4. Require a fresh frame showing the disposable tip still attached and plausibly straight. If software/logical and physical evidence disagree, stop rather than forcing a move.
5. Use a one-command `move_to_well` continuation with no home, reload, pickup, or liquid handling. Verify the emitted destination includes the configured tip-length Z offset, then confirm the tip remains attached in the post-move frame.

## Eject-then-home endpoint

For an explicit request to eject the retained tip and then home:

1. Preserve attached-tip state until ejection; do not home first because Sartorius initialization can clear the software flag while leaving a physical tip attached.
2. Use `drop_tip` to the configured trash-bin well, applying the physical tip offset, followed by `home` in the same validated protocol. Protocol sequencing ensures home runs only after successful ejection.
3. Verify exactly one ejection command (for this installation, `RE30`), `Tip Ejection Complete`, `Tip dropped successfully`, full gantry home, and Sartorius `RZ` initialization.
4. Capture a post-run frame showing a bare endpoint at a plausible home pose. If a person enters after COMPLETE, dispatch nothing and recheck fresh idle/no-run and empty queue state before reporting.

## Duplicate-motion prevention after an interrupted reply

A model/UI response interruption can occur after the physical protocol has already completed. If the operator repeats the same instruction:

1. Do not immediately resend it.
2. Inspect authoritative `command_log`/run records, the retained run log, fresh machine state, and queue counters.
3. If START, target command success, and COMPLETE are present and the machine is idle with an empty queue, report the existing completed run and do not duplicate the motion.
4. If the command boundary is uncertain, apply the generic interrupted-run rule and do not retry automatically.
5. Treat `/stop` as stopping agent work, not proof of physical cancellation; always reconcile live run/queue state before any later dispatch.

## Verification and reporting

- Verify the edge-emitted safe-Z lift, lateral move, final descent, and driver completion coordinates.
- `move_to_well` returns driver-reported completion coordinates, not an independent controller pose measurement. If the deployed read-only query path is known unsafe or incompatible, state this limitation rather than launching it merely for formality.
- Capture a post-move frame. If someone enters only after COMPLETE, do not claim they were present during motion; verify the machine remains idle, send no further motion, and record the post-completion entry separately.
- Report protocol/run ID, exact target, tip state, excluded operations, final PUDA/edge/queue state, and whether physical position is camera-supported, driver-reported, or independently measured.
