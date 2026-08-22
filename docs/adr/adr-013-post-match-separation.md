# ADR-013: Post-match facts never mutate the pre-match lock

- Status: accepted
- Date: 2026-08-22

## Decision

The canonical `prediction_locks.manifest_json` contains only data known at or
before the locked cutoff. Official results and every derived learning artifact
are written to separate `match_results`, `autopsies`, `variance_attributions`,
`lessons`, and `cases` tables. Those records retain the original lock SHA-256 as
their provenance pointer.

Post-match ingestion cannot add fields to, update, or delete a prediction lock.
The database trigger is the final enforcement boundary; API and domain tests also
assert that the exact manifest remains unchanged after an autopsy.

## Consequences

Historical evaluation is reproducible without contaminating the forecast that is
being evaluated. Corrections to official results require a new result version;
they cannot rewrite the original forecast. Case-memory retrieval must filter out
outcome-bearing fields whenever it serves a pre-match request.
