# Direct Dobot transfers when pick/place visual verification is waived

Use this procedure when an operator explicitly authorizes an M1Pro tube transfer from calibrated source geometry to registered destination geometry without wrist-camera pick/place-location checks.

## Scope of the waiver

The waiver removes wrist-camera alignment/occupancy pauses only. It does **not** waive:

- fresh PUDA idle/run-state and edge-health checks;
- an edge-mediated controller pose query;
- confirmation that a centrifuge is stopped and its lid is open;
- broad enclosure/person/obstruction safety;
- independent final pose/state verification;
- honest distinction between controller success and physical tube placement.

Do not silently treat “no visual verification” as permission to ignore a known loose tube, unresolved prior placement anomaly, person entry, or blocked travel path.

## Preflight after a prior anomaly or unavailable broad camera

1. Reconcile the previous transfer boundary from the command log and final pose query.
2. If a prior broad safety image showed a loose/fallen tube, keep the robot idle until that obstruction is cleared.
3. Attempt the normal fresh broad safety view. If it is unavailable, do not encode the outage as a permanent tool limitation. Require an explicit operator confirmation that:
   - the prior loose tube was removed or reseated;
   - the enclosure and robot travel path are clear; and
   - the named destination well is empty.
4. Treat that confirmation as scoped to the next transfer. After the robot moves, a new request needs a fresh view or fresh operator clearance when the camera remains unavailable.
5. If the broad stream returns during a later transfer, resume normal fresh pre/post broad safety captures immediately. When the fresh preflight shows no person, loose/fallen tube, broad-path obstruction, closed lid, or displaced equipment, proceed without asking for redundant operator clearance; do not analyze exact source alignment or destination occupancy after those checks were explicitly waived.
6. In a repeated direct-transfer series, a successful final pose query for transfer N proves robot endpoint only. It does not establish that transfer N seated correctly or that transfer N+1's destination is clear; re-establish broad safety independently before every subsequent motion.

## Deterministic direct-transfer sequence

Resolve the source from the latest accepted scan/calibration row and the destination from the active registered labware artifact. Keep their provenance separate. For a driver whose `pick_from` does not actually lift, use explicit steps:

1. `safe_move` to the source pick pose.
2. `close_gripper`.
3. `safe_move` to the source X/Y/R at the approved carry Z.
4. `safe_move` to the destination X/Y/R at the carry Z.
5. `place_to` at the registered destination Z.
6. `safe_move` to the destination X/Y/R at the retreat Z.

Validate the protocol, recheck idle/edge state immediately before dispatch, run with `set -o pipefail` and stdin redirected from `/dev/null`, then issue a separate edge-mediated `get_pose` query.

## Evidence and reporting

- A successful `close_gripper`/`DOExecute` proves command acceptance, not retention.
- A successful `place_to` proves the descent and open command completed at the controller level, not that the tube seated upright.
- Without visual, sensor, or operator confirmation, report pickup and destination seating as **software-inferred**, never physically confirmed.
- If a broad safety frame taken for person/obstruction monitoring incidentally reveals a newly fallen or diagonal tube, that is a safety finding even when precise pick/place visual verification was waived. Stop further motion, label the requested placement physically incomplete, retain the robot at the verified retreat pose, and require manual clearance or an explicitly reviewed recovery. Never auto-repeat the pick or place.
- If all indexed controller sequences succeed but the post-series broad frame apparently shows a source tube remaining, treat the series as **physically discrepant**, not complete. Do not guess which sensorless grasp failed and do not issue an unplanned extra pickup (for example, a seventh move after six indexed transfers). Home only after confirming the broad path is safe; preserve each successful controller run, mark all unverified physical outcomes separately, and request explicit operator direction for a diagnostic scan or recovery.
- Maintain an occupancy ledger with evidence grades: before a waived-visual run, `source=expected occupied` and `destination=expected empty`; afterward use `source=software-inferred empty` and `destination=software-inferred occupied`. Upgrade to `confirmed` only from an allowed physical observation or sensor. A six-target de novo scan validates target geometry, not later grasp retention.
- Record source geometry, destination labware UUID/well, protocol/run IDs, final measured pose, gripper command state, edge state/restarts, camera availability, and the evidence grade in `project.md`.

## Calibration correction after a controller-successful bad placement

A controller-successful descent/open can still leave a tube lying across the rack when the registered placement depth is wrong. Do not retry the same placement or edit the old artifact in place.

1. Stop at the independently verified retreat pose and clear the loose tube manually or through an explicitly reviewed recovery.
2. Preserve the broad-safety evidence and record that controller execution succeeded while physical placement failed/incomplete.
3. When the operator supplies corrected coordinates, create a new UUID-backed labware artifact, preserve and hash the exact source CSV, and mark the previous UUID as superseded.
4. Compare old and new artifacts field-by-field and report the exact changed positions/axes; verify all unchanged values as well as exact CSV-to-JSON round trip.
5. Resolve every later named-well transfer from the active labware UUID in `project.md`; do not copy coordinates from historical protocols. Keep historical protocols unchanged for provenance.

In one September 2026 MTP calibration revision, all 24 `A1:D6` well Z values changed uniformly from 14 mm to 12 mm while X/Y/R and the special `CAP` pose stayed unchanged. This is provenance, not a universal depth; always load the currently active revision.
