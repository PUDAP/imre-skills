# PipQuBot Sartorius liquid-handling semantics

Use this reference when diagnosing or changing `aspirate_from` / `dispense_to` behavior for a Sartorius rLINE pipette behind a PipQuBot PUDA edge.

## Command selection

The driver must track successfully aspirated volume for the current tip.

- **Full-volume dispense:** when `dispense_amount == tracked_aspirated_volume`, send blowout **`RB`**. Do not send `RO<steps>`.
- **Partial dispense:** when `dispense_amount < tracked_aspirated_volume`, send relative outward movement **`RO<steps>`**, then decrement tracked volume only after success.
- Clear tracked volume only after a successful `RB`.
- Do not decrement or clear software volume state after a rejected or uncertain controller command.

Minimal regression examples:

```text
tracked=100 uL, dispense=100 uL -> exactly RB; tracked becomes 0
tracked=100 uL, dispense=40 uL  -> RO<40 uL in steps>; tracked becomes 60
```

## Sartorius response handling

Sartorius immediate errors use `er1`–`er4` (one `r`), not the generic string `err`:

| Reply | Meaning |
|---|---|
| `er1` | command not understood |
| `er2` | command would result in an out-of-bounds state |
| `er3` | checksum/LRC mismatch |
| `er4` | drive is busy and cannot answer the command/query |

Parse these replies explicitly and raise an execution error. Never emit a success log, update tracked liquid state, or publish PUDA success after an `erN` reply.

A useful regression injects raw `1er2` as the serial response and asserts that the public operation raises rather than returning success.

## Initialization pitfall

`RZ` may acknowledge before the piston drive becomes query-ready. A `DR`, `DP`, or other query sent immediately afterward can return `er4`.

- Do not add speculative post-`RZ` queries to a production startup path merely to diagnose a dispense failure.
- If model/resolution discovery is genuinely required, wait for documented readiness or use bounded polling that treats `er4` as busy, while preserving all other errors.
- Ensure a failed startup cannot enter an unbounded restart/home loop; stop the edge before iterating on initialization.

## Physical evidence limits

Controller acceptance is not proof of liquid transfer. Keep these separate:

1. gantry reached the requested well/height;
2. Sartorius accepted the piston command;
3. liquid was physically aspirated or dispensed.

For aspiration above the well bottom, check whether the liquid surface reaches that height. For a cylindrical well:

```text
minimum volume to reach height h = pi * (diameter / 2)^2 * h
```

Use consistent units (`mm^3 == uL`). A valid robot position can still aspirate air.

If physical volume is uncertain, do not rerun the transfer automatically. Reconcile attached-tip state, residual liquid, source/destination volumes, and piston state first.

## Stateful continuation after tip pickup

When a prior verified stage intentionally ends with a Sartorius tip attached, a later aspiration or dispense is a **stateful continuation**, not a fresh self-contained workflow.

1. Do **not** prepend `home` or restart/recreate the edge merely to satisfy a generic “home first” template. Full gantry home runs Sartorius `RZ`, which clears this driver's software tip and tracked-volume state even if the physical tip remains attached.
2. Before continuing, prove continuity: edge restart count and start time unchanged since pickup, recent logs contain the successful attachment boundary and no later `RZ`/ejection, PUDA is idle with no active run, queues have zero pending/unacknowledged work, and a fresh camera frame shows the tip still attached with the enclosure clear.
3. Ask for `height_from_bottom` when it is omitted; do not silently use the method default for a physical aspiration. Confirm the source `(deck_slot, well_name)` and deployed labware identifier.
4. Create a clearly labeled no-home continuation protocol that loads only newly required labware, then calls the existing `aspirate_from` or `dispense_to`. Validation establishes schema validity, not continuity; record the dependency on the prior attached-tip state in the protocol description and project history.
5. After aspiration, verify the exact Sartorius command from the **deployed machine-profile conversion**, lack of an `erN` rejection, final gantry target, idle/queue/edge state, and continued visible attachment. Do not reuse a command example from another Sartorius profile: at `0.5 uL/step`, 100 uL maps to `RI200`, while the MOF profile at `2.5 uL/step` maps 100 uL to `RI40` and 500 uL to `RI200`. Record the new tracked volume because it controls whether the next full dispense must use `RB`.
6. Do not claim physical liquid uptake from command success or imagery. If source height is above the liquid surface, the same successful command may aspirate air. For the 16.9 mm diameter Polyelectric well, 30 mm liquid height requires about 6.73 mL; treat the actual source volume as operator-provided unless independently measured.

A continuation may intentionally end with liquid held in the attached tip. Do not home, initialize, eject, blow out, or dispense unless explicitly requested, because each changes or destroys the state needed for the next stage.

## Full-volume dispense continuation

When the next operator request dispenses the entire tracked amount:

1. Re-prove continuity from the immediately preceding aspiration: unchanged edge start time/restart count, no later `RZ`/`RE`/`RB`/`RO`, idle state, empty queues, and a fresh frame showing the same attached tip.
2. Ask for `height_from_bottom` if omitted. Load only the newly required destination labware; do not home or recreate the edge.
3. Run `dispense_to` once. Verify the gantry reached the transformed destination and modeled height before the piston command.
4. Require logs showing the parameterless command `RB` exactly and explicitly confirm that no `RO<steps>` was emitted. An `RB` log without an `erN` rejection establishes controller-path success, not measured liquid delivery.
5. Only after accepted `RB`, record tracked volume as `0 uL`. The disposable tip remains attached unless a separate, explicitly authorized `drop_tip`/ejection step runs.
6. Recheck edge health/restarts, idle/no-active-run, zero pending/unacknowledged queue work, and fresh imagery for retained tip/no collision. Report physical delivered volume as unmeasured unless an independent balance, liquid-level sensor, or operator measurement establishes it.

This is the preferred end-to-end proof that the corrected full-delivery path is live: prior aspiration logs (for example `RI200`) establish tracked volume, and the following equal-volume dispense must emit `RB`, never `RO200`.

## Tip-ejection continuation

When the operator explicitly requests disposal after the tracked volume has returned to `0 uL`:

1. Treat ejection as another no-home continuation. Re-prove unchanged edge start time/restart count, no later `RZ`/tip pickup, idle state, empty queues, and visible tip attachment. Do not home first: that can clear software tip state while leaving the physical tip attached.
2. Verify the **deployed** trash definition and transformed target before motion, not only the checkout. Runtime names and geometry may have changed; never silently substitute a removed legacy identifier.
3. For this MOF installation, use `trash_bin_mof` at D1. Its internally consistent model has `zDimension=91 mm`, and D1/A1 with the required 97 mm tip offset resolves to `X=43.5, Y=-1.2, Z=-37.0`. Confirm these values from the deployed image and ensure the 1.2 mm Y-axis margin remains valid before moving.
4. Apply the operator's persistent rule: **all moves to any trash-bin labware assume a physical Sartorius disposable tip is attached and apply the 97 mm offset unless the operator explicitly says no tip is attached.** This assumption must hold even after home/redeployment clears software tip state. Log when the physical-tip assumption overrides cleared software state.
5. Treat that override as a **geometry-only safety rule**, not state reconciliation. It must not make `attach_tip`, aspiration, dispensing, or `drop_tip` proceed under an unresolved physical/software mismatch. In particular, `drop_tip` still requires a logically attached tip; reconcile first rather than bypassing that guard.
6. When software tip state is logically attached, call the existing `drop_tip(D1, A1)` exactly once. Verify the gantry reached the deployed target and the Sartorius command was exactly `RE30` with no `erN` rejection.
7. Treat `RE30` acceptance and the driver's cleared tip flag as **software/controller evidence only**. This installation has previously acknowledged `RE30` while retaining the disposable tip physically.
8. Capture fresh before/after images and compare the pipette endpoint. A successful release removes the bulky translucent disposable tip and leaves only the thinner permanent stem/nozzle; use an operator-confirmed no-tip reference crop when perspective is ambiguous. Also inspect for collision and people/hands.
9. If the physical result is uncertain or the tip remains attached, do not retry automatically: software already says no tip, so a duplicate ejection can worsen the mismatch. Stop, report the discrepancy, and require reconciliation or operator action.
10. Record controller, software, and physical outcomes separately, including that no retry occurred.

## Full-cycle transfer after manual tip reconciliation

Use this when a requested pickup-transfer-ejection workflow starts while an old physical tip is present but software tip state was cleared by home/redeployment.

1. Stop before `attach_tip`; never stack or reseat a new tip onto the existing physical tip. Ask the operator whether to retain it or manually remove it. If the requested rack well was previously consumed, require replenishment or a different occupied well.
2. Treat each successful pickup as consuming that named rack well. If a later request repeats the same well, do not infer replenishment from the new request or from an empty software deck: require explicit operator replenishment (or a different occupied well) before another insertion. Camera occupancy can be ambiguous; combine operator confirmation with a fresh image showing a plausible tip and no person/hand.
3. After the operator confirms manual removal/replenishment, capture a new frame. Independently verify the bare nozzle, clear enclosure, rack placement, and plausible occupancy of the requested tip well. A confirmation message alone is not physical proof.
4. Once no-tip physical and software state agree, a self-contained protocol may use: `home`; load tiprack/source/destination/trash labware; `attach_tip`; `aspirate_from`; `dispense_to`; `drop_tip`.
5. Resolve liquid targets from the deployed geometry for the requested height; do not clone the previous run's Z. For the current 16.9 mm Polyelectric 8-well definition (`insert_depth=76 mm`, `well depth=77 mm`) with an attached-tip top pose at `Z=-54.0 mm`:
   - 30 mm above bottom resolves to `Z=-100.0` and needs about 6.73 mL to reach that liquid height;
   - 10 mm above bottom resolves to `Z=-120.0` and needs about 2.24 mL;
   - 1 mm above bottom resolves to `Z=-129.0`.
   Treat these coordinates as versioned calibration data: confirm the deployed definition before every new protocol rather than carrying them forward blindly.
6. Verify the requested tiprack well independently from the liquid targets. On the current C1 Sartorius definition, known pickup paths are:
   - C1/A1: `X=11.35, Y=-141.6`, approach `Z=-120.1`, insertion `Z=-133.1`;
   - C1/A2: `X=11.35, Y=-132.6`, same approach/insertion Z;
   - C1/A4: `X=11.35, Y=-114.6`, same approach/insertion Z.
   Confirm the deployed definition and require the `Tip attached successfully` marker followed by Z home; command success alone does not prove a tip was physically seated.
7. Audit liquid/ejection commands against the deployed machine profile rather than a historical constant. For the current MOF `2.5 uL/step` profile:
   - 100 uL maps to `RI40`;
   - 500 uL maps to `RI200`;
   - an equal full-volume dispense uses exactly `RB` and no `RO<steps>`;
   - `trash_bin_mof` D1/A1 resolves to `X=43.5, Y=-1.2, Z=-37.0` and uses exactly one `RE30`.
   Resolve source/destination X/Y/Z from the active slot, well, and requested height for every new protocol; do not reuse coordinates from a different slot or destination well.
8. Compare the final endpoint against the operator-confirmed pre-run bare-nozzle image. Matching shapes support physical release; if ambiguous, do not retry.
9. Report controller-path success separately from actual liquid volume or identity. Treat statements such as “the well is filled with water” as operator-provided evidence, not camera verification. State the minimum source fill needed to reach the requested aspiration height (for example, approximately 6.73 mL at 30 mm or 2.24 mL at 10 mm in this source well); controller acceptance may still represent air aspiration if fill is lower.

## Explicit home while a physical tip is attached

Use this when the operator explicitly asks to home after a positioning check that intentionally ended with a disposable tip attached or inserted.

1. Treat the explicit home as authorization to retract/home, **not** as authorization to eject the tip. Run a fresh idle/edge/queue/camera preflight and require no person or obstruction; verify the tip is plausibly straight before retracting from a deep well pose.
2. Prefer the first-class direct command `puda machine home pipqubot_mof` for a home-only request. Do not wrap it in a protocol or silently prepend `drop_tip` merely to make later state easier.
3. Verify all boundaries: one successful PUDA `home`, full gantry `$H` completion, Sartorius `RZ`, final idle state, healthy unchanged edge, and empty queue. Capture a post-home frame.
4. Expect `RZ` to clear software tip/tracked-volume state while the physical disposable tip may remain attached. Report this mismatch explicitly. Do not run `attach_tip`, aspiration, dispensing, or software-guarded `drop_tip` until physical/software state is reconciled; a subsequent pickup could stack or bend tips.
5. If the next operator request says “home, then pick a new tip” while the old physical tip is still attached, stop before motion and ask how to reconcile it. With explicit authorization to eject first, use the reviewed order: `load_labware(D1, trash_bin_mof)` → one `drop_tip(D1/A1)` → `home` → reload tiprack and destination labware → `attach_tip` → position. Never home first and then attempt a new pickup over the retained physical tip.
6. A person entering only after the command completed does not invalidate the verified home, but it is a hard stop for every subsequent motion. Record the post-completion entry and dispatch nothing further until a new clear frame is obtained.

## Labware recalibration during a stateful session

When an operator supplies an updated labware definition after a tip has already been positioned:

1. Treat the new definition as superseding the old modeled height immediately for future planning, but do not reinterpret the already-executed physical coordinate as if it had moved. Recompute the old absolute Z against the new insert depth and report its new height-from-bottom explicitly.
2. Distinguish three states: source definition on disk, definition inside the running container, and the already-instantiated labware object in the edge process. Updating a JSON file does not mutate an existing in-memory deck object.
3. Validate JSON, runtime discovery, transformed top/bottom targets, axis limits, and the full relevant driver suite. Add a regression for the calibrated height.
4. If a tip is inserted or a person is inside, do not recreate/restart/home merely to activate a data-only change. It is safe to build the future image and update the live container file without motion, but require a future `load_labware` call to instantiate the new geometry before any depth-relative move.
5. Record the old and new insert depths, resulting absolute targets, source/live/image hashes, image ID, test count, current physical Z, and whether the current in-memory deck remains stale. Before the next motion, re-prove tip/person state and reload the labware definition.

## Repeated one-shot height or destination series

Use this pattern when an operator submits several similar single-transfer requests to compare dispense heights or destination wells. Treat every message as a new physical cycle, not permission to reuse the previous protocol or consumable state.

1. Carry forward consumable history: the tip used and ejected in the immediately preceding cycle is consumed. If the next request names the same rack well, pause before motion and require explicit confirmation that it was physically replenished, or select another operator-approved occupied well.
2. After replenishment confirmation, capture a fresh frame. If a hand or body part is visible, dispatch nothing; wait for explicit clearance and capture a second fresh frame before continuing. Verify bare nozzle, plausible requested-tip occupancy, required labware, and unobstructed travel independently.
3. Create a new protocol whenever the tip well, destination well, aspiration height, or dispense height changes. Do not rerun the prior JSON merely because volume and source are unchanged.
4. Reject negative `height_from_bottom` values before validation or dispatch: they target below the modeled bottom. Offer a known-safe positive height or ask the operator for a corrected nonnegative value; never silently clamp the requested value.
5. Derive transformed coordinates from the active geometry each time. For a height series, verify that only the intended destination axis/height changed; for a destination-well series, verify the expected well-to-well XY shift and the requested Z.
6. Audit every one-shot cycle independently: exactly one calibrated `RI<steps>`, one full-volume `RB`, no `RO<steps>`, one `RE30`, no `er1`–`er4`, final idle/healthy/zero-queue state, and a before/after endpoint comparison consistent with release.
7. Record each protocol/run separately. Report reagent identity and stock quantity as operator-provided, and distinguish controller-verified commands from independently measured delivered volume.

## Multi-reagent formulation runs and sample identity

Use this pattern for CSV-driven runs that create several labeled formulations with one tip per reagent.

1. Parse every newly supplied formulation, deck-loading, and stock CSV with BOM-safe UTF-8 (`utf-8-sig`) and preserve each absolute source path and SHA-256 hash. Compare row labels, destinations, reagent totals, and per-destination volumes against the protocol/audit artifact. Reuse a validated protocol only after proving exact equivalence; matching filenames or descriptions are insufficient.
   - Deck-loading CSVs may encode generic contents such as `Vials` or `Tips` in a `Load` column while reserving `Identity` for named reagents. Normalize the operative content as `Identity` when non-empty, otherwise `Load`; do not reject a valid destination/tiprack row merely because `Identity` is blank.
   - If the formulation CSV omits destination wells, infer row-major destinations only when the deck file makes the mapping uniquely determined (for example, exactly 24 formulation rows paired with the explicit destination range `A1-D6`). Persist the inferred label-to-well map and the inference rule in the audit. If row count, ordering, or destination range is ambiguous, stop and ask rather than inventing wells.
2. Audit every requested aspiration and partial dispense against the deployed volume resolution before motion. The MOF profile is 2.5 uL/step, while the current driver converts `steps = int(amount / 2.5)` (floor). Values not divisible by 2.5 uL are therefore not represented exactly. In a stock-batched sequence, partial `RO` truncation and the final `RB` can redistribute the quantization remainder into the batch's last destination. Prefer rejecting or explicitly revising non-representable CSV volumes before dispatch. If an already-authorized run executes such values, preserve requested volumes, generate a per-transfer and per-sample actuator-volume audit from the exact RI/RO-floor and final-RB semantics, and report the deviations prominently; never present requested microlitres as independently measured delivery.
3. Match each reagent name exactly to the stock table and persist stock ID, concentration, units, source well, and operator-stated starting volume. If a solvent such as DMF is physically supplied but has no standalone stock-table row, record `stock_id=null` and `concentration=null` with an explicit note; never invent an ID from its appearance as another stock's solvent.
4. Reconcile source wells, stock volumes, destination labware, trash labware, and available tip range. Verify required totals do not exceed stocks. When one reagent spans multiple source wells, allocate sources sequentially without exceeding either well. Persist **starting**, **allocated**, and **expected residual** volume for every source well; excess capacity is not consumed and must not be reported as transferred. By default, “one new tip per reagent” means retain the same tip across source wells for that reagent, then eject once after all its transfers; do not consume an extra tip merely because the source well changes unless the operator specifies otherwise.
   - Make tip cardinality an explicit hard gate: count distinct contamination/reagent classes and compare that number with the inclusive occupied rack-well range. For example, eight reagent classes require eight tips; `A1-A7` is seven, not eight. Do not silently reuse a tip, omit a reagent, or assume the next well is occupied. Ask for an eighth tip/alternate position, and after the operator says they will load it, require a separate confirmation that it **is loaded** before physical dispatch because individual occupancy is often camera-limited.
   - Interpret tip ranges in deck context. A statement such as “tips C2–C12” alongside one Sartorius rack at C1 normally names **rack wells**, not deck slots (the deck has no C12 slot). Persist both the rack deck slot and each selected rack well, and ask only if both interpretations remain physically possible.
   - If home/RZ previously cleared software tip state while a physical tip remained, do not begin the multi-reagent protocol from operator confirmation alone. Require explicit manual-removal confirmation **and** a fresh frame showing a bare endpoint and clear enclosure before the protocol’s first `home`/`attach_tip`.
5. Build stock-batched transfers with a maximum 1000 uL aspirate. At every aspirate batch, dispense exactly the tracked amount before another aspiration, source switch, or ejection: preceding partial dispenses use `RO`, and the dispense equal to the remaining tracked amount uses `RB`. Ensure tracked volume is zero at every `drop_tip`. At a source boundary, ensure the final aspiration does not exceed the operator-stated remaining source volume and that the requested aspiration height remains physically plausible at the start of that aspiration.
6. Resolve sample identity before motion. If an authoritative external request already supplies one UUID sample ID per sample, preserve those IDs exactly and validate UUID version, uniqueness, count, and one-to-one destination coverage; do **not** generate replacements merely because the PUDA protocol is new. Generate fresh UUIDv4 values only for samples that lack authoritative IDs. Persist a pending run manifest with label, UUID, destination, target/formulation metadata, protocol ID, stock mapping, source allocations, and all input hashes. Do not regenerate IDs after execution begins. Treat visible sample labels as run-scoped rather than globally unique: if a filename/requested range conflicts with CSV or request labels, pause for explicit operator selection. When the operator deliberately chooses literal labels that duplicate a prior run and no authoritative IDs were supplied, retain those labels exactly, generate fresh UUIDs, and require the run/protocol ID in every artifact and user-facing reference so the two sets remain unambiguous. Never overwrite or merge earlier label-matched records. When the operator supplies a run label such as `practice`, carry it in the protocol description, audit, pending provenance JSON/CSV, and final run record. A static/dry run dispatches no robot command; if a later physical run is requested as a newly labeled run, create a fresh protocol/provenance set and fresh UUIDs only where the external request did not already assign them.
7. Independently audit the generated protocol before dispatch, in addition to `puda protocol validate`: require contiguous step numbers; exact tip order; one attach/drop cycle per reagent; positive aspirates no larger than capacity; nonnegative exact requested heights; no dispense larger than tracked volume; zero tracked volume at every source switch/drop; reconstructed destination-by-reagent totals equal the request/CSV; reconstructed source totals equal the allocation ledger; and all source/destination labware identifiers match the deployed deck. For a request that omits destination wells, a later generic instruction such as “execute” authorizes the proposed mapping but does not prove physical loading. Before dispatch, explicitly confirm exact source identities/volumes, fresh tip wells, removal of prior destination samples, and fresh empty destination vessels. Treat `puda protocol validate` plus this static audit as planning evidence only—never as evidence that a dry run moved liquid.
   - If byte-identical inputs justify using an earlier audited protocol as a generation template, treat cloning as code generation—not validation. Replace the protocol ID, timestamps, current attachment paths/hashes, every sample UUID, operator authorization, tip wells, and all run-scoped artifact references. Then independently reconstruct destination-by-reagent totals and source allocations from the generated commands; successful text substitution alone is not an audit.
8. Before the camera preflight, reconcile **destination occupancy across runs**. If project history says the same BioShake wells held samples from a preceding workflow, do not infer that a new request replaced them merely because it names the BioShake or repeats the slot. Ask the operator whether the prior samples were removed and whether fresh empty destination vials are loaded. Record that confirmation as operator evidence; camera imagery generally cannot establish vial identity, emptiness, or sample labels. Keep the new protocol in a pending safety-clearance state until this gate is resolved.
9. Run a fresh camera preflight immediately before dispatch. Treat any person/body part crossing the enclosure boundary as a hard stop. Compare the Sartorius endpoint against a known bare-nozzle reference: if a physical tip appears attached while software state may be clear, withhold `home` and `attach_tip`; require manual removal/reconciliation and a second fresh frame. Camera evidence can establish coarse placement and safety, not exact source identity, well contents, concentration, destination-vial identity/emptiness, or individual rack-well occupancy; retain those as operator/file provenance.
10. During execution, retain the process handle, record the actual run ID as soon as START succeeds, and monitor monotonic command progress. Never treat a client wait timeout as cancellation or resend the protocol. For long runs, start a passive edge-log monitor before dispatch and capture one frame after each `Tip dropped successfully` boundary; keep the monitor's expected count equal to the planned reagent count and persist a JSON capture index. Do not implement the bounded monitor as `docker logs -f | while ...; break` under `pipefail`: breaking the downstream loop may leave the upstream `docker logs -f` process alive. Use a monitor that owns and explicitly terminates its log subprocess after the expected count, or stop the tracked monitor process after verifying all captures. Record an intentional monitor termination separately from protocol outcome; it is not a robot-run failure.
11. Verify completion at all layers: every protocol command succeeded exactly once; database command counts match expected aspirate/dispense/attach/drop operations; edge logs show the calibrated `RI` sequence, one terminal `RB` per aspiration batch, only the expected partial `RO` commands, one `RE30` per reagent, and no `er1`–`er4`; machine is idle; edge is healthy with unchanged restart count; queue has zero pending and ack-pending work. Count exact Sartorius wire-send lines rather than generic log mentions: one physical `RB` may appear in multiple descriptive messages, and framed commands such as `\x011RE30...` can defeat naïve word-boundary regexes. Normalize the framed send payload, then compare exact command counts. Derive expected `RB` count from aspirations rather than assuming `RO=0` for stock-batched multi-destination runs.
12. Inspect every ejection frame and the post-run frame for a bare endpoint, people/hands, collision, spill, displaced labware, and obstruction. Keep controller-path success, commanded formulation, operator-provided stock identity, and independently measured physical delivery as separate evidence classes.
13. Bind the **same pending UUID manifest** to the actual run ID and completion/partial/failure status. If no supported PUDA sample-write interface exists and SQL writes are intentionally blocked, do not bypass that protection; retain run-scoped audited JSON and CSV artifacts, link them from project history, and include label → UUID → destination directly in the completion report.
14. When the external request includes downstream stages not executed by the liquid handler—such as microwave treatment—do not label the overall request complete after dispensing. Mark each sample and the run as `liquid_handling_completed_<downstream>_pending`, preserve the requested downstream parameters and units, and state explicitly that the downstream stage was not executed. Only promote the overall request to complete after that machine/workflow is separately executed and verified.

## Single-reagent multiwell prefills after edge reconnection

Use this pattern for a solvent/reagent prefill that spans many destination wells, especially after the PipQuBot mini-PC or edge has been offline.

1. **Reject stale readiness evidence.** If `puda machine state` still returns an old `idle` record while `puda machine list` does not show `pipqubot_mof`, treat the state/deck as retained KV data, not a live edge. Dispatch nothing.
2. Before recreating an actuating edge, require a fresh enclosure frame showing no person/body part or obstruction and a plausibly bare endpoint. Verify both serial-by-id devices and the `.env` bind source exist with the expected file types, render the Compose config, then start only the PipQuBot edge.
3. Startup performs gantry home and Sartorius `RZ`; wait for explicit startup-complete, NATS-ready, and queue-subscription markers. Require a fresh `pipqubot_mof` entry in `puda machine list`, a newly timestamped `idle` state with `run_id=null`, healthy/zero-restart edge status, and `pending=0` / `ack_pending=0` before authoring or dispatching against the new empty deck.
4. Treat one reagent as one contamination class: use one operator-confirmed replenished tip across all same-reagent sources/destinations, then eject once. Persist the rack deck slot and rack well separately.
5. Respect the 1000 µL aspiration limit. For a 2000 µL destination, emit two independent `aspirate 1000 → dispense 1000` cycles. Because each dispense equals tracked volume, each must produce `RB`; the expected controller audit is `RI400 × 2` and `RB × 2` per destination at the MOF 2.5 µL/step profile, with no `RO`.
6. When identical reagent occupies multiple source wells and the operator does not prescribe depletion order, choose and record an auditable allocation that preserves safe residual volume (balanced allocation is usually safer than fully draining one source). Check the requested aspiration height against the source geometry and the volume remaining before the final aspiration. Record starting, allocated, and expected residual volumes as operator-derived quantities.
7. Generate a destination ledger with exact per-well total and height. Independently verify command counts, contiguous steps, one attach/eject cycle, exact source totals, exact destination totals, and zero tracked volume before ejection; then validate the protocol.
8. Capture a second fresh frame immediately before dispatch. During execution, retain the process handle and run ID and passively capture the single post-ejection frame. Never infer cancellation from a client wait timeout or resend automatically.
9. Reconcile protocol/database counts and require the exact expected `RI400`, `RB`, and `RE30` counts with `RO=0` and no `er1`–`er4`. Recheck fresh idle state, edge health/restarts, empty queue, and post-run imagery. Keep operator-provided stock identity/starting quantity separate from controller acceptance and independently measured delivery.

## Verification and deployment

1. Add failing tests for full-volume `RB`, partial `RO`, and `erN` propagation.
2. Make the smallest behavior change; avoid unrelated calibration/model assumptions.
3. Run safe driver regressions without hardware-operating test modules.
4. Before recreating the edge, verify serial-by-id devices, no active run/pending queue, no attached tip, and a clear enclosure.
5. Verify startup home, Sartorius initialization, NATS registration, edge health, idle state, and empty queues.
6. State explicitly whether liquid behavior was physically tested; software tests and startup verification do not establish liquid delivery.
