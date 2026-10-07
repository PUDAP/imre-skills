# Dobot M1 Pro wrist-camera visual servoing with `R`

Use this procedure when an operator asks to keep Cartesian position fixed and rotate the M1 Pro wrist camera until a visible target is centered.

## Coordinate interpretation

- Operator-facing poses may be supplied as `x, y, z, r, a, b`.
- On the 4-axis M1 Pro path, command and verify `x, y, z, r`; preserve trailing `a=b=0` as non-actuated fields rather than silently inventing motion for them.
- During an R-only alignment, hold `x`, `y`, and `z` exactly fixed unless the operator separately authorizes translation.

## Safety and preflight

1. Use the existing PUDA edge as the sole controller client. Confirm edge readiness, machine `idle`, empty pending/ack queues, and a fresh controller-mediated pose.
2. Capture a fresh overhead safety image and a fresh wrist-camera image. At IMRE-MOF, the wrist image source is `/dev/v4l/by-id/usb-Generic_USB2.0_PC_CAMERA-video-index0` (YUYV 640x480); check ownership and allow a short exposure warm-up.
3. Treat close labware in the wrist view as a possible collision hazard. A 2D image cannot prove depth clearance; obtain operator confirmation when expected objects are immediately below/near the endpoint.
4. Treat low-clearance approval as **full-pose scoped**, including `R`, not merely scoped to `(X,Y,Z)`. A previously confirmed descent to the same XYZ does not authorize a later descent after wrist rotation: the camera bracket, cable, and asymmetric tooling occupy a different swept volume. Re-inspect both views and obtain fresh operator confirmation when endpoint clearance remains occluded.
5. Remember that this driver's `safe_move` is not an in-place wrist twist: it may lift to travel height, rotate/reposition, then descend. Validate both the raised rotation and final descent path before every adjustment. After a substantial R change at low Z, verify the exact controller pose, camera health, cable posture, and nearby labware before declaring success.

## Direction-constrained long R sweeps

When the operator specifies clockwise/counterclockwise motion to protect a wrist-camera cable, reaching the numerically equivalent target angle is not enough: the controller may choose the shorter rotation direction for a large single move.

1. Map the requested physical direction to the installation's observed R sign; on the IMRE-MOF M1 Pro, counterclockwise is positive R. Do not generalize this sign to another installation without a bounded probe or operator confirmation.
2. Read and hold the fresh controller-measured X/Y/Z. Compute a monotonic sequence of R waypoints in the requested sign.
3. Keep every R leg strictly below 180 degrees (prefer roughly 90–120 degrees) so each controller move is unambiguous. Example: a requested positive-R path from `-163°` to `+73.7°` is a `+236.7°` sweep and can be split as `-163 → -43.5 → +73.7`, rather than sent as one large endpoint move.
4. Execute and independently verify each leg before continuing. Recheck idle state, queue emptiness, overhead safety, and the wrist camera between legs; do not dispatch all legs as one blind batch.
5. Treat `safe_move` as a lift–rotate/travel–descend sequence, not an in-place twist, and validate the swept path for each waypoint.
6. After the final leg, independently query pose and capture a new wrist frame. If the camera hot-disconnects, stop rotation, wait for stable by-id re-enumeration, and verify a fresh frame before declaring alignment; never use the failed or stale capture.

### Crossing the ±180° representation boundary

An exact target such as `R=-163°` can be physically equivalent to `R=197°`, so a bare endpoint does not document or guarantee the cable-safe path.

1. If the operator previously established a cable-safe direction for the current workflow and later supplies an exact pose without restating direction, preserve that established direction unless they explicitly override it.
2. For a positive-R/counterclockwise crossing, use a verified waypoint near but below `+180°` (for example, current `136.2° → 175° → -163°`). Each leg then has an unambiguous short positive physical rotation across the representation wrap.
3. For a negative-R/clockwise crossing, use the mirrored pattern near `-180°`.
4. Verify pose, idle state, empty queues, fresh overhead safety, and wrist-camera health at the waypoint before crossing. This is especially important after any earlier USB hot-disconnect associated with cable motion.
5. Do not normalize away the operator's requested final numeric representation: independently verify and report the exact requested endpoint (for example `-163°`), while documenting the physically directed waypoint path separately.
6. On the 4-axis M1 Pro, preserve supplied `A=B=0` in provenance as non-actuated fields; do not invent fifth- or sixth-axis motion.

## Bounded image-feedback loop

1. Record image center `(width/2, height/2)` and the designated target centroid. Preserve the clean source frame.
2. Make a small bounded R probe (typically 2–5 degrees) while holding X/Y/Z fixed. Do not assume the sign of image motion.
3. Verify the resulting controller pose, capture a fresh wrist frame, and remeasure the same target.
4. Estimate local sensitivity from the probe:

   `d_pixel/dR = (centroid_after - centroid_before) / (R_after - R_before)`

5. Choose a conservative intermediate R step. Re-capture and update the estimate rather than making one large blind extrapolation.
6. Stop immediately if the target moves opposite expectation, leaves the frame, the machine errors, pose verification fails, or visual safety degrades.
7. Finish with a fine adjustment, an independent `get_pose`, fresh wrist and overhead images, healthy edge/state checks, and empty queues.

## Tracking an operator-marked adjacent target

When the operator uploads an annotated wrist image (for example, an arrow pointing to an adjacent cap), use the annotation only to establish target identity:

1. Inspect the uploaded source first and record which neighboring object is designated (for example, the partial orange component at the upper-right edge relative to the currently centered cap).
2. Capture a fresh **unannotated** live wrist frame before motion. Never run color segmentation on the annotated upload: an orange/red arrow can merge with the cap mask and corrupt its centroid.
3. Match the designated target into the clean frame by spatial relation and continuity. Track that same component across probes; do not silently switch to the larger or currently centered orange component.
4. When the target is clipped by the image boundary, treat its visible-component centroid as biased. Use it only to confirm motion direction and continue with conservative intermediate probes until the whole cap is visible; do not extrapolate a final R from a clipped centroid.
5. Once fully visible, estimate local pixel-per-degree sensitivity from the latest two clean frames and make a bounded refinement. Re-segment after every move because perspective makes the sensitivity nonlinear over a large R sweep.
6. For simple orange-cap tracking without OpenCV, a Pillow connected-component mask is sufficient when thresholds are logged and checked visually. Record component area, bounding box, centroid, frame center, and whether the frame-center pixel belongs to the **selected component** (not merely to any orange pixel).
7. Camera auto-exposure can make a strict color-ratio mask fragment between otherwise equivalent frames. Before refining from a surprising centroid jump, compare at least two logged masks (for example, a ratio threshold and a looser channel-difference threshold), require a plausible cap-sized connected component/bounding box, and visually inspect the frame. Prefer the R value whose horizontal centroid is stable across reasonable thresholds; do not steer from one fragmented mask.
8. If two consecutive adjacent caps were centered at known R values with X/Y/Z unchanged, their measured `ΔR` can seed the next adjacent-cap prediction. Treat this as an installation- and pose-specific prior, validate the predicted R against a fresh clean frame, then probe/refine if the target is not already centered.
9. Preserve the annotated upload as operator intent and the clean final frame as physical evidence. Report which objective was achieved and any residual error.

## One degree of freedom versus two image axes

Changing only `R` gives one control degree of freedom but image centering has two errors `(dx, dy)`. Exact 2D centroid coincidence may therefore be impossible. Use an explicit objective:

- If the operator's wording or setup implies horizontal centering, minimize `abs(dx)` and report residual `dy`.
- Otherwise minimize Euclidean centroid distance while keeping motion bounded.
- A frame center lying inside a large cap is useful visual evidence, but it is not the same as exact centroid alignment.
- Never claim exact centering when a measured residual remains. Report frame center, target centroid, pixel offsets, tolerance/result, and whether further R motion would worsen the chosen objective.

## Worked IMRE-MOF example (session-specific)

At fixed `(X,Y,Z)=(239.5,-77.5,50)`, the designated right orange cap began near centroid `(512,168)` in a 640x480 frame at `R=-68`. A +5 degree probe moved it toward center, and bounded updates `-68 -> -63 -> -43 -> -43.5` produced centroid approximately `(318,194)`. Horizontal error was about 2 px while vertical error remained about -46 px; the frame center lay within the cap.

In a later adjacent-target alignment, the operator marked the next upper-right cap with an arrow while the first cap was centered at `R=-43.5`. Clean live-frame tracking showed the selected target entering from the upper-right; R-only updates `-43.5 -> -35.5 -> -20.5 -> -5.5 -> 9.5 -> 15.1` kept X/Y/Z fixed and moved the selected cap to centroid approximately `(314.95,191.63)`. The horizontal error was about -5 px, the frame-center pixel lay inside that cap, and the residual vertical error was reported rather than hidden. The early target centroids were clipped-edge measurements and were used only for direction, while the final refinement used fully visible components.

For the following upper-right adjacent cap, the prior centered-cap spacing supplied a prediction of `ΔR=+58.6°`, from `R=15.1` to `R=73.7`. A strict orange ratio mask initially reported inconsistent centroids after a `72.8°` comparison because auto-exposure fragmented the cap. Reprocessing both clean frames with several exposure-robust thresholds showed stable horizontal centroids near `x=319.4` at `R=73.7` and `x=327.1` at `R=72.8`; the robot returned to `R=73.7`, and a fresh final frame measured `(319.44,183.89)` with the `(320,240)` frame-center pixel inside the selected cap. The controller independently reported `R=73.699997`, while X/Y/Z remained fixed. This demonstrates how a repeated adjacent-cap `ΔR` can seed the next move and why threshold-stability checks must precede a fine correction.

For the next **counterclockwise/positive-R adjacent cap** after the cap centered at `R=73.7`, the selected target initially appeared only as a small clipped orange component at the upper-right boundary. Holding fresh controller-measured `(X,Y,Z)=(239.532227,-77.489616,49.994659)`, bounded waypoints `73.7 → 88.7 → 108.7 → 128.7 → 135.7 → 136.2` progressively brought that same component into view and then centered it. The clipped-component centroids at the first waypoints were used only for continuity and direction; refinement began once the target was fully visible. At `R=135.7`, exposure-robust masks placed its horizontal centroid about `3.4–4.2 px` right of center. A final `+0.5°` step to `R=136.2` yielded threshold-stable `x=319.28–320.15`, or `-0.72–+0.15 px` horizontal residual, while the roughly `-71 px` vertical residual was reported rather than hidden. This is a worked example of why successive adjacent-cap spacing is only a seed: local image geometry can require substantially more rotation, so continue bounded live tracking rather than stopping at a predicted angle.

For the operator-marked **upper-left** adjacent cap, the direction reversed. After a controller power cycle, the live pose was slightly offset from the named calibration (`X=239.532225, Y=-77.489616, Z=49.994659, R=-43.402942`). Holding those freshly measured X/Y/Z values, the prior adjacent-cap spacing seeded `R=-102.002942`; the clean frame gave horizontal centroid `x≈311`. A bounded negative refinement to `R=-103.0` produced centroid `(319.91,191.91)` in a 640×480 frame, with about `0.09 px` horizontal error and the center pixel inside the selected cap. This demonstrates two important points: derive the sign from the annotation/live frame rather than reusing the preceding direction, and after a power cycle hold the freshly measured Cartesian pose instead of silently substituting nominal calibration coordinates.

During the final negative-R refinement, the USB wrist camera briefly disconnected and re-enumerated (`1908:2311`) before capture. Treat a one-shot `VIDIOC_DQBUF: No such device` after wrist rotation as a hotplug event to verify, not as permission to reuse a stale image: inspect current `/dev/video*` and the stable by-id link, check recent kernel USB events, wait for re-enumeration, then capture a new frame and verify it. If the device does not return or repeated disconnects suggest cable strain, stop further wrist rotation and escalate rather than continuing blind.

A related failure can present **without** a visible hotplug event: FFmpeg may receive no packets and write no image while the by-id symlink and `/dev/video0` remain present and kernel logs show no disconnect/re-enumeration. Treat this as camera-feedback loss, not as a successful capture or proof that the cable is healthy. After one bounded retry confirms that no valid image artifact is produced, stop all further visual-servo motion, independently record the reached robot pose/state/queue status, and ask the operator to inspect or reseat the wrist-camera cable. Do not infer the probe direction from the pre-probe frame, continue blind, or automatically reset/rebind USB hardware. Resume only after a fresh unannotated frame is captured and visually verified.

For operator-marked **non-orange targets** such as a dark empty rotor slot, use the annotation solely to identify the feature by its relation to neighboring caps. In the fresh unannotated frame, measure that slot directly rather than steering from orange-cap segmentation. Make a small R probe and require a fresh post-probe image before estimating sign or sensitivity; if that image is unavailable, leave the robot at the independently verified probe pose and report alignment as incomplete.

### Physical printed markers versus annotation arrows and look-alike symbols

Operators may call several different rotor symbols an “arrow,” while replied-to images may also contain annotation arrows. **Target identity is a safety precondition, not a cosmetic labeling step.** Distinguish these before moving:

1. Convert the operator’s crop into a positive/negative signature before motion. Example: positive = “solid white shield/chevron with a black downward arrow”; negative = “not the thin outlined triangular warning symbol, not a nearby orange cap, not a digital overlay.” Preserve the crop as the identity reference.
2. Inspect the exact target feature, not only its nearest cap. A physical outlined warning triangle and a solid white down-arrow sticker are distinct targets even though both may be casually called “the arrow.” Never choose the most salient arrow-like symbol merely because it is easier to segment.
3. Capture a fresh live frame at the independently measured pose and match the full signature—shape, fill, internal glyph, neighboring objects, and continuity. If the uploaded arrow is absent and only exists as an overlay, use it solely to identify what it points to.
4. If multiple plausible symbols remain, ask for a crop or confirmation before steering. Do not move first and disambiguate later.
5. If the operator corrects target identity after an alignment, explicitly invalidate the prior result. Restart localization from a fresh frame; do not reuse the wrong target’s centroid, pixel-per-degree estimate, or optimum R.
6. Track the correct marker centroid itself through bounded R probes. For a thin outline, estimate the geometric center from the full outline; for a white shield with an internal black arrow, measure the outer white shape consistently and use the internal glyph as an identity check.
7. When a cable-safe interval is supplied (for example `R∈[-180,+180]`), treat it as a hard representation/safety bound, not a requirement to sweep the full interval. If the target is visible, use local probes. If absent, search with bounded monotonic steps, a fresh wrist frame and overhead/cable check after every step, and stop as soon as the correct signature appears.
8. If a monotonic search reaches the ±180 representation boundary, use a verified waypoint near the boundary and preserve the established short physical direction across the numeric wrap. Continue only while overhead evidence shows usable cable slack and the wrist camera still delivers valid frames.
9. With R-only control, optimize the declared objective—normally horizontal residual `dx`—and report `dy` separately. Do not describe a marker high in the frame as fully 2D-centered merely because `x≈width/2`.

#### Corrected-target worked pattern

A thin outlined warning triangle was initially centered because it was mistaken for the requested arrow. The operator then supplied a crop showing the actual target: a **solid white shield containing a black downward arrow**. The correction invalidated the earlier alignment. A bounded positive physical-R search, with fresh wrist and overhead checks at each step, found the correct marker entering the frame near `R≈129.8°`. Tracking continued through a verified `+175° → -175°` representation crossing in the same physical direction and refined to approximately `R=-152°`, where the white marker’s horizontal centroid was near `x=320` in a 640-pixel-wide frame. Its large vertical residual remained and was reported because R alone could not remove it. The reusable lesson is the target-signature/restart procedure—not the absolute R values.

### Camera handling resets the visual calibration epoch

A manual USB reseat, cable-slack adjustment, camera-bracket touch, or other physical handling can shift the camera extrinsics even when the robot pose is unchanged. After any such intervention:

1. Treat every pre-intervention centroid, pixel-per-degree estimate, and predicted optimum as invalid for steering. Keep the old annotated image only for target identity and provenance.
2. Capture and visually verify a fresh unannotated frame at the independently measured current robot pose.
3. If the target is not already within tolerance, make a new bounded R probe and calculate sensitivity using two frames captured **after** the intervention. Never interpolate between a pre-reseat frame and a post-reseat frame; apparent target motion may be camera motion rather than robot response.
4. If the fresh frame already meets the horizontal objective, do not move merely to complete a planned correction. Report the residual and stop.

A 2026-09-07 post-reseat run demonstrated how large this epoch shift can be. At the calibrated centrifuge pose `(X,Y,Z)=(239.5,-77.5,50)`, the operator's **leftmost visible orange cap** was freshly tracked from about `x=154` at `R=-43.5`. A bounded `-5°` probe moved that same cap to about `x=176`, establishing the local sign; subsequent bounded waypoints `-48.5 → -68.5 → -76.5 → -77.7` brought it to threshold/geometry estimates near `x=318–320`. The independently measured final pose was `R=-77.699997`. An older epoch had centered an upper-left cap near `R=-103`, so reusing that absolute R would have been wrong by roughly 25°. This also reinforces target continuity: after rotation introduces other caps at the image corners, continue following the originally designated cap rather than redefining “left” from each new frame. When glare fragments a strict orange mask, compare a looser channel-difference mask with the visible circular cap/ring geometry before making the final small correction.

A second alignment in the same camera epoch showed that **Z and target scale define a new local servo regime even without reseating the camera**. At `(X,Y,Z)=(240.5,-77.5,25)`, the replied-to large cap was near the right of center at `R=-22.5`; a bounded `+3°` probe to `R=-19.5` established that positive R moved it left. An initial visual/brightness-centroid estimate then incorrectly called `R=-17.7` centered, and the operator rejected it. Re-analysis of the clean frames showed why: glare and uneven orange intensity biased the color-mask area centroid even though the task concerned the geometric center of the circular cap.

For a large, fully visible circular cap, use the **full outline geometry** as the final objective: log a plausible connected-component bounding box, inspect the metal/cap ring, and calculate `geometric_mid_x=(min_x+max_x)/2`. Use the color/intensity centroid only for target continuity and coarse direction when lighting is asymmetric. After the correction, bounded refinements `R=-17.7 → -17.2 → -17.0` moved the outline midpoint from about `x=324.5` to `x=321.5` and finally `x=319.5` in a 640-pixel-wide frame, leaving a measured horizontal residual of `-0.5 px` at independently verified `R=-17.0`. Do not claim “perfect” from a visual estimate alone; report the chosen center definition, bounds, and pixel residual, and treat ±0.5 px as the quantization floor when an integer-pixel bounding box has odd width.

Do not carry pixels-per-degree estimates from `Z=50` down to `Z=25`: apparent cap size and perspective change materially. At low Z, keep every correction small, revalidate the full lift–rotate–descent path, preserve the replied-to cap as target identity, and report horizontal geometric residual separately from the still-large vertical residual.

### Illumination changes: photometric, not geometric, recalibration

Switching the wrist-camera illuminator on or off changes color masks and brightness centroids, but does **not** by itself imply that the camera extrinsics moved. Treat it differently from a USB reseat, bracket touch, or cable adjustment:

1. Preserve the last verified R and target identity as a geometric prior, but capture a fresh stabilized frame under the new illumination before steering.
2. Re-measure the full circular outline using several reasonable masks rather than reusing one threshold. For orange caps without OpenCV, compare at least three channel-difference thresholds plus one broader ratio mask; log each selected component's area, bounding box, midpoint, and intensity centroid.
3. Require the same cap-sized component and outline across thresholds. Use the median or stable range of `geometric_mid_x=(min_x+max_x)/2` for the control objective; use brightness centroid only as a diagnostic because illumination can move it without physical motion.
4. If the stable geometric residual is already at the integer-pixel floor, stop. Otherwise make only the sub-degree correction supported by the current-pose local sensitivity, then independently verify pose and re-capture under the same illumination.
5. Keep exposure/illumination fixed throughout the final comparison. If it changes again, start a new photometric measurement set; do not compare raw mask centroids across lighting states.

In the 2026-09-07 low-Z example, turning illumination off at independently verified `R=-17.0` produced threshold-stable outline midpoints near `x=318.5–319.5`, while brightness centroids differed by threshold. A bounded `-0.05°` correction to independently verified `R=-17.049999` yielded outline midpoints `x=319.0–320.0` across four masks, a robust residual of `0–1 px` against the 640-pixel frame center. This is the appropriate stopping condition; further motion would chase threshold and pixel quantization noise rather than improve evidenced geometric centering.

### Adjacent-left cap entering from a clipped boundary at low Z

A 2026-09-07 run at fixed `(X,Y,Z)=(240.5,-77.5,25)` demonstrated a robust clipped-target-to-outline workflow. At `R=-17.700001`, the requested orange cap immediately left of the currently centered cap was only partially visible at the upper-left boundary. It remained the locked target throughout the sweep; “left” was not re-evaluated after other caps entered or exited the frame.

Bounded negative-R waypoints `-17.7 → -22.7 → -37.7 → -57.7 → -77.7` progressively brought that same cap into view. The clipped observations were used only for continuity and sign. Once the cap was fully visible, a channel-difference mask measured geometric outline midpoint `x=173.5` at `R=-57.7` and `x=322.0` at `R=-77.7`, giving a local sensitivity near `-7.425 px/degree`. Because the target was about `+2 px` right of the `x=320` objective, a bounded `+0.27°` correction produced independently verified `R=-77.43`.

In the final 640×480 frame, four reasonable orange masks gave outline bounds of approximately `x=223/224–415/416`; every midpoint was `x=319.5`, leaving `-0.5 px` horizontal residual—the integer-pixel quantization floor. This run reinforces that large clipped-to-centered sweeps need intermediate fresh frames, while the final sub-degree correction should use **two nearby fully visible outline measurements**, not a clipped centroid or a pixel-per-degree estimate imported from another Z/target regime. Fresh overhead checks at each major waypoint also verified that the wrist cable remained usable and the occupied centrifuge labware was not displaced.

### Sequential adjacent-left caps at the same low-Z pose

When the operator asks for the orange cap “on the left” immediately after one cap has been centered, interpret the request relative to the **currently centered cap in the newest frame**. Lock the newly adjacent cap before moving; do not reuse the cap that was just centered merely because it remains the largest orange component.

A continuation of the 2026-09-07 low-Z run centered the next cap to the left while holding `(X,Y,Z)=(240.5,-77.5,25)`. Starting from the independently verified prior alignment `R=-77.43`, the new target was initially clipped at the upper-left edge. Bounded negative-R waypoints `-77.43 → -97.43 → -117.43 → -137.43` preserved target continuity and brought it fully into view. The clipped observations established sign and continuity only. At `R=-117.43`, a channel-difference mask placed the outline midpoint near `x=162`; at `R=-137.43`, it was near `x=306`, giving a local sensitivity around `-7.2 px/degree` over the latest useful interval.

A bounded correction to `R=-139.38` overshot slightly to threshold-dependent midpoints `x=321.0–322.0`. A final `+0.21°` correction produced independently verified `R=-139.169998`; four reasonable masks gave outline midpoints `x=319.0–319.5`, or `-1.0–-0.5 px` residual against `x=320`. Fresh overhead images after each major waypoint showed no person, displaced labware, or obvious cable tension, and the USB camera remained available. Reusable lessons: consecutive-neighbor spacing is only a seed; recompute sensitivity from nearby frames because it changes along the sweep; and after a small overshoot, reverse with a bounded sub-degree correction rather than accepting a visually plausible estimate.

### Sequential adjacent-right caps at the same low-Z pose

Apply the same target-lock discipline when the operator requests the cap immediately to the **right** of the currently visible cap. “Right” identifies the neighbor only in the fresh starting frame; after motion begins, follow that physical cap by continuity rather than repeatedly choosing whichever cap is currently image-right.

A 2026-09-07 low-Z run began at controller-verified `(X,Y,Z,R)=(240.5,-77.5,25,-22.5)`. The requested right-adjacent cap was initially outside or clipped at the upper-right boundary. Bounded positive-R waypoints `-22.5 → -2.5 → 17.5 → 37.5` brought the same cap fully into view while the original cap moved toward the left. The interval from `R=17.5` to `R=37.5` moved the selected cap from roughly `x≈490` to `x≈351`, giving a local sensitivity near `-6.95 px/degree`. A bounded refinement to `R=42.0` placed the full circular outline slightly left of center; reversing by only `-0.45°` produced independently verified `R=41.549999`, with orange-outline midpoint about `x=319.5` against the `x=320` objective.

Reusable lessons:

- Determine the R sign from fresh motion; do not assume “right” always means positive R on another installation or camera epoch.
- Two caps may be visible simultaneously during the handoff. Preserve identity using the original right-neighbor relation plus continuity as one cap exits left and the selected cap enters right.
- Use clipped targets only for direction and continuity. Estimate sensitivity from two nearby frames after the selected cap is fully visible.
- If a final correction crosses the center slightly, reverse with a sub-degree step rather than continuing in the original direction.
- Keep X/Y/Z fixed, independently verify final pose, and finish with fresh wrist/overhead frames plus idle, edge, camera, and queue checks.

#### Continuing to the next right-hand neighbor from a supplied start pose

A later 2026-09-07 continuation exposed an important state-handling detail: the operator said to work “from” `(240.5,-77.5,25,41.549999)` and attached the frame captured there, but the robot had since returned to the named center at `R=-22.5`. An attached or replied-to frame establishes **target identity and intended start geometry**, not live robot state. Independently query the controller; if the measured pose differs, safely move to the supplied start pose, verify it, and capture a fresh clean frame before beginning the neighbor servo. Never calculate the first correction as though the robot were still at the pose represented by the attachment.

From the freshly restored start near `R=41.55`, the next upper-right neighbor was locked by relation to the centered cap. Bounded positive-R waypoints `41.55 → 61.55 → 81.55 → 96.55 → 100.35` brought that same clipped component into full view. At `R=96.55`, its full-outline midpoint remained roughly 27–32 px right of `x=320`; the local fully-visible sensitivity supported the final `+3.8°` refinement. Independent verification measured `R=100.349998`, and the final full circular outline was approximately centered at `x=319–320` while X/Y/Z remained unchanged.

Reusable additions:

- Distinguish **image pose**, **operator-specified start pose**, and **live controller pose**; reconcile them before motion.
- When the requested start pose was previously verified but is not current, re-run its safe move and take a new clean target-lock frame rather than steering from the old attachment.
- For sequential neighbors, do not infer the final R by simply adding the previous spacing. Use that spacing only to choose bounded probes, then derive the refinement from nearby fully visible frames.
- Preserve the same physical neighbor through frames where both the old cap and new cap are visible; the old cap moving left while the new cap enters from the right is useful continuity evidence.

### Chaining adjacent-cap centering into an R-relative X/Y transform

When one request combines visual centering with a calibrated translation, treat it as two independently verified phases. Do not compute the translation from the operator-supplied start R, a predicted adjacent-cap spacing, or the last commanded target.

1. Reconcile the supplied/image pose with live controller state, then complete the bounded R-only servo while holding X/Y/Z fixed.
2. Independently query the final centered R and preserve the clean centered wrist frame as alignment evidence. This measured R is the transform input.
3. Apply the installation's calibrated displacement rule. For the current IMRE-MOF centrifuge workflow:

   `theta = R_measured - (-17.049999 deg)`

   `dX = cos(theta)*30.5 - sin(theta)*1.0`

   `dY = sin(theta)*30.5 + cos(theta)*1.0`

   Keep full precision through calculation and protocol generation; let the controller report its own final precision.
4. Check queues and fresh overhead/cable safety again after the final R correction. The alignment verification does not authorize a subsequent X/Y move automatically.
5. Near occupied centrifuge labware, execute the translation as lift to a validated clearance Z, traverse to transformed X/Y while preserving measured R, inspect fresh wrist/overhead frames at the staged destination, then descend vertically to the requested Z.
6. Independently verify the transformed endpoint and report both phases separately: centered R and residual first, transformed dX/dY and final measured pose second.
7. Near the +/-180-degree representation boundary, calculate with the controller's numeric R exactly as reported. The rotation formula is periodic, but the physical cable path is not; preserve cable-safe waypoint discipline for any later R move.

A low-Z continuation illustrated the sequence: the supplied start `R=100.349998` was first restored from a different live pose, the next right-hand cap was tracked through bounded positive-R probes, and the final controller-verified center was `R=160.949997`. Only then was the transform calculated, yielding approximately `dX=-30.516320 mm`, `dY=+0.065046 mm`. The robot staged the transformed X/Y at clearance height before descending to `Z=50`. The durable lesson is the phase boundary: **verify centered R, then calculate and safety-gate the transform**.

### Full-range repeated-cap census

Use this pattern when the operator explicitly requests an entire bounded R sweep to detect and log every repeated circular target, rather than only a local alignment:

1. Reconcile the live controller pose and hold the freshly measured X/Y/Z. Inspect the overhead and wrist views before motion; at low Z, remember each `safe_move` may lift, rotate/travel, and descend.
2. Treat known centers or expected angular spacing only as **search/refinement seeds**. The result still requires a fresh frame and fresh full-outline measurement at every candidate; never report historical R values as a new scan.
3. Establish the first boundary safely, then advance in one physical direction through ordered candidate/scan waypoints. Keep each motion leg below 180 degrees, verify controller pose after every cap, and take periodic overhead cable checks at major angular legs. Reach the requested final boundary only after the last target is verified.
4. When illumination makes strict masks fragment into several small components, do not steer from those fragments. Compare multiple logged masks and inspect the visible metal/cap ring. A broad mask may recover one plausible cap-sized bounding box; accept a center only when the **full circular outline** supports the same horizontal midpoint. Refine with a bounded sub-degree move when the stable midpoint is outside the 0–1 px quantization/noise floor.
5. De-duplicate targets by ordered angular continuity. For a ring of `N` targets, calculate all adjacent spacings plus the wraparound spacing `R_first + 360 - R_last`; verify the count, mean spacing, and maximum deviation from `360/N` with a calculation tool.
6. Persist an inspectable CSV (one row per target) containing controller-measured R, spacing to next, verification time, move/run ID, centering method, measured midpoint/range, and wrist-image path. Record the scan protocol, any refinement protocol, final boundary pose, health/state, and report path in `project.md`.
7. Finish with an independent pose query at the requested boundary, idle/queue and edge-health checks, wrist-camera enumeration, and a final overhead image. Report target coordinates separately from the robot's final boundary pose.

A 2026-09-08 low-Z census at fixed `(X,Y,Z)=(240.5,-77.5,25)` swept `R=-180°` to `R=+180°` and freshly verified six orange caps. Historical centers were used only as candidates. Five candidates were accepted from fresh full-outline evidence; one candidate at `R=-17.049999°` showed a 1–2 px left residual and received a bounded `-0.15°` refinement to controller-measured `R=-17.200001°`, where the complete broad outline midpoint was `x=320.0`. The six measured centers were approximately `[-139.169998, -77.43, -17.200001, 41.549999, 100.349998, 160.949997]°`; circular spacings averaged exactly `60°`, with the wraparound included. Several frames demonstrated the photometric pitfall: strict/medium masks fragmented while the full visible ring and a broader mask remained geometrically centered. The reusable lesson is to combine fresh per-cap evidence, full-outline recovery, bounded refinements, circular-spacing validation, and auditable CSV provenance—not to reuse these absolute angles as universal calibration.

### Leaving an alignment pose or homing

Homing can be a much larger wrist sweep than the final visual-servo correction and can expose cable problems that tiny probes did not. On this M1 Pro, the first-class `home` operation also opens the gripper before moving to the configured home pose.

- Before homing from a rotated wrist pose, inspect cable slack for the **entire current-R to home-R sweep**, not only the local probe range, and account for the gripper-open side effect if anything may be held.
- Verify home independently through the edge and with an overhead frame. Treat wrist-camera health as a separate result: a successful, exactly verified home can coexist with the USB camera disconnecting during the sweep.
- If the camera disconnects and does not re-enumerate, do not dispute the independently measured robot home pose, but report that no post-home wrist evidence exists and request a physical cable check before the next camera-guided motion.

These examples demonstrate the calibration method, not reusable absolute R values or universal adjacent-cap spacing.