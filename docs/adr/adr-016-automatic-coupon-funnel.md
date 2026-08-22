# ADR-016: Automatic coupon funnel and case-memory loop

## Status

Accepted on 2026-08-22.

## Decision

Expose a separate automatic workflow with a fixed eight-league allowlist: Premier
League, LaLiga, Bundesliga, Serie A, Ligue 1, Eredivisie, Primeira Liga, and Süper
Lig. Competition membership is explicit; country-risk stereotypes are not used as
a scoring feature. Mexico, Colombia, lower divisions, cups, and every unlisted
competition are excluded by policy.

Rank no more than ten current fixtures deterministically. Use Gemini Flash-Lite for
an adaptive rough shortlist and a different Gemini Flash model as independent
critic. Exactly three survivors enter the existing four-route MİRON BABA analysis
and immutable prediction-lock path.

Use authenticated football-data.org v4 as the primary fixture source for its seven
free European top leagues when a token is configured. Keep OpenLigaDB as the
no-token, empty-response, error, and Süper Lig fallback. A directory of public APIs
is discovery evidence only; every selected provider still needs its own documented
contract, coverage, and terms check.

Use The Odds API only for read-only, timestamped 1X2 market observations. Average
valid bookmaker quotes by outcome and remove overround proportionally. If no API key
is configured, show reciprocal model probability only as `model_fair_odds`; never
mislabel it as a bookmaker quote.

Persist coupon selections separately from prediction locks. After final scores,
create the existing autopsy and variance artifacts and add a full-text searchable
case-memory chunk containing pre-match thesis, predicted and realized outcomes,
failure explanation, variance, and hindsight-safe lesson.

## Consequences

- The user gets a one-action 10→shortlist→3 flow without weakening prediction-lock
  immutability.
- Historical cases support mechanisms and error patterns, never outcome copying.
- Provider gaps are visible: an unavailable league produces no candidate rather than
  a stale or fabricated fixture.
- No bet-placement or bookmaker-account action is implemented.
