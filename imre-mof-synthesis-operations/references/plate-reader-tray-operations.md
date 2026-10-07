# PUDA plate-reader tray operations

Use this pattern for non-robot lab instruments exposed through PUDA when the requested physical action is tray open/close.

## Live discovery and preflight

```bash
puda machine list
puda machine commands <reader-machine-id>
puda machine state <reader-machine-id>
```

Copy the exact live machine ID and command name. Before actuation, require a fresh state showing `connected: true`, a non-busy state, and no unresolved run. Record the initial tray state. Ensure nobody is reaching into the tray path and the front of the instrument is unobstructed.

## Live status versus retained telemetry

`puda machine state` may return the last retained heartbeat rather than a controller-fresh read. Compare its timestamp with the current host time. For a status request—or when the retained value is not fresh enough for actuation—use the reader's exposed read-only `get_state`/`get_position` command through a one-command PUDA protocol, then re-read `puda machine state` after completion. Reuse a registered query protocol when one exists; if a new protocol file is created, place it under `protocols/`, validate it, and immediately record both creation and every run in `project.md` according to `puda-memory`. Do not leave an unrecorded ad-hoc query protocol in `/tmp` merely because it is read-only.

A reader edge may run on another host. Absence of a matching container in local `docker ps` is not evidence that the reader is offline. In that topology, use live PUDA discovery, a successful edge-mediated read-only query, heartbeat freshness, and machine-scoped NATS consumer counters as the available health evidence; state that local container health/restart information is unavailable rather than guessing.

## One-command protocol pattern

Create a protocol containing only the exact exposed tray command, normally with empty parameters:

```json
{
  "step_number": 1,
  "name": "open_tray",
  "machine_id": "<reader-machine-id>",
  "params": {}
}
```

Follow the `puda-protocol` and `puda-memory` skills: validate, record creation, execute with stdin detached, record the run, and preserve the run ID.

```bash
puda protocol validate -f <protocol.json>
puda protocol run --file <protocol.json> </dev/null
```

## Independent verification

After the command succeeds, query the machine again:

```bash
puda machine state <reader-machine-id>
```

Report success only when the command response and fresh state agree:

- opening: response reports success and post-state has `tray_open: true`
- closing: response reports success and post-state has `tray_open: false`
- machine remains connected and idle
- `run_id` is cleared
- `last_error` is null

A successful command proves tray position, not plate presence, plate identity, or correct plate seating. State those as unknown unless separately verified.

## IMRE Tecan Infinite 200 Pro details

Current machine ID observed: `imre-tecan-infinite-200-pro`. Live registry exposed `open_tray`, `close_tray`, `get_position`, `get_state`, `home`, `reset`, `shutdown`, and absorbance/fluorescence/luminescence reads. Treat current `puda machine commands` output as authoritative because deployed edge commands can change.

Do not use `home` merely for tray motion: on this reader it reinitializes the backend. Do not use `reset` for routine closure: it reinitializes the reader and leaves the tray closed. Keep tray-only requests separate from measurement operations unless the operator explicitly authorizes a validated sequence.

## Long wavelength scans on the IMRE Tecan

The deployed `read_absorbance` interface accepts one integer wavelength and a well list per command; it does not expose a native range/interval scan. Expand a requested spectrum deterministically and verify the inclusive point count, endpoints, interval, well list, sequential step numbers, and exact machine ID before execution.

For scans longer than roughly 40 wavelength points, split the range into contiguous non-overlapping protocols of at most 36 readings each. This installation completed two consecutive single-well chunks of 36 and 35 readings, while an earlier 78-command run completed 51 readings and then timed out reading the USB device. Between chunks, require fresh `idle`, `run_id=null`, `connected=true`, `tray_open=false`, `last_error=null`, and empty queue counters. Preserve a separate log and run ID for every chunk, then parse successful response JSON blocks into one sorted CSV/JSON artifact and verify the expected wavelength set has no gaps or duplicates.

Do not estimate an all-well scan from single-well timing. On this installation, one A1-only wavelength took about 5 seconds, while one all-96-well wavelength took about 77 seconds; a 36-wavelength all-well chunk therefore takes roughly 46 minutes. Before launching the full job, time one representative wavelength (or use a recent same-scope run), calculate a conservative per-chunk timeout, and start each chunk as a tracked background process with `notify_on_complete=true` and a timeout comfortably above the estimate. A default or arbitrarily chosen 600-second timeout can terminate a healthy all-well chunk mid-read. For multi-hour scans, report that execution is in progress with an evidence-based ETA, but do not claim completion until every chunk and the combined artifact are verified.

If a chunk fails with a USB read timeout, do not discard earlier successful readings or blindly rerun the whole spectrum. Record the exact completed boundary and failed wavelength, inspect fresh state and queues, and use the exposed reset path only for recovery. A client-side reset timeout can race with a successful backend reinitialization; require a later fresh state proving `idle`, `run_id=null`, connected, tray closed, and no last error before creating a suffix protocol beginning at the first unrecorded wavelength. Report the split outcome and preserve both run logs. Do not claim blank-corrected absorbance unless a blank/reference procedure was explicitly run.

If the client process is interrupted during an all-well read, treat the in-flight wavelength separately from the already logged completed wavelengths. The edge can remain `state=reading` with one `ack_pending` command after the client has sent its completion boundary. Wait for a fresh state transition rather than resetting during the physical read. Once the edge returns idle, a stale non-null run ID may remain; with empty queues and no error, invoke the exposed reset once, tolerate a short client-side reset timeout, and require a later fresh `idle`/`run_id=null`/connected/tray-closed/no-error state before resuming. Rerun only the unverified wavelength suffix; if a complete chunk is deliberately rerun, ensure the final artifact deterministically selects one complete run and records the discarded attempt.

If the operator changes priorities while a scan is active, report the exact completed and in-flight boundary and ask whether to finish the current workflow or stop before dispatching the replacement scan. A newly requested scan does not implicitly cancel an accepted read, and killing the client does not cancel the device-side operation.

For result shaping, map the returned 8×12 plate matrix by rows `A`–`H` and columns `1`–`12`. Preserve a long-form provenance table with `wavelength_nm`, `well`, `absorbance`, completion time, run ID, chunk, and source log. When the operator requests a wide dataframe, pivot to one row per wavelength and columns `A1`…`H12` in plate order. Verify unique `(wavelength, well)` keys, the complete wavelength series, exactly 96 well columns, and zero missing cells before delivery.
