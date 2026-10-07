# Capper Connectivity Preflight and No-Route Failure Boundary

Use this when operating a PUDA capper backed by an HTTP RepRap controller.

## Why container health and PUDA state are insufficient

A capper edge container can report `healthy`, and `puda machine state capper` can report `idle`, while the physical RepRap controller is unreachable. Always inspect the state timestamp: an old timestamp may be stale KV state rather than current readiness. The edge may remain connected to NATS and continue exposing commands even while every `rr_status` request fails.

## Required preflight before capper motion

1. Check `puda machine state capper` and compare its timestamp with the current operation time. Treat a materially stale timestamp as unverified readiness.
2. Confirm the capper edge container is running/healthy, but do not treat that as controller health.
3. Inspect recent edge logs for repeated telemetry failures such as `Failed to reach RepRap device`, `No route to host`, or failed `rr_status` requests.
4. Run an edge-mediated read-only `get_position` or `get_status` command. Require a fresh successful response before dispatching `decap`, `cap`, clamp, release, or gantry motion commands.
5. If the read-only check fails, stop and report the controller as unreachable. Do not dispatch motion merely because PUDA says `idle`.

## Failure-boundary reconstruction

For a failed `decap`, inspect the driver traceback and the first device request:

- If the first call (commonly `release_top`, emitted as an HTTP `rr_gcode` request such as `M42 P1 S0`) fails at connection establishment with `No route to host`, no device command was accepted. Report no capper action dispatched; tube/cap state is unchanged only as a software inference, not sensor-confirmed.
- If any HTTP request received a controller response before failure, reconstruct all accepted steps and treat the physical state as unknown until independently verified. Never rerun `decap` from the beginning without this reconstruction.

## Recovery

Verify host routing and reachability to the configured numeric controller IP. A container restart cannot repair an offline controller or a failed network path. Once connectivity returns, first obtain a fresh edge-mediated position/status response, then establish a clean PUDA run state and execute only the reviewed unfinished operation.

## Applying a controller-IP change by Docker rebuild

Use this when the operator explicitly changed the Capper edge `.env` and requests a rebuild/redeployment.

1. Read only the required non-secret keys (typically `QUBOT_IP` and `MACHINE_ID`); redact NATS URLs, tokens, and unrelated environment values. Validate `docker compose config` and Docker daemon access before stopping the working container.
2. Inspect startup semantics before recreation. This Capper edge calls `driver.startup()`, which connects to the RepRap controller, homes all gantry axes, and releases both clamps. Treat rebuild/recreation as physical actuation: require no active run or queued work and a fresh camera frame showing no person, held tube/cap, clamp obstruction, or blocked homing path.
3. When the user explicitly requested a rebuild, run `docker compose build`, record the resulting image digest, then `docker compose up -d --force-recreate`. A mounted `.env` still requires recreation to affect the running process.
4. Verify the mounted configuration inside the new container contains the requested controller IP without printing secret-bearing lines. Avoid echoing the edge's `Full config` log record because it can include NATS connection details; filter logs to startup/controller/NATS readiness markers.
5. Require all layers before reporting success:
   - container running/healthy with zero unexpected restarts;
   - startup reached machine initialization and edge-ready/NATS subscription markers;
   - fresh `puda machine state capper` is `idle` with no active run;
   - an edge-mediated, non-motion `get_status` and `get_position` both succeed against the new controller session;
   - controller status reports idle and expected homed-axis flags/position;
   - queues have zero pending and unacknowledged work;
   - a post-startup image shows no visible collision or abnormality.
6. Report the configured IP, image digest, container status, restart count, PUDA state, controller firmware status, homed axes, and measured position separately. A green Docker healthcheck alone is not controller verification.
