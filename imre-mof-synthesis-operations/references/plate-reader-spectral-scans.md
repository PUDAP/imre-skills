# PUDA plate-reader spectral scans

Use this workflow when a plate-reader edge exposes only a single-wavelength read such as `read_absorbance(wavelength: int, wells: list[str])`, but the operator requests a spectrum.

## Resolve the scan before execution

1. Discover the live machine ID and command signature with `puda machine list` and `puda machine commands <id>`.
2. Confirm the requested wells, wavelength range, and interval. Do not silently interpret “full spectrum” as every supported integer wavelength: explicitly offer practical intervals and state the resulting point count.
3. Compute the inclusive wavelength list deterministically and verify:
   - `count = ((stop - start) / step) + 1` when exactly divisible;
   - first and last wavelengths match the request;
   - every command targets only the requested well(s);
   - step numbers are sequential.
4. Confirm the loaded plate model, tray closed, reader connected/idle, `run_id=null`, no last error, and empty command consumers.

## Protocol shape

Expand the spectrum into one sequential command per wavelength. Keep all reads in one protocol when practical, but expect a long run and preserve its complete output in a log.

```json
{
  "step_number": 1,
  "name": "read_absorbance",
  "machine_id": "<reader-id>",
  "params": {"wavelength": 230, "wells": ["A1"]}
}
```

Validate the generated protocol and independently audit command count, endpoints, interval, machine ID, command name, and well list before running. Execute with stdin detached, `set -o pipefail`, and `tee` to a durable log.

## Interrupted-scan recovery

Treat an interrupted spectrum as a data-boundary problem, not as permission to rerun the entire scan.

1. Reconstruct the exact successful prefix from per-command success responses in the run log. Map command index back to wavelength from the protocol; do not infer completion from the last “sending command” line.
2. Preserve the failed run ID, error, successful wavelength range, failed wavelength, and raw log.
3. Check fresh reader state and queues. If recovery/reset is exposed, invoke it once when appropriate. A client-side reset timeout and a later fresh idle/connected state are separate facts: only the fresh state proves recovery.
4. Require `idle`, `run_id=null`, connected, tray closed, no last error, and empty queues before resuming.
5. Generate a new validated suffix protocol beginning at the first unconfirmed wavelength. Retrying that read after verified recovery is acceptable for a non-destructive optical measurement, but do not duplicate the already confirmed prefix.
6. If the same wavelength deterministically fails again, stop and diagnose wavelength support/device health rather than cycling resets.

## Result extraction and provenance

The CLI log may contain pretty-printed multi-line JSON responses. Parse each `Response: { ... }` as a complete JSON object rather than grepping individual value lines. For each successful read, record:

- wavelength and measured value;
- well;
- completion timestamp;
- run ID;
- initial/recovery segment;
- source log path.

For a sparse plate response, verify the requested well’s matrix location (for example, A1 is the first row/first column) and ensure all unrequested wells are null as expected.

Merge segments by wavelength, sort ascending, and validate against the deterministic expected list. Require the requested point count, no missing wavelengths, no extras, and no duplicates before calling the spectrum complete.

Export:

- CSV: one row per wavelength for analysis;
- JSON: scan parameters, instrument/machine/plate/well metadata, run IDs, interruption and recovery provenance, source logs, and the full data rows.

Hash both artifacts and link them plus both run logs from `project.md`. State whether values are raw or blank-corrected; never imply blank correction when none was requested or run.

## Final verification and reporting

After the final segment, verify fresh reader state and queue counters. Report:

- requested versus recorded point count;
- range and interval;
- well and plate model;
- initial and recovery outcomes separately when applicable;
- final connected/idle/tray state and errors;
- artifact paths and hashes;
- whether the result is raw or blank-corrected.
