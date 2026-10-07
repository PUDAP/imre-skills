# Dobot M1Pro centrifuge empty-ring scans and controlled-speed placement

Use this reference for M1Pro centrifuge geometry workflows: fresh empty black-holder-ring scans, fresh loaded orange-cap scans followed by rotor-to-MTP unloading, and transfers that require an exact native Dobot speed factor for the final placement descent.

## Fresh empty-ring census

1. **Freeze the geometry epoch.** Resolve the active scan-center pose, camera-to-tool transform, destination Z, and centrifuge-open state. A prior scan is calibration/provenance only; do not reuse its accepted R values as seeds when the rotor may have moved. Treat the active center as run data, not a source-code constant: before acquisition/finalization, audit every stage protocol, transform script, report metadata field, and plot origin for stale hard-coded center values. Prefer explicit `--center-x/--center-y/--center-z` arguments or a UUID-linked calibration input. After a center update, fail the run if any generated artifact still names the superseded center.
2. **Preflight evidence.** Require fresh idle state, healthy edge/session, fresh controller pose, open centrifuge, usable wrist frame, and overhead evidence of no person, loose labware, broad-path obstruction, collision, or cable hazard. Use the edge-owned controller session only.

   **IMRE-MOF centrifuge-2 lid visual signature:** in the fixed overhead view, centrifuge 2 is the left member of the bottom pair. A **closed/lowered** lid appears as a green translucent cylindrical cover surrounding the rotor; the rotor and black holder rings can remain visible through it, so rotor/ring visibility alone does **not** prove the lid is open. An **open/raised** lid is visibly lifted upward/back from that unit, leaving the rotor directly exposed on a white circular base. Cross-check against the **raw two-axis `Position: a;b` string in the existing centrifuge-edge logs**, not the public `get_position` dictionary (the deployed float parser can collapse semicolon-delimited values to `0.0`). Interpret the intended device axis relative to the freshly established epoch: `0` is open/home and `50` is the normal closed endpoint; the other axis may independently be open or closed. If the intended axis is not at `0` or the visual signature is ambiguous, issue the device-scoped `open_lid(device="2")` protocol and verify both the raised-lid image and stable raw open telemetry before staging the robot. Never substitute global `home()` when only one device is intended, and do not let a usable through-lid wrist image override this gate.
3. **Full coarse sweep.** At fixed scan-center X/Y/Z, scan the complete allowed R interval uniformly. A 10° sweep from `-180°` through `+180°` contains **37 captured samples**, but because `+180°≡-180°`, only **36 unique physical orientations**; do not describe `-170°…+180°` as 37 samples (it contains 36). Move monotonically and capture a fresh wrist image after each blocking move. Preserve angle, protocol/run ID, image path, timestamp, and image-validity statistics. Every claimed sample—including a separately staged `-180°` boundary—must appear in the scan's manifest or an explicitly linked boundary manifest with the same provenance fields; do not claim a 37-image scan from a 36-row coarse manifest plus an unlinked preflight image. Before dispatching the first move, run a no-motion acquisition-script preflight that imports its declared image dependencies and verifies output-directory writability. Create both capture and aggregate-log parent directories before piping through `tee`, because `tee` opens its destination before the acquisition script can create per-item directories. If startup preflight fails, verify from live state/logs that no movement was dispatched, correct the invocation/setup, and repeat the safety preflight rather than treating it as an interrupted motion.
4. **Camera timeout rule.** If capture fails after the robot reaches a pose, hold that independently verified pose. Retry capture at the same stationary R; do not advance without a usable frame. If a bounded retry also fails or disconnects repeat, stop and request a cable check. The durable lesson is retry-at-stationary-pose, not that any particular capture command is permanently broken.
5. **Detect the correct feature.** Segment or Hough-detect the **complete outer black holder ring**. Reject inner bores, screws, glare circles, rotor symbols, neighboring partial rings, and any circle whose outline touches the frame border. Calibrate plausible outer-radius, vertical-ROI, and detector-sensitivity ranges from fresh frames rather than hard-coding them across camera epochs. With OpenCV Hough detection, keep the **search** radius band broad enough to let the accumulator recover the outer circle, then post-filter accepted circles to the fresh outer-ring radius band; setting `minRadius` equal to the acceptance minimum can suppress a valid outer circle even when its fitted radius is above that minimum. If one otherwise usable stationary refinement frame misses at the initial Hough threshold, retry detection on that same saved frame with a bounded sensitivity/search-band adjustment; accept only when the complete outer-ring identity passes visual QA and the center remains stable across nearby reasonable thresholds. Do not move again merely to compensate for one detector-parameter miss.
6. **Generate six candidates de novo.** For each outer ring crossing, bracket image center `x_target = image_width/2` with adjacent coarse samples. Interpolate R from fresh `(R,x)` pairs. Do not accept every numerical sign change from a “circle nearest frame center” series: when one holder exits and another enters, nearest-circle identity can switch discontinuously and create a false crossing. First establish the expected same-ring image-motion direction from fresh consecutive frames; for the current monotonic IMRE-MOF sweep, a genuine crossing has decreasing `x` as R increases. Require the bracketing pair to preserve that direction and plausible local displacement, then visually confirm that both frames show the same complete outer ring. Include the final `+170°→+180°` bracket when applicable even though `+180°` is physically equivalent to `−180°`; do not accidentally omit this sixth crossing while removing the duplicated boundary orientation from uniqueness counts. Use [scripts/extract_empty_ring_candidates.py](../scripts/extract_empty_ring_candidates.py) to deterministically apply the direction filter and refuse output unless the expected count is found; its CSV still requires bracket-frame visual QA before refinement. Check approximately uniform circular spacing, including wraparound, as a consistency test—not as a substitute for image evidence. Number holders by an explicit current-scan convention, normally increasing accepted R. A later completed fresh scan supersedes the prior scan for future holder moves; keep older reports as provenance, not active geometry.
7. **Reset before refinement.** After reaching the upper sweep boundary, use the reviewed normal home/neutral workflow to unwind before a second monotonic pass. Confirm cable/path safety before home.
8. **Refine and accept.** Move through candidate R values monotonically, capture a fresh frame, redetect the full outer ring, and independently query controller pose. Accept only within an explicit pixel tolerance (for a 640 px frame, `|x-320| ≤ 3 px` is a proven practical threshold). If correction is needed, derive it from the fresh local pixel-per-degree slope and use a bounded sub-degree move.
9. **Visual QA.** Produce an annotated contact sheet showing the outer-ring circle, detected center, frame-center line, R, and residual. Reject any tile tracking an inner hole or partial neighboring feature.
10. **Transform to tool XY.** For scan center `(Cx,Cy)`, reference angle `Rref`, and camera-to-tool offset `(dx,dy)`, compute:

   ```text
   θ = Rcentered − Rref
   X = Cx + dx cos θ − dy sin θ
   Y = Cy + dx sin θ + dy cos θ
   ```

   Use the independently measured accepted R, preserve precision, and record all transform constants in the report.

   If the operator requests an **exact radial XY distance** `ρ` from the centrifuge center, do not merely relabel the calibrated offset magnitude. Normalize the reference vector before rotation:

   ```text
   s = ρ / hypot(dx, dy)
   dxρ = s·dx
   dyρ = s·dy
   X = Cx + dxρ cos θ − dyρ sin θ
   Y = Cy + dxρ sin θ + dyρ cos θ
   ```

   This preserves the calibrated angular phase/cross-axis component while making every transformed point satisfy `hypot(X−Cx, Y−Cy)=ρ`. Verify that equality numerically for every holder and report both the raw calibrated vector and normalized vector. For the IMRE-MOF reference vector `[30.5,1.0] mm`, an exact `ρ=30 mm` request uses normalized `[29.983888291,0.983078305] mm`, not `[30,0]`.

   For **mat-fox's centrifuge transformed-XY plots**, render a 90° clockwise view: `Y` is the horizontal axis and `X` is the vertical axis with the vertical axis inverted so increasing `X` goes downward. Keep point labels in canonical `(X,Y)` order even though plotting coordinates are `(Y,X)`; state the orientation explicitly on the axes/title. Visually QA the rendered plot before delivery for label overlap, clipping, and missing-glyph/tofu boxes. PIL's default bitmap font may not contain arrows, en dashes, or some degree symbols; either load a font with verified Unicode coverage or use legible ASCII (`90 deg`, `Robot Y (mm)`, `Robot X (mm)`) rather than shipping broken symbols. For headless Linux execution, select a non-interactive Matplotlib backend **before** importing `pyplot` (`import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt`). Otherwise a Tk-backed default can fail at render time even though Matplotlib imports successfully. Regenerate and re-hash the plot after any legibility fix.
11. **Close safely.** Return through the normal home/neutral workflow, verify final pose/state/edge health, and record whether the centrifuge remains open.

## Transfer out of a freshly scanned loaded rotor

Use this pattern when a fresh orange-cap scan is followed by unloading the detected tubes into registered MTP wells.

1. **Freeze the source geometry epoch.** Resolve source X/Y from the latest completed orange-cap scan, and require no centrifuge spin, rotor manipulation, newer scan, or manual intervention after that scan. A black empty-ring scan is not a substitute for loaded-cap centers.
2. **Reconcile destination occupancy separately.** Establish that the requested MTP wells are empty from the run ledger or an explicit operator boundary. The cap scan proves source geometry/occupancy at scan time; it says nothing about MTP occupancy.
3. **Separate scan R from pickup orientation.** The centered scan R locates each tube and produces its transformed source X/Y, but it need not be used as the gripper orientation. Preserve the fresh source X/Y while applying a reviewed pickup R override when required by clearance.
   - At IMRE-MOF, a prior cap-6 pickup using the large positive scan R collided the wrist camera with the raised centrifuge-2 lid. The established clearance-safe unloading pattern is source high-stage, descent, close, and lift at `R=-22.5°`; destination motions also use the active MTP R. Treat this as installation-specific evidence, not a universal Dobot rule.
   - Do not descend directly from an arbitrary prior pose. Stage first at the source X/Y and approved carry Z with the clearance-safe R, then descend vertically.
4. **Use one independently recoverable protocol per tube.** For the current IMRE-MOF geometry, the deterministic eight-command sequence is:
   1. `safe_move` to source X/Y at carry Z and clearance-safe R;
   2. `safe_move` vertically to the approved rotor pickup Z;
   3. `close_gripper`;
   4. `safe_move` vertically back to carry Z;
   5. `safe_move` to destination X/Y/R at carry Z;
   6. `safe_move` vertically to the active MTP well Z;
   7. `open_gripper`;
   8. `safe_move` to the destination retreat endpoint.

   **`safe_move` retreat is not necessarily a direct vertical rise to the requested retreat Z.** The deployed M1Pro implementation computes `travel_z = max(configured_safe_height, current.z, target.z)`. From a low MTP placement pose such as `Z=9` to a nominal retreat endpoint `Z=100`, it may first command a lift to the configured safe height (currently `Z=240`) and then descend to `Z=100`. Describe `Z=100` as the verified retreat **endpoint**, not as the maximum height or a single vertical segment. If the operator requires an exact no-overshoot vertical raise, inspect the live command surface and use a reviewed primitive that actually provides it; do not claim `safe_move` satisfies that geometry merely because X/Y/R are unchanged. A timeout during this final command can occur after the safe-height `MovJ` was accepted but before `Sync` or the descent-to-endpoint completes, so the physical pose is unknown until independently measured.
5. **Resolve Z values from current approved artifacts.** Do not copy historical depths blindly. In the September 2026 IMRE-MOF configuration, rotor pickup used `Z=27 mm`, active centrifuge-tube MTP wells used `Z=9 mm`, and carry/retreat endpoints used `Z=100 mm`; later calibration supersedes these values.
6. **Waived fine visuals remain safety-only.** If the operator says not to perform visual checks, do not inspect or report exact source vacancy, destination occupancy, grasp retention, or seating. Still take fresh broad overhead hard-stop checks before every transfer for people, loose/fallen/horizontal tubes, displaced equipment, cable posture, swept-path obstruction, and the raised/open lid. A frame captured after transfer N may gate N+1 only if no intervention occurred.
7. **Verify and report honestly.** After every transfer, independently query the retreat pose, require idle state and empty queue counters, and preserve the accepted close/open gripper responses. Report successful physical transfer only as controller-inferred unless allowed sensor, camera, or operator evidence confirms it. Finish with a UUID-linked CSV/JSON ledger mapping source cap to destination well, protocol/run/pose IDs, geometry, command count, and evidence grade; return home only after a final safety-only frame clears the path.

## Transfer into a freshly scanned holder

- Resolve source coordinates from the **active** UUID-backed labware revision and destination X/Y/R from the latest completed scan report. Historical protocols remain provenance, not current geometry.
- If the operator explicitly overrides the **placement orientation** (for example, “use `R=-22.5` for all place moves”), preserve the freshly scanned destination **X/Y** but replace the scan-centered R in every destination-side pose: high staging, final descent, and retreat. Do not rotate or recompute X/Y from the override R—the scan R already produced the transformed holder center, while the override controls tool/camera orientation at that fixed destination. Resolve source orientation separately from active labware or the operator’s instruction. Treat the override as a new swept-volume/clearance geometry even when X/Y/Z are unchanged; retain broad safety-only gates when fine visual checks are waived. Before execution, audit every generated protocol to prove destination staging, placement, and retreat all use the override R and only the final descent carries the requested speed factor.
- Reconcile occupancy from project history **after the scan timestamp** before authoring the transfer. A fresh scan establishes geometry and occupancy only at scan time; later successful placements can fill holders, and later picks can empty source wells. Build a short source/destination ledger from completed runs, use only the operator-requested holder, and stop for reconciliation if history makes either occupancy ambiguous. Do not infer current emptiness merely because the scan originally detected an empty ring.
- Confirm that the scan's geometry epoch remains valid: require no recorded spin, rotor manipulation, or newer scan since the selected scan. Fresh open-lid telemetry and imagery prove lid state, not unchanged rotor angle; use project/run history to establish the no-rotation interval.
- Pick at the active source Z, close, lift to a safe Z, travel above the transformed destination, descend, open, and retreat. Keep gripper commands and lift/retreat as explicit steps.
- Use fresh overhead pre/post evidence. A broad frame can clear people, loose labware, and swept-path hazards while still being unable to resolve a specific MTP well or rotor holder. Record fine occupancy as occluded/uncertain rather than upgrading controller success to visual confirmation. If the source is occluded after motion, state that source vacancy is controller-inferred even when destination seating is visible.
- Interpret an operator instruction such as **“do not run visual checks”** narrowly: waive fine wrist-camera pickup/placement checks and occupancy/seating classification, but retain mandatory broad overhead hard-stop gates for people, loose/fallen/horizontal labware, swept-path obstructions, collisions, displaced equipment, cable hazards, and lid-open state. Label these frames and analyses `safety-only`, do not inspect or report exact source vacancy/destination occupancy from them, and describe the transfer outcome as controller-inferred. This prevents a safety gate from silently becoming the visual verification the operator declined.
- Treat **post-completion person entry** as a new physical-state boundary. If the first post-run frame shows hands, forearms, or any body part **inside the enclosure or crossing its access boundary**—even when the controller already completed and the robot reports idle—issue no further motion, including no visibility-improving home or reposition. Preserve the controller-completion evidence, take a fresh camera-only safety recheck, and confirm the person has withdrawn before doing anything else. Do not classify a person who is merely visible outside the enclosure as an in-enclosure hard stop; use the enclosure frame/access boundary and swept volume, and state uncertainty when the boundary is occluded. If the intervention or robot occlusion prevents confirmation of source vacancy or destination seating, report those outcomes as controller-inferred; do not use a later clear frame to assume that the physical state remained untouched during the intervention. Any subsequent motion requires a new request/authorization and a fresh full preflight.

## Repeated or batch MTP-to-holder loading series

When an operator replenishes a contiguous MTP range (for example, `B1:B6`) and requests matching transfers either one at a time or as one batch (`B1→holder 1` through `B6→holder 6`):

1. Treat the operator's replenishment statement as occupancy evidence for the named source range, then update the ledger after each completed transfer. Do not require the operator to restate that the next source is occupied. For an exact repeat of a previously completed batch, require a new explicit paired boundary before any motion: the source range was reloaded **and** the destination range was emptied. A fresh empty-ring scan after unloading can establish the destination-empty half only if no later placement or manual rotor intervention occurred; it does not establish source refill. Once both halves are explicit and the geometry epoch is still valid, one confirmation may authorize the named batch—do not interrupt after every successful member merely to ask the same occupancy question again.

   **Immediate inverse-batch exception:** when a just-completed, fully indexed controller-successful batch moved `A1…An → B1…Bn`, the ledger itself establishes `A=software-inferred empty` and `B=software-inferred occupied`. A subsequent explicit operator request for the exact inverse `B1…Bn → A1…An` may proceed without asking the operator to restate a reload/clear boundary, provided there was no intervening spin, manual intervention, conflicting move, or geometry change. Preserve the evidence grade: with fine visuals waived, both the forward and inverse physical outcomes remain controller-inferred. This exception does not authorize another same-direction repeat after the inverse batch closes.
2. Reuse the latest completed holder-center geometry only while its geometry epoch remains intact: confirm no centrifuge spin, rotor manipulation, newer scan, or conflicting placement/pick occurred. A fresh empty-ring scan is the preferred empty-holder source, but a freshly centered loaded-cap scan can also supply holder X/Y after those tubes are unloaded, because unloading changes occupancy rather than rotor angle. Preserve the cap scan as loaded-center provenance, keep its transformed X/Y unchanged, and apply any operator-specified placement `R` only as a tool-orientation override. Earlier transfers in the same series change occupancy but do not invalidate geometry.
3. Resolve each destination from the scan's explicit holder number, not from angular proximity or a prior cap scan. Preserve the scan's full `X/Y/R` precision and the active MTP revision's current source `Z`.
4. Generate a fresh auditable protocol for each transfer using the explicit seven-command sequence: source `safe_move`, close, source lift, destination stage, controlled final descent, open, and destination retreat. This keeps each request independently recoverable and prevents a later failure from obscuring the completed boundary of earlier transfers.
5. Before every transfer—not just the first in the series—require fresh idle/controller pose, healthy edge, empty queues, open-lid telemetry, and a fresh broad overhead hard-stop check. A previous clear frame does not carry forward after robot motion or operator tube replacement.
6. If the operator requests an ipcam image after each transfer, capture it only after controller completion and retreat. Inspect it for people, loose/horizontal/diagonal tubes, collisions, displaced equipment, and cable posture. An upright tube visible in the rotor supports seating, but exact holder-number identity remains coordinate/controller-inferred unless the image independently resolves rotor numbering; likewise, do not claim the exact MTP source vacancy when the rack is occluded.
7. After each transfer, independently query the retreat pose, recheck idle state, queue counters, edge health/restarts, and lid telemetry, then append both the transfer run and pose-query run to `project.md`. Deliver the requested post-run image to the operator.
8. Treat an exact repeated source→destination request as a duplicate hazard, not an implicit refill. If the ledger says the source was just emptied and the destination filled, issue **no motion or gripper command**. Capture a fresh camera-only frame for broad safety/current-state context, then require explicit paired confirmation that the source was reloaded **and** the destination was emptied. A prior statement that a whole MTP range was replenished repopulates those sources only at that stated boundary; it does not silently apply again after a completed transfer and does not clear rotor holders. If the operator cancels, leave the robot idle and do not create or run another transfer protocol.
9. Close the series explicitly when the final requested transfer completes. Reconcile the full ledger (for example, all replenished `B1:B6` sources consumed once and holders `1:6` filled once) and compare it with the final broad frame. If six distinct upright caps are clearly visible in the six rotor positions, report that the **rotor fill pattern/count** is visually confirmed; retain coordinate/controller provenance for which source went to which numbered holder unless numbering is independently visible. Mark the source rack's exact vacancy pattern uncertain when the rack is occluded. Treat any later request for a member of the closed series as a duplicate until a new operator refill/clear boundary is stated and verified.

## Delayed release after controlled placement

Use a two-phase protocol pair when the operator requires the gripper to remain closed at the placement pose for a measured delay before release and the machine command surface has no validated blocking wait command:

1. **Phase A — pick and place-hold:** source `safe_move`, `close_gripper`, source lift to carry Z, destination stage at carry Z, then the controlled final Z descent. End Phase A at the placement pose with the gripper still closed.
2. Start the host timer only after Phase A reports successful protocol completion. Prefer a monotonic timer for interval measurement; record UTC start/end timestamps separately for provenance. Do not count movement time or protocol-startup time toward the requested hold.
3. Require the measured elapsed interval to be at least the operator’s requested delay before dispatching Phase B. A small positive scheduling margin is appropriate, but report the measured interval rather than the nominal `sleep` argument.
4. **Phase B — release and retreat:** `open_gripper`, then move to the requested retreat endpoint at unchanged destination X/Y/R. Audit the live movement primitive before calling this a vertical raise: with the deployed `safe_move`, a low-Z start can first rise to configured safe height above the requested endpoint and then descend to it. Preserve the accepted intermediate `MovJ`/`Sync` boundaries because an interruption can leave the endpoint unknown even after release succeeded.
5. Independently query the retreat pose and verify idle state, empty queued/immediate consumer counters, healthy edge state, and open-lid telemetry before continuing the batch.
6. Preserve a UUID-linked manifest joining each Phase-A protocol/run, measured hold log, Phase-B protocol/run, and pose-query run. If fine camera checks were waived, classify pickup and seating as controller-inferred even when all commands succeed.

For a batch, create one independently recoverable Phase-A/Phase-B pair per source→holder mapping. Before each next member, use a fresh broad safety-only gate; do not let that gate silently become a fine occupancy or seating inspection the operator declined. Apply any placement R override consistently to destination stage, final descent, and retreat. Apply the requested speed factor only to the final Z descent.

## Exact native SpeedFactor for final Z only

The deployed M1Pro driver may expose normalized factors in `(0,1]` while the Dobot controller uses integer percentages `1…100`. Inspect the **live deployed methods** before authoring:

- Native `SpeedFactor(P)` maps to normalized `P/100` when `set_speed_factor` multiplies by 100 and rounds/clamps to the controller’s integer range.
- Examples: native `SpeedFactor(5)` uses `speed_factor_down=0.05`; native `SpeedFactor(10)` uses `speed_factor_down=0.10`. Never pass native percentages such as `5` or `10` into a normalized `(0,1]` driver argument.
- If `place_to` does not expose a speed argument and internally calls `safe_move` with a fixed default descent factor, do not use it for this requirement. Split placement into:
  1. `safe_move` to destination X/Y/R at safe Z;
  2. `safe_move` to final Z with `speed_factor_down=P/100` (and explicit normal lift/lateral factors);
  3. `open_gripper`;
  4. `safe_move` retreat.
- Confirm the live `_move` implementation restores the previous speed after the segment. Preserve the protocol response showing the requested factor and independently verify the retreat pose.
- Do not require ordinary edge DEBUG logs to echo the native `SpeedFactor(...)` call: some deployed drivers log only `MovJ` and `Sync` responses. In that case, establish the exact mapping from the live deployed `set_speed_factor`/`_move` implementation, preserve the protocol command and response containing `speed_factor_down=P/100`, and report that evidence accurately. Absence of a speed-setting line is not proof of failure, but it is also not native-command evidence; if literal controller-call evidence is required, arrange instrumentation before motion rather than rerunning a completed transfer.

## Queue verification through the edge environment

Before dispatch and after verification, require both immediate and queued Dobot consumers to report `num_pending=0` and `num_ack_pending=0`. If the normal NATS inspection CLI is not available on the host, use the already-running edge container's project environment as a **read-only NATS client**—never open a second Dobot controller connection. Obtain the actual NATS server list and consumer names from deployed configuration/startup evidence rather than guessing them. With current `nats-py`, `JetStreamManager.streams_info()` and `consumers_info()` are awaited coroutines returning collections, not async iterators:

```python
import asyncio, nats

async def check(servers, wanted_consumers):
    nc = await nats.connect(servers)
    js = nc.jetstream()
    for stream in await js.streams_info():
        for consumer in await js.consumers_info(stream.config.name):
            if consumer.name in wanted_consumers:
                print(stream.config.name, consumer.name,
                      "pending", consumer.num_pending,
                      "ack_pending", consumer.num_ack_pending,
                      "waiting", consumer.num_waiting)
    await nc.close()
```

Run it through the edge's declared environment launcher (for example, `uv run python`) so it uses the deployed dependency set. An idle pull consumer may show `waiting=1`; this is not queued work when pending and ack-pending are both zero. This fallback verifies queue state only—it does not replace PUDA state, container health, or an edge-mediated pose query.

## Evidence and reporting

When saving `puda protocol run` output, use `set -o pipefail` and merge stderr before `tee`: `puda protocol run --file "$protocol" </dev/null 2>&1 | tee "$log"`. Some PUDA CLI builds emit run IDs, command responses, and completion markers on stderr, so plain `| tee` can produce a zero-byte evidence file even though the terminal displayed the full successful run. Verify that each saved log is non-empty and contains its run ID/completion boundary. If physical motion already completed and a log is empty, never rerun the motion merely to recreate evidence; recover the IDs from the actual command response/session record and write a clearly labeled result ledger instead.

Persist:

- coarse/refinement manifests and fresh images;
- accepted R, outer-ring center/radius, pixel residual, move run ID, pose-verification run ID;
- transformed X/Y and transform constants;
- scan/report UUID and hashes;
- protocol command showing the exact final-Z speed factor;
- pre/post overhead checks, final robot state, edge restart count, and centrifuge state.

Separate controller success, visual destination seating, source vacancy, and gripper intent. Never infer all physical outcomes from a successful protocol alone.
