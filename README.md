# MİRON BABA AI

Evidence-first personal football intelligence workstation. The canonical implementation contract is [`miron-baba-ai-canonical-master-spec.md`](./miron-baba-ai-canonical-master-spec.md).

## Host prerequisite

- Docker Desktop with Docker Compose v2

No host Node.js, Python, database, or package manager is required.

## First run

```bash
docker compose --env-file .env.example run --rm init-env
docker compose build
docker compose up -d
docker compose --profile test run --rm test-api
docker compose --profile test run --rm test-web
```

The example configuration keeps paid Gemini calls disabled. Runtime fixture discovery can use
the keyless OpenLigaDB community JSON API. When `FOOTBALL_DATA_API_KEY` is configured, the
football-data.org v4 feed becomes the primary source for seven covered top leagues while
OpenLigaDB remains the fallback. The test profile stays deterministic/offline.

## Live fixture source

Set `LIVE_FIXTURES_ENABLED=true` to refresh live fixtures. Add a football-data.org token to
`FOOTBALL_DATA_API_KEY` for its free top-league coverage, or leave it empty to use OpenLigaDB.
The scan, search, analysis, PostgreSQL fixture snapshot, and UI then use the same canonical live
fixture. OpenLigaDB is community-maintained, its read API needs no authentication, and
its data is licensed under ODbL; it is not an official low-latency betting feed.

## Gemini-only model setup

All LLM routes are restricted to Gemini. The configured ensemble uses Gemini
3.5 Flash-Lite for extraction, Gemini 3.7 Flash for research, Gemini 3.6 Flash
for independent criticism, and Gemini 3.5 Flash for final synthesis. No OpenAI or
Anthropic key is accepted by the environment contract.

To prepare a real connection, put `GEMINI_API_KEY` in the ignored `.env` file and
set `GEMINI_ENABLED=true`. The example and test environments keep paid calls off.
When enabled, the analysis endpoint fails closed instead of returning a mock result
after a Gemini error. See
[`docs/adr/adr-014-gemini-only-model-routing.md`](./docs/adr/adr-014-gemini-only-model-routing.md).

## Implemented runtime path

- Istanbul-canonical three-day scan and explicit fixture search from football-data.org/OpenLigaDB
- transparent candidate ranking and 31-stage pre-match analysis contract
- live four-model Gemini forecast with deterministic mock mode for tests and keyless setup
- responsible-use notice, independent critic gate, structured-output validation, and hard budget policy
- Temporal workflow registration and deterministic worker execution
- PostgreSQL persistence plus immutable prediction-lock trigger
- content-addressed MinIO lock manifests with exact SHA-256 replay
- JSON and Markdown lock exports
- post-match result ingestion, Brier autopsy, variance decomposition, validated lesson,
  and case memory kept strictly outside the pre-match lock
- leakage-failing chronological walk-forward backtest primitives
- correlation IDs, security headers, body-size limits, recursive secret redaction,
  health probes, and Prometheus-format route metrics
- simplified Gemini-first interface with one primary scan action and a collapsed
  31-stage audit trail
- separate `/auto` funnel: fixed eight-league allowlist, stale-season rejection,
  same-Istanbul-day scan, 10→adaptive shortlist→3 Gemini filtering, three locked
  MİRON BABA analyses, and single/double/treble tickets
- The Odds API/API-Football bookmaker averages with proportional overround removal;
  daily journal creation stays alive during quota/timeout failures and records
  fixture-only entries without inventing odds
- automatic result settlement, post-match autopsy, and PostgreSQL full-text case-memory
  retrieval kept outside every pre-match lock
- GitHub Actions daily pre-match/post-match cycle that runs the Docker stack on
  the runner and persists encrypted PostgreSQL/report state on the `automation-state`
  branch
- private Telegram bot notification for daily coupons and next-day learning summaries
  when `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` repository secrets are configured

Use `make quality` for the complete containerized quality gate. Operational checks
are documented in [`docs/runbooks/local-pilot.md`](./docs/runbooks/local-pilot.md).
Telegram setup is documented in [`docs/runbooks/telegram-bot.md`](./docs/runbooks/telegram-bot.md).
