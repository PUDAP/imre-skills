# Sample and stock provenance for CSV-driven liquid handling

Use this with `pipqubot-liquid-handling.md` and `run-scoped-sample-identifiers.md` when an operator supplies both a formulation CSV and a stock-register CSV.

## Provenance workflow

1. Read the original uploaded files, preserve their paths, and compute SHA-256 hashes. Do not rely on a prior same-named attachment.
2. Match each protocol reagent to a stock-register row using chemical identity plus formulation context. A name-only join may be ambiguous when the stock table contains multiple preparations of the same compound.
3. Resolve duplicate compound rows from explicit evidence only: concentration/solubility comments, mixture description, formulation stoichiometry, or operator confirmation. For example, a mixed precursor name can select the row whose comment explicitly describes that mixture; different transfer volumes may support—but do not alone prove—a particular concentration choice.
4. If more than one row remains plausible, pause and ask. Never choose the first row silently.
5. If a transferred reagent has no stock-register row, record `stock_id: null` and `concentration: null` with a note such as `not listed in uploaded stock CSV`. Do not invent IDs or infer pure-reagent molarity. This commonly applies to solvents and modulators.
6. Copy concentration values and units exactly as supplied. Preserve comments that define the basis (for example, “concentration by Ti, Zr:Ti 1:4”) rather than reinterpreting the number.
7. Validate every reagent’s commanded total against the operator-stated available source volume before motion. Keep operator-declared starting volume separate from measured inventory.
8. Generate UUIDs before motion and save one pending manifest containing:
   - source CSV paths and hashes;
   - protocol ID and pending status;
   - reagent → source slot/well → stock ID → concentration mapping;
   - per-sample UUID, label, target, destination, formulation volumes, and stock metadata;
   - reagent totals and stated source capacities.
9. After execution, retain the same UUIDs, bind the manifest to the actual run ID/outcome, and add controller audit counts. Do not regenerate identifiers after dispatch.
10. Export a flat CSV as well as JSON when humans need to review provenance. Prefer one row per `(sample, reagent)` with sample UUID, label, target, destination, commanded volume, source, stock ID, concentration, units, and note.

## Evidence boundaries

- Stock identity, concentration, and starting quantity are operator/upload evidence unless independently assayed.
- Controller logs prove commanded aspiration/dispense/ejection behavior, not composition or delivered volume.
- A completed manifest is artifact persistence, not PUDA `sample`-table registration. Read back database rows before claiming registration.
- A safety-gated or cancelled pending manifest does not prove samples were produced.

## Completion report

Include:

- run ID and command/controller verification;
- a compact stock mapping table, explicitly showing missing stock rows;
- label → destination → UUID;
- paths or attachments for the final JSON and review CSV;
- the operator-evidence/controller-evidence limitation statement.
