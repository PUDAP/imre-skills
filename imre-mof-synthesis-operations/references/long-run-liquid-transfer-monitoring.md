# Long-run liquid-transfer monitoring

Use this pattern for multi-reagent PipQuBot protocols that run for tens of minutes and eject one tip after each reagent.

## Pre-dispatch gate

1. Validate the protocol and independently audit command counts, contiguous step numbers, source allocations, heights, tip wells, sample UUID uniqueness, and CSV-to-command totals.
2. Check both live heartbeat discovery and persisted machine state. A stale KV-state timestamp alone does not prove the edge is offline; require a current heartbeat, healthy container/process, and an idle/no-run state before dispatch.
3. Verify both PipQuBot NATS consumers are empty:
   - `cmd_queue_pipqubot_mof`
   - `cmd_immed_pipqubot_mof`
   Require `num_pending=0` and `num_ack_pending=0`; a queue consumer with `num_waiting=1` is normally waiting for work.
4. On hosts exposing the NATS monitor endpoint, obtain JetStream consumer details from `http://127.0.0.1:8222/jsz?consumers=1&accounts=1` and reduce the JSON locally rather than printing the full account report.
5. Confirm serial devices are mapped into the edge container and startup logs show successful controller connections. Host and container device names may differ; inspect the container device mapping rather than assuming identical paths.
6. Capture a fresh enclosure frame using the camera endpoint documented for that machine. Do not hard-code a generic stream name. Gate on: no person/body part inside, no obvious obstruction/spill/displaced labware, required labware plausibly present, and endpoint consistent with a known bare reference. Treat exact stock identity/volume and individual tip-well occupancy as operator provenance unless independently observable.

## Passive ejection evidence

Start the monitor **before** dispatch:

1. Record a UTC start timestamp.
2. Poll edge logs from that timestamp for the completed event `Tip dropped successfully` (not merely issuance of `RE30`).
3. After each newly completed ejection, capture one fresh camera frame and append its index, UTC timestamp, path, and capture exit code to a JSON record.
4. Stop after the protocol's audited ejection count. Keep monitoring passive; never open a second serial/controller session.

## Dispatch and durable logs

For a bounded long run, use a tracked background process with completion notification and preserve CLI output:

```bash
set -o pipefail
puda protocol run -f protocols/<protocol-id>.json 2>&1 \
  | tee logs/<protocol-id>-run-<UTC>.log
```

`pipefail` is required so a failed `puda protocol run` is not hidden by a successful `tee`.

## Post-run verification

Do not report completion from CLI exit alone. Reconcile:

- run ID and start/completion timestamps;
- every protocol command successful in the database/log, plus start/complete records;
- expected command-name counts;
- low-level pipette actions (`RI`, `RO`, `RB`, `RE30`, and `RZ` where expected) and absence of controller errors;
- final idle/no-run state, healthy edge, and empty immediate/queued consumers;
- expected number of ejection captures and a fresh post-run frame consistent with a bare endpoint;
- final run-scoped provenance/quantization artifacts preserving the original UUIDs.

Controller and camera evidence prove commanded execution and visible safety state; they do not independently measure liquid identity or delivered volume.
