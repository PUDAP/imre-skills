# Visual cap-status inspection

Use this procedure when deciding whether a laboratory tube is capped from a camera frame.

## Classification labels

Report exactly one primary label:

- **CAPPED** — a solid cap surface visibly covers the tube opening; a complete cap boundary, disk, or characteristic ridged top is visible.
- **UNCAPPED** — the open tube mouth is visibly unobstructed; the dark opening and tube rim are distinguishable, with no cap surface covering them.
- **UNCERTAIN** — neither condition is clearly visible because of rack occlusion, blur, glare, low contrast, crop, or ambiguous slot occupancy.
- **EMPTY** — use only when the task includes checking whether a slot contains a tube and the image clearly shows an empty well.

Never use a successful `cap` or `decap` command as visual evidence. Protocol history may explain why the frame was captured, but the classification must come from visible pixels.

## Target localization

1. Name the physical object and rack before analyzing: for example, **black cap rack**, **white tube rack**, or **CAP station**.
2. Resolve spatial language explicitly: `upper-left`, `bottom-left`, `leftmost visible tube`, etc. Do not silently substitute a nearby rack.
3. If the request is ambiguous and several racks are visible, state which rack and slot you interpreted. If the user corrects the rack, re-run image analysis focused on the corrected object.
4. Distinguish a dark open tube mouth from an empty dark rack well. If the tube body/rim is not visible enough to establish occupancy, report **UNCERTAIN**, not uncapped.

## Preferred camera checkpoint

For cap-status verification, prefer placing the tube at the dedicated **CAP station** and moving the robot to the documented overhead safe pose before capture. A rack can hide most of the tube top and produce an inconclusive crescent or dark well. At CAP, a solid colored cap disk or an open tube mouth is usually much easier to distinguish.

If a rack image is uncertain and moving the sample is authorized, use a staged workflow:

1. Move the tube to CAP.
2. Move the robot to the safe overhead CAP pose.
3. Capture and validate one RTSP frame.
4. Classify CAPPED / UNCAPPED / UNCERTAIN from pixels.
5. If return requires approval, leave the tube at CAP and request approval before the return protocol.

## Reporting

Include:

- primary label and confidence;
- the exact rack/station and slot assessed;
- 1–3 visible cues;
- any occlusion or ambiguity;
- the image attachment;
- whether the tube remains at CAP or was returned.

Do not overstate moderate evidence. A completed capping command plus an ambiguous rack image is still **UNCERTAIN** visually.
