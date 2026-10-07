# Run-scoped sample UUID manifests

Use this alongside a physical protocol run when named output samples require unique identifiers.

## State model

Distinguish clearly:

1. **Generated** — UUIDs exist in working output.
2. **Persisted as an artifact** — mapping is saved in a run/project JSON or CSV.
3. **Registered in PUDA** — rows exist in the live `sample` table and have been read back.

Never call artifact-only identifiers database-registered.

## Procedure

1. Generate one UUIDv4 per named output and bind it to label, destination slot/well, target identity, protocol ID, and run ID when available.
2. If UUIDs are generated before execution, save the manifest with an explicit status such as `pending_run_safety_clearance`; retain the same UUIDs when the run proceeds rather than silently creating a second set.
3. Confirm the live `sample` schema and look for an official sample-create command/API.
4. Do not assume `puda db exec` allows mutation; some deployments restrict it to query operations. Do not bypass that policy by mutating SQLite directly.
5. If no supported sample-write interface exists, preserve the run-scoped manifest under `reports/` and state that the database table remains unchanged.
6. Verify by reading the artifact or database rows back: exact sample count, unique UUIDs, UUID version 4, labels, wells, protocol, and run association.
7. After execution, change the manifest status to the actual run outcome and add the run ID. Cancelled or failed runs retain provenance but must not be presented as produced samples.

## Reporting

Report identifier provenance separately from physical execution. A UUID can be valid and durable even while motion is withheld at a safety gate; that does not mean the sample was made.