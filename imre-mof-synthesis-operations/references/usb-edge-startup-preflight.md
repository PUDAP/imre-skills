# USB-backed PUDA edge startup preflight

Use this checklist before starting or recreating a Docker Compose edge that maps serial/USB hardware.

## Preflight

1. Render the effective Compose configuration and record each `devices:` source and bind-mount source.
2. Verify Docker daemon access in the same execution context used for startup.
3. Verify each device source exists as a character device. Check stable `/dev/serial/by-id/` links when available; do not silently substitute a different port.
4. Verify every bind source exists and has the expected type. In particular, a source intended to be a file must be a regular file—not a directory.
5. If configuration or hardware is absent, report the exact prerequisites before startup. Do not infer controller readiness from a previously stored PUDA state.

## Startup and failure handling

1. Start with Compose and retain the exact daemon error.
2. If Docker reports `error gathering device information ... no such file or directory`, the container never started and no physical command was dispatched.
3. After a failed create/start, inspect `compose ps -a`: distinguish `Created`, `Restarting`, `Running`, and `Healthy`.
4. Recheck bind sources. Docker may create a missing bind source as a root-owned directory during container creation. Before retrying, remove the accidental directory with appropriate authorization and restore the intended configuration file.
5. Do not repeatedly retry while the hardware device remains absent.

### Hot-unplugged serial devices on an already-running edge

A shallow Docker healthcheck can remain `healthy` after USB serial hardware disappears. Treat `termios.error: (5, 'Input/output error')`, missing `/dev/serial/by-id`, and absent `/dev/ttyUSB*`/`ttyACM*` nodes as controller-disconnected evidence even when the container and NATS consumer are alive.

1. Reconcile the failed run before recovery. If logs and `command_log` show failure at the first `home` serial-buffer operation, before tip pickup or liquid handling, record zero transfer commands; do not infer this from the client exit code alone.
2. Check host enumeration at three layers: stable by-id symlinks and their resolved targets, serial character nodes, and USB enumeration. Do not restart repeatedly while the host still sees only root hubs/no serial bridges.
3. A user saying the cables were reconnected is permission to recheck, not proof that Linux enumerated them. Retry bounded enumeration checks, then report the physical prerequisite if devices remain absent.
4. Once the exact configured by-id devices return, capture a fresh no-person/no-obstruction frame because edge startup may home and initialize actuators.
5. Use Compose **force-recreate**, not merely an in-place process restart, so the new container receives fresh device mappings after hot unplug/replug.
6. Prove both channels independently from startup logs: gantry serial connect followed by successful homing, and pipette serial connect followed by successful initialization. Then require edge-ready/NATS subscription markers, fresh `idle` with `run_id=null`, and zero pending/ack-pending queue work.
7. Expect edge recreation to clear software deck registration. Do not mistake an empty software deck for physical labware absence; require the next protocol to load/register every required labware item.

## Live verification

After prerequisites are repaired:

1. Recreate/start only the affected edge.
2. Require a running/healthy container and successful controller initialization in logs.
3. Confirm a fresh PUDA heartbeat/live discovery entry.
4. Read machine state and verify its timestamp is fresh.
5. Run an exposed read-only position/status command through the edge when available.
6. Report physical readiness only after controller and edge-mediated checks succeed.

## Reporting distinctions

- **Stored state:** historical KV value; stale if heartbeat/discovery is absent.
- **Edge state:** container lifecycle and health.
- **Controller state:** serial/network controller connection established by the edge.
- **Physical outcome:** motion or attachment confirmed separately; a failed Docker startup proves no edge command was dispatched.
