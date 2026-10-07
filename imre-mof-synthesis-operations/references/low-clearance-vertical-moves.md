# Low-clearance vertical moves near fixtures

Use this reference when an operator asks to raise or lower a robot endpoint near a rack, holder, vessel, rim, cap, or other fixture.

## Critical path-semantics warning

A requested pure Z increase or decrease is not necessarily a monotonic vertical move. On the IMRE-MOF M1 Pro, `safe_move` can take a target such as `Z=50 → Z=100` through the configured travel height first (observed `Z=50 → Z=240 → Z=100`) while preserving X/Y/R. A later low endpoint request reproduced `Z=50 → Z=240 → Z=240 → Z=8`: the implementation emitted a duplicate same-height travel segment before the final descent. Therefore:

- validate clearance for the **entire safe-path excursion** to travel height and the subsequent descent, not only the requested endpoint change;
- when asking for operator clearance, state the actual expected path explicitly (for example, “confirm `Z=50 → Z=240 → Z=8` is clear”), rather than asking only whether the descent is clear;
- inspect edge logs after execution to reconstruct the actual segment sequence, including harmless duplicate same-target segments;
- do not describe a `safe_move` as a direct vertical lift or descent unless the logs prove that path.

If the operator requires a strictly monotonic vertical move, confirm that the exposed primitive guarantees it or use a separately reviewed operation rather than assuming `safe_move` does.

## Safety gate

1. Obtain a fresh edge-mediated pose and preserve every axis the operator did not ask to change.
2. Confirm current `idle`, healthy edge/controller session, zero pending and ack-pending queue work, and workspace validity for the proposed target.
3. Capture both:
   - a fresh overhead frame for people, broad swept-path hazards, and displaced labware;
   - a fresh wrist/local frame for objects immediately beneath or beside the endpoint.
   If the wrist/local camera is unavailable, do not treat an overhead frame as equivalent. Make a tight crop of the endpoint/descent region from the fresh overhead image as supplemental evidence. If fixed hardware remains under or beside the endpoint, pause and obtain explicit operator confirmation that the object is expected and the full vertical path to the requested Z is clear; record both the unavailable local camera and that confirmation in the protocol description. A crop can localize the concern but cannot establish hidden 3D clearance.
4. Treat a nearby rim, cap, vessel, or fixture in the wrist view as a possible descent hazard. A monocular 2D frame cannot prove the requested millimetres of vertical clearance.
5. Scope operator clearance confirmations to the verified full endpoint pose and tooling orientation. A prior confirmation for the same X/Y/Z does not automatically cover a different R: rotating the wrist can move an offset camera bracket, cable loop, or other asymmetric tooling through a different swept volume. Reconfirm when R or tooling geometry changes at low clearance.
   - A prior explicit clearance to a **deeper** endpoint may cover a later shallower endpoint only when X/Y/R, tool/gripper state, labware identity, and the complete safe-path corridor are unchanged; the only intervening motion was an independently verified withdrawal along that same corridor; there was no manual access, refill, displacement, or other state change; and a fresh broad frame shows no new hazard. Record this evidence chain. Otherwise obtain a new confirmation.
   - A new low-Z command is not by itself proof of hidden clearance when local visual evidence is unavailable and the physical state may have changed.
6. If a person or body part appears in any preflight frame, dispatch nothing. After they leave, capture and inspect a new overhead frame; do not treat the old frame plus an assumption that they moved away as clearance evidence. Recheck that the machine is still idle before dispatch because the safety evidence and machine state must describe the same execution window.
7. When clearance remains unresolved, pause before dispatch and ask the operator to confirm that the visible object is expected and the descent path is clear, or to revise/cancel the target.
8. Treat a revised height in the operator's confirmation as replacing the original request. Do not execute the superseded target first. Revalidate the revised pose while preserving the fresh measured X/Y/R values.

## Staged inspection when the destination is not visible

When a low-Z request also changes X/Y and the final descent area cannot be assessed from the source pose, split the operation at a conservative inspection height:

1. Move to the requested X/Y/R at a clearly safe Z (for example, `Z=100` when installation evidence supports it), rather than descending directly to the low endpoint.
2. Independently verify the staged pose and capture fresh wrist plus overhead frames from directly above the requested endpoint.
3. Use the wrist frame to identify what lies in the descent corridor. If an occupied rotor, cap, rim, rack, or other fixture remains directly below, do not infer clearance from apparent scale; obtain explicit operator confirmation for the exact final X/Y/Z/R.
4. Describe the staging move as an intermediate safety action, not completion of the user's requested endpoint. After confirmation, execute only the fixed-X/Y/R descent and independently verify the final pose.
5. If the operator declines or revises the endpoint, keep the robot at the staged safe height and discard the superseded low target.

This pattern is especially useful for lateral moves toward occupied centrifuges: the source camera view may show only the departure area, while staging above the destination provides relevant local evidence without committing to the low descent.

## Execution and verification

- Use the exposed safe motion primitive and remember that `safe_move` may lift to travel height before descending, even for a pure Z change.
- Record the operator clearance confirmation and any revised target in the protocol description.
- After execution, require an independent edge-mediated pose query, fresh idle state, healthy edge/restart count, empty queues, and fresh overhead plus wrist images.
- Report visible contact, deformation, displacement, breakage, or abnormality conservatively. A normal-looking post-move image does not prove hidden 3D clearance or absence of contact.

### Person entering after motion

A clear preflight frame and a person visible in the post-motion frame describe different moments. Handle this timing explicitly:

1. Do not infer that the person was present during motion unless the evidence actually shows that; likewise, do not call the final scene clear merely because the move already completed.
2. State that the commanded move completed and was independently verified **before/independently of** the post-motion intrusion finding, when supported by timestamps and run logs.
3. Issue no further motion while any person or body part remains visible. A successful endpoint verification is not permission for a follow-on command.
4. Report the post-motion person/body-part observation prominently, separate from robot pose and collision findings. Avoid a blanket “no safety issue” conclusion.
5. Before the next command, require a new overhead frame showing the enclosure clear and recheck idle state and queues; do not reuse the earlier preflight frame.
6. If image/run timing is ambiguous, say so and use the conservative interpretation rather than reconstructing an unsupported sequence.

## Worked decision pattern

If an operator requests `Z=25` from `Z=50`, but the wrist frame shows a holder rim close to the endpoint, do not infer 25 mm clearance. Ask for a decision. If the operator replies that the path is clear but revises the destination to `Z=35`, execute only `Z=35`, preserve the other measured axes, and independently verify the resulting pose.