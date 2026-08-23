# Local pilot runbook

All development and verification commands execute inside Docker Compose services.

## Bootstrap

1. Copy `.env.example` to `.env` and keep real credentials out of Git.
2. Run `make bootstrap`.
3. Open the dashboard at `http://localhost:3000`, the API docs at
   `http://localhost:8000/api/docs`, Temporal UI at `http://localhost:8080`, and
   MinIO at `http://localhost:9001`.

## Verification

- `make quality` runs format, lint, strict type checking, API tests, and web tests.
- `make build` produces the API and web images using frozen dependency contracts.
- `curl http://localhost:8000/metrics` returns bounded route-template metrics.
- `docker compose run --rm migrate` upgrades the database to the current head.

## Live Gemini operation

1. Keep the API key only in the ignored `.env` file as `GEMINI_API_KEY`.
2. Set `GEMINI_ENABLED=true` in that same local file.
3. Recreate the runtime with `docker compose up -d --force-recreate migrate api worker web`.
4. Confirm the API container reports that Gemini is enabled without printing the key.
5. Start an analysis from the dashboard. A live response has
   `forecast.analysis_provider=google_gemini`, four model IDs, and a non-zero
   estimated `actual_cost_usd`.

The checked-in example and test service force `GEMINI_ENABLED=false`, preventing
paid calls during tests. Live mode fails closed with a bounded API error if a
model, quota, key, or structured response is unavailable; it never disguises a
provider failure as a mock forecast.

## Live fixture operation

1. Set `LIVE_FIXTURES_ENABLED=true` in the ignored `.env` file.
2. Optionally set `FOOTBALL_DATA_API_KEY` to a football-data.org token. It becomes
   primary for PL, PD, BL1, SA, FL1, DED, and PPL. Keep `OPENLIGADB_BASE_URL` and
   `OPENLIGADB_LEAGUES` configured as the no-token/error fallback.
3. Recreate `api`, `worker`, and `web` after changing the environment.
4. Check `/api/v1/fixtures/source-status` and a non-null `observed_at`.
5. Start a scan and confirm candidates report either
   `source_provider=football_data_org` or `source_provider=openligadb`.

Both providers use documented read-only JSON `GET` endpoints. football-data.org is
cached for five minutes to stay within its free-plan limit; an empty or failed primary
read falls back to OpenLigaDB. The OpenLigaDB cache refreshes every 60 seconds and
retains the last good in-memory snapshot during a transient upstream error.
OpenLigaDB is community-maintained ODbL data, so it can lag and must not be described as
an official second-by-second score or betting feed.

## Automatic coupon funnel

Open `http://localhost:3000/auto` and choose **En iyi maçları bul**. The service:

1. scans the configured current window but keeps only Premier League, LaLiga, Bundesliga, Serie A,
   Ligue 1, Eredivisie, Primeira Liga, and Süper Lig;
2. rejects stale seasons and every non-allowlisted competition, including Mexico
   and Colombia;
3. writes a daily journal of up to five monitored fixtures with reasons, risks,
   observed odds when available, and an explicit `journal_only` marker when odds
   are absent;
4. ranks at most ten candidates, asks a cheap Gemini role for an adaptive shortlist,
   then asks an independent Gemini critic for exactly three when live odds are present;
5. runs and locks the existing four-model MİRON BABA analysis for priced finalists;
6. returns single, double, and treble tickets only when the 70% probability and
   1.80+ live-odds value gate is cleared.

A completed run whose three selections are still pending and have not kicked off is
reused for `AUTO_COUPON_REUSE_SECONDS` (six hours by default). This prevents repeated
button clicks from spending fourteen more Gemini requests on the same fixture window.

`THE_ODDS_API_KEY` and `API_FOOTBALL_API_KEY` are used as read-only bookmaker
sources. The Odds API is tried first; API-Football is a fail-soft fallback for
quota, timeout, or empty-result days. When both bookmaker feeds are unavailable,
the system still creates a fixture-only daily journal, but `market_decimal_odds`
is `null`, the tier remains `journal_only`, and no coupon/ticket is published.
The default free-quota market set is `h2h,totals`; set `THE_ODDS_WIDE_MARKETS`
only when the quota/billing plan supports wider markets.

The API checks pending selections every `AUTO_COUPON_SETTLEMENT_SECONDS`. A final
score creates an autopsy, variance decomposition, hindsight-safe lesson, and a
searchable `case_memory_chunks` record. Case memory is retrieved for mechanism
support only and never changes a historical prediction lock.

For 30-day monitoring, call `GET /api/v1/auto-coupons/journal?limit=30` or open
`/auto`. Each pre-match run stores `daily_predictions`; each post-match run
updates `post_match_review` with hit/loss/void, Brier score where a priced pick
exists, equal-stake ROI where odds exist, and a short process verdict.

## GitHub Actions automation

`.github/workflows/daily-analysis.yml` runs the same Docker stack on GitHub-hosted
runners, so daily analysis does not depend on the local machine being online. Required
repository secrets:

- `GEMINI_API_KEY`
- `THE_ODDS_API_KEY`
- `API_FOOTBALL_API_KEY`
- `RAPIDAPI_KEY` when RapidAPI fixture fallback is used
- `MIRON_BABA_AUTOMATION_TOKEN`
- `DATA_ENCRYPTION_KEY`

The workflow writes raw runtime state only inside the runner. It commits encrypted
PostgreSQL dumps and encrypted cycle reports to the `automation-state` branch; do not
commit decrypted database dumps, raw reports, or `.env`.

## Prediction lock incident checks

1. Fetch `/api/v1/prediction-locks/{lock_id}` and record `manifest_sha256` and
   `object_uri`.
2. Hash the exact MinIO object bytes; the digest must match `manifest_sha256`.
3. Never update or delete `prediction_locks`; PostgreSQL deliberately rejects it.
4. Post-match facts belong only to `match_results`, `autopsies`,
   `variance_attributions`, `lessons`, and `cases`.

## Degraded operation

The example environment is disabled by default. The deterministic local mock
pipeline remains available with zero external model cost and marks its forecast
as provisional/degraded. The approved local environment uses four verified
Gemini routes and keeps model verification expiry, per-run cost ceilings, and
rate-limit errors explicit.
