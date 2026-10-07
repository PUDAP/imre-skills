# Dobot composite late-transport reconciliation

Use when a blocking `pick_and_place` or similar composite physically progresses but PUDA ends with a late socket failure such as `Connection reset by peer`, `Broken pipe`, or a lost reply.

## Core rule

A nonzero client result does not prove the composite failed physically, and an expected final retreat pose is not required for the transfer itself to have completed. The labware may already be released while the robot stops during a later retreat or transit segment. Never replay the composite until the physical boundary is reconstructed.

## Reconciliation sequence

1. Preserve the protocol log and run ID. Identify whether the failure occurred before dispatch, during pick, during placement, or after release/retreat began.
2. Query PUDA state and an edge-mediated pose once. If the controller session is stale, do not open a second direct dashboard connection and do not repeatedly call reset through the same dead socket.
3. Capture a fresh broad overhead image. Seek independent physical cues:
   - source position newly vacant;
   - destination contains one new upright item;
   - gripper visibly empty versus still holding an item;
   - no fallen, horizontal, trapped, or displaced item;
   - robot location consistent with source, destination, or retreat/transit.
4. Classify the boundary explicitly:
   - **not dispatched** — logs prove no motion command was emitted;
   - **picked/possibly held** — source vacant but destination/release unverified;
   - **placed, retreat incomplete** — source vacant, destination gained the item, gripper empty, robot stopped away from the expected final retreat;
   - **unknown** — evidence is incomplete or contradictory.
5. Retry only a suffix whose prerequisites are physically established. For **placed, retreat incomplete**, never repeat the pick/place; recover the robot from its measured pose instead.

## Stale controller-session recovery

If `puda machine reset` fails with `Broken pipe` after the late transport error:

1. Confirm the robot is stationary and broad safety evidence is clear.
2. Confirm there is no active/pending/unacknowledged motion work.
3. Restart only the affected edge container/service to recreate its owned controller session; do not create a competing raw controller session.
4. Require fresh edge readiness, live registration, `idle` with `run_id=null`, and a successful edge-mediated pose query.
5. Treat the post-reconnect pose as authoritative. It may be an intermediate retreat/transit pose rather than the protocol's expected endpoint.
6. If physical evidence proves the gripper is empty and the home path is clear, home or retreat under a new reviewed command. Otherwise stop for operator reconciliation.

## Reporting

Report command status and physical status separately. Example:

- PUDA command: failed late with connection reset.
- Transfer: visually reconciled as placed/released.
- Robot: stopped at an intermediate safe transit pose after reconnect.
- Recovery: affected edge recreated; robot homed after fresh safety and empty-gripper checks.

Do not rewrite the failed run as successful; preserve it as a failed transport run with a separately verified physical outcome.
