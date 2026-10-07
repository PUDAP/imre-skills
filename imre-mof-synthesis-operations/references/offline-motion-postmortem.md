# Offline Robot Motion Postmortem

Use this when the robot is offline or the user explicitly prohibits motion, code edits, or controller contact.

## Evidence order

1. Read the PUDA project record, protocol JSON, saved run logs, and `command_log` database rows.
2. Read edge/container logs without starting or restarting the edge.
3. Inspect the exact deployed source snapshot, not only repository HEAD. For a stopped Docker container, copy the relevant files to a temporary directory with `docker cp`; compare hashes or Git blobs, image/container creation times, and commit times.
4. Trace request → driver → dashboard/move API → completion synchronization. Identify the last controller command that could have been sent.
5. Compare a motion response with an immediately following edge-mediated pose query. A returned target is not a measured pose.
6. Check generic workspace validation independently of controller behavior and orientation logic.
7. Reproduce false-success paths offline with a fake device that returns controller rejection/empty responses. Assert whether the driver still returns success; do not contact hardware.
8. Verify the repository remains unchanged with `git status` and `git diff --exit-code`.

## Failure signatures

### Reported target but unchanged pose

A driver may return the requested target unconditionally after calling `MovJ`/`Sync`. If API return values are ignored or nonzero controller responses are not parsed, PUDA can report success even when the robot rejected motion. Confirm with a follow-up pose from the same edge connection and an offline fake-controller replay.

### Long wait or stuck run

Trace blocking reads separately:

- dashboard path: `GetPose`, `GetAngle`, orientation/config commands;
- move path: `MovJ`, `Sync`.

Look for sockets without timeouts, swallowed send/receive exceptions, retries that multiply the timeout, and redundant pose queries. A completion stall is not proof that the target was invalid.

### Bytes/string parser failure

If an empty or closed socket returns bytes and a string regex/parser consumes them, establish whether the exception occurred before `MovJ`. When it did, state explicitly that no motion command was reached. Do not blame a preceding orientation command merely because it ran first; compare with non-orientation commands that fail through the same stale connection.

### Orientation change near regression

Treat an orientation commit as a plausible trigger, not a confirmed root cause, unless raw controller responses show rejection. Check:

- documented numeric mapping (for example, left/right values);
- whether the branch is chosen from an oversimplified heuristic such as the sign of one coordinate;
- whether the selected branch makes the pose unreachable;
- whether the deployed API discarded the `SetArmOrientation`, `MovJ`, or `Sync` error response.

The usual causal chain may be: orientation or pose causes controller rejection → API suppresses rejection → driver returns requested target → PUDA records false success. Separate the trigger from the error-handling defect.

## Reporting

Report confirmed, plausible, and unproven causes separately. Include:

- exact run IDs and timestamps;
- last reached source line/command;
- whether `MovJ` was reached;
- requested target versus measured pose;
- deployed revision versus repository HEAD;
- code-change and hardware-contact status.
