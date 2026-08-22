# ADR-015: OpenLigaDB live fixture feed

## Status

Accepted on 2026-08-22.

## Decision

Use OpenLigaDB's documented, unauthenticated JSON read API as the continuously
refreshed fixture-discovery source. Normalize upstream match IDs, competitions,
teams, timestamps, status, scores, and observation time into the existing domain
contract. Cache the last good response for 60 seconds and preserve it across
transient upstream failures.

Gemini does not invent or discover the authoritative fixture list. Gemini receives
the normalized fixture and deterministic triage packet, then performs the four
analysis roles already registered in the Gemini-only model routing contract.

## Consequences

- Local scans and search work without a second paid API key.
- Analysis and prediction locks persist an exact snapshot of the selected live fixture.
- OpenLigaDB attribution and ODbL licensing must remain visible.
- The community feed can be delayed or incomplete and is not represented as an
  official league, betting, or second-by-second score service.
- Tests explicitly disable live fixtures and use deterministic adapters.
