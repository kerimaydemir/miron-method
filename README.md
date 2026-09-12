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

The example configuration keeps model calls disabled (`AI_PROVIDER=disabled`). Runtime fixture discovery can use
the keyless OpenLigaDB community JSON API. When `FOOTBALL_DATA_API_KEY` is configured, the
football-data.org v4 feed becomes the primary source for seven covered top leagues while
OpenLigaDB remains the fallback. The test profile stays deterministic/offline.

## Live fixture source

Set `LIVE_FIXTURES_ENABLED=true` to refresh live fixtures. Add a football-data.org token to
`FOOTBALL_DATA_API_KEY` for its free top-league coverage, or leave it empty to use OpenLigaDB.
The scan, search, analysis, PostgreSQL fixture snapshot, and UI then use the same canonical live
fixture. OpenLigaDB is community-maintained, its read API needs no authentication, and
its data is licensed under ODbL; it is not an official low-latency betting feed.

## NVIDIA model setup

The model registry now routes analysis to NVIDIA NIM. It assigns Nemotron
3.5 Lightning to evidence processing and four separate specialist calls,
Nemotron 3 Super to criticism, scenarios and synthesis, and Nemotron 3 Ultra
to the final critic. Exact model IDs and route limits live in
[`config/models.yaml`](./config/models.yaml). The result screen displays only
model IDs recorded by the completed run, with duplicate IDs collapsed.

For local use, set `NVIDIA_API_KEY` in the ignored `.env` file,
`AI_PROVIDER=nvidia_nim`, `NVIDIA_ENABLED=true`, and `GEMINI_ENABLED=false`.
For unattended use, set the `NVIDIA_API_KEY` GitHub Actions repository secret;
the daily workflow builds its temporary environment on the GitHub runner.
No local computer or Docker installation needs to remain running for that workflow.
The Gemini adapter remains for explicitly configured legacy use and needs its
own matching model registry; it is not an automatic paid fallback.

The NVIDIA routes use `billing_mode: trial_rate_limited`. A recorded model cost
of zero describes this trial configuration; it does not promise unlimited free
capacity, permanent pricing or a production SLA. Provider quotas and availability
still apply. Enabled model failures do not become successful mock forecasts.
See [`docs/adr/adr-019-nvidia-multi-agent-analysis.md`](./docs/adr/adr-019-nvidia-multi-agent-analysis.md)
for evidence, cost and validation boundaries.

## Implemented runtime path

- Istanbul-canonical three-day scan and explicit fixture search from football-data.org/OpenLigaDB
- transparent candidate ranking and 31-stage pre-match analysis contract
- provider-recorded multi-agent forecast with deterministic, explicitly labelled mock mode for tests and keyless setup
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
- simplified evidence-first interface with one primary scan action and a collapsed
  31-stage audit trail
- separate `/auto` funnel: fixed ten-league allowlist, stale-season rejection,
  same-Istanbul-day scan, 10→adaptive shortlist→up to 3 finalists, locked
  MİRON BABA analyses, and eligible single/double/treble tickets
- Odds-API.io/The Odds API/API-Football executable bookmaker prices with a
  separately calculated, margin-removed market consensus; every multi-leg
  ticket uses prices available at one named bookmaker rather than mixing shops;
  daily journal creation stays alive during quota/timeout failures and records
  fixture-only entries without inventing odds
- automatic result settlement, post-match autopsy, and PostgreSQL full-text case-memory
  retrieval kept outside every pre-match lock
- GitHub Actions daily pre-match/post-match cycle that runs the Docker stack on
  the runner and persists encrypted PostgreSQL/report state on the `automation-state`
  branch
- private Telegram bot notification for daily coupons and next-day learning summaries
  when `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` repository secrets are configured
- paid Gemini is disabled in unattended automation; model probabilities remain
  provisional until evaluated on settled, out-of-sample predictions. Market-only
  tickets carry no fabricated analysis lock, model edge, or 70% guarantee

Use `make quality` for the complete containerized quality gate. Operational checks
are documented in [`docs/runbooks/local-pilot.md`](./docs/runbooks/local-pilot.md).
Telegram setup is documented in [`docs/runbooks/telegram-bot.md`](./docs/runbooks/telegram-bot.md).
