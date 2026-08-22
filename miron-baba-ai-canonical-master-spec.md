---
title: "MİRON BABA AI — Canonical Master Implementation Specification"
short_title: "MİRON BABA AI Master Spec"
document_status: "canonical"
document_version: "1.0.0"
product_name: "MİRON BABA AI"
technical_slug: "miron-baba-ai"
generated_at: "2026-08-22T00:00:00+03:00"
timezone: "Europe/Istanbul"
primary_sport: "football"
future_sports: ["basketball", "volleyball"]
audience: ["Codex", "maintainers", "analysts"]
minimum_required_lines: 6000
normative_language: "MUST/SHOULD/MAY per RFC 2119 style"
---

# MİRON BABA AI — Canonical Master Implementation Specification

> This file is the single canonical implementation contract for the personal-use sports intelligence application.
> The canonical product name is MİRON BABA AI; UI labels, metadata, Compose project names, and user-facing exports MUST use this exact spelling.
> Codex MUST treat explicit requirements in this file as authoritative unless a later ADR intentionally supersedes them.
> The system produces probabilistic analysis, not certainty, financial advice, or guaranteed betting outcomes.

## 0. How Codex Must Read This Document

1. Read sections 0 through 12 before creating any production source file.
2. Create an implementation ledger that maps each requirement ID to code, tests, and evidence.
3. Do not silently replace the prescribed stack; write an ADR before any material substitution.
4. Do not bind business logic directly to a fixture, odds, search, or model vendor.
5. Implement the vertical slice in the roadmap before breadth.
6. Keep every prediction reproducible from immutable inputs, configuration, prompts, and model metadata.
7. Treat provider timestamps, observation timestamps, and event cutoffs as distinct fields.
8. Never use post-cutoff information in a pre-match prediction or backtest.
9. Do not scrape restricted betting websites; use licensed or explicitly permitted provider APIs only.
10. Do not call a model ID “current” without passing the re-verification gate defined later.
11. Default to a mock provider and deterministic model stubs in tests.
12. Never expose provider secrets, model keys, raw private notes, or internal chain-of-thought in the UI.
13. Emit concise rationale, citations, uncertainty, and structured evidence instead of hidden reasoning.
14. Stop a run safely when budget, provenance, freshness, or identity constraints fail.
15. Prefer an explicit degraded result over a deceptively complete-looking result.

## 1. Product Mandate

### 1.1 Product statement

Build MİRON BABA AI as a deliberately slow, evidence-first, personal sports intelligence workstation.
Football is the first production sport.
Basketball and volleyball are later adapters, not conditionals scattered through football code.
The user can press one scan button to inspect fixtures for three Istanbul calendar dates.
The user can also search for any supported match and start a deep analysis manually.
The system ranks which fixtures deserve expensive analysis before spending substantial model or data-provider budget.
The final output is a calibrated scenario forecast with transparent evidence, disagreement, uncertainty, and lock status.

### 1.2 Core user outcomes

- See today, tomorrow, and the day-after-tomorrow fixtures according to Europe/Istanbul calendar boundaries.
- Understand why a match is or is not worth deep analysis.
- Start one analysis from a compact match row or search result.
- Watch meaningful progress through separately named stages.
- Inspect evidence, timestamps, provider provenance, contradictions, and missing data.
- Receive probabilities, scenarios, uncertainty bands, and market comparison without false certainty.
- Freeze a prediction before kickoff and prove that it was not changed afterward.
- After the match, ingest the result, separate luck from model error, and preserve lessons.

### 1.3 Explicit non-goals for the pilot

- No automated bet placement.
- No bankroll custody, deposits, withdrawals, or bookmaker account automation.
- No evasion of geo-restrictions, access controls, robots rules, paywalls, or provider terms.
- No claim that an LLM is a statistically validated forecasting model by itself.
- No real-time in-play decision engine in phase one.
- No public multi-tenant SaaS in phase one.
- No universal coverage promise for every league.
- No training on copyrighted provider content beyond the provider license.
- No display of private chain-of-thought; only auditable conclusions and evidence summaries.

### 1.4 Public-information and private-life boundary

- MİRON BABA AI MAY use public, reliable, performance-relevant information such as official absences, public disciplinary decisions, travel, workload, and public press-conference statements.
- MİRON BABA AI MUST NOT collect private messages, private medical records, private psychological information, doxxed material, or unlawfully obtained personal data.
- The system MUST NOT infer or diagnose depression, anxiety, relationship conflict, addiction, or another sensitive condition from rumor or behavior.
- A public off-field development is admissible only when its relevance, source, timestamp, and uncertainty are explicit.
- Gossip, anonymous rumor, and private-life speculation cannot become a player-impact feature.

### 1.5 Normative requirement vocabulary

| Term | Meaning |
| --- | --- |
| MUST | Required for acceptance; absence blocks release. |
| MUST NOT | Forbidden; presence blocks release. |
| SHOULD | Default expectation; deviation requires documented reason. |
| SHOULD NOT | Avoid unless measured evidence supports the exception. |
| MAY | Optional extension that cannot weaken required guarantees. |

## 2. Non-Negotiable System Invariants

### INV-001 — Istanbul date window

- Rule: A scan resolves exactly three local dates from an injected clock and converts boundaries to UTC safely.
- Enforcement: application service, database constraint where possible, and a test named `test_inv_001`.
- Failure behavior: stop the affected stage, preserve evidence, emit a machine-readable reason, and show a compact user-facing explanation.
- Audit evidence: record the decision in `audit_events` with the run correlation ID.

### INV-002 — Fixture identity

- Rule: The canonical event ID never equals a vendor ID and survives provider changes.
- Enforcement: application service, database constraint where possible, and a test named `test_inv_002`.
- Failure behavior: stop the affected stage, preserve evidence, emit a machine-readable reason, and show a compact user-facing explanation.
- Audit evidence: record the decision in `audit_events` with the run correlation ID.

### INV-003 — Prediction cutoff

- Rule: Every evidence item used in a prediction has observed_at less than or equal to cutoff_at.
- Enforcement: application service, database constraint where possible, and a test named `test_inv_003`.
- Failure behavior: stop the affected stage, preserve evidence, emit a machine-readable reason, and show a compact user-facing explanation.
- Audit evidence: record the decision in `audit_events` with the run correlation ID.

### INV-004 — Immutable lock

- Rule: A locked forecast cannot be updated or deleted through application code.
- Enforcement: application service, database constraint where possible, and a test named `test_inv_004`.
- Failure behavior: stop the affected stage, preserve evidence, emit a machine-readable reason, and show a compact user-facing explanation.
- Audit evidence: record the decision in `audit_events` with the run correlation ID.

### INV-005 — Evidence provenance

- Rule: Every material factual claim points to one or more immutable source snapshots.
- Enforcement: application service, database constraint where possible, and a test named `test_inv_005`.
- Failure behavior: stop the affected stage, preserve evidence, emit a machine-readable reason, and show a compact user-facing explanation.
- Audit evidence: record the decision in `audit_events` with the run correlation ID.

### INV-006 — Model configurability

- Rule: Model IDs, prices, capabilities, and routing rules come from versioned configuration.
- Enforcement: application service, database constraint where possible, and a test named `test_inv_006`.
- Failure behavior: stop the affected stage, preserve evidence, emit a machine-readable reason, and show a compact user-facing explanation.
- Audit evidence: record the decision in `audit_events` with the run correlation ID.

### INV-007 — Price re-verification

- Rule: Production model pricing and IDs are manually or automatically re-verified immediately before implementation and release.
- Enforcement: application service, database constraint where possible, and a test named `test_inv_007`.
- Failure behavior: stop the affected stage, preserve evidence, emit a machine-readable reason, and show a compact user-facing explanation.
- Audit evidence: record the decision in `audit_events` with the run correlation ID.

### INV-008 — Provider legality

- Rule: Only configured allowed providers are called; restricted-site scraping is impossible by design.
- Enforcement: application service, database constraint where possible, and a test named `test_inv_008`.
- Failure behavior: stop the affected stage, preserve evidence, emit a machine-readable reason, and show a compact user-facing explanation.
- Audit evidence: record the decision in `audit_events` with the run correlation ID.

### INV-009 — Budget stop

- Rule: A run cannot exceed its approved hard budget.
- Enforcement: application service, database constraint where possible, and a test named `test_inv_009`.
- Failure behavior: stop the affected stage, preserve evidence, emit a machine-readable reason, and show a compact user-facing explanation.
- Audit evidence: record the decision in `audit_events` with the run correlation ID.

### INV-010 — Idempotency

- Rule: Replaying the same command and idempotency key cannot create duplicate logical work.
- Enforcement: application service, database constraint where possible, and a test named `test_inv_010`.
- Failure behavior: stop the affected stage, preserve evidence, emit a machine-readable reason, and show a compact user-facing explanation.
- Audit evidence: record the decision in `audit_events` with the run correlation ID.

### INV-011 — Reproducibility

- Rule: Locked output can be reconstructed from stored versions, inputs, and deterministic transforms.
- Enforcement: application service, database constraint where possible, and a test named `test_inv_011`.
- Failure behavior: stop the affected stage, preserve evidence, emit a machine-readable reason, and show a compact user-facing explanation.
- Audit evidence: record the decision in `audit_events` with the run correlation ID.

### INV-012 — No look-ahead

- Rule: Backtests enforce knowledge-time and effective-time boundaries.
- Enforcement: application service, database constraint where possible, and a test named `test_inv_012`.
- Failure behavior: stop the affected stage, preserve evidence, emit a machine-readable reason, and show a compact user-facing explanation.
- Audit evidence: record the decision in `audit_events` with the run correlation ID.

### INV-013 — Uncertainty

- Rule: Probabilities are accompanied by calibration state and uncertainty.
- Enforcement: application service, database constraint where possible, and a test named `test_inv_013`.
- Failure behavior: stop the affected stage, preserve evidence, emit a machine-readable reason, and show a compact user-facing explanation.
- Audit evidence: record the decision in `audit_events` with the run correlation ID.

### INV-014 — Contradictions

- Rule: Unresolved material contradictions are visible and reduce confidence.
- Enforcement: application service, database constraint where possible, and a test named `test_inv_014`.
- Failure behavior: stop the affected stage, preserve evidence, emit a machine-readable reason, and show a compact user-facing explanation.
- Audit evidence: record the decision in `audit_events` with the run correlation ID.

### INV-015 — Degraded honesty

- Rule: Missing critical inputs produce explicit degraded status rather than fabricated completeness.
- Enforcement: application service, database constraint where possible, and a test named `test_inv_015`.
- Failure behavior: stop the affected stage, preserve evidence, emit a machine-readable reason, and show a compact user-facing explanation.
- Audit evidence: record the decision in `audit_events` with the run correlation ID.

### INV-016 — Sport isolation

- Rule: Sport-specific rules live behind a SportPlugin interface.
- Enforcement: application service, database constraint where possible, and a test named `test_inv_016`.
- Failure behavior: stop the affected stage, preserve evidence, emit a machine-readable reason, and show a compact user-facing explanation.
- Audit evidence: record the decision in `audit_events` with the run correlation ID.

### INV-017 — Human control

- Rule: The user can cancel queued or running work without corrupting completed stages.
- Enforcement: application service, database constraint where possible, and a test named `test_inv_017`.
- Failure behavior: stop the affected stage, preserve evidence, emit a machine-readable reason, and show a compact user-facing explanation.
- Audit evidence: record the decision in `audit_events` with the run correlation ID.

### INV-018 — Post-match separation

- Rule: Post-match facts never mutate pre-match evidence or locked forecasts.
- Enforcement: application service, database constraint where possible, and a test named `test_inv_018`.
- Failure behavior: stop the affected stage, preserve evidence, emit a machine-readable reason, and show a compact user-facing explanation.
- Audit evidence: record the decision in `audit_events` with the run correlation ID.

### INV-019 — Auditability

- Rule: Each state transition records actor, reason, time, correlation ID, and prior state.
- Enforcement: application service, database constraint where possible, and a test named `test_inv_019`.
- Failure behavior: stop the affected stage, preserve evidence, emit a machine-readable reason, and show a compact user-facing explanation.
- Audit evidence: record the decision in `audit_events` with the run correlation ID.

### INV-020 — Secret safety

- Rule: Secrets never enter prompts, logs, snapshots, exports, or client bundles.
- Enforcement: application service, database constraint where possible, and a test named `test_inv_020`.
- Failure behavior: stop the affected stage, preserve evidence, emit a machine-readable reason, and show a compact user-facing explanation.
- Audit evidence: record the decision in `audit_events` with the run correlation ID.

### INV-021 — Personal data minimization

- Rule: The pilot stores no unnecessary personal data.
- Enforcement: application service, database constraint where possible, and a test named `test_inv_021`.
- Failure behavior: stop the affected stage, preserve evidence, emit a machine-readable reason, and show a compact user-facing explanation.
- Audit evidence: record the decision in `audit_events` with the run correlation ID.

### INV-022 — No automatic wagering

- Rule: No code path can place, confirm, or settle a wager.
- Enforcement: application service, database constraint where possible, and a test named `test_inv_022`.
- Failure behavior: stop the affected stage, preserve evidence, emit a machine-readable reason, and show a compact user-facing explanation.
- Audit evidence: record the decision in `audit_events` with the run correlation ID.

### INV-023 — Source freshness

- Rule: Each source class has a declared TTL and stale behavior.
- Enforcement: application service, database constraint where possible, and a test named `test_inv_023`.
- Failure behavior: stop the affected stage, preserve evidence, emit a machine-readable reason, and show a compact user-facing explanation.
- Audit evidence: record the decision in `audit_events` with the run correlation ID.

### INV-024 — Claim normalization

- Rule: Equivalent claims use canonical subjects, predicates, units, and time ranges.
- Enforcement: application service, database constraint where possible, and a test named `test_inv_024`.
- Failure behavior: stop the affected stage, preserve evidence, emit a machine-readable reason, and show a compact user-facing explanation.
- Audit evidence: record the decision in `audit_events` with the run correlation ID.

### INV-025 — Lineup uncertainty

- Rule: Unconfirmed lineup information is probabilistic and never represented as confirmed.
- Enforcement: application service, database constraint where possible, and a test named `test_inv_025`.
- Failure behavior: stop the affected stage, preserve evidence, emit a machine-readable reason, and show a compact user-facing explanation.
- Audit evidence: record the decision in `audit_events` with the run correlation ID.

### INV-026 — Odds timestamps

- Rule: Odds snapshots preserve provider, bookmaker, market, line, price, and observed time.
- Enforcement: application service, database constraint where possible, and a test named `test_inv_026`.
- Failure behavior: stop the affected stage, preserve evidence, emit a machine-readable reason, and show a compact user-facing explanation.
- Audit evidence: record the decision in `audit_events` with the run correlation ID.

### INV-027 — Fair probabilities

- Rule: Market comparisons remove overround with a named method.
- Enforcement: application service, database constraint where possible, and a test named `test_inv_027`.
- Failure behavior: stop the affected stage, preserve evidence, emit a machine-readable reason, and show a compact user-facing explanation.
- Audit evidence: record the decision in `audit_events` with the run correlation ID.

### INV-028 — Independent critics

- Rule: Critical stages do not see another critic’s prose before producing their first verdict.
- Enforcement: application service, database constraint where possible, and a test named `test_inv_028`.
- Failure behavior: stop the affected stage, preserve evidence, emit a machine-readable reason, and show a compact user-facing explanation.
- Audit evidence: record the decision in `audit_events` with the run correlation ID.

### INV-029 — Prompt versioning

- Rule: Every model response records a prompt template version and rendered-input hash.
- Enforcement: application service, database constraint where possible, and a test named `test_inv_029`.
- Failure behavior: stop the affected stage, preserve evidence, emit a machine-readable reason, and show a compact user-facing explanation.
- Audit evidence: record the decision in `audit_events` with the run correlation ID.

### INV-030 — Experiment isolation

- Rule: Shadow experiments cannot change the user-visible production forecast.
- Enforcement: application service, database constraint where possible, and a test named `test_inv_030`.
- Failure behavior: stop the affected stage, preserve evidence, emit a machine-readable reason, and show a compact user-facing explanation.
- Audit evidence: record the decision in `audit_events` with the run correlation ID.

### INV-031 — Safe retry

- Rule: Retries use bounded exponential backoff with jitter and error classification.
- Enforcement: application service, database constraint where possible, and a test named `test_inv_031`.
- Failure behavior: stop the affected stage, preserve evidence, emit a machine-readable reason, and show a compact user-facing explanation.
- Audit evidence: record the decision in `audit_events` with the run correlation ID.

### INV-032 — Provider quota

- Rule: Quota consumption is measured and included in run budget decisions.
- Enforcement: application service, database constraint where possible, and a test named `test_inv_032`.
- Failure behavior: stop the affected stage, preserve evidence, emit a machine-readable reason, and show a compact user-facing explanation.
- Audit evidence: record the decision in `audit_events` with the run correlation ID.

### INV-033 — Search ambiguity

- Rule: Ambiguous match search requires explicit selection, never heuristic auto-start.
- Enforcement: application service, database constraint where possible, and a test named `test_inv_033`.
- Failure behavior: stop the affected stage, preserve evidence, emit a machine-readable reason, and show a compact user-facing explanation.
- Audit evidence: record the decision in `audit_events` with the run correlation ID.

### INV-034 — Timezone display

- Rule: The UI labels Istanbul time and preserves original provider timezone metadata.
- Enforcement: application service, database constraint where possible, and a test named `test_inv_034`.
- Failure behavior: stop the affected stage, preserve evidence, emit a machine-readable reason, and show a compact user-facing explanation.
- Audit evidence: record the decision in `audit_events` with the run correlation ID.

### INV-035 — Structured output

- Rule: All agent outputs validate against versioned Pydantic contracts before persistence.
- Enforcement: application service, database constraint where possible, and a test named `test_inv_035`.
- Failure behavior: stop the affected stage, preserve evidence, emit a machine-readable reason, and show a compact user-facing explanation.
- Audit evidence: record the decision in `audit_events` with the run correlation ID.

### INV-036 — No silent coercion

- Rule: Invalid provider values are quarantined rather than coerced into plausible values.
- Enforcement: application service, database constraint where possible, and a test named `test_inv_036`.
- Failure behavior: stop the affected stage, preserve evidence, emit a machine-readable reason, and show a compact user-facing explanation.
- Audit evidence: record the decision in `audit_events` with the run correlation ID.

### INV-037 — Data deletion

- Rule: Retention and deletion are explicit, scoped, and auditable.
- Enforcement: application service, database constraint where possible, and a test named `test_inv_037`.
- Failure behavior: stop the affected stage, preserve evidence, emit a machine-readable reason, and show a compact user-facing explanation.
- Audit evidence: record the decision in `audit_events` with the run correlation ID.

### INV-038 — Model refusal

- Rule: Refusals are classified as model outcomes and never parsed as successful analysis.
- Enforcement: application service, database constraint where possible, and a test named `test_inv_038`.
- Failure behavior: stop the affected stage, preserve evidence, emit a machine-readable reason, and show a compact user-facing explanation.
- Audit evidence: record the decision in `audit_events` with the run correlation ID.

### INV-039 — Cost attribution

- Rule: Every external call is attributed to a run, stage, vendor, and purpose.
- Enforcement: application service, database constraint where possible, and a test named `test_inv_039`.
- Failure behavior: stop the affected stage, preserve evidence, emit a machine-readable reason, and show a compact user-facing explanation.
- Audit evidence: record the decision in `audit_events` with the run correlation ID.

### INV-040 — Final critic veto

- Rule: The final critic can force one bounded revision or a no-publish outcome.
- Enforcement: application service, database constraint where possible, and a test named `test_inv_040`.
- Failure behavior: stop the affected stage, preserve evidence, emit a machine-readable reason, and show a compact user-facing explanation.
- Audit evidence: record the decision in `audit_events` with the run correlation ID.

### INV-041 — Docker-only local runtime

- Rule: On macOS, Docker Desktop and the repository are the only host prerequisites; every application, worker, migration, test, build, and tool command runs in a container.
- Enforcement: application service, database constraint where possible, and a test named `test_inv_041`.
- Failure behavior: stop the affected stage, preserve evidence, emit a machine-readable reason, and show a compact user-facing explanation.
- Audit evidence: record the decision in `audit_events` with the run correlation ID.

### INV-042 — Canonical product identity

- Rule: The user-facing product name is exactly MİRON BABA AI and cannot drift across UI, exports, logs, or Compose metadata.
- Enforcement: application service, database constraint where possible, and a test named `test_inv_042`.
- Failure behavior: stop the affected stage, preserve evidence, emit a machine-readable reason, and show a compact user-facing explanation.
- Audit evidence: record the decision in `audit_events` with the run correlation ID.

### INV-043 — Prediction abstention before Chief

- Rule: Research, verification, specialists, critics, Sonnet syntheses, and steelman agents cannot select a winner or emit the final LLM probability vector; only the Chief stage may do so.
- Enforcement: application service, database constraint where possible, and a test named `test_inv_043`.
- Failure behavior: stop the affected stage, preserve evidence, emit a machine-readable reason, and show a compact user-facing explanation.
- Audit evidence: record the decision in `audit_events` with the run correlation ID.

### INV-044 — Live market isolation

- Rule: In-play odds live in the LIVE MARKET namespace and can never be inserted retroactively into pre-match evidence or the locked forecast.
- Enforcement: application service, database constraint where possible, and a test named `test_inv_044`.
- Failure behavior: stop the affected stage, preserve evidence, emit a machine-readable reason, and show a compact user-facing explanation.
- Audit evidence: record the decision in `audit_events` with the run correlation ID.

### INV-045 — Result versus process

- Rule: Post-match evaluation stores result correctness and process correctness separately.
- Enforcement: application service, database constraint where possible, and a test named `test_inv_045`.
- Failure behavior: stop the affected stage, preserve evidence, emit a machine-readable reason, and show a compact user-facing explanation.
- Audit evidence: record the decision in `audit_events` with the run correlation ID.

### INV-046 — Evidence-layer separation

- Rule: Raw source, normalized claim, and analytical interpretation are distinct immutable lineage-linked artifacts.
- Enforcement: application service, database constraint where possible, and a test named `test_inv_046`.
- Failure behavior: stop the affected stage, preserve evidence, emit a machine-readable reason, and show a compact user-facing explanation.
- Audit evidence: record the decision in `audit_events` with the run correlation ID.

### INV-047 — Docker test parity

- Rule: The same container images and Compose-defined commands used locally execute lint, typecheck, contract, integration, and browser tests.
- Enforcement: application service, database constraint where possible, and a test named `test_inv_047`.
- Failure behavior: stop the affected stage, preserve evidence, emit a machine-readable reason, and show a compact user-facing explanation.
- Audit evidence: record the decision in `audit_events` with the run correlation ID.

## 3. Canonical Glossary

- **analysis run:** One orchestrated evaluation of one canonical fixture under one cutoff and one config snapshot.
- **scan run:** Discovery and ranking of fixtures across the three-day Istanbul window.
- **candidate:** A fixture eligible for triage but not yet approved for deep analysis.
- **deep analysis:** The full evidence, quant, committee, critic, and locking workflow.
- **evidence item:** An immutable captured statement or structured datum with source and observation time.
- **source snapshot:** A content-addressed record of provider or web content used as evidence.
- **claim:** A normalized proposition derived from one or more evidence items.
- **contradiction:** Two or more claims that cannot simultaneously be accepted for the same scope and time.
- **freshness:** The relationship between observed time, provider update time, cutoff, and source-specific TTL.
- **cutoff:** Latest permitted knowledge timestamp for a forecast.
- **prediction lock:** Append-only artifact containing the final pre-match forecast and integrity hashes.
- **market snapshot:** Odds and lines observed from an allowed provider at a precise instant.
- **fair probability:** A bookmaker-implied probability after the named margin-removal method.
- **edge:** Model probability minus fair market probability, never a guarantee.
- **calibration:** Agreement between predicted probability buckets and empirical outcome rates.
- **sharpness:** Concentration of forecasts away from base rates, evaluated only with calibration.
- **Brier score:** Mean squared error of probability forecasts.
- **log loss:** Negative log likelihood of the realized class.
- **expected calibration error:** Weighted difference between confidence and observed frequency across bins.
- **variance:** Random outcome variation not necessarily attributable to model error.
- **autopsy:** Post-match comparison of forecast, evidence, process, scenarios, and result.
- **lesson:** A validated, reusable post-match finding with scope and confidence.
- **case memory:** Retrievable prior match cases and lessons that are cutoff-safe.
- **agent:** A bounded stage role with a schema, retrieval policy, tools, budget, and exit criteria.
- **committee:** Independent high-value model calls followed by structured synthesis.
- **critic:** An adversarial stage that searches for material weaknesses.
- **red team:** A stage that attempts to invalidate assumptions, evidence, and scenarios.
- **steelman:** The strongest plausible construction of an alternative scenario.
- **degraded mode:** An explicit reduced-capability result caused by missing or stale inputs.
- **quarantine:** Storage for invalid, ambiguous, or untrusted payloads excluded from decisions.
- **knowledge time:** When the system could have known a datum.
- **effective time:** When the datum applies in the real world.
- **bitemporal:** Data modeled with both knowledge time and effective time.
- **provider abstraction:** A stable internal interface isolating vendor-specific behavior.
- **canonical fixture:** Provider-independent normalized sports event.
- **entity resolution:** Mapping provider teams, players, competitions, and venues to canonical IDs.
- **retrieval policy:** Agent-specific rules defining allowed indexes, filters, ranking, and context budget.
- **RAG:** Retrieval-augmented generation using stored, cited, cutoff-safe context.
- **vector index:** Similarity index used for semantically retrieving documents and prior cases.
- **knowledge graph:** Entity and relationship representation for cross-source identity and fact traversal.
- **time series:** Ordered observations such as odds, ratings, injuries, or performance metrics.
- **shadow experiment:** Candidate logic evaluated alongside production without affecting output.
- **golden fixture:** Frozen test case with provider payloads, expected transforms, and assertions.
- **idempotency key:** Caller-supplied token guaranteeing one logical effect for repeat commands.
- **correlation ID:** Identifier linking UI actions, API calls, jobs, model calls, and logs.
- **config snapshot:** Immutable resolved configuration stored with a run.
- **prompt snapshot:** Versioned rendered model instruction and input reference without secrets.
- **run budget:** Hard maximum external cost and optional token/provider quotas for one run.
- **pilot budget:** Small monthly cap used to enforce selective analysis.
- **worthwhile score:** Triage score estimating information value, coverage, uncertainty, market relevance, and cost.
- **no-bet conclusion:** A valid result stating evidence or edge is insufficient; retained even though no wagering occurs.

## 4. Product Scope and User Journeys

### 4.1 Three-day scan journey

1. User opens Dashboard.
2. Client displays the current Europe/Istanbul date and three explicit date chips.
3. User presses `Üç Günü Tara`.
4. Client sends one idempotent scan command with timezone and UI config version.
5. Server computes local day boundaries using the injected clock.
6. Fixture adapters fetch supported competitions for all three dates.
7. Normalizer resolves teams, competitions, venues, kickoff changes, and duplicates.
8. Cheap enrichment estimates coverage, data freshness, model cost, market availability, and match relevance.
9. Triage model ranks candidates and provides factor-level explanations.
10. UI streams stage progress and progressively renders ranked fixtures.
11. No deep analysis starts automatically unless the user has explicitly enabled an allowlisted auto-analysis policy.
12. User selects a fixture and starts deep analysis.

### 4.2 Manual match search journey

1. User types at least two normalized characters into global match search.
2. Client debounces for 250 ms and cancels stale requests.
3. Server searches local canonical fixtures first.
4. If local coverage is insufficient, server queries configured fixture providers within quota.
5. Results group by date and competition and display Istanbul kickoff time.
6. Exact vendor IDs remain hidden from the user interface.
7. Ambiguous team names show country and competition context.
8. User selects exactly one canonical fixture.
9. A compact preflight panel displays provider coverage, estimated time, and estimated maximum cost.
10. User presses `Analizi Başlat`.
11. Server creates or reuses an idempotent analysis run.

### 4.3 Analysis inspection journey

1. Run page shows stage DAG, current stage, elapsed time, estimated remaining range, and spend.
2. Completed stages can be opened without blocking current work.
3. Evidence drawer shows source, captured timestamp, effective timestamp, freshness, and claim links.
4. Contradiction drawer groups material disagreements and their resolution state.
5. Quant tab shows probabilities, intervals, calibration status, and feature availability.
6. Committee tab shows the four prediction-forbidden Sonnet syntheses and unresolved disagreement, not private reasoning.
7. Final tab remains clearly marked `UNLOCKED` until the immutable lock succeeds.
8. After lock, UI displays hash, cutoff, lock time, model/config versions, and export button.

### 4.4 Post-match journey

1. Result provider detects final status or the user requests refresh.
2. Server ingests official result and event statistics as post-match facts.
3. Autopsy waits for data completeness or declares a degraded autopsy.
4. Variance analysis separates forecast error, scenario miss, data miss, execution variance, and irreducible luck.
5. Lesson extractor proposes bounded lessons.
6. Lesson validator rejects hindsight, leakage, and overgeneralization.
7. Accepted lessons become case memory and can influence future retrieval only within scope.

## 5. Exact Technology Stack

| Layer | Required choice | Reason | Change policy |
| --- | --- | --- | --- |
| Monorepo | pnpm workspaces + Turborepo | Shared contracts and coordinated builds | ADR required |
| Frontend | Next.js App Router + TypeScript | Compact production UI and typed server/client boundaries | ADR required |
| UI | Tailwind CSS + shadcn/ui primitives + Radix | Polished accessible compact components | Minor substitutions allowed |
| Client data | TanStack Query | Caching, cancellation, polling, mutations | ADR required |
| Forms | React Hook Form + Zod | Typed validation and compact forms | Equivalent allowed by ADR |
| Backend API | Python 3.13 + FastAPI | Pydantic contracts and data/model ecosystem | ADR required |
| Validation | Pydantic v2 | Versioned structured contracts | Required |
| Workflow | Temporal Python SDK | Durable long-running DAGs, retries, cancellation | ADR required |
| Primary database | PostgreSQL 17 | Relational, bitemporal, JSONB, strong constraints | Required |
| Vector | pgvector initially | Small-pilot simplicity and transactional provenance | May split after measured need |
| Time-series | Native partitioned Postgres initially; TimescaleDB optional | Avoid premature operational complexity | ADR after benchmark |
| Graph | Postgres adjacency/edge tables initially | Identity graph with transactional integrity | Neo4j only after graph workload proof |
| Cache/locks | Redis 7 | Rate limits, short cache, distributed locks | ADR required |
| Object storage | S3-compatible MinIO locally | Immutable source snapshots and exports | Provider-neutral |
| Dataframes | Polars | Fast deterministic transforms | Pandas only at library boundary |
| Quant | NumPy + SciPy + scikit-learn + statsmodels | Transparent baselines and calibration | Additive |
| Bayesian | PyMC optional after baseline | Uncertainty-rich hierarchical models | Phase-gated |
| Migrations | Alembic | Reviewable SQL lifecycle | Required |
| Python quality | Ruff + mypy + pytest + Hypothesis | Static and property checks | Required |
| TypeScript quality | Biome + TypeScript strict + Vitest | Fast consistent checks | Required |
| Browser tests | Playwright | End-to-end and visual behavior | Required |
| Observability | OpenTelemetry + Prometheus + Grafana + Loki locally | Correlated traces, metrics, logs | Provider-neutral |
| Secrets | dotenv only locally; secret manager in hosted environments | No secrets in repo | Required |
| Containers | Docker Compose for the entire local system | Mac requires only Docker Desktop; application and toolchains stay isolated | Required |

### 5.1 Stack constraints

- No LangChain dependency in the core domain; provider SDKs and small explicit adapters are preferred.
- No ORM model may double as an API contract.
- SQLAlchemy 2.x typed models MAY be used for persistence, but migrations remain explicit.
- Temporal workflow code MUST remain deterministic; external calls occur in activities.
- No local-development instruction may require host Node.js, pnpm, Python, pip, PostgreSQL, Redis, Temporal, MinIO, or observability binaries.
- All builds, migrations, seeds, code generation, linting, typing, tests, and development servers MUST execute through Docker Compose services.
- Frontend server actions MUST NOT bypass the public application service authorization and idempotency rules.
- All packages pin major and minor versions through the lockfile and automated dependency review.

## 6. Repository Structure

```text
miron-baba-ai/
├── apps/
│   ├── web/                         # Next.js application
│   │   ├── app/                     # Routes and layouts
│   │   ├── components/              # Product components
│   │   ├── features/                # Feature modules
│   │   ├── lib/                     # API client, date, formatting
│   │   ├── styles/                  # Design tokens and globals
│   │   ├── tests/                   # UI integration tests
│   │   └── Dockerfile               # Development, test, and runtime targets
│   └── api/                         # FastAPI application
│       ├── app/api/                 # HTTP route modules
│       ├── app/application/         # Commands, queries, services
│       ├── app/domain/              # Pure domain models and policies
│       ├── app/infrastructure/      # Providers and persistence
│       ├── app/workflows/           # Temporal workflows
│       ├── app/activities/          # External and compute activities
│       ├── tests/                   # API and domain tests
│       └── Dockerfile               # Shared API, worker, migration, and toolbox image
├── packages/
│   ├── contracts/                   # Generated JSON Schema and TS types
│   ├── prompts/                     # Versioned prompt templates
│   ├── model-registry/              # Model and pricing config
│   ├── provider-fixtures/           # Sanitized golden payloads
│   ├── sport-football/              # Football plugin and features
│   ├── sport-basketball/            # Future plugin skeleton
│   ├── sport-volleyball/            # Future plugin skeleton
│   ├── design-system/               # Shared UI primitives
│   └── observability/               # Semantic conventions
├── db/
│   ├── migrations/                  # Alembic migrations
│   ├── seeds/                       # Deterministic sample data
│   ├── sql/                         # Views and administrative queries
│   └── policies/                    # Retention and access policies
├── config/
│   ├── models.yaml                  # Model routes and verified prices
│   ├── providers.yaml               # Provider capabilities and limits
│   ├── competitions.yaml            # Allowlisted competition coverage
│   ├── freshness.yaml               # Source-specific TTLs
│   ├── budgets.yaml                 # Pilot and run budgets
│   └── experiments.yaml             # Shadow experiment assignments
├── docs/
│   ├── adr/                         # Architecture decision records
│   ├── runbooks/                    # Operations and failures
│   ├── data-dictionary/             # Entity and feature definitions
│   └── evaluations/                 # Model and prompt eval reports
├── infra/
│   ├── compose/                     # Local Docker configuration
│   ├── otel/                        # Collector configuration
│   └── dashboards/                  # Grafana dashboards
├── scripts/                         # Narrow developer commands
├── tests/
│   ├── e2e/                         # Playwright flows
│   ├── contract/                    # Provider and API contracts
│   ├── golden/                      # Golden run assertions
│   ├── backtest/                    # Leakage and calibration checks
│   └── load/                        # Bounded performance tests
├── .env.example
├── compose.yaml                     # Entire local runtime, not only dependencies
├── compose.dev.yaml                 # Bind mounts and development commands
├── compose.test.yaml                # Isolated deterministic test topology
├── .dockerignore
├── Makefile
├── pnpm-workspace.yaml
├── pyproject.toml
├── turbo.json
└── README.md
```

### 6.1 Module dependency rule

`domain <- application <- api/workflows <- infrastructure` is the only allowed inward dependency direction.
Provider adapters implement domain-facing ports; domain code never imports a provider SDK.
Prompts consume serialized contracts and evidence packets; prompts never query the database directly.

## 7. High-Level Architecture

```mermaid
flowchart LR
  UI[Compact Next.js UI] --> API[FastAPI Commands and Queries]
  API --> DB[(PostgreSQL + pgvector)]
  API --> T[Temporal]
  T --> A[Activities]
  A --> FP[Fixture Providers]
  A --> OP[Allowed Odds Providers]
  A --> WP[Research/Search Providers]
  A --> LLM[Model Gateway]
  A --> OBJ[(S3/MinIO Snapshots)]
  A --> DB
  A --> REDIS[(Redis)]
  API --> SSE[SSE Progress]
  SSE --> UI
```

### 7.1 Bounded contexts

- **Discovery:** Three-day fixture ingestion, search, identity resolution, and ranking.
- **Evidence:** Source capture, claims, provenance, freshness, contradictions, and RAG.
- **Analysis:** Specialist agents, quant models, committee, critics, scenarios, and synthesis.
- **Markets:** Allowed odds acquisition, normalization, margin removal, movement, and comparison.
- **Forecast:** Final probability contract, lock, export, and immutable audit.
- **Learning:** Post-match result, autopsy, variance, lessons, case memory, and experiments.
- **Platform:** Models, providers, budgets, jobs, observability, security, and configuration.

## 8. Orchestration DAG and State Machine

| ID | State | Depends on | Exit meaning |
| --- | --- | --- | --- |
| S00 | preflight | none | Validate fixture, cutoff, config, provider capability, and budget. |
| S01 | current_research | S00 | Acquire current permitted web and provider evidence. |
| S02 | source_verification | S01 | Verify source identity, timestamps, duplication, and trust. |
| S03 | claim_normalization | S02 | Normalize factual claims and units. |
| S04 | contradiction_freshness | S03 | Resolve or expose contradictions and staleness. |
| S05 | statistics | S04 | Build statistical profile and availability report. |
| S06 | player_squad | S04 | Assess player availability, role, and squad depth. |
| S07 | tactical | S04 | Assess tactical structures and matchup mechanisms. |
| S08 | form | S04 | Assess opponent-adjusted form and trend uncertainty. |
| S09 | fatigue | S04 | Assess rest, travel, congestion, and rotation. |
| S10 | goalkeeper | S04 | Assess goalkeeper availability and shot-stopping uncertainty. |
| S11 | set_piece | S04 | Assess set-piece creation, prevention, and personnel. |
| S12 | environment | S04 | Assess venue, weather, surface, altitude, and officiating. |
| S13 | odds_market_isolated | S04 | Normalize allowed market snapshots and movement without seeing news explanations. |
| S14 | market_movement_explainer | S01, S13 | Search for cutoff-safe public events aligned with movement and allow UNEXPLAINED. |
| S15 | quant_models | S05, S06, S08, S09, S10, S11, S12 | Generate independent calibrated model distributions. |
| S16 | historical_similarity | S03, S15 | Retrieve cutoff-safe structurally comparable cases. |
| S17 | specialist_critics | S05, S06, S07, S08, S09, S10, S11, S12, S13, S14, S15, S16 | Independently attack each specialist conclusion. |
| S18 | sonnet_evidence_audit | S17 | Audit evidence quality without producing a match prediction. |
| S19 | sonnet_tactical_synthesis | S17 | Synthesize tactical report and critic without producing a match prediction. |
| S20 | sonnet_player_squad_synthesis | S17 | Synthesize player, squad, fatigue, and goalkeeper evidence without predicting. |
| S21 | sonnet_quant_market_interpretation | S13, S14, S15, S17 | Interpret quant and market agreement or disagreement without predicting. |
| S22 | home_win_steelman | S18, S19, S20, S21 | Construct the strongest realistic home-win case without final probabilities. |
| S23 | draw_steelman | S18, S19, S20, S21 | Construct the strongest realistic draw case without final probabilities. |
| S24 | away_win_steelman | S18, S19, S20, S21 | Construct the strongest realistic away-win case without final probabilities. |
| S25 | scenario_red_team | S22, S23, S24 | Attack all three steelmanned outcome cases. |
| S26 | scenario_engine | S25 | Build mutually exclusive match-flow branches and triggers. |
| S27 | chief_analyst | S18, S19, S20, S21, S25, S26 | Allow the first LLM-authored final outcome probability vector. |
| S28 | final_critic | S27 | Critique but never directly change the Chief forecast. |
| S29 | chief_revision | S28 | Let Chief perform at most one bounded revision. |
| S30 | prediction_lock | S28, S29 | Create immutable signed pre-match forecast artifact. |
| S31 | live_market_namespace | S30 | Optionally collect allowed live odds separately from pre-match evidence. |
| S32 | post_match_ingestion | S30 | Wait for and ingest official final facts. |
| S33 | autopsy | S32 | Compare locked theses and process with the realized match. |
| S34 | variance_analysis | S33 | Attribute result divergence without automatic luck excuses. |
| S35 | thesis_agent_source_scoring | S34 | Score thesis, agent, and source reliability by scope. |
| S36 | lesson_extraction | S35 | Propose scoped reusable lessons. |
| S37 | lesson_validation | S36 | Reject leakage, overfit, and overgeneralization. |
| S38 | case_memory | S37 | Persist a validated case for future cutoff-safe retrieval. |

```mermaid
stateDiagram-v2
  [*] --> CREATED
  CREATED --> PREFLIGHT
  PREFLIGHT --> RUNNING
  RUNNING --> PAUSED_BUDGET
  PAUSED_BUDGET --> RUNNING
  RUNNING --> REVISION_REQUIRED
  REVISION_REQUIRED --> RUNNING
  RUNNING --> LOCKING
  LOCKING --> LOCKED
  RUNNING --> DEGRADED
  DEGRADED --> LOCKING
  RUNNING --> FAILED
  RUNNING --> CANCEL_REQUESTED
  CANCEL_REQUESTED --> CANCELLED
  LOCKED --> WAITING_RESULT
  WAITING_RESULT --> POST_MATCH
  POST_MATCH --> COMPLETE
  FAILED --> [*]
  CANCELLED --> [*]
  COMPLETE --> [*]
```

### 8.1 State transition requirements

#### CREATED

- Entry MUST be recorded in `run_state_transitions` before the UI reports CREATED.
- The transition MUST include `from_state`, `to_state`, `reason_code`, `actor_type`, `actor_id`, `occurred_at`, and `correlation_id`.
- The transition handler MUST be idempotent.
- An invalid predecessor MUST return HTTP 409 and MUST NOT mutate the run.
- Metrics MUST increment `miron_baba_ai_run_state_transition_total` with bounded labels.

#### PREFLIGHT

- Entry MUST be recorded in `run_state_transitions` before the UI reports PREFLIGHT.
- The transition MUST include `from_state`, `to_state`, `reason_code`, `actor_type`, `actor_id`, `occurred_at`, and `correlation_id`.
- The transition handler MUST be idempotent.
- An invalid predecessor MUST return HTTP 409 and MUST NOT mutate the run.
- Metrics MUST increment `miron_baba_ai_run_state_transition_total` with bounded labels.

#### RUNNING

- Entry MUST be recorded in `run_state_transitions` before the UI reports RUNNING.
- The transition MUST include `from_state`, `to_state`, `reason_code`, `actor_type`, `actor_id`, `occurred_at`, and `correlation_id`.
- The transition handler MUST be idempotent.
- An invalid predecessor MUST return HTTP 409 and MUST NOT mutate the run.
- Metrics MUST increment `miron_baba_ai_run_state_transition_total` with bounded labels.

#### PAUSED_BUDGET

- Entry MUST be recorded in `run_state_transitions` before the UI reports PAUSED_BUDGET.
- The transition MUST include `from_state`, `to_state`, `reason_code`, `actor_type`, `actor_id`, `occurred_at`, and `correlation_id`.
- The transition handler MUST be idempotent.
- An invalid predecessor MUST return HTTP 409 and MUST NOT mutate the run.
- Metrics MUST increment `miron_baba_ai_run_state_transition_total` with bounded labels.

#### REVISION_REQUIRED

- Entry MUST be recorded in `run_state_transitions` before the UI reports REVISION_REQUIRED.
- The transition MUST include `from_state`, `to_state`, `reason_code`, `actor_type`, `actor_id`, `occurred_at`, and `correlation_id`.
- The transition handler MUST be idempotent.
- An invalid predecessor MUST return HTTP 409 and MUST NOT mutate the run.
- Metrics MUST increment `miron_baba_ai_run_state_transition_total` with bounded labels.

#### LOCKING

- Entry MUST be recorded in `run_state_transitions` before the UI reports LOCKING.
- The transition MUST include `from_state`, `to_state`, `reason_code`, `actor_type`, `actor_id`, `occurred_at`, and `correlation_id`.
- The transition handler MUST be idempotent.
- An invalid predecessor MUST return HTTP 409 and MUST NOT mutate the run.
- Metrics MUST increment `miron_baba_ai_run_state_transition_total` with bounded labels.

#### LOCKED

- Entry MUST be recorded in `run_state_transitions` before the UI reports LOCKED.
- The transition MUST include `from_state`, `to_state`, `reason_code`, `actor_type`, `actor_id`, `occurred_at`, and `correlation_id`.
- The transition handler MUST be idempotent.
- An invalid predecessor MUST return HTTP 409 and MUST NOT mutate the run.
- Metrics MUST increment `miron_baba_ai_run_state_transition_total` with bounded labels.

#### DEGRADED

- Entry MUST be recorded in `run_state_transitions` before the UI reports DEGRADED.
- The transition MUST include `from_state`, `to_state`, `reason_code`, `actor_type`, `actor_id`, `occurred_at`, and `correlation_id`.
- The transition handler MUST be idempotent.
- An invalid predecessor MUST return HTTP 409 and MUST NOT mutate the run.
- Metrics MUST increment `miron_baba_ai_run_state_transition_total` with bounded labels.

#### FAILED

- Entry MUST be recorded in `run_state_transitions` before the UI reports FAILED.
- The transition MUST include `from_state`, `to_state`, `reason_code`, `actor_type`, `actor_id`, `occurred_at`, and `correlation_id`.
- The transition handler MUST be idempotent.
- An invalid predecessor MUST return HTTP 409 and MUST NOT mutate the run.
- Metrics MUST increment `miron_baba_ai_run_state_transition_total` with bounded labels.

#### CANCEL_REQUESTED

- Entry MUST be recorded in `run_state_transitions` before the UI reports CANCEL_REQUESTED.
- The transition MUST include `from_state`, `to_state`, `reason_code`, `actor_type`, `actor_id`, `occurred_at`, and `correlation_id`.
- The transition handler MUST be idempotent.
- An invalid predecessor MUST return HTTP 409 and MUST NOT mutate the run.
- Metrics MUST increment `miron_baba_ai_run_state_transition_total` with bounded labels.

#### CANCELLED

- Entry MUST be recorded in `run_state_transitions` before the UI reports CANCELLED.
- The transition MUST include `from_state`, `to_state`, `reason_code`, `actor_type`, `actor_id`, `occurred_at`, and `correlation_id`.
- The transition handler MUST be idempotent.
- An invalid predecessor MUST return HTTP 409 and MUST NOT mutate the run.
- Metrics MUST increment `miron_baba_ai_run_state_transition_total` with bounded labels.

#### WAITING_RESULT

- Entry MUST be recorded in `run_state_transitions` before the UI reports WAITING_RESULT.
- The transition MUST include `from_state`, `to_state`, `reason_code`, `actor_type`, `actor_id`, `occurred_at`, and `correlation_id`.
- The transition handler MUST be idempotent.
- An invalid predecessor MUST return HTTP 409 and MUST NOT mutate the run.
- Metrics MUST increment `miron_baba_ai_run_state_transition_total` with bounded labels.

#### POST_MATCH

- Entry MUST be recorded in `run_state_transitions` before the UI reports POST_MATCH.
- The transition MUST include `from_state`, `to_state`, `reason_code`, `actor_type`, `actor_id`, `occurred_at`, and `correlation_id`.
- The transition handler MUST be idempotent.
- An invalid predecessor MUST return HTTP 409 and MUST NOT mutate the run.
- Metrics MUST increment `miron_baba_ai_run_state_transition_total` with bounded labels.

#### COMPLETE

- Entry MUST be recorded in `run_state_transitions` before the UI reports COMPLETE.
- The transition MUST include `from_state`, `to_state`, `reason_code`, `actor_type`, `actor_id`, `occurred_at`, and `correlation_id`.
- The transition handler MUST be idempotent.
- An invalid predecessor MUST return HTTP 409 and MUST NOT mutate the run.
- Metrics MUST increment `miron_baba_ai_run_state_transition_total` with bounded labels.

## 9. Agent-by-Agent Prescriptive Specifications

Every agent below is a logical role. Multiple roles MAY use the same provider model, but their prompts, tools, schemas, budgets, and retrieval policies remain separate.
An “agent” MUST NOT be implemented as an unconstrained autonomous loop.

### 9.1 A00 — Preflight Controller

- Orchestration stage: `S00`.
- Goal: Prove the run can start safely and reproducibly.
- Failure code: `BLOCKED_PREFLIGHT`.
- Default execution mode: one bounded structured-output call or one deterministic compute activity.
- Maximum self-repair attempts: one schema-repair call; then fail or degrade according to policy.

#### Inputs

- A00-IN-01: canonical fixture.
- A00-IN-02: requested cutoff.
- A00-IN-03: resolved config.
- A00-IN-04: remaining monthly budget.
- Input envelope MUST contain `run_id`, `fixture_id`, `cutoff_at`, `config_snapshot_id`, and `correlation_id`.
- Each input artifact MUST be referenced by immutable artifact ID and SHA-256 hash.

#### Outputs

- A00-OUT-01: preflight decision.
- A00-OUT-02: budget reservation.
- A00-OUT-03: config snapshot.
- Output MUST validate against the agent-specific Pydantic schema version recorded in the envelope.
- Output MUST contain `status`, `confidence`, `limitations`, `citations`, and `created_at`.
- Output MUST NOT contain unbounded free-form chain-of-thought.
- Explanations MUST be concise evidence summaries suitable for audit and display.

#### Allowed sources and tools

- Allowed: internal configuration.
- Allowed: provider capability registry.
- Deny by default: any source, index, or tool not named by this role or runtime policy.
- Secrets MUST be injected by the adapter and MUST NOT appear in the rendered prompt.

#### Retrieval policy

- Primary rule: No semantic retrieval; exact configuration and fixture queries only.
- Filter order: tenant/personal scope, sport, fixture/entity, knowledge time, effective time, source class, then semantic rank.
- Retrieved chunks MUST preserve source snapshot ID, byte/character span, observed time, and content hash.
- Context packing MUST prioritize materiality and source independence over raw similarity score.
- Retrieval MUST return an explicit empty result when constraints remove all candidates.
- The agent MUST NOT ask the model to “remember” facts that are absent from the packet.

#### Mandatory checks

- A00-CHK-01: verify fixture has two resolved teams.
- A00-CHK-02: verify kickoff is future relative to cutoff.
- A00-CHK-03: verify provider coverage is sufficient.
- A00-CHK-04: verify hard cost ceiling can be reserved.
- A00-CHK-90: verify every material statement has a source or is labeled inference.
- A00-CHK-91: verify no evidence has `observed_at > cutoff_at`.
- A00-CHK-92: verify confidence decreases when critical evidence is absent or contradictory.
- A00-CHK-93: verify all probabilities are finite decimals within [0, 1] when this role is authorized to emit probabilities.
- A00-CHK-94: verify the output is deterministic under the deterministic test adapter.

#### System instruction template

```text
You are Preflight Controller, logical role A00 in MİRON BABA AI.
Your only objective is: Prove the run can start safely and reproducibly.
Use only the supplied, cutoff-safe evidence packet and explicitly allowed tools.
Never invent a fact, source, timestamp, player status, statistic, price, or provider result.
Separate observed facts, derived metrics, inferences, and unknowns.
Treat conflicting evidence as a first-class output; do not average contradictions into false certainty.
Do not select a winner or emit final outcome probabilities unless this role's stated goal explicitly authorizes it.
Do not expose private chain-of-thought. Return concise conclusions, supporting citations, checks, and uncertainty.
Do not give guaranteed outcomes, financial advice, or wagering instructions.
If a critical input is unavailable, return the declared degraded or failure status: BLOCKED_PREFLIGHT.
Return only JSON conforming exactly to schema {{schema_version}}.
Run ID: {{run_id}}
Fixture ID: {{fixture_id}}
Cutoff: {{cutoff_at}}
Prompt version: {{prompt_version}}
```

#### User/task prompt template

```text
TASK
Evaluate the supplied artifacts for Preflight Controller.

INPUT MANIFEST
{{input_manifest_json}}

EVIDENCE PACKET
{{evidence_packet_json}}

POLICY
{{role_policy_json}}

REQUIRED OUTPUT
{{output_schema_json}}

Before returning, check identifiers, cutoff compliance, citations, units, uncertainty, and schema validity.
```

#### Acceptance tests

- A00-T-01: a fixture with a controlled fixture has two resolved teams defect is rejected or degraded with the expected code.
- A00-T-02: a fixture with a controlled kickoff is future relative to cutoff defect is rejected or degraded with the expected code.
- A00-T-03: a fixture with a controlled provider coverage is sufficient defect is rejected or degraded with the expected code.
- A00-T-04: a fixture with a controlled hard cost ceiling can be reserved defect is rejected or degraded with the expected code.
- A00-T-90: an evidence item one second after cutoff is excluded and logged.
- A00-T-91: an unknown field in strict output causes validation failure.
- A00-T-92: a provider timeout produces a bounded retry and no duplicate artifact.
- A00-T-93: a model refusal is classified and never accepted as a valid report.
- A00-T-94: snapshot hashes remain identical on idempotent replay.

### 9.2 A01 — Current Research Scout

- Orchestration stage: `S01`.
- Goal: Collect current, relevant, permitted pre-match evidence without drawing conclusions.
- Failure code: `DEGRADED_RESEARCH`.
- Default execution mode: one bounded structured-output call or one deterministic compute activity.
- Maximum self-repair attempts: one schema-repair call; then fail or degrade according to policy.

#### Inputs

- A01-IN-01: fixture identity packet.
- A01-IN-02: research query plan.
- A01-IN-03: cutoff.
- Input envelope MUST contain `run_id`, `fixture_id`, `cutoff_at`, `config_snapshot_id`, and `correlation_id`.
- Each input artifact MUST be referenced by immutable artifact ID and SHA-256 hash.

#### Outputs

- A01-OUT-01: source candidates.
- A01-OUT-02: captured source snapshots.
- A01-OUT-03: query audit.
- Output MUST validate against the agent-specific Pydantic schema version recorded in the envelope.
- Output MUST contain `status`, `confidence`, `limitations`, `citations`, and `created_at`.
- Output MUST NOT contain unbounded free-form chain-of-thought.
- Explanations MUST be concise evidence summaries suitable for audit and display.

#### Allowed sources and tools

- Allowed: grounded web research.
- Allowed: official club and competition sources.
- Allowed: allowed news/data providers.
- Deny by default: any source, index, or tool not named by this role or runtime policy.
- Secrets MUST be injected by the adapter and MUST NOT appear in the rendered prompt.

#### Retrieval policy

- Primary rule: Search first; no case memory; enforce domain and cutoff policy.
- Filter order: tenant/personal scope, sport, fixture/entity, knowledge time, effective time, source class, then semantic rank.
- Retrieved chunks MUST preserve source snapshot ID, byte/character span, observed time, and content hash.
- Context packing MUST prioritize materiality and source independence over raw similarity score.
- Retrieval MUST return an explicit empty result when constraints remove all candidates.
- The agent MUST NOT ask the model to “remember” facts that are absent from the packet.

#### Mandatory checks

- A01-CHK-01: verify query coverage.
- A01-CHK-02: verify source capture time.
- A01-CHK-03: verify robots/license policy.
- A01-CHK-04: verify duplicate content hash.
- A01-CHK-90: verify every material statement has a source or is labeled inference.
- A01-CHK-91: verify no evidence has `observed_at > cutoff_at`.
- A01-CHK-92: verify confidence decreases when critical evidence is absent or contradictory.
- A01-CHK-93: verify all probabilities are finite decimals within [0, 1] when this role is authorized to emit probabilities.
- A01-CHK-94: verify the output is deterministic under the deterministic test adapter.

#### System instruction template

```text
You are Current Research Scout, logical role A01 in MİRON BABA AI.
Your only objective is: Collect current, relevant, permitted pre-match evidence without drawing conclusions.
Use only the supplied, cutoff-safe evidence packet and explicitly allowed tools.
Never invent a fact, source, timestamp, player status, statistic, price, or provider result.
Separate observed facts, derived metrics, inferences, and unknowns.
Treat conflicting evidence as a first-class output; do not average contradictions into false certainty.
Do not select a winner or emit final outcome probabilities unless this role's stated goal explicitly authorizes it.
Do not expose private chain-of-thought. Return concise conclusions, supporting citations, checks, and uncertainty.
Do not give guaranteed outcomes, financial advice, or wagering instructions.
If a critical input is unavailable, return the declared degraded or failure status: DEGRADED_RESEARCH.
Return only JSON conforming exactly to schema {{schema_version}}.
Run ID: {{run_id}}
Fixture ID: {{fixture_id}}
Cutoff: {{cutoff_at}}
Prompt version: {{prompt_version}}
```

#### User/task prompt template

```text
TASK
Evaluate the supplied artifacts for Current Research Scout.

INPUT MANIFEST
{{input_manifest_json}}

EVIDENCE PACKET
{{evidence_packet_json}}

POLICY
{{role_policy_json}}

REQUIRED OUTPUT
{{output_schema_json}}

Before returning, check identifiers, cutoff compliance, citations, units, uncertainty, and schema validity.
```

#### Acceptance tests

- A01-T-01: a fixture with a controlled query coverage defect is rejected or degraded with the expected code.
- A01-T-02: a fixture with a controlled source capture time defect is rejected or degraded with the expected code.
- A01-T-03: a fixture with a controlled robots/license policy defect is rejected or degraded with the expected code.
- A01-T-04: a fixture with a controlled duplicate content hash defect is rejected or degraded with the expected code.
- A01-T-90: an evidence item one second after cutoff is excluded and logged.
- A01-T-91: an unknown field in strict output causes validation failure.
- A01-T-92: a provider timeout produces a bounded retry and no duplicate artifact.
- A01-T-93: a model refusal is classified and never accepted as a valid report.
- A01-T-94: snapshot hashes remain identical on idempotent replay.

### 9.3 A02 — Source Verification Agent

- Orchestration stage: `S02`.
- Goal: Assess identity, authority, timestamp, independence, and integrity of every source.
- Failure code: `DEGRADED_PROVENANCE`.
- Default execution mode: one bounded structured-output call or one deterministic compute activity.
- Maximum self-repair attempts: one schema-repair call; then fail or degrade according to policy.

#### Inputs

- A02-IN-01: source candidates.
- A02-IN-02: provider metadata.
- Input envelope MUST contain `run_id`, `fixture_id`, `cutoff_at`, `config_snapshot_id`, and `correlation_id`.
- Each input artifact MUST be referenced by immutable artifact ID and SHA-256 hash.

#### Outputs

- A02-OUT-01: verified sources.
- A02-OUT-02: rejected sources.
- A02-OUT-03: trust scores.
- Output MUST validate against the agent-specific Pydantic schema version recorded in the envelope.
- Output MUST contain `status`, `confidence`, `limitations`, `citations`, and `created_at`.
- Output MUST NOT contain unbounded free-form chain-of-thought.
- Explanations MUST be concise evidence summaries suitable for audit and display.

#### Allowed sources and tools

- Allowed: source registry.
- Allowed: domain policy.
- Allowed: snapshot metadata.
- Deny by default: any source, index, or tool not named by this role or runtime policy.
- Secrets MUST be injected by the adapter and MUST NOT appear in the rendered prompt.

#### Retrieval policy

- Primary rule: Exact domain and prior reliability lookup only.
- Filter order: tenant/personal scope, sport, fixture/entity, knowledge time, effective time, source class, then semantic rank.
- Retrieved chunks MUST preserve source snapshot ID, byte/character span, observed time, and content hash.
- Context packing MUST prioritize materiality and source independence over raw similarity score.
- Retrieval MUST return an explicit empty result when constraints remove all candidates.
- The agent MUST NOT ask the model to “remember” facts that are absent from the packet.

#### Mandatory checks

- A02-CHK-01: verify canonical URL.
- A02-CHK-02: verify publication time.
- A02-CHK-03: verify observation time.
- A02-CHK-04: verify author/issuer.
- A02-CHK-05: verify cross-source independence.
- A02-CHK-90: verify every material statement has a source or is labeled inference.
- A02-CHK-91: verify no evidence has `observed_at > cutoff_at`.
- A02-CHK-92: verify confidence decreases when critical evidence is absent or contradictory.
- A02-CHK-93: verify all probabilities are finite decimals within [0, 1] when this role is authorized to emit probabilities.
- A02-CHK-94: verify the output is deterministic under the deterministic test adapter.

#### System instruction template

```text
You are Source Verification Agent, logical role A02 in MİRON BABA AI.
Your only objective is: Assess identity, authority, timestamp, independence, and integrity of every source.
Use only the supplied, cutoff-safe evidence packet and explicitly allowed tools.
Never invent a fact, source, timestamp, player status, statistic, price, or provider result.
Separate observed facts, derived metrics, inferences, and unknowns.
Treat conflicting evidence as a first-class output; do not average contradictions into false certainty.
Do not select a winner or emit final outcome probabilities unless this role's stated goal explicitly authorizes it.
Do not expose private chain-of-thought. Return concise conclusions, supporting citations, checks, and uncertainty.
Do not give guaranteed outcomes, financial advice, or wagering instructions.
If a critical input is unavailable, return the declared degraded or failure status: DEGRADED_PROVENANCE.
Return only JSON conforming exactly to schema {{schema_version}}.
Run ID: {{run_id}}
Fixture ID: {{fixture_id}}
Cutoff: {{cutoff_at}}
Prompt version: {{prompt_version}}
```

#### User/task prompt template

```text
TASK
Evaluate the supplied artifacts for Source Verification Agent.

INPUT MANIFEST
{{input_manifest_json}}

EVIDENCE PACKET
{{evidence_packet_json}}

POLICY
{{role_policy_json}}

REQUIRED OUTPUT
{{output_schema_json}}

Before returning, check identifiers, cutoff compliance, citations, units, uncertainty, and schema validity.
```

#### Acceptance tests

- A02-T-01: a fixture with a controlled canonical URL defect is rejected or degraded with the expected code.
- A02-T-02: a fixture with a controlled publication time defect is rejected or degraded with the expected code.
- A02-T-03: a fixture with a controlled observation time defect is rejected or degraded with the expected code.
- A02-T-04: a fixture with a controlled author/issuer defect is rejected or degraded with the expected code.
- A02-T-05: a fixture with a controlled cross-source independence defect is rejected or degraded with the expected code.
- A02-T-90: an evidence item one second after cutoff is excluded and logged.
- A02-T-91: an unknown field in strict output causes validation failure.
- A02-T-92: a provider timeout produces a bounded retry and no duplicate artifact.
- A02-T-93: a model refusal is classified and never accepted as a valid report.
- A02-T-94: snapshot hashes remain identical on idempotent replay.

### 9.4 A03 — Claim Normalizer

- Orchestration stage: `S03`.
- Goal: Convert source content into atomic canonical claims without adding facts.
- Failure code: `QUARANTINED_CLAIMS`.
- Default execution mode: one bounded structured-output call or one deterministic compute activity.
- Maximum self-repair attempts: one schema-repair call; then fail or degrade according to policy.

#### Inputs

- A03-IN-01: verified sources.
- A03-IN-02: entity dictionary.
- A03-IN-03: unit dictionary.
- Input envelope MUST contain `run_id`, `fixture_id`, `cutoff_at`, `config_snapshot_id`, and `correlation_id`.
- Each input artifact MUST be referenced by immutable artifact ID and SHA-256 hash.

#### Outputs

- A03-OUT-01: normalized claims.
- A03-OUT-02: entity links.
- A03-OUT-03: source spans.
- Output MUST validate against the agent-specific Pydantic schema version recorded in the envelope.
- Output MUST contain `status`, `confidence`, `limitations`, `citations`, and `created_at`.
- Output MUST NOT contain unbounded free-form chain-of-thought.
- Explanations MUST be concise evidence summaries suitable for audit and display.

#### Allowed sources and tools

- Allowed: verified run sources.
- Deny by default: any source, index, or tool not named by this role or runtime policy.
- Secrets MUST be injected by the adapter and MUST NOT appear in the rendered prompt.

#### Retrieval policy

- Primary rule: Hybrid exact/vector within this run only; cutoff filter mandatory.
- Filter order: tenant/personal scope, sport, fixture/entity, knowledge time, effective time, source class, then semantic rank.
- Retrieved chunks MUST preserve source snapshot ID, byte/character span, observed time, and content hash.
- Context packing MUST prioritize materiality and source independence over raw similarity score.
- Retrieval MUST return an explicit empty result when constraints remove all candidates.
- The agent MUST NOT ask the model to “remember” facts that are absent from the packet.

#### Mandatory checks

- A03-CHK-01: verify atomicity.
- A03-CHK-02: verify subject identity.
- A03-CHK-03: verify predicate vocabulary.
- A03-CHK-04: verify unit conversion.
- A03-CHK-05: verify scope and time.
- A03-CHK-90: verify every material statement has a source or is labeled inference.
- A03-CHK-91: verify no evidence has `observed_at > cutoff_at`.
- A03-CHK-92: verify confidence decreases when critical evidence is absent or contradictory.
- A03-CHK-93: verify all probabilities are finite decimals within [0, 1] when this role is authorized to emit probabilities.
- A03-CHK-94: verify the output is deterministic under the deterministic test adapter.

#### System instruction template

```text
You are Claim Normalizer, logical role A03 in MİRON BABA AI.
Your only objective is: Convert source content into atomic canonical claims without adding facts.
Use only the supplied, cutoff-safe evidence packet and explicitly allowed tools.
Never invent a fact, source, timestamp, player status, statistic, price, or provider result.
Separate observed facts, derived metrics, inferences, and unknowns.
Treat conflicting evidence as a first-class output; do not average contradictions into false certainty.
Do not select a winner or emit final outcome probabilities unless this role's stated goal explicitly authorizes it.
Do not expose private chain-of-thought. Return concise conclusions, supporting citations, checks, and uncertainty.
Do not give guaranteed outcomes, financial advice, or wagering instructions.
If a critical input is unavailable, return the declared degraded or failure status: QUARANTINED_CLAIMS.
Return only JSON conforming exactly to schema {{schema_version}}.
Run ID: {{run_id}}
Fixture ID: {{fixture_id}}
Cutoff: {{cutoff_at}}
Prompt version: {{prompt_version}}
```

#### User/task prompt template

```text
TASK
Evaluate the supplied artifacts for Claim Normalizer.

INPUT MANIFEST
{{input_manifest_json}}

EVIDENCE PACKET
{{evidence_packet_json}}

POLICY
{{role_policy_json}}

REQUIRED OUTPUT
{{output_schema_json}}

Before returning, check identifiers, cutoff compliance, citations, units, uncertainty, and schema validity.
```

#### Acceptance tests

- A03-T-01: a fixture with a controlled atomicity defect is rejected or degraded with the expected code.
- A03-T-02: a fixture with a controlled subject identity defect is rejected or degraded with the expected code.
- A03-T-03: a fixture with a controlled predicate vocabulary defect is rejected or degraded with the expected code.
- A03-T-04: a fixture with a controlled unit conversion defect is rejected or degraded with the expected code.
- A03-T-05: a fixture with a controlled scope and time defect is rejected or degraded with the expected code.
- A03-T-90: an evidence item one second after cutoff is excluded and logged.
- A03-T-91: an unknown field in strict output causes validation failure.
- A03-T-92: a provider timeout produces a bounded retry and no duplicate artifact.
- A03-T-93: a model refusal is classified and never accepted as a valid report.
- A03-T-94: snapshot hashes remain identical on idempotent replay.

### 9.5 A04 — Contradiction and Freshness Judge

- Orchestration stage: `S04`.
- Goal: Detect conflicts, supersession, staleness, and unresolved ambiguity.
- Failure code: `UNRESOLVED_CONTRADICTION`.
- Default execution mode: one bounded structured-output call or one deterministic compute activity.
- Maximum self-repair attempts: one schema-repair call; then fail or degrade according to policy.

#### Inputs

- A04-IN-01: normalized claims.
- A04-IN-02: freshness policies.
- Input envelope MUST contain `run_id`, `fixture_id`, `cutoff_at`, `config_snapshot_id`, and `correlation_id`.
- Each input artifact MUST be referenced by immutable artifact ID and SHA-256 hash.

#### Outputs

- A04-OUT-01: claim status.
- A04-OUT-02: contradiction sets.
- A04-OUT-03: freshness verdicts.
- Output MUST validate against the agent-specific Pydantic schema version recorded in the envelope.
- Output MUST contain `status`, `confidence`, `limitations`, `citations`, and `created_at`.
- Output MUST NOT contain unbounded free-form chain-of-thought.
- Explanations MUST be concise evidence summaries suitable for audit and display.

#### Allowed sources and tools

- Allowed: run claims.
- Allowed: source reliability history.
- Deny by default: any source, index, or tool not named by this role or runtime policy.
- Secrets MUST be injected by the adapter and MUST NOT appear in the rendered prompt.

#### Retrieval policy

- Primary rule: Claim graph traversal plus exact time filters.
- Filter order: tenant/personal scope, sport, fixture/entity, knowledge time, effective time, source class, then semantic rank.
- Retrieved chunks MUST preserve source snapshot ID, byte/character span, observed time, and content hash.
- Context packing MUST prioritize materiality and source independence over raw similarity score.
- Retrieval MUST return an explicit empty result when constraints remove all candidates.
- The agent MUST NOT ask the model to “remember” facts that are absent from the packet.

#### Mandatory checks

- A04-CHK-01: verify same scope comparison.
- A04-CHK-02: verify newer official supersession.
- A04-CHK-03: verify independent corroboration.
- A04-CHK-04: verify materiality.
- A04-CHK-90: verify every material statement has a source or is labeled inference.
- A04-CHK-91: verify no evidence has `observed_at > cutoff_at`.
- A04-CHK-92: verify confidence decreases when critical evidence is absent or contradictory.
- A04-CHK-93: verify all probabilities are finite decimals within [0, 1] when this role is authorized to emit probabilities.
- A04-CHK-94: verify the output is deterministic under the deterministic test adapter.

#### System instruction template

```text
You are Contradiction and Freshness Judge, logical role A04 in MİRON BABA AI.
Your only objective is: Detect conflicts, supersession, staleness, and unresolved ambiguity.
Use only the supplied, cutoff-safe evidence packet and explicitly allowed tools.
Never invent a fact, source, timestamp, player status, statistic, price, or provider result.
Separate observed facts, derived metrics, inferences, and unknowns.
Treat conflicting evidence as a first-class output; do not average contradictions into false certainty.
Do not select a winner or emit final outcome probabilities unless this role's stated goal explicitly authorizes it.
Do not expose private chain-of-thought. Return concise conclusions, supporting citations, checks, and uncertainty.
Do not give guaranteed outcomes, financial advice, or wagering instructions.
If a critical input is unavailable, return the declared degraded or failure status: UNRESOLVED_CONTRADICTION.
Return only JSON conforming exactly to schema {{schema_version}}.
Run ID: {{run_id}}
Fixture ID: {{fixture_id}}
Cutoff: {{cutoff_at}}
Prompt version: {{prompt_version}}
```

#### User/task prompt template

```text
TASK
Evaluate the supplied artifacts for Contradiction and Freshness Judge.

INPUT MANIFEST
{{input_manifest_json}}

EVIDENCE PACKET
{{evidence_packet_json}}

POLICY
{{role_policy_json}}

REQUIRED OUTPUT
{{output_schema_json}}

Before returning, check identifiers, cutoff compliance, citations, units, uncertainty, and schema validity.
```

#### Acceptance tests

- A04-T-01: a fixture with a controlled same scope comparison defect is rejected or degraded with the expected code.
- A04-T-02: a fixture with a controlled newer official supersession defect is rejected or degraded with the expected code.
- A04-T-03: a fixture with a controlled independent corroboration defect is rejected or degraded with the expected code.
- A04-T-04: a fixture with a controlled materiality defect is rejected or degraded with the expected code.
- A04-T-90: an evidence item one second after cutoff is excluded and logged.
- A04-T-91: an unknown field in strict output causes validation failure.
- A04-T-92: a provider timeout produces a bounded retry and no duplicate artifact.
- A04-T-93: a model refusal is classified and never accepted as a valid report.
- A04-T-94: snapshot hashes remain identical on idempotent replay.

### 9.6 A05 — Statistical Analyst

- Orchestration stage: `S05`.
- Goal: Build transparent, opponent-adjusted statistical features with missingness.
- Failure code: `DEGRADED_STATS`.
- Default execution mode: one bounded structured-output call or one deterministic compute activity.
- Maximum self-repair attempts: one schema-repair call; then fail or degrade according to policy.

#### Inputs

- A05-IN-01: match history.
- A05-IN-02: event stats.
- A05-IN-03: competition baselines.
- Input envelope MUST contain `run_id`, `fixture_id`, `cutoff_at`, `config_snapshot_id`, and `correlation_id`.
- Each input artifact MUST be referenced by immutable artifact ID and SHA-256 hash.

#### Outputs

- A05-OUT-01: statistical feature set.
- A05-OUT-02: data quality report.
- A05-OUT-03: distribution summaries.
- Output MUST validate against the agent-specific Pydantic schema version recorded in the envelope.
- Output MUST contain `status`, `confidence`, `limitations`, `citations`, and `created_at`.
- Output MUST NOT contain unbounded free-form chain-of-thought.
- Explanations MUST be concise evidence summaries suitable for audit and display.

#### Allowed sources and tools

- Allowed: licensed statistics provider.
- Allowed: internal derived tables.
- Deny by default: any source, index, or tool not named by this role or runtime policy.
- Secrets MUST be injected by the adapter and MUST NOT appear in the rendered prompt.

#### Retrieval policy

- Primary rule: Structured SQL and time-series only; no web prose.
- Filter order: tenant/personal scope, sport, fixture/entity, knowledge time, effective time, source class, then semantic rank.
- Retrieved chunks MUST preserve source snapshot ID, byte/character span, observed time, and content hash.
- Context packing MUST prioritize materiality and source independence over raw similarity score.
- Retrieval MUST return an explicit empty result when constraints remove all candidates.
- The agent MUST NOT ask the model to “remember” facts that are absent from the packet.

#### Mandatory checks

- A05-CHK-01: verify sample size.
- A05-CHK-02: verify season boundary.
- A05-CHK-03: verify opponent strength.
- A05-CHK-04: verify home-away split.
- A05-CHK-05: verify leakage cutoff.
- A05-CHK-90: verify every material statement has a source or is labeled inference.
- A05-CHK-91: verify no evidence has `observed_at > cutoff_at`.
- A05-CHK-92: verify confidence decreases when critical evidence is absent or contradictory.
- A05-CHK-93: verify all probabilities are finite decimals within [0, 1] when this role is authorized to emit probabilities.
- A05-CHK-94: verify the output is deterministic under the deterministic test adapter.

#### System instruction template

```text
You are Statistical Analyst, logical role A05 in MİRON BABA AI.
Your only objective is: Build transparent, opponent-adjusted statistical features with missingness.
Use only the supplied, cutoff-safe evidence packet and explicitly allowed tools.
Never invent a fact, source, timestamp, player status, statistic, price, or provider result.
Separate observed facts, derived metrics, inferences, and unknowns.
Treat conflicting evidence as a first-class output; do not average contradictions into false certainty.
Do not select a winner or emit final outcome probabilities unless this role's stated goal explicitly authorizes it.
Do not expose private chain-of-thought. Return concise conclusions, supporting citations, checks, and uncertainty.
Do not give guaranteed outcomes, financial advice, or wagering instructions.
If a critical input is unavailable, return the declared degraded or failure status: DEGRADED_STATS.
Return only JSON conforming exactly to schema {{schema_version}}.
Run ID: {{run_id}}
Fixture ID: {{fixture_id}}
Cutoff: {{cutoff_at}}
Prompt version: {{prompt_version}}
```

#### User/task prompt template

```text
TASK
Evaluate the supplied artifacts for Statistical Analyst.

INPUT MANIFEST
{{input_manifest_json}}

EVIDENCE PACKET
{{evidence_packet_json}}

POLICY
{{role_policy_json}}

REQUIRED OUTPUT
{{output_schema_json}}

Before returning, check identifiers, cutoff compliance, citations, units, uncertainty, and schema validity.
```

#### Acceptance tests

- A05-T-01: a fixture with a controlled sample size defect is rejected or degraded with the expected code.
- A05-T-02: a fixture with a controlled season boundary defect is rejected or degraded with the expected code.
- A05-T-03: a fixture with a controlled opponent strength defect is rejected or degraded with the expected code.
- A05-T-04: a fixture with a controlled home-away split defect is rejected or degraded with the expected code.
- A05-T-05: a fixture with a controlled leakage cutoff defect is rejected or degraded with the expected code.
- A05-T-90: an evidence item one second after cutoff is excluded and logged.
- A05-T-91: an unknown field in strict output causes validation failure.
- A05-T-92: a provider timeout produces a bounded retry and no duplicate artifact.
- A05-T-93: a model refusal is classified and never accepted as a valid report.
- A05-T-94: snapshot hashes remain identical on idempotent replay.

### 9.7 A06 — Player and Squad Analyst

- Orchestration stage: `S06`.
- Goal: Estimate availability, role impact, replacements, and squad depth.
- Failure code: `DEGRADED_SQUAD`.
- Default execution mode: one bounded structured-output call or one deterministic compute activity.
- Maximum self-repair attempts: one schema-repair call; then fail or degrade according to policy.

#### Inputs

- A06-IN-01: rosters.
- A06-IN-02: injuries.
- A06-IN-03: suspensions.
- A06-IN-04: expected minutes.
- Input envelope MUST contain `run_id`, `fixture_id`, `cutoff_at`, `config_snapshot_id`, and `correlation_id`.
- Each input artifact MUST be referenced by immutable artifact ID and SHA-256 hash.

#### Outputs

- A06-OUT-01: availability distributions.
- A06-OUT-02: role impact ranges.
- A06-OUT-03: depth risks.
- Output MUST validate against the agent-specific Pydantic schema version recorded in the envelope.
- Output MUST contain `status`, `confidence`, `limitations`, `citations`, and `created_at`.
- Output MUST NOT contain unbounded free-form chain-of-thought.
- Explanations MUST be concise evidence summaries suitable for audit and display.

#### Allowed sources and tools

- Allowed: official squads.
- Allowed: licensed injury feeds.
- Allowed: verified reports.
- Deny by default: any source, index, or tool not named by this role or runtime policy.
- Secrets MUST be injected by the adapter and MUST NOT appear in the rendered prompt.

#### Retrieval policy

- Primary rule: Entity-scoped hybrid retrieval; recency boost; unconfirmed-source penalty.
- Filter order: tenant/personal scope, sport, fixture/entity, knowledge time, effective time, source class, then semantic rank.
- Retrieved chunks MUST preserve source snapshot ID, byte/character span, observed time, and content hash.
- Context packing MUST prioritize materiality and source independence over raw similarity score.
- Retrieval MUST return an explicit empty result when constraints remove all candidates.
- The agent MUST NOT ask the model to “remember” facts that are absent from the packet.

#### Mandatory checks

- A06-CHK-01: verify identity.
- A06-CHK-02: verify status timestamp.
- A06-CHK-03: verify role.
- A06-CHK-04: verify replacement quality.
- A06-CHK-05: verify double counting.
- A06-CHK-90: verify every material statement has a source or is labeled inference.
- A06-CHK-91: verify no evidence has `observed_at > cutoff_at`.
- A06-CHK-92: verify confidence decreases when critical evidence is absent or contradictory.
- A06-CHK-93: verify all probabilities are finite decimals within [0, 1] when this role is authorized to emit probabilities.
- A06-CHK-94: verify the output is deterministic under the deterministic test adapter.

#### System instruction template

```text
You are Player and Squad Analyst, logical role A06 in MİRON BABA AI.
Your only objective is: Estimate availability, role impact, replacements, and squad depth.
Use only the supplied, cutoff-safe evidence packet and explicitly allowed tools.
Never invent a fact, source, timestamp, player status, statistic, price, or provider result.
Separate observed facts, derived metrics, inferences, and unknowns.
Treat conflicting evidence as a first-class output; do not average contradictions into false certainty.
Do not select a winner or emit final outcome probabilities unless this role's stated goal explicitly authorizes it.
Do not expose private chain-of-thought. Return concise conclusions, supporting citations, checks, and uncertainty.
Do not give guaranteed outcomes, financial advice, or wagering instructions.
If a critical input is unavailable, return the declared degraded or failure status: DEGRADED_SQUAD.
Return only JSON conforming exactly to schema {{schema_version}}.
Run ID: {{run_id}}
Fixture ID: {{fixture_id}}
Cutoff: {{cutoff_at}}
Prompt version: {{prompt_version}}
```

#### User/task prompt template

```text
TASK
Evaluate the supplied artifacts for Player and Squad Analyst.

INPUT MANIFEST
{{input_manifest_json}}

EVIDENCE PACKET
{{evidence_packet_json}}

POLICY
{{role_policy_json}}

REQUIRED OUTPUT
{{output_schema_json}}

Before returning, check identifiers, cutoff compliance, citations, units, uncertainty, and schema validity.
```

#### Acceptance tests

- A06-T-01: a fixture with a controlled identity defect is rejected or degraded with the expected code.
- A06-T-02: a fixture with a controlled status timestamp defect is rejected or degraded with the expected code.
- A06-T-03: a fixture with a controlled role defect is rejected or degraded with the expected code.
- A06-T-04: a fixture with a controlled replacement quality defect is rejected or degraded with the expected code.
- A06-T-05: a fixture with a controlled double counting defect is rejected or degraded with the expected code.
- A06-T-90: an evidence item one second after cutoff is excluded and logged.
- A06-T-91: an unknown field in strict output causes validation failure.
- A06-T-92: a provider timeout produces a bounded retry and no duplicate artifact.
- A06-T-93: a model refusal is classified and never accepted as a valid report.
- A06-T-94: snapshot hashes remain identical on idempotent replay.

### 9.8 A07 — Tactical Analyst

- Orchestration stage: `S07`.
- Goal: Model tactical structures, likely plans, matchup mechanisms, and adaptation paths.
- Failure code: `DEGRADED_TACTICS`.
- Default execution mode: one bounded structured-output call or one deterministic compute activity.
- Maximum self-repair attempts: one schema-repair call; then fail or degrade according to policy.

#### Inputs

- A07-IN-01: formations.
- A07-IN-02: event tendencies.
- A07-IN-03: coach history.
- A07-IN-04: verified tactical reports.
- Input envelope MUST contain `run_id`, `fixture_id`, `cutoff_at`, `config_snapshot_id`, and `correlation_id`.
- Each input artifact MUST be referenced by immutable artifact ID and SHA-256 hash.

#### Outputs

- A07-OUT-01: tactical mechanisms.
- A07-OUT-02: matchup edges.
- A07-OUT-03: adaptation scenarios.
- Output MUST validate against the agent-specific Pydantic schema version recorded in the envelope.
- Output MUST contain `status`, `confidence`, `limitations`, `citations`, and `created_at`.
- Output MUST NOT contain unbounded free-form chain-of-thought.
- Explanations MUST be concise evidence summaries suitable for audit and display.

#### Allowed sources and tools

- Allowed: structured events.
- Allowed: verified analysis.
- Allowed: case memory.
- Deny by default: any source, index, or tool not named by this role or runtime policy.
- Secrets MUST be injected by the adapter and MUST NOT appear in the rendered prompt.

#### Retrieval policy

- Primary rule: Case similarity allowed only after current-match facts are fixed.
- Filter order: tenant/personal scope, sport, fixture/entity, knowledge time, effective time, source class, then semantic rank.
- Retrieved chunks MUST preserve source snapshot ID, byte/character span, observed time, and content hash.
- Context packing MUST prioritize materiality and source independence over raw similarity score.
- Retrieval MUST return an explicit empty result when constraints remove all candidates.
- The agent MUST NOT ask the model to “remember” facts that are absent from the packet.

#### Mandatory checks

- A07-CHK-01: verify descriptive versus causal claim.
- A07-CHK-02: verify coach continuity.
- A07-CHK-03: verify personnel compatibility.
- A07-CHK-04: verify opponent interaction.
- A07-CHK-90: verify every material statement has a source or is labeled inference.
- A07-CHK-91: verify no evidence has `observed_at > cutoff_at`.
- A07-CHK-92: verify confidence decreases when critical evidence is absent or contradictory.
- A07-CHK-93: verify all probabilities are finite decimals within [0, 1] when this role is authorized to emit probabilities.
- A07-CHK-94: verify the output is deterministic under the deterministic test adapter.

#### System instruction template

```text
You are Tactical Analyst, logical role A07 in MİRON BABA AI.
Your only objective is: Model tactical structures, likely plans, matchup mechanisms, and adaptation paths.
Use only the supplied, cutoff-safe evidence packet and explicitly allowed tools.
Never invent a fact, source, timestamp, player status, statistic, price, or provider result.
Separate observed facts, derived metrics, inferences, and unknowns.
Treat conflicting evidence as a first-class output; do not average contradictions into false certainty.
Do not select a winner or emit final outcome probabilities unless this role's stated goal explicitly authorizes it.
Do not expose private chain-of-thought. Return concise conclusions, supporting citations, checks, and uncertainty.
Do not give guaranteed outcomes, financial advice, or wagering instructions.
If a critical input is unavailable, return the declared degraded or failure status: DEGRADED_TACTICS.
Return only JSON conforming exactly to schema {{schema_version}}.
Run ID: {{run_id}}
Fixture ID: {{fixture_id}}
Cutoff: {{cutoff_at}}
Prompt version: {{prompt_version}}
```

#### User/task prompt template

```text
TASK
Evaluate the supplied artifacts for Tactical Analyst.

INPUT MANIFEST
{{input_manifest_json}}

EVIDENCE PACKET
{{evidence_packet_json}}

POLICY
{{role_policy_json}}

REQUIRED OUTPUT
{{output_schema_json}}

Before returning, check identifiers, cutoff compliance, citations, units, uncertainty, and schema validity.
```

#### Acceptance tests

- A07-T-01: a fixture with a controlled descriptive versus causal claim defect is rejected or degraded with the expected code.
- A07-T-02: a fixture with a controlled coach continuity defect is rejected or degraded with the expected code.
- A07-T-03: a fixture with a controlled personnel compatibility defect is rejected or degraded with the expected code.
- A07-T-04: a fixture with a controlled opponent interaction defect is rejected or degraded with the expected code.
- A07-T-90: an evidence item one second after cutoff is excluded and logged.
- A07-T-91: an unknown field in strict output causes validation failure.
- A07-T-92: a provider timeout produces a bounded retry and no duplicate artifact.
- A07-T-93: a model refusal is classified and never accepted as a valid report.
- A07-T-94: snapshot hashes remain identical on idempotent replay.

### 9.9 A08 — Form Analyst

- Orchestration stage: `S08`.
- Goal: Estimate current strength change without recency theater.
- Failure code: `DEGRADED_FORM`.
- Default execution mode: one bounded structured-output call or one deterministic compute activity.
- Maximum self-repair attempts: one schema-repair call; then fail or degrade according to policy.

#### Inputs

- A08-IN-01: recent matches.
- A08-IN-02: expected metrics.
- A08-IN-03: opponent ratings.
- A08-IN-04: squad continuity.
- Input envelope MUST contain `run_id`, `fixture_id`, `cutoff_at`, `config_snapshot_id`, and `correlation_id`.
- Each input artifact MUST be referenced by immutable artifact ID and SHA-256 hash.

#### Outputs

- A08-OUT-01: form posterior.
- A08-OUT-02: trend uncertainty.
- A08-OUT-03: regression warnings.
- Output MUST validate against the agent-specific Pydantic schema version recorded in the envelope.
- Output MUST contain `status`, `confidence`, `limitations`, `citations`, and `created_at`.
- Output MUST NOT contain unbounded free-form chain-of-thought.
- Explanations MUST be concise evidence summaries suitable for audit and display.

#### Allowed sources and tools

- Allowed: structured match history.
- Deny by default: any source, index, or tool not named by this role or runtime policy.
- Secrets MUST be injected by the adapter and MUST NOT appear in the rendered prompt.

#### Retrieval policy

- Primary rule: Time-series with exponentially decayed weights and competition filter.
- Filter order: tenant/personal scope, sport, fixture/entity, knowledge time, effective time, source class, then semantic rank.
- Retrieved chunks MUST preserve source snapshot ID, byte/character span, observed time, and content hash.
- Context packing MUST prioritize materiality and source independence over raw similarity score.
- Retrieval MUST return an explicit empty result when constraints remove all candidates.
- The agent MUST NOT ask the model to “remember” facts that are absent from the packet.

#### Mandatory checks

- A08-CHK-01: verify opponent adjustment.
- A08-CHK-02: verify venue.
- A08-CHK-03: verify finishing variance.
- A08-CHK-04: verify manager change.
- A08-CHK-05: verify sample size.
- A08-CHK-90: verify every material statement has a source or is labeled inference.
- A08-CHK-91: verify no evidence has `observed_at > cutoff_at`.
- A08-CHK-92: verify confidence decreases when critical evidence is absent or contradictory.
- A08-CHK-93: verify all probabilities are finite decimals within [0, 1] when this role is authorized to emit probabilities.
- A08-CHK-94: verify the output is deterministic under the deterministic test adapter.

#### System instruction template

```text
You are Form Analyst, logical role A08 in MİRON BABA AI.
Your only objective is: Estimate current strength change without recency theater.
Use only the supplied, cutoff-safe evidence packet and explicitly allowed tools.
Never invent a fact, source, timestamp, player status, statistic, price, or provider result.
Separate observed facts, derived metrics, inferences, and unknowns.
Treat conflicting evidence as a first-class output; do not average contradictions into false certainty.
Do not select a winner or emit final outcome probabilities unless this role's stated goal explicitly authorizes it.
Do not expose private chain-of-thought. Return concise conclusions, supporting citations, checks, and uncertainty.
Do not give guaranteed outcomes, financial advice, or wagering instructions.
If a critical input is unavailable, return the declared degraded or failure status: DEGRADED_FORM.
Return only JSON conforming exactly to schema {{schema_version}}.
Run ID: {{run_id}}
Fixture ID: {{fixture_id}}
Cutoff: {{cutoff_at}}
Prompt version: {{prompt_version}}
```

#### User/task prompt template

```text
TASK
Evaluate the supplied artifacts for Form Analyst.

INPUT MANIFEST
{{input_manifest_json}}

EVIDENCE PACKET
{{evidence_packet_json}}

POLICY
{{role_policy_json}}

REQUIRED OUTPUT
{{output_schema_json}}

Before returning, check identifiers, cutoff compliance, citations, units, uncertainty, and schema validity.
```

#### Acceptance tests

- A08-T-01: a fixture with a controlled opponent adjustment defect is rejected or degraded with the expected code.
- A08-T-02: a fixture with a controlled venue defect is rejected or degraded with the expected code.
- A08-T-03: a fixture with a controlled finishing variance defect is rejected or degraded with the expected code.
- A08-T-04: a fixture with a controlled manager change defect is rejected or degraded with the expected code.
- A08-T-05: a fixture with a controlled sample size defect is rejected or degraded with the expected code.
- A08-T-90: an evidence item one second after cutoff is excluded and logged.
- A08-T-91: an unknown field in strict output causes validation failure.
- A08-T-92: a provider timeout produces a bounded retry and no duplicate artifact.
- A08-T-93: a model refusal is classified and never accepted as a valid report.
- A08-T-94: snapshot hashes remain identical on idempotent replay.

### 9.10 A09 — Fatigue and Schedule Analyst

- Orchestration stage: `S09`.
- Goal: Quantify rest, travel, congestion, extra time, and rotation pressure.
- Failure code: `DEGRADED_FATIGUE`.
- Default execution mode: one bounded structured-output call or one deterministic compute activity.
- Maximum self-repair attempts: one schema-repair call; then fail or degrade according to policy.

#### Inputs

- A09-IN-01: fixtures.
- A09-IN-02: minutes.
- A09-IN-03: travel coordinates.
- A09-IN-04: competition priority.
- Input envelope MUST contain `run_id`, `fixture_id`, `cutoff_at`, `config_snapshot_id`, and `correlation_id`.
- Each input artifact MUST be referenced by immutable artifact ID and SHA-256 hash.

#### Outputs

- A09-OUT-01: fatigue features.
- A09-OUT-02: travel load.
- A09-OUT-03: rotation likelihood.
- Output MUST validate against the agent-specific Pydantic schema version recorded in the envelope.
- Output MUST contain `status`, `confidence`, `limitations`, `citations`, and `created_at`.
- Output MUST NOT contain unbounded free-form chain-of-thought.
- Explanations MUST be concise evidence summaries suitable for audit and display.

#### Allowed sources and tools

- Allowed: fixture provider.
- Allowed: minutes provider.
- Allowed: venue registry.
- Deny by default: any source, index, or tool not named by this role or runtime policy.
- Secrets MUST be injected by the adapter and MUST NOT appear in the rendered prompt.

#### Retrieval policy

- Primary rule: Structured schedule queries only.
- Filter order: tenant/personal scope, sport, fixture/entity, knowledge time, effective time, source class, then semantic rank.
- Retrieved chunks MUST preserve source snapshot ID, byte/character span, observed time, and content hash.
- Context packing MUST prioritize materiality and source independence over raw similarity score.
- Retrieval MUST return an explicit empty result when constraints remove all candidates.
- The agent MUST NOT ask the model to “remember” facts that are absent from the packet.

#### Mandatory checks

- A09-CHK-01: verify local kickoff conversion.
- A09-CHK-02: verify extra time.
- A09-CHK-03: verify time zones.
- A09-CHK-04: verify distance method.
- A09-CHK-05: verify rest asymmetry.
- A09-CHK-90: verify every material statement has a source or is labeled inference.
- A09-CHK-91: verify no evidence has `observed_at > cutoff_at`.
- A09-CHK-92: verify confidence decreases when critical evidence is absent or contradictory.
- A09-CHK-93: verify all probabilities are finite decimals within [0, 1] when this role is authorized to emit probabilities.
- A09-CHK-94: verify the output is deterministic under the deterministic test adapter.

#### System instruction template

```text
You are Fatigue and Schedule Analyst, logical role A09 in MİRON BABA AI.
Your only objective is: Quantify rest, travel, congestion, extra time, and rotation pressure.
Use only the supplied, cutoff-safe evidence packet and explicitly allowed tools.
Never invent a fact, source, timestamp, player status, statistic, price, or provider result.
Separate observed facts, derived metrics, inferences, and unknowns.
Treat conflicting evidence as a first-class output; do not average contradictions into false certainty.
Do not select a winner or emit final outcome probabilities unless this role's stated goal explicitly authorizes it.
Do not expose private chain-of-thought. Return concise conclusions, supporting citations, checks, and uncertainty.
Do not give guaranteed outcomes, financial advice, or wagering instructions.
If a critical input is unavailable, return the declared degraded or failure status: DEGRADED_FATIGUE.
Return only JSON conforming exactly to schema {{schema_version}}.
Run ID: {{run_id}}
Fixture ID: {{fixture_id}}
Cutoff: {{cutoff_at}}
Prompt version: {{prompt_version}}
```

#### User/task prompt template

```text
TASK
Evaluate the supplied artifacts for Fatigue and Schedule Analyst.

INPUT MANIFEST
{{input_manifest_json}}

EVIDENCE PACKET
{{evidence_packet_json}}

POLICY
{{role_policy_json}}

REQUIRED OUTPUT
{{output_schema_json}}

Before returning, check identifiers, cutoff compliance, citations, units, uncertainty, and schema validity.
```

#### Acceptance tests

- A09-T-01: a fixture with a controlled local kickoff conversion defect is rejected or degraded with the expected code.
- A09-T-02: a fixture with a controlled extra time defect is rejected or degraded with the expected code.
- A09-T-03: a fixture with a controlled time zones defect is rejected or degraded with the expected code.
- A09-T-04: a fixture with a controlled distance method defect is rejected or degraded with the expected code.
- A09-T-05: a fixture with a controlled rest asymmetry defect is rejected or degraded with the expected code.
- A09-T-90: an evidence item one second after cutoff is excluded and logged.
- A09-T-91: an unknown field in strict output causes validation failure.
- A09-T-92: a provider timeout produces a bounded retry and no duplicate artifact.
- A09-T-93: a model refusal is classified and never accepted as a valid report.
- A09-T-94: snapshot hashes remain identical on idempotent replay.

### 9.11 A10 — Goalkeeper Analyst

- Orchestration stage: `S10`.
- Goal: Assess goalkeeper availability, baseline quality, style fit, and uncertainty.
- Failure code: `DEGRADED_GOALKEEPER`.
- Default execution mode: one bounded structured-output call or one deterministic compute activity.
- Maximum self-repair attempts: one schema-repair call; then fail or degrade according to policy.

#### Inputs

- A10-IN-01: goalkeeper history.
- A10-IN-02: shots faced.
- A10-IN-03: cross claims.
- A10-IN-04: lineup status.
- Input envelope MUST contain `run_id`, `fixture_id`, `cutoff_at`, `config_snapshot_id`, and `correlation_id`.
- Each input artifact MUST be referenced by immutable artifact ID and SHA-256 hash.

#### Outputs

- A10-OUT-01: keeper distribution.
- A10-OUT-02: style interactions.
- A10-OUT-03: replacement penalty.
- Output MUST validate against the agent-specific Pydantic schema version recorded in the envelope.
- Output MUST contain `status`, `confidence`, `limitations`, `citations`, and `created_at`.
- Output MUST NOT contain unbounded free-form chain-of-thought.
- Explanations MUST be concise evidence summaries suitable for audit and display.

#### Allowed sources and tools

- Allowed: event data.
- Allowed: official squad evidence.
- Deny by default: any source, index, or tool not named by this role or runtime policy.
- Secrets MUST be injected by the adapter and MUST NOT appear in the rendered prompt.

#### Retrieval policy

- Primary rule: Player-specific structured data plus verified current claims.
- Filter order: tenant/personal scope, sport, fixture/entity, knowledge time, effective time, source class, then semantic rank.
- Retrieved chunks MUST preserve source snapshot ID, byte/character span, observed time, and content hash.
- Context packing MUST prioritize materiality and source independence over raw similarity score.
- Retrieval MUST return an explicit empty result when constraints remove all candidates.
- The agent MUST NOT ask the model to “remember” facts that are absent from the packet.

#### Mandatory checks

- A10-CHK-01: verify small-sample shrinkage.
- A10-CHK-02: verify post-shot metric availability.
- A10-CHK-03: verify defensive context.
- A10-CHK-04: verify starter probability.
- A10-CHK-90: verify every material statement has a source or is labeled inference.
- A10-CHK-91: verify no evidence has `observed_at > cutoff_at`.
- A10-CHK-92: verify confidence decreases when critical evidence is absent or contradictory.
- A10-CHK-93: verify all probabilities are finite decimals within [0, 1] when this role is authorized to emit probabilities.
- A10-CHK-94: verify the output is deterministic under the deterministic test adapter.

#### System instruction template

```text
You are Goalkeeper Analyst, logical role A10 in MİRON BABA AI.
Your only objective is: Assess goalkeeper availability, baseline quality, style fit, and uncertainty.
Use only the supplied, cutoff-safe evidence packet and explicitly allowed tools.
Never invent a fact, source, timestamp, player status, statistic, price, or provider result.
Separate observed facts, derived metrics, inferences, and unknowns.
Treat conflicting evidence as a first-class output; do not average contradictions into false certainty.
Do not select a winner or emit final outcome probabilities unless this role's stated goal explicitly authorizes it.
Do not expose private chain-of-thought. Return concise conclusions, supporting citations, checks, and uncertainty.
Do not give guaranteed outcomes, financial advice, or wagering instructions.
If a critical input is unavailable, return the declared degraded or failure status: DEGRADED_GOALKEEPER.
Return only JSON conforming exactly to schema {{schema_version}}.
Run ID: {{run_id}}
Fixture ID: {{fixture_id}}
Cutoff: {{cutoff_at}}
Prompt version: {{prompt_version}}
```

#### User/task prompt template

```text
TASK
Evaluate the supplied artifacts for Goalkeeper Analyst.

INPUT MANIFEST
{{input_manifest_json}}

EVIDENCE PACKET
{{evidence_packet_json}}

POLICY
{{role_policy_json}}

REQUIRED OUTPUT
{{output_schema_json}}

Before returning, check identifiers, cutoff compliance, citations, units, uncertainty, and schema validity.
```

#### Acceptance tests

- A10-T-01: a fixture with a controlled small-sample shrinkage defect is rejected or degraded with the expected code.
- A10-T-02: a fixture with a controlled post-shot metric availability defect is rejected or degraded with the expected code.
- A10-T-03: a fixture with a controlled defensive context defect is rejected or degraded with the expected code.
- A10-T-04: a fixture with a controlled starter probability defect is rejected or degraded with the expected code.
- A10-T-90: an evidence item one second after cutoff is excluded and logged.
- A10-T-91: an unknown field in strict output causes validation failure.
- A10-T-92: a provider timeout produces a bounded retry and no duplicate artifact.
- A10-T-93: a model refusal is classified and never accepted as a valid report.
- A10-T-94: snapshot hashes remain identical on idempotent replay.

### 9.12 A11 — Set-Piece Analyst

- Orchestration stage: `S11`.
- Goal: Estimate set-piece creation and prevention mechanisms.
- Failure code: `DEGRADED_SET_PIECE`.
- Default execution mode: one bounded structured-output call or one deterministic compute activity.
- Maximum self-repair attempts: one schema-repair call; then fail or degrade according to policy.

#### Inputs

- A11-IN-01: set-piece events.
- A11-IN-02: delivery roles.
- A11-IN-03: aerial personnel.
- A11-IN-04: opponent schemes.
- Input envelope MUST contain `run_id`, `fixture_id`, `cutoff_at`, `config_snapshot_id`, and `correlation_id`.
- Each input artifact MUST be referenced by immutable artifact ID and SHA-256 hash.

#### Outputs

- A11-OUT-01: set-piece feature set.
- A11-OUT-02: mismatch scenarios.
- A11-OUT-03: uncertainty.
- Output MUST validate against the agent-specific Pydantic schema version recorded in the envelope.
- Output MUST contain `status`, `confidence`, `limitations`, `citations`, and `created_at`.
- Output MUST NOT contain unbounded free-form chain-of-thought.
- Explanations MUST be concise evidence summaries suitable for audit and display.

#### Allowed sources and tools

- Allowed: event provider.
- Allowed: squad evidence.
- Allowed: tactical reports.
- Deny by default: any source, index, or tool not named by this role or runtime policy.
- Secrets MUST be injected by the adapter and MUST NOT appear in the rendered prompt.

#### Retrieval policy

- Primary rule: Structured event filters and current personnel claims.
- Filter order: tenant/personal scope, sport, fixture/entity, knowledge time, effective time, source class, then semantic rank.
- Retrieved chunks MUST preserve source snapshot ID, byte/character span, observed time, and content hash.
- Context packing MUST prioritize materiality and source independence over raw similarity score.
- Retrieval MUST return an explicit empty result when constraints remove all candidates.
- The agent MUST NOT ask the model to “remember” facts that are absent from the packet.

#### Mandatory checks

- A11-CHK-01: verify penalty exclusion.
- A11-CHK-02: verify sample size.
- A11-CHK-03: verify competition definitions.
- A11-CHK-04: verify personnel availability.
- A11-CHK-90: verify every material statement has a source or is labeled inference.
- A11-CHK-91: verify no evidence has `observed_at > cutoff_at`.
- A11-CHK-92: verify confidence decreases when critical evidence is absent or contradictory.
- A11-CHK-93: verify all probabilities are finite decimals within [0, 1] when this role is authorized to emit probabilities.
- A11-CHK-94: verify the output is deterministic under the deterministic test adapter.

#### System instruction template

```text
You are Set-Piece Analyst, logical role A11 in MİRON BABA AI.
Your only objective is: Estimate set-piece creation and prevention mechanisms.
Use only the supplied, cutoff-safe evidence packet and explicitly allowed tools.
Never invent a fact, source, timestamp, player status, statistic, price, or provider result.
Separate observed facts, derived metrics, inferences, and unknowns.
Treat conflicting evidence as a first-class output; do not average contradictions into false certainty.
Do not select a winner or emit final outcome probabilities unless this role's stated goal explicitly authorizes it.
Do not expose private chain-of-thought. Return concise conclusions, supporting citations, checks, and uncertainty.
Do not give guaranteed outcomes, financial advice, or wagering instructions.
If a critical input is unavailable, return the declared degraded or failure status: DEGRADED_SET_PIECE.
Return only JSON conforming exactly to schema {{schema_version}}.
Run ID: {{run_id}}
Fixture ID: {{fixture_id}}
Cutoff: {{cutoff_at}}
Prompt version: {{prompt_version}}
```

#### User/task prompt template

```text
TASK
Evaluate the supplied artifacts for Set-Piece Analyst.

INPUT MANIFEST
{{input_manifest_json}}

EVIDENCE PACKET
{{evidence_packet_json}}

POLICY
{{role_policy_json}}

REQUIRED OUTPUT
{{output_schema_json}}

Before returning, check identifiers, cutoff compliance, citations, units, uncertainty, and schema validity.
```

#### Acceptance tests

- A11-T-01: a fixture with a controlled penalty exclusion defect is rejected or degraded with the expected code.
- A11-T-02: a fixture with a controlled sample size defect is rejected or degraded with the expected code.
- A11-T-03: a fixture with a controlled competition definitions defect is rejected or degraded with the expected code.
- A11-T-04: a fixture with a controlled personnel availability defect is rejected or degraded with the expected code.
- A11-T-90: an evidence item one second after cutoff is excluded and logged.
- A11-T-91: an unknown field in strict output causes validation failure.
- A11-T-92: a provider timeout produces a bounded retry and no duplicate artifact.
- A11-T-93: a model refusal is classified and never accepted as a valid report.
- A11-T-94: snapshot hashes remain identical on idempotent replay.

### 9.13 A12 — Environment Analyst

- Orchestration stage: `S12`.
- Goal: Assess venue, surface, weather, altitude, travel, and referee context.
- Failure code: `DEGRADED_ENVIRONMENT`.
- Default execution mode: one bounded structured-output call or one deterministic compute activity.
- Maximum self-repair attempts: one schema-repair call; then fail or degrade according to policy.

#### Inputs

- A12-IN-01: venue.
- A12-IN-02: forecast snapshots.
- A12-IN-03: official assignments.
- A12-IN-04: team adaptation history.
- Input envelope MUST contain `run_id`, `fixture_id`, `cutoff_at`, `config_snapshot_id`, and `correlation_id`.
- Each input artifact MUST be referenced by immutable artifact ID and SHA-256 hash.

#### Outputs

- A12-OUT-01: environment factors.
- A12-OUT-02: weather uncertainty.
- A12-OUT-03: referee context.
- Output MUST validate against the agent-specific Pydantic schema version recorded in the envelope.
- Output MUST contain `status`, `confidence`, `limitations`, `citations`, and `created_at`.
- Output MUST NOT contain unbounded free-form chain-of-thought.
- Explanations MUST be concise evidence summaries suitable for audit and display.

#### Allowed sources and tools

- Allowed: weather provider.
- Allowed: competition officials.
- Allowed: venue registry.
- Deny by default: any source, index, or tool not named by this role or runtime policy.
- Secrets MUST be injected by the adapter and MUST NOT appear in the rendered prompt.

#### Retrieval policy

- Primary rule: Geospatial and time-window exact queries.
- Filter order: tenant/personal scope, sport, fixture/entity, knowledge time, effective time, source class, then semantic rank.
- Retrieved chunks MUST preserve source snapshot ID, byte/character span, observed time, and content hash.
- Context packing MUST prioritize materiality and source independence over raw similarity score.
- Retrieval MUST return an explicit empty result when constraints remove all candidates.
- The agent MUST NOT ask the model to “remember” facts that are absent from the packet.

#### Mandatory checks

- A12-CHK-01: verify forecast horizon.
- A12-CHK-02: verify units.
- A12-CHK-03: verify venue roof/surface.
- A12-CHK-04: verify referee sample shrinkage.
- A12-CHK-90: verify every material statement has a source or is labeled inference.
- A12-CHK-91: verify no evidence has `observed_at > cutoff_at`.
- A12-CHK-92: verify confidence decreases when critical evidence is absent or contradictory.
- A12-CHK-93: verify all probabilities are finite decimals within [0, 1] when this role is authorized to emit probabilities.
- A12-CHK-94: verify the output is deterministic under the deterministic test adapter.

#### System instruction template

```text
You are Environment Analyst, logical role A12 in MİRON BABA AI.
Your only objective is: Assess venue, surface, weather, altitude, travel, and referee context.
Use only the supplied, cutoff-safe evidence packet and explicitly allowed tools.
Never invent a fact, source, timestamp, player status, statistic, price, or provider result.
Separate observed facts, derived metrics, inferences, and unknowns.
Treat conflicting evidence as a first-class output; do not average contradictions into false certainty.
Do not select a winner or emit final outcome probabilities unless this role's stated goal explicitly authorizes it.
Do not expose private chain-of-thought. Return concise conclusions, supporting citations, checks, and uncertainty.
Do not give guaranteed outcomes, financial advice, or wagering instructions.
If a critical input is unavailable, return the declared degraded or failure status: DEGRADED_ENVIRONMENT.
Return only JSON conforming exactly to schema {{schema_version}}.
Run ID: {{run_id}}
Fixture ID: {{fixture_id}}
Cutoff: {{cutoff_at}}
Prompt version: {{prompt_version}}
```

#### User/task prompt template

```text
TASK
Evaluate the supplied artifacts for Environment Analyst.

INPUT MANIFEST
{{input_manifest_json}}

EVIDENCE PACKET
{{evidence_packet_json}}

POLICY
{{role_policy_json}}

REQUIRED OUTPUT
{{output_schema_json}}

Before returning, check identifiers, cutoff compliance, citations, units, uncertainty, and schema validity.
```

#### Acceptance tests

- A12-T-01: a fixture with a controlled forecast horizon defect is rejected or degraded with the expected code.
- A12-T-02: a fixture with a controlled units defect is rejected or degraded with the expected code.
- A12-T-03: a fixture with a controlled venue roof/surface defect is rejected or degraded with the expected code.
- A12-T-04: a fixture with a controlled referee sample shrinkage defect is rejected or degraded with the expected code.
- A12-T-90: an evidence item one second after cutoff is excluded and logged.
- A12-T-91: an unknown field in strict output causes validation failure.
- A12-T-92: a provider timeout produces a bounded retry and no duplicate artifact.
- A12-T-93: a model refusal is classified and never accepted as a valid report.
- A12-T-94: snapshot hashes remain identical on idempotent replay.

### 9.14 A13 — Odds and Market Intelligence Analyst

- Orchestration stage: `S13`.
- Goal: Normalize allowed odds, remove margin, detect movement, and quantify market uncertainty.
- Failure code: `DEGRADED_MARKET`.
- Default execution mode: one bounded structured-output call or one deterministic compute activity.
- Maximum self-repair attempts: one schema-repair call; then fail or degrade according to policy.

#### Inputs

- A13-IN-01: allowed odds snapshots.
- A13-IN-02: market mappings.
- A13-IN-03: bookmaker registry.
- Input envelope MUST contain `run_id`, `fixture_id`, `cutoff_at`, `config_snapshot_id`, and `correlation_id`.
- Each input artifact MUST be referenced by immutable artifact ID and SHA-256 hash.

#### Outputs

- A13-OUT-01: fair probabilities.
- A13-OUT-02: consensus.
- A13-OUT-03: movement features.
- A13-OUT-04: liquidity proxies.
- Output MUST validate against the agent-specific Pydantic schema version recorded in the envelope.
- Output MUST contain `status`, `confidence`, `limitations`, `citations`, and `created_at`.
- Output MUST NOT contain unbounded free-form chain-of-thought.
- Explanations MUST be concise evidence summaries suitable for audit and display.

#### Allowed sources and tools

- Allowed: licensed or explicitly allowed odds APIs.
- Deny by default: any source, index, or tool not named by this role or runtime policy.
- Secrets MUST be injected by the adapter and MUST NOT appear in the rendered prompt.

#### Retrieval policy

- Primary rule: Time-series only; bookmaker and market allowlists mandatory.
- Filter order: tenant/personal scope, sport, fixture/entity, knowledge time, effective time, source class, then semantic rank.
- Retrieved chunks MUST preserve source snapshot ID, byte/character span, observed time, and content hash.
- Context packing MUST prioritize materiality and source independence over raw similarity score.
- Retrieval MUST return an explicit empty result when constraints remove all candidates.
- The agent MUST NOT ask the model to “remember” facts that are absent from the packet.

#### Mandatory checks

- A13-CHK-01: verify event mapping.
- A13-CHK-02: verify market mapping.
- A13-CHK-03: verify timestamp.
- A13-CHK-04: verify stale quotes.
- A13-CHK-05: verify overround method.
- A13-CHK-90: verify every material statement has a source or is labeled inference.
- A13-CHK-91: verify no evidence has `observed_at > cutoff_at`.
- A13-CHK-92: verify confidence decreases when critical evidence is absent or contradictory.
- A13-CHK-93: verify all probabilities are finite decimals within [0, 1] when this role is authorized to emit probabilities.
- A13-CHK-94: verify the output is deterministic under the deterministic test adapter.

#### System instruction template

```text
You are Odds and Market Intelligence Analyst, logical role A13 in MİRON BABA AI.
Your only objective is: Normalize allowed odds, remove margin, detect movement, and quantify market uncertainty.
Use only the supplied, cutoff-safe evidence packet and explicitly allowed tools.
Never invent a fact, source, timestamp, player status, statistic, price, or provider result.
Separate observed facts, derived metrics, inferences, and unknowns.
Treat conflicting evidence as a first-class output; do not average contradictions into false certainty.
Do not select a winner or emit final outcome probabilities unless this role's stated goal explicitly authorizes it.
Do not expose private chain-of-thought. Return concise conclusions, supporting citations, checks, and uncertainty.
Do not give guaranteed outcomes, financial advice, or wagering instructions.
If a critical input is unavailable, return the declared degraded or failure status: DEGRADED_MARKET.
Return only JSON conforming exactly to schema {{schema_version}}.
Run ID: {{run_id}}
Fixture ID: {{fixture_id}}
Cutoff: {{cutoff_at}}
Prompt version: {{prompt_version}}
```

#### User/task prompt template

```text
TASK
Evaluate the supplied artifacts for Odds and Market Intelligence Analyst.

INPUT MANIFEST
{{input_manifest_json}}

EVIDENCE PACKET
{{evidence_packet_json}}

POLICY
{{role_policy_json}}

REQUIRED OUTPUT
{{output_schema_json}}

Before returning, check identifiers, cutoff compliance, citations, units, uncertainty, and schema validity.
```

#### Acceptance tests

- A13-T-01: a fixture with a controlled event mapping defect is rejected or degraded with the expected code.
- A13-T-02: a fixture with a controlled market mapping defect is rejected or degraded with the expected code.
- A13-T-03: a fixture with a controlled timestamp defect is rejected or degraded with the expected code.
- A13-T-04: a fixture with a controlled stale quotes defect is rejected or degraded with the expected code.
- A13-T-05: a fixture with a controlled overround method defect is rejected or degraded with the expected code.
- A13-T-90: an evidence item one second after cutoff is excluded and logged.
- A13-T-91: an unknown field in strict output causes validation failure.
- A13-T-92: a provider timeout produces a bounded retry and no duplicate artifact.
- A13-T-93: a model refusal is classified and never accepted as a valid report.
- A13-T-94: snapshot hashes remain identical on idempotent replay.

### 9.15 A14 — Market Movement Explainer

- Orchestration stage: `S14`.
- Goal: Search for cutoff-safe public events aligned with market movement while returning UNEXPLAINED when no supported cause exists.
- Failure code: `MARKET_MOVEMENT_UNEXPLAINED`.
- Default execution mode: one bounded structured-output call or one deterministic compute activity.
- Maximum self-repair attempts: one schema-repair call; then fail or degrade according to policy.

#### Inputs

- A14-IN-01: isolated market movement windows.
- A14-IN-02: verified research corpus.
- A14-IN-03: cutoff.
- Input envelope MUST contain `run_id`, `fixture_id`, `cutoff_at`, `config_snapshot_id`, and `correlation_id`.
- Each input artifact MUST be referenced by immutable artifact ID and SHA-256 hash.

#### Outputs

- A14-OUT-01: candidate public explanations.
- A14-OUT-02: timing alignment.
- A14-OUT-03: UNEXPLAINED status.
- Output MUST validate against the agent-specific Pydantic schema version recorded in the envelope.
- Output MUST contain `status`, `confidence`, `limitations`, `citations`, and `created_at`.
- Output MUST NOT contain unbounded free-form chain-of-thought.
- Explanations MUST be concise evidence summaries suitable for audit and display.

#### Allowed sources and tools

- Allowed: grounded current research.
- Allowed: verified official and journalistic sources.
- Deny by default: any source, index, or tool not named by this role or runtime policy.
- Secrets MUST be injected by the adapter and MUST NOT appear in the rendered prompt.

#### Retrieval policy

- Primary rule: Contradiction-aware time-window search; the raw Market Analyst narrative remains hidden.
- Filter order: tenant/personal scope, sport, fixture/entity, knowledge time, effective time, source class, then semantic rank.
- Retrieved chunks MUST preserve source snapshot ID, byte/character span, observed time, and content hash.
- Context packing MUST prioritize materiality and source independence over raw similarity score.
- Retrieval MUST return an explicit empty result when constraints remove all candidates.
- The agent MUST NOT ask the model to “remember” facts that are absent from the packet.

#### Mandatory checks

- A14-CHK-01: verify event occurred before movement or plausibly during it.
- A14-CHK-02: verify source independence.
- A14-CHK-03: verify no invented causality.
- A14-CHK-04: verify unexplained state preserved.
- A14-CHK-90: verify every material statement has a source or is labeled inference.
- A14-CHK-91: verify no evidence has `observed_at > cutoff_at`.
- A14-CHK-92: verify confidence decreases when critical evidence is absent or contradictory.
- A14-CHK-93: verify all probabilities are finite decimals within [0, 1] when this role is authorized to emit probabilities.
- A14-CHK-94: verify the output is deterministic under the deterministic test adapter.

#### System instruction template

```text
You are Market Movement Explainer, logical role A14 in MİRON BABA AI.
Your only objective is: Search for cutoff-safe public events aligned with market movement while returning UNEXPLAINED when no supported cause exists.
Use only the supplied, cutoff-safe evidence packet and explicitly allowed tools.
Never invent a fact, source, timestamp, player status, statistic, price, or provider result.
Separate observed facts, derived metrics, inferences, and unknowns.
Treat conflicting evidence as a first-class output; do not average contradictions into false certainty.
Do not select a winner or emit final outcome probabilities unless this role's stated goal explicitly authorizes it.
Do not expose private chain-of-thought. Return concise conclusions, supporting citations, checks, and uncertainty.
Do not give guaranteed outcomes, financial advice, or wagering instructions.
If a critical input is unavailable, return the declared degraded or failure status: MARKET_MOVEMENT_UNEXPLAINED.
Return only JSON conforming exactly to schema {{schema_version}}.
Run ID: {{run_id}}
Fixture ID: {{fixture_id}}
Cutoff: {{cutoff_at}}
Prompt version: {{prompt_version}}
```

#### User/task prompt template

```text
TASK
Evaluate the supplied artifacts for Market Movement Explainer.

INPUT MANIFEST
{{input_manifest_json}}

EVIDENCE PACKET
{{evidence_packet_json}}

POLICY
{{role_policy_json}}

REQUIRED OUTPUT
{{output_schema_json}}

Before returning, check identifiers, cutoff compliance, citations, units, uncertainty, and schema validity.
```

#### Acceptance tests

- A14-T-01: a fixture with a controlled event occurred before movement or plausibly during it defect is rejected or degraded with the expected code.
- A14-T-02: a fixture with a controlled source independence defect is rejected or degraded with the expected code.
- A14-T-03: a fixture with a controlled no invented causality defect is rejected or degraded with the expected code.
- A14-T-04: a fixture with a controlled unexplained state preserved defect is rejected or degraded with the expected code.
- A14-T-90: an evidence item one second after cutoff is excluded and logged.
- A14-T-91: an unknown field in strict output causes validation failure.
- A14-T-92: a provider timeout produces a bounded retry and no duplicate artifact.
- A14-T-93: a model refusal is classified and never accepted as a valid report.
- A14-T-94: snapshot hashes remain identical on idempotent replay.

### 9.16 A15 — Quant Model Ensemble

- Orchestration stage: `S15`.
- Goal: Generate reproducible probability distributions from transparent non-LLM models.
- Failure code: `QUANT_INVALID`.
- Default execution mode: one bounded structured-output call or one deterministic compute activity.
- Maximum self-repair attempts: one schema-repair call; then fail or degrade according to policy.

#### Inputs

- A15-IN-01: validated feature bundle.
- A15-IN-02: model artifacts.
- A15-IN-03: calibrators.
- Input envelope MUST contain `run_id`, `fixture_id`, `cutoff_at`, `config_snapshot_id`, and `correlation_id`.
- Each input artifact MUST be referenced by immutable artifact ID and SHA-256 hash.

#### Outputs

- A15-OUT-01: per-model distributions.
- A15-OUT-02: ensemble distribution.
- A15-OUT-03: diagnostics.
- Output MUST validate against the agent-specific Pydantic schema version recorded in the envelope.
- Output MUST contain `status`, `confidence`, `limitations`, `citations`, and `created_at`.
- Output MUST NOT contain unbounded free-form chain-of-thought.
- Explanations MUST be concise evidence summaries suitable for audit and display.

#### Allowed sources and tools

- Allowed: feature store.
- Allowed: quant model registry.
- Deny by default: any source, index, or tool not named by this role or runtime policy.
- Secrets MUST be injected by the adapter and MUST NOT appear in the rendered prompt.

#### Retrieval policy

- Primary rule: No semantic retrieval; exact versioned artifacts only.
- Filter order: tenant/personal scope, sport, fixture/entity, knowledge time, effective time, source class, then semantic rank.
- Retrieved chunks MUST preserve source snapshot ID, byte/character span, observed time, and content hash.
- Context packing MUST prioritize materiality and source independence over raw similarity score.
- Retrieval MUST return an explicit empty result when constraints remove all candidates.
- The agent MUST NOT ask the model to “remember” facts that are absent from the packet.

#### Mandatory checks

- A15-CHK-01: verify feature schema.
- A15-CHK-02: verify missingness policy.
- A15-CHK-03: verify model version.
- A15-CHK-04: verify calibration domain.
- A15-CHK-05: verify sum-to-one.
- A15-CHK-90: verify every material statement has a source or is labeled inference.
- A15-CHK-91: verify no evidence has `observed_at > cutoff_at`.
- A15-CHK-92: verify confidence decreases when critical evidence is absent or contradictory.
- A15-CHK-93: verify all probabilities are finite decimals within [0, 1] when this role is authorized to emit probabilities.
- A15-CHK-94: verify the output is deterministic under the deterministic test adapter.

#### System instruction template

```text
You are Quant Model Ensemble, logical role A15 in MİRON BABA AI.
Your only objective is: Generate reproducible probability distributions from transparent non-LLM models.
Use only the supplied, cutoff-safe evidence packet and explicitly allowed tools.
Never invent a fact, source, timestamp, player status, statistic, price, or provider result.
Separate observed facts, derived metrics, inferences, and unknowns.
Treat conflicting evidence as a first-class output; do not average contradictions into false certainty.
Do not select a winner or emit final outcome probabilities unless this role's stated goal explicitly authorizes it.
Do not expose private chain-of-thought. Return concise conclusions, supporting citations, checks, and uncertainty.
Do not give guaranteed outcomes, financial advice, or wagering instructions.
If a critical input is unavailable, return the declared degraded or failure status: QUANT_INVALID.
Return only JSON conforming exactly to schema {{schema_version}}.
Run ID: {{run_id}}
Fixture ID: {{fixture_id}}
Cutoff: {{cutoff_at}}
Prompt version: {{prompt_version}}
```

#### User/task prompt template

```text
TASK
Evaluate the supplied artifacts for Quant Model Ensemble.

INPUT MANIFEST
{{input_manifest_json}}

EVIDENCE PACKET
{{evidence_packet_json}}

POLICY
{{role_policy_json}}

REQUIRED OUTPUT
{{output_schema_json}}

Before returning, check identifiers, cutoff compliance, citations, units, uncertainty, and schema validity.
```

#### Acceptance tests

- A15-T-01: a fixture with a controlled feature schema defect is rejected or degraded with the expected code.
- A15-T-02: a fixture with a controlled missingness policy defect is rejected or degraded with the expected code.
- A15-T-03: a fixture with a controlled model version defect is rejected or degraded with the expected code.
- A15-T-04: a fixture with a controlled calibration domain defect is rejected or degraded with the expected code.
- A15-T-05: a fixture with a controlled sum-to-one defect is rejected or degraded with the expected code.
- A15-T-90: an evidence item one second after cutoff is excluded and logged.
- A15-T-91: an unknown field in strict output causes validation failure.
- A15-T-92: a provider timeout produces a bounded retry and no duplicate artifact.
- A15-T-93: a model refusal is classified and never accepted as a valid report.
- A15-T-94: snapshot hashes remain identical on idempotent replay.

### 9.17 A16 — Historical Similarity Analyst

- Orchestration stage: `S16`.
- Goal: Retrieve structurally comparable cases without treating team-name history or analogy as proof.
- Failure code: `NO_RELIABLE_ANALOGS`.
- Default execution mode: one bounded structured-output call or one deterministic compute activity.
- Maximum self-repair attempts: one schema-repair call; then fail or degrade according to policy.

#### Inputs

- A16-IN-01: current match feature vector.
- A16-IN-02: validated case memory.
- A16-IN-03: scope rules.
- Input envelope MUST contain `run_id`, `fixture_id`, `cutoff_at`, `config_snapshot_id`, and `correlation_id`.
- Each input artifact MUST be referenced by immutable artifact ID and SHA-256 hash.

#### Outputs

- A16-OUT-01: similar cases.
- A16-OUT-02: distance decomposition.
- A16-OUT-03: transfer cautions.
- Output MUST validate against the agent-specific Pydantic schema version recorded in the envelope.
- Output MUST contain `status`, `confidence`, `limitations`, `citations`, and `created_at`.
- Output MUST NOT contain unbounded free-form chain-of-thought.
- Explanations MUST be concise evidence summaries suitable for audit and display.

#### Allowed sources and tools

- Allowed: locked validated historical cases only.
- Deny by default: any source, index, or tool not named by this role or runtime policy.
- Secrets MUST be injected by the adapter and MUST NOT appear in the rendered prompt.

#### Retrieval policy

- Primary rule: Hybrid numeric and semantic similarity with sport, era, knowledge-time, and outcome-leakage filters.
- Filter order: tenant/personal scope, sport, fixture/entity, knowledge time, effective time, source class, then semantic rank.
- Retrieved chunks MUST preserve source snapshot ID, byte/character span, observed time, and content hash.
- Context packing MUST prioritize materiality and source independence over raw similarity score.
- Retrieval MUST return an explicit empty result when constraints remove all candidates.
- The agent MUST NOT ask the model to “remember” facts that are absent from the packet.

#### Mandatory checks

- A16-CHK-01: verify competition era.
- A16-CHK-02: verify rules.
- A16-CHK-03: verify feature availability.
- A16-CHK-04: verify outcome leakage.
- A16-CHK-05: verify structural rather than team-name similarity.
- A16-CHK-90: verify every material statement has a source or is labeled inference.
- A16-CHK-91: verify no evidence has `observed_at > cutoff_at`.
- A16-CHK-92: verify confidence decreases when critical evidence is absent or contradictory.
- A16-CHK-93: verify all probabilities are finite decimals within [0, 1] when this role is authorized to emit probabilities.
- A16-CHK-94: verify the output is deterministic under the deterministic test adapter.

#### System instruction template

```text
You are Historical Similarity Analyst, logical role A16 in MİRON BABA AI.
Your only objective is: Retrieve structurally comparable cases without treating team-name history or analogy as proof.
Use only the supplied, cutoff-safe evidence packet and explicitly allowed tools.
Never invent a fact, source, timestamp, player status, statistic, price, or provider result.
Separate observed facts, derived metrics, inferences, and unknowns.
Treat conflicting evidence as a first-class output; do not average contradictions into false certainty.
Do not select a winner or emit final outcome probabilities unless this role's stated goal explicitly authorizes it.
Do not expose private chain-of-thought. Return concise conclusions, supporting citations, checks, and uncertainty.
Do not give guaranteed outcomes, financial advice, or wagering instructions.
If a critical input is unavailable, return the declared degraded or failure status: NO_RELIABLE_ANALOGS.
Return only JSON conforming exactly to schema {{schema_version}}.
Run ID: {{run_id}}
Fixture ID: {{fixture_id}}
Cutoff: {{cutoff_at}}
Prompt version: {{prompt_version}}
```

#### User/task prompt template

```text
TASK
Evaluate the supplied artifacts for Historical Similarity Analyst.

INPUT MANIFEST
{{input_manifest_json}}

EVIDENCE PACKET
{{evidence_packet_json}}

POLICY
{{role_policy_json}}

REQUIRED OUTPUT
{{output_schema_json}}

Before returning, check identifiers, cutoff compliance, citations, units, uncertainty, and schema validity.
```

#### Acceptance tests

- A16-T-01: a fixture with a controlled competition era defect is rejected or degraded with the expected code.
- A16-T-02: a fixture with a controlled rules defect is rejected or degraded with the expected code.
- A16-T-03: a fixture with a controlled feature availability defect is rejected or degraded with the expected code.
- A16-T-04: a fixture with a controlled outcome leakage defect is rejected or degraded with the expected code.
- A16-T-05: a fixture with a controlled structural rather than team-name similarity defect is rejected or degraded with the expected code.
- A16-T-90: an evidence item one second after cutoff is excluded and logged.
- A16-T-91: an unknown field in strict output causes validation failure.
- A16-T-92: a provider timeout produces a bounded retry and no duplicate artifact.
- A16-T-93: a model refusal is classified and never accepted as a valid report.
- A16-T-94: snapshot hashes remain identical on idempotent replay.

### 9.18 A17 — Statistics Critic

- Orchestration stage: `S17`.
- Goal: Attack statistical definitions, samples, leakage, and model assumptions without making a match prediction.
- Failure code: `CRITIC_REJECT`.
- Default execution mode: one bounded structured-output call or one deterministic compute activity.
- Maximum self-repair attempts: one schema-repair call; then fail or degrade according to policy.

#### Inputs

- A17-IN-01: statistical report.
- A17-IN-02: quant diagnostics.
- Input envelope MUST contain `run_id`, `fixture_id`, `cutoff_at`, `config_snapshot_id`, and `correlation_id`.
- Each input artifact MUST be referenced by immutable artifact ID and SHA-256 hash.

#### Outputs

- A17-OUT-01: critic verdict.
- A17-OUT-02: material defects.
- A17-OUT-03: required fixes.
- Output MUST validate against the agent-specific Pydantic schema version recorded in the envelope.
- Output MUST contain `status`, `confidence`, `limitations`, `citations`, and `created_at`.
- Output MUST NOT contain unbounded free-form chain-of-thought.
- Explanations MUST be concise evidence summaries suitable for audit and display.

#### Allowed sources and tools

- Allowed: same evidence packet, no other critic prose.
- Deny by default: any source, index, or tool not named by this role or runtime policy.
- Secrets MUST be injected by the adapter and MUST NOT appear in the rendered prompt.

#### Retrieval policy

- Primary rule: Exact referenced data only; no broad search.
- Filter order: tenant/personal scope, sport, fixture/entity, knowledge time, effective time, source class, then semantic rank.
- Retrieved chunks MUST preserve source snapshot ID, byte/character span, observed time, and content hash.
- Context packing MUST prioritize materiality and source independence over raw similarity score.
- Retrieval MUST return an explicit empty result when constraints remove all candidates.
- The agent MUST NOT ask the model to “remember” facts that are absent from the packet.

#### Mandatory checks

- A17-CHK-01: verify denominator.
- A17-CHK-02: verify selection bias.
- A17-CHK-03: verify regression.
- A17-CHK-04: verify multiple comparisons.
- A17-CHK-05: verify look-ahead.
- A17-CHK-90: verify every material statement has a source or is labeled inference.
- A17-CHK-91: verify no evidence has `observed_at > cutoff_at`.
- A17-CHK-92: verify confidence decreases when critical evidence is absent or contradictory.
- A17-CHK-93: verify all probabilities are finite decimals within [0, 1] when this role is authorized to emit probabilities.
- A17-CHK-94: verify the output is deterministic under the deterministic test adapter.

#### System instruction template

```text
You are Statistics Critic, logical role A17 in MİRON BABA AI.
Your only objective is: Attack statistical definitions, samples, leakage, and model assumptions without making a match prediction.
Use only the supplied, cutoff-safe evidence packet and explicitly allowed tools.
Never invent a fact, source, timestamp, player status, statistic, price, or provider result.
Separate observed facts, derived metrics, inferences, and unknowns.
Treat conflicting evidence as a first-class output; do not average contradictions into false certainty.
Do not select a winner or emit final outcome probabilities unless this role's stated goal explicitly authorizes it.
Do not expose private chain-of-thought. Return concise conclusions, supporting citations, checks, and uncertainty.
Do not give guaranteed outcomes, financial advice, or wagering instructions.
If a critical input is unavailable, return the declared degraded or failure status: CRITIC_REJECT.
Return only JSON conforming exactly to schema {{schema_version}}.
Run ID: {{run_id}}
Fixture ID: {{fixture_id}}
Cutoff: {{cutoff_at}}
Prompt version: {{prompt_version}}
```

#### User/task prompt template

```text
TASK
Evaluate the supplied artifacts for Statistics Critic.

INPUT MANIFEST
{{input_manifest_json}}

EVIDENCE PACKET
{{evidence_packet_json}}

POLICY
{{role_policy_json}}

REQUIRED OUTPUT
{{output_schema_json}}

Before returning, check identifiers, cutoff compliance, citations, units, uncertainty, and schema validity.
```

#### Acceptance tests

- A17-T-01: a fixture with a controlled denominator defect is rejected or degraded with the expected code.
- A17-T-02: a fixture with a controlled selection bias defect is rejected or degraded with the expected code.
- A17-T-03: a fixture with a controlled regression defect is rejected or degraded with the expected code.
- A17-T-04: a fixture with a controlled multiple comparisons defect is rejected or degraded with the expected code.
- A17-T-05: a fixture with a controlled look-ahead defect is rejected or degraded with the expected code.
- A17-T-90: an evidence item one second after cutoff is excluded and logged.
- A17-T-91: an unknown field in strict output causes validation failure.
- A17-T-92: a provider timeout produces a bounded retry and no duplicate artifact.
- A17-T-93: a model refusal is classified and never accepted as a valid report.
- A17-T-94: snapshot hashes remain identical on idempotent replay.

### 9.19 A18 — Evidence Critic

- Orchestration stage: `S17`.
- Goal: Attack provenance, claim strength, missing sources, and false corroboration without making a match prediction.
- Failure code: `CRITIC_REJECT`.
- Default execution mode: one bounded structured-output call or one deterministic compute activity.
- Maximum self-repair attempts: one schema-repair call; then fail or degrade according to policy.

#### Inputs

- A18-IN-01: evidence ledger.
- A18-IN-02: contradiction report.
- Input envelope MUST contain `run_id`, `fixture_id`, `cutoff_at`, `config_snapshot_id`, and `correlation_id`.
- Each input artifact MUST be referenced by immutable artifact ID and SHA-256 hash.

#### Outputs

- A18-OUT-01: evidence verdict.
- A18-OUT-02: unsupported claims.
- A18-OUT-03: severity.
- Output MUST validate against the agent-specific Pydantic schema version recorded in the envelope.
- Output MUST contain `status`, `confidence`, `limitations`, `citations`, and `created_at`.
- Output MUST NOT contain unbounded free-form chain-of-thought.
- Explanations MUST be concise evidence summaries suitable for audit and display.

#### Allowed sources and tools

- Allowed: source snapshots and claim graph.
- Deny by default: any source, index, or tool not named by this role or runtime policy.
- Secrets MUST be injected by the adapter and MUST NOT appear in the rendered prompt.

#### Retrieval policy

- Primary rule: Graph traversal and source exact lookup.
- Filter order: tenant/personal scope, sport, fixture/entity, knowledge time, effective time, source class, then semantic rank.
- Retrieved chunks MUST preserve source snapshot ID, byte/character span, observed time, and content hash.
- Context packing MUST prioritize materiality and source independence over raw similarity score.
- Retrieval MUST return an explicit empty result when constraints remove all candidates.
- The agent MUST NOT ask the model to “remember” facts that are absent from the packet.

#### Mandatory checks

- A18-CHK-01: verify circular reporting.
- A18-CHK-02: verify copied articles.
- A18-CHK-03: verify timestamp ambiguity.
- A18-CHK-04: verify authority mismatch.
- A18-CHK-90: verify every material statement has a source or is labeled inference.
- A18-CHK-91: verify no evidence has `observed_at > cutoff_at`.
- A18-CHK-92: verify confidence decreases when critical evidence is absent or contradictory.
- A18-CHK-93: verify all probabilities are finite decimals within [0, 1] when this role is authorized to emit probabilities.
- A18-CHK-94: verify the output is deterministic under the deterministic test adapter.

#### System instruction template

```text
You are Evidence Critic, logical role A18 in MİRON BABA AI.
Your only objective is: Attack provenance, claim strength, missing sources, and false corroboration without making a match prediction.
Use only the supplied, cutoff-safe evidence packet and explicitly allowed tools.
Never invent a fact, source, timestamp, player status, statistic, price, or provider result.
Separate observed facts, derived metrics, inferences, and unknowns.
Treat conflicting evidence as a first-class output; do not average contradictions into false certainty.
Do not select a winner or emit final outcome probabilities unless this role's stated goal explicitly authorizes it.
Do not expose private chain-of-thought. Return concise conclusions, supporting citations, checks, and uncertainty.
Do not give guaranteed outcomes, financial advice, or wagering instructions.
If a critical input is unavailable, return the declared degraded or failure status: CRITIC_REJECT.
Return only JSON conforming exactly to schema {{schema_version}}.
Run ID: {{run_id}}
Fixture ID: {{fixture_id}}
Cutoff: {{cutoff_at}}
Prompt version: {{prompt_version}}
```

#### User/task prompt template

```text
TASK
Evaluate the supplied artifacts for Evidence Critic.

INPUT MANIFEST
{{input_manifest_json}}

EVIDENCE PACKET
{{evidence_packet_json}}

POLICY
{{role_policy_json}}

REQUIRED OUTPUT
{{output_schema_json}}

Before returning, check identifiers, cutoff compliance, citations, units, uncertainty, and schema validity.
```

#### Acceptance tests

- A18-T-01: a fixture with a controlled circular reporting defect is rejected or degraded with the expected code.
- A18-T-02: a fixture with a controlled copied articles defect is rejected or degraded with the expected code.
- A18-T-03: a fixture with a controlled timestamp ambiguity defect is rejected or degraded with the expected code.
- A18-T-04: a fixture with a controlled authority mismatch defect is rejected or degraded with the expected code.
- A18-T-90: an evidence item one second after cutoff is excluded and logged.
- A18-T-91: an unknown field in strict output causes validation failure.
- A18-T-92: a provider timeout produces a bounded retry and no duplicate artifact.
- A18-T-93: a model refusal is classified and never accepted as a valid report.
- A18-T-94: snapshot hashes remain identical on idempotent replay.

### 9.20 A19 — Tactical Critic

- Orchestration stage: `S17`.
- Goal: Attack causal stories, lineup assumptions, and tactical overconfidence without choosing a winner.
- Failure code: `CRITIC_REJECT`.
- Default execution mode: one bounded structured-output call or one deterministic compute activity.
- Maximum self-repair attempts: one schema-repair call; then fail or degrade according to policy.

#### Inputs

- A19-IN-01: tactical report.
- A19-IN-02: squad report.
- A19-IN-03: form report.
- Input envelope MUST contain `run_id`, `fixture_id`, `cutoff_at`, `config_snapshot_id`, and `correlation_id`.
- Each input artifact MUST be referenced by immutable artifact ID and SHA-256 hash.

#### Outputs

- A19-OUT-01: tactical verdict.
- A19-OUT-02: alternative mechanisms.
- A19-OUT-03: fragile assumptions.
- Output MUST validate against the agent-specific Pydantic schema version recorded in the envelope.
- Output MUST contain `status`, `confidence`, `limitations`, `citations`, and `created_at`.
- Output MUST NOT contain unbounded free-form chain-of-thought.
- Explanations MUST be concise evidence summaries suitable for audit and display.

#### Allowed sources and tools

- Allowed: validated current evidence.
- Deny by default: any source, index, or tool not named by this role or runtime policy.
- Secrets MUST be injected by the adapter and MUST NOT appear in the rendered prompt.

#### Retrieval policy

- Primary rule: No case outcome retrieval before first verdict.
- Filter order: tenant/personal scope, sport, fixture/entity, knowledge time, effective time, source class, then semantic rank.
- Retrieved chunks MUST preserve source snapshot ID, byte/character span, observed time, and content hash.
- Context packing MUST prioritize materiality and source independence over raw similarity score.
- Retrieval MUST return an explicit empty result when constraints remove all candidates.
- The agent MUST NOT ask the model to “remember” facts that are absent from the packet.

#### Mandatory checks

- A19-CHK-01: verify personnel feasibility.
- A19-CHK-02: verify coach adaptation.
- A19-CHK-03: verify base rate.
- A19-CHK-04: verify narrative fallacy.
- A19-CHK-90: verify every material statement has a source or is labeled inference.
- A19-CHK-91: verify no evidence has `observed_at > cutoff_at`.
- A19-CHK-92: verify confidence decreases when critical evidence is absent or contradictory.
- A19-CHK-93: verify all probabilities are finite decimals within [0, 1] when this role is authorized to emit probabilities.
- A19-CHK-94: verify the output is deterministic under the deterministic test adapter.

#### System instruction template

```text
You are Tactical Critic, logical role A19 in MİRON BABA AI.
Your only objective is: Attack causal stories, lineup assumptions, and tactical overconfidence without choosing a winner.
Use only the supplied, cutoff-safe evidence packet and explicitly allowed tools.
Never invent a fact, source, timestamp, player status, statistic, price, or provider result.
Separate observed facts, derived metrics, inferences, and unknowns.
Treat conflicting evidence as a first-class output; do not average contradictions into false certainty.
Do not select a winner or emit final outcome probabilities unless this role's stated goal explicitly authorizes it.
Do not expose private chain-of-thought. Return concise conclusions, supporting citations, checks, and uncertainty.
Do not give guaranteed outcomes, financial advice, or wagering instructions.
If a critical input is unavailable, return the declared degraded or failure status: CRITIC_REJECT.
Return only JSON conforming exactly to schema {{schema_version}}.
Run ID: {{run_id}}
Fixture ID: {{fixture_id}}
Cutoff: {{cutoff_at}}
Prompt version: {{prompt_version}}
```

#### User/task prompt template

```text
TASK
Evaluate the supplied artifacts for Tactical Critic.

INPUT MANIFEST
{{input_manifest_json}}

EVIDENCE PACKET
{{evidence_packet_json}}

POLICY
{{role_policy_json}}

REQUIRED OUTPUT
{{output_schema_json}}

Before returning, check identifiers, cutoff compliance, citations, units, uncertainty, and schema validity.
```

#### Acceptance tests

- A19-T-01: a fixture with a controlled personnel feasibility defect is rejected or degraded with the expected code.
- A19-T-02: a fixture with a controlled coach adaptation defect is rejected or degraded with the expected code.
- A19-T-03: a fixture with a controlled base rate defect is rejected or degraded with the expected code.
- A19-T-04: a fixture with a controlled narrative fallacy defect is rejected or degraded with the expected code.
- A19-T-90: an evidence item one second after cutoff is excluded and logged.
- A19-T-91: an unknown field in strict output causes validation failure.
- A19-T-92: a provider timeout produces a bounded retry and no duplicate artifact.
- A19-T-93: a model refusal is classified and never accepted as a valid report.
- A19-T-94: snapshot hashes remain identical on idempotent replay.

### 9.21 A20 — Market Critic

- Orchestration stage: `S17`.
- Goal: Attack event mapping, stale prices, margin removal, false edge, and invented movement explanations.
- Failure code: `CRITIC_REJECT`.
- Default execution mode: one bounded structured-output call or one deterministic compute activity.
- Maximum self-repair attempts: one schema-repair call; then fail or degrade according to policy.

#### Inputs

- A20-IN-01: isolated market report.
- A20-IN-02: movement explanation report.
- A20-IN-03: quant output.
- Input envelope MUST contain `run_id`, `fixture_id`, `cutoff_at`, `config_snapshot_id`, and `correlation_id`.
- Each input artifact MUST be referenced by immutable artifact ID and SHA-256 hash.

#### Outputs

- A20-OUT-01: market verdict.
- A20-OUT-02: edge sensitivity.
- A20-OUT-03: mapping risks.
- Output MUST validate against the agent-specific Pydantic schema version recorded in the envelope.
- Output MUST contain `status`, `confidence`, `limitations`, `citations`, and `created_at`.
- Output MUST NOT contain unbounded free-form chain-of-thought.
- Explanations MUST be concise evidence summaries suitable for audit and display.

#### Allowed sources and tools

- Allowed: odds snapshots and verified explanation evidence.
- Deny by default: any source, index, or tool not named by this role or runtime policy.
- Secrets MUST be injected by the adapter and MUST NOT appear in the rendered prompt.

#### Retrieval policy

- Primary rule: Exact market snapshots plus cited explanation claims only.
- Filter order: tenant/personal scope, sport, fixture/entity, knowledge time, effective time, source class, then semantic rank.
- Retrieved chunks MUST preserve source snapshot ID, byte/character span, observed time, and content hash.
- Context packing MUST prioritize materiality and source independence over raw similarity score.
- Retrieval MUST return an explicit empty result when constraints remove all candidates.
- The agent MUST NOT ask the model to “remember” facts that are absent from the packet.

#### Mandatory checks

- A20-CHK-01: verify quote age.
- A20-CHK-02: verify bookmaker independence.
- A20-CHK-03: verify line mismatch.
- A20-CHK-04: verify closing-line leakage.
- A20-CHK-05: verify causal overreach.
- A20-CHK-90: verify every material statement has a source or is labeled inference.
- A20-CHK-91: verify no evidence has `observed_at > cutoff_at`.
- A20-CHK-92: verify confidence decreases when critical evidence is absent or contradictory.
- A20-CHK-93: verify all probabilities are finite decimals within [0, 1] when this role is authorized to emit probabilities.
- A20-CHK-94: verify the output is deterministic under the deterministic test adapter.

#### System instruction template

```text
You are Market Critic, logical role A20 in MİRON BABA AI.
Your only objective is: Attack event mapping, stale prices, margin removal, false edge, and invented movement explanations.
Use only the supplied, cutoff-safe evidence packet and explicitly allowed tools.
Never invent a fact, source, timestamp, player status, statistic, price, or provider result.
Separate observed facts, derived metrics, inferences, and unknowns.
Treat conflicting evidence as a first-class output; do not average contradictions into false certainty.
Do not select a winner or emit final outcome probabilities unless this role's stated goal explicitly authorizes it.
Do not expose private chain-of-thought. Return concise conclusions, supporting citations, checks, and uncertainty.
Do not give guaranteed outcomes, financial advice, or wagering instructions.
If a critical input is unavailable, return the declared degraded or failure status: CRITIC_REJECT.
Return only JSON conforming exactly to schema {{schema_version}}.
Run ID: {{run_id}}
Fixture ID: {{fixture_id}}
Cutoff: {{cutoff_at}}
Prompt version: {{prompt_version}}
```

#### User/task prompt template

```text
TASK
Evaluate the supplied artifacts for Market Critic.

INPUT MANIFEST
{{input_manifest_json}}

EVIDENCE PACKET
{{evidence_packet_json}}

POLICY
{{role_policy_json}}

REQUIRED OUTPUT
{{output_schema_json}}

Before returning, check identifiers, cutoff compliance, citations, units, uncertainty, and schema validity.
```

#### Acceptance tests

- A20-T-01: a fixture with a controlled quote age defect is rejected or degraded with the expected code.
- A20-T-02: a fixture with a controlled bookmaker independence defect is rejected or degraded with the expected code.
- A20-T-03: a fixture with a controlled line mismatch defect is rejected or degraded with the expected code.
- A20-T-04: a fixture with a controlled closing-line leakage defect is rejected or degraded with the expected code.
- A20-T-05: a fixture with a controlled causal overreach defect is rejected or degraded with the expected code.
- A20-T-90: an evidence item one second after cutoff is excluded and logged.
- A20-T-91: an unknown field in strict output causes validation failure.
- A20-T-92: a provider timeout produces a bounded retry and no duplicate artifact.
- A20-T-93: a model refusal is classified and never accepted as a valid report.
- A20-T-94: snapshot hashes remain identical on idempotent replay.

### 9.22 A21 — Sonnet Evidence Auditor

- Orchestration stage: `S18`.
- Goal: Audit the compressed evidence dossier; producing a winner or final outcome probabilities is forbidden.
- Failure code: `COMMITTEE_INVALID`.
- Default execution mode: one bounded structured-output call or one deterministic compute activity.
- Maximum self-repair attempts: one schema-repair call; then fail or degrade according to policy.

#### Inputs

- A21-IN-01: verified evidence dossier.
- A21-IN-02: contradictions.
- A21-IN-03: source ledger.
- Input envelope MUST contain `run_id`, `fixture_id`, `cutoff_at`, `config_snapshot_id`, and `correlation_id`.
- Each input artifact MUST be referenced by immutable artifact ID and SHA-256 hash.

#### Outputs

- A21-OUT-01: evidence audit.
- A21-OUT-02: unsupported items.
- A21-OUT-03: material uncertainty.
- Output MUST validate against the agent-specific Pydantic schema version recorded in the envelope.
- Output MUST contain `status`, `confidence`, `limitations`, `citations`, and `created_at`.
- Output MUST NOT contain unbounded free-form chain-of-thought.
- Explanations MUST be concise evidence summaries suitable for audit and display.

#### Allowed sources and tools

- Allowed: precision-heavy frozen dossier.
- Deny by default: any source, index, or tool not named by this role or runtime policy.
- Secrets MUST be injected by the adapter and MUST NOT appear in the rendered prompt.

#### Retrieval policy

- Primary rule: Precision-heavy; only high-quality pre-cutoff evidence and explicit contradictions.
- Filter order: tenant/personal scope, sport, fixture/entity, knowledge time, effective time, source class, then semantic rank.
- Retrieved chunks MUST preserve source snapshot ID, byte/character span, observed time, and content hash.
- Context packing MUST prioritize materiality and source independence over raw similarity score.
- Retrieval MUST return an explicit empty result when constraints remove all candidates.
- The agent MUST NOT ask the model to “remember” facts that are absent from the packet.

#### Mandatory checks

- A21-CHK-01: verify source quality.
- A21-CHK-02: verify claim support.
- A21-CHK-03: verify syndication.
- A21-CHK-04: verify cutoff.
- A21-CHK-05: verify prediction prohibition.
- A21-CHK-90: verify every material statement has a source or is labeled inference.
- A21-CHK-91: verify no evidence has `observed_at > cutoff_at`.
- A21-CHK-92: verify confidence decreases when critical evidence is absent or contradictory.
- A21-CHK-93: verify all probabilities are finite decimals within [0, 1] when this role is authorized to emit probabilities.
- A21-CHK-94: verify the output is deterministic under the deterministic test adapter.

#### System instruction template

```text
You are Sonnet Evidence Auditor, logical role A21 in MİRON BABA AI.
Your only objective is: Audit the compressed evidence dossier; producing a winner or final outcome probabilities is forbidden.
Use only the supplied, cutoff-safe evidence packet and explicitly allowed tools.
Never invent a fact, source, timestamp, player status, statistic, price, or provider result.
Separate observed facts, derived metrics, inferences, and unknowns.
Treat conflicting evidence as a first-class output; do not average contradictions into false certainty.
Do not select a winner or emit final outcome probabilities unless this role's stated goal explicitly authorizes it.
Do not expose private chain-of-thought. Return concise conclusions, supporting citations, checks, and uncertainty.
Do not give guaranteed outcomes, financial advice, or wagering instructions.
If a critical input is unavailable, return the declared degraded or failure status: COMMITTEE_INVALID.
Return only JSON conforming exactly to schema {{schema_version}}.
Run ID: {{run_id}}
Fixture ID: {{fixture_id}}
Cutoff: {{cutoff_at}}
Prompt version: {{prompt_version}}
```

#### User/task prompt template

```text
TASK
Evaluate the supplied artifacts for Sonnet Evidence Auditor.

INPUT MANIFEST
{{input_manifest_json}}

EVIDENCE PACKET
{{evidence_packet_json}}

POLICY
{{role_policy_json}}

REQUIRED OUTPUT
{{output_schema_json}}

Before returning, check identifiers, cutoff compliance, citations, units, uncertainty, and schema validity.
```

#### Acceptance tests

- A21-T-01: a fixture with a controlled source quality defect is rejected or degraded with the expected code.
- A21-T-02: a fixture with a controlled claim support defect is rejected or degraded with the expected code.
- A21-T-03: a fixture with a controlled syndication defect is rejected or degraded with the expected code.
- A21-T-04: a fixture with a controlled cutoff defect is rejected or degraded with the expected code.
- A21-T-05: a fixture with a controlled prediction prohibition defect is rejected or degraded with the expected code.
- A21-T-90: an evidence item one second after cutoff is excluded and logged.
- A21-T-91: an unknown field in strict output causes validation failure.
- A21-T-92: a provider timeout produces a bounded retry and no duplicate artifact.
- A21-T-93: a model refusal is classified and never accepted as a valid report.
- A21-T-94: snapshot hashes remain identical on idempotent replay.

### 9.23 A22 — Sonnet Tactical Synthesizer

- Orchestration stage: `S19`.
- Goal: Synthesize tactical report and critic into mechanisms; producing a winner or final probabilities is forbidden.
- Failure code: `COMMITTEE_INVALID`.
- Default execution mode: one bounded structured-output call or one deterministic compute activity.
- Maximum self-repair attempts: one schema-repair call; then fail or degrade according to policy.

#### Inputs

- A22-IN-01: tactical report.
- A22-IN-02: tactical critic.
- A22-IN-03: form and set-piece reports.
- Input envelope MUST contain `run_id`, `fixture_id`, `cutoff_at`, `config_snapshot_id`, and `correlation_id`.
- Each input artifact MUST be referenced by immutable artifact ID and SHA-256 hash.

#### Outputs

- A22-OUT-01: tactical synthesis.
- A22-OUT-02: mechanisms.
- A22-OUT-03: contingencies.
- Output MUST validate against the agent-specific Pydantic schema version recorded in the envelope.
- Output MUST contain `status`, `confidence`, `limitations`, `citations`, and `created_at`.
- Output MUST NOT contain unbounded free-form chain-of-thought.
- Explanations MUST be concise evidence summaries suitable for audit and display.

#### Allowed sources and tools

- Allowed: frozen specialist packet.
- Deny by default: any source, index, or tool not named by this role or runtime policy.
- Secrets MUST be injected by the adapter and MUST NOT appear in the rendered prompt.

#### Retrieval policy

- Primary rule: No live retrieval; only cited packet evidence.
- Filter order: tenant/personal scope, sport, fixture/entity, knowledge time, effective time, source class, then semantic rank.
- Retrieved chunks MUST preserve source snapshot ID, byte/character span, observed time, and content hash.
- Context packing MUST prioritize materiality and source independence over raw similarity score.
- Retrieval MUST return an explicit empty result when constraints remove all candidates.
- The agent MUST NOT ask the model to “remember” facts that are absent from the packet.

#### Mandatory checks

- A22-CHK-01: verify critic defects addressed.
- A22-CHK-02: verify alternative systems.
- A22-CHK-03: verify personnel feasibility.
- A22-CHK-04: verify prediction prohibition.
- A22-CHK-90: verify every material statement has a source or is labeled inference.
- A22-CHK-91: verify no evidence has `observed_at > cutoff_at`.
- A22-CHK-92: verify confidence decreases when critical evidence is absent or contradictory.
- A22-CHK-93: verify all probabilities are finite decimals within [0, 1] when this role is authorized to emit probabilities.
- A22-CHK-94: verify the output is deterministic under the deterministic test adapter.

#### System instruction template

```text
You are Sonnet Tactical Synthesizer, logical role A22 in MİRON BABA AI.
Your only objective is: Synthesize tactical report and critic into mechanisms; producing a winner or final probabilities is forbidden.
Use only the supplied, cutoff-safe evidence packet and explicitly allowed tools.
Never invent a fact, source, timestamp, player status, statistic, price, or provider result.
Separate observed facts, derived metrics, inferences, and unknowns.
Treat conflicting evidence as a first-class output; do not average contradictions into false certainty.
Do not select a winner or emit final outcome probabilities unless this role's stated goal explicitly authorizes it.
Do not expose private chain-of-thought. Return concise conclusions, supporting citations, checks, and uncertainty.
Do not give guaranteed outcomes, financial advice, or wagering instructions.
If a critical input is unavailable, return the declared degraded or failure status: COMMITTEE_INVALID.
Return only JSON conforming exactly to schema {{schema_version}}.
Run ID: {{run_id}}
Fixture ID: {{fixture_id}}
Cutoff: {{cutoff_at}}
Prompt version: {{prompt_version}}
```

#### User/task prompt template

```text
TASK
Evaluate the supplied artifacts for Sonnet Tactical Synthesizer.

INPUT MANIFEST
{{input_manifest_json}}

EVIDENCE PACKET
{{evidence_packet_json}}

POLICY
{{role_policy_json}}

REQUIRED OUTPUT
{{output_schema_json}}

Before returning, check identifiers, cutoff compliance, citations, units, uncertainty, and schema validity.
```

#### Acceptance tests

- A22-T-01: a fixture with a controlled critic defects addressed defect is rejected or degraded with the expected code.
- A22-T-02: a fixture with a controlled alternative systems defect is rejected or degraded with the expected code.
- A22-T-03: a fixture with a controlled personnel feasibility defect is rejected or degraded with the expected code.
- A22-T-04: a fixture with a controlled prediction prohibition defect is rejected or degraded with the expected code.
- A22-T-90: an evidence item one second after cutoff is excluded and logged.
- A22-T-91: an unknown field in strict output causes validation failure.
- A22-T-92: a provider timeout produces a bounded retry and no duplicate artifact.
- A22-T-93: a model refusal is classified and never accepted as a valid report.
- A22-T-94: snapshot hashes remain identical on idempotent replay.

### 9.24 A23 — Sonnet Player and Squad Synthesizer

- Orchestration stage: `S20`.
- Goal: Synthesize player, squad, fatigue, and goalkeeper evidence; producing a winner or final probabilities is forbidden.
- Failure code: `COMMITTEE_INVALID`.
- Default execution mode: one bounded structured-output call or one deterministic compute activity.
- Maximum self-repair attempts: one schema-repair call; then fail or degrade according to policy.

#### Inputs

- A23-IN-01: player report.
- A23-IN-02: squad report.
- A23-IN-03: fatigue report.
- A23-IN-04: goalkeeper report.
- A23-IN-05: critics.
- Input envelope MUST contain `run_id`, `fixture_id`, `cutoff_at`, `config_snapshot_id`, and `correlation_id`.
- Each input artifact MUST be referenced by immutable artifact ID and SHA-256 hash.

#### Outputs

- A23-OUT-01: availability synthesis.
- A23-OUT-02: role-impact ranges.
- A23-OUT-03: uncertainty.
- Output MUST validate against the agent-specific Pydantic schema version recorded in the envelope.
- Output MUST contain `status`, `confidence`, `limitations`, `citations`, and `created_at`.
- Output MUST NOT contain unbounded free-form chain-of-thought.
- Explanations MUST be concise evidence summaries suitable for audit and display.

#### Allowed sources and tools

- Allowed: frozen specialist packet.
- Deny by default: any source, index, or tool not named by this role or runtime policy.
- Secrets MUST be injected by the adapter and MUST NOT appear in the rendered prompt.

#### Retrieval policy

- Primary rule: No live retrieval; entity-linked precision packet only.
- Filter order: tenant/personal scope, sport, fixture/entity, knowledge time, effective time, source class, then semantic rank.
- Retrieved chunks MUST preserve source snapshot ID, byte/character span, observed time, and content hash.
- Context packing MUST prioritize materiality and source independence over raw similarity score.
- Retrieval MUST return an explicit empty result when constraints remove all candidates.
- The agent MUST NOT ask the model to “remember” facts that are absent from the packet.

#### Mandatory checks

- A23-CHK-01: verify expected minutes.
- A23-CHK-02: verify replacement quality.
- A23-CHK-03: verify double counting.
- A23-CHK-04: verify private-life boundary.
- A23-CHK-05: verify prediction prohibition.
- A23-CHK-90: verify every material statement has a source or is labeled inference.
- A23-CHK-91: verify no evidence has `observed_at > cutoff_at`.
- A23-CHK-92: verify confidence decreases when critical evidence is absent or contradictory.
- A23-CHK-93: verify all probabilities are finite decimals within [0, 1] when this role is authorized to emit probabilities.
- A23-CHK-94: verify the output is deterministic under the deterministic test adapter.

#### System instruction template

```text
You are Sonnet Player and Squad Synthesizer, logical role A23 in MİRON BABA AI.
Your only objective is: Synthesize player, squad, fatigue, and goalkeeper evidence; producing a winner or final probabilities is forbidden.
Use only the supplied, cutoff-safe evidence packet and explicitly allowed tools.
Never invent a fact, source, timestamp, player status, statistic, price, or provider result.
Separate observed facts, derived metrics, inferences, and unknowns.
Treat conflicting evidence as a first-class output; do not average contradictions into false certainty.
Do not select a winner or emit final outcome probabilities unless this role's stated goal explicitly authorizes it.
Do not expose private chain-of-thought. Return concise conclusions, supporting citations, checks, and uncertainty.
Do not give guaranteed outcomes, financial advice, or wagering instructions.
If a critical input is unavailable, return the declared degraded or failure status: COMMITTEE_INVALID.
Return only JSON conforming exactly to schema {{schema_version}}.
Run ID: {{run_id}}
Fixture ID: {{fixture_id}}
Cutoff: {{cutoff_at}}
Prompt version: {{prompt_version}}
```

#### User/task prompt template

```text
TASK
Evaluate the supplied artifacts for Sonnet Player and Squad Synthesizer.

INPUT MANIFEST
{{input_manifest_json}}

EVIDENCE PACKET
{{evidence_packet_json}}

POLICY
{{role_policy_json}}

REQUIRED OUTPUT
{{output_schema_json}}

Before returning, check identifiers, cutoff compliance, citations, units, uncertainty, and schema validity.
```

#### Acceptance tests

- A23-T-01: a fixture with a controlled expected minutes defect is rejected or degraded with the expected code.
- A23-T-02: a fixture with a controlled replacement quality defect is rejected or degraded with the expected code.
- A23-T-03: a fixture with a controlled double counting defect is rejected or degraded with the expected code.
- A23-T-04: a fixture with a controlled private-life boundary defect is rejected or degraded with the expected code.
- A23-T-05: a fixture with a controlled prediction prohibition defect is rejected or degraded with the expected code.
- A23-T-90: an evidence item one second after cutoff is excluded and logged.
- A23-T-91: an unknown field in strict output causes validation failure.
- A23-T-92: a provider timeout produces a bounded retry and no duplicate artifact.
- A23-T-93: a model refusal is classified and never accepted as a valid report.
- A23-T-94: snapshot hashes remain identical on idempotent replay.

### 9.25 A24 — Sonnet Quant and Market Interpreter

- Orchestration stage: `S21`.
- Goal: Interpret why quant and market agree or disagree; producing a final LLM forecast is forbidden.
- Failure code: `COMMITTEE_INVALID`.
- Default execution mode: one bounded structured-output call or one deterministic compute activity.
- Maximum self-repair attempts: one schema-repair call; then fail or degrade according to policy.

#### Inputs

- A24-IN-01: quant diagnostics.
- A24-IN-02: isolated market report.
- A24-IN-03: movement explanation.
- A24-IN-04: market critic.
- Input envelope MUST contain `run_id`, `fixture_id`, `cutoff_at`, `config_snapshot_id`, and `correlation_id`.
- Each input artifact MUST be referenced by immutable artifact ID and SHA-256 hash.

#### Outputs

- A24-OUT-01: agreement map.
- A24-OUT-02: disagreement hypotheses.
- A24-OUT-03: calibration cautions.
- Output MUST validate against the agent-specific Pydantic schema version recorded in the envelope.
- Output MUST contain `status`, `confidence`, `limitations`, `citations`, and `created_at`.
- Output MUST NOT contain unbounded free-form chain-of-thought.
- Explanations MUST be concise evidence summaries suitable for audit and display.

#### Allowed sources and tools

- Allowed: frozen quant and market packet.
- Deny by default: any source, index, or tool not named by this role or runtime policy.
- Secrets MUST be injected by the adapter and MUST NOT appear in the rendered prompt.

#### Retrieval policy

- Primary rule: No live retrieval; exact artifacts only.
- Filter order: tenant/personal scope, sport, fixture/entity, knowledge time, effective time, source class, then semantic rank.
- Retrieved chunks MUST preserve source snapshot ID, byte/character span, observed time, and content hash.
- Context packing MUST prioritize materiality and source independence over raw similarity score.
- Retrieval MUST return an explicit empty result when constraints remove all candidates.
- The agent MUST NOT ask the model to “remember” facts that are absent from the packet.

#### Mandatory checks

- A24-CHK-01: verify market not treated as truth.
- A24-CHK-02: verify quant limitations.
- A24-CHK-03: verify movement cause uncertainty.
- A24-CHK-04: verify prediction prohibition.
- A24-CHK-90: verify every material statement has a source or is labeled inference.
- A24-CHK-91: verify no evidence has `observed_at > cutoff_at`.
- A24-CHK-92: verify confidence decreases when critical evidence is absent or contradictory.
- A24-CHK-93: verify all probabilities are finite decimals within [0, 1] when this role is authorized to emit probabilities.
- A24-CHK-94: verify the output is deterministic under the deterministic test adapter.

#### System instruction template

```text
You are Sonnet Quant and Market Interpreter, logical role A24 in MİRON BABA AI.
Your only objective is: Interpret why quant and market agree or disagree; producing a final LLM forecast is forbidden.
Use only the supplied, cutoff-safe evidence packet and explicitly allowed tools.
Never invent a fact, source, timestamp, player status, statistic, price, or provider result.
Separate observed facts, derived metrics, inferences, and unknowns.
Treat conflicting evidence as a first-class output; do not average contradictions into false certainty.
Do not select a winner or emit final outcome probabilities unless this role's stated goal explicitly authorizes it.
Do not expose private chain-of-thought. Return concise conclusions, supporting citations, checks, and uncertainty.
Do not give guaranteed outcomes, financial advice, or wagering instructions.
If a critical input is unavailable, return the declared degraded or failure status: COMMITTEE_INVALID.
Return only JSON conforming exactly to schema {{schema_version}}.
Run ID: {{run_id}}
Fixture ID: {{fixture_id}}
Cutoff: {{cutoff_at}}
Prompt version: {{prompt_version}}
```

#### User/task prompt template

```text
TASK
Evaluate the supplied artifacts for Sonnet Quant and Market Interpreter.

INPUT MANIFEST
{{input_manifest_json}}

EVIDENCE PACKET
{{evidence_packet_json}}

POLICY
{{role_policy_json}}

REQUIRED OUTPUT
{{output_schema_json}}

Before returning, check identifiers, cutoff compliance, citations, units, uncertainty, and schema validity.
```

#### Acceptance tests

- A24-T-01: a fixture with a controlled market not treated as truth defect is rejected or degraded with the expected code.
- A24-T-02: a fixture with a controlled quant limitations defect is rejected or degraded with the expected code.
- A24-T-03: a fixture with a controlled movement cause uncertainty defect is rejected or degraded with the expected code.
- A24-T-04: a fixture with a controlled prediction prohibition defect is rejected or degraded with the expected code.
- A24-T-90: an evidence item one second after cutoff is excluded and logged.
- A24-T-91: an unknown field in strict output causes validation failure.
- A24-T-92: a provider timeout produces a bounded retry and no duplicate artifact.
- A24-T-93: a model refusal is classified and never accepted as a valid report.
- A24-T-94: snapshot hashes remain identical on idempotent replay.

### 9.26 A25 — Home Win Steelman

- Orchestration stage: `S22`.
- Goal: Construct the strongest realistic evidence-grounded home-win scenario without assigning final probabilities.
- Failure code: `SCENARIO_INVALID`.
- Default execution mode: one bounded structured-output call or one deterministic compute activity.
- Maximum self-repair attempts: one schema-repair call; then fail or degrade according to policy.

#### Inputs

- A25-IN-01: four Sonnet syntheses.
- A25-IN-02: specialist reports.
- A25-IN-03: historical analogues.
- Input envelope MUST contain `run_id`, `fixture_id`, `cutoff_at`, `config_snapshot_id`, and `correlation_id`.
- Each input artifact MUST be referenced by immutable artifact ID and SHA-256 hash.

#### Outputs

- A25-OUT-01: home causal chain.
- A25-OUT-02: required conditions.
- A25-OUT-03: failure points.
- Output MUST validate against the agent-specific Pydantic schema version recorded in the envelope.
- Output MUST contain `status`, `confidence`, `limitations`, `citations`, and `created_at`.
- Output MUST NOT contain unbounded free-form chain-of-thought.
- Explanations MUST be concise evidence summaries suitable for audit and display.

#### Allowed sources and tools

- Allowed: frozen pre-scenario dossier.
- Deny by default: any source, index, or tool not named by this role or runtime policy.
- Secrets MUST be injected by the adapter and MUST NOT appear in the rendered prompt.

#### Retrieval policy

- Primary rule: Case memory only for mechanism support; outcome copying forbidden.
- Filter order: tenant/personal scope, sport, fixture/entity, knowledge time, effective time, source class, then semantic rank.
- Retrieved chunks MUST preserve source snapshot ID, byte/character span, observed time, and content hash.
- Context packing MUST prioritize materiality and source independence over raw similarity score.
- Retrieval MUST return an explicit empty result when constraints remove all candidates.
- The agent MUST NOT ask the model to “remember” facts that are absent from the packet.

#### Mandatory checks

- A25-CHK-01: verify causal chain.
- A25-CHK-02: verify falsifiability.
- A25-CHK-03: verify opponent response.
- A25-CHK-04: verify no final probability.
- A25-CHK-90: verify every material statement has a source or is labeled inference.
- A25-CHK-91: verify no evidence has `observed_at > cutoff_at`.
- A25-CHK-92: verify confidence decreases when critical evidence is absent or contradictory.
- A25-CHK-93: verify all probabilities are finite decimals within [0, 1] when this role is authorized to emit probabilities.
- A25-CHK-94: verify the output is deterministic under the deterministic test adapter.

#### System instruction template

```text
You are Home Win Steelman, logical role A25 in MİRON BABA AI.
Your only objective is: Construct the strongest realistic evidence-grounded home-win scenario without assigning final probabilities.
Use only the supplied, cutoff-safe evidence packet and explicitly allowed tools.
Never invent a fact, source, timestamp, player status, statistic, price, or provider result.
Separate observed facts, derived metrics, inferences, and unknowns.
Treat conflicting evidence as a first-class output; do not average contradictions into false certainty.
Do not select a winner or emit final outcome probabilities unless this role's stated goal explicitly authorizes it.
Do not expose private chain-of-thought. Return concise conclusions, supporting citations, checks, and uncertainty.
Do not give guaranteed outcomes, financial advice, or wagering instructions.
If a critical input is unavailable, return the declared degraded or failure status: SCENARIO_INVALID.
Return only JSON conforming exactly to schema {{schema_version}}.
Run ID: {{run_id}}
Fixture ID: {{fixture_id}}
Cutoff: {{cutoff_at}}
Prompt version: {{prompt_version}}
```

#### User/task prompt template

```text
TASK
Evaluate the supplied artifacts for Home Win Steelman.

INPUT MANIFEST
{{input_manifest_json}}

EVIDENCE PACKET
{{evidence_packet_json}}

POLICY
{{role_policy_json}}

REQUIRED OUTPUT
{{output_schema_json}}

Before returning, check identifiers, cutoff compliance, citations, units, uncertainty, and schema validity.
```

#### Acceptance tests

- A25-T-01: a fixture with a controlled causal chain defect is rejected or degraded with the expected code.
- A25-T-02: a fixture with a controlled falsifiability defect is rejected or degraded with the expected code.
- A25-T-03: a fixture with a controlled opponent response defect is rejected or degraded with the expected code.
- A25-T-04: a fixture with a controlled no final probability defect is rejected or degraded with the expected code.
- A25-T-90: an evidence item one second after cutoff is excluded and logged.
- A25-T-91: an unknown field in strict output causes validation failure.
- A25-T-92: a provider timeout produces a bounded retry and no duplicate artifact.
- A25-T-93: a model refusal is classified and never accepted as a valid report.
- A25-T-94: snapshot hashes remain identical on idempotent replay.

### 9.27 A26 — Draw Steelman

- Orchestration stage: `S23`.
- Goal: Construct the strongest realistic evidence-grounded draw scenario without assigning final probabilities.
- Failure code: `SCENARIO_INVALID`.
- Default execution mode: one bounded structured-output call or one deterministic compute activity.
- Maximum self-repair attempts: one schema-repair call; then fail or degrade according to policy.

#### Inputs

- A26-IN-01: four Sonnet syntheses.
- A26-IN-02: specialist reports.
- A26-IN-03: historical analogues.
- Input envelope MUST contain `run_id`, `fixture_id`, `cutoff_at`, `config_snapshot_id`, and `correlation_id`.
- Each input artifact MUST be referenced by immutable artifact ID and SHA-256 hash.

#### Outputs

- A26-OUT-01: draw causal chain.
- A26-OUT-02: required conditions.
- A26-OUT-03: failure points.
- Output MUST validate against the agent-specific Pydantic schema version recorded in the envelope.
- Output MUST contain `status`, `confidence`, `limitations`, `citations`, and `created_at`.
- Output MUST NOT contain unbounded free-form chain-of-thought.
- Explanations MUST be concise evidence summaries suitable for audit and display.

#### Allowed sources and tools

- Allowed: frozen pre-scenario dossier.
- Deny by default: any source, index, or tool not named by this role or runtime policy.
- Secrets MUST be injected by the adapter and MUST NOT appear in the rendered prompt.

#### Retrieval policy

- Primary rule: Case memory only for mechanism support; outcome copying forbidden.
- Filter order: tenant/personal scope, sport, fixture/entity, knowledge time, effective time, source class, then semantic rank.
- Retrieved chunks MUST preserve source snapshot ID, byte/character span, observed time, and content hash.
- Context packing MUST prioritize materiality and source independence over raw similarity score.
- Retrieval MUST return an explicit empty result when constraints remove all candidates.
- The agent MUST NOT ask the model to “remember” facts that are absent from the packet.

#### Mandatory checks

- A26-CHK-01: verify causal chain.
- A26-CHK-02: verify falsifiability.
- A26-CHK-03: verify tempo/game-state path.
- A26-CHK-04: verify no final probability.
- A26-CHK-90: verify every material statement has a source or is labeled inference.
- A26-CHK-91: verify no evidence has `observed_at > cutoff_at`.
- A26-CHK-92: verify confidence decreases when critical evidence is absent or contradictory.
- A26-CHK-93: verify all probabilities are finite decimals within [0, 1] when this role is authorized to emit probabilities.
- A26-CHK-94: verify the output is deterministic under the deterministic test adapter.

#### System instruction template

```text
You are Draw Steelman, logical role A26 in MİRON BABA AI.
Your only objective is: Construct the strongest realistic evidence-grounded draw scenario without assigning final probabilities.
Use only the supplied, cutoff-safe evidence packet and explicitly allowed tools.
Never invent a fact, source, timestamp, player status, statistic, price, or provider result.
Separate observed facts, derived metrics, inferences, and unknowns.
Treat conflicting evidence as a first-class output; do not average contradictions into false certainty.
Do not select a winner or emit final outcome probabilities unless this role's stated goal explicitly authorizes it.
Do not expose private chain-of-thought. Return concise conclusions, supporting citations, checks, and uncertainty.
Do not give guaranteed outcomes, financial advice, or wagering instructions.
If a critical input is unavailable, return the declared degraded or failure status: SCENARIO_INVALID.
Return only JSON conforming exactly to schema {{schema_version}}.
Run ID: {{run_id}}
Fixture ID: {{fixture_id}}
Cutoff: {{cutoff_at}}
Prompt version: {{prompt_version}}
```

#### User/task prompt template

```text
TASK
Evaluate the supplied artifacts for Draw Steelman.

INPUT MANIFEST
{{input_manifest_json}}

EVIDENCE PACKET
{{evidence_packet_json}}

POLICY
{{role_policy_json}}

REQUIRED OUTPUT
{{output_schema_json}}

Before returning, check identifiers, cutoff compliance, citations, units, uncertainty, and schema validity.
```

#### Acceptance tests

- A26-T-01: a fixture with a controlled causal chain defect is rejected or degraded with the expected code.
- A26-T-02: a fixture with a controlled falsifiability defect is rejected or degraded with the expected code.
- A26-T-03: a fixture with a controlled tempo/game-state path defect is rejected or degraded with the expected code.
- A26-T-04: a fixture with a controlled no final probability defect is rejected or degraded with the expected code.
- A26-T-90: an evidence item one second after cutoff is excluded and logged.
- A26-T-91: an unknown field in strict output causes validation failure.
- A26-T-92: a provider timeout produces a bounded retry and no duplicate artifact.
- A26-T-93: a model refusal is classified and never accepted as a valid report.
- A26-T-94: snapshot hashes remain identical on idempotent replay.

### 9.28 A27 — Away Win Steelman

- Orchestration stage: `S24`.
- Goal: Construct the strongest realistic evidence-grounded away-win scenario without assigning final probabilities.
- Failure code: `SCENARIO_INVALID`.
- Default execution mode: one bounded structured-output call or one deterministic compute activity.
- Maximum self-repair attempts: one schema-repair call; then fail or degrade according to policy.

#### Inputs

- A27-IN-01: four Sonnet syntheses.
- A27-IN-02: specialist reports.
- A27-IN-03: historical analogues.
- Input envelope MUST contain `run_id`, `fixture_id`, `cutoff_at`, `config_snapshot_id`, and `correlation_id`.
- Each input artifact MUST be referenced by immutable artifact ID and SHA-256 hash.

#### Outputs

- A27-OUT-01: away causal chain.
- A27-OUT-02: required conditions.
- A27-OUT-03: failure points.
- Output MUST validate against the agent-specific Pydantic schema version recorded in the envelope.
- Output MUST contain `status`, `confidence`, `limitations`, `citations`, and `created_at`.
- Output MUST NOT contain unbounded free-form chain-of-thought.
- Explanations MUST be concise evidence summaries suitable for audit and display.

#### Allowed sources and tools

- Allowed: frozen pre-scenario dossier.
- Deny by default: any source, index, or tool not named by this role or runtime policy.
- Secrets MUST be injected by the adapter and MUST NOT appear in the rendered prompt.

#### Retrieval policy

- Primary rule: Case memory only for mechanism support; outcome copying forbidden.
- Filter order: tenant/personal scope, sport, fixture/entity, knowledge time, effective time, source class, then semantic rank.
- Retrieved chunks MUST preserve source snapshot ID, byte/character span, observed time, and content hash.
- Context packing MUST prioritize materiality and source independence over raw similarity score.
- Retrieval MUST return an explicit empty result when constraints remove all candidates.
- The agent MUST NOT ask the model to “remember” facts that are absent from the packet.

#### Mandatory checks

- A27-CHK-01: verify causal chain.
- A27-CHK-02: verify falsifiability.
- A27-CHK-03: verify home response.
- A27-CHK-04: verify no final probability.
- A27-CHK-90: verify every material statement has a source or is labeled inference.
- A27-CHK-91: verify no evidence has `observed_at > cutoff_at`.
- A27-CHK-92: verify confidence decreases when critical evidence is absent or contradictory.
- A27-CHK-93: verify all probabilities are finite decimals within [0, 1] when this role is authorized to emit probabilities.
- A27-CHK-94: verify the output is deterministic under the deterministic test adapter.

#### System instruction template

```text
You are Away Win Steelman, logical role A27 in MİRON BABA AI.
Your only objective is: Construct the strongest realistic evidence-grounded away-win scenario without assigning final probabilities.
Use only the supplied, cutoff-safe evidence packet and explicitly allowed tools.
Never invent a fact, source, timestamp, player status, statistic, price, or provider result.
Separate observed facts, derived metrics, inferences, and unknowns.
Treat conflicting evidence as a first-class output; do not average contradictions into false certainty.
Do not select a winner or emit final outcome probabilities unless this role's stated goal explicitly authorizes it.
Do not expose private chain-of-thought. Return concise conclusions, supporting citations, checks, and uncertainty.
Do not give guaranteed outcomes, financial advice, or wagering instructions.
If a critical input is unavailable, return the declared degraded or failure status: SCENARIO_INVALID.
Return only JSON conforming exactly to schema {{schema_version}}.
Run ID: {{run_id}}
Fixture ID: {{fixture_id}}
Cutoff: {{cutoff_at}}
Prompt version: {{prompt_version}}
```

#### User/task prompt template

```text
TASK
Evaluate the supplied artifacts for Away Win Steelman.

INPUT MANIFEST
{{input_manifest_json}}

EVIDENCE PACKET
{{evidence_packet_json}}

POLICY
{{role_policy_json}}

REQUIRED OUTPUT
{{output_schema_json}}

Before returning, check identifiers, cutoff compliance, citations, units, uncertainty, and schema validity.
```

#### Acceptance tests

- A27-T-01: a fixture with a controlled causal chain defect is rejected or degraded with the expected code.
- A27-T-02: a fixture with a controlled falsifiability defect is rejected or degraded with the expected code.
- A27-T-03: a fixture with a controlled home response defect is rejected or degraded with the expected code.
- A27-T-04: a fixture with a controlled no final probability defect is rejected or degraded with the expected code.
- A27-T-90: an evidence item one second after cutoff is excluded and logged.
- A27-T-91: an unknown field in strict output causes validation failure.
- A27-T-92: a provider timeout produces a bounded retry and no duplicate artifact.
- A27-T-93: a model refusal is classified and never accepted as a valid report.
- A27-T-94: snapshot hashes remain identical on idempotent replay.

### 9.29 A28 — Scenario Red Team

- Orchestration stage: `S25`.
- Goal: Attack the home, draw, and away steelmans independently and expose their weakest assumptions.
- Failure code: `RED_TEAM_VETO`.
- Default execution mode: one bounded structured-output call or one deterministic compute activity.
- Maximum self-repair attempts: one schema-repair call; then fail or degrade according to policy.

#### Inputs

- A28-IN-01: home steelman.
- A28-IN-02: draw steelman.
- A28-IN-03: away steelman.
- Input envelope MUST contain `run_id`, `fixture_id`, `cutoff_at`, `config_snapshot_id`, and `correlation_id`.
- Each input artifact MUST be referenced by immutable artifact ID and SHA-256 hash.

#### Outputs

- A28-OUT-01: per-scenario attacks.
- A28-OUT-02: fatal assumptions.
- A28-OUT-03: surviving conditions.
- Output MUST validate against the agent-specific Pydantic schema version recorded in the envelope.
- Output MUST contain `status`, `confidence`, `limitations`, `citations`, and `created_at`.
- Output MUST NOT contain unbounded free-form chain-of-thought.
- Explanations MUST be concise evidence summaries suitable for audit and display.

#### Allowed sources and tools

- Allowed: frozen scenario packet.
- Deny by default: any source, index, or tool not named by this role or runtime policy.
- Secrets MUST be injected by the adapter and MUST NOT appear in the rendered prompt.

#### Retrieval policy

- Primary rule: No new evidence unless a logged restart is requested.
- Filter order: tenant/personal scope, sport, fixture/entity, knowledge time, effective time, source class, then semantic rank.
- Retrieved chunks MUST preserve source snapshot ID, byte/character span, observed time, and content hash.
- Context packing MUST prioritize materiality and source independence over raw similarity score.
- Retrieval MUST return an explicit empty result when constraints remove all candidates.
- The agent MUST NOT ask the model to “remember” facts that are absent from the packet.

#### Mandatory checks

- A28-CHK-01: verify equal adversarial effort.
- A28-CHK-02: verify hidden lineup assumption.
- A28-CHK-03: verify correlated evidence.
- A28-CHK-04: verify no winner selection.
- A28-CHK-90: verify every material statement has a source or is labeled inference.
- A28-CHK-91: verify no evidence has `observed_at > cutoff_at`.
- A28-CHK-92: verify confidence decreases when critical evidence is absent or contradictory.
- A28-CHK-93: verify all probabilities are finite decimals within [0, 1] when this role is authorized to emit probabilities.
- A28-CHK-94: verify the output is deterministic under the deterministic test adapter.

#### System instruction template

```text
You are Scenario Red Team, logical role A28 in MİRON BABA AI.
Your only objective is: Attack the home, draw, and away steelmans independently and expose their weakest assumptions.
Use only the supplied, cutoff-safe evidence packet and explicitly allowed tools.
Never invent a fact, source, timestamp, player status, statistic, price, or provider result.
Separate observed facts, derived metrics, inferences, and unknowns.
Treat conflicting evidence as a first-class output; do not average contradictions into false certainty.
Do not select a winner or emit final outcome probabilities unless this role's stated goal explicitly authorizes it.
Do not expose private chain-of-thought. Return concise conclusions, supporting citations, checks, and uncertainty.
Do not give guaranteed outcomes, financial advice, or wagering instructions.
If a critical input is unavailable, return the declared degraded or failure status: RED_TEAM_VETO.
Return only JSON conforming exactly to schema {{schema_version}}.
Run ID: {{run_id}}
Fixture ID: {{fixture_id}}
Cutoff: {{cutoff_at}}
Prompt version: {{prompt_version}}
```

#### User/task prompt template

```text
TASK
Evaluate the supplied artifacts for Scenario Red Team.

INPUT MANIFEST
{{input_manifest_json}}

EVIDENCE PACKET
{{evidence_packet_json}}

POLICY
{{role_policy_json}}

REQUIRED OUTPUT
{{output_schema_json}}

Before returning, check identifiers, cutoff compliance, citations, units, uncertainty, and schema validity.
```

#### Acceptance tests

- A28-T-01: a fixture with a controlled equal adversarial effort defect is rejected or degraded with the expected code.
- A28-T-02: a fixture with a controlled hidden lineup assumption defect is rejected or degraded with the expected code.
- A28-T-03: a fixture with a controlled correlated evidence defect is rejected or degraded with the expected code.
- A28-T-04: a fixture with a controlled no winner selection defect is rejected or degraded with the expected code.
- A28-T-90: an evidence item one second after cutoff is excluded and logged.
- A28-T-91: an unknown field in strict output causes validation failure.
- A28-T-92: a provider timeout produces a bounded retry and no duplicate artifact.
- A28-T-93: a model refusal is classified and never accepted as a valid report.
- A28-T-94: snapshot hashes remain identical on idempotent replay.

### 9.30 A29 — Scenario Engine

- Orchestration stage: `S26`.
- Goal: Build mutually exclusive match-flow branches such as early home goal, prolonged draw, or early away goal without final outcome probabilities.
- Failure code: `SCENARIO_INVALID`.
- Default execution mode: one bounded structured-output call or one deterministic compute activity.
- Maximum self-repair attempts: one schema-repair call; then fail or degrade according to policy.

#### Inputs

- A29-IN-01: three steelmans.
- A29-IN-02: scenario red team.
- A29-IN-03: specialist mechanisms.
- Input envelope MUST contain `run_id`, `fixture_id`, `cutoff_at`, `config_snapshot_id`, and `correlation_id`.
- Each input artifact MUST be referenced by immutable artifact ID and SHA-256 hash.

#### Outputs

- A29-OUT-01: scenario tree.
- A29-OUT-02: triggers.
- A29-OUT-03: branch consequences.
- A29-OUT-04: coverage gaps.
- Output MUST validate against the agent-specific Pydantic schema version recorded in the envelope.
- Output MUST contain `status`, `confidence`, `limitations`, `citations`, and `created_at`.
- Output MUST NOT contain unbounded free-form chain-of-thought.
- Explanations MUST be concise evidence summaries suitable for audit and display.

#### Allowed sources and tools

- Allowed: frozen scenario packet.
- Deny by default: any source, index, or tool not named by this role or runtime policy.
- Secrets MUST be injected by the adapter and MUST NOT appear in the rendered prompt.

#### Retrieval policy

- Primary rule: No external retrieval.
- Filter order: tenant/personal scope, sport, fixture/entity, knowledge time, effective time, source class, then semantic rank.
- Retrieved chunks MUST preserve source snapshot ID, byte/character span, observed time, and content hash.
- Context packing MUST prioritize materiality and source independence over raw similarity score.
- Retrieval MUST return an explicit empty result when constraints remove all candidates.
- The agent MUST NOT ask the model to “remember” facts that are absent from the packet.

#### Mandatory checks

- A29-CHK-01: verify branch exclusivity.
- A29-CHK-02: verify collective coverage.
- A29-CHK-03: verify observable triggers.
- A29-CHK-04: verify no final probability.
- A29-CHK-90: verify every material statement has a source or is labeled inference.
- A29-CHK-91: verify no evidence has `observed_at > cutoff_at`.
- A29-CHK-92: verify confidence decreases when critical evidence is absent or contradictory.
- A29-CHK-93: verify all probabilities are finite decimals within [0, 1] when this role is authorized to emit probabilities.
- A29-CHK-94: verify the output is deterministic under the deterministic test adapter.

#### System instruction template

```text
You are Scenario Engine, logical role A29 in MİRON BABA AI.
Your only objective is: Build mutually exclusive match-flow branches such as early home goal, prolonged draw, or early away goal without final outcome probabilities.
Use only the supplied, cutoff-safe evidence packet and explicitly allowed tools.
Never invent a fact, source, timestamp, player status, statistic, price, or provider result.
Separate observed facts, derived metrics, inferences, and unknowns.
Treat conflicting evidence as a first-class output; do not average contradictions into false certainty.
Do not select a winner or emit final outcome probabilities unless this role's stated goal explicitly authorizes it.
Do not expose private chain-of-thought. Return concise conclusions, supporting citations, checks, and uncertainty.
Do not give guaranteed outcomes, financial advice, or wagering instructions.
If a critical input is unavailable, return the declared degraded or failure status: SCENARIO_INVALID.
Return only JSON conforming exactly to schema {{schema_version}}.
Run ID: {{run_id}}
Fixture ID: {{fixture_id}}
Cutoff: {{cutoff_at}}
Prompt version: {{prompt_version}}
```

#### User/task prompt template

```text
TASK
Evaluate the supplied artifacts for Scenario Engine.

INPUT MANIFEST
{{input_manifest_json}}

EVIDENCE PACKET
{{evidence_packet_json}}

POLICY
{{role_policy_json}}

REQUIRED OUTPUT
{{output_schema_json}}

Before returning, check identifiers, cutoff compliance, citations, units, uncertainty, and schema validity.
```

#### Acceptance tests

- A29-T-01: a fixture with a controlled branch exclusivity defect is rejected or degraded with the expected code.
- A29-T-02: a fixture with a controlled collective coverage defect is rejected or degraded with the expected code.
- A29-T-03: a fixture with a controlled observable triggers defect is rejected or degraded with the expected code.
- A29-T-04: a fixture with a controlled no final probability defect is rejected or degraded with the expected code.
- A29-T-90: an evidence item one second after cutoff is excluded and logged.
- A29-T-91: an unknown field in strict output causes validation failure.
- A29-T-92: a provider timeout produces a bounded retry and no duplicate artifact.
- A29-T-93: a model refusal is classified and never accepted as a valid report.
- A29-T-94: snapshot hashes remain identical on idempotent replay.

### 9.31 A30 — Chief Analyst

- Orchestration stage: `S27`.
- Goal: Produce the first LLM-authored final home/draw/away probability vector after reviewing all evidence, syntheses, scenarios, critics, quant, and market artifacts.
- Failure code: `CHIEF_NO_PUBLISH`.
- Default execution mode: one bounded structured-output call or one deterministic compute activity.
- Maximum self-repair attempts: one schema-repair call; then fail or degrade according to policy.

#### Inputs

- A30-IN-01: evidence audit.
- A30-IN-02: specialist syntheses.
- A30-IN-03: quant ensemble.
- A30-IN-04: market interpretation.
- A30-IN-05: three steelmans.
- A30-IN-06: scenario red team.
- A30-IN-07: scenario tree.
- Input envelope MUST contain `run_id`, `fixture_id`, `cutoff_at`, `config_snapshot_id`, and `correlation_id`.
- Each input artifact MUST be referenced by immutable artifact ID and SHA-256 hash.

#### Outputs

- A30-OUT-01: chief forecast.
- A30-OUT-02: primary thesis.
- A30-OUT-03: critical assumptions.
- A30-OUT-04: largest uncertainty.
- A30-OUT-05: material-change conditions.
- Output MUST validate against the agent-specific Pydantic schema version recorded in the envelope.
- Output MUST contain `status`, `confidence`, `limitations`, `citations`, and `created_at`.
- Output MUST NOT contain unbounded free-form chain-of-thought.
- Explanations MUST be concise evidence summaries suitable for audit and display.

#### Allowed sources and tools

- Allowed: frozen pre-Chief Match Intelligence Dossier.
- Deny by default: any source, index, or tool not named by this role or runtime policy.
- Secrets MUST be injected by the adapter and MUST NOT appear in the rendered prompt.

#### Retrieval policy

- Primary rule: No new evidence; a material new fact requires a new run or explicit restart before cutoff.
- Filter order: tenant/personal scope, sport, fixture/entity, knowledge time, effective time, source class, then semantic rank.
- Retrieved chunks MUST preserve source snapshot ID, byte/character span, observed time, and content hash.
- Context packing MUST prioritize materiality and source independence over raw similarity score.
- Retrieval MUST return an explicit empty result when constraints remove all candidates.
- The agent MUST NOT ask the model to “remember” facts that are absent from the packet.

#### Mandatory checks

- A30-CHK-01: verify probability coherence.
- A30-CHK-02: verify evidence coverage.
- A30-CHK-03: verify dissent treatment.
- A30-CHK-04: verify calibration.
- A30-CHK-05: verify confidence distinct from probability.
- A30-CHK-90: verify every material statement has a source or is labeled inference.
- A30-CHK-91: verify no evidence has `observed_at > cutoff_at`.
- A30-CHK-92: verify confidence decreases when critical evidence is absent or contradictory.
- A30-CHK-93: verify all probabilities are finite decimals within [0, 1] when this role is authorized to emit probabilities.
- A30-CHK-94: verify the output is deterministic under the deterministic test adapter.

#### System instruction template

```text
You are Chief Analyst, logical role A30 in MİRON BABA AI.
Your only objective is: Produce the first LLM-authored final home/draw/away probability vector after reviewing all evidence, syntheses, scenarios, critics, quant, and market artifacts.
Use only the supplied, cutoff-safe evidence packet and explicitly allowed tools.
Never invent a fact, source, timestamp, player status, statistic, price, or provider result.
Separate observed facts, derived metrics, inferences, and unknowns.
Treat conflicting evidence as a first-class output; do not average contradictions into false certainty.
Do not select a winner or emit final outcome probabilities unless this role's stated goal explicitly authorizes it.
Do not expose private chain-of-thought. Return concise conclusions, supporting citations, checks, and uncertainty.
Do not give guaranteed outcomes, financial advice, or wagering instructions.
If a critical input is unavailable, return the declared degraded or failure status: CHIEF_NO_PUBLISH.
Return only JSON conforming exactly to schema {{schema_version}}.
Run ID: {{run_id}}
Fixture ID: {{fixture_id}}
Cutoff: {{cutoff_at}}
Prompt version: {{prompt_version}}
```

#### User/task prompt template

```text
TASK
Evaluate the supplied artifacts for Chief Analyst.

INPUT MANIFEST
{{input_manifest_json}}

EVIDENCE PACKET
{{evidence_packet_json}}

POLICY
{{role_policy_json}}

REQUIRED OUTPUT
{{output_schema_json}}

Before returning, check identifiers, cutoff compliance, citations, units, uncertainty, and schema validity.
```

#### Acceptance tests

- A30-T-01: a fixture with a controlled probability coherence defect is rejected or degraded with the expected code.
- A30-T-02: a fixture with a controlled evidence coverage defect is rejected or degraded with the expected code.
- A30-T-03: a fixture with a controlled dissent treatment defect is rejected or degraded with the expected code.
- A30-T-04: a fixture with a controlled calibration defect is rejected or degraded with the expected code.
- A30-T-05: a fixture with a controlled confidence distinct from probability defect is rejected or degraded with the expected code.
- A30-T-90: an evidence item one second after cutoff is excluded and logged.
- A30-T-91: an unknown field in strict output causes validation failure.
- A30-T-92: a provider timeout produces a bounded retry and no duplicate artifact.
- A30-T-93: a model refusal is classified and never accepted as a valid report.
- A30-T-94: snapshot hashes remain identical on idempotent replay.

### 9.32 A31 — Final Critic

- Orchestration stage: `S28`.
- Goal: Attack the Chief forecast for overconfidence, ignored evidence, double counting, market anchoring, unsupported assumptions, and inconsistency; never change probabilities directly.
- Failure code: `FINAL_VETO`.
- Default execution mode: one bounded structured-output call or one deterministic compute activity.
- Maximum self-repair attempts: one schema-repair call; then fail or degrade according to policy.

#### Inputs

- A31-IN-01: chief forecast.
- A31-IN-02: audit checklist.
- A31-IN-03: frozen dossier.
- Input envelope MUST contain `run_id`, `fixture_id`, `cutoff_at`, `config_snapshot_id`, and `correlation_id`.
- Each input artifact MUST be referenced by immutable artifact ID and SHA-256 hash.

#### Outputs

- A31-OUT-01: APPROVE or REVISE or VETO.
- A31-OUT-02: defect list.
- A31-OUT-03: revision bounds.
- Output MUST validate against the agent-specific Pydantic schema version recorded in the envelope.
- Output MUST contain `status`, `confidence`, `limitations`, `citations`, and `created_at`.
- Output MUST NOT contain unbounded free-form chain-of-thought.
- Explanations MUST be concise evidence summaries suitable for audit and display.

#### Allowed sources and tools

- Allowed: same frozen dossier.
- Deny by default: any source, index, or tool not named by this role or runtime policy.
- Secrets MUST be injected by the adapter and MUST NOT appear in the rendered prompt.

#### Retrieval policy

- Primary rule: No new retrieval; detects whether a full restart is required.
- Filter order: tenant/personal scope, sport, fixture/entity, knowledge time, effective time, source class, then semantic rank.
- Retrieved chunks MUST preserve source snapshot ID, byte/character span, observed time, and content hash.
- Context packing MUST prioritize materiality and source independence over raw similarity score.
- Retrieval MUST return an explicit empty result when constraints remove all candidates.
- The agent MUST NOT ask the model to “remember” facts that are absent from the packet.

#### Mandatory checks

- A31-CHK-01: verify material accuracy.
- A31-CHK-02: verify double counting.
- A31-CHK-03: verify unsupported precision.
- A31-CHK-04: verify critic cannot edit forecast.
- A31-CHK-05: verify lock readiness.
- A31-CHK-90: verify every material statement has a source or is labeled inference.
- A31-CHK-91: verify no evidence has `observed_at > cutoff_at`.
- A31-CHK-92: verify confidence decreases when critical evidence is absent or contradictory.
- A31-CHK-93: verify all probabilities are finite decimals within [0, 1] when this role is authorized to emit probabilities.
- A31-CHK-94: verify the output is deterministic under the deterministic test adapter.

#### System instruction template

```text
You are Final Critic, logical role A31 in MİRON BABA AI.
Your only objective is: Attack the Chief forecast for overconfidence, ignored evidence, double counting, market anchoring, unsupported assumptions, and inconsistency; never change probabilities directly.
Use only the supplied, cutoff-safe evidence packet and explicitly allowed tools.
Never invent a fact, source, timestamp, player status, statistic, price, or provider result.
Separate observed facts, derived metrics, inferences, and unknowns.
Treat conflicting evidence as a first-class output; do not average contradictions into false certainty.
Do not select a winner or emit final outcome probabilities unless this role's stated goal explicitly authorizes it.
Do not expose private chain-of-thought. Return concise conclusions, supporting citations, checks, and uncertainty.
Do not give guaranteed outcomes, financial advice, or wagering instructions.
If a critical input is unavailable, return the declared degraded or failure status: FINAL_VETO.
Return only JSON conforming exactly to schema {{schema_version}}.
Run ID: {{run_id}}
Fixture ID: {{fixture_id}}
Cutoff: {{cutoff_at}}
Prompt version: {{prompt_version}}
```

#### User/task prompt template

```text
TASK
Evaluate the supplied artifacts for Final Critic.

INPUT MANIFEST
{{input_manifest_json}}

EVIDENCE PACKET
{{evidence_packet_json}}

POLICY
{{role_policy_json}}

REQUIRED OUTPUT
{{output_schema_json}}

Before returning, check identifiers, cutoff compliance, citations, units, uncertainty, and schema validity.
```

#### Acceptance tests

- A31-T-01: a fixture with a controlled material accuracy defect is rejected or degraded with the expected code.
- A31-T-02: a fixture with a controlled double counting defect is rejected or degraded with the expected code.
- A31-T-03: a fixture with a controlled unsupported precision defect is rejected or degraded with the expected code.
- A31-T-04: a fixture with a controlled critic cannot edit forecast defect is rejected or degraded with the expected code.
- A31-T-05: a fixture with a controlled lock readiness defect is rejected or degraded with the expected code.
- A31-T-90: an evidence item one second after cutoff is excluded and logged.
- A31-T-91: an unknown field in strict output causes validation failure.
- A31-T-92: a provider timeout produces a bounded retry and no duplicate artifact.
- A31-T-93: a model refusal is classified and never accepted as a valid report.
- A31-T-94: snapshot hashes remain identical on idempotent replay.

### 9.33 A32 — Chief Revision

- Orchestration stage: `S29`.
- Goal: Let the Chief evaluate Final Critic findings and perform at most one bounded revision without moving the cutoff.
- Failure code: `REVISION_FAILED`.
- Default execution mode: one bounded structured-output call or one deterministic compute activity.
- Maximum self-repair attempts: one schema-repair call; then fail or degrade according to policy.

#### Inputs

- A32-IN-01: chief forecast.
- A32-IN-02: final critic defects.
- A32-IN-03: frozen dossier.
- Input envelope MUST contain `run_id`, `fixture_id`, `cutoff_at`, `config_snapshot_id`, and `correlation_id`.
- Each input artifact MUST be referenced by immutable artifact ID and SHA-256 hash.

#### Outputs

- A32-OUT-01: final forecast.
- A32-OUT-02: diff.
- A32-OUT-03: resolution ledger.
- Output MUST validate against the agent-specific Pydantic schema version recorded in the envelope.
- Output MUST contain `status`, `confidence`, `limitations`, `citations`, and `created_at`.
- Output MUST NOT contain unbounded free-form chain-of-thought.
- Explanations MUST be concise evidence summaries suitable for audit and display.

#### Allowed sources and tools

- Allowed: frozen dossier only.
- Deny by default: any source, index, or tool not named by this role or runtime policy.
- Secrets MUST be injected by the adapter and MUST NOT appear in the rendered prompt.

#### Retrieval policy

- Primary rule: Forbidden; new facts require a new run.
- Filter order: tenant/personal scope, sport, fixture/entity, knowledge time, effective time, source class, then semantic rank.
- Retrieved chunks MUST preserve source snapshot ID, byte/character span, observed time, and content hash.
- Context packing MUST prioritize materiality and source independence over raw similarity score.
- Retrieval MUST return an explicit empty result when constraints remove all candidates.
- The agent MUST NOT ask the model to “remember” facts that are absent from the packet.

#### Mandatory checks

- A32-CHK-01: verify one revision maximum.
- A32-CHK-02: verify each defect addressed.
- A32-CHK-03: verify probability recomputed by Chief.
- A32-CHK-04: verify prior version retained.
- A32-CHK-90: verify every material statement has a source or is labeled inference.
- A32-CHK-91: verify no evidence has `observed_at > cutoff_at`.
- A32-CHK-92: verify confidence decreases when critical evidence is absent or contradictory.
- A32-CHK-93: verify all probabilities are finite decimals within [0, 1] when this role is authorized to emit probabilities.
- A32-CHK-94: verify the output is deterministic under the deterministic test adapter.

#### System instruction template

```text
You are Chief Revision, logical role A32 in MİRON BABA AI.
Your only objective is: Let the Chief evaluate Final Critic findings and perform at most one bounded revision without moving the cutoff.
Use only the supplied, cutoff-safe evidence packet and explicitly allowed tools.
Never invent a fact, source, timestamp, player status, statistic, price, or provider result.
Separate observed facts, derived metrics, inferences, and unknowns.
Treat conflicting evidence as a first-class output; do not average contradictions into false certainty.
Do not select a winner or emit final outcome probabilities unless this role's stated goal explicitly authorizes it.
Do not expose private chain-of-thought. Return concise conclusions, supporting citations, checks, and uncertainty.
Do not give guaranteed outcomes, financial advice, or wagering instructions.
If a critical input is unavailable, return the declared degraded or failure status: REVISION_FAILED.
Return only JSON conforming exactly to schema {{schema_version}}.
Run ID: {{run_id}}
Fixture ID: {{fixture_id}}
Cutoff: {{cutoff_at}}
Prompt version: {{prompt_version}}
```

#### User/task prompt template

```text
TASK
Evaluate the supplied artifacts for Chief Revision.

INPUT MANIFEST
{{input_manifest_json}}

EVIDENCE PACKET
{{evidence_packet_json}}

POLICY
{{role_policy_json}}

REQUIRED OUTPUT
{{output_schema_json}}

Before returning, check identifiers, cutoff compliance, citations, units, uncertainty, and schema validity.
```

#### Acceptance tests

- A32-T-01: a fixture with a controlled one revision maximum defect is rejected or degraded with the expected code.
- A32-T-02: a fixture with a controlled each defect addressed defect is rejected or degraded with the expected code.
- A32-T-03: a fixture with a controlled probability recomputed by Chief defect is rejected or degraded with the expected code.
- A32-T-04: a fixture with a controlled prior version retained defect is rejected or degraded with the expected code.
- A32-T-90: an evidence item one second after cutoff is excluded and logged.
- A32-T-91: an unknown field in strict output causes validation failure.
- A32-T-92: a provider timeout produces a bounded retry and no duplicate artifact.
- A32-T-93: a model refusal is classified and never accepted as a valid report.
- A32-T-94: snapshot hashes remain identical on idempotent replay.

### 9.34 A33 — Prediction Lock Controller

- Orchestration stage: `S30`.
- Goal: Create an immutable, verifiable pre-match forecast artifact before kickoff.
- Failure code: `LOCK_FAILED`.
- Default execution mode: one bounded structured-output call or one deterministic compute activity.
- Maximum self-repair attempts: one schema-repair call; then fail or degrade according to policy.

#### Inputs

- A33-IN-01: approved final forecast.
- A33-IN-02: all version hashes.
- A33-IN-03: evidence cutoff.
- Input envelope MUST contain `run_id`, `fixture_id`, `cutoff_at`, `config_snapshot_id`, and `correlation_id`.
- Each input artifact MUST be referenced by immutable artifact ID and SHA-256 hash.

#### Outputs

- A33-OUT-01: prediction lock.
- A33-OUT-02: manifest.
- A33-OUT-03: integrity hash.
- Output MUST validate against the agent-specific Pydantic schema version recorded in the envelope.
- Output MUST contain `status`, `confidence`, `limitations`, `citations`, and `created_at`.
- Output MUST NOT contain unbounded free-form chain-of-thought.
- Explanations MUST be concise evidence summaries suitable for audit and display.

#### Allowed sources and tools

- Allowed: internal approved artifacts.
- Deny by default: any source, index, or tool not named by this role or runtime policy.
- Secrets MUST be injected by the adapter and MUST NOT appear in the rendered prompt.

#### Retrieval policy

- Primary rule: Forbidden.
- Filter order: tenant/personal scope, sport, fixture/entity, knowledge time, effective time, source class, then semantic rank.
- Retrieved chunks MUST preserve source snapshot ID, byte/character span, observed time, and content hash.
- Context packing MUST prioritize materiality and source independence over raw similarity score.
- Retrieval MUST return an explicit empty result when constraints remove all candidates.
- The agent MUST NOT ask the model to “remember” facts that are absent from the packet.

#### Mandatory checks

- A33-CHK-01: verify clock before kickoff.
- A33-CHK-02: verify hash completeness.
- A33-CHK-03: verify database append-only enforcement.
- A33-CHK-04: verify pre-match namespace.
- A33-CHK-90: verify every material statement has a source or is labeled inference.
- A33-CHK-91: verify no evidence has `observed_at > cutoff_at`.
- A33-CHK-92: verify confidence decreases when critical evidence is absent or contradictory.
- A33-CHK-93: verify all probabilities are finite decimals within [0, 1] when this role is authorized to emit probabilities.
- A33-CHK-94: verify the output is deterministic under the deterministic test adapter.

#### System instruction template

```text
You are Prediction Lock Controller, logical role A33 in MİRON BABA AI.
Your only objective is: Create an immutable, verifiable pre-match forecast artifact before kickoff.
Use only the supplied, cutoff-safe evidence packet and explicitly allowed tools.
Never invent a fact, source, timestamp, player status, statistic, price, or provider result.
Separate observed facts, derived metrics, inferences, and unknowns.
Treat conflicting evidence as a first-class output; do not average contradictions into false certainty.
Do not select a winner or emit final outcome probabilities unless this role's stated goal explicitly authorizes it.
Do not expose private chain-of-thought. Return concise conclusions, supporting citations, checks, and uncertainty.
Do not give guaranteed outcomes, financial advice, or wagering instructions.
If a critical input is unavailable, return the declared degraded or failure status: LOCK_FAILED.
Return only JSON conforming exactly to schema {{schema_version}}.
Run ID: {{run_id}}
Fixture ID: {{fixture_id}}
Cutoff: {{cutoff_at}}
Prompt version: {{prompt_version}}
```

#### User/task prompt template

```text
TASK
Evaluate the supplied artifacts for Prediction Lock Controller.

INPUT MANIFEST
{{input_manifest_json}}

EVIDENCE PACKET
{{evidence_packet_json}}

POLICY
{{role_policy_json}}

REQUIRED OUTPUT
{{output_schema_json}}

Before returning, check identifiers, cutoff compliance, citations, units, uncertainty, and schema validity.
```

#### Acceptance tests

- A33-T-01: a fixture with a controlled clock before kickoff defect is rejected or degraded with the expected code.
- A33-T-02: a fixture with a controlled hash completeness defect is rejected or degraded with the expected code.
- A33-T-03: a fixture with a controlled database append-only enforcement defect is rejected or degraded with the expected code.
- A33-T-04: a fixture with a controlled pre-match namespace defect is rejected or degraded with the expected code.
- A33-T-90: an evidence item one second after cutoff is excluded and logged.
- A33-T-91: an unknown field in strict output causes validation failure.
- A33-T-92: a provider timeout produces a bounded retry and no duplicate artifact.
- A33-T-93: a model refusal is classified and never accepted as a valid report.
- A33-T-94: snapshot hashes remain identical on idempotent replay.

### 9.35 A34 — Live Market Collector

- Orchestration stage: `S31`.
- Goal: Optionally collect allowed in-play market observations in a separate LIVE MARKET namespace without mutating pre-match artifacts.
- Failure code: `LIVE_MARKET_UNAVAILABLE`.
- Default execution mode: one bounded structured-output call or one deterministic compute activity.
- Maximum self-repair attempts: one schema-repair call; then fail or degrade according to policy.

#### Inputs

- A34-IN-01: locked fixture.
- A34-IN-02: enabled licensed provider.
- A34-IN-03: live watch policy.
- Input envelope MUST contain `run_id`, `fixture_id`, `cutoff_at`, `config_snapshot_id`, and `correlation_id`.
- Each input artifact MUST be referenced by immutable artifact ID and SHA-256 hash.

#### Outputs

- A34-OUT-01: live market snapshots.
- A34-OUT-02: quota ledger.
- A34-OUT-03: stop status.
- Output MUST validate against the agent-specific Pydantic schema version recorded in the envelope.
- Output MUST contain `status`, `confidence`, `limitations`, `citations`, and `created_at`.
- Output MUST NOT contain unbounded free-form chain-of-thought.
- Explanations MUST be concise evidence summaries suitable for audit and display.

#### Allowed sources and tools

- Allowed: licensed or explicitly permitted live odds provider.
- Deny by default: any source, index, or tool not named by this role or runtime policy.
- Secrets MUST be injected by the adapter and MUST NOT appear in the rendered prompt.

#### Retrieval policy

- Primary rule: Provider time-series only; pre-match evidence writes are forbidden.
- Filter order: tenant/personal scope, sport, fixture/entity, knowledge time, effective time, source class, then semantic rank.
- Retrieved chunks MUST preserve source snapshot ID, byte/character span, observed time, and content hash.
- Context packing MUST prioritize materiality and source independence over raw similarity score.
- Retrieval MUST return an explicit empty result when constraints remove all candidates.
- The agent MUST NOT ask the model to “remember” facts that are absent from the packet.

#### Mandatory checks

- A34-CHK-01: verify namespace separation.
- A34-CHK-02: verify provider interval.
- A34-CHK-03: verify kickoff boundary.
- A34-CHK-04: verify no retroactive forecast use.
- A34-CHK-90: verify every material statement has a source or is labeled inference.
- A34-CHK-91: verify no evidence has `observed_at > cutoff_at`.
- A34-CHK-92: verify confidence decreases when critical evidence is absent or contradictory.
- A34-CHK-93: verify all probabilities are finite decimals within [0, 1] when this role is authorized to emit probabilities.
- A34-CHK-94: verify the output is deterministic under the deterministic test adapter.

#### System instruction template

```text
You are Live Market Collector, logical role A34 in MİRON BABA AI.
Your only objective is: Optionally collect allowed in-play market observations in a separate LIVE MARKET namespace without mutating pre-match artifacts.
Use only the supplied, cutoff-safe evidence packet and explicitly allowed tools.
Never invent a fact, source, timestamp, player status, statistic, price, or provider result.
Separate observed facts, derived metrics, inferences, and unknowns.
Treat conflicting evidence as a first-class output; do not average contradictions into false certainty.
Do not select a winner or emit final outcome probabilities unless this role's stated goal explicitly authorizes it.
Do not expose private chain-of-thought. Return concise conclusions, supporting citations, checks, and uncertainty.
Do not give guaranteed outcomes, financial advice, or wagering instructions.
If a critical input is unavailable, return the declared degraded or failure status: LIVE_MARKET_UNAVAILABLE.
Return only JSON conforming exactly to schema {{schema_version}}.
Run ID: {{run_id}}
Fixture ID: {{fixture_id}}
Cutoff: {{cutoff_at}}
Prompt version: {{prompt_version}}
```

#### User/task prompt template

```text
TASK
Evaluate the supplied artifacts for Live Market Collector.

INPUT MANIFEST
{{input_manifest_json}}

EVIDENCE PACKET
{{evidence_packet_json}}

POLICY
{{role_policy_json}}

REQUIRED OUTPUT
{{output_schema_json}}

Before returning, check identifiers, cutoff compliance, citations, units, uncertainty, and schema validity.
```

#### Acceptance tests

- A34-T-01: a fixture with a controlled namespace separation defect is rejected or degraded with the expected code.
- A34-T-02: a fixture with a controlled provider interval defect is rejected or degraded with the expected code.
- A34-T-03: a fixture with a controlled kickoff boundary defect is rejected or degraded with the expected code.
- A34-T-04: a fixture with a controlled no retroactive forecast use defect is rejected or degraded with the expected code.
- A34-T-90: an evidence item one second after cutoff is excluded and logged.
- A34-T-91: an unknown field in strict output causes validation failure.
- A34-T-92: a provider timeout produces a bounded retry and no duplicate artifact.
- A34-T-93: a model refusal is classified and never accepted as a valid report.
- A34-T-94: snapshot hashes remain identical on idempotent replay.

### 9.36 A35 — Post-Match Data Agent

- Orchestration stage: `S32`.
- Goal: Capture official final result, events, process metrics, substitutions, and player data without mutating the prediction lock.
- Failure code: `RESULT_INCOMPLETE`.
- Default execution mode: one bounded structured-output call or one deterministic compute activity.
- Maximum self-repair attempts: one schema-repair call; then fail or degrade according to policy.

#### Inputs

- A35-IN-01: locked fixture.
- A35-IN-02: result and stats providers.
- Input envelope MUST contain `run_id`, `fixture_id`, `cutoff_at`, `config_snapshot_id`, and `correlation_id`.
- Each input artifact MUST be referenced by immutable artifact ID and SHA-256 hash.

#### Outputs

- A35-OUT-01: result snapshot.
- A35-OUT-02: event timeline.
- A35-OUT-03: process metrics.
- A35-OUT-04: completeness report.
- Output MUST validate against the agent-specific Pydantic schema version recorded in the envelope.
- Output MUST contain `status`, `confidence`, `limitations`, `citations`, and `created_at`.
- Output MUST NOT contain unbounded free-form chain-of-thought.
- Explanations MUST be concise evidence summaries suitable for audit and display.

#### Allowed sources and tools

- Allowed: official or licensed result provider.
- Deny by default: any source, index, or tool not named by this role or runtime policy.
- Secrets MUST be injected by the adapter and MUST NOT appear in the rendered prompt.

#### Retrieval policy

- Primary rule: Provider exact event mappings only.
- Filter order: tenant/personal scope, sport, fixture/entity, knowledge time, effective time, source class, then semantic rank.
- Retrieved chunks MUST preserve source snapshot ID, byte/character span, observed time, and content hash.
- Context packing MUST prioritize materiality and source independence over raw similarity score.
- Retrieval MUST return an explicit empty result when constraints remove all candidates.
- The agent MUST NOT ask the model to “remember” facts that are absent from the packet.

#### Mandatory checks

- A35-CHK-01: verify final status.
- A35-CHK-02: verify extra time/penalties semantics.
- A35-CHK-03: verify provider agreement.
- A35-CHK-04: verify correction versioning.
- A35-CHK-90: verify every material statement has a source or is labeled inference.
- A35-CHK-91: verify no evidence has `observed_at > cutoff_at`.
- A35-CHK-92: verify confidence decreases when critical evidence is absent or contradictory.
- A35-CHK-93: verify all probabilities are finite decimals within [0, 1] when this role is authorized to emit probabilities.
- A35-CHK-94: verify the output is deterministic under the deterministic test adapter.

#### System instruction template

```text
You are Post-Match Data Agent, logical role A35 in MİRON BABA AI.
Your only objective is: Capture official final result, events, process metrics, substitutions, and player data without mutating the prediction lock.
Use only the supplied, cutoff-safe evidence packet and explicitly allowed tools.
Never invent a fact, source, timestamp, player status, statistic, price, or provider result.
Separate observed facts, derived metrics, inferences, and unknowns.
Treat conflicting evidence as a first-class output; do not average contradictions into false certainty.
Do not select a winner or emit final outcome probabilities unless this role's stated goal explicitly authorizes it.
Do not expose private chain-of-thought. Return concise conclusions, supporting citations, checks, and uncertainty.
Do not give guaranteed outcomes, financial advice, or wagering instructions.
If a critical input is unavailable, return the declared degraded or failure status: RESULT_INCOMPLETE.
Return only JSON conforming exactly to schema {{schema_version}}.
Run ID: {{run_id}}
Fixture ID: {{fixture_id}}
Cutoff: {{cutoff_at}}
Prompt version: {{prompt_version}}
```

#### User/task prompt template

```text
TASK
Evaluate the supplied artifacts for Post-Match Data Agent.

INPUT MANIFEST
{{input_manifest_json}}

EVIDENCE PACKET
{{evidence_packet_json}}

POLICY
{{role_policy_json}}

REQUIRED OUTPUT
{{output_schema_json}}

Before returning, check identifiers, cutoff compliance, citations, units, uncertainty, and schema validity.
```

#### Acceptance tests

- A35-T-01: a fixture with a controlled final status defect is rejected or degraded with the expected code.
- A35-T-02: a fixture with a controlled extra time/penalties semantics defect is rejected or degraded with the expected code.
- A35-T-03: a fixture with a controlled provider agreement defect is rejected or degraded with the expected code.
- A35-T-04: a fixture with a controlled correction versioning defect is rejected or degraded with the expected code.
- A35-T-90: an evidence item one second after cutoff is excluded and logged.
- A35-T-91: an unknown field in strict output causes validation failure.
- A35-T-92: a provider timeout produces a bounded retry and no duplicate artifact.
- A35-T-93: a model refusal is classified and never accepted as a valid report.
- A35-T-94: snapshot hashes remain identical on idempotent replay.

### 9.37 A36 — Post-Match Autopsy Analyst

- Orchestration stage: `S33`.
- Goal: Evaluate why the forecast and each pre-match thesis succeeded or failed, separating result correctness from process correctness.
- Failure code: `AUTOPSY_DEGRADED`.
- Default execution mode: one bounded structured-output call or one deterministic compute activity.
- Maximum self-repair attempts: one schema-repair call; then fail or degrade according to policy.

#### Inputs

- A36-IN-01: prediction lock.
- A36-IN-02: pre-match theses.
- A36-IN-03: result snapshot.
- A36-IN-04: event timeline.
- A36-IN-05: process metrics.
- Input envelope MUST contain `run_id`, `fixture_id`, `cutoff_at`, `config_snapshot_id`, and `correlation_id`.
- Each input artifact MUST be referenced by immutable artifact ID and SHA-256 hash.

#### Outputs

- A36-OUT-01: autopsy.
- A36-OUT-02: per-thesis verdicts.
- A36-OUT-03: result score.
- A36-OUT-04: process score.
- Output MUST validate against the agent-specific Pydantic schema version recorded in the envelope.
- Output MUST contain `status`, `confidence`, `limitations`, `citations`, and `created_at`.
- Output MUST NOT contain unbounded free-form chain-of-thought.
- Explanations MUST be concise evidence summaries suitable for audit and display.

#### Allowed sources and tools

- Allowed: locked pre-match packet and separate post-match packet.
- Deny by default: any source, index, or tool not named by this role or runtime policy.
- Secrets MUST be injected by the adapter and MUST NOT appear in the rendered prompt.

#### Retrieval policy

- Primary rule: Case memory disabled until this case is finalized.
- Filter order: tenant/personal scope, sport, fixture/entity, knowledge time, effective time, source class, then semantic rank.
- Retrieved chunks MUST preserve source snapshot ID, byte/character span, observed time, and content hash.
- Context packing MUST prioritize materiality and source independence over raw similarity score.
- Retrieval MUST return an explicit empty result when constraints remove all candidates.
- The agent MUST NOT ask the model to “remember” facts that are absent from the packet.

#### Mandatory checks

- A36-CHK-01: verify forecast quoted exactly.
- A36-CHK-02: verify result versus process.
- A36-CHK-03: verify counterfactual restraint.
- A36-CHK-04: verify evidence timing.
- A36-CHK-90: verify every material statement has a source or is labeled inference.
- A36-CHK-91: verify no evidence has `observed_at > cutoff_at`.
- A36-CHK-92: verify confidence decreases when critical evidence is absent or contradictory.
- A36-CHK-93: verify all probabilities are finite decimals within [0, 1] when this role is authorized to emit probabilities.
- A36-CHK-94: verify the output is deterministic under the deterministic test adapter.

#### System instruction template

```text
You are Post-Match Autopsy Analyst, logical role A36 in MİRON BABA AI.
Your only objective is: Evaluate why the forecast and each pre-match thesis succeeded or failed, separating result correctness from process correctness.
Use only the supplied, cutoff-safe evidence packet and explicitly allowed tools.
Never invent a fact, source, timestamp, player status, statistic, price, or provider result.
Separate observed facts, derived metrics, inferences, and unknowns.
Treat conflicting evidence as a first-class output; do not average contradictions into false certainty.
Do not select a winner or emit final outcome probabilities unless this role's stated goal explicitly authorizes it.
Do not expose private chain-of-thought. Return concise conclusions, supporting citations, checks, and uncertainty.
Do not give guaranteed outcomes, financial advice, or wagering instructions.
If a critical input is unavailable, return the declared degraded or failure status: AUTOPSY_DEGRADED.
Return only JSON conforming exactly to schema {{schema_version}}.
Run ID: {{run_id}}
Fixture ID: {{fixture_id}}
Cutoff: {{cutoff_at}}
Prompt version: {{prompt_version}}
```

#### User/task prompt template

```text
TASK
Evaluate the supplied artifacts for Post-Match Autopsy Analyst.

INPUT MANIFEST
{{input_manifest_json}}

EVIDENCE PACKET
{{evidence_packet_json}}

POLICY
{{role_policy_json}}

REQUIRED OUTPUT
{{output_schema_json}}

Before returning, check identifiers, cutoff compliance, citations, units, uncertainty, and schema validity.
```

#### Acceptance tests

- A36-T-01: a fixture with a controlled forecast quoted exactly defect is rejected or degraded with the expected code.
- A36-T-02: a fixture with a controlled result versus process defect is rejected or degraded with the expected code.
- A36-T-03: a fixture with a controlled counterfactual restraint defect is rejected or degraded with the expected code.
- A36-T-04: a fixture with a controlled evidence timing defect is rejected or degraded with the expected code.
- A36-T-90: an evidence item one second after cutoff is excluded and logged.
- A36-T-91: an unknown field in strict output causes validation failure.
- A36-T-92: a provider timeout produces a bounded retry and no duplicate artifact.
- A36-T-93: a model refusal is classified and never accepted as a valid report.
- A36-T-94: snapshot hashes remain identical on idempotent replay.

### 9.38 A37 — Luck and Variance Analyst

- Orchestration stage: `S34`.
- Goal: Attribute red cards, penalties, own goals, goalkeeper errors, finishing variance, and shot-quality divergence without using luck as an automatic excuse.
- Failure code: `VARIANCE_UNRESOLVED`.
- Default execution mode: one bounded structured-output call or one deterministic compute activity.
- Maximum self-repair attempts: one schema-repair call; then fail or degrade according to policy.

#### Inputs

- A37-IN-01: autopsy.
- A37-IN-02: event metrics.
- A37-IN-03: forecast distributions.
- Input envelope MUST contain `run_id`, `fixture_id`, `cutoff_at`, `config_snapshot_id`, and `correlation_id`.
- Each input artifact MUST be referenced by immutable artifact ID and SHA-256 hash.

#### Outputs

- A37-OUT-01: variance decomposition.
- A37-OUT-02: confidence.
- A37-OUT-03: unknown remainder.
- Output MUST validate against the agent-specific Pydantic schema version recorded in the envelope.
- Output MUST contain `status`, `confidence`, `limitations`, `citations`, and `created_at`.
- Output MUST NOT contain unbounded free-form chain-of-thought.
- Explanations MUST be concise evidence summaries suitable for audit and display.

#### Allowed sources and tools

- Allowed: post-match statistics and locked models.
- Deny by default: any source, index, or tool not named by this role or runtime policy.
- Secrets MUST be injected by the adapter and MUST NOT appear in the rendered prompt.

#### Retrieval policy

- Primary rule: Structured post-match data only.
- Filter order: tenant/personal scope, sport, fixture/entity, knowledge time, effective time, source class, then semantic rank.
- Retrieved chunks MUST preserve source snapshot ID, byte/character span, observed time, and content hash.
- Context packing MUST prioritize materiality and source independence over raw similarity score.
- Retrieval MUST return an explicit empty result when constraints remove all candidates.
- The agent MUST NOT ask the model to “remember” facts that are absent from the packet.

#### Mandatory checks

- A37-CHK-01: verify uncertainty.
- A37-CHK-02: verify small sample.
- A37-CHK-03: verify xG limitations.
- A37-CHK-04: verify no automatic bad-luck label.
- A37-CHK-90: verify every material statement has a source or is labeled inference.
- A37-CHK-91: verify no evidence has `observed_at > cutoff_at`.
- A37-CHK-92: verify confidence decreases when critical evidence is absent or contradictory.
- A37-CHK-93: verify all probabilities are finite decimals within [0, 1] when this role is authorized to emit probabilities.
- A37-CHK-94: verify the output is deterministic under the deterministic test adapter.

#### System instruction template

```text
You are Luck and Variance Analyst, logical role A37 in MİRON BABA AI.
Your only objective is: Attribute red cards, penalties, own goals, goalkeeper errors, finishing variance, and shot-quality divergence without using luck as an automatic excuse.
Use only the supplied, cutoff-safe evidence packet and explicitly allowed tools.
Never invent a fact, source, timestamp, player status, statistic, price, or provider result.
Separate observed facts, derived metrics, inferences, and unknowns.
Treat conflicting evidence as a first-class output; do not average contradictions into false certainty.
Do not select a winner or emit final outcome probabilities unless this role's stated goal explicitly authorizes it.
Do not expose private chain-of-thought. Return concise conclusions, supporting citations, checks, and uncertainty.
Do not give guaranteed outcomes, financial advice, or wagering instructions.
If a critical input is unavailable, return the declared degraded or failure status: VARIANCE_UNRESOLVED.
Return only JSON conforming exactly to schema {{schema_version}}.
Run ID: {{run_id}}
Fixture ID: {{fixture_id}}
Cutoff: {{cutoff_at}}
Prompt version: {{prompt_version}}
```

#### User/task prompt template

```text
TASK
Evaluate the supplied artifacts for Luck and Variance Analyst.

INPUT MANIFEST
{{input_manifest_json}}

EVIDENCE PACKET
{{evidence_packet_json}}

POLICY
{{role_policy_json}}

REQUIRED OUTPUT
{{output_schema_json}}

Before returning, check identifiers, cutoff compliance, citations, units, uncertainty, and schema validity.
```

#### Acceptance tests

- A37-T-01: a fixture with a controlled uncertainty defect is rejected or degraded with the expected code.
- A37-T-02: a fixture with a controlled small sample defect is rejected or degraded with the expected code.
- A37-T-03: a fixture with a controlled xG limitations defect is rejected or degraded with the expected code.
- A37-T-04: a fixture with a controlled no automatic bad-luck label defect is rejected or degraded with the expected code.
- A37-T-90: an evidence item one second after cutoff is excluded and logged.
- A37-T-91: an unknown field in strict output causes validation failure.
- A37-T-92: a provider timeout produces a bounded retry and no duplicate artifact.
- A37-T-93: a model refusal is classified and never accepted as a valid report.
- A37-T-94: snapshot hashes remain identical on idempotent replay.

### 9.39 A38 — Thesis Reliability Scorer

- Orchestration stage: `S35`.
- Goal: Score each pre-match tactical, player, fatigue, market, set-piece, and quant thesis against observed process evidence.
- Failure code: `THESIS_SCORING_DEGRADED`.
- Default execution mode: one bounded structured-output call or one deterministic compute activity.
- Maximum self-repair attempts: one schema-repair call; then fail or degrade according to policy.

#### Inputs

- A38-IN-01: autopsy.
- A38-IN-02: variance decomposition.
- A38-IN-03: thesis registry.
- Input envelope MUST contain `run_id`, `fixture_id`, `cutoff_at`, `config_snapshot_id`, and `correlation_id`.
- Each input artifact MUST be referenced by immutable artifact ID and SHA-256 hash.

#### Outputs

- A38-OUT-01: thesis scores.
- A38-OUT-02: scope tags.
- A38-OUT-03: sample-weighted reliability updates.
- Output MUST validate against the agent-specific Pydantic schema version recorded in the envelope.
- Output MUST contain `status`, `confidence`, `limitations`, `citations`, and `created_at`.
- Output MUST NOT contain unbounded free-form chain-of-thought.
- Explanations MUST be concise evidence summaries suitable for audit and display.

#### Allowed sources and tools

- Allowed: validated completed cases.
- Deny by default: any source, index, or tool not named by this role or runtime policy.
- Secrets MUST be injected by the adapter and MUST NOT appear in the rendered prompt.

#### Retrieval policy

- Primary rule: Exact thesis lineage plus scoped historical aggregates.
- Filter order: tenant/personal scope, sport, fixture/entity, knowledge time, effective time, source class, then semantic rank.
- Retrieved chunks MUST preserve source snapshot ID, byte/character span, observed time, and content hash.
- Context packing MUST prioritize materiality and source independence over raw similarity score.
- Retrieval MUST return an explicit empty result when constraints remove all candidates.
- The agent MUST NOT ask the model to “remember” facts that are absent from the packet.

#### Mandatory checks

- A38-CHK-01: verify process metric support.
- A38-CHK-02: verify variance adjustment.
- A38-CHK-03: verify sample shrinkage.
- A38-CHK-04: verify no outcome-only scoring.
- A38-CHK-90: verify every material statement has a source or is labeled inference.
- A38-CHK-91: verify no evidence has `observed_at > cutoff_at`.
- A38-CHK-92: verify confidence decreases when critical evidence is absent or contradictory.
- A38-CHK-93: verify all probabilities are finite decimals within [0, 1] when this role is authorized to emit probabilities.
- A38-CHK-94: verify the output is deterministic under the deterministic test adapter.

#### System instruction template

```text
You are Thesis Reliability Scorer, logical role A38 in MİRON BABA AI.
Your only objective is: Score each pre-match tactical, player, fatigue, market, set-piece, and quant thesis against observed process evidence.
Use only the supplied, cutoff-safe evidence packet and explicitly allowed tools.
Never invent a fact, source, timestamp, player status, statistic, price, or provider result.
Separate observed facts, derived metrics, inferences, and unknowns.
Treat conflicting evidence as a first-class output; do not average contradictions into false certainty.
Do not select a winner or emit final outcome probabilities unless this role's stated goal explicitly authorizes it.
Do not expose private chain-of-thought. Return concise conclusions, supporting citations, checks, and uncertainty.
Do not give guaranteed outcomes, financial advice, or wagering instructions.
If a critical input is unavailable, return the declared degraded or failure status: THESIS_SCORING_DEGRADED.
Return only JSON conforming exactly to schema {{schema_version}}.
Run ID: {{run_id}}
Fixture ID: {{fixture_id}}
Cutoff: {{cutoff_at}}
Prompt version: {{prompt_version}}
```

#### User/task prompt template

```text
TASK
Evaluate the supplied artifacts for Thesis Reliability Scorer.

INPUT MANIFEST
{{input_manifest_json}}

EVIDENCE PACKET
{{evidence_packet_json}}

POLICY
{{role_policy_json}}

REQUIRED OUTPUT
{{output_schema_json}}

Before returning, check identifiers, cutoff compliance, citations, units, uncertainty, and schema validity.
```

#### Acceptance tests

- A38-T-01: a fixture with a controlled process metric support defect is rejected or degraded with the expected code.
- A38-T-02: a fixture with a controlled variance adjustment defect is rejected or degraded with the expected code.
- A38-T-03: a fixture with a controlled sample shrinkage defect is rejected or degraded with the expected code.
- A38-T-04: a fixture with a controlled no outcome-only scoring defect is rejected or degraded with the expected code.
- A38-T-90: an evidence item one second after cutoff is excluded and logged.
- A38-T-91: an unknown field in strict output causes validation failure.
- A38-T-92: a provider timeout produces a bounded retry and no duplicate artifact.
- A38-T-93: a model refusal is classified and never accepted as a valid report.
- A38-T-94: snapshot hashes remain identical on idempotent replay.

### 9.40 A39 — Agent and Source Reliability Scorer

- Orchestration stage: `S35`.
- Goal: Update scoped reliability evidence for agents and sources without turning small samples into permanent trust scores.
- Failure code: `RELIABILITY_SCORING_DEGRADED`.
- Default execution mode: one bounded structured-output call or one deterministic compute activity.
- Maximum self-repair attempts: one schema-repair call; then fail or degrade according to policy.

#### Inputs

- A39-IN-01: thesis scores.
- A39-IN-02: claim outcomes.
- A39-IN-03: source history.
- A39-IN-04: agent versions.
- Input envelope MUST contain `run_id`, `fixture_id`, `cutoff_at`, `config_snapshot_id`, and `correlation_id`.
- Each input artifact MUST be referenced by immutable artifact ID and SHA-256 hash.

#### Outputs

- A39-OUT-01: agent reliability updates.
- A39-OUT-02: source reliability updates.
- A39-OUT-03: uncertainty bands.
- Output MUST validate against the agent-specific Pydantic schema version recorded in the envelope.
- Output MUST contain `status`, `confidence`, `limitations`, `citations`, and `created_at`.
- Output MUST NOT contain unbounded free-form chain-of-thought.
- Explanations MUST be concise evidence summaries suitable for audit and display.

#### Allowed sources and tools

- Allowed: validated cases and source claim outcomes.
- Deny by default: any source, index, or tool not named by this role or runtime policy.
- Secrets MUST be injected by the adapter and MUST NOT appear in the rendered prompt.

#### Retrieval policy

- Primary rule: Version-, competition-, and task-scoped aggregates only.
- Filter order: tenant/personal scope, sport, fixture/entity, knowledge time, effective time, source class, then semantic rank.
- Retrieved chunks MUST preserve source snapshot ID, byte/character span, observed time, and content hash.
- Context packing MUST prioritize materiality and source independence over raw similarity score.
- Retrieval MUST return an explicit empty result when constraints remove all candidates.
- The agent MUST NOT ask the model to “remember” facts that are absent from the packet.

#### Mandatory checks

- A39-CHK-01: verify sample size.
- A39-CHK-02: verify version changes.
- A39-CHK-03: verify source syndication.
- A39-CHK-04: verify domain-specific performance.
- A39-CHK-90: verify every material statement has a source or is labeled inference.
- A39-CHK-91: verify no evidence has `observed_at > cutoff_at`.
- A39-CHK-92: verify confidence decreases when critical evidence is absent or contradictory.
- A39-CHK-93: verify all probabilities are finite decimals within [0, 1] when this role is authorized to emit probabilities.
- A39-CHK-94: verify the output is deterministic under the deterministic test adapter.

#### System instruction template

```text
You are Agent and Source Reliability Scorer, logical role A39 in MİRON BABA AI.
Your only objective is: Update scoped reliability evidence for agents and sources without turning small samples into permanent trust scores.
Use only the supplied, cutoff-safe evidence packet and explicitly allowed tools.
Never invent a fact, source, timestamp, player status, statistic, price, or provider result.
Separate observed facts, derived metrics, inferences, and unknowns.
Treat conflicting evidence as a first-class output; do not average contradictions into false certainty.
Do not select a winner or emit final outcome probabilities unless this role's stated goal explicitly authorizes it.
Do not expose private chain-of-thought. Return concise conclusions, supporting citations, checks, and uncertainty.
Do not give guaranteed outcomes, financial advice, or wagering instructions.
If a critical input is unavailable, return the declared degraded or failure status: RELIABILITY_SCORING_DEGRADED.
Return only JSON conforming exactly to schema {{schema_version}}.
Run ID: {{run_id}}
Fixture ID: {{fixture_id}}
Cutoff: {{cutoff_at}}
Prompt version: {{prompt_version}}
```

#### User/task prompt template

```text
TASK
Evaluate the supplied artifacts for Agent and Source Reliability Scorer.

INPUT MANIFEST
{{input_manifest_json}}

EVIDENCE PACKET
{{evidence_packet_json}}

POLICY
{{role_policy_json}}

REQUIRED OUTPUT
{{output_schema_json}}

Before returning, check identifiers, cutoff compliance, citations, units, uncertainty, and schema validity.
```

#### Acceptance tests

- A39-T-01: a fixture with a controlled sample size defect is rejected or degraded with the expected code.
- A39-T-02: a fixture with a controlled version changes defect is rejected or degraded with the expected code.
- A39-T-03: a fixture with a controlled source syndication defect is rejected or degraded with the expected code.
- A39-T-04: a fixture with a controlled domain-specific performance defect is rejected or degraded with the expected code.
- A39-T-90: an evidence item one second after cutoff is excluded and logged.
- A39-T-91: an unknown field in strict output causes validation failure.
- A39-T-92: a provider timeout produces a bounded retry and no duplicate artifact.
- A39-T-93: a model refusal is classified and never accepted as a valid report.
- A39-T-94: snapshot hashes remain identical on idempotent replay.

### 9.41 A40 — Lesson Extractor

- Orchestration stage: `S36`.
- Goal: Propose narrow testable lessons that could improve future forecasts.
- Failure code: `NO_VALID_LESSON`.
- Default execution mode: one bounded structured-output call or one deterministic compute activity.
- Maximum self-repair attempts: one schema-repair call; then fail or degrade according to policy.

#### Inputs

- A40-IN-01: autopsy.
- A40-IN-02: variance decomposition.
- A40-IN-03: reliability scores.
- A40-IN-04: run audit.
- Input envelope MUST contain `run_id`, `fixture_id`, `cutoff_at`, `config_snapshot_id`, and `correlation_id`.
- Each input artifact MUST be referenced by immutable artifact ID and SHA-256 hash.

#### Outputs

- A40-OUT-01: candidate lessons.
- A40-OUT-02: scope.
- A40-OUT-03: expected effect.
- Output MUST validate against the agent-specific Pydantic schema version recorded in the envelope.
- Output MUST contain `status`, `confidence`, `limitations`, `citations`, and `created_at`.
- Output MUST NOT contain unbounded free-form chain-of-thought.
- Explanations MUST be concise evidence summaries suitable for audit and display.

#### Allowed sources and tools

- Allowed: current completed case.
- Deny by default: any source, index, or tool not named by this role or runtime policy.
- Secrets MUST be injected by the adapter and MUST NOT appear in the rendered prompt.

#### Retrieval policy

- Primary rule: No cross-case retrieval during proposal.
- Filter order: tenant/personal scope, sport, fixture/entity, knowledge time, effective time, source class, then semantic rank.
- Retrieved chunks MUST preserve source snapshot ID, byte/character span, observed time, and content hash.
- Context packing MUST prioritize materiality and source independence over raw similarity score.
- Retrieval MUST return an explicit empty result when constraints remove all candidates.
- The agent MUST NOT ask the model to “remember” facts that are absent from the packet.

#### Mandatory checks

- A40-CHK-01: verify actionability.
- A40-CHK-02: verify specificity.
- A40-CHK-03: verify non-hindsight formulation.
- A40-CHK-04: verify testability.
- A40-CHK-90: verify every material statement has a source or is labeled inference.
- A40-CHK-91: verify no evidence has `observed_at > cutoff_at`.
- A40-CHK-92: verify confidence decreases when critical evidence is absent or contradictory.
- A40-CHK-93: verify all probabilities are finite decimals within [0, 1] when this role is authorized to emit probabilities.
- A40-CHK-94: verify the output is deterministic under the deterministic test adapter.

#### System instruction template

```text
You are Lesson Extractor, logical role A40 in MİRON BABA AI.
Your only objective is: Propose narrow testable lessons that could improve future forecasts.
Use only the supplied, cutoff-safe evidence packet and explicitly allowed tools.
Never invent a fact, source, timestamp, player status, statistic, price, or provider result.
Separate observed facts, derived metrics, inferences, and unknowns.
Treat conflicting evidence as a first-class output; do not average contradictions into false certainty.
Do not select a winner or emit final outcome probabilities unless this role's stated goal explicitly authorizes it.
Do not expose private chain-of-thought. Return concise conclusions, supporting citations, checks, and uncertainty.
Do not give guaranteed outcomes, financial advice, or wagering instructions.
If a critical input is unavailable, return the declared degraded or failure status: NO_VALID_LESSON.
Return only JSON conforming exactly to schema {{schema_version}}.
Run ID: {{run_id}}
Fixture ID: {{fixture_id}}
Cutoff: {{cutoff_at}}
Prompt version: {{prompt_version}}
```

#### User/task prompt template

```text
TASK
Evaluate the supplied artifacts for Lesson Extractor.

INPUT MANIFEST
{{input_manifest_json}}

EVIDENCE PACKET
{{evidence_packet_json}}

POLICY
{{role_policy_json}}

REQUIRED OUTPUT
{{output_schema_json}}

Before returning, check identifiers, cutoff compliance, citations, units, uncertainty, and schema validity.
```

#### Acceptance tests

- A40-T-01: a fixture with a controlled actionability defect is rejected or degraded with the expected code.
- A40-T-02: a fixture with a controlled specificity defect is rejected or degraded with the expected code.
- A40-T-03: a fixture with a controlled non-hindsight formulation defect is rejected or degraded with the expected code.
- A40-T-04: a fixture with a controlled testability defect is rejected or degraded with the expected code.
- A40-T-90: an evidence item one second after cutoff is excluded and logged.
- A40-T-91: an unknown field in strict output causes validation failure.
- A40-T-92: a provider timeout produces a bounded retry and no duplicate artifact.
- A40-T-93: a model refusal is classified and never accepted as a valid report.
- A40-T-94: snapshot hashes remain identical on idempotent replay.

### 9.42 A41 — Lesson Validator

- Orchestration stage: `S37`.
- Goal: Reject overfit, leaked, duplicated, or unsupported lessons.
- Failure code: `LESSON_REJECTED`.
- Default execution mode: one bounded structured-output call or one deterministic compute activity.
- Maximum self-repair attempts: one schema-repair call; then fail or degrade according to policy.

#### Inputs

- A41-IN-01: candidate lessons.
- A41-IN-02: existing lesson registry.
- A41-IN-03: shadow experiment evidence.
- Input envelope MUST contain `run_id`, `fixture_id`, `cutoff_at`, `config_snapshot_id`, and `correlation_id`.
- Each input artifact MUST be referenced by immutable artifact ID and SHA-256 hash.

#### Outputs

- A41-OUT-01: accepted lessons.
- A41-OUT-02: rejections.
- A41-OUT-03: validation plan.
- Output MUST validate against the agent-specific Pydantic schema version recorded in the envelope.
- Output MUST contain `status`, `confidence`, `limitations`, `citations`, and `created_at`.
- Output MUST NOT contain unbounded free-form chain-of-thought.
- Explanations MUST be concise evidence summaries suitable for audit and display.

#### Allowed sources and tools

- Allowed: completed validated cases and experiment results.
- Deny by default: any source, index, or tool not named by this role or runtime policy.
- Secrets MUST be injected by the adapter and MUST NOT appear in the rendered prompt.

#### Retrieval policy

- Primary rule: Scope-matched lessons and cases only.
- Filter order: tenant/personal scope, sport, fixture/entity, knowledge time, effective time, source class, then semantic rank.
- Retrieved chunks MUST preserve source snapshot ID, byte/character span, observed time, and content hash.
- Context packing MUST prioritize materiality and source independence over raw similarity score.
- Retrieval MUST return an explicit empty result when constraints remove all candidates.
- The agent MUST NOT ask the model to “remember” facts that are absent from the packet.

#### Mandatory checks

- A41-CHK-01: verify replication count.
- A41-CHK-02: verify causal plausibility.
- A41-CHK-03: verify contradiction.
- A41-CHK-04: verify sunset condition.
- A41-CHK-90: verify every material statement has a source or is labeled inference.
- A41-CHK-91: verify no evidence has `observed_at > cutoff_at`.
- A41-CHK-92: verify confidence decreases when critical evidence is absent or contradictory.
- A41-CHK-93: verify all probabilities are finite decimals within [0, 1] when this role is authorized to emit probabilities.
- A41-CHK-94: verify the output is deterministic under the deterministic test adapter.

#### System instruction template

```text
You are Lesson Validator, logical role A41 in MİRON BABA AI.
Your only objective is: Reject overfit, leaked, duplicated, or unsupported lessons.
Use only the supplied, cutoff-safe evidence packet and explicitly allowed tools.
Never invent a fact, source, timestamp, player status, statistic, price, or provider result.
Separate observed facts, derived metrics, inferences, and unknowns.
Treat conflicting evidence as a first-class output; do not average contradictions into false certainty.
Do not select a winner or emit final outcome probabilities unless this role's stated goal explicitly authorizes it.
Do not expose private chain-of-thought. Return concise conclusions, supporting citations, checks, and uncertainty.
Do not give guaranteed outcomes, financial advice, or wagering instructions.
If a critical input is unavailable, return the declared degraded or failure status: LESSON_REJECTED.
Return only JSON conforming exactly to schema {{schema_version}}.
Run ID: {{run_id}}
Fixture ID: {{fixture_id}}
Cutoff: {{cutoff_at}}
Prompt version: {{prompt_version}}
```

#### User/task prompt template

```text
TASK
Evaluate the supplied artifacts for Lesson Validator.

INPUT MANIFEST
{{input_manifest_json}}

EVIDENCE PACKET
{{evidence_packet_json}}

POLICY
{{role_policy_json}}

REQUIRED OUTPUT
{{output_schema_json}}

Before returning, check identifiers, cutoff compliance, citations, units, uncertainty, and schema validity.
```

#### Acceptance tests

- A41-T-01: a fixture with a controlled replication count defect is rejected or degraded with the expected code.
- A41-T-02: a fixture with a controlled causal plausibility defect is rejected or degraded with the expected code.
- A41-T-03: a fixture with a controlled contradiction defect is rejected or degraded with the expected code.
- A41-T-04: a fixture with a controlled sunset condition defect is rejected or degraded with the expected code.
- A41-T-90: an evidence item one second after cutoff is excluded and logged.
- A41-T-91: an unknown field in strict output causes validation failure.
- A41-T-92: a provider timeout produces a bounded retry and no duplicate artifact.
- A41-T-93: a model refusal is classified and never accepted as a valid report.
- A41-T-94: snapshot hashes remain identical on idempotent replay.

### 9.43 A42 — Case Memory Curator

- Orchestration stage: `S38`.
- Goal: Persist a validated case containing pre-match evidence, locked prediction, thesis outcomes, process metrics, variance, and lessons.
- Failure code: `MEMORY_WRITE_FAILED`.
- Default execution mode: one bounded structured-output call or one deterministic compute activity.
- Maximum self-repair attempts: one schema-repair call; then fail or degrade according to policy.

#### Inputs

- A42-IN-01: validated autopsy.
- A42-IN-02: accepted lessons.
- A42-IN-03: lock manifest.
- A42-IN-04: reliability updates.
- Input envelope MUST contain `run_id`, `fixture_id`, `cutoff_at`, `config_snapshot_id`, and `correlation_id`.
- Each input artifact MUST be referenced by immutable artifact ID and SHA-256 hash.

#### Outputs

- A42-OUT-01: case record.
- A42-OUT-02: embeddings.
- A42-OUT-03: graph edges.
- A42-OUT-04: retrieval tags.
- Output MUST validate against the agent-specific Pydantic schema version recorded in the envelope.
- Output MUST contain `status`, `confidence`, `limitations`, `citations`, and `created_at`.
- Output MUST NOT contain unbounded free-form chain-of-thought.
- Explanations MUST be concise evidence summaries suitable for audit and display.

#### Allowed sources and tools

- Allowed: current finalized case.
- Deny by default: any source, index, or tool not named by this role or runtime policy.
- Secrets MUST be injected by the adapter and MUST NOT appear in the rendered prompt.

#### Retrieval policy

- Primary rule: Writes only after validation.
- Filter order: tenant/personal scope, sport, fixture/entity, knowledge time, effective time, source class, then semantic rank.
- Retrieved chunks MUST preserve source snapshot ID, byte/character span, observed time, and content hash.
- Context packing MUST prioritize materiality and source independence over raw similarity score.
- Retrieval MUST return an explicit empty result when constraints remove all candidates.
- The agent MUST NOT ask the model to “remember” facts that are absent from the packet.

#### Mandatory checks

- A42-CHK-01: verify PII absence.
- A42-CHK-02: verify cutoff labels.
- A42-CHK-03: verify sport/competition scope.
- A42-CHK-04: verify embedding version.
- A42-CHK-90: verify every material statement has a source or is labeled inference.
- A42-CHK-91: verify no evidence has `observed_at > cutoff_at`.
- A42-CHK-92: verify confidence decreases when critical evidence is absent or contradictory.
- A42-CHK-93: verify all probabilities are finite decimals within [0, 1] when this role is authorized to emit probabilities.
- A42-CHK-94: verify the output is deterministic under the deterministic test adapter.

#### System instruction template

```text
You are Case Memory Curator, logical role A42 in MİRON BABA AI.
Your only objective is: Persist a validated case containing pre-match evidence, locked prediction, thesis outcomes, process metrics, variance, and lessons.
Use only the supplied, cutoff-safe evidence packet and explicitly allowed tools.
Never invent a fact, source, timestamp, player status, statistic, price, or provider result.
Separate observed facts, derived metrics, inferences, and unknowns.
Treat conflicting evidence as a first-class output; do not average contradictions into false certainty.
Do not select a winner or emit final outcome probabilities unless this role's stated goal explicitly authorizes it.
Do not expose private chain-of-thought. Return concise conclusions, supporting citations, checks, and uncertainty.
Do not give guaranteed outcomes, financial advice, or wagering instructions.
If a critical input is unavailable, return the declared degraded or failure status: MEMORY_WRITE_FAILED.
Return only JSON conforming exactly to schema {{schema_version}}.
Run ID: {{run_id}}
Fixture ID: {{fixture_id}}
Cutoff: {{cutoff_at}}
Prompt version: {{prompt_version}}
```

#### User/task prompt template

```text
TASK
Evaluate the supplied artifacts for Case Memory Curator.

INPUT MANIFEST
{{input_manifest_json}}

EVIDENCE PACKET
{{evidence_packet_json}}

POLICY
{{role_policy_json}}

REQUIRED OUTPUT
{{output_schema_json}}

Before returning, check identifiers, cutoff compliance, citations, units, uncertainty, and schema validity.
```

#### Acceptance tests

- A42-T-01: a fixture with a controlled PII absence defect is rejected or degraded with the expected code.
- A42-T-02: a fixture with a controlled cutoff labels defect is rejected or degraded with the expected code.
- A42-T-03: a fixture with a controlled sport/competition scope defect is rejected or degraded with the expected code.
- A42-T-04: a fixture with a controlled embedding version defect is rejected or degraded with the expected code.
- A42-T-90: an evidence item one second after cutoff is excluded and logged.
- A42-T-91: an unknown field in strict output causes validation failure.
- A42-T-92: a provider timeout produces a bounded retry and no duplicate artifact.
- A42-T-93: a model refusal is classified and never accepted as a valid report.
- A42-T-94: snapshot hashes remain identical on idempotent replay.

## 10. Model Registry, Routing, and Cost Control

### 10.1 Current verified snapshot — re-verification still mandatory

The following snapshot was researched on 2026-08-22T00:00:00+03:00. It is evidence for initial configuration, not a permanent truth.
| Role | Initial candidate | Snapshot price | Why | Hard rule |
| --- | --- | --- | --- | --- |
| Grounded current research / extraction | `gemini-3.5-flash` | $1.50 input / $9 output per MTok; Google Search grounding pricing is separate | Stable Flash with grounding-oriented positioning | Re-query official Google catalog and pricing before code/config merge |
| Cheap normalization / routine verification | `gpt-5.6-luna` | $0.20 input / $1.20 output per MTok | Cost-sensitive high-volume structured work | Must pass schema and factual evals |
| Balanced verification fallback | `gpt-5.6-terra` | $2 input / $12 output per MTok | Balanced capability and cost | Escalate only on declared triggers |
| Adversarial critic / red team | `gpt-5.6-sol` | $5 input / $30 output per MTok | Frontier reasoning for difficult criticism | Use bounded packets and budget |
| High-value committee / Chief Analyst | `claude-sonnet-5` | $2 input / $10 output per MTok in the checked August 2026 snapshot | Requested Sonnet committee role with 1M context and adaptive thinking | Pricing schedule and behavior MUST be rechecked before implementation |

Prices above are USD per one million tokens and may change.
Search/tool charges, caching, batch, priority, taxes, and platform markups are separate.
The implementation MUST store the exact resolved model ID and price-card version used for each call.

### 10.2 Official source ledger

| Source | URL | Use |
| --- | --- | --- |
| OpenAI model catalog | [link](https://developers.openai.com/api/docs/models) | Current model IDs, capabilities, and token prices |
| OpenAI model comparison | [link](https://developers.openai.com/api/docs/models/compare) | Cached input, output, context, and endpoint support |
| Anthropic Sonnet 5 guide | [link](https://platform.claude.com/docs/en/about-claude/models/whats-new-sonnet-5) | Model ID, adaptive thinking, context, and migration constraints |
| Anthropic pricing | [link](https://platform.claude.com/docs/en/about-claude/pricing) | Current and scheduled token pricing |
| Gemini model catalog | [link](https://ai.google.dev/gemini-api/docs/models) | Stable and preview model families |
| Gemini pricing | [link](https://ai.google.dev/gemini-api/docs/pricing) | Tokens, grounding, caching, free and paid tiers |
| The Odds API v4 | [link](https://the-odds-api.com/liveapi/guides/v4/index.html) | Allowed provider API behavior, quota headers, event and odds fields |
| football-data.org quickstart | [link](https://www.football-data.org/documentation/quickstart) | Fixture provider interface reference |

### 10.3 Model configuration contract

```yaml
schema_version: model-registry.v1
verified_at: "2026-08-22T00:00:00+03:00"
verification_expires_at: "2026-08-29T00:00:00+03:00"
currency: USD
routes:
  grounded_research:
    provider: google
    model_id: gemini-3.5-flash
    capabilities: [structured_output, search_grounding]
    input_usd_per_mtok: 1.50
    output_usd_per_mtok: 9.00
    max_calls_per_run: 8
  normalization:
    provider: openai
    model_id: gpt-5.6-luna
    capabilities: [structured_output, tool_calling]
    input_usd_per_mtok: 0.20
    cached_input_usd_per_mtok: 0.02
    output_usd_per_mtok: 1.20
    reasoning_effort: low
    max_calls_per_run: 20
  critic:
    provider: openai
    model_id: gpt-5.6-sol
    capabilities: [structured_output, reasoning]
    input_usd_per_mtok: 5.00
    cached_input_usd_per_mtok: 0.50
    output_usd_per_mtok: 30.00
    reasoning_effort: high
    max_calls_per_run: 4
  committee:
    provider: anthropic
    model_id: claude-sonnet-5
    capabilities: [structured_output, adaptive_thinking]
    input_usd_per_mtok: 2.00
    output_usd_per_mtok: 10.00
    max_calls_per_run: 4
policies:
  reject_expired_verification: true
  reject_unknown_price: true
  reject_missing_capability: true
  record_provider_request_id: true
  store_prompts_without_secrets: true
```

### 10.4 Re-verification gate

1. Open the official vendor model catalog, not a search snippet or third-party comparison.
2. Confirm exact model ID, availability to the account, endpoint, region, and structured-output support.
3. Confirm input, cached input, output, tool, search/grounding, batch, and priority prices.
4. Confirm context, output limit, tokenizer or parameter behavior, deprecations, and snapshot semantics.
5. Update `verified_at`, `verification_expires_at`, source URL, page hash or captured note, and reviewer.
6. Run one minimal capability probe with no sensitive data.
7. Run golden structured-output and refusal tests.
8. Fail CI/release when verification is expired or capability probes fail.

### 10.5 Pilot budget policy

| Budget | Default | Behavior |
| --- | --- | --- |
| Monthly external pilot cap | $10.00 | Hard stop; user must deliberately edit config to raise it |
| Three-day scan cap | $0.15 | Use provider data and cheap triage only |
| One full deep analysis soft cap | $0.50 | Router compresses or pauses optional expensive work |
| One full deep analysis hard cap | $2.00 | Run pauses before exceeding reservation |
| One post-match autopsy hard cap | $0.20 | Prefer deterministic computation and one cheap synthesis |
| Shadow experiment share | 10% | Cannot consume reserved production budget |

- Budget reservation occurs before each external stage.
- Actual provider usage headers and model token usage reconcile the reservation.
- Unused reservation returns immediately after stage completion.
- If price is unknown, the call is prohibited rather than estimated as zero.
- Committee calls are parallel for independence but individually budgeted.
- Cache reuse requires identical provider, model, prompt version, input hash, tool policy, and cutoff-safe context.

## 11. Provider Abstractions and Legal Boundaries

### 11.1 Mandatory provider interfaces

```python
from datetime import datetime
from typing import Protocol, Sequence

class FixtureProvider(Protocol):
    async def list_fixtures(self, *, start_utc: datetime, end_utc: datetime,
                            competition_ids: Sequence[str]) -> "FixtureBatch": ...
    async def search_fixtures(self, *, query: str, start_utc: datetime | None,
                              end_utc: datetime | None) -> "FixtureBatch": ...
    async def get_fixture(self, *, provider_fixture_id: str) -> "ProviderFixture": ...

class OddsProvider(Protocol):
    async def list_event_odds(self, *, provider_event_id: str,
                              markets: Sequence[str]) -> "OddsBatch": ...
    async def get_quota(self) -> "ProviderQuota": ...

class StatsProvider(Protocol):
    async def get_team_history(self, *, canonical_team_id: str,
                               cutoff_at: datetime) -> "TeamHistory": ...
    async def get_fixture_events(self, *, provider_fixture_id: str) -> "EventBatch": ...

class ResearchProvider(Protocol):
    async def search(self, *, query: str, cutoff_at: datetime,
                     domain_policy: "DomainPolicy") -> "ResearchBatch": ...

class WeatherProvider(Protocol):
    async def get_forecast(self, *, latitude: float, longitude: float,
                           kickoff_at: datetime) -> "WeatherSnapshot": ...
```

### 11.2 Provider compliance manifest

```yaml
provider_id: the_odds_api
provider_type: odds
enabled: false
approval_status: requires_user_key_and_terms_review
base_url: https://api.the-odds-api.com/v4
allowed_methods: [GET]
allowed_data_classes: [fixtures, current_odds, scores]
forbidden_actions: [scraping_bookmaker_pages, bet_placement, account_automation]
license_reviewed_at: null
license_review_expires_at: null
retention_policy: provider_specific
display_attribution: provider_specific
quota_headers:
  remaining: x-requests-remaining
  used: x-requests-used
  last_cost: x-requests-last
secrets:
  api_key_env: THE_ODDS_API_KEY
```

### 11.3 Legal and operational rules

1. No provider is enabled until its terms, license, retention, attribution, and personal-use permissions are reviewed.
2. No betting-site HTML scraping adapter may exist in the repository.
3. Robots permission does not replace contractual permission.
4. API access does not imply the right to redistribute raw data.
5. The UI must label odds as informational market observations from configured providers.
6. The system must not place or recommend a wager as a guaranteed or personalized financial action.
7. Provider payloads are retained only for the configured permitted duration.
8. On license expiry, the adapter stops and previously retained data follows deletion policy.
9. Live monitoring uses provider-supported endpoints and documented update intervals only.
10. Quota costs are read from provider response headers where available.

### 11.4 Live odds monitor policy

- Disabled by default in the pilot.
- Starts only for explicitly watched fixtures.
- Stops at kickoff unless an in-play licensed use case is separately approved.
- Poll interval is never faster than provider documentation and plan allow.
- Uses exponential backoff after errors and a circuit breaker after repeated provider failures.
- Stores each normalized observation as append-only time-series data.
- Deduplicates identical quotes by event, bookmaker, market, outcome, line, price, and provider timestamp.
- Does not infer “smart money” from movement without liquidity evidence.

## 12. Time, Fixture Identity, and Three-Day Scan Semantics

### 12.1 Istanbul date-window algorithm

```python
from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

ISTANBUL = ZoneInfo("Europe/Istanbul")

def three_day_window(now: datetime) -> tuple[datetime, datetime, list[str]]:
    if now.tzinfo is None:
        raise ValueError("now must be timezone-aware")
    local_now = now.astimezone(ISTANBUL)
    first_date = local_now.date()
    last_date = first_date + timedelta(days=2)
    start_local = datetime.combine(first_date, time.min, tzinfo=ISTANBUL)
    end_exclusive_local = datetime.combine(last_date + timedelta(days=1), time.min, tzinfo=ISTANBUL)
    labels = [(first_date + timedelta(days=i)).isoformat() for i in range(3)]
    return start_local.astimezone(timezone.utc), end_exclusive_local.astimezone(timezone.utc), labels
```

- The end boundary is exclusive.
- The clock is injected; tests never call the wall clock directly.
- Provider queries use UTC, while UI grouping uses Europe/Istanbul local dates.
- Kickoff postponements update the canonical fixture version and may move the fixture between date groups.
- A scan snapshot retains the fixture version visible when ranking occurred.

### 12.2 Canonical fixture resolution

1. Normalize provider strings with Unicode NFKC and conservative whitespace folding.
2. Resolve provider competition ID to canonical competition mapping.
3. Resolve home and away teams using active aliases scoped to sport, country, and effective time.
4. Compare kickoff within provider-specific tolerance, never without teams and competition.
5. Compare venue when available.
6. If one high-confidence match remains, attach provider mapping.
7. If multiple plausible matches remain, quarantine and request explicit administrative resolution.
8. Never merge fixtures based only on fuzzy team names.
9. Record every mapping rule version and confidence component.

### 12.3 Worthwhile-match ranking

```text
worthwhile_score =
  0.20 * coverage_score
+ 0.15 * source_freshness_score
+ 0.15 * competitive_relevance_score
+ 0.10 * model_information_gain_score
+ 0.10 * market_coverage_score
+ 0.10 * lineup_uncertainty_resolvability
+ 0.10 * user_interest_score
+ 0.05 * historical_case_support
+ 0.05 * kickoff_time_practicality
- 0.15 * estimated_cost_penalty
- 0.10 * unresolved_identity_penalty
- 0.10 * stale_data_penalty
```

Weights are versioned configuration and MUST be backtested.
The ranking is a triage tool, not a forecast probability.
Each row displays the top positive and negative factors.

## 13. Data Architecture

### 13.1 Storage decision

- PostgreSQL is the system of record.
- JSONB stores provider payload metadata, not ungoverned domain blobs.
- pgvector stores embeddings with explicit model and dimension versions.
- Odds and metrics use append-only partitioned tables by observation month.
- Knowledge graph edges live in relational tables until graph queries justify a separate database.
- Object storage contains raw immutable snapshots addressed by SHA-256.
- Redis is disposable and never the only copy of business state.

### 13.2 Entity catalog

#### Table: sports

- Purpose: Sport taxonomy and plugin binding.
- Primary key: UUIDv7 generated server-side unless the table is a pure association table.
- Every mutable business table MUST have `created_at`, `updated_at`, and optimistic `row_version`.
- Every run-scoped row MUST include `analysis_run_id` or a documented path to it.
- External identifiers MUST be namespaced by provider and never globally unique by assumption.
- Time values MUST use timezone-aware `timestamptz`; calendar dates use `date`.
- JSON fields MUST have a documented schema and size limit.
- Deletion behavior MUST be explicit; core audit and lock rows are append-only.
- Repository contract: `SportsRepository` exposes domain-specific methods, not arbitrary query dictionaries.
- Test fixture: `tests/golden/db/sports.json` contains a minimal valid and invalid row example.

#### Table: competitions

- Purpose: Canonical competitions and seasons.
- Primary key: UUIDv7 generated server-side unless the table is a pure association table.
- Every mutable business table MUST have `created_at`, `updated_at`, and optimistic `row_version`.
- Every run-scoped row MUST include `analysis_run_id` or a documented path to it.
- External identifiers MUST be namespaced by provider and never globally unique by assumption.
- Time values MUST use timezone-aware `timestamptz`; calendar dates use `date`.
- JSON fields MUST have a documented schema and size limit.
- Deletion behavior MUST be explicit; core audit and lock rows are append-only.
- Repository contract: `CompetitionsRepository` exposes domain-specific methods, not arbitrary query dictionaries.
- Test fixture: `tests/golden/db/competitions.json` contains a minimal valid and invalid row example.

#### Table: competition_seasons

- Purpose: Season boundaries and rules.
- Primary key: UUIDv7 generated server-side unless the table is a pure association table.
- Every mutable business table MUST have `created_at`, `updated_at`, and optimistic `row_version`.
- Every run-scoped row MUST include `analysis_run_id` or a documented path to it.
- External identifiers MUST be namespaced by provider and never globally unique by assumption.
- Time values MUST use timezone-aware `timestamptz`; calendar dates use `date`.
- JSON fields MUST have a documented schema and size limit.
- Deletion behavior MUST be explicit; core audit and lock rows are append-only.
- Repository contract: `CompetitionSeasonsRepository` exposes domain-specific methods, not arbitrary query dictionaries.
- Test fixture: `tests/golden/db/competition_seasons.json` contains a minimal valid and invalid row example.

#### Table: teams

- Purpose: Canonical teams.
- Primary key: UUIDv7 generated server-side unless the table is a pure association table.
- Every mutable business table MUST have `created_at`, `updated_at`, and optimistic `row_version`.
- Every run-scoped row MUST include `analysis_run_id` or a documented path to it.
- External identifiers MUST be namespaced by provider and never globally unique by assumption.
- Time values MUST use timezone-aware `timestamptz`; calendar dates use `date`.
- JSON fields MUST have a documented schema and size limit.
- Deletion behavior MUST be explicit; core audit and lock rows are append-only.
- Repository contract: `TeamsRepository` exposes domain-specific methods, not arbitrary query dictionaries.
- Test fixture: `tests/golden/db/teams.json` contains a minimal valid and invalid row example.

#### Table: team_aliases

- Purpose: Provider and historical team aliases.
- Primary key: UUIDv7 generated server-side unless the table is a pure association table.
- Every mutable business table MUST have `created_at`, `updated_at`, and optimistic `row_version`.
- Every run-scoped row MUST include `analysis_run_id` or a documented path to it.
- External identifiers MUST be namespaced by provider and never globally unique by assumption.
- Time values MUST use timezone-aware `timestamptz`; calendar dates use `date`.
- JSON fields MUST have a documented schema and size limit.
- Deletion behavior MUST be explicit; core audit and lock rows are append-only.
- Repository contract: `TeamAliasesRepository` exposes domain-specific methods, not arbitrary query dictionaries.
- Test fixture: `tests/golden/db/team_aliases.json` contains a minimal valid and invalid row example.

#### Table: players

- Purpose: Canonical players.
- Primary key: UUIDv7 generated server-side unless the table is a pure association table.
- Every mutable business table MUST have `created_at`, `updated_at`, and optimistic `row_version`.
- Every run-scoped row MUST include `analysis_run_id` or a documented path to it.
- External identifiers MUST be namespaced by provider and never globally unique by assumption.
- Time values MUST use timezone-aware `timestamptz`; calendar dates use `date`.
- JSON fields MUST have a documented schema and size limit.
- Deletion behavior MUST be explicit; core audit and lock rows are append-only.
- Repository contract: `PlayersRepository` exposes domain-specific methods, not arbitrary query dictionaries.
- Test fixture: `tests/golden/db/players.json` contains a minimal valid and invalid row example.

#### Table: player_aliases

- Purpose: Provider and historical player aliases.
- Primary key: UUIDv7 generated server-side unless the table is a pure association table.
- Every mutable business table MUST have `created_at`, `updated_at`, and optimistic `row_version`.
- Every run-scoped row MUST include `analysis_run_id` or a documented path to it.
- External identifiers MUST be namespaced by provider and never globally unique by assumption.
- Time values MUST use timezone-aware `timestamptz`; calendar dates use `date`.
- JSON fields MUST have a documented schema and size limit.
- Deletion behavior MUST be explicit; core audit and lock rows are append-only.
- Repository contract: `PlayerAliasesRepository` exposes domain-specific methods, not arbitrary query dictionaries.
- Test fixture: `tests/golden/db/player_aliases.json` contains a minimal valid and invalid row example.

#### Table: venues

- Purpose: Canonical venues and geospatial metadata.
- Primary key: UUIDv7 generated server-side unless the table is a pure association table.
- Every mutable business table MUST have `created_at`, `updated_at`, and optimistic `row_version`.
- Every run-scoped row MUST include `analysis_run_id` or a documented path to it.
- External identifiers MUST be namespaced by provider and never globally unique by assumption.
- Time values MUST use timezone-aware `timestamptz`; calendar dates use `date`.
- JSON fields MUST have a documented schema and size limit.
- Deletion behavior MUST be explicit; core audit and lock rows are append-only.
- Repository contract: `VenuesRepository` exposes domain-specific methods, not arbitrary query dictionaries.
- Test fixture: `tests/golden/db/venues.json` contains a minimal valid and invalid row example.

#### Table: officials

- Purpose: Canonical match officials.
- Primary key: UUIDv7 generated server-side unless the table is a pure association table.
- Every mutable business table MUST have `created_at`, `updated_at`, and optimistic `row_version`.
- Every run-scoped row MUST include `analysis_run_id` or a documented path to it.
- External identifiers MUST be namespaced by provider and never globally unique by assumption.
- Time values MUST use timezone-aware `timestamptz`; calendar dates use `date`.
- JSON fields MUST have a documented schema and size limit.
- Deletion behavior MUST be explicit; core audit and lock rows are append-only.
- Repository contract: `OfficialsRepository` exposes domain-specific methods, not arbitrary query dictionaries.
- Test fixture: `tests/golden/db/officials.json` contains a minimal valid and invalid row example.

#### Table: fixtures

- Purpose: Canonical match identity and current version.
- Primary key: UUIDv7 generated server-side unless the table is a pure association table.
- Every mutable business table MUST have `created_at`, `updated_at`, and optimistic `row_version`.
- Every run-scoped row MUST include `analysis_run_id` or a documented path to it.
- External identifiers MUST be namespaced by provider and never globally unique by assumption.
- Time values MUST use timezone-aware `timestamptz`; calendar dates use `date`.
- JSON fields MUST have a documented schema and size limit.
- Deletion behavior MUST be explicit; core audit and lock rows are append-only.
- Repository contract: `FixturesRepository` exposes domain-specific methods, not arbitrary query dictionaries.
- Test fixture: `tests/golden/db/fixtures.json` contains a minimal valid and invalid row example.

#### Table: fixture_versions

- Purpose: Append-only kickoff/status/venue revisions.
- Primary key: UUIDv7 generated server-side unless the table is a pure association table.
- Every mutable business table MUST have `created_at`, `updated_at`, and optimistic `row_version`.
- Every run-scoped row MUST include `analysis_run_id` or a documented path to it.
- External identifiers MUST be namespaced by provider and never globally unique by assumption.
- Time values MUST use timezone-aware `timestamptz`; calendar dates use `date`.
- JSON fields MUST have a documented schema and size limit.
- Deletion behavior MUST be explicit; core audit and lock rows are append-only.
- Repository contract: `FixtureVersionsRepository` exposes domain-specific methods, not arbitrary query dictionaries.
- Test fixture: `tests/golden/db/fixture_versions.json` contains a minimal valid and invalid row example.

#### Table: provider_entities

- Purpose: Provider-to-canonical mappings.
- Primary key: UUIDv7 generated server-side unless the table is a pure association table.
- Every mutable business table MUST have `created_at`, `updated_at`, and optimistic `row_version`.
- Every run-scoped row MUST include `analysis_run_id` or a documented path to it.
- External identifiers MUST be namespaced by provider and never globally unique by assumption.
- Time values MUST use timezone-aware `timestamptz`; calendar dates use `date`.
- JSON fields MUST have a documented schema and size limit.
- Deletion behavior MUST be explicit; core audit and lock rows are append-only.
- Repository contract: `ProviderEntitiesRepository` exposes domain-specific methods, not arbitrary query dictionaries.
- Test fixture: `tests/golden/db/provider_entities.json` contains a minimal valid and invalid row example.

#### Table: scan_runs

- Purpose: Three-day discovery command record.
- Primary key: UUIDv7 generated server-side unless the table is a pure association table.
- Every mutable business table MUST have `created_at`, `updated_at`, and optimistic `row_version`.
- Every run-scoped row MUST include `analysis_run_id` or a documented path to it.
- External identifiers MUST be namespaced by provider and never globally unique by assumption.
- Time values MUST use timezone-aware `timestamptz`; calendar dates use `date`.
- JSON fields MUST have a documented schema and size limit.
- Deletion behavior MUST be explicit; core audit and lock rows are append-only.
- Repository contract: `ScanRunsRepository` exposes domain-specific methods, not arbitrary query dictionaries.
- Test fixture: `tests/golden/db/scan_runs.json` contains a minimal valid and invalid row example.

#### Table: scan_candidates

- Purpose: Ranked fixture snapshot and explanations.
- Primary key: UUIDv7 generated server-side unless the table is a pure association table.
- Every mutable business table MUST have `created_at`, `updated_at`, and optimistic `row_version`.
- Every run-scoped row MUST include `analysis_run_id` or a documented path to it.
- External identifiers MUST be namespaced by provider and never globally unique by assumption.
- Time values MUST use timezone-aware `timestamptz`; calendar dates use `date`.
- JSON fields MUST have a documented schema and size limit.
- Deletion behavior MUST be explicit; core audit and lock rows are append-only.
- Repository contract: `ScanCandidatesRepository` exposes domain-specific methods, not arbitrary query dictionaries.
- Test fixture: `tests/golden/db/scan_candidates.json` contains a minimal valid and invalid row example.

#### Table: analysis_runs

- Purpose: Deep analysis aggregate.
- Primary key: UUIDv7 generated server-side unless the table is a pure association table.
- Every mutable business table MUST have `created_at`, `updated_at`, and optimistic `row_version`.
- Every run-scoped row MUST include `analysis_run_id` or a documented path to it.
- External identifiers MUST be namespaced by provider and never globally unique by assumption.
- Time values MUST use timezone-aware `timestamptz`; calendar dates use `date`.
- JSON fields MUST have a documented schema and size limit.
- Deletion behavior MUST be explicit; core audit and lock rows are append-only.
- Repository contract: `AnalysisRunsRepository` exposes domain-specific methods, not arbitrary query dictionaries.
- Test fixture: `tests/golden/db/analysis_runs.json` contains a minimal valid and invalid row example.

#### Table: run_state_transitions

- Purpose: Append-only state history.
- Primary key: UUIDv7 generated server-side unless the table is a pure association table.
- Every mutable business table MUST have `created_at`, `updated_at`, and optimistic `row_version`.
- Every run-scoped row MUST include `analysis_run_id` or a documented path to it.
- External identifiers MUST be namespaced by provider and never globally unique by assumption.
- Time values MUST use timezone-aware `timestamptz`; calendar dates use `date`.
- JSON fields MUST have a documented schema and size limit.
- Deletion behavior MUST be explicit; core audit and lock rows are append-only.
- Repository contract: `RunStateTransitionsRepository` exposes domain-specific methods, not arbitrary query dictionaries.
- Test fixture: `tests/golden/db/run_state_transitions.json` contains a minimal valid and invalid row example.

#### Table: stage_runs

- Purpose: Per-stage attempt and status.
- Primary key: UUIDv7 generated server-side unless the table is a pure association table.
- Every mutable business table MUST have `created_at`, `updated_at`, and optimistic `row_version`.
- Every run-scoped row MUST include `analysis_run_id` or a documented path to it.
- External identifiers MUST be namespaced by provider and never globally unique by assumption.
- Time values MUST use timezone-aware `timestamptz`; calendar dates use `date`.
- JSON fields MUST have a documented schema and size limit.
- Deletion behavior MUST be explicit; core audit and lock rows are append-only.
- Repository contract: `StageRunsRepository` exposes domain-specific methods, not arbitrary query dictionaries.
- Test fixture: `tests/golden/db/stage_runs.json` contains a minimal valid and invalid row example.

#### Table: activity_calls

- Purpose: External activity attempts and costs.
- Primary key: UUIDv7 generated server-side unless the table is a pure association table.
- Every mutable business table MUST have `created_at`, `updated_at`, and optimistic `row_version`.
- Every run-scoped row MUST include `analysis_run_id` or a documented path to it.
- External identifiers MUST be namespaced by provider and never globally unique by assumption.
- Time values MUST use timezone-aware `timestamptz`; calendar dates use `date`.
- JSON fields MUST have a documented schema and size limit.
- Deletion behavior MUST be explicit; core audit and lock rows are append-only.
- Repository contract: `ActivityCallsRepository` exposes domain-specific methods, not arbitrary query dictionaries.
- Test fixture: `tests/golden/db/activity_calls.json` contains a minimal valid and invalid row example.

#### Table: provider_calls

- Purpose: Provider request metadata and quota.
- Primary key: UUIDv7 generated server-side unless the table is a pure association table.
- Every mutable business table MUST have `created_at`, `updated_at`, and optimistic `row_version`.
- Every run-scoped row MUST include `analysis_run_id` or a documented path to it.
- External identifiers MUST be namespaced by provider and never globally unique by assumption.
- Time values MUST use timezone-aware `timestamptz`; calendar dates use `date`.
- JSON fields MUST have a documented schema and size limit.
- Deletion behavior MUST be explicit; core audit and lock rows are append-only.
- Repository contract: `ProviderCallsRepository` exposes domain-specific methods, not arbitrary query dictionaries.
- Test fixture: `tests/golden/db/provider_calls.json` contains a minimal valid and invalid row example.

#### Table: model_calls

- Purpose: Model request metadata, tokens, and price card.
- Primary key: UUIDv7 generated server-side unless the table is a pure association table.
- Every mutable business table MUST have `created_at`, `updated_at`, and optimistic `row_version`.
- Every run-scoped row MUST include `analysis_run_id` or a documented path to it.
- External identifiers MUST be namespaced by provider and never globally unique by assumption.
- Time values MUST use timezone-aware `timestamptz`; calendar dates use `date`.
- JSON fields MUST have a documented schema and size limit.
- Deletion behavior MUST be explicit; core audit and lock rows are append-only.
- Repository contract: `ModelCallsRepository` exposes domain-specific methods, not arbitrary query dictionaries.
- Test fixture: `tests/golden/db/model_calls.json` contains a minimal valid and invalid row example.

#### Table: config_snapshots

- Purpose: Immutable resolved configuration.
- Primary key: UUIDv7 generated server-side unless the table is a pure association table.
- Every mutable business table MUST have `created_at`, `updated_at`, and optimistic `row_version`.
- Every run-scoped row MUST include `analysis_run_id` or a documented path to it.
- External identifiers MUST be namespaced by provider and never globally unique by assumption.
- Time values MUST use timezone-aware `timestamptz`; calendar dates use `date`.
- JSON fields MUST have a documented schema and size limit.
- Deletion behavior MUST be explicit; core audit and lock rows are append-only.
- Repository contract: `ConfigSnapshotsRepository` exposes domain-specific methods, not arbitrary query dictionaries.
- Test fixture: `tests/golden/db/config_snapshots.json` contains a minimal valid and invalid row example.

#### Table: prompt_templates

- Purpose: Versioned prompt definitions.
- Primary key: UUIDv7 generated server-side unless the table is a pure association table.
- Every mutable business table MUST have `created_at`, `updated_at`, and optimistic `row_version`.
- Every run-scoped row MUST include `analysis_run_id` or a documented path to it.
- External identifiers MUST be namespaced by provider and never globally unique by assumption.
- Time values MUST use timezone-aware `timestamptz`; calendar dates use `date`.
- JSON fields MUST have a documented schema and size limit.
- Deletion behavior MUST be explicit; core audit and lock rows are append-only.
- Repository contract: `PromptTemplatesRepository` exposes domain-specific methods, not arbitrary query dictionaries.
- Test fixture: `tests/golden/db/prompt_templates.json` contains a minimal valid and invalid row example.

#### Table: prompt_renders

- Purpose: Rendered prompt hashes and artifact references.
- Primary key: UUIDv7 generated server-side unless the table is a pure association table.
- Every mutable business table MUST have `created_at`, `updated_at`, and optimistic `row_version`.
- Every run-scoped row MUST include `analysis_run_id` or a documented path to it.
- External identifiers MUST be namespaced by provider and never globally unique by assumption.
- Time values MUST use timezone-aware `timestamptz`; calendar dates use `date`.
- JSON fields MUST have a documented schema and size limit.
- Deletion behavior MUST be explicit; core audit and lock rows are append-only.
- Repository contract: `PromptRendersRepository` exposes domain-specific methods, not arbitrary query dictionaries.
- Test fixture: `tests/golden/db/prompt_renders.json` contains a minimal valid and invalid row example.

#### Table: source_snapshots

- Purpose: Immutable captured source metadata.
- Primary key: UUIDv7 generated server-side unless the table is a pure association table.
- Every mutable business table MUST have `created_at`, `updated_at`, and optimistic `row_version`.
- Every run-scoped row MUST include `analysis_run_id` or a documented path to it.
- External identifiers MUST be namespaced by provider and never globally unique by assumption.
- Time values MUST use timezone-aware `timestamptz`; calendar dates use `date`.
- JSON fields MUST have a documented schema and size limit.
- Deletion behavior MUST be explicit; core audit and lock rows are append-only.
- Repository contract: `SourceSnapshotsRepository` exposes domain-specific methods, not arbitrary query dictionaries.
- Test fixture: `tests/golden/db/source_snapshots.json` contains a minimal valid and invalid row example.

#### Table: source_clusters

- Purpose: Duplicate and syndication clusters so copied reports do not count as independent corroboration.
- Primary key: UUIDv7 generated server-side unless the table is a pure association table.
- Every mutable business table MUST have `created_at`, `updated_at`, and optimistic `row_version`.
- Every run-scoped row MUST include `analysis_run_id` or a documented path to it.
- External identifiers MUST be namespaced by provider and never globally unique by assumption.
- Time values MUST use timezone-aware `timestamptz`; calendar dates use `date`.
- JSON fields MUST have a documented schema and size limit.
- Deletion behavior MUST be explicit; core audit and lock rows are append-only.
- Repository contract: `SourceClustersRepository` exposes domain-specific methods, not arbitrary query dictionaries.
- Test fixture: `tests/golden/db/source_clusters.json` contains a minimal valid and invalid row example.

#### Table: evidence_items

- Purpose: Atomic captured evidence.
- Primary key: UUIDv7 generated server-side unless the table is a pure association table.
- Every mutable business table MUST have `created_at`, `updated_at`, and optimistic `row_version`.
- Every run-scoped row MUST include `analysis_run_id` or a documented path to it.
- External identifiers MUST be namespaced by provider and never globally unique by assumption.
- Time values MUST use timezone-aware `timestamptz`; calendar dates use `date`.
- JSON fields MUST have a documented schema and size limit.
- Deletion behavior MUST be explicit; core audit and lock rows are append-only.
- Repository contract: `EvidenceItemsRepository` exposes domain-specific methods, not arbitrary query dictionaries.
- Test fixture: `tests/golden/db/evidence_items.json` contains a minimal valid and invalid row example.

#### Table: claims

- Purpose: Normalized propositions.
- Primary key: UUIDv7 generated server-side unless the table is a pure association table.
- Every mutable business table MUST have `created_at`, `updated_at`, and optimistic `row_version`.
- Every run-scoped row MUST include `analysis_run_id` or a documented path to it.
- External identifiers MUST be namespaced by provider and never globally unique by assumption.
- Time values MUST use timezone-aware `timestamptz`; calendar dates use `date`.
- JSON fields MUST have a documented schema and size limit.
- Deletion behavior MUST be explicit; core audit and lock rows are append-only.
- Repository contract: `ClaimsRepository` exposes domain-specific methods, not arbitrary query dictionaries.
- Test fixture: `tests/golden/db/claims.json` contains a minimal valid and invalid row example.

#### Table: interpretations

- Purpose: Explicit analytical inferences linked to claims and never stored as raw fact.
- Primary key: UUIDv7 generated server-side unless the table is a pure association table.
- Every mutable business table MUST have `created_at`, `updated_at`, and optimistic `row_version`.
- Every run-scoped row MUST include `analysis_run_id` or a documented path to it.
- External identifiers MUST be namespaced by provider and never globally unique by assumption.
- Time values MUST use timezone-aware `timestamptz`; calendar dates use `date`.
- JSON fields MUST have a documented schema and size limit.
- Deletion behavior MUST be explicit; core audit and lock rows are append-only.
- Repository contract: `InterpretationsRepository` exposes domain-specific methods, not arbitrary query dictionaries.
- Test fixture: `tests/golden/db/interpretations.json` contains a minimal valid and invalid row example.

#### Table: claim_evidence

- Purpose: Many-to-many claim provenance.
- Primary key: UUIDv7 generated server-side unless the table is a pure association table.
- Every mutable business table MUST have `created_at`, `updated_at`, and optimistic `row_version`.
- Every run-scoped row MUST include `analysis_run_id` or a documented path to it.
- External identifiers MUST be namespaced by provider and never globally unique by assumption.
- Time values MUST use timezone-aware `timestamptz`; calendar dates use `date`.
- JSON fields MUST have a documented schema and size limit.
- Deletion behavior MUST be explicit; core audit and lock rows are append-only.
- Repository contract: `ClaimEvidenceRepository` exposes domain-specific methods, not arbitrary query dictionaries.
- Test fixture: `tests/golden/db/claim_evidence.json` contains a minimal valid and invalid row example.

#### Table: contradiction_sets

- Purpose: Material conflict groups.
- Primary key: UUIDv7 generated server-side unless the table is a pure association table.
- Every mutable business table MUST have `created_at`, `updated_at`, and optimistic `row_version`.
- Every run-scoped row MUST include `analysis_run_id` or a documented path to it.
- External identifiers MUST be namespaced by provider and never globally unique by assumption.
- Time values MUST use timezone-aware `timestamptz`; calendar dates use `date`.
- JSON fields MUST have a documented schema and size limit.
- Deletion behavior MUST be explicit; core audit and lock rows are append-only.
- Repository contract: `ContradictionSetsRepository` exposes domain-specific methods, not arbitrary query dictionaries.
- Test fixture: `tests/golden/db/contradiction_sets.json` contains a minimal valid and invalid row example.

#### Table: contradiction_members

- Purpose: Claims participating in conflicts.
- Primary key: UUIDv7 generated server-side unless the table is a pure association table.
- Every mutable business table MUST have `created_at`, `updated_at`, and optimistic `row_version`.
- Every run-scoped row MUST include `analysis_run_id` or a documented path to it.
- External identifiers MUST be namespaced by provider and never globally unique by assumption.
- Time values MUST use timezone-aware `timestamptz`; calendar dates use `date`.
- JSON fields MUST have a documented schema and size limit.
- Deletion behavior MUST be explicit; core audit and lock rows are append-only.
- Repository contract: `ContradictionMembersRepository` exposes domain-specific methods, not arbitrary query dictionaries.
- Test fixture: `tests/golden/db/contradiction_members.json` contains a minimal valid and invalid row example.

#### Table: freshness_policies

- Purpose: TTL and stale behavior by source class.
- Primary key: UUIDv7 generated server-side unless the table is a pure association table.
- Every mutable business table MUST have `created_at`, `updated_at`, and optimistic `row_version`.
- Every run-scoped row MUST include `analysis_run_id` or a documented path to it.
- External identifiers MUST be namespaced by provider and never globally unique by assumption.
- Time values MUST use timezone-aware `timestamptz`; calendar dates use `date`.
- JSON fields MUST have a documented schema and size limit.
- Deletion behavior MUST be explicit; core audit and lock rows are append-only.
- Repository contract: `FreshnessPoliciesRepository` exposes domain-specific methods, not arbitrary query dictionaries.
- Test fixture: `tests/golden/db/freshness_policies.json` contains a minimal valid and invalid row example.

#### Table: team_match_stats

- Purpose: Normalized team-match metrics.
- Primary key: UUIDv7 generated server-side unless the table is a pure association table.
- Every mutable business table MUST have `created_at`, `updated_at`, and optimistic `row_version`.
- Every run-scoped row MUST include `analysis_run_id` or a documented path to it.
- External identifiers MUST be namespaced by provider and never globally unique by assumption.
- Time values MUST use timezone-aware `timestamptz`; calendar dates use `date`.
- JSON fields MUST have a documented schema and size limit.
- Deletion behavior MUST be explicit; core audit and lock rows are append-only.
- Repository contract: `TeamMatchStatsRepository` exposes domain-specific methods, not arbitrary query dictionaries.
- Test fixture: `tests/golden/db/team_match_stats.json` contains a minimal valid and invalid row example.

#### Table: player_match_stats

- Purpose: Normalized player-match metrics.
- Primary key: UUIDv7 generated server-side unless the table is a pure association table.
- Every mutable business table MUST have `created_at`, `updated_at`, and optimistic `row_version`.
- Every run-scoped row MUST include `analysis_run_id` or a documented path to it.
- External identifiers MUST be namespaced by provider and never globally unique by assumption.
- Time values MUST use timezone-aware `timestamptz`; calendar dates use `date`.
- JSON fields MUST have a documented schema and size limit.
- Deletion behavior MUST be explicit; core audit and lock rows are append-only.
- Repository contract: `PlayerMatchStatsRepository` exposes domain-specific methods, not arbitrary query dictionaries.
- Test fixture: `tests/golden/db/player_match_stats.json` contains a minimal valid and invalid row example.

#### Table: lineup_observations

- Purpose: Probabilistic and confirmed lineups.
- Primary key: UUIDv7 generated server-side unless the table is a pure association table.
- Every mutable business table MUST have `created_at`, `updated_at`, and optimistic `row_version`.
- Every run-scoped row MUST include `analysis_run_id` or a documented path to it.
- External identifiers MUST be namespaced by provider and never globally unique by assumption.
- Time values MUST use timezone-aware `timestamptz`; calendar dates use `date`.
- JSON fields MUST have a documented schema and size limit.
- Deletion behavior MUST be explicit; core audit and lock rows are append-only.
- Repository contract: `LineupObservationsRepository` exposes domain-specific methods, not arbitrary query dictionaries.
- Test fixture: `tests/golden/db/lineup_observations.json` contains a minimal valid and invalid row example.

#### Table: availability_observations

- Purpose: Injury, suspension, and selection status.
- Primary key: UUIDv7 generated server-side unless the table is a pure association table.
- Every mutable business table MUST have `created_at`, `updated_at`, and optimistic `row_version`.
- Every run-scoped row MUST include `analysis_run_id` or a documented path to it.
- External identifiers MUST be namespaced by provider and never globally unique by assumption.
- Time values MUST use timezone-aware `timestamptz`; calendar dates use `date`.
- JSON fields MUST have a documented schema and size limit.
- Deletion behavior MUST be explicit; core audit and lock rows are append-only.
- Repository contract: `AvailabilityObservationsRepository` exposes domain-specific methods, not arbitrary query dictionaries.
- Test fixture: `tests/golden/db/availability_observations.json` contains a minimal valid and invalid row example.

#### Table: weather_observations

- Purpose: Forecast snapshots by venue and target time.
- Primary key: UUIDv7 generated server-side unless the table is a pure association table.
- Every mutable business table MUST have `created_at`, `updated_at`, and optimistic `row_version`.
- Every run-scoped row MUST include `analysis_run_id` or a documented path to it.
- External identifiers MUST be namespaced by provider and never globally unique by assumption.
- Time values MUST use timezone-aware `timestamptz`; calendar dates use `date`.
- JSON fields MUST have a documented schema and size limit.
- Deletion behavior MUST be explicit; core audit and lock rows are append-only.
- Repository contract: `WeatherObservationsRepository` exposes domain-specific methods, not arbitrary query dictionaries.
- Test fixture: `tests/golden/db/weather_observations.json` contains a minimal valid and invalid row example.

#### Table: odds_snapshots

- Purpose: Append-only normalized market observations.
- Primary key: UUIDv7 generated server-side unless the table is a pure association table.
- Every mutable business table MUST have `created_at`, `updated_at`, and optimistic `row_version`.
- Every run-scoped row MUST include `analysis_run_id` or a documented path to it.
- External identifiers MUST be namespaced by provider and never globally unique by assumption.
- Time values MUST use timezone-aware `timestamptz`; calendar dates use `date`.
- JSON fields MUST have a documented schema and size limit.
- Deletion behavior MUST be explicit; core audit and lock rows are append-only.
- Repository contract: `OddsSnapshotsRepository` exposes domain-specific methods, not arbitrary query dictionaries.
- Test fixture: `tests/golden/db/odds_snapshots.json` contains a minimal valid and invalid row example.

#### Table: live_odds_snapshots

- Purpose: Append-only LIVE MARKET observations isolated from pre-match evidence.
- Primary key: UUIDv7 generated server-side unless the table is a pure association table.
- Every mutable business table MUST have `created_at`, `updated_at`, and optimistic `row_version`.
- Every run-scoped row MUST include `analysis_run_id` or a documented path to it.
- External identifiers MUST be namespaced by provider and never globally unique by assumption.
- Time values MUST use timezone-aware `timestamptz`; calendar dates use `date`.
- JSON fields MUST have a documented schema and size limit.
- Deletion behavior MUST be explicit; core audit and lock rows are append-only.
- Repository contract: `LiveOddsSnapshotsRepository` exposes domain-specific methods, not arbitrary query dictionaries.
- Test fixture: `tests/golden/db/live_odds_snapshots.json` contains a minimal valid and invalid row example.

#### Table: market_mappings

- Purpose: Provider market to canonical market mapping.
- Primary key: UUIDv7 generated server-side unless the table is a pure association table.
- Every mutable business table MUST have `created_at`, `updated_at`, and optimistic `row_version`.
- Every run-scoped row MUST include `analysis_run_id` or a documented path to it.
- External identifiers MUST be namespaced by provider and never globally unique by assumption.
- Time values MUST use timezone-aware `timestamptz`; calendar dates use `date`.
- JSON fields MUST have a documented schema and size limit.
- Deletion behavior MUST be explicit; core audit and lock rows are append-only.
- Repository contract: `MarketMappingsRepository` exposes domain-specific methods, not arbitrary query dictionaries.
- Test fixture: `tests/golden/db/market_mappings.json` contains a minimal valid and invalid row example.

#### Table: feature_sets

- Purpose: Versioned feature manifests.
- Primary key: UUIDv7 generated server-side unless the table is a pure association table.
- Every mutable business table MUST have `created_at`, `updated_at`, and optimistic `row_version`.
- Every run-scoped row MUST include `analysis_run_id` or a documented path to it.
- External identifiers MUST be namespaced by provider and never globally unique by assumption.
- Time values MUST use timezone-aware `timestamptz`; calendar dates use `date`.
- JSON fields MUST have a documented schema and size limit.
- Deletion behavior MUST be explicit; core audit and lock rows are append-only.
- Repository contract: `FeatureSetsRepository` exposes domain-specific methods, not arbitrary query dictionaries.
- Test fixture: `tests/golden/db/feature_sets.json` contains a minimal valid and invalid row example.

#### Table: feature_values

- Purpose: Typed feature observations and missingness.
- Primary key: UUIDv7 generated server-side unless the table is a pure association table.
- Every mutable business table MUST have `created_at`, `updated_at`, and optimistic `row_version`.
- Every run-scoped row MUST include `analysis_run_id` or a documented path to it.
- External identifiers MUST be namespaced by provider and never globally unique by assumption.
- Time values MUST use timezone-aware `timestamptz`; calendar dates use `date`.
- JSON fields MUST have a documented schema and size limit.
- Deletion behavior MUST be explicit; core audit and lock rows are append-only.
- Repository contract: `FeatureValuesRepository` exposes domain-specific methods, not arbitrary query dictionaries.
- Test fixture: `tests/golden/db/feature_values.json` contains a minimal valid and invalid row example.

#### Table: model_artifacts

- Purpose: Quant model binaries and metadata.
- Primary key: UUIDv7 generated server-side unless the table is a pure association table.
- Every mutable business table MUST have `created_at`, `updated_at`, and optimistic `row_version`.
- Every run-scoped row MUST include `analysis_run_id` or a documented path to it.
- External identifiers MUST be namespaced by provider and never globally unique by assumption.
- Time values MUST use timezone-aware `timestamptz`; calendar dates use `date`.
- JSON fields MUST have a documented schema and size limit.
- Deletion behavior MUST be explicit; core audit and lock rows are append-only.
- Repository contract: `ModelArtifactsRepository` exposes domain-specific methods, not arbitrary query dictionaries.
- Test fixture: `tests/golden/db/model_artifacts.json` contains a minimal valid and invalid row example.

#### Table: calibrators

- Purpose: Versioned probability calibration artifacts.
- Primary key: UUIDv7 generated server-side unless the table is a pure association table.
- Every mutable business table MUST have `created_at`, `updated_at`, and optimistic `row_version`.
- Every run-scoped row MUST include `analysis_run_id` or a documented path to it.
- External identifiers MUST be namespaced by provider and never globally unique by assumption.
- Time values MUST use timezone-aware `timestamptz`; calendar dates use `date`.
- JSON fields MUST have a documented schema and size limit.
- Deletion behavior MUST be explicit; core audit and lock rows are append-only.
- Repository contract: `CalibratorsRepository` exposes domain-specific methods, not arbitrary query dictionaries.
- Test fixture: `tests/golden/db/calibrators.json` contains a minimal valid and invalid row example.

#### Table: quant_predictions

- Purpose: Per-model distributions and diagnostics.
- Primary key: UUIDv7 generated server-side unless the table is a pure association table.
- Every mutable business table MUST have `created_at`, `updated_at`, and optimistic `row_version`.
- Every run-scoped row MUST include `analysis_run_id` or a documented path to it.
- External identifiers MUST be namespaced by provider and never globally unique by assumption.
- Time values MUST use timezone-aware `timestamptz`; calendar dates use `date`.
- JSON fields MUST have a documented schema and size limit.
- Deletion behavior MUST be explicit; core audit and lock rows are append-only.
- Repository contract: `QuantPredictionsRepository` exposes domain-specific methods, not arbitrary query dictionaries.
- Test fixture: `tests/golden/db/quant_predictions.json` contains a minimal valid and invalid row example.

#### Table: agent_reports

- Purpose: Validated stage reports.
- Primary key: UUIDv7 generated server-side unless the table is a pure association table.
- Every mutable business table MUST have `created_at`, `updated_at`, and optimistic `row_version`.
- Every run-scoped row MUST include `analysis_run_id` or a documented path to it.
- External identifiers MUST be namespaced by provider and never globally unique by assumption.
- Time values MUST use timezone-aware `timestamptz`; calendar dates use `date`.
- JSON fields MUST have a documented schema and size limit.
- Deletion behavior MUST be explicit; core audit and lock rows are append-only.
- Repository contract: `AgentReportsRepository` exposes domain-specific methods, not arbitrary query dictionaries.
- Test fixture: `tests/golden/db/agent_reports.json` contains a minimal valid and invalid row example.

#### Table: sonnet_syntheses

- Purpose: Prediction-forbidden evidence, tactical, player/squad, and quant/market syntheses.
- Primary key: UUIDv7 generated server-side unless the table is a pure association table.
- Every mutable business table MUST have `created_at`, `updated_at`, and optimistic `row_version`.
- Every run-scoped row MUST include `analysis_run_id` or a documented path to it.
- External identifiers MUST be namespaced by provider and never globally unique by assumption.
- Time values MUST use timezone-aware `timestamptz`; calendar dates use `date`.
- JSON fields MUST have a documented schema and size limit.
- Deletion behavior MUST be explicit; core audit and lock rows are append-only.
- Repository contract: `SonnetSynthesesRepository` exposes domain-specific methods, not arbitrary query dictionaries.
- Test fixture: `tests/golden/db/sonnet_syntheses.json` contains a minimal valid and invalid row example.

#### Table: pre_match_theses

- Purpose: Versioned falsifiable theses produced before prediction lock.
- Primary key: UUIDv7 generated server-side unless the table is a pure association table.
- Every mutable business table MUST have `created_at`, `updated_at`, and optimistic `row_version`.
- Every run-scoped row MUST include `analysis_run_id` or a documented path to it.
- External identifiers MUST be namespaced by provider and never globally unique by assumption.
- Time values MUST use timezone-aware `timestamptz`; calendar dates use `date`.
- JSON fields MUST have a documented schema and size limit.
- Deletion behavior MUST be explicit; core audit and lock rows are append-only.
- Repository contract: `PreMatchThesesRepository` exposes domain-specific methods, not arbitrary query dictionaries.
- Test fixture: `tests/golden/db/pre_match_theses.json` contains a minimal valid and invalid row example.

#### Table: scenario_nodes

- Purpose: Scenario tree nodes and triggers.
- Primary key: UUIDv7 generated server-side unless the table is a pure association table.
- Every mutable business table MUST have `created_at`, `updated_at`, and optimistic `row_version`.
- Every run-scoped row MUST include `analysis_run_id` or a documented path to it.
- External identifiers MUST be namespaced by provider and never globally unique by assumption.
- Time values MUST use timezone-aware `timestamptz`; calendar dates use `date`.
- JSON fields MUST have a documented schema and size limit.
- Deletion behavior MUST be explicit; core audit and lock rows are append-only.
- Repository contract: `ScenarioNodesRepository` exposes domain-specific methods, not arbitrary query dictionaries.
- Test fixture: `tests/golden/db/scenario_nodes.json` contains a minimal valid and invalid row example.

#### Table: critic_findings

- Purpose: Structured defects and severity.
- Primary key: UUIDv7 generated server-side unless the table is a pure association table.
- Every mutable business table MUST have `created_at`, `updated_at`, and optimistic `row_version`.
- Every run-scoped row MUST include `analysis_run_id` or a documented path to it.
- External identifiers MUST be namespaced by provider and never globally unique by assumption.
- Time values MUST use timezone-aware `timestamptz`; calendar dates use `date`.
- JSON fields MUST have a documented schema and size limit.
- Deletion behavior MUST be explicit; core audit and lock rows are append-only.
- Repository contract: `CriticFindingsRepository` exposes domain-specific methods, not arbitrary query dictionaries.
- Test fixture: `tests/golden/db/critic_findings.json` contains a minimal valid and invalid row example.

#### Table: forecast_versions

- Purpose: Chief and revised forecasts.
- Primary key: UUIDv7 generated server-side unless the table is a pure association table.
- Every mutable business table MUST have `created_at`, `updated_at`, and optimistic `row_version`.
- Every run-scoped row MUST include `analysis_run_id` or a documented path to it.
- External identifiers MUST be namespaced by provider and never globally unique by assumption.
- Time values MUST use timezone-aware `timestamptz`; calendar dates use `date`.
- JSON fields MUST have a documented schema and size limit.
- Deletion behavior MUST be explicit; core audit and lock rows are append-only.
- Repository contract: `ForecastVersionsRepository` exposes domain-specific methods, not arbitrary query dictionaries.
- Test fixture: `tests/golden/db/forecast_versions.json` contains a minimal valid and invalid row example.

#### Table: prediction_locks

- Purpose: Immutable approved forecast manifest.
- Primary key: UUIDv7 generated server-side unless the table is a pure association table.
- Every mutable business table MUST have `created_at`, `updated_at`, and optimistic `row_version`.
- Every run-scoped row MUST include `analysis_run_id` or a documented path to it.
- External identifiers MUST be namespaced by provider and never globally unique by assumption.
- Time values MUST use timezone-aware `timestamptz`; calendar dates use `date`.
- JSON fields MUST have a documented schema and size limit.
- Deletion behavior MUST be explicit; core audit and lock rows are append-only.
- Repository contract: `PredictionLocksRepository` exposes domain-specific methods, not arbitrary query dictionaries.
- Test fixture: `tests/golden/db/prediction_locks.json` contains a minimal valid and invalid row example.

#### Table: match_results

- Purpose: Official result facts.
- Primary key: UUIDv7 generated server-side unless the table is a pure association table.
- Every mutable business table MUST have `created_at`, `updated_at`, and optimistic `row_version`.
- Every run-scoped row MUST include `analysis_run_id` or a documented path to it.
- External identifiers MUST be namespaced by provider and never globally unique by assumption.
- Time values MUST use timezone-aware `timestamptz`; calendar dates use `date`.
- JSON fields MUST have a documented schema and size limit.
- Deletion behavior MUST be explicit; core audit and lock rows are append-only.
- Repository contract: `MatchResultsRepository` exposes domain-specific methods, not arbitrary query dictionaries.
- Test fixture: `tests/golden/db/match_results.json` contains a minimal valid and invalid row example.

#### Table: match_event_snapshots

- Purpose: Post-match event timeline.
- Primary key: UUIDv7 generated server-side unless the table is a pure association table.
- Every mutable business table MUST have `created_at`, `updated_at`, and optimistic `row_version`.
- Every run-scoped row MUST include `analysis_run_id` or a documented path to it.
- External identifiers MUST be namespaced by provider and never globally unique by assumption.
- Time values MUST use timezone-aware `timestamptz`; calendar dates use `date`.
- JSON fields MUST have a documented schema and size limit.
- Deletion behavior MUST be explicit; core audit and lock rows are append-only.
- Repository contract: `MatchEventSnapshotsRepository` exposes domain-specific methods, not arbitrary query dictionaries.
- Test fixture: `tests/golden/db/match_event_snapshots.json` contains a minimal valid and invalid row example.

#### Table: autopsies

- Purpose: Locked forecast evaluation.
- Primary key: UUIDv7 generated server-side unless the table is a pure association table.
- Every mutable business table MUST have `created_at`, `updated_at`, and optimistic `row_version`.
- Every run-scoped row MUST include `analysis_run_id` or a documented path to it.
- External identifiers MUST be namespaced by provider and never globally unique by assumption.
- Time values MUST use timezone-aware `timestamptz`; calendar dates use `date`.
- JSON fields MUST have a documented schema and size limit.
- Deletion behavior MUST be explicit; core audit and lock rows are append-only.
- Repository contract: `AutopsiesRepository` exposes domain-specific methods, not arbitrary query dictionaries.
- Test fixture: `tests/golden/db/autopsies.json` contains a minimal valid and invalid row example.

#### Table: variance_attributions

- Purpose: Outcome deviation categories.
- Primary key: UUIDv7 generated server-side unless the table is a pure association table.
- Every mutable business table MUST have `created_at`, `updated_at`, and optimistic `row_version`.
- Every run-scoped row MUST include `analysis_run_id` or a documented path to it.
- External identifiers MUST be namespaced by provider and never globally unique by assumption.
- Time values MUST use timezone-aware `timestamptz`; calendar dates use `date`.
- JSON fields MUST have a documented schema and size limit.
- Deletion behavior MUST be explicit; core audit and lock rows are append-only.
- Repository contract: `VarianceAttributionsRepository` exposes domain-specific methods, not arbitrary query dictionaries.
- Test fixture: `tests/golden/db/variance_attributions.json` contains a minimal valid and invalid row example.

#### Table: thesis_outcomes

- Purpose: Per-thesis process verdict and supporting post-match evidence.
- Primary key: UUIDv7 generated server-side unless the table is a pure association table.
- Every mutable business table MUST have `created_at`, `updated_at`, and optimistic `row_version`.
- Every run-scoped row MUST include `analysis_run_id` or a documented path to it.
- External identifiers MUST be namespaced by provider and never globally unique by assumption.
- Time values MUST use timezone-aware `timestamptz`; calendar dates use `date`.
- JSON fields MUST have a documented schema and size limit.
- Deletion behavior MUST be explicit; core audit and lock rows are append-only.
- Repository contract: `ThesisOutcomesRepository` exposes domain-specific methods, not arbitrary query dictionaries.
- Test fixture: `tests/golden/db/thesis_outcomes.json` contains a minimal valid and invalid row example.

#### Table: agent_reliability

- Purpose: Versioned task- and scope-specific agent reliability estimates.
- Primary key: UUIDv7 generated server-side unless the table is a pure association table.
- Every mutable business table MUST have `created_at`, `updated_at`, and optimistic `row_version`.
- Every run-scoped row MUST include `analysis_run_id` or a documented path to it.
- External identifiers MUST be namespaced by provider and never globally unique by assumption.
- Time values MUST use timezone-aware `timestamptz`; calendar dates use `date`.
- JSON fields MUST have a documented schema and size limit.
- Deletion behavior MUST be explicit; core audit and lock rows are append-only.
- Repository contract: `AgentReliabilityRepository` exposes domain-specific methods, not arbitrary query dictionaries.
- Test fixture: `tests/golden/db/agent_reliability.json` contains a minimal valid and invalid row example.

#### Table: source_reliability

- Purpose: Versioned domain- and claim-type-specific source reliability estimates.
- Primary key: UUIDv7 generated server-side unless the table is a pure association table.
- Every mutable business table MUST have `created_at`, `updated_at`, and optimistic `row_version`.
- Every run-scoped row MUST include `analysis_run_id` or a documented path to it.
- External identifiers MUST be namespaced by provider and never globally unique by assumption.
- Time values MUST use timezone-aware `timestamptz`; calendar dates use `date`.
- JSON fields MUST have a documented schema and size limit.
- Deletion behavior MUST be explicit; core audit and lock rows are append-only.
- Repository contract: `SourceReliabilityRepository` exposes domain-specific methods, not arbitrary query dictionaries.
- Test fixture: `tests/golden/db/source_reliability.json` contains a minimal valid and invalid row example.

#### Table: lessons

- Purpose: Candidate and validated lessons.
- Primary key: UUIDv7 generated server-side unless the table is a pure association table.
- Every mutable business table MUST have `created_at`, `updated_at`, and optimistic `row_version`.
- Every run-scoped row MUST include `analysis_run_id` or a documented path to it.
- External identifiers MUST be namespaced by provider and never globally unique by assumption.
- Time values MUST use timezone-aware `timestamptz`; calendar dates use `date`.
- JSON fields MUST have a documented schema and size limit.
- Deletion behavior MUST be explicit; core audit and lock rows are append-only.
- Repository contract: `LessonsRepository` exposes domain-specific methods, not arbitrary query dictionaries.
- Test fixture: `tests/golden/db/lessons.json` contains a minimal valid and invalid row example.

#### Table: cases

- Purpose: Final case-memory packages.
- Primary key: UUIDv7 generated server-side unless the table is a pure association table.
- Every mutable business table MUST have `created_at`, `updated_at`, and optimistic `row_version`.
- Every run-scoped row MUST include `analysis_run_id` or a documented path to it.
- External identifiers MUST be namespaced by provider and never globally unique by assumption.
- Time values MUST use timezone-aware `timestamptz`; calendar dates use `date`.
- JSON fields MUST have a documented schema and size limit.
- Deletion behavior MUST be explicit; core audit and lock rows are append-only.
- Repository contract: `CasesRepository` exposes domain-specific methods, not arbitrary query dictionaries.
- Test fixture: `tests/golden/db/cases.json` contains a minimal valid and invalid row example.

#### Table: documents

- Purpose: RAG document records.
- Primary key: UUIDv7 generated server-side unless the table is a pure association table.
- Every mutable business table MUST have `created_at`, `updated_at`, and optimistic `row_version`.
- Every run-scoped row MUST include `analysis_run_id` or a documented path to it.
- External identifiers MUST be namespaced by provider and never globally unique by assumption.
- Time values MUST use timezone-aware `timestamptz`; calendar dates use `date`.
- JSON fields MUST have a documented schema and size limit.
- Deletion behavior MUST be explicit; core audit and lock rows are append-only.
- Repository contract: `DocumentsRepository` exposes domain-specific methods, not arbitrary query dictionaries.
- Test fixture: `tests/golden/db/documents.json` contains a minimal valid and invalid row example.

#### Table: document_chunks

- Purpose: Chunk text, spans, and embeddings.
- Primary key: UUIDv7 generated server-side unless the table is a pure association table.
- Every mutable business table MUST have `created_at`, `updated_at`, and optimistic `row_version`.
- Every run-scoped row MUST include `analysis_run_id` or a documented path to it.
- External identifiers MUST be namespaced by provider and never globally unique by assumption.
- Time values MUST use timezone-aware `timestamptz`; calendar dates use `date`.
- JSON fields MUST have a documented schema and size limit.
- Deletion behavior MUST be explicit; core audit and lock rows are append-only.
- Repository contract: `DocumentChunksRepository` exposes domain-specific methods, not arbitrary query dictionaries.
- Test fixture: `tests/golden/db/document_chunks.json` contains a minimal valid and invalid row example.

#### Table: knowledge_edges

- Purpose: Canonical graph relationships.
- Primary key: UUIDv7 generated server-side unless the table is a pure association table.
- Every mutable business table MUST have `created_at`, `updated_at`, and optimistic `row_version`.
- Every run-scoped row MUST include `analysis_run_id` or a documented path to it.
- External identifiers MUST be namespaced by provider and never globally unique by assumption.
- Time values MUST use timezone-aware `timestamptz`; calendar dates use `date`.
- JSON fields MUST have a documented schema and size limit.
- Deletion behavior MUST be explicit; core audit and lock rows are append-only.
- Repository contract: `KnowledgeEdgesRepository` exposes domain-specific methods, not arbitrary query dictionaries.
- Test fixture: `tests/golden/db/knowledge_edges.json` contains a minimal valid and invalid row example.

#### Table: experiments

- Purpose: Shadow experiment definitions.
- Primary key: UUIDv7 generated server-side unless the table is a pure association table.
- Every mutable business table MUST have `created_at`, `updated_at`, and optimistic `row_version`.
- Every run-scoped row MUST include `analysis_run_id` or a documented path to it.
- External identifiers MUST be namespaced by provider and never globally unique by assumption.
- Time values MUST use timezone-aware `timestamptz`; calendar dates use `date`.
- JSON fields MUST have a documented schema and size limit.
- Deletion behavior MUST be explicit; core audit and lock rows are append-only.
- Repository contract: `ExperimentsRepository` exposes domain-specific methods, not arbitrary query dictionaries.
- Test fixture: `tests/golden/db/experiments.json` contains a minimal valid and invalid row example.

#### Table: experiment_assignments

- Purpose: Deterministic run assignments.
- Primary key: UUIDv7 generated server-side unless the table is a pure association table.
- Every mutable business table MUST have `created_at`, `updated_at`, and optimistic `row_version`.
- Every run-scoped row MUST include `analysis_run_id` or a documented path to it.
- External identifiers MUST be namespaced by provider and never globally unique by assumption.
- Time values MUST use timezone-aware `timestamptz`; calendar dates use `date`.
- JSON fields MUST have a documented schema and size limit.
- Deletion behavior MUST be explicit; core audit and lock rows are append-only.
- Repository contract: `ExperimentAssignmentsRepository` exposes domain-specific methods, not arbitrary query dictionaries.
- Test fixture: `tests/golden/db/experiment_assignments.json` contains a minimal valid and invalid row example.

#### Table: experiment_results

- Purpose: Offline comparison metrics.
- Primary key: UUIDv7 generated server-side unless the table is a pure association table.
- Every mutable business table MUST have `created_at`, `updated_at`, and optimistic `row_version`.
- Every run-scoped row MUST include `analysis_run_id` or a documented path to it.
- External identifiers MUST be namespaced by provider and never globally unique by assumption.
- Time values MUST use timezone-aware `timestamptz`; calendar dates use `date`.
- JSON fields MUST have a documented schema and size limit.
- Deletion behavior MUST be explicit; core audit and lock rows are append-only.
- Repository contract: `ExperimentResultsRepository` exposes domain-specific methods, not arbitrary query dictionaries.
- Test fixture: `tests/golden/db/experiment_results.json` contains a minimal valid and invalid row example.

#### Table: budget_ledgers

- Purpose: Reservations, actuals, and releases.
- Primary key: UUIDv7 generated server-side unless the table is a pure association table.
- Every mutable business table MUST have `created_at`, `updated_at`, and optimistic `row_version`.
- Every run-scoped row MUST include `analysis_run_id` or a documented path to it.
- External identifiers MUST be namespaced by provider and never globally unique by assumption.
- Time values MUST use timezone-aware `timestamptz`; calendar dates use `date`.
- JSON fields MUST have a documented schema and size limit.
- Deletion behavior MUST be explicit; core audit and lock rows are append-only.
- Repository contract: `BudgetLedgersRepository` exposes domain-specific methods, not arbitrary query dictionaries.
- Test fixture: `tests/golden/db/budget_ledgers.json` contains a minimal valid and invalid row example.

#### Table: audit_events

- Purpose: Security and domain audit trail.
- Primary key: UUIDv7 generated server-side unless the table is a pure association table.
- Every mutable business table MUST have `created_at`, `updated_at`, and optimistic `row_version`.
- Every run-scoped row MUST include `analysis_run_id` or a documented path to it.
- External identifiers MUST be namespaced by provider and never globally unique by assumption.
- Time values MUST use timezone-aware `timestamptz`; calendar dates use `date`.
- JSON fields MUST have a documented schema and size limit.
- Deletion behavior MUST be explicit; core audit and lock rows are append-only.
- Repository contract: `AuditEventsRepository` exposes domain-specific methods, not arbitrary query dictionaries.
- Test fixture: `tests/golden/db/audit_events.json` contains a minimal valid and invalid row example.

#### Table: idempotency_records

- Purpose: Command result replay records.
- Primary key: UUIDv7 generated server-side unless the table is a pure association table.
- Every mutable business table MUST have `created_at`, `updated_at`, and optimistic `row_version`.
- Every run-scoped row MUST include `analysis_run_id` or a documented path to it.
- External identifiers MUST be namespaced by provider and never globally unique by assumption.
- Time values MUST use timezone-aware `timestamptz`; calendar dates use `date`.
- JSON fields MUST have a documented schema and size limit.
- Deletion behavior MUST be explicit; core audit and lock rows are append-only.
- Repository contract: `IdempotencyRecordsRepository` exposes domain-specific methods, not arbitrary query dictionaries.
- Test fixture: `tests/golden/db/idempotency_records.json` contains a minimal valid and invalid row example.

#### Table: outbox_events

- Purpose: Transactional event publication.
- Primary key: UUIDv7 generated server-side unless the table is a pure association table.
- Every mutable business table MUST have `created_at`, `updated_at`, and optimistic `row_version`.
- Every run-scoped row MUST include `analysis_run_id` or a documented path to it.
- External identifiers MUST be namespaced by provider and never globally unique by assumption.
- Time values MUST use timezone-aware `timestamptz`; calendar dates use `date`.
- JSON fields MUST have a documented schema and size limit.
- Deletion behavior MUST be explicit; core audit and lock rows are append-only.
- Repository contract: `OutboxEventsRepository` exposes domain-specific methods, not arbitrary query dictionaries.
- Test fixture: `tests/golden/db/outbox_events.json` contains a minimal valid and invalid row example.

#### Table: quarantine_records

- Purpose: Invalid or ambiguous input records.
- Primary key: UUIDv7 generated server-side unless the table is a pure association table.
- Every mutable business table MUST have `created_at`, `updated_at`, and optimistic `row_version`.
- Every run-scoped row MUST include `analysis_run_id` or a documented path to it.
- External identifiers MUST be namespaced by provider and never globally unique by assumption.
- Time values MUST use timezone-aware `timestamptz`; calendar dates use `date`.
- JSON fields MUST have a documented schema and size limit.
- Deletion behavior MUST be explicit; core audit and lock rows are append-only.
- Repository contract: `QuarantineRecordsRepository` exposes domain-specific methods, not arbitrary query dictionaries.
- Test fixture: `tests/golden/db/quarantine_records.json` contains a minimal valid and invalid row example.

### 13.3 Core SQL schema excerpt

```sql
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE analysis_runs (
  id uuid PRIMARY KEY,
  fixture_id uuid NOT NULL REFERENCES fixtures(id),
  state text NOT NULL,
  cutoff_at timestamptz NOT NULL,
  kickoff_at_snapshot timestamptz NOT NULL,
  config_snapshot_id uuid NOT NULL REFERENCES config_snapshots(id),
  prompt_bundle_version text NOT NULL,
  reserved_cost_usd numeric(12,6) NOT NULL DEFAULT 0,
  actual_cost_usd numeric(12,6) NOT NULL DEFAULT 0,
  degraded_reasons jsonb NOT NULL DEFAULT '[]'::jsonb,
  correlation_id uuid NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  row_version bigint NOT NULL DEFAULT 0,
  CHECK (cutoff_at <= kickoff_at_snapshot),
  CHECK (reserved_cost_usd >= 0),
  CHECK (actual_cost_usd >= 0)
);

CREATE TABLE source_snapshots (
  id uuid PRIMARY KEY,
  analysis_run_id uuid REFERENCES analysis_runs(id),
  source_type text NOT NULL,
  canonical_url text,
  provider_id text,
  provider_object_id text,
  published_at timestamptz,
  provider_updated_at timestamptz,
  observed_at timestamptz NOT NULL,
  retrieved_at timestamptz NOT NULL,
  content_sha256 char(64) NOT NULL,
  object_uri text NOT NULL,
  media_type text NOT NULL,
  license_policy_version text NOT NULL,
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  UNIQUE (content_sha256, object_uri)
);

CREATE TABLE claims (
  id uuid PRIMARY KEY,
  analysis_run_id uuid NOT NULL REFERENCES analysis_runs(id),
  subject_entity_type text NOT NULL,
  subject_entity_id uuid NOT NULL,
  predicate text NOT NULL,
  object_json jsonb NOT NULL,
  effective_start timestamptz,
  effective_end timestamptz,
  observed_at timestamptz NOT NULL,
  confidence numeric(5,4) NOT NULL,
  status text NOT NULL,
  normalization_version text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  CHECK (confidence BETWEEN 0 AND 1),
  CHECK (effective_end IS NULL OR effective_start IS NULL OR effective_end >= effective_start)
);

CREATE TABLE odds_snapshots (
  id uuid NOT NULL,
  fixture_id uuid NOT NULL REFERENCES fixtures(id),
  provider_id text NOT NULL,
  provider_event_id text NOT NULL,
  bookmaker_key text NOT NULL,
  market_key text NOT NULL,
  outcome_key text NOT NULL,
  line numeric(12,4),
  decimal_price numeric(12,6) NOT NULL,
  provider_updated_at timestamptz,
  observed_at timestamptz NOT NULL,
  raw_snapshot_id uuid NOT NULL REFERENCES source_snapshots(id),
  mapping_version text NOT NULL,
  PRIMARY KEY (id, observed_at),
  CHECK (decimal_price > 1.0)
) PARTITION BY RANGE (observed_at);

CREATE TABLE prediction_locks (
  id uuid PRIMARY KEY,
  analysis_run_id uuid NOT NULL UNIQUE REFERENCES analysis_runs(id),
  forecast_version_id uuid NOT NULL UNIQUE REFERENCES forecast_versions(id),
  cutoff_at timestamptz NOT NULL,
  locked_at timestamptz NOT NULL,
  kickoff_at_snapshot timestamptz NOT NULL,
  manifest_json jsonb NOT NULL,
  manifest_sha256 char(64) NOT NULL UNIQUE,
  signature text,
  object_uri text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  CHECK (locked_at < kickoff_at_snapshot)
);

CREATE OR REPLACE FUNCTION forbid_prediction_lock_mutation()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  RAISE EXCEPTION 'prediction_locks are immutable';
END;
$$;

CREATE TRIGGER prediction_locks_no_update
BEFORE UPDATE OR DELETE ON prediction_locks
FOR EACH ROW EXECUTE FUNCTION forbid_prediction_lock_mutation();
```

### 13.4 Bitemporal requirements

- `observed_at` means when this system first captured the datum.
- `provider_updated_at` means when the provider says it last updated the datum.
- `published_at` means when a publisher exposed the information.
- `effective_start` and `effective_end` mean when the claim applies.
- Backtests filter primarily on `observed_at <= simulated_cutoff` and verify provider timestamps as secondary evidence.
- Corrections append a new row and supersession edge; they do not rewrite past knowledge.

## 14. RAG, Vector, Time-Series, and Knowledge Graph Architecture

### 14.1 Corpus partitions

| Partition | Examples | Default retrieval |
| --- | --- | --- |
| current_run_evidence | Captured official sources, news, provider notes | Hybrid exact/vector with cutoff |
| entity_profile | Team, player, coach, venue summaries | Entity ID plus effective time |
| methodology | Metric definitions, model cards, provider field semantics | Exact version then semantic fallback |
| case_memory | Locked historical cases and validated lessons | Sport/competition/time filters plus similarity |
| market_history | Odds snapshots and closing lines | Structured time-series only |
| quarantine | Rejected or ambiguous records | Never available to agents by default |

### 14.2 Chunking requirements

- Chunk boundaries follow semantic sections or provider records, not arbitrary fixed token slices alone.
- Every chunk stores document ID, source snapshot ID, character span, heading path, language, and content hash.
- Tables preserve row and column headers in each chunk.
- Lineup and injury statements remain atomic and entity-linked.
- Embedding text contains normalized entity labels but never overwrites the original excerpt.
- Re-embedding creates a new embedding version; it does not mutate prior vectors.

### 14.3 Retrieval scoring

```text
retrieval_score =
  w_semantic * cosine_similarity
+ w_lexical * normalized_bm25
+ w_entity * entity_match
+ w_recency * source_class_recency
+ w_authority * source_trust
+ w_independence * source_independence
- w_stale * stale_penalty
- w_conflict * unresolved_conflict_penalty
```

Weights are agent-specific and versioned.
The system logs the pre-filter candidate count, post-filter count, and chosen chunk scores.

### 14.4 Agent-specific retrieval matrix

| Agent group | Allowed partitions | Forbidden partitions | Top-k | Key filters |
| --- | --- | --- | --- | --- |
| Research | none initially; external permitted search | case outcomes | provider-defined | cutoff, domain policy |
| Claim normalization | current_run_evidence | case_memory, quarantine | 20 | run, source verified |
| Statistical specialists | methodology plus structured SQL | web opinion | 8 | metric version, competition |
| Tactical specialist | current_run_evidence, entity_profile, case_memory | quarantine | 16 | coach era, personnel, cutoff |
| Market analyst | market_history, methodology | web tips | structured | bookmaker, market, timestamp |
| Historical similarity | case_memory | current case outcomes | 12 | sport, era, feature completeness |
| Sonnet synthesis roles | frozen Match Intelligence Dossier only | all live indexes | 0 | packet hash and role-specific slice |
| Red team | all pre-cutoff validated artifacts | post-match data | 12 | cutoff, attack query log |
| Autopsy | current locked case and post-match facts | future cases | 0 | case ID |
| Lesson validator | validated cases and lessons | unvalidated candidate corpus | 20 | scope, replication |

### 14.5 Knowledge graph edge types

- `PLAYS_FOR`: MUST include source, knowledge-time interval, effective-time interval where applicable, and confidence.
- `COACHED_BY`: MUST include source, knowledge-time interval, effective-time interval where applicable, and confidence.
- `COMPETES_IN`: MUST include source, knowledge-time interval, effective-time interval where applicable, and confidence.
- `PLAYED_AT`: MUST include source, knowledge-time interval, effective-time interval where applicable, and confidence.
- `OFFICIATED_BY`: MUST include source, knowledge-time interval, effective-time interval where applicable, and confidence.
- `SOURCE_SUPPORTS_CLAIM`: MUST include source, knowledge-time interval, effective-time interval where applicable, and confidence.
- `SOURCE_CONTRADICTS_CLAIM`: MUST include source, knowledge-time interval, effective-time interval where applicable, and confidence.
- `CLAIM_SUPERSEDES_CLAIM`: MUST include source, knowledge-time interval, effective-time interval where applicable, and confidence.
- `FIXTURE_HAS_VERSION`: MUST include source, knowledge-time interval, effective-time interval where applicable, and confidence.
- `PLAYER_EXPECTED_AVAILABLE`: MUST include source, knowledge-time interval, effective-time interval where applicable, and confidence.
- `PLAYER_CONFIRMED_AVAILABLE`: MUST include source, knowledge-time interval, effective-time interval where applicable, and confidence.
- `TEAM_USED_FORMATION`: MUST include source, knowledge-time interval, effective-time interval where applicable, and confidence.
- `CASE_SIMILAR_TO`: MUST include source, knowledge-time interval, effective-time interval where applicable, and confidence.
- `LESSON_APPLIES_TO`: MUST include source, knowledge-time interval, effective-time interval where applicable, and confidence.
- `MODEL_USED_FEATURE_SET`: MUST include source, knowledge-time interval, effective-time interval where applicable, and confidence.
- `FORECAST_DERIVED_FROM`: MUST include source, knowledge-time interval, effective-time interval where applicable, and confidence.
- `LOCK_CONTAINS_ARTIFACT`: MUST include source, knowledge-time interval, effective-time interval where applicable, and confidence.

## 15. Structured Contracts

### 15.1 Universal agent envelope

```python
from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import Annotated, Generic, Literal, TypeVar
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field

class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

class ArtifactRef(StrictModel):
    artifact_id: UUID
    artifact_type: str
    schema_version: str
    sha256: Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]

class Citation(StrictModel):
    claim_id: UUID | None = None
    source_snapshot_id: UUID
    start_offset: int | None = Field(default=None, ge=0)
    end_offset: int | None = Field(default=None, ge=0)
    observed_at: datetime
    note: str = Field(min_length=1, max_length=500)

class ReportStatus(StrEnum):
    COMPLETE = "complete"
    DEGRADED = "degraded"
    FAILED = "failed"
    REFUSED = "refused"

T = TypeVar("T")

class AgentEnvelope(StrictModel, Generic[T]):
    schema_version: str
    agent_id: str
    run_id: UUID
    fixture_id: UUID
    stage_run_id: UUID
    cutoff_at: datetime
    config_snapshot_id: UUID
    prompt_version: str
    model_route: str
    status: ReportStatus
    confidence: Annotated[Decimal, Field(ge=0, le=1)]
    limitations: tuple[str, ...]
    citations: tuple[Citation, ...]
    inputs: tuple[ArtifactRef, ...]
    payload: T
    created_at: datetime
```

### 15.2 Forecast contract

```python
class OutcomeProbability(StrictModel):
    outcome: Literal["home", "draw", "away"]
    probability: Annotated[Decimal, Field(ge=0, le=1)]
    lower: Annotated[Decimal, Field(ge=0, le=1)]
    upper: Annotated[Decimal, Field(ge=0, le=1)]

class MarketComparison(StrictModel):
    market_key: str
    outcome_key: str
    model_probability: Annotated[Decimal, Field(ge=0, le=1)]
    fair_market_probability: Annotated[Decimal, Field(ge=0, le=1)]
    difference: Decimal
    margin_removal_method: Literal["multiplicative", "power", "shin"]
    quote_observed_at: datetime
    stale: bool

class FinalForecast(StrictModel):
    schema_version: Literal["final-forecast.v1"]
    fixture_id: UUID
    cutoff_at: datetime
    outcome_probabilities: tuple[OutcomeProbability, OutcomeProbability, OutcomeProbability]
    expected_home_goals: Decimal | None
    expected_away_goals: Decimal | None
    calibration_status: Literal["validated", "provisional", "out_of_domain", "unavailable"]
    confidence: Annotated[Decimal, Field(ge=0, le=1)]
    uncertainty_drivers: tuple[str, ...]
    decisive_evidence: tuple[Citation, ...]
    dissent_summary: tuple[str, ...]
    scenarios: tuple[UUID, ...]
    market_comparisons: tuple[MarketComparison, ...]
    publish_status: Literal["publish", "degraded_publish", "no_publish"]
    responsible_use_notice: str

    def validate_sum(self) -> "FinalForecast":
        total = sum(x.probability for x in self.outcome_probabilities)
        if abs(total - Decimal("1")) > Decimal("0.000001"):
            raise ValueError("outcome probabilities must sum to one")
        return self
```

### 15.3 Source and claim JSON example

```json
{
  "schema_version": "claim.v1",
  "claim_id": "018f0000-0000-7000-8000-000000000001",
  "run_id": "018f0000-0000-7000-8000-000000000002",
  "subject": {
    "entity_type": "player",
    "entity_id": "018f0000-0000-7000-8000-000000000003"
  },
  "predicate": "availability_status",
  "object": {
    "status": "doubtful",
    "probability_available": 0.35,
    "scope": "starting_xi"
  },
  "effective_start": "2026-08-22T18:00:00+03:00",
  "effective_end": "2026-08-22T23:59:59+03:00",
  "observed_at": "2026-08-22T10:15:00+03:00",
  "confidence": 0.72,
  "status": "unresolved",
  "citations": [
    {
      "source_snapshot_id": "018f0000-0000-7000-8000-000000000004",
      "start_offset": 120,
      "end_offset": 278,
      "observed_at": "2026-08-22T10:15:00+03:00",
      "note": "Official training update does not confirm match availability."
    }
  ]
}
```

### 15.4 Prediction lock manifest

```json
{
  "schema_version": "prediction-lock.v1",
  "analysis_run_id": "018f0000-0000-7000-8000-000000000010",
  "fixture_id": "018f0000-0000-7000-8000-000000000011",
  "forecast_version_id": "018f0000-0000-7000-8000-000000000012",
  "cutoff_at": "2026-08-22T17:00:00+03:00",
  "locked_at": "2026-08-22T17:05:12+03:00",
  "kickoff_at_snapshot": "2026-08-22T20:00:00+03:00",
  "config_snapshot_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "prompt_bundle_sha256": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
  "forecast_sha256": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
  "input_artifacts_merkle_root": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
  "code_commit": "0123456789abcdef0123456789abcdef01234567",
  "database_migration_head": "20260822_0001",
  "signature_algorithm": "ed25519",
  "signature": null
}
```

## 16. API Specification

### 16.1 Endpoint catalog

#### POST /api/v1/scans

- Purpose: Start an idempotent three-day scan.
- Request contract: `StartScanRequest`.
- Success contract: `ScanAccepted`.
- Authentication: local personal session in pilot; all mutating routes require CSRF-safe same-site session or bearer token.
- Authorization: the caller must own the personal workspace; no cross-workspace access.
- Correlation: accept or generate `X-Correlation-ID` and return it.
- Idempotency: mutating commands require `Idempotency-Key`; repeat returns the original logical result.
- Validation: reject unknown fields and invalid timezone-aware timestamps with HTTP 422.
- Conflict: invalid state or ambiguous identity returns HTTP 409 with a stable error code.
- Rate limit: return HTTP 429 with `Retry-After` for bounded local/provider limits.
- Errors: RFC 9457-style problem details with no secrets or raw provider payload.
- Observability: one server span and child spans for database/provider work.
- Test: authorized happy path, invalid input, replay, conflict, timeout, and ownership boundary.

#### GET /api/v1/scans/{scan_id}

- Purpose: Get scan summary.
- Request contract: `none`.
- Success contract: `ScanSummary`.
- Authentication: local personal session in pilot; all mutating routes require CSRF-safe same-site session or bearer token.
- Authorization: the caller must own the personal workspace; no cross-workspace access.
- Correlation: accept or generate `X-Correlation-ID` and return it.
- Idempotency: mutating commands require `Idempotency-Key`; repeat returns the original logical result.
- Validation: reject unknown fields and invalid timezone-aware timestamps with HTTP 422.
- Conflict: invalid state or ambiguous identity returns HTTP 409 with a stable error code.
- Rate limit: return HTTP 429 with `Retry-After` for bounded local/provider limits.
- Errors: RFC 9457-style problem details with no secrets or raw provider payload.
- Observability: one server span and child spans for database/provider work.
- Test: authorized happy path, invalid input, replay, conflict, timeout, and ownership boundary.

#### GET /api/v1/scans/{scan_id}/candidates

- Purpose: List ranked candidates.
- Request contract: `CandidateQuery`.
- Success contract: `CandidatePage`.
- Authentication: local personal session in pilot; all mutating routes require CSRF-safe same-site session or bearer token.
- Authorization: the caller must own the personal workspace; no cross-workspace access.
- Correlation: accept or generate `X-Correlation-ID` and return it.
- Idempotency: mutating commands require `Idempotency-Key`; repeat returns the original logical result.
- Validation: reject unknown fields and invalid timezone-aware timestamps with HTTP 422.
- Conflict: invalid state or ambiguous identity returns HTTP 409 with a stable error code.
- Rate limit: return HTTP 429 with `Retry-After` for bounded local/provider limits.
- Errors: RFC 9457-style problem details with no secrets or raw provider payload.
- Observability: one server span and child spans for database/provider work.
- Test: authorized happy path, invalid input, replay, conflict, timeout, and ownership boundary.

#### POST /api/v1/scans/{scan_id}/cancel

- Purpose: Cancel scan.
- Request contract: `CancelRequest`.
- Success contract: `OperationAccepted`.
- Authentication: local personal session in pilot; all mutating routes require CSRF-safe same-site session or bearer token.
- Authorization: the caller must own the personal workspace; no cross-workspace access.
- Correlation: accept or generate `X-Correlation-ID` and return it.
- Idempotency: mutating commands require `Idempotency-Key`; repeat returns the original logical result.
- Validation: reject unknown fields and invalid timezone-aware timestamps with HTTP 422.
- Conflict: invalid state or ambiguous identity returns HTTP 409 with a stable error code.
- Rate limit: return HTTP 429 with `Retry-After` for bounded local/provider limits.
- Errors: RFC 9457-style problem details with no secrets or raw provider payload.
- Observability: one server span and child spans for database/provider work.
- Test: authorized happy path, invalid input, replay, conflict, timeout, and ownership boundary.

#### GET /api/v1/fixtures/search

- Purpose: Search supported fixtures.
- Request contract: `FixtureSearchQuery`.
- Success contract: `FixtureSearchPage`.
- Authentication: local personal session in pilot; all mutating routes require CSRF-safe same-site session or bearer token.
- Authorization: the caller must own the personal workspace; no cross-workspace access.
- Correlation: accept or generate `X-Correlation-ID` and return it.
- Idempotency: mutating commands require `Idempotency-Key`; repeat returns the original logical result.
- Validation: reject unknown fields and invalid timezone-aware timestamps with HTTP 422.
- Conflict: invalid state or ambiguous identity returns HTTP 409 with a stable error code.
- Rate limit: return HTTP 429 with `Retry-After` for bounded local/provider limits.
- Errors: RFC 9457-style problem details with no secrets or raw provider payload.
- Observability: one server span and child spans for database/provider work.
- Test: authorized happy path, invalid input, replay, conflict, timeout, and ownership boundary.

#### GET /api/v1/fixtures/{fixture_id}

- Purpose: Get canonical fixture.
- Request contract: `none`.
- Success contract: `FixtureDetail`.
- Authentication: local personal session in pilot; all mutating routes require CSRF-safe same-site session or bearer token.
- Authorization: the caller must own the personal workspace; no cross-workspace access.
- Correlation: accept or generate `X-Correlation-ID` and return it.
- Idempotency: mutating commands require `Idempotency-Key`; repeat returns the original logical result.
- Validation: reject unknown fields and invalid timezone-aware timestamps with HTTP 422.
- Conflict: invalid state or ambiguous identity returns HTTP 409 with a stable error code.
- Rate limit: return HTTP 429 with `Retry-After` for bounded local/provider limits.
- Errors: RFC 9457-style problem details with no secrets or raw provider payload.
- Observability: one server span and child spans for database/provider work.
- Test: authorized happy path, invalid input, replay, conflict, timeout, and ownership boundary.

#### GET /api/v1/fixtures/{fixture_id}/coverage

- Purpose: Get provider coverage.
- Request contract: `none`.
- Success contract: `CoverageReport`.
- Authentication: local personal session in pilot; all mutating routes require CSRF-safe same-site session or bearer token.
- Authorization: the caller must own the personal workspace; no cross-workspace access.
- Correlation: accept or generate `X-Correlation-ID` and return it.
- Idempotency: mutating commands require `Idempotency-Key`; repeat returns the original logical result.
- Validation: reject unknown fields and invalid timezone-aware timestamps with HTTP 422.
- Conflict: invalid state or ambiguous identity returns HTTP 409 with a stable error code.
- Rate limit: return HTTP 429 with `Retry-After` for bounded local/provider limits.
- Errors: RFC 9457-style problem details with no secrets or raw provider payload.
- Observability: one server span and child spans for database/provider work.
- Test: authorized happy path, invalid input, replay, conflict, timeout, and ownership boundary.

#### POST /api/v1/analysis-runs

- Purpose: Start deep analysis.
- Request contract: `StartAnalysisRequest`.
- Success contract: `AnalysisAccepted`.
- Authentication: local personal session in pilot; all mutating routes require CSRF-safe same-site session or bearer token.
- Authorization: the caller must own the personal workspace; no cross-workspace access.
- Correlation: accept or generate `X-Correlation-ID` and return it.
- Idempotency: mutating commands require `Idempotency-Key`; repeat returns the original logical result.
- Validation: reject unknown fields and invalid timezone-aware timestamps with HTTP 422.
- Conflict: invalid state or ambiguous identity returns HTTP 409 with a stable error code.
- Rate limit: return HTTP 429 with `Retry-After` for bounded local/provider limits.
- Errors: RFC 9457-style problem details with no secrets or raw provider payload.
- Observability: one server span and child spans for database/provider work.
- Test: authorized happy path, invalid input, replay, conflict, timeout, and ownership boundary.

#### GET /api/v1/analysis-runs/{run_id}

- Purpose: Get run summary.
- Request contract: `none`.
- Success contract: `AnalysisRunSummary`.
- Authentication: local personal session in pilot; all mutating routes require CSRF-safe same-site session or bearer token.
- Authorization: the caller must own the personal workspace; no cross-workspace access.
- Correlation: accept or generate `X-Correlation-ID` and return it.
- Idempotency: mutating commands require `Idempotency-Key`; repeat returns the original logical result.
- Validation: reject unknown fields and invalid timezone-aware timestamps with HTTP 422.
- Conflict: invalid state or ambiguous identity returns HTTP 409 with a stable error code.
- Rate limit: return HTTP 429 with `Retry-After` for bounded local/provider limits.
- Errors: RFC 9457-style problem details with no secrets or raw provider payload.
- Observability: one server span and child spans for database/provider work.
- Test: authorized happy path, invalid input, replay, conflict, timeout, and ownership boundary.

#### POST /api/v1/analysis-runs/{run_id}/cancel

- Purpose: Request cancellation.
- Request contract: `CancelRequest`.
- Success contract: `OperationAccepted`.
- Authentication: local personal session in pilot; all mutating routes require CSRF-safe same-site session or bearer token.
- Authorization: the caller must own the personal workspace; no cross-workspace access.
- Correlation: accept or generate `X-Correlation-ID` and return it.
- Idempotency: mutating commands require `Idempotency-Key`; repeat returns the original logical result.
- Validation: reject unknown fields and invalid timezone-aware timestamps with HTTP 422.
- Conflict: invalid state or ambiguous identity returns HTTP 409 with a stable error code.
- Rate limit: return HTTP 429 with `Retry-After` for bounded local/provider limits.
- Errors: RFC 9457-style problem details with no secrets or raw provider payload.
- Observability: one server span and child spans for database/provider work.
- Test: authorized happy path, invalid input, replay, conflict, timeout, and ownership boundary.

#### POST /api/v1/analysis-runs/{run_id}/resume

- Purpose: Resume permitted pause.
- Request contract: `ResumeRequest`.
- Success contract: `OperationAccepted`.
- Authentication: local personal session in pilot; all mutating routes require CSRF-safe same-site session or bearer token.
- Authorization: the caller must own the personal workspace; no cross-workspace access.
- Correlation: accept or generate `X-Correlation-ID` and return it.
- Idempotency: mutating commands require `Idempotency-Key`; repeat returns the original logical result.
- Validation: reject unknown fields and invalid timezone-aware timestamps with HTTP 422.
- Conflict: invalid state or ambiguous identity returns HTTP 409 with a stable error code.
- Rate limit: return HTTP 429 with `Retry-After` for bounded local/provider limits.
- Errors: RFC 9457-style problem details with no secrets or raw provider payload.
- Observability: one server span and child spans for database/provider work.
- Test: authorized happy path, invalid input, replay, conflict, timeout, and ownership boundary.

#### GET /api/v1/analysis-runs/{run_id}/events

- Purpose: Stream progress via SSE.
- Request contract: `Last-Event-ID`.
- Success contract: `text/event-stream`.
- Authentication: local personal session in pilot; all mutating routes require CSRF-safe same-site session or bearer token.
- Authorization: the caller must own the personal workspace; no cross-workspace access.
- Correlation: accept or generate `X-Correlation-ID` and return it.
- Idempotency: mutating commands require `Idempotency-Key`; repeat returns the original logical result.
- Validation: reject unknown fields and invalid timezone-aware timestamps with HTTP 422.
- Conflict: invalid state or ambiguous identity returns HTTP 409 with a stable error code.
- Rate limit: return HTTP 429 with `Retry-After` for bounded local/provider limits.
- Errors: RFC 9457-style problem details with no secrets or raw provider payload.
- Observability: one server span and child spans for database/provider work.
- Test: authorized happy path, invalid input, replay, conflict, timeout, and ownership boundary.

#### GET /api/v1/analysis-runs/{run_id}/stages

- Purpose: List stage states.
- Request contract: `none`.
- Success contract: `StageRunList`.
- Authentication: local personal session in pilot; all mutating routes require CSRF-safe same-site session or bearer token.
- Authorization: the caller must own the personal workspace; no cross-workspace access.
- Correlation: accept or generate `X-Correlation-ID` and return it.
- Idempotency: mutating commands require `Idempotency-Key`; repeat returns the original logical result.
- Validation: reject unknown fields and invalid timezone-aware timestamps with HTTP 422.
- Conflict: invalid state or ambiguous identity returns HTTP 409 with a stable error code.
- Rate limit: return HTTP 429 with `Retry-After` for bounded local/provider limits.
- Errors: RFC 9457-style problem details with no secrets or raw provider payload.
- Observability: one server span and child spans for database/provider work.
- Test: authorized happy path, invalid input, replay, conflict, timeout, and ownership boundary.

#### GET /api/v1/analysis-runs/{run_id}/stages/{stage_id}

- Purpose: Get stage report.
- Request contract: `none`.
- Success contract: `StageDetail`.
- Authentication: local personal session in pilot; all mutating routes require CSRF-safe same-site session or bearer token.
- Authorization: the caller must own the personal workspace; no cross-workspace access.
- Correlation: accept or generate `X-Correlation-ID` and return it.
- Idempotency: mutating commands require `Idempotency-Key`; repeat returns the original logical result.
- Validation: reject unknown fields and invalid timezone-aware timestamps with HTTP 422.
- Conflict: invalid state or ambiguous identity returns HTTP 409 with a stable error code.
- Rate limit: return HTTP 429 with `Retry-After` for bounded local/provider limits.
- Errors: RFC 9457-style problem details with no secrets or raw provider payload.
- Observability: one server span and child spans for database/provider work.
- Test: authorized happy path, invalid input, replay, conflict, timeout, and ownership boundary.

#### GET /api/v1/analysis-runs/{run_id}/evidence

- Purpose: List evidence.
- Request contract: `EvidenceQuery`.
- Success contract: `EvidencePage`.
- Authentication: local personal session in pilot; all mutating routes require CSRF-safe same-site session or bearer token.
- Authorization: the caller must own the personal workspace; no cross-workspace access.
- Correlation: accept or generate `X-Correlation-ID` and return it.
- Idempotency: mutating commands require `Idempotency-Key`; repeat returns the original logical result.
- Validation: reject unknown fields and invalid timezone-aware timestamps with HTTP 422.
- Conflict: invalid state or ambiguous identity returns HTTP 409 with a stable error code.
- Rate limit: return HTTP 429 with `Retry-After` for bounded local/provider limits.
- Errors: RFC 9457-style problem details with no secrets or raw provider payload.
- Observability: one server span and child spans for database/provider work.
- Test: authorized happy path, invalid input, replay, conflict, timeout, and ownership boundary.

#### GET /api/v1/analysis-runs/{run_id}/claims

- Purpose: List normalized claims.
- Request contract: `ClaimQuery`.
- Success contract: `ClaimPage`.
- Authentication: local personal session in pilot; all mutating routes require CSRF-safe same-site session or bearer token.
- Authorization: the caller must own the personal workspace; no cross-workspace access.
- Correlation: accept or generate `X-Correlation-ID` and return it.
- Idempotency: mutating commands require `Idempotency-Key`; repeat returns the original logical result.
- Validation: reject unknown fields and invalid timezone-aware timestamps with HTTP 422.
- Conflict: invalid state or ambiguous identity returns HTTP 409 with a stable error code.
- Rate limit: return HTTP 429 with `Retry-After` for bounded local/provider limits.
- Errors: RFC 9457-style problem details with no secrets or raw provider payload.
- Observability: one server span and child spans for database/provider work.
- Test: authorized happy path, invalid input, replay, conflict, timeout, and ownership boundary.

#### GET /api/v1/analysis-runs/{run_id}/contradictions

- Purpose: List contradictions.
- Request contract: `none`.
- Success contract: `ContradictionList`.
- Authentication: local personal session in pilot; all mutating routes require CSRF-safe same-site session or bearer token.
- Authorization: the caller must own the personal workspace; no cross-workspace access.
- Correlation: accept or generate `X-Correlation-ID` and return it.
- Idempotency: mutating commands require `Idempotency-Key`; repeat returns the original logical result.
- Validation: reject unknown fields and invalid timezone-aware timestamps with HTTP 422.
- Conflict: invalid state or ambiguous identity returns HTTP 409 with a stable error code.
- Rate limit: return HTTP 429 with `Retry-After` for bounded local/provider limits.
- Errors: RFC 9457-style problem details with no secrets or raw provider payload.
- Observability: one server span and child spans for database/provider work.
- Test: authorized happy path, invalid input, replay, conflict, timeout, and ownership boundary.

#### GET /api/v1/analysis-runs/{run_id}/quant

- Purpose: Get quant report.
- Request contract: `none`.
- Success contract: `QuantReport`.
- Authentication: local personal session in pilot; all mutating routes require CSRF-safe same-site session or bearer token.
- Authorization: the caller must own the personal workspace; no cross-workspace access.
- Correlation: accept or generate `X-Correlation-ID` and return it.
- Idempotency: mutating commands require `Idempotency-Key`; repeat returns the original logical result.
- Validation: reject unknown fields and invalid timezone-aware timestamps with HTTP 422.
- Conflict: invalid state or ambiguous identity returns HTTP 409 with a stable error code.
- Rate limit: return HTTP 429 with `Retry-After` for bounded local/provider limits.
- Errors: RFC 9457-style problem details with no secrets or raw provider payload.
- Observability: one server span and child spans for database/provider work.
- Test: authorized happy path, invalid input, replay, conflict, timeout, and ownership boundary.

#### GET /api/v1/analysis-runs/{run_id}/markets

- Purpose: Get market intelligence.
- Request contract: `MarketQuery`.
- Success contract: `MarketReport`.
- Authentication: local personal session in pilot; all mutating routes require CSRF-safe same-site session or bearer token.
- Authorization: the caller must own the personal workspace; no cross-workspace access.
- Correlation: accept or generate `X-Correlation-ID` and return it.
- Idempotency: mutating commands require `Idempotency-Key`; repeat returns the original logical result.
- Validation: reject unknown fields and invalid timezone-aware timestamps with HTTP 422.
- Conflict: invalid state or ambiguous identity returns HTTP 409 with a stable error code.
- Rate limit: return HTTP 429 with `Retry-After` for bounded local/provider limits.
- Errors: RFC 9457-style problem details with no secrets or raw provider payload.
- Observability: one server span and child spans for database/provider work.
- Test: authorized happy path, invalid input, replay, conflict, timeout, and ownership boundary.

#### GET /api/v1/analysis-runs/{run_id}/committee

- Purpose: Get committee summary.
- Request contract: `none`.
- Success contract: `CommitteeSummary`.
- Authentication: local personal session in pilot; all mutating routes require CSRF-safe same-site session or bearer token.
- Authorization: the caller must own the personal workspace; no cross-workspace access.
- Correlation: accept or generate `X-Correlation-ID` and return it.
- Idempotency: mutating commands require `Idempotency-Key`; repeat returns the original logical result.
- Validation: reject unknown fields and invalid timezone-aware timestamps with HTTP 422.
- Conflict: invalid state or ambiguous identity returns HTTP 409 with a stable error code.
- Rate limit: return HTTP 429 with `Retry-After` for bounded local/provider limits.
- Errors: RFC 9457-style problem details with no secrets or raw provider payload.
- Observability: one server span and child spans for database/provider work.
- Test: authorized happy path, invalid input, replay, conflict, timeout, and ownership boundary.

#### GET /api/v1/analysis-runs/{run_id}/scenarios

- Purpose: Get scenario tree.
- Request contract: `none`.
- Success contract: `ScenarioTree`.
- Authentication: local personal session in pilot; all mutating routes require CSRF-safe same-site session or bearer token.
- Authorization: the caller must own the personal workspace; no cross-workspace access.
- Correlation: accept or generate `X-Correlation-ID` and return it.
- Idempotency: mutating commands require `Idempotency-Key`; repeat returns the original logical result.
- Validation: reject unknown fields and invalid timezone-aware timestamps with HTTP 422.
- Conflict: invalid state or ambiguous identity returns HTTP 409 with a stable error code.
- Rate limit: return HTTP 429 with `Retry-After` for bounded local/provider limits.
- Errors: RFC 9457-style problem details with no secrets or raw provider payload.
- Observability: one server span and child spans for database/provider work.
- Test: authorized happy path, invalid input, replay, conflict, timeout, and ownership boundary.

#### GET /api/v1/analysis-runs/{run_id}/critics

- Purpose: Get critic findings.
- Request contract: `none`.
- Success contract: `CriticFindingList`.
- Authentication: local personal session in pilot; all mutating routes require CSRF-safe same-site session or bearer token.
- Authorization: the caller must own the personal workspace; no cross-workspace access.
- Correlation: accept or generate `X-Correlation-ID` and return it.
- Idempotency: mutating commands require `Idempotency-Key`; repeat returns the original logical result.
- Validation: reject unknown fields and invalid timezone-aware timestamps with HTTP 422.
- Conflict: invalid state or ambiguous identity returns HTTP 409 with a stable error code.
- Rate limit: return HTTP 429 with `Retry-After` for bounded local/provider limits.
- Errors: RFC 9457-style problem details with no secrets or raw provider payload.
- Observability: one server span and child spans for database/provider work.
- Test: authorized happy path, invalid input, replay, conflict, timeout, and ownership boundary.

#### GET /api/v1/analysis-runs/{run_id}/forecast

- Purpose: Get current forecast.
- Request contract: `none`.
- Success contract: `ForecastView`.
- Authentication: local personal session in pilot; all mutating routes require CSRF-safe same-site session or bearer token.
- Authorization: the caller must own the personal workspace; no cross-workspace access.
- Correlation: accept or generate `X-Correlation-ID` and return it.
- Idempotency: mutating commands require `Idempotency-Key`; repeat returns the original logical result.
- Validation: reject unknown fields and invalid timezone-aware timestamps with HTTP 422.
- Conflict: invalid state or ambiguous identity returns HTTP 409 with a stable error code.
- Rate limit: return HTTP 429 with `Retry-After` for bounded local/provider limits.
- Errors: RFC 9457-style problem details with no secrets or raw provider payload.
- Observability: one server span and child spans for database/provider work.
- Test: authorized happy path, invalid input, replay, conflict, timeout, and ownership boundary.

#### POST /api/v1/analysis-runs/{run_id}/lock

- Purpose: Request lock after approval.
- Request contract: `LockRequest`.
- Success contract: `LockAccepted`.
- Authentication: local personal session in pilot; all mutating routes require CSRF-safe same-site session or bearer token.
- Authorization: the caller must own the personal workspace; no cross-workspace access.
- Correlation: accept or generate `X-Correlation-ID` and return it.
- Idempotency: mutating commands require `Idempotency-Key`; repeat returns the original logical result.
- Validation: reject unknown fields and invalid timezone-aware timestamps with HTTP 422.
- Conflict: invalid state or ambiguous identity returns HTTP 409 with a stable error code.
- Rate limit: return HTTP 429 with `Retry-After` for bounded local/provider limits.
- Errors: RFC 9457-style problem details with no secrets or raw provider payload.
- Observability: one server span and child spans for database/provider work.
- Test: authorized happy path, invalid input, replay, conflict, timeout, and ownership boundary.

#### GET /api/v1/prediction-locks/{lock_id}

- Purpose: Get immutable lock.
- Request contract: `none`.
- Success contract: `PredictionLockView`.
- Authentication: local personal session in pilot; all mutating routes require CSRF-safe same-site session or bearer token.
- Authorization: the caller must own the personal workspace; no cross-workspace access.
- Correlation: accept or generate `X-Correlation-ID` and return it.
- Idempotency: mutating commands require `Idempotency-Key`; repeat returns the original logical result.
- Validation: reject unknown fields and invalid timezone-aware timestamps with HTTP 422.
- Conflict: invalid state or ambiguous identity returns HTTP 409 with a stable error code.
- Rate limit: return HTTP 429 with `Retry-After` for bounded local/provider limits.
- Errors: RFC 9457-style problem details with no secrets or raw provider payload.
- Observability: one server span and child spans for database/provider work.
- Test: authorized happy path, invalid input, replay, conflict, timeout, and ownership boundary.

#### GET /api/v1/prediction-locks/{lock_id}/export.md

- Purpose: Export Markdown.
- Request contract: `none`.
- Success contract: `text/markdown`.
- Authentication: local personal session in pilot; all mutating routes require CSRF-safe same-site session or bearer token.
- Authorization: the caller must own the personal workspace; no cross-workspace access.
- Correlation: accept or generate `X-Correlation-ID` and return it.
- Idempotency: mutating commands require `Idempotency-Key`; repeat returns the original logical result.
- Validation: reject unknown fields and invalid timezone-aware timestamps with HTTP 422.
- Conflict: invalid state or ambiguous identity returns HTTP 409 with a stable error code.
- Rate limit: return HTTP 429 with `Retry-After` for bounded local/provider limits.
- Errors: RFC 9457-style problem details with no secrets or raw provider payload.
- Observability: one server span and child spans for database/provider work.
- Test: authorized happy path, invalid input, replay, conflict, timeout, and ownership boundary.

#### GET /api/v1/prediction-locks/{lock_id}/export.json

- Purpose: Export JSON.
- Request contract: `none`.
- Success contract: `application/json`.
- Authentication: local personal session in pilot; all mutating routes require CSRF-safe same-site session or bearer token.
- Authorization: the caller must own the personal workspace; no cross-workspace access.
- Correlation: accept or generate `X-Correlation-ID` and return it.
- Idempotency: mutating commands require `Idempotency-Key`; repeat returns the original logical result.
- Validation: reject unknown fields and invalid timezone-aware timestamps with HTTP 422.
- Conflict: invalid state or ambiguous identity returns HTTP 409 with a stable error code.
- Rate limit: return HTTP 429 with `Retry-After` for bounded local/provider limits.
- Errors: RFC 9457-style problem details with no secrets or raw provider payload.
- Observability: one server span and child spans for database/provider work.
- Test: authorized happy path, invalid input, replay, conflict, timeout, and ownership boundary.

#### POST /api/v1/fixtures/{fixture_id}/odds-watch

- Purpose: Start allowed odds watch.
- Request contract: `OddsWatchRequest`.
- Success contract: `OddsWatchAccepted`.
- Authentication: local personal session in pilot; all mutating routes require CSRF-safe same-site session or bearer token.
- Authorization: the caller must own the personal workspace; no cross-workspace access.
- Correlation: accept or generate `X-Correlation-ID` and return it.
- Idempotency: mutating commands require `Idempotency-Key`; repeat returns the original logical result.
- Validation: reject unknown fields and invalid timezone-aware timestamps with HTTP 422.
- Conflict: invalid state or ambiguous identity returns HTTP 409 with a stable error code.
- Rate limit: return HTTP 429 with `Retry-After` for bounded local/provider limits.
- Errors: RFC 9457-style problem details with no secrets or raw provider payload.
- Observability: one server span and child spans for database/provider work.
- Test: authorized happy path, invalid input, replay, conflict, timeout, and ownership boundary.

#### DELETE /api/v1/fixtures/{fixture_id}/odds-watch

- Purpose: Stop odds watch.
- Request contract: `none`.
- Success contract: `OperationAccepted`.
- Authentication: local personal session in pilot; all mutating routes require CSRF-safe same-site session or bearer token.
- Authorization: the caller must own the personal workspace; no cross-workspace access.
- Correlation: accept or generate `X-Correlation-ID` and return it.
- Idempotency: mutating commands require `Idempotency-Key`; repeat returns the original logical result.
- Validation: reject unknown fields and invalid timezone-aware timestamps with HTTP 422.
- Conflict: invalid state or ambiguous identity returns HTTP 409 with a stable error code.
- Rate limit: return HTTP 429 with `Retry-After` for bounded local/provider limits.
- Errors: RFC 9457-style problem details with no secrets or raw provider payload.
- Observability: one server span and child spans for database/provider work.
- Test: authorized happy path, invalid input, replay, conflict, timeout, and ownership boundary.

#### GET /api/v1/fixtures/{fixture_id}/odds

- Purpose: Get normalized odds series.
- Request contract: `OddsSeriesQuery`.
- Success contract: `OddsSeries`.
- Authentication: local personal session in pilot; all mutating routes require CSRF-safe same-site session or bearer token.
- Authorization: the caller must own the personal workspace; no cross-workspace access.
- Correlation: accept or generate `X-Correlation-ID` and return it.
- Idempotency: mutating commands require `Idempotency-Key`; repeat returns the original logical result.
- Validation: reject unknown fields and invalid timezone-aware timestamps with HTTP 422.
- Conflict: invalid state or ambiguous identity returns HTTP 409 with a stable error code.
- Rate limit: return HTTP 429 with `Retry-After` for bounded local/provider limits.
- Errors: RFC 9457-style problem details with no secrets or raw provider payload.
- Observability: one server span and child spans for database/provider work.
- Test: authorized happy path, invalid input, replay, conflict, timeout, and ownership boundary.

#### POST /api/v1/prediction-locks/{lock_id}/post-match

- Purpose: Start post-match ingestion.
- Request contract: `PostMatchRequest`.
- Success contract: `OperationAccepted`.
- Authentication: local personal session in pilot; all mutating routes require CSRF-safe same-site session or bearer token.
- Authorization: the caller must own the personal workspace; no cross-workspace access.
- Correlation: accept or generate `X-Correlation-ID` and return it.
- Idempotency: mutating commands require `Idempotency-Key`; repeat returns the original logical result.
- Validation: reject unknown fields and invalid timezone-aware timestamps with HTTP 422.
- Conflict: invalid state or ambiguous identity returns HTTP 409 with a stable error code.
- Rate limit: return HTTP 429 with `Retry-After` for bounded local/provider limits.
- Errors: RFC 9457-style problem details with no secrets or raw provider payload.
- Observability: one server span and child spans for database/provider work.
- Test: authorized happy path, invalid input, replay, conflict, timeout, and ownership boundary.

#### GET /api/v1/prediction-locks/{lock_id}/autopsy

- Purpose: Get autopsy.
- Request contract: `none`.
- Success contract: `AutopsyView`.
- Authentication: local personal session in pilot; all mutating routes require CSRF-safe same-site session or bearer token.
- Authorization: the caller must own the personal workspace; no cross-workspace access.
- Correlation: accept or generate `X-Correlation-ID` and return it.
- Idempotency: mutating commands require `Idempotency-Key`; repeat returns the original logical result.
- Validation: reject unknown fields and invalid timezone-aware timestamps with HTTP 422.
- Conflict: invalid state or ambiguous identity returns HTTP 409 with a stable error code.
- Rate limit: return HTTP 429 with `Retry-After` for bounded local/provider limits.
- Errors: RFC 9457-style problem details with no secrets or raw provider payload.
- Observability: one server span and child spans for database/provider work.
- Test: authorized happy path, invalid input, replay, conflict, timeout, and ownership boundary.

#### GET /api/v1/cases

- Purpose: List case memory.
- Request contract: `CaseQuery`.
- Success contract: `CasePage`.
- Authentication: local personal session in pilot; all mutating routes require CSRF-safe same-site session or bearer token.
- Authorization: the caller must own the personal workspace; no cross-workspace access.
- Correlation: accept or generate `X-Correlation-ID` and return it.
- Idempotency: mutating commands require `Idempotency-Key`; repeat returns the original logical result.
- Validation: reject unknown fields and invalid timezone-aware timestamps with HTTP 422.
- Conflict: invalid state or ambiguous identity returns HTTP 409 with a stable error code.
- Rate limit: return HTTP 429 with `Retry-After` for bounded local/provider limits.
- Errors: RFC 9457-style problem details with no secrets or raw provider payload.
- Observability: one server span and child spans for database/provider work.
- Test: authorized happy path, invalid input, replay, conflict, timeout, and ownership boundary.

#### GET /api/v1/cases/{case_id}

- Purpose: Get case.
- Request contract: `none`.
- Success contract: `CaseDetail`.
- Authentication: local personal session in pilot; all mutating routes require CSRF-safe same-site session or bearer token.
- Authorization: the caller must own the personal workspace; no cross-workspace access.
- Correlation: accept or generate `X-Correlation-ID` and return it.
- Idempotency: mutating commands require `Idempotency-Key`; repeat returns the original logical result.
- Validation: reject unknown fields and invalid timezone-aware timestamps with HTTP 422.
- Conflict: invalid state or ambiguous identity returns HTTP 409 with a stable error code.
- Rate limit: return HTTP 429 with `Retry-After` for bounded local/provider limits.
- Errors: RFC 9457-style problem details with no secrets or raw provider payload.
- Observability: one server span and child spans for database/provider work.
- Test: authorized happy path, invalid input, replay, conflict, timeout, and ownership boundary.

#### GET /api/v1/lessons

- Purpose: List validated lessons.
- Request contract: `LessonQuery`.
- Success contract: `LessonPage`.
- Authentication: local personal session in pilot; all mutating routes require CSRF-safe same-site session or bearer token.
- Authorization: the caller must own the personal workspace; no cross-workspace access.
- Correlation: accept or generate `X-Correlation-ID` and return it.
- Idempotency: mutating commands require `Idempotency-Key`; repeat returns the original logical result.
- Validation: reject unknown fields and invalid timezone-aware timestamps with HTTP 422.
- Conflict: invalid state or ambiguous identity returns HTTP 409 with a stable error code.
- Rate limit: return HTTP 429 with `Retry-After` for bounded local/provider limits.
- Errors: RFC 9457-style problem details with no secrets or raw provider payload.
- Observability: one server span and child spans for database/provider work.
- Test: authorized happy path, invalid input, replay, conflict, timeout, and ownership boundary.

#### PATCH /api/v1/lessons/{lesson_id}

- Purpose: Administrative lesson status change.
- Request contract: `LessonPatch`.
- Success contract: `LessonView`.
- Authentication: local personal session in pilot; all mutating routes require CSRF-safe same-site session or bearer token.
- Authorization: the caller must own the personal workspace; no cross-workspace access.
- Correlation: accept or generate `X-Correlation-ID` and return it.
- Idempotency: mutating commands require `Idempotency-Key`; repeat returns the original logical result.
- Validation: reject unknown fields and invalid timezone-aware timestamps with HTTP 422.
- Conflict: invalid state or ambiguous identity returns HTTP 409 with a stable error code.
- Rate limit: return HTTP 429 with `Retry-After` for bounded local/provider limits.
- Errors: RFC 9457-style problem details with no secrets or raw provider payload.
- Observability: one server span and child spans for database/provider work.
- Test: authorized happy path, invalid input, replay, conflict, timeout, and ownership boundary.

#### GET /api/v1/budget

- Purpose: Get budget ledger.
- Request contract: `none`.
- Success contract: `BudgetSummary`.
- Authentication: local personal session in pilot; all mutating routes require CSRF-safe same-site session or bearer token.
- Authorization: the caller must own the personal workspace; no cross-workspace access.
- Correlation: accept or generate `X-Correlation-ID` and return it.
- Idempotency: mutating commands require `Idempotency-Key`; repeat returns the original logical result.
- Validation: reject unknown fields and invalid timezone-aware timestamps with HTTP 422.
- Conflict: invalid state or ambiguous identity returns HTTP 409 with a stable error code.
- Rate limit: return HTTP 429 with `Retry-After` for bounded local/provider limits.
- Errors: RFC 9457-style problem details with no secrets or raw provider payload.
- Observability: one server span and child spans for database/provider work.
- Test: authorized happy path, invalid input, replay, conflict, timeout, and ownership boundary.

#### GET /api/v1/providers

- Purpose: List safe provider status.
- Request contract: `none`.
- Success contract: `ProviderStatusList`.
- Authentication: local personal session in pilot; all mutating routes require CSRF-safe same-site session or bearer token.
- Authorization: the caller must own the personal workspace; no cross-workspace access.
- Correlation: accept or generate `X-Correlation-ID` and return it.
- Idempotency: mutating commands require `Idempotency-Key`; repeat returns the original logical result.
- Validation: reject unknown fields and invalid timezone-aware timestamps with HTTP 422.
- Conflict: invalid state or ambiguous identity returns HTTP 409 with a stable error code.
- Rate limit: return HTTP 429 with `Retry-After` for bounded local/provider limits.
- Errors: RFC 9457-style problem details with no secrets or raw provider payload.
- Observability: one server span and child spans for database/provider work.
- Test: authorized happy path, invalid input, replay, conflict, timeout, and ownership boundary.

#### POST /api/v1/providers/{provider_id}/probe

- Purpose: Run capability probe.
- Request contract: `ProbeRequest`.
- Success contract: `ProbeResult`.
- Authentication: local personal session in pilot; all mutating routes require CSRF-safe same-site session or bearer token.
- Authorization: the caller must own the personal workspace; no cross-workspace access.
- Correlation: accept or generate `X-Correlation-ID` and return it.
- Idempotency: mutating commands require `Idempotency-Key`; repeat returns the original logical result.
- Validation: reject unknown fields and invalid timezone-aware timestamps with HTTP 422.
- Conflict: invalid state or ambiguous identity returns HTTP 409 with a stable error code.
- Rate limit: return HTTP 429 with `Retry-After` for bounded local/provider limits.
- Errors: RFC 9457-style problem details with no secrets or raw provider payload.
- Observability: one server span and child spans for database/provider work.
- Test: authorized happy path, invalid input, replay, conflict, timeout, and ownership boundary.

#### GET /api/v1/models

- Purpose: List model registry status.
- Request contract: `none`.
- Success contract: `ModelRegistryView`.
- Authentication: local personal session in pilot; all mutating routes require CSRF-safe same-site session or bearer token.
- Authorization: the caller must own the personal workspace; no cross-workspace access.
- Correlation: accept or generate `X-Correlation-ID` and return it.
- Idempotency: mutating commands require `Idempotency-Key`; repeat returns the original logical result.
- Validation: reject unknown fields and invalid timezone-aware timestamps with HTTP 422.
- Conflict: invalid state or ambiguous identity returns HTTP 409 with a stable error code.
- Rate limit: return HTTP 429 with `Retry-After` for bounded local/provider limits.
- Errors: RFC 9457-style problem details with no secrets or raw provider payload.
- Observability: one server span and child spans for database/provider work.
- Test: authorized happy path, invalid input, replay, conflict, timeout, and ownership boundary.

#### POST /api/v1/models/verify

- Purpose: Record verified price/capability evidence.
- Request contract: `ModelVerificationRequest`.
- Success contract: `ModelVerificationResult`.
- Authentication: local personal session in pilot; all mutating routes require CSRF-safe same-site session or bearer token.
- Authorization: the caller must own the personal workspace; no cross-workspace access.
- Correlation: accept or generate `X-Correlation-ID` and return it.
- Idempotency: mutating commands require `Idempotency-Key`; repeat returns the original logical result.
- Validation: reject unknown fields and invalid timezone-aware timestamps with HTTP 422.
- Conflict: invalid state or ambiguous identity returns HTTP 409 with a stable error code.
- Rate limit: return HTTP 429 with `Retry-After` for bounded local/provider limits.
- Errors: RFC 9457-style problem details with no secrets or raw provider payload.
- Observability: one server span and child spans for database/provider work.
- Test: authorized happy path, invalid input, replay, conflict, timeout, and ownership boundary.

#### GET /api/v1/config

- Purpose: Get non-secret effective config.
- Request contract: `none`.
- Success contract: `PublicConfigView`.
- Authentication: local personal session in pilot; all mutating routes require CSRF-safe same-site session or bearer token.
- Authorization: the caller must own the personal workspace; no cross-workspace access.
- Correlation: accept or generate `X-Correlation-ID` and return it.
- Idempotency: mutating commands require `Idempotency-Key`; repeat returns the original logical result.
- Validation: reject unknown fields and invalid timezone-aware timestamps with HTTP 422.
- Conflict: invalid state or ambiguous identity returns HTTP 409 with a stable error code.
- Rate limit: return HTTP 429 with `Retry-After` for bounded local/provider limits.
- Errors: RFC 9457-style problem details with no secrets or raw provider payload.
- Observability: one server span and child spans for database/provider work.
- Test: authorized happy path, invalid input, replay, conflict, timeout, and ownership boundary.

#### GET /api/v1/health/live

- Purpose: Liveness.
- Request contract: `none`.
- Success contract: `HealthStatus`.
- Authentication: local personal session in pilot; all mutating routes require CSRF-safe same-site session or bearer token.
- Authorization: the caller must own the personal workspace; no cross-workspace access.
- Correlation: accept or generate `X-Correlation-ID` and return it.
- Idempotency: mutating commands require `Idempotency-Key`; repeat returns the original logical result.
- Validation: reject unknown fields and invalid timezone-aware timestamps with HTTP 422.
- Conflict: invalid state or ambiguous identity returns HTTP 409 with a stable error code.
- Rate limit: return HTTP 429 with `Retry-After` for bounded local/provider limits.
- Errors: RFC 9457-style problem details with no secrets or raw provider payload.
- Observability: one server span and child spans for database/provider work.
- Test: authorized happy path, invalid input, replay, conflict, timeout, and ownership boundary.

#### GET /api/v1/health/ready

- Purpose: Readiness.
- Request contract: `none`.
- Success contract: `ReadinessStatus`.
- Authentication: local personal session in pilot; all mutating routes require CSRF-safe same-site session or bearer token.
- Authorization: the caller must own the personal workspace; no cross-workspace access.
- Correlation: accept or generate `X-Correlation-ID` and return it.
- Idempotency: mutating commands require `Idempotency-Key`; repeat returns the original logical result.
- Validation: reject unknown fields and invalid timezone-aware timestamps with HTTP 422.
- Conflict: invalid state or ambiguous identity returns HTTP 409 with a stable error code.
- Rate limit: return HTTP 429 with `Retry-After` for bounded local/provider limits.
- Errors: RFC 9457-style problem details with no secrets or raw provider payload.
- Observability: one server span and child spans for database/provider work.
- Test: authorized happy path, invalid input, replay, conflict, timeout, and ownership boundary.

#### GET /api/v1/version

- Purpose: Build and migration version.
- Request contract: `none`.
- Success contract: `VersionInfo`.
- Authentication: local personal session in pilot; all mutating routes require CSRF-safe same-site session or bearer token.
- Authorization: the caller must own the personal workspace; no cross-workspace access.
- Correlation: accept or generate `X-Correlation-ID` and return it.
- Idempotency: mutating commands require `Idempotency-Key`; repeat returns the original logical result.
- Validation: reject unknown fields and invalid timezone-aware timestamps with HTTP 422.
- Conflict: invalid state or ambiguous identity returns HTTP 409 with a stable error code.
- Rate limit: return HTTP 429 with `Retry-After` for bounded local/provider limits.
- Errors: RFC 9457-style problem details with no secrets or raw provider payload.
- Observability: one server span and child spans for database/provider work.
- Test: authorized happy path, invalid input, replay, conflict, timeout, and ownership boundary.

### 16.2 SSE event contract

```text
id: 018f0000-0000-7000-8000-000000000099
event: stage.progress
data: {"schema_version":"progress.v1","run_id":"...","stage_id":"S05","status":"running","progress":0.42,"message_key":"statistics.features","occurred_at":"2026-08-22T12:00:00+03:00"}
```

- Events are persisted before publication through the transactional outbox.
- Clients reconnect with `Last-Event-ID`.
- Progress is monotonic within one stage attempt.
- User-facing text comes from bounded message keys, not raw logs.
- No model prompt, secret, chain-of-thought, or raw copyrighted snapshot appears in events.

## 17. Frontend Information Architecture and UX

### 17.1 Page catalog

#### Dashboard — /

- Primary purpose: Three-day scan control, date chips, recent runs, budget.
- Layout MUST remain usable at 360 px width and avoid information-dense decorative chrome.
- Primary action MUST be visually unambiguous and keyboard reachable.
- Loading uses content-shaped skeletons; no full-page spinner after initial navigation.
- Empty state explains what is missing and offers one relevant next action.
- Error state displays stable reason code and recovery action without raw stack trace.
- Stale data displays the observation time and a stale badge.
- Dates show Europe/Istanbul and include full date in accessible text.
- Desktop density target: key match row height 56–68 px.
- Focus order follows visual order; dialogs trap and restore focus.
- Playwright test covers loading, success, empty, degraded, and error states.

#### Scan Results — /scan/[scanId]

- Primary purpose: Ranked candidates, filters, reasons, coverage.
- Layout MUST remain usable at 360 px width and avoid information-dense decorative chrome.
- Primary action MUST be visually unambiguous and keyboard reachable.
- Loading uses content-shaped skeletons; no full-page spinner after initial navigation.
- Empty state explains what is missing and offers one relevant next action.
- Error state displays stable reason code and recovery action without raw stack trace.
- Stale data displays the observation time and a stale badge.
- Dates show Europe/Istanbul and include full date in accessible text.
- Desktop density target: key match row height 56–68 px.
- Focus order follows visual order; dialogs trap and restore focus.
- Playwright test covers loading, success, empty, degraded, and error states.

#### Match Search — /search

- Primary purpose: Manual search, grouped results, ambiguity-safe selection.
- Layout MUST remain usable at 360 px width and avoid information-dense decorative chrome.
- Primary action MUST be visually unambiguous and keyboard reachable.
- Loading uses content-shaped skeletons; no full-page spinner after initial navigation.
- Empty state explains what is missing and offers one relevant next action.
- Error state displays stable reason code and recovery action without raw stack trace.
- Stale data displays the observation time and a stale badge.
- Dates show Europe/Istanbul and include full date in accessible text.
- Desktop density target: key match row height 56–68 px.
- Focus order follows visual order; dialogs trap and restore focus.
- Playwright test covers loading, success, empty, degraded, and error states.

#### Fixture Preflight — /fixtures/[fixtureId]

- Primary purpose: Match identity, coverage, cost/time estimate, start action.
- Layout MUST remain usable at 360 px width and avoid information-dense decorative chrome.
- Primary action MUST be visually unambiguous and keyboard reachable.
- Loading uses content-shaped skeletons; no full-page spinner after initial navigation.
- Empty state explains what is missing and offers one relevant next action.
- Error state displays stable reason code and recovery action without raw stack trace.
- Stale data displays the observation time and a stale badge.
- Dates show Europe/Istanbul and include full date in accessible text.
- Desktop density target: key match row height 56–68 px.
- Focus order follows visual order; dialogs trap and restore focus.
- Playwright test covers loading, success, empty, degraded, and error states.

#### Run Overview — /runs/[runId]

- Primary purpose: DAG progress, status, spend, elapsed time, cancel.
- Layout MUST remain usable at 360 px width and avoid information-dense decorative chrome.
- Primary action MUST be visually unambiguous and keyboard reachable.
- Loading uses content-shaped skeletons; no full-page spinner after initial navigation.
- Empty state explains what is missing and offers one relevant next action.
- Error state displays stable reason code and recovery action without raw stack trace.
- Stale data displays the observation time and a stale badge.
- Dates show Europe/Istanbul and include full date in accessible text.
- Desktop density target: key match row height 56–68 px.
- Focus order follows visual order; dialogs trap and restore focus.
- Playwright test covers loading, success, empty, degraded, and error states.

#### Evidence Ledger — /runs/[runId]/evidence

- Primary purpose: Sources, claims, freshness, citations.
- Layout MUST remain usable at 360 px width and avoid information-dense decorative chrome.
- Primary action MUST be visually unambiguous and keyboard reachable.
- Loading uses content-shaped skeletons; no full-page spinner after initial navigation.
- Empty state explains what is missing and offers one relevant next action.
- Error state displays stable reason code and recovery action without raw stack trace.
- Stale data displays the observation time and a stale badge.
- Dates show Europe/Istanbul and include full date in accessible text.
- Desktop density target: key match row height 56–68 px.
- Focus order follows visual order; dialogs trap and restore focus.
- Playwright test covers loading, success, empty, degraded, and error states.

#### Specialist Reports — /runs/[runId]/specialists

- Primary purpose: Stats, squad, tactics, form, fatigue, keeper, set pieces, environment.
- Layout MUST remain usable at 360 px width and avoid information-dense decorative chrome.
- Primary action MUST be visually unambiguous and keyboard reachable.
- Loading uses content-shaped skeletons; no full-page spinner after initial navigation.
- Empty state explains what is missing and offers one relevant next action.
- Error state displays stable reason code and recovery action without raw stack trace.
- Stale data displays the observation time and a stale badge.
- Dates show Europe/Istanbul and include full date in accessible text.
- Desktop density target: key match row height 56–68 px.
- Focus order follows visual order; dialogs trap and restore focus.
- Playwright test covers loading, success, empty, degraded, and error states.

#### Quant Models — /runs/[runId]/quant

- Primary purpose: Model distributions, diagnostics, calibration.
- Layout MUST remain usable at 360 px width and avoid information-dense decorative chrome.
- Primary action MUST be visually unambiguous and keyboard reachable.
- Loading uses content-shaped skeletons; no full-page spinner after initial navigation.
- Empty state explains what is missing and offers one relevant next action.
- Error state displays stable reason code and recovery action without raw stack trace.
- Stale data displays the observation time and a stale badge.
- Dates show Europe/Istanbul and include full date in accessible text.
- Desktop density target: key match row height 56–68 px.
- Focus order follows visual order; dialogs trap and restore focus.
- Playwright test covers loading, success, empty, degraded, and error states.

#### Market Intelligence — /runs/[runId]/market

- Primary purpose: Allowed odds snapshots, fair probability, movement.
- Layout MUST remain usable at 360 px width and avoid information-dense decorative chrome.
- Primary action MUST be visually unambiguous and keyboard reachable.
- Loading uses content-shaped skeletons; no full-page spinner after initial navigation.
- Empty state explains what is missing and offers one relevant next action.
- Error state displays stable reason code and recovery action without raw stack trace.
- Stale data displays the observation time and a stale badge.
- Dates show Europe/Istanbul and include full date in accessible text.
- Desktop density target: key match row height 56–68 px.
- Focus order follows visual order; dialogs trap and restore focus.
- Playwright test covers loading, success, empty, degraded, and error states.

#### Sonnet Committee — /runs/[runId]/committee

- Primary purpose: Evidence, tactical, player/squad, and quant/market syntheses with prediction prohibition.
- Layout MUST remain usable at 360 px width and avoid information-dense decorative chrome.
- Primary action MUST be visually unambiguous and keyboard reachable.
- Loading uses content-shaped skeletons; no full-page spinner after initial navigation.
- Empty state explains what is missing and offers one relevant next action.
- Error state displays stable reason code and recovery action without raw stack trace.
- Stale data displays the observation time and a stale badge.
- Dates show Europe/Istanbul and include full date in accessible text.
- Desktop density target: key match row height 56–68 px.
- Focus order follows visual order; dialogs trap and restore focus.
- Playwright test covers loading, success, empty, degraded, and error states.

#### Scenarios — /runs/[runId]/scenarios

- Primary purpose: Steelman tree and triggers.
- Layout MUST remain usable at 360 px width and avoid information-dense decorative chrome.
- Primary action MUST be visually unambiguous and keyboard reachable.
- Loading uses content-shaped skeletons; no full-page spinner after initial navigation.
- Empty state explains what is missing and offers one relevant next action.
- Error state displays stable reason code and recovery action without raw stack trace.
- Stale data displays the observation time and a stale badge.
- Dates show Europe/Istanbul and include full date in accessible text.
- Desktop density target: key match row height 56–68 px.
- Focus order follows visual order; dialogs trap and restore focus.
- Playwright test covers loading, success, empty, degraded, and error states.

#### Final Forecast — /runs/[runId]/final

- Primary purpose: Forecast, critic status, lock state, export.
- Layout MUST remain usable at 360 px width and avoid information-dense decorative chrome.
- Primary action MUST be visually unambiguous and keyboard reachable.
- Loading uses content-shaped skeletons; no full-page spinner after initial navigation.
- Empty state explains what is missing and offers one relevant next action.
- Error state displays stable reason code and recovery action without raw stack trace.
- Stale data displays the observation time and a stale badge.
- Dates show Europe/Istanbul and include full date in accessible text.
- Desktop density target: key match row height 56–68 px.
- Focus order follows visual order; dialogs trap and restore focus.
- Playwright test covers loading, success, empty, degraded, and error states.

#### Locked Prediction — /locks/[lockId]

- Primary purpose: Immutable manifest, hashes, frozen forecast.
- Layout MUST remain usable at 360 px width and avoid information-dense decorative chrome.
- Primary action MUST be visually unambiguous and keyboard reachable.
- Loading uses content-shaped skeletons; no full-page spinner after initial navigation.
- Empty state explains what is missing and offers one relevant next action.
- Error state displays stable reason code and recovery action without raw stack trace.
- Stale data displays the observation time and a stale badge.
- Dates show Europe/Istanbul and include full date in accessible text.
- Desktop density target: key match row height 56–68 px.
- Focus order follows visual order; dialogs trap and restore focus.
- Playwright test covers loading, success, empty, degraded, and error states.

#### Post-Match Autopsy — /locks/[lockId]/autopsy

- Primary purpose: Result, process evaluation, variance, lessons.
- Layout MUST remain usable at 360 px width and avoid information-dense decorative chrome.
- Primary action MUST be visually unambiguous and keyboard reachable.
- Loading uses content-shaped skeletons; no full-page spinner after initial navigation.
- Empty state explains what is missing and offers one relevant next action.
- Error state displays stable reason code and recovery action without raw stack trace.
- Stale data displays the observation time and a stale badge.
- Dates show Europe/Istanbul and include full date in accessible text.
- Desktop density target: key match row height 56–68 px.
- Focus order follows visual order; dialogs trap and restore focus.
- Playwright test covers loading, success, empty, degraded, and error states.

#### Case Memory — /cases

- Primary purpose: Historical cases and validated lessons.
- Layout MUST remain usable at 360 px width and avoid information-dense decorative chrome.
- Primary action MUST be visually unambiguous and keyboard reachable.
- Loading uses content-shaped skeletons; no full-page spinner after initial navigation.
- Empty state explains what is missing and offers one relevant next action.
- Error state displays stable reason code and recovery action without raw stack trace.
- Stale data displays the observation time and a stale badge.
- Dates show Europe/Istanbul and include full date in accessible text.
- Desktop density target: key match row height 56–68 px.
- Focus order follows visual order; dialogs trap and restore focus.
- Playwright test covers loading, success, empty, degraded, and error states.

#### Providers — /settings/providers

- Primary purpose: Capability, quota, legal status, safe probes.
- Layout MUST remain usable at 360 px width and avoid information-dense decorative chrome.
- Primary action MUST be visually unambiguous and keyboard reachable.
- Loading uses content-shaped skeletons; no full-page spinner after initial navigation.
- Empty state explains what is missing and offers one relevant next action.
- Error state displays stable reason code and recovery action without raw stack trace.
- Stale data displays the observation time and a stale badge.
- Dates show Europe/Istanbul and include full date in accessible text.
- Desktop density target: key match row height 56–68 px.
- Focus order follows visual order; dialogs trap and restore focus.
- Playwright test covers loading, success, empty, degraded, and error states.

#### Models — /settings/models

- Primary purpose: Routes, verification expiry, prices, eval status.
- Layout MUST remain usable at 360 px width and avoid information-dense decorative chrome.
- Primary action MUST be visually unambiguous and keyboard reachable.
- Loading uses content-shaped skeletons; no full-page spinner after initial navigation.
- Empty state explains what is missing and offers one relevant next action.
- Error state displays stable reason code and recovery action without raw stack trace.
- Stale data displays the observation time and a stale badge.
- Dates show Europe/Istanbul and include full date in accessible text.
- Desktop density target: key match row height 56–68 px.
- Focus order follows visual order; dialogs trap and restore focus.
- Playwright test covers loading, success, empty, degraded, and error states.

#### Budget — /settings/budget

- Primary purpose: Monthly cap, spend ledger, reservations.
- Layout MUST remain usable at 360 px width and avoid information-dense decorative chrome.
- Primary action MUST be visually unambiguous and keyboard reachable.
- Loading uses content-shaped skeletons; no full-page spinner after initial navigation.
- Empty state explains what is missing and offers one relevant next action.
- Error state displays stable reason code and recovery action without raw stack trace.
- Stale data displays the observation time and a stale badge.
- Dates show Europe/Istanbul and include full date in accessible text.
- Desktop density target: key match row height 56–68 px.
- Focus order follows visual order; dialogs trap and restore focus.
- Playwright test covers loading, success, empty, degraded, and error states.

### 17.2 Core component catalog

- `AppShell`: typed props, Storybook state fixtures, keyboard test, compact mobile state, and no direct API calls.
- `TopCommandBar`: typed props, Storybook state fixtures, keyboard test, compact mobile state, and no direct API calls.
- `ThreeDayDateStrip`: typed props, Storybook state fixtures, keyboard test, compact mobile state, and no direct API calls.
- `ScanButton`: typed props, Storybook state fixtures, keyboard test, compact mobile state, and no direct API calls.
- `ScanStatusCard`: typed props, Storybook state fixtures, keyboard test, compact mobile state, and no direct API calls.
- `FixtureSearchCombobox`: typed props, Storybook state fixtures, keyboard test, compact mobile state, and no direct API calls.
- `FixtureResultRow`: typed props, Storybook state fixtures, keyboard test, compact mobile state, and no direct API calls.
- `CompetitionBadge`: typed props, Storybook state fixtures, keyboard test, compact mobile state, and no direct API calls.
- `CoverageMeter`: typed props, Storybook state fixtures, keyboard test, compact mobile state, and no direct API calls.
- `WorthwhileScore`: typed props, Storybook state fixtures, keyboard test, compact mobile state, and no direct API calls.
- `RankReasonChips`: typed props, Storybook state fixtures, keyboard test, compact mobile state, and no direct API calls.
- `AnalysisPreflightSheet`: typed props, Storybook state fixtures, keyboard test, compact mobile state, and no direct API calls.
- `RunHeader`: typed props, Storybook state fixtures, keyboard test, compact mobile state, and no direct API calls.
- `StageDAG`: typed props, Storybook state fixtures, keyboard test, compact mobile state, and no direct API calls.
- `StageNode`: typed props, Storybook state fixtures, keyboard test, compact mobile state, and no direct API calls.
- `StageDetailDrawer`: typed props, Storybook state fixtures, keyboard test, compact mobile state, and no direct API calls.
- `ElapsedTimer`: typed props, Storybook state fixtures, keyboard test, compact mobile state, and no direct API calls.
- `BudgetMeter`: typed props, Storybook state fixtures, keyboard test, compact mobile state, and no direct API calls.
- `CancelRunDialog`: typed props, Storybook state fixtures, keyboard test, compact mobile state, and no direct API calls.
- `EvidenceTable`: typed props, Storybook state fixtures, keyboard test, compact mobile state, and no direct API calls.
- `SourceBadge`: typed props, Storybook state fixtures, keyboard test, compact mobile state, and no direct API calls.
- `FreshnessBadge`: typed props, Storybook state fixtures, keyboard test, compact mobile state, and no direct API calls.
- `ClaimCard`: typed props, Storybook state fixtures, keyboard test, compact mobile state, and no direct API calls.
- `ContradictionGroup`: typed props, Storybook state fixtures, keyboard test, compact mobile state, and no direct API calls.
- `SpecialistReportCard`: typed props, Storybook state fixtures, keyboard test, compact mobile state, and no direct API calls.
- `ProbabilityBar`: typed props, Storybook state fixtures, keyboard test, compact mobile state, and no direct API calls.
- `UncertaintyInterval`: typed props, Storybook state fixtures, keyboard test, compact mobile state, and no direct API calls.
- `CalibrationBadge`: typed props, Storybook state fixtures, keyboard test, compact mobile state, and no direct API calls.
- `OddsMovementChart`: typed props, Storybook state fixtures, keyboard test, compact mobile state, and no direct API calls.
- `FairProbabilityTable`: typed props, Storybook state fixtures, keyboard test, compact mobile state, and no direct API calls.
- `SonnetSynthesisCard`: typed props, Storybook state fixtures, keyboard test, compact mobile state, and no direct API calls.
- `DissentPanel`: typed props, Storybook state fixtures, keyboard test, compact mobile state, and no direct API calls.
- `ScenarioTree`: typed props, Storybook state fixtures, keyboard test, compact mobile state, and no direct API calls.
- `CriticFindingList`: typed props, Storybook state fixtures, keyboard test, compact mobile state, and no direct API calls.
- `ForecastCard`: typed props, Storybook state fixtures, keyboard test, compact mobile state, and no direct API calls.
- `LockStatusBanner`: typed props, Storybook state fixtures, keyboard test, compact mobile state, and no direct API calls.
- `IntegrityManifest`: typed props, Storybook state fixtures, keyboard test, compact mobile state, and no direct API calls.
- `AutopsyTimeline`: typed props, Storybook state fixtures, keyboard test, compact mobile state, and no direct API calls.
- `VarianceWaterfall`: typed props, Storybook state fixtures, keyboard test, compact mobile state, and no direct API calls.
- `LessonCard`: typed props, Storybook state fixtures, keyboard test, compact mobile state, and no direct API calls.
- `ProviderStatusRow`: typed props, Storybook state fixtures, keyboard test, compact mobile state, and no direct API calls.
- `ModelRouteRow`: typed props, Storybook state fixtures, keyboard test, compact mobile state, and no direct API calls.
- `EmptyState`: typed props, Storybook state fixtures, keyboard test, compact mobile state, and no direct API calls.
- `DegradedBanner`: typed props, Storybook state fixtures, keyboard test, compact mobile state, and no direct API calls.
- `ProblemDetailsPanel`: typed props, Storybook state fixtures, keyboard test, compact mobile state, and no direct API calls.

### 17.3 Visual design direction

- The product wordmark and browser title use exactly `MİRON BABA AI`; `Sports Intelligence` is a descriptive subtitle, not the product name.
- Tone: analytical, calm, premium, compact, and non-casino.
- Avoid flashing odds, neon betting colors, countdown pressure, confetti, and urgency manipulation.
- Use a neutral graphite surface, restrained blue accent, amber for uncertainty, red only for material defects.
- Use tabular numerals for times, probabilities, prices, and costs.
- Use typography hierarchy, spacing, and alignment before borders and shadows.
- Charts require text summaries and accessible data tables.
- Motion is subtle, respects reduced-motion settings, and never hides state changes.

### 17.3.1 Canonical compact dashboard copy

```text
MİRON BABA AI
Sports Intelligence & Prediction Engine

[ Maç ara... ]                         [ 3 GÜNÜ TARA ]

BUGÜN              YARIN              +2 GÜN

Liverpool                          Arsenal
20:00 · Premier League
Analysis Worthiness Score: 94/100
Veri: Mükemmel · Piyasa: Güçlü · Tahmini maliyet: $0.21
[ DERİN ANALİZİ BAŞLAT ]
```

The default user-facing locale is Turkish, while canonical technical keys and contracts remain English.
The scan and deep-analysis actions may show concise English secondary labels, but Turkish primary labels are the default.

### 17.4 Progress UX semantics

- Show stage names users can understand, with technical IDs in details.
- Display elapsed time as exact and remaining time as a range.
- Never fake linear progress while waiting on an external model/provider.
- Use indeterminate substate only when total work is unknowable.
- Show retry count and degraded continuation when meaningful.
- Cancellation becomes `Cancel requested` until workflow acknowledgement.
- Completed stage reports remain readable during later failures.

## 18. Deterministic Quantitative Models

### 18.1 Football baseline suite

#### Q01 — Elo rating

- Purpose: Team strength with home advantage and competition-aware K factors.
- Training split MUST be chronological and competition-aware.
- Features MUST have explicit availability timestamps.
- Missing values MUST use a documented policy and missingness indicators where appropriate.
- Hyperparameters MUST be selected without touching the final holdout.
- Output MUST include three-way probabilities and diagnostics.
- Model card MUST state data coverage, exclusions, limitations, and calibration domain.
- Promotion requires improvement over simple base rates on multiple proper scoring rules.
- A model that improves accuracy but worsens calibration cannot be promoted without justification.

#### Q02 — Poisson goals

- Purpose: Home and away scoring intensities with shrinkage.
- Training split MUST be chronological and competition-aware.
- Features MUST have explicit availability timestamps.
- Missing values MUST use a documented policy and missingness indicators where appropriate.
- Hyperparameters MUST be selected without touching the final holdout.
- Output MUST include three-way probabilities and diagnostics.
- Model card MUST state data coverage, exclusions, limitations, and calibration domain.
- Promotion requires improvement over simple base rates on multiple proper scoring rules.
- A model that improves accuracy but worsens calibration cannot be promoted without justification.

#### Q03 — Dixon-Coles adjustment

- Purpose: Low-score dependence correction.
- Training split MUST be chronological and competition-aware.
- Features MUST have explicit availability timestamps.
- Missing values MUST use a documented policy and missingness indicators where appropriate.
- Hyperparameters MUST be selected without touching the final holdout.
- Output MUST include three-way probabilities and diagnostics.
- Model card MUST state data coverage, exclusions, limitations, and calibration domain.
- Promotion requires improvement over simple base rates on multiple proper scoring rules.
- A model that improves accuracy but worsens calibration cannot be promoted without justification.

#### Q04 — Expected-goals rolling model

- Purpose: Opponent-adjusted xG for and against with decay.
- Training split MUST be chronological and competition-aware.
- Features MUST have explicit availability timestamps.
- Missing values MUST use a documented policy and missingness indicators where appropriate.
- Hyperparameters MUST be selected without touching the final holdout.
- Output MUST include three-way probabilities and diagnostics.
- Model card MUST state data coverage, exclusions, limitations, and calibration domain.
- Promotion requires improvement over simple base rates on multiple proper scoring rules.
- A model that improves accuracy but worsens calibration cannot be promoted without justification.

#### Q05 — Shot-quality logistic model

- Purpose: Outcome-sensitive shot features when licensed event data exists.
- Training split MUST be chronological and competition-aware.
- Features MUST have explicit availability timestamps.
- Missing values MUST use a documented policy and missingness indicators where appropriate.
- Hyperparameters MUST be selected without touching the final holdout.
- Output MUST include three-way probabilities and diagnostics.
- Model card MUST state data coverage, exclusions, limitations, and calibration domain.
- Promotion requires improvement over simple base rates on multiple proper scoring rules.
- A model that improves accuracy but worsens calibration cannot be promoted without justification.

#### Q06 — Gradient-boosted outcome model

- Purpose: Nonlinear interactions with strict temporal validation.
- Training split MUST be chronological and competition-aware.
- Features MUST have explicit availability timestamps.
- Missing values MUST use a documented policy and missingness indicators where appropriate.
- Hyperparameters MUST be selected without touching the final holdout.
- Output MUST include three-way probabilities and diagnostics.
- Model card MUST state data coverage, exclusions, limitations, and calibration domain.
- Promotion requires improvement over simple base rates on multiple proper scoring rules.
- A model that improves accuracy but worsens calibration cannot be promoted without justification.

#### Q07 — Market prior model

- Purpose: Margin-removed market consensus as a benchmark, not ground truth.
- Training split MUST be chronological and competition-aware.
- Features MUST have explicit availability timestamps.
- Missing values MUST use a documented policy and missingness indicators where appropriate.
- Hyperparameters MUST be selected without touching the final holdout.
- Output MUST include three-way probabilities and diagnostics.
- Model card MUST state data coverage, exclusions, limitations, and calibration domain.
- Promotion requires improvement over simple base rates on multiple proper scoring rules.
- A model that improves accuracy but worsens calibration cannot be promoted without justification.

#### Q08 — Bayesian ensemble

- Purpose: Weighted predictive distribution with model uncertainty.
- Training split MUST be chronological and competition-aware.
- Features MUST have explicit availability timestamps.
- Missing values MUST use a documented policy and missingness indicators where appropriate.
- Hyperparameters MUST be selected without touching the final holdout.
- Output MUST include three-way probabilities and diagnostics.
- Model card MUST state data coverage, exclusions, limitations, and calibration domain.
- Promotion requires improvement over simple base rates on multiple proper scoring rules.
- A model that improves accuracy but worsens calibration cannot be promoted without justification.

#### Q09 — Calibration layer

- Purpose: Isotonic, Platt/temperature, or Dirichlet selected by validation.
- Training split MUST be chronological and competition-aware.
- Features MUST have explicit availability timestamps.
- Missing values MUST use a documented policy and missingness indicators where appropriate.
- Hyperparameters MUST be selected without touching the final holdout.
- Output MUST include three-way probabilities and diagnostics.
- Model card MUST state data coverage, exclusions, limitations, and calibration domain.
- Promotion requires improvement over simple base rates on multiple proper scoring rules.
- A model that improves accuracy but worsens calibration cannot be promoted without justification.

#### Q10 — Scenario mixture

- Purpose: Lineup and tactical branches integrated as a probability mixture.
- Training split MUST be chronological and competition-aware.
- Features MUST have explicit availability timestamps.
- Missing values MUST use a documented policy and missingness indicators where appropriate.
- Hyperparameters MUST be selected without touching the final holdout.
- Output MUST include three-way probabilities and diagnostics.
- Model card MUST state data coverage, exclusions, limitations, and calibration domain.
- Promotion requires improvement over simple base rates on multiple proper scoring rules.
- A model that improves accuracy but worsens calibration cannot be promoted without justification.

### 18.2 Market probability normalization

```python
from decimal import Decimal

def multiplicative_fair_probabilities(decimal_prices: list[Decimal]) -> list[Decimal]:
    if any(price <= Decimal("1") for price in decimal_prices):
        raise ValueError("decimal prices must exceed 1")
    raw = [Decimal("1") / price for price in decimal_prices]
    overround = sum(raw)
    if overround <= 0:
        raise ValueError("invalid overround")
    return [p / overround for p in raw]
```

The production system additionally implements power and Shin methods and stores the chosen method.
Comparisons at different lines are forbidden.

### 18.3 Evaluation metrics

- multiclass Brier score: report overall, by competition, by season, by probability band, and with bootstrap uncertainty when meaningful.
- log loss: report overall, by competition, by season, by probability band, and with bootstrap uncertainty when meaningful.
- ranked probability score: report overall, by competition, by season, by probability band, and with bootstrap uncertainty when meaningful.
- expected calibration error: report overall, by competition, by season, by probability band, and with bootstrap uncertainty when meaningful.
- adaptive calibration error: report overall, by competition, by season, by probability band, and with bootstrap uncertainty when meaningful.
- reliability slope and intercept: report overall, by competition, by season, by probability band, and with bootstrap uncertainty when meaningful.
- sharpness: report overall, by competition, by season, by probability band, and with bootstrap uncertainty when meaningful.
- accuracy as secondary context: report overall, by competition, by season, by probability band, and with bootstrap uncertainty when meaningful.
- top-label calibration error: report overall, by competition, by season, by probability band, and with bootstrap uncertainty when meaningful.
- decision curve by threshold: report overall, by competition, by season, by probability band, and with bootstrap uncertainty when meaningful.
- closing-line value as market-comparison metric: report overall, by competition, by season, by probability band, and with bootstrap uncertainty when meaningful.
- coverage by league and season: report overall, by competition, by season, by probability band, and with bootstrap uncertainty when meaningful.
- abstention rate: report overall, by competition, by season, by probability band, and with bootstrap uncertainty when meaningful.
- degraded-run rate: report overall, by competition, by season, by probability band, and with bootstrap uncertainty when meaningful.
- cost per valid locked forecast: report overall, by competition, by season, by probability band, and with bootstrap uncertainty when meaningful.
- latency per stage: report overall, by competition, by season, by probability band, and with bootstrap uncertainty when meaningful.

## 19. Backtesting, Calibration, and Shadow Experiments

### 19.1 Backtest protocol

1. Select a historical date range before examining final metrics.
2. Construct simulated cutoffs relative to kickoff.
3. Rebuild features using only records whose knowledge time is at or before each cutoff.
4. Use walk-forward folds with no random cross-time leakage.
5. Freeze the feature definition and model configuration per fold.
6. Compare against competition base rate, Elo, Poisson, and market-prior baselines.
7. Fit calibrators only on training/validation history preceding the test fold.
8. Report missingness and provider coverage drift.
9. Bootstrap match-level differences with competition-aware grouping.
10. Store the full backtest manifest and code commit.

### 19.2 Leakage sentinels

- Sentinel: create a poisoned fixture for “final score accidentally joined by fixture ID” and assert the pipeline excludes or fails it.
- Sentinel: create a poisoned fixture for “closing odds used at an earlier cutoff” and assert the pipeline excludes or fails it.
- Sentinel: create a poisoned fixture for “confirmed lineup captured after cutoff” and assert the pipeline excludes or fails it.
- Sentinel: create a poisoned fixture for “injury article publication time inferred from crawl time” and assert the pipeline excludes or fails it.
- Sentinel: create a poisoned fixture for “provider record overwritten instead of versioned” and assert the pipeline excludes or fails it.
- Sentinel: create a poisoned fixture for “season aggregate including the target match” and assert the pipeline excludes or fails it.
- Sentinel: create a poisoned fixture for “future Elo rating used as current” and assert the pipeline excludes or fails it.
- Sentinel: create a poisoned fixture for “post-match xG in pre-match feature table” and assert the pipeline excludes or fails it.
- Sentinel: create a poisoned fixture for “case-memory outcome text embedded in current query” and assert the pipeline excludes or fails it.
- Sentinel: create a poisoned fixture for “timezone conversion moving a record before cutoff” and assert the pipeline excludes or fails it.
- Sentinel: create a poisoned fixture for “replayed provider sandbox returning current data for historical call” and assert the pipeline excludes or fails it.
- Sentinel: create a poisoned fixture for “calibrator trained on test fold” and assert the pipeline excludes or fails it.

### 19.3 Shadow experiment rules

- Assignment is deterministic from fixture ID and experiment salt.
- Production output is computed first and immutable to experiment results.
- Shadow calls use a separate budget ledger.
- Experiments compare one primary variable at a time when feasible.
- Promotion criteria are declared before evaluation.
- Negative, neutral, and failed results are retained.
- No experiment is promoted on fewer than the declared minimum cases.

### 19.4 Required initial shadow architecture variants

| Variant | Pipeline | User-visible | Purpose |
| --- | --- | --- | --- |
| A | Quant only | Only when selected as production control | Measure transparent mathematical baseline |
| B | Gemini research + Sonnet synthesis | Shadow by default | Measure simple multi-model lift |
| C | Gemini + specialist critics + Sonnet | Shadow by default | Measure adversarial-review lift |
| D | Full agent architecture + historical RAG | Shadow by default | Measure retrieval and specialization lift |
| E | Full architecture + isolated market signal | Shadow by default | Measure market contribution against leakage-safe baseline |

Every variant produces an independently locked shadow prediction before kickoff.
Only the configured production variant is visible in the main prediction UI; shadow results remain evaluation artifacts.
Promotion decisions compare Brier score, log loss, ranked probability score, calibration, coverage, latency, and cost against the bookmaker market baseline.

### 19.5 The three controlled learning mechanisms

| Mechanism | What changes | What does not happen automatically | Promotion evidence |
| --- | --- | --- | --- |
| Memory learning | Validated case memory, retrieval tags, and scoped lessons grow | LLM weights do not change after every match | Retrieval eval and leakage-safe case utility |
| Statistical learning | Quant model artifacts and calibrators are retrained on chronological data | A new artifact never silently replaces production | Walk-forward backtest, calibration, and shadow comparison |
| Policy learning | Agent routing, source weights, retrieval policy, and budget allocation may change | Small samples never permanently bless or ban an agent/source | Predeclared experiment with uncertainty and rollback |

Every learned artifact is versioned, reversible, scope-limited, and linked to the cases or experiments that justified it.

## 20. Reliability: Retry, Idempotency, Caching, and Deduplication

### 20.1 Error classes

| Class | Examples | Retry |
| --- | --- | --- |
| Transient provider | timeout, 429, 502, 503 | bounded exponential backoff with jitter |
| Permanent provider | invalid key, forbidden endpoint, invalid market | no automatic retry |
| Schema mismatch | missing required field, incompatible type | one refetch or repair based on source |
| Model refusal | provider refusal outcome | route-specific fallback only if policy allows |
| Model malformed output | invalid JSON or schema | one schema-repair attempt |
| Budget | reservation unavailable | pause; requires budget/config change |
| Identity ambiguity | multiple fixture matches | quarantine; human resolution |
| Cutoff violation | evidence after cutoff | exclude; fail if material coverage lost |
| Internal invariant | illegal transition, lock mutation | no retry; alert |

### 20.2 Retry schedule

```text
delay = min(max_delay, base_delay * 2^attempt) + uniform(0, jitter)
provider default: base=1s, max=30s, attempts=4
model default: base=2s, max=60s, attempts=3
database serialization: base=50ms, max=1s, attempts=5
schema repair: exactly 1 attempt, no open-ended loop
```

### 20.3 Idempotency scope

- Command key namespace includes personal workspace, route, and caller key.
- Request hash mismatch for an existing key returns HTTP 409.
- The first completed response is stored and replayed.
- In-progress replay returns the original operation resource.
- Temporal workflow IDs derive from logical operation IDs.
- Activity idempotency uses business keys and database uniqueness constraints.

### 20.4 Cache keys

- fixture list: key includes provider, competitions, start UTC, end UTC, provider config version.
- fixture search: key includes normalized query, date range, provider set.
- source snapshot: key includes canonical URL/provider object, provider update time, content hash.
- retrieval result: key includes agent, policy version, query hash, cutoff, corpus version.
- model response: key includes provider, exact model ID, prompt version, rendered hash, tool policy, schema version.
- quant prediction: key includes model artifact hash, feature set hash, calibrator hash.
- public view: key includes resource row version, locale, permission scope.

## 21. Security and Privacy

### 21.1 Threat boundaries

- External provider payloads and web content are untrusted data.
- Retrieved text may contain prompt injection and must never modify system policy or tool permissions.
- Model output is untrusted until strict schema and domain validation pass.
- Client input is untrusted even in a personal-use app.
- Object storage URLs and provider identifiers may be sensitive.
- Logs are a data sink and must be redacted before emission.

### 21.2 Required controls

- SEC-001 — **Secret isolation:** Keys exist only in server-side secret providers and provider adapters.
  - Test: `tests/security/test_sec_001.py`.
- SEC-002 — **Prompt injection boundary:** Retrieved content is delimited as data and cannot grant tools or override role policy.
  - Test: `tests/security/test_sec_002.py`.
- SEC-003 — **SSRF defense:** Research fetches use allowlisted schemes, DNS/IP validation, redirect limits, and egress controls.
  - Test: `tests/security/test_sec_003.py`.
- SEC-004 — **SQL safety:** All queries are parameterized; no model-authored SQL executes directly.
  - Test: `tests/security/test_sec_004.py`.
- SEC-005 — **Object access:** Snapshots use private buckets and short-lived signed URLs.
  - Test: `tests/security/test_sec_005.py`.
- SEC-006 — **Auth:** Personal session uses secure, HttpOnly, SameSite cookies and CSRF protection.
  - Test: `tests/security/test_sec_006.py`.
- SEC-007 — **Authorization:** Every resource query is scoped to workspace ownership.
  - Test: `tests/security/test_sec_007.py`.
- SEC-008 — **Rate limiting:** Mutations, searches, probes, and streams have bounded limits.
  - Test: `tests/security/test_sec_008.py`.
- SEC-009 — **Dependency integrity:** Lockfiles, provenance, and automated vulnerability review are required.
  - Test: `tests/security/test_sec_009.py`.
- SEC-010 — **Container safety:** Run as non-root with read-only filesystem where feasible.
  - Test: `tests/security/test_sec_010.py`.
- SEC-011 — **PII minimization:** Do not store bookmaker credentials, user financial data, or unnecessary identity data.
  - Test: `tests/security/test_sec_011.py`.
- SEC-012 — **Audit:** Security-sensitive config, provider, lock, and deletion actions are append-only audited.
  - Test: `tests/security/test_sec_012.py`.

### 21.3 Retention defaults

| Data class | Pilot retention | Notes |
| --- | --- | --- |
| Provider raw payloads | 30 days or shorter provider license | Delete sooner when terms require |
| Normalized factual records | Indefinite personal use subject to license | Retain provenance pointer |
| Model prompts/responses | 90 days | Redacted and no secrets |
| Locked predictions | Indefinite | Immutable audit artifact |
| Post-match cases/lessons | Indefinite | No personal data |
| Operational logs | 14 days | Redacted |
| Trace spans | 7 days | No payload bodies by default |
| Quarantine | 7 days | Restricted access then delete |

## 22. Observability

### 22.1 Trace topology

```text
ui.action
└── http.command
    ├── db.idempotency
    ├── temporal.start_workflow
    └── workflow.run
        ├── stage.S01
        │   ├── provider.search
        │   ├── object.snapshot_write
        │   └── db.evidence_write
        ├── stage.S14
        │   ├── feature.load
        │   ├── quant.predict
        │   └── calibrator.apply
        └── stage.S23
            ├── manifest.hash
            ├── object.lock_write
            └── db.lock_insert
```

### 22.2 Metrics catalog

| Metric | Type | Bounded labels |
| --- | --- | --- |
| miron_baba_ai_scan_total | counter | status |
| miron_baba_ai_scan_duration_seconds | histogram | status |
| miron_baba_ai_candidates_per_scan | histogram | none |
| miron_baba_ai_analysis_run_total | counter | final_state |
| miron_baba_ai_analysis_duration_seconds | histogram | sport,final_state |
| miron_baba_ai_stage_duration_seconds | histogram | stage,status |
| miron_baba_ai_stage_retry_total | counter | stage,error_class |
| miron_baba_ai_provider_call_total | counter | provider,operation,status |
| miron_baba_ai_provider_latency_seconds | histogram | provider,operation |
| miron_baba_ai_provider_quota_remaining | gauge | provider |
| miron_baba_ai_model_call_total | counter | provider,route,status |
| miron_baba_ai_model_input_tokens_total | counter | provider,route |
| miron_baba_ai_model_output_tokens_total | counter | provider,route |
| miron_baba_ai_external_cost_usd_total | counter | provider,purpose |
| miron_baba_ai_budget_reserved_usd | gauge | scope |
| miron_baba_ai_evidence_item_total | counter | source_class,status |
| miron_baba_ai_contradiction_total | counter | materiality,resolution |
| miron_baba_ai_stale_evidence_total | counter | source_class |
| miron_baba_ai_lock_total | counter | status |
| miron_baba_ai_backtest_brier | gauge | model,fold |
| miron_baba_ai_calibration_ece | gauge | model,domain |
| miron_baba_ai_autopsy_total | counter | status |

### 22.3 Logging rules

- Use structured JSON logs.
- Include timestamp, level, service, environment, correlation ID, run ID, stage ID, and stable event name.
- Do not log prompt bodies, full provider payloads, API keys, cookies, authorization headers, or private URLs.
- Hash external IDs where operationally sufficient.
- Sample successful high-volume logs; never sample lock failures or invariant violations.

### 22.4 Alert conditions

- Alert on prediction lock mutation attempt; link the matching runbook and correlation search.
- Alert on cutoff violation reaches an agent packet; link the matching runbook and correlation search.
- Alert on monthly budget above 90%; link the matching runbook and correlation search.
- Alert on provider quota below configured floor; link the matching runbook and correlation search.
- Alert on model verification expired; link the matching runbook and correlation search.
- Alert on schema invalid rate above 5% for 15 minutes; link the matching runbook and correlation search.
- Alert on fixture identity quarantine spike; link the matching runbook and correlation search.
- Alert on workflow stuck beyond stage SLA; link the matching runbook and correlation search.
- Alert on SSE delivery backlog; link the matching runbook and correlation search.
- Alert on object snapshot hash mismatch; link the matching runbook and correlation search.
- Alert on database migration drift; link the matching runbook and correlation search.
- Alert on backtest leakage sentinel failure; link the matching runbook and correlation search.

## 23. Environment Variables

| Variable | Default/presence | Purpose |
| --- | --- | --- |
| COMPOSE_PROJECT_NAME | miron-baba-ai | Stable Docker Compose project slug |
| PRODUCT_NAME | MİRON BABA AI | Exact user-facing product name |
| APP_ENV | local | Environment name |
| APP_TIMEZONE | Europe/Istanbul | Display and scan timezone; server storage remains UTC |
| APP_BASE_URL | http://localhost:3000 | Frontend origin |
| NEXT_PUBLIC_API_BASE_URL | http://localhost:8000 | Browser-visible backend origin |
| API_INTERNAL_BASE_URL | http://api:8000 | Container-network backend origin |
| DATABASE_URL | postgresql+psycopg://miron_baba_ai:local_only@postgres:5432/miron_baba_ai | Container-network PostgreSQL DSN |
| REDIS_URL | redis://redis:6379/0 | Container-network Redis DSN |
| TEMPORAL_ADDRESS | temporal:7233 | Container-network Temporal endpoint |
| TEMPORAL_NAMESPACE | miron-baba-ai | Temporal namespace |
| S3_ENDPOINT_URL | http://minio:9000 | Container-network S3-compatible endpoint |
| S3_BUCKET_SNAPSHOTS | miron-baba-ai-snapshots | Private snapshot bucket |
| S3_ACCESS_KEY_ID | required-local | Local MinIO access ID |
| S3_SECRET_ACCESS_KEY | required-local | Local MinIO secret |
| OPENAI_API_KEY | optional-until-enabled | OpenAI server-side key |
| ANTHROPIC_API_KEY | optional-until-enabled | Anthropic server-side key |
| GEMINI_API_KEY | optional-until-enabled | Google server-side key |
| THE_ODDS_API_KEY | optional-until-enabled | Allowed odds provider key |
| FOOTBALL_DATA_API_KEY | optional-until-enabled | Fixture provider key |
| SPORT_STATS_API_KEY | optional-until-enabled | Licensed statistics provider key |
| WEATHER_API_KEY | optional-until-enabled | Weather provider key |
| MODEL_REGISTRY_PATH | config/models.yaml | Versioned registry |
| PROVIDER_REGISTRY_PATH | config/providers.yaml | Provider policy registry |
| MONTHLY_BUDGET_USD | 10.00 | Hard monthly cap |
| RUN_SOFT_CAP_USD | 0.50 | Soft per-analysis cap |
| RUN_HARD_CAP_USD | 2.00 | Hard per-analysis cap |
| OTEL_EXPORTER_OTLP_ENDPOINT | http://otel-collector:4318 | Container-network telemetry exporter |
| LOG_LEVEL | INFO | Bounded log level |
| SESSION_SECRET | required | At least 32 random bytes |
| LOCK_SIGNING_PRIVATE_KEY_PATH | optional-local | Ed25519 signing key location |

`.env.example` contains placeholders only.
Startup fails if an enabled provider lacks its required secret.

## 24. Docker and Local Setup

### 24.0 Docker-only local-development contract

- The Mac host prerequisite is Docker Desktop with Docker Compose v2; no Homebrew package is required.
- The host MUST NOT need Node.js, pnpm, Python, pip, uv, PostgreSQL, Redis, Temporal CLI, MinIO CLI, Playwright, OpenTelemetry, Prometheus, Grafana, or Loki.
- Every long-running service runs in Docker Compose.
- Every one-shot operation runs through a Docker Compose service.
- Source files are bind-mounted for development; dependency directories live in named Docker volumes.
- The host repository never receives container-owned `node_modules`, virtual environments, database files, or generated caches.
- Dockerfiles use non-root runtime users and pinned base-image versions; release builds SHOULD pin image digests.
- Compose health checks, not arbitrary sleeps, control service readiness.
- The canonical Compose project slug is `miron-baba-ai`; the visible product name remains exactly `MİRON BABA AI`.
- Codex MUST express all setup, lint, test, build, migration, seed, and run instructions as `docker compose` commands.

### 24.1 Services

| Service | Local port | Health criterion |
| --- | --- | --- |
| web | 3000 | HTTP 200 from `/` |
| api | 8000 | HTTP 200 from `/api/v1/health/ready` |
| worker | none | Temporal worker poller registered and heartbeat healthy |
| postgres | 5432 | `pg_isready` and migration head |
| redis | 6379 | PING |
| temporal | 7233 | namespace reachable |
| temporal-ui | 8080 | HTTP 200 |
| minio | 9000/9001 | bucket health and private policy |
| otel-collector | 4317/4318 | OTLP receiver healthy |
| prometheus | 9090 | targets healthy |
| grafana | 3001 | datasources provisioned |
| loki | 3100 | ready endpoint |
| migrate | one-shot | Alembic reaches expected head then exits zero |
| seed | one-shot | Deterministic seed transaction commits then exits zero |
| contracts | one-shot | JSON Schema and TypeScript contracts regenerate cleanly |
| toolbox | one-shot | Repository maintenance commands run in an isolated image |
| test-api | profile:test | Python test suite exits zero |
| test-web | profile:test | TypeScript/Vitest suite exits zero |
| test-e2e | profile:test | Containerized Playwright suite exits zero |

### 24.2 Canonical Compose topology

```yaml
name: miron-baba-ai

x-api-image: &api-image
  build:
    context: .
    dockerfile: apps/api/Dockerfile
    target: development
  env_file: [.env]
  init: true
  networks: [miron-baba-ai]

services:
  postgres:
    image: pgvector/pgvector:pg17
    environment:
      POSTGRES_DB: miron_baba_ai
      POSTGRES_USER: miron_baba_ai
      POSTGRES_PASSWORD: local_only
    volumes:
      - postgres-data:/var/lib/postgresql/data
    healthcheck:
      test: [CMD-SHELL, pg_isready -U miron_baba_ai -d miron_baba_ai]
      interval: 5s
      timeout: 3s
      retries: 20
    networks: [miron-baba-ai]

  redis:
    image: redis:7-alpine
    command: [redis-server, --appendonly, yes]
    volumes:
      - redis-data:/data
    healthcheck:
      test: [CMD, redis-cli, ping]
      interval: 5s
      timeout: 3s
      retries: 20
    networks: [miron-baba-ai]

  temporal:
    image: temporalio/auto-setup:PINNED_VERSION
    environment:
      DB: postgres12
      DB_PORT: 5432
      POSTGRES_USER: miron_baba_ai
      POSTGRES_PWD: local_only
      POSTGRES_SEEDS: postgres
    depends_on:
      postgres:
        condition: service_healthy
    networks: [miron-baba-ai]

  temporal-ui:
    image: temporalio/ui:PINNED_VERSION
    environment:
      TEMPORAL_ADDRESS: temporal:7233
    ports: ["8080:8080"]
    depends_on:
      temporal:
        condition: service_started
    networks: [miron-baba-ai]

  minio:
    image: minio/minio:PINNED_VERSION
    command: [server, /data, --console-address, :9001]
    env_file: [.env]
    volumes:
      - minio-data:/data
    ports: ["9000:9000", "9001:9001"]
    networks: [miron-baba-ai]

  migrate:
    <<: *api-image
    command: [alembic, upgrade, head]
    depends_on:
      postgres:
        condition: service_healthy
    restart: no

  seed:
    <<: *api-image
    command: [python, -m, app.seed]
    depends_on:
      migrate:
        condition: service_completed_successfully
    restart: no

  api:
    <<: *api-image
    command: [uvicorn, app.main:app, --host, 0.0.0.0, --port, "8000", --reload]
    volumes:
      - ./apps/api:/workspace/apps/api
      - ./packages:/workspace/packages
    ports: ["8000:8000"]
    depends_on:
      migrate:
        condition: service_completed_successfully
      redis:
        condition: service_healthy
      temporal:
        condition: service_started
      minio:
        condition: service_started

  worker:
    <<: *api-image
    command: [python, -m, app.worker]
    volumes:
      - ./apps/api:/workspace/apps/api
      - ./packages:/workspace/packages
    depends_on:
      migrate:
        condition: service_completed_successfully
      temporal:
        condition: service_started

  web:
    build:
      context: .
      dockerfile: apps/web/Dockerfile
      target: development
    env_file: [.env]
    init: true
    command: [pnpm, --filter, web, dev, --hostname, 0.0.0.0]
    volumes:
      - ./apps/web:/workspace/apps/web
      - ./packages:/workspace/packages
      - web-node-modules:/workspace/node_modules
    ports: ["3000:3000"]
    depends_on:
      api:
        condition: service_healthy
    networks: [miron-baba-ai]

  toolbox:
    <<: *api-image
    profiles: [tools]
    volumes:
      - ./:/workspace
    entrypoint: [./scripts/docker-toolbox]

  test-api:
    <<: *api-image
    profiles: [test]
    command: [pytest, -q]

  test-web:
    build:
      context: .
      dockerfile: apps/web/Dockerfile
      target: test
    profiles: [test]
    command: [pnpm, test]
    networks: [miron-baba-ai]

  test-e2e:
    image: mcr.microsoft.com/playwright:PINNED_VERSION
    profiles: [test]
    working_dir: /workspace
    command: [pnpm, playwright, test]
    volumes:
      - ./:/workspace
      - e2e-node-modules:/workspace/node_modules
    depends_on:
      web:
        condition: service_healthy
    networks: [miron-baba-ai]

networks:
  miron-baba-ai:
    name: miron-baba-ai

volumes:
  postgres-data:
  redis-data:
  minio-data:
  web-node-modules:
  e2e-node-modules:
```

`PINNED_VERSION` is a specification marker: Codex MUST resolve a compatible current version, record it in the dependency ledger, and replace the marker before the first runnable commit.
The actual Compose files MAY split development, test, and observability overrides, but the Docker-only guarantee cannot weaken.

### 24.3 First-run commands

```bash
docker compose --env-file .env.example run --rm toolbox init-env
docker compose build
docker compose up -d postgres redis temporal minio
docker compose run --rm migrate
docker compose run --rm seed
docker compose run --rm contracts
docker compose --profile test run --rm test-api
docker compose --profile test run --rm test-web
docker compose up -d web api worker temporal-ui
docker compose --profile observability up -d otel-collector prometheus grafana loki
```

The `toolbox init-env` command copies `.env.example` to `.env` through a bind-mounted, narrowly scoped container and refuses to overwrite an existing `.env`.
Codex MUST implement all commands as documented Compose services; host package-manager commands are forbidden.
The default run uses mock providers and deterministic model stubs until keys are intentionally enabled.

### 24.4 Daily Docker commands

```bash
docker compose up -d
docker compose logs -f web api worker
docker compose run --rm migrate
docker compose run --rm seed
docker compose run --rm contracts
docker compose --profile test run --rm test-api
docker compose --profile test run --rm test-web
docker compose --profile test run --rm test-e2e
docker compose run --rm toolbox lint
docker compose run --rm toolbox typecheck
docker compose down
```

`docker compose down` removes containers and the network but preserves named volumes.
Volume deletion is a separate destructive operation and MUST NOT appear in routine setup instructions.

### 24.5 Image and volume topology

| Concern | Docker decision | Requirement |
| --- | --- | --- |
| Web image | Multi-stage Node image | Install with frozen lockfile; non-root dev/runtime user |
| API/worker/toolbox image | Shared multi-stage Python image | Locked dependencies; separate commands; non-root user |
| E2E image | Official Playwright image compatible with project version | Browsers exist only in container |
| PostgreSQL image | pgvector-enabled PostgreSQL 17 image | Persistent named volume and health check |
| Redis image | Redis 7 Alpine | Persistent only if workflow policy requires it |
| Temporal | Pinned server plus UI images | Namespace initialization is idempotent |
| MinIO | Pinned S3-compatible image | Private bucket initialization through one-shot service |
| Node dependencies | Named volume | Never create host `node_modules` |
| Python environment | Image layer | Never create host `.venv` |
| Database data | Named volume | Never write database files into repository |
| Snapshots | Named volume backed MinIO | Never expose public bucket |

### 24.6 Compose dependency rules

- `api` depends on healthy PostgreSQL, Redis, Temporal, MinIO, and successful migration.
- `worker` depends on the same healthy infrastructure and successful migration.
- `web` depends on healthy API but still renders a recoverable unavailable state.
- `seed` depends on successful migration and remains safe to rerun.
- `test-api` starts an isolated test database and mock provider network.
- `test-web` uses container-local dependencies and generated contracts.
- `test-e2e` starts the test topology and reaches `web` through the Compose network.
- Production-like services restart on failure; one-shot jobs never restart infinitely.
- External provider access is disabled in test profiles.

### 24.7 Forbidden host commands

```text
FORBIDDEN IN DOCUMENTATION AND CODEX HANDOFFS:
pnpm install
pnpm dev
npm install
python -m venv
pip install
uv sync
alembic upgrade head
pytest
playwright test
psql
redis-cli

REQUIRED FORM:
docker compose run --rm <service> <bounded-command>
or
docker compose up -d <service>
```

### 24.8 Migration policy

1. Every schema change has an Alembic migration and downgrade unless irreversible by explicit ADR.
2. Migration review includes lock duration, table rewrite risk, index build method, and backfill plan.
3. Production-like migration tests run from the previous released schema.
4. Application deployment supports one-version rolling compatibility when hosted.
5. Prediction-lock constraints may never be weakened without a security and audit ADR.

## 25. Seed Data and Mock Providers

### 25.1 Deterministic seed fixtures

| Seed ID | Kickoff | Home | Away | Purpose |
| --- | --- | --- | --- | --- |
| FIX-IST-001 | 2026-08-22T20:00:00+03:00 | Anka FK | Boğaz SK | normal complete coverage |
| FIX-IST-002 | 2026-08-23T16:00:00+03:00 | Marmara 1923 | Ege Atletik | stale weather and missing lineup |
| FIX-IST-003 | 2026-08-24T21:45:00+03:00 | Toros Birlik | Trakya Spor | provider identity alias collision |
| FIX-IST-004 | 2026-08-24T23:30:00+03:00 | Başkent Gücü | Karadeniz FK | crosses UTC date boundary |

Seed names are fictional and must remain separate from provider production mappings.

### 25.2 Mock provider scenarios

- MOCK-001: happy path; fixed clock, request transcript, response fixture, and expected domain result.
- MOCK-002: empty fixture window; fixed clock, request transcript, response fixture, and expected domain result.
- MOCK-003: duplicate fixture from two providers; fixed clock, request transcript, response fixture, and expected domain result.
- MOCK-004: postponed kickoff; fixed clock, request transcript, response fixture, and expected domain result.
- MOCK-005: ambiguous team alias; fixed clock, request transcript, response fixture, and expected domain result.
- MOCK-006: provider timeout then recovery; fixed clock, request transcript, response fixture, and expected domain result.
- MOCK-007: 429 with Retry-After; fixed clock, request transcript, response fixture, and expected domain result.
- MOCK-008: invalid API key; fixed clock, request transcript, response fixture, and expected domain result.
- MOCK-009: quota exhausted; fixed clock, request transcript, response fixture, and expected domain result.
- MOCK-010: malformed JSON; fixed clock, request transcript, response fixture, and expected domain result.
- MOCK-011: unknown enum; fixed clock, request transcript, response fixture, and expected domain result.
- MOCK-012: source published after cutoff; fixed clock, request transcript, response fixture, and expected domain result.
- MOCK-013: odds stale by TTL; fixed clock, request transcript, response fixture, and expected domain result.
- MOCK-014: odds line mismatch; fixed clock, request transcript, response fixture, and expected domain result.
- MOCK-015: one bookmaker outlier; fixed clock, request transcript, response fixture, and expected domain result.
- MOCK-016: injury contradiction; fixed clock, request transcript, response fixture, and expected domain result.
- MOCK-017: unconfirmed lineup; fixed clock, request transcript, response fixture, and expected domain result.
- MOCK-018: weather forecast unavailable; fixed clock, request transcript, response fixture, and expected domain result.
- MOCK-019: model malformed output then repair; fixed clock, request transcript, response fixture, and expected domain result.
- MOCK-020: model refusal; fixed clock, request transcript, response fixture, and expected domain result.
- MOCK-021: committee disagreement; fixed clock, request transcript, response fixture, and expected domain result.
- MOCK-022: final critic revision; fixed clock, request transcript, response fixture, and expected domain result.
- MOCK-023: lock after kickoff attempt; fixed clock, request transcript, response fixture, and expected domain result.
- MOCK-024: result correction after final; fixed clock, request transcript, response fixture, and expected domain result.
- MOCK-025: post-match events incomplete; fixed clock, request transcript, response fixture, and expected domain result.

## 26. Failure and Degraded Modes

#### F001 — No fixture provider

- Required behavior: Search/scan unavailable; existing canonical fixtures remain viewable.
- UI: show a compact degraded or blocked banner with one recovery action.
- API: return stable reason code and correlation ID.
- Workflow: preserve completed immutable artifacts and release unused budget.
- Observability: increment bounded failure metric and emit one structured warning or error.
- Test fixture: `tests/golden/failures/f001.json`.

#### F002 — One fixture provider down

- Required behavior: Use another enabled provider; expose reduced coverage.
- UI: show a compact degraded or blocked banner with one recovery action.
- API: return stable reason code and correlation ID.
- Workflow: preserve completed immutable artifacts and release unused budget.
- Observability: increment bounded failure metric and emit one structured warning or error.
- Test fixture: `tests/golden/failures/f002.json`.

#### F003 — Fixture ambiguity

- Required behavior: Quarantine mapping and block deep analysis.
- UI: show a compact degraded or blocked banner with one recovery action.
- API: return stable reason code and correlation ID.
- Workflow: preserve completed immutable artifacts and release unused budget.
- Observability: increment bounded failure metric and emit one structured warning or error.
- Test fixture: `tests/golden/failures/f003.json`.

#### F004 — No research provider

- Required behavior: Continue only with structured providers if minimum evidence policy passes.
- UI: show a compact degraded or blocked banner with one recovery action.
- API: return stable reason code and correlation ID.
- Workflow: preserve completed immutable artifacts and release unused budget.
- Observability: increment bounded failure metric and emit one structured warning or error.
- Test fixture: `tests/golden/failures/f004.json`.

#### F005 — No stats provider

- Required behavior: Do not fabricate metrics; produce qualitative degraded report or no-publish.
- UI: show a compact degraded or blocked banner with one recovery action.
- API: return stable reason code and correlation ID.
- Workflow: preserve completed immutable artifacts and release unused budget.
- Observability: increment bounded failure metric and emit one structured warning or error.
- Test fixture: `tests/golden/failures/f005.json`.

#### F006 — No odds provider

- Required behavior: Forecast may continue; market comparison is unavailable.
- UI: show a compact degraded or blocked banner with one recovery action.
- API: return stable reason code and correlation ID.
- Workflow: preserve completed immutable artifacts and release unused budget.
- Observability: increment bounded failure metric and emit one structured warning or error.
- Test fixture: `tests/golden/failures/f006.json`.

#### F007 — Odds stale

- Required behavior: Mark stale and exclude from edge calculations.
- UI: show a compact degraded or blocked banner with one recovery action.
- API: return stable reason code and correlation ID.
- Workflow: preserve completed immutable artifacts and release unused budget.
- Observability: increment bounded failure metric and emit one structured warning or error.
- Test fixture: `tests/golden/failures/f007.json`.

#### F008 — Weather unavailable

- Required behavior: Use unknown environment factor; no guessed forecast.
- UI: show a compact degraded or blocked banner with one recovery action.
- API: return stable reason code and correlation ID.
- Workflow: preserve completed immutable artifacts and release unused budget.
- Observability: increment bounded failure metric and emit one structured warning or error.
- Test fixture: `tests/golden/failures/f008.json`.

#### F009 — Model route unavailable

- Required behavior: Use evaluated fallback route or pause; no arbitrary model substitution.
- UI: show a compact degraded or blocked banner with one recovery action.
- API: return stable reason code and correlation ID.
- Workflow: preserve completed immutable artifacts and release unused budget.
- Observability: increment bounded failure metric and emit one structured warning or error.
- Test fixture: `tests/golden/failures/f009.json`.

#### F010 — Model price unknown

- Required behavior: Prohibit call and fail verification gate.
- UI: show a compact degraded or blocked banner with one recovery action.
- API: return stable reason code and correlation ID.
- Workflow: preserve completed immutable artifacts and release unused budget.
- Observability: increment bounded failure metric and emit one structured warning or error.
- Test fixture: `tests/golden/failures/f010.json`.

#### F011 — Model malformed output

- Required behavior: One repair attempt then fail/degrade.
- UI: show a compact degraded or blocked banner with one recovery action.
- API: return stable reason code and correlation ID.
- Workflow: preserve completed immutable artifacts and release unused budget.
- Observability: increment bounded failure metric and emit one structured warning or error.
- Test fixture: `tests/golden/failures/f011.json`.

#### F012 — Sonnet synthesis role missing

- Required behavior: Apply the role-specific criticality policy; never substitute another synthesis as if equivalent.
- UI: show a compact degraded or blocked banner with one recovery action.
- API: return stable reason code and correlation ID.
- Workflow: preserve completed immutable artifacts and release unused budget.
- Observability: increment bounded failure metric and emit one structured warning or error.
- Test fixture: `tests/golden/failures/f012.json`.

#### F013 — Final critic veto

- Required behavior: No prediction lock.
- UI: show a compact degraded or blocked banner with one recovery action.
- API: return stable reason code and correlation ID.
- Workflow: preserve completed immutable artifacts and release unused budget.
- Observability: increment bounded failure metric and emit one structured warning or error.
- Test fixture: `tests/golden/failures/f013.json`.

#### F014 — Budget exhausted

- Required behavior: Pause before external call; retain completed stages.
- UI: show a compact degraded or blocked banner with one recovery action.
- API: return stable reason code and correlation ID.
- Workflow: preserve completed immutable artifacts and release unused budget.
- Observability: increment bounded failure metric and emit one structured warning or error.
- Test fixture: `tests/golden/failures/f014.json`.

#### F015 — User cancellation

- Required behavior: Stop at safe cancellation point; release reservations.
- UI: show a compact degraded or blocked banner with one recovery action.
- API: return stable reason code and correlation ID.
- Workflow: preserve completed immutable artifacts and release unused budget.
- Observability: increment bounded failure metric and emit one structured warning or error.
- Test fixture: `tests/golden/failures/f015.json`.

#### F016 — Temporal restart

- Required behavior: Workflow resumes from persisted deterministic history.
- UI: show a compact degraded or blocked banner with one recovery action.
- API: return stable reason code and correlation ID.
- Workflow: preserve completed immutable artifacts and release unused budget.
- Observability: increment bounded failure metric and emit one structured warning or error.
- Test fixture: `tests/golden/failures/f016.json`.

#### F017 — Database transient error

- Required behavior: Bounded retry; no duplicate artifacts.
- UI: show a compact degraded or blocked banner with one recovery action.
- API: return stable reason code and correlation ID.
- Workflow: preserve completed immutable artifacts and release unused budget.
- Observability: increment bounded failure metric and emit one structured warning or error.
- Test fixture: `tests/golden/failures/f017.json`.

#### F018 — Object storage failure

- Required behavior: Do not mark snapshot or lock complete.
- UI: show a compact degraded or blocked banner with one recovery action.
- API: return stable reason code and correlation ID.
- Workflow: preserve completed immutable artifacts and release unused budget.
- Observability: increment bounded failure metric and emit one structured warning or error.
- Test fixture: `tests/golden/failures/f018.json`.

#### F019 — SSE disconnect

- Required behavior: Client reconnects from last event ID.
- UI: show a compact degraded or blocked banner with one recovery action.
- API: return stable reason code and correlation ID.
- Workflow: preserve completed immutable artifacts and release unused budget.
- Observability: increment bounded failure metric and emit one structured warning or error.
- Test fixture: `tests/golden/failures/f019.json`.

#### F020 — Kickoff moved earlier

- Required behavior: Re-run preflight; block lock if time condition fails.
- UI: show a compact degraded or blocked banner with one recovery action.
- API: return stable reason code and correlation ID.
- Workflow: preserve completed immutable artifacts and release unused budget.
- Observability: increment bounded failure metric and emit one structured warning or error.
- Test fixture: `tests/golden/failures/f020.json`.

#### F021 — Kickoff passed before lock

- Required behavior: Run may be retained as analysis but never labeled pre-match locked forecast.
- UI: show a compact degraded or blocked banner with one recovery action.
- API: return stable reason code and correlation ID.
- Workflow: preserve completed immutable artifacts and release unused budget.
- Observability: increment bounded failure metric and emit one structured warning or error.
- Test fixture: `tests/golden/failures/f021.json`.

#### F022 — Result providers disagree

- Required behavior: Keep result unresolved until policy resolves.
- UI: show a compact degraded or blocked banner with one recovery action.
- API: return stable reason code and correlation ID.
- Workflow: preserve completed immutable artifacts and release unused budget.
- Observability: increment bounded failure metric and emit one structured warning or error.
- Test fixture: `tests/golden/failures/f022.json`.

#### F023 — Post-match data incomplete

- Required behavior: Produce degraded autopsy with explicit missing fields.
- UI: show a compact degraded or blocked banner with one recovery action.
- API: return stable reason code and correlation ID.
- Workflow: preserve completed immutable artifacts and release unused budget.
- Observability: increment bounded failure metric and emit one structured warning or error.
- Test fixture: `tests/golden/failures/f023.json`.

#### F024 — Embedding service unavailable

- Required behavior: Use lexical/entity retrieval or pause according to agent policy.
- UI: show a compact degraded or blocked banner with one recovery action.
- API: return stable reason code and correlation ID.
- Workflow: preserve completed immutable artifacts and release unused budget.
- Observability: increment bounded failure metric and emit one structured warning or error.
- Test fixture: `tests/golden/failures/f024.json`.

#### F025 — Prompt injection in source

- Required behavior: Treat as quoted data, flag, and deny tool/policy changes.
- UI: show a compact degraded or blocked banner with one recovery action.
- API: return stable reason code and correlation ID.
- Workflow: preserve completed immutable artifacts and release unused budget.
- Observability: increment bounded failure metric and emit one structured warning or error.
- Test fixture: `tests/golden/failures/f025.json`.

## 27. Test Strategy

### 27.1 Test pyramid

| Layer | Target | Examples |
| --- | --- | --- |
| Pure unit | Most domain policies | time windows, fair probabilities, transitions, scoring |
| Property | Invariants over generated inputs | probability sums, idempotency, time ordering |
| Contract | Every provider and API schema | golden payload parsing, error mapping |
| Integration | Database, Temporal, object store | retries, outbox, locks, migrations |
| Golden run | Full deterministic pipeline | frozen artifacts and expected forecast |
| Browser E2E | Critical user journeys | scan, search, run, cancel, lock, autopsy |
| Visual | Compact UI states | mobile, desktop, degraded, dark/light if supported |
| Backtest | Leakage and calibration | walk-forward folds and sentinels |
| Load | Bounded personal workload | three-day scan and concurrent stage fan-out |
| Security | Trust boundaries | SSRF, prompt injection, authz, secrets |

### 27.2 Detailed required tests

#### T-0001 — Istanbul three-day boundaries

- Arrange: use a deterministic fixture explicitly targeting Istanbul three-day boundaries.
- Act: invoke the smallest public domain/application interface that exercises the rule.
- Assert: validate the typed result and stable reason codes.
- Assert: validate database side effects and absence of forbidden duplicate rows.
- Assert: validate emitted audit event and correlation ID.
- Assert: validate external calls against the mock transcript.
- Assert: run twice with the same idempotency key where applicable.
- Evidence: retain failure output as CI artifact, but redact secrets and payload bodies.

#### T-0002 — UTC conversion

- Arrange: use a deterministic fixture explicitly targeting UTC conversion.
- Act: invoke the smallest public domain/application interface that exercises the rule.
- Assert: validate the typed result and stable reason codes.
- Assert: validate database side effects and absence of forbidden duplicate rows.
- Assert: validate emitted audit event and correlation ID.
- Assert: validate external calls against the mock transcript.
- Assert: run twice with the same idempotency key where applicable.
- Evidence: retain failure output as CI artifact, but redact secrets and payload bodies.

#### T-0003 — exclusive end boundary

- Arrange: use a deterministic fixture explicitly targeting exclusive end boundary.
- Act: invoke the smallest public domain/application interface that exercises the rule.
- Assert: validate the typed result and stable reason codes.
- Assert: validate database side effects and absence of forbidden duplicate rows.
- Assert: validate emitted audit event and correlation ID.
- Assert: validate external calls against the mock transcript.
- Assert: run twice with the same idempotency key where applicable.
- Evidence: retain failure output as CI artifact, but redact secrets and payload bodies.

#### T-0004 — postponed fixture grouping

- Arrange: use a deterministic fixture explicitly targeting postponed fixture grouping.
- Act: invoke the smallest public domain/application interface that exercises the rule.
- Assert: validate the typed result and stable reason codes.
- Assert: validate database side effects and absence of forbidden duplicate rows.
- Assert: validate emitted audit event and correlation ID.
- Assert: validate external calls against the mock transcript.
- Assert: run twice with the same idempotency key where applicable.
- Evidence: retain failure output as CI artifact, but redact secrets and payload bodies.

#### T-0005 — canonical team alias resolution

- Arrange: use a deterministic fixture explicitly targeting canonical team alias resolution.
- Act: invoke the smallest public domain/application interface that exercises the rule.
- Assert: validate the typed result and stable reason codes.
- Assert: validate database side effects and absence of forbidden duplicate rows.
- Assert: validate emitted audit event and correlation ID.
- Assert: validate external calls against the mock transcript.
- Assert: run twice with the same idempotency key where applicable.
- Evidence: retain failure output as CI artifact, but redact secrets and payload bodies.

#### T-0006 — fixture ambiguity quarantine

- Arrange: use a deterministic fixture explicitly targeting fixture ambiguity quarantine.
- Act: invoke the smallest public domain/application interface that exercises the rule.
- Assert: validate the typed result and stable reason codes.
- Assert: validate database side effects and absence of forbidden duplicate rows.
- Assert: validate emitted audit event and correlation ID.
- Assert: validate external calls against the mock transcript.
- Assert: run twice with the same idempotency key where applicable.
- Evidence: retain failure output as CI artifact, but redact secrets and payload bodies.

#### T-0007 — duplicate provider merge

- Arrange: use a deterministic fixture explicitly targeting duplicate provider merge.
- Act: invoke the smallest public domain/application interface that exercises the rule.
- Assert: validate the typed result and stable reason codes.
- Assert: validate database side effects and absence of forbidden duplicate rows.
- Assert: validate emitted audit event and correlation ID.
- Assert: validate external calls against the mock transcript.
- Assert: run twice with the same idempotency key where applicable.
- Evidence: retain failure output as CI artifact, but redact secrets and payload bodies.

#### T-0008 — manual search debounce

- Arrange: use a deterministic fixture explicitly targeting manual search debounce.
- Act: invoke the smallest public domain/application interface that exercises the rule.
- Assert: validate the typed result and stable reason codes.
- Assert: validate database side effects and absence of forbidden duplicate rows.
- Assert: validate emitted audit event and correlation ID.
- Assert: validate external calls against the mock transcript.
- Assert: run twice with the same idempotency key where applicable.
- Evidence: retain failure output as CI artifact, but redact secrets and payload bodies.

#### T-0009 — manual search cancellation

- Arrange: use a deterministic fixture explicitly targeting manual search cancellation.
- Act: invoke the smallest public domain/application interface that exercises the rule.
- Assert: validate the typed result and stable reason codes.
- Assert: validate database side effects and absence of forbidden duplicate rows.
- Assert: validate emitted audit event and correlation ID.
- Assert: validate external calls against the mock transcript.
- Assert: run twice with the same idempotency key where applicable.
- Evidence: retain failure output as CI artifact, but redact secrets and payload bodies.

#### T-0010 — scan idempotency

- Arrange: use a deterministic fixture explicitly targeting scan idempotency.
- Act: invoke the smallest public domain/application interface that exercises the rule.
- Assert: validate the typed result and stable reason codes.
- Assert: validate database side effects and absence of forbidden duplicate rows.
- Assert: validate emitted audit event and correlation ID.
- Assert: validate external calls against the mock transcript.
- Assert: run twice with the same idempotency key where applicable.
- Evidence: retain failure output as CI artifact, but redact secrets and payload bodies.

#### T-0011 — analysis idempotency

- Arrange: use a deterministic fixture explicitly targeting analysis idempotency.
- Act: invoke the smallest public domain/application interface that exercises the rule.
- Assert: validate the typed result and stable reason codes.
- Assert: validate database side effects and absence of forbidden duplicate rows.
- Assert: validate emitted audit event and correlation ID.
- Assert: validate external calls against the mock transcript.
- Assert: run twice with the same idempotency key where applicable.
- Evidence: retain failure output as CI artifact, but redact secrets and payload bodies.

#### T-0012 — workflow state legality

- Arrange: use a deterministic fixture explicitly targeting workflow state legality.
- Act: invoke the smallest public domain/application interface that exercises the rule.
- Assert: validate the typed result and stable reason codes.
- Assert: validate database side effects and absence of forbidden duplicate rows.
- Assert: validate emitted audit event and correlation ID.
- Assert: validate external calls against the mock transcript.
- Assert: run twice with the same idempotency key where applicable.
- Evidence: retain failure output as CI artifact, but redact secrets and payload bodies.

#### T-0013 — workflow cancellation

- Arrange: use a deterministic fixture explicitly targeting workflow cancellation.
- Act: invoke the smallest public domain/application interface that exercises the rule.
- Assert: validate the typed result and stable reason codes.
- Assert: validate database side effects and absence of forbidden duplicate rows.
- Assert: validate emitted audit event and correlation ID.
- Assert: validate external calls against the mock transcript.
- Assert: run twice with the same idempotency key where applicable.
- Evidence: retain failure output as CI artifact, but redact secrets and payload bodies.

#### T-0014 — budget reservation

- Arrange: use a deterministic fixture explicitly targeting budget reservation.
- Act: invoke the smallest public domain/application interface that exercises the rule.
- Assert: validate the typed result and stable reason codes.
- Assert: validate database side effects and absence of forbidden duplicate rows.
- Assert: validate emitted audit event and correlation ID.
- Assert: validate external calls against the mock transcript.
- Assert: run twice with the same idempotency key where applicable.
- Evidence: retain failure output as CI artifact, but redact secrets and payload bodies.

#### T-0015 — budget reconciliation

- Arrange: use a deterministic fixture explicitly targeting budget reconciliation.
- Act: invoke the smallest public domain/application interface that exercises the rule.
- Assert: validate the typed result and stable reason codes.
- Assert: validate database side effects and absence of forbidden duplicate rows.
- Assert: validate emitted audit event and correlation ID.
- Assert: validate external calls against the mock transcript.
- Assert: run twice with the same idempotency key where applicable.
- Evidence: retain failure output as CI artifact, but redact secrets and payload bodies.

#### T-0016 — provider quota parsing

- Arrange: use a deterministic fixture explicitly targeting provider quota parsing.
- Act: invoke the smallest public domain/application interface that exercises the rule.
- Assert: validate the typed result and stable reason codes.
- Assert: validate database side effects and absence of forbidden duplicate rows.
- Assert: validate emitted audit event and correlation ID.
- Assert: validate external calls against the mock transcript.
- Assert: run twice with the same idempotency key where applicable.
- Evidence: retain failure output as CI artifact, but redact secrets and payload bodies.

#### T-0017 — provider 429 backoff

- Arrange: use a deterministic fixture explicitly targeting provider 429 backoff.
- Act: invoke the smallest public domain/application interface that exercises the rule.
- Assert: validate the typed result and stable reason codes.
- Assert: validate database side effects and absence of forbidden duplicate rows.
- Assert: validate emitted audit event and correlation ID.
- Assert: validate external calls against the mock transcript.
- Assert: run twice with the same idempotency key where applicable.
- Evidence: retain failure output as CI artifact, but redact secrets and payload bodies.

#### T-0018 — provider circuit breaker

- Arrange: use a deterministic fixture explicitly targeting provider circuit breaker.
- Act: invoke the smallest public domain/application interface that exercises the rule.
- Assert: validate the typed result and stable reason codes.
- Assert: validate database side effects and absence of forbidden duplicate rows.
- Assert: validate emitted audit event and correlation ID.
- Assert: validate external calls against the mock transcript.
- Assert: run twice with the same idempotency key where applicable.
- Evidence: retain failure output as CI artifact, but redact secrets and payload bodies.

#### T-0019 — source content hashing

- Arrange: use a deterministic fixture explicitly targeting source content hashing.
- Act: invoke the smallest public domain/application interface that exercises the rule.
- Assert: validate the typed result and stable reason codes.
- Assert: validate database side effects and absence of forbidden duplicate rows.
- Assert: validate emitted audit event and correlation ID.
- Assert: validate external calls against the mock transcript.
- Assert: run twice with the same idempotency key where applicable.
- Evidence: retain failure output as CI artifact, but redact secrets and payload bodies.

#### T-0020 — source timestamp ordering

- Arrange: use a deterministic fixture explicitly targeting source timestamp ordering.
- Act: invoke the smallest public domain/application interface that exercises the rule.
- Assert: validate the typed result and stable reason codes.
- Assert: validate database side effects and absence of forbidden duplicate rows.
- Assert: validate emitted audit event and correlation ID.
- Assert: validate external calls against the mock transcript.
- Assert: run twice with the same idempotency key where applicable.
- Evidence: retain failure output as CI artifact, but redact secrets and payload bodies.

#### T-0021 — raw source claim interpretation separation

- Arrange: use a deterministic fixture explicitly targeting raw source claim interpretation separation.
- Act: invoke the smallest public domain/application interface that exercises the rule.
- Assert: validate the typed result and stable reason codes.
- Assert: validate database side effects and absence of forbidden duplicate rows.
- Assert: validate emitted audit event and correlation ID.
- Assert: validate external calls against the mock transcript.
- Assert: run twice with the same idempotency key where applicable.
- Evidence: retain failure output as CI artifact, but redact secrets and payload bodies.

#### T-0022 — syndication independence

- Arrange: use a deterministic fixture explicitly targeting syndication independence.
- Act: invoke the smallest public domain/application interface that exercises the rule.
- Assert: validate the typed result and stable reason codes.
- Assert: validate database side effects and absence of forbidden duplicate rows.
- Assert: validate emitted audit event and correlation ID.
- Assert: validate external calls against the mock transcript.
- Assert: run twice with the same idempotency key where applicable.
- Evidence: retain failure output as CI artifact, but redact secrets and payload bodies.

#### T-0023 — claim atomicity

- Arrange: use a deterministic fixture explicitly targeting claim atomicity.
- Act: invoke the smallest public domain/application interface that exercises the rule.
- Assert: validate the typed result and stable reason codes.
- Assert: validate database side effects and absence of forbidden duplicate rows.
- Assert: validate emitted audit event and correlation ID.
- Assert: validate external calls against the mock transcript.
- Assert: run twice with the same idempotency key where applicable.
- Evidence: retain failure output as CI artifact, but redact secrets and payload bodies.

#### T-0024 — claim unit normalization

- Arrange: use a deterministic fixture explicitly targeting claim unit normalization.
- Act: invoke the smallest public domain/application interface that exercises the rule.
- Assert: validate the typed result and stable reason codes.
- Assert: validate database side effects and absence of forbidden duplicate rows.
- Assert: validate emitted audit event and correlation ID.
- Assert: validate external calls against the mock transcript.
- Assert: run twice with the same idempotency key where applicable.
- Evidence: retain failure output as CI artifact, but redact secrets and payload bodies.

#### T-0025 — contradiction grouping

- Arrange: use a deterministic fixture explicitly targeting contradiction grouping.
- Act: invoke the smallest public domain/application interface that exercises the rule.
- Assert: validate the typed result and stable reason codes.
- Assert: validate database side effects and absence of forbidden duplicate rows.
- Assert: validate emitted audit event and correlation ID.
- Assert: validate external calls against the mock transcript.
- Assert: run twice with the same idempotency key where applicable.
- Evidence: retain failure output as CI artifact, but redact secrets and payload bodies.

#### T-0026 — freshness TTL

- Arrange: use a deterministic fixture explicitly targeting freshness TTL.
- Act: invoke the smallest public domain/application interface that exercises the rule.
- Assert: validate the typed result and stable reason codes.
- Assert: validate database side effects and absence of forbidden duplicate rows.
- Assert: validate emitted audit event and correlation ID.
- Assert: validate external calls against the mock transcript.
- Assert: run twice with the same idempotency key where applicable.
- Evidence: retain failure output as CI artifact, but redact secrets and payload bodies.

#### T-0027 — cutoff exclusion

- Arrange: use a deterministic fixture explicitly targeting cutoff exclusion.
- Act: invoke the smallest public domain/application interface that exercises the rule.
- Assert: validate the typed result and stable reason codes.
- Assert: validate database side effects and absence of forbidden duplicate rows.
- Assert: validate emitted audit event and correlation ID.
- Assert: validate external calls against the mock transcript.
- Assert: run twice with the same idempotency key where applicable.
- Evidence: retain failure output as CI artifact, but redact secrets and payload bodies.

#### T-0028 — statistics sample shrinkage

- Arrange: use a deterministic fixture explicitly targeting statistics sample shrinkage.
- Act: invoke the smallest public domain/application interface that exercises the rule.
- Assert: validate the typed result and stable reason codes.
- Assert: validate database side effects and absence of forbidden duplicate rows.
- Assert: validate emitted audit event and correlation ID.
- Assert: validate external calls against the mock transcript.
- Assert: run twice with the same idempotency key where applicable.
- Evidence: retain failure output as CI artifact, but redact secrets and payload bodies.

#### T-0029 — opponent adjustment

- Arrange: use a deterministic fixture explicitly targeting opponent adjustment.
- Act: invoke the smallest public domain/application interface that exercises the rule.
- Assert: validate the typed result and stable reason codes.
- Assert: validate database side effects and absence of forbidden duplicate rows.
- Assert: validate emitted audit event and correlation ID.
- Assert: validate external calls against the mock transcript.
- Assert: run twice with the same idempotency key where applicable.
- Evidence: retain failure output as CI artifact, but redact secrets and payload bodies.

#### T-0030 — form regression

- Arrange: use a deterministic fixture explicitly targeting form regression.
- Act: invoke the smallest public domain/application interface that exercises the rule.
- Assert: validate the typed result and stable reason codes.
- Assert: validate database side effects and absence of forbidden duplicate rows.
- Assert: validate emitted audit event and correlation ID.
- Assert: validate external calls against the mock transcript.
- Assert: run twice with the same idempotency key where applicable.
- Evidence: retain failure output as CI artifact, but redact secrets and payload bodies.

#### T-0031 — fatigue travel distance

- Arrange: use a deterministic fixture explicitly targeting fatigue travel distance.
- Act: invoke the smallest public domain/application interface that exercises the rule.
- Assert: validate the typed result and stable reason codes.
- Assert: validate database side effects and absence of forbidden duplicate rows.
- Assert: validate emitted audit event and correlation ID.
- Assert: validate external calls against the mock transcript.
- Assert: run twice with the same idempotency key where applicable.
- Evidence: retain failure output as CI artifact, but redact secrets and payload bodies.

#### T-0032 — goalkeeper starter uncertainty

- Arrange: use a deterministic fixture explicitly targeting goalkeeper starter uncertainty.
- Act: invoke the smallest public domain/application interface that exercises the rule.
- Assert: validate the typed result and stable reason codes.
- Assert: validate database side effects and absence of forbidden duplicate rows.
- Assert: validate emitted audit event and correlation ID.
- Assert: validate external calls against the mock transcript.
- Assert: run twice with the same idempotency key where applicable.
- Evidence: retain failure output as CI artifact, but redact secrets and payload bodies.

#### T-0033 — set-piece penalty exclusion

- Arrange: use a deterministic fixture explicitly targeting set-piece penalty exclusion.
- Act: invoke the smallest public domain/application interface that exercises the rule.
- Assert: validate the typed result and stable reason codes.
- Assert: validate database side effects and absence of forbidden duplicate rows.
- Assert: validate emitted audit event and correlation ID.
- Assert: validate external calls against the mock transcript.
- Assert: run twice with the same idempotency key where applicable.
- Evidence: retain failure output as CI artifact, but redact secrets and payload bodies.

#### T-0034 — weather units

- Arrange: use a deterministic fixture explicitly targeting weather units.
- Act: invoke the smallest public domain/application interface that exercises the rule.
- Assert: validate the typed result and stable reason codes.
- Assert: validate database side effects and absence of forbidden duplicate rows.
- Assert: validate emitted audit event and correlation ID.
- Assert: validate external calls against the mock transcript.
- Assert: run twice with the same idempotency key where applicable.
- Evidence: retain failure output as CI artifact, but redact secrets and payload bodies.

#### T-0035 — odds market isolation

- Arrange: use a deterministic fixture explicitly targeting odds market isolation.
- Act: invoke the smallest public domain/application interface that exercises the rule.
- Assert: validate the typed result and stable reason codes.
- Assert: validate database side effects and absence of forbidden duplicate rows.
- Assert: validate emitted audit event and correlation ID.
- Assert: validate external calls against the mock transcript.
- Assert: run twice with the same idempotency key where applicable.
- Evidence: retain failure output as CI artifact, but redact secrets and payload bodies.

#### T-0036 — market movement unexplained state

- Arrange: use a deterministic fixture explicitly targeting market movement unexplained state.
- Act: invoke the smallest public domain/application interface that exercises the rule.
- Assert: validate the typed result and stable reason codes.
- Assert: validate database side effects and absence of forbidden duplicate rows.
- Assert: validate emitted audit event and correlation ID.
- Assert: validate external calls against the mock transcript.
- Assert: run twice with the same idempotency key where applicable.
- Evidence: retain failure output as CI artifact, but redact secrets and payload bodies.

#### T-0037 — odds market mapping

- Arrange: use a deterministic fixture explicitly targeting odds market mapping.
- Act: invoke the smallest public domain/application interface that exercises the rule.
- Assert: validate the typed result and stable reason codes.
- Assert: validate database side effects and absence of forbidden duplicate rows.
- Assert: validate emitted audit event and correlation ID.
- Assert: validate external calls against the mock transcript.
- Assert: run twice with the same idempotency key where applicable.
- Evidence: retain failure output as CI artifact, but redact secrets and payload bodies.

#### T-0038 — odds deduplication

- Arrange: use a deterministic fixture explicitly targeting odds deduplication.
- Act: invoke the smallest public domain/application interface that exercises the rule.
- Assert: validate the typed result and stable reason codes.
- Assert: validate database side effects and absence of forbidden duplicate rows.
- Assert: validate emitted audit event and correlation ID.
- Assert: validate external calls against the mock transcript.
- Assert: run twice with the same idempotency key where applicable.
- Evidence: retain failure output as CI artifact, but redact secrets and payload bodies.

#### T-0039 — overround removal

- Arrange: use a deterministic fixture explicitly targeting overround removal.
- Act: invoke the smallest public domain/application interface that exercises the rule.
- Assert: validate the typed result and stable reason codes.
- Assert: validate database side effects and absence of forbidden duplicate rows.
- Assert: validate emitted audit event and correlation ID.
- Assert: validate external calls against the mock transcript.
- Assert: run twice with the same idempotency key where applicable.
- Evidence: retain failure output as CI artifact, but redact secrets and payload bodies.

#### T-0040 — probability sum

- Arrange: use a deterministic fixture explicitly targeting probability sum.
- Act: invoke the smallest public domain/application interface that exercises the rule.
- Assert: validate the typed result and stable reason codes.
- Assert: validate database side effects and absence of forbidden duplicate rows.
- Assert: validate emitted audit event and correlation ID.
- Assert: validate external calls against the mock transcript.
- Assert: run twice with the same idempotency key where applicable.
- Evidence: retain failure output as CI artifact, but redact secrets and payload bodies.

#### T-0041 — calibration domain

- Arrange: use a deterministic fixture explicitly targeting calibration domain.
- Act: invoke the smallest public domain/application interface that exercises the rule.
- Assert: validate the typed result and stable reason codes.
- Assert: validate database side effects and absence of forbidden duplicate rows.
- Assert: validate emitted audit event and correlation ID.
- Assert: validate external calls against the mock transcript.
- Assert: run twice with the same idempotency key where applicable.
- Evidence: retain failure output as CI artifact, but redact secrets and payload bodies.

#### T-0042 — historical similarity leakage

- Arrange: use a deterministic fixture explicitly targeting historical similarity leakage.
- Act: invoke the smallest public domain/application interface that exercises the rule.
- Assert: validate the typed result and stable reason codes.
- Assert: validate database side effects and absence of forbidden duplicate rows.
- Assert: validate emitted audit event and correlation ID.
- Assert: validate external calls against the mock transcript.
- Assert: run twice with the same idempotency key where applicable.
- Evidence: retain failure output as CI artifact, but redact secrets and payload bodies.

#### T-0043 — critic independence

- Arrange: use a deterministic fixture explicitly targeting critic independence.
- Act: invoke the smallest public domain/application interface that exercises the rule.
- Assert: validate the typed result and stable reason codes.
- Assert: validate database side effects and absence of forbidden duplicate rows.
- Assert: validate emitted audit event and correlation ID.
- Assert: validate external calls against the mock transcript.
- Assert: run twice with the same idempotency key where applicable.
- Evidence: retain failure output as CI artifact, but redact secrets and payload bodies.

#### T-0044 — pre-Chief prediction prohibition

- Arrange: use a deterministic fixture explicitly targeting pre-Chief prediction prohibition.
- Act: invoke the smallest public domain/application interface that exercises the rule.
- Assert: validate the typed result and stable reason codes.
- Assert: validate database side effects and absence of forbidden duplicate rows.
- Assert: validate emitted audit event and correlation ID.
- Assert: validate external calls against the mock transcript.
- Assert: run twice with the same idempotency key where applicable.
- Evidence: retain failure output as CI artifact, but redact secrets and payload bodies.

#### T-0045 — three outcome steelman independence

- Arrange: use a deterministic fixture explicitly targeting three outcome steelman independence.
- Act: invoke the smallest public domain/application interface that exercises the rule.
- Assert: validate the typed result and stable reason codes.
- Assert: validate database side effects and absence of forbidden duplicate rows.
- Assert: validate emitted audit event and correlation ID.
- Assert: validate external calls against the mock transcript.
- Assert: run twice with the same idempotency key where applicable.
- Evidence: retain failure output as CI artifact, but redact secrets and payload bodies.

#### T-0046 — scenario exclusivity

- Arrange: use a deterministic fixture explicitly targeting scenario exclusivity.
- Act: invoke the smallest public domain/application interface that exercises the rule.
- Assert: validate the typed result and stable reason codes.
- Assert: validate database side effects and absence of forbidden duplicate rows.
- Assert: validate emitted audit event and correlation ID.
- Assert: validate external calls against the mock transcript.
- Assert: run twice with the same idempotency key where applicable.
- Evidence: retain failure output as CI artifact, but redact secrets and payload bodies.

#### T-0047 — red-team equal attack

- Arrange: use a deterministic fixture explicitly targeting red-team equal attack.
- Act: invoke the smallest public domain/application interface that exercises the rule.
- Assert: validate the typed result and stable reason codes.
- Assert: validate database side effects and absence of forbidden duplicate rows.
- Assert: validate emitted audit event and correlation ID.
- Assert: validate external calls against the mock transcript.
- Assert: run twice with the same idempotency key where applicable.
- Evidence: retain failure output as CI artifact, but redact secrets and payload bodies.

#### T-0048 — chief first probability authorization

- Arrange: use a deterministic fixture explicitly targeting chief first probability authorization.
- Act: invoke the smallest public domain/application interface that exercises the rule.
- Assert: validate the typed result and stable reason codes.
- Assert: validate database side effects and absence of forbidden duplicate rows.
- Assert: validate emitted audit event and correlation ID.
- Assert: validate external calls against the mock transcript.
- Assert: run twice with the same idempotency key where applicable.
- Evidence: retain failure output as CI artifact, but redact secrets and payload bodies.

#### T-0049 — final critic no mutation

- Arrange: use a deterministic fixture explicitly targeting final critic no mutation.
- Act: invoke the smallest public domain/application interface that exercises the rule.
- Assert: validate the typed result and stable reason codes.
- Assert: validate database side effects and absence of forbidden duplicate rows.
- Assert: validate emitted audit event and correlation ID.
- Assert: validate external calls against the mock transcript.
- Assert: run twice with the same idempotency key where applicable.
- Evidence: retain failure output as CI artifact, but redact secrets and payload bodies.

#### T-0050 — chief no-publish

- Arrange: use a deterministic fixture explicitly targeting chief no-publish.
- Act: invoke the smallest public domain/application interface that exercises the rule.
- Assert: validate the typed result and stable reason codes.
- Assert: validate database side effects and absence of forbidden duplicate rows.
- Assert: validate emitted audit event and correlation ID.
- Assert: validate external calls against the mock transcript.
- Assert: run twice with the same idempotency key where applicable.
- Evidence: retain failure output as CI artifact, but redact secrets and payload bodies.

#### T-0051 — single revision bound

- Arrange: use a deterministic fixture explicitly targeting single revision bound.
- Act: invoke the smallest public domain/application interface that exercises the rule.
- Assert: validate the typed result and stable reason codes.
- Assert: validate database side effects and absence of forbidden duplicate rows.
- Assert: validate emitted audit event and correlation ID.
- Assert: validate external calls against the mock transcript.
- Assert: run twice with the same idempotency key where applicable.
- Evidence: retain failure output as CI artifact, but redact secrets and payload bodies.

#### T-0052 — prediction lock timing

- Arrange: use a deterministic fixture explicitly targeting prediction lock timing.
- Act: invoke the smallest public domain/application interface that exercises the rule.
- Assert: validate the typed result and stable reason codes.
- Assert: validate database side effects and absence of forbidden duplicate rows.
- Assert: validate emitted audit event and correlation ID.
- Assert: validate external calls against the mock transcript.
- Assert: run twice with the same idempotency key where applicable.
- Evidence: retain failure output as CI artifact, but redact secrets and payload bodies.

#### T-0053 — prediction lock immutability

- Arrange: use a deterministic fixture explicitly targeting prediction lock immutability.
- Act: invoke the smallest public domain/application interface that exercises the rule.
- Assert: validate the typed result and stable reason codes.
- Assert: validate database side effects and absence of forbidden duplicate rows.
- Assert: validate emitted audit event and correlation ID.
- Assert: validate external calls against the mock transcript.
- Assert: run twice with the same idempotency key where applicable.
- Evidence: retain failure output as CI artifact, but redact secrets and payload bodies.

#### T-0054 — live market namespace isolation

- Arrange: use a deterministic fixture explicitly targeting live market namespace isolation.
- Act: invoke the smallest public domain/application interface that exercises the rule.
- Assert: validate the typed result and stable reason codes.
- Assert: validate database side effects and absence of forbidden duplicate rows.
- Assert: validate emitted audit event and correlation ID.
- Assert: validate external calls against the mock transcript.
- Assert: run twice with the same idempotency key where applicable.
- Evidence: retain failure output as CI artifact, but redact secrets and payload bodies.

#### T-0055 — manifest hash

- Arrange: use a deterministic fixture explicitly targeting manifest hash.
- Act: invoke the smallest public domain/application interface that exercises the rule.
- Assert: validate the typed result and stable reason codes.
- Assert: validate database side effects and absence of forbidden duplicate rows.
- Assert: validate emitted audit event and correlation ID.
- Assert: validate external calls against the mock transcript.
- Assert: run twice with the same idempotency key where applicable.
- Evidence: retain failure output as CI artifact, but redact secrets and payload bodies.

#### T-0056 — result final status

- Arrange: use a deterministic fixture explicitly targeting result final status.
- Act: invoke the smallest public domain/application interface that exercises the rule.
- Assert: validate the typed result and stable reason codes.
- Assert: validate database side effects and absence of forbidden duplicate rows.
- Assert: validate emitted audit event and correlation ID.
- Assert: validate external calls against the mock transcript.
- Assert: run twice with the same idempotency key where applicable.
- Evidence: retain failure output as CI artifact, but redact secrets and payload bodies.

#### T-0057 — extra-time semantics

- Arrange: use a deterministic fixture explicitly targeting extra-time semantics.
- Act: invoke the smallest public domain/application interface that exercises the rule.
- Assert: validate the typed result and stable reason codes.
- Assert: validate database side effects and absence of forbidden duplicate rows.
- Assert: validate emitted audit event and correlation ID.
- Assert: validate external calls against the mock transcript.
- Assert: run twice with the same idempotency key where applicable.
- Evidence: retain failure output as CI artifact, but redact secrets and payload bodies.

#### T-0058 — autopsy pre/post separation

- Arrange: use a deterministic fixture explicitly targeting autopsy pre/post separation.
- Act: invoke the smallest public domain/application interface that exercises the rule.
- Assert: validate the typed result and stable reason codes.
- Assert: validate database side effects and absence of forbidden duplicate rows.
- Assert: validate emitted audit event and correlation ID.
- Assert: validate external calls against the mock transcript.
- Assert: run twice with the same idempotency key where applicable.
- Evidence: retain failure output as CI artifact, but redact secrets and payload bodies.

#### T-0059 — result process separation

- Arrange: use a deterministic fixture explicitly targeting result process separation.
- Act: invoke the smallest public domain/application interface that exercises the rule.
- Assert: validate the typed result and stable reason codes.
- Assert: validate database side effects and absence of forbidden duplicate rows.
- Assert: validate emitted audit event and correlation ID.
- Assert: validate external calls against the mock transcript.
- Assert: run twice with the same idempotency key where applicable.
- Evidence: retain failure output as CI artifact, but redact secrets and payload bodies.

#### T-0060 — variance unknown remainder

- Arrange: use a deterministic fixture explicitly targeting variance unknown remainder.
- Act: invoke the smallest public domain/application interface that exercises the rule.
- Assert: validate the typed result and stable reason codes.
- Assert: validate database side effects and absence of forbidden duplicate rows.
- Assert: validate emitted audit event and correlation ID.
- Assert: validate external calls against the mock transcript.
- Assert: run twice with the same idempotency key where applicable.
- Evidence: retain failure output as CI artifact, but redact secrets and payload bodies.

#### T-0061 — thesis reliability shrinkage

- Arrange: use a deterministic fixture explicitly targeting thesis reliability shrinkage.
- Act: invoke the smallest public domain/application interface that exercises the rule.
- Assert: validate the typed result and stable reason codes.
- Assert: validate database side effects and absence of forbidden duplicate rows.
- Assert: validate emitted audit event and correlation ID.
- Assert: validate external calls against the mock transcript.
- Assert: run twice with the same idempotency key where applicable.
- Evidence: retain failure output as CI artifact, but redact secrets and payload bodies.

#### T-0062 — agent source reliability versioning

- Arrange: use a deterministic fixture explicitly targeting agent source reliability versioning.
- Act: invoke the smallest public domain/application interface that exercises the rule.
- Assert: validate the typed result and stable reason codes.
- Assert: validate database side effects and absence of forbidden duplicate rows.
- Assert: validate emitted audit event and correlation ID.
- Assert: validate external calls against the mock transcript.
- Assert: run twice with the same idempotency key where applicable.
- Evidence: retain failure output as CI artifact, but redact secrets and payload bodies.

#### T-0063 — lesson hindsight rejection

- Arrange: use a deterministic fixture explicitly targeting lesson hindsight rejection.
- Act: invoke the smallest public domain/application interface that exercises the rule.
- Assert: validate the typed result and stable reason codes.
- Assert: validate database side effects and absence of forbidden duplicate rows.
- Assert: validate emitted audit event and correlation ID.
- Assert: validate external calls against the mock transcript.
- Assert: run twice with the same idempotency key where applicable.
- Evidence: retain failure output as CI artifact, but redact secrets and payload bodies.

#### T-0064 — case memory scope

- Arrange: use a deterministic fixture explicitly targeting case memory scope.
- Act: invoke the smallest public domain/application interface that exercises the rule.
- Assert: validate the typed result and stable reason codes.
- Assert: validate database side effects and absence of forbidden duplicate rows.
- Assert: validate emitted audit event and correlation ID.
- Assert: validate external calls against the mock transcript.
- Assert: run twice with the same idempotency key where applicable.
- Evidence: retain failure output as CI artifact, but redact secrets and payload bodies.

#### T-0065 — RAG cutoff filter

- Arrange: use a deterministic fixture explicitly targeting RAG cutoff filter.
- Act: invoke the smallest public domain/application interface that exercises the rule.
- Assert: validate the typed result and stable reason codes.
- Assert: validate database side effects and absence of forbidden duplicate rows.
- Assert: validate emitted audit event and correlation ID.
- Assert: validate external calls against the mock transcript.
- Assert: run twice with the same idempotency key where applicable.
- Evidence: retain failure output as CI artifact, but redact secrets and payload bodies.

#### T-0066 — RAG source independence

- Arrange: use a deterministic fixture explicitly targeting RAG source independence.
- Act: invoke the smallest public domain/application interface that exercises the rule.
- Assert: validate the typed result and stable reason codes.
- Assert: validate database side effects and absence of forbidden duplicate rows.
- Assert: validate emitted audit event and correlation ID.
- Assert: validate external calls against the mock transcript.
- Assert: run twice with the same idempotency key where applicable.
- Evidence: retain failure output as CI artifact, but redact secrets and payload bodies.

#### T-0067 — embedding version

- Arrange: use a deterministic fixture explicitly targeting embedding version.
- Act: invoke the smallest public domain/application interface that exercises the rule.
- Assert: validate the typed result and stable reason codes.
- Assert: validate database side effects and absence of forbidden duplicate rows.
- Assert: validate emitted audit event and correlation ID.
- Assert: validate external calls against the mock transcript.
- Assert: run twice with the same idempotency key where applicable.
- Evidence: retain failure output as CI artifact, but redact secrets and payload bodies.

#### T-0068 — prompt injection isolation

- Arrange: use a deterministic fixture explicitly targeting prompt injection isolation.
- Act: invoke the smallest public domain/application interface that exercises the rule.
- Assert: validate the typed result and stable reason codes.
- Assert: validate database side effects and absence of forbidden duplicate rows.
- Assert: validate emitted audit event and correlation ID.
- Assert: validate external calls against the mock transcript.
- Assert: run twice with the same idempotency key where applicable.
- Evidence: retain failure output as CI artifact, but redact secrets and payload bodies.

#### T-0069 — model schema repair

- Arrange: use a deterministic fixture explicitly targeting model schema repair.
- Act: invoke the smallest public domain/application interface that exercises the rule.
- Assert: validate the typed result and stable reason codes.
- Assert: validate database side effects and absence of forbidden duplicate rows.
- Assert: validate emitted audit event and correlation ID.
- Assert: validate external calls against the mock transcript.
- Assert: run twice with the same idempotency key where applicable.
- Evidence: retain failure output as CI artifact, but redact secrets and payload bodies.

#### T-0070 — model refusal mapping

- Arrange: use a deterministic fixture explicitly targeting model refusal mapping.
- Act: invoke the smallest public domain/application interface that exercises the rule.
- Assert: validate the typed result and stable reason codes.
- Assert: validate database side effects and absence of forbidden duplicate rows.
- Assert: validate emitted audit event and correlation ID.
- Assert: validate external calls against the mock transcript.
- Assert: run twice with the same idempotency key where applicable.
- Evidence: retain failure output as CI artifact, but redact secrets and payload bodies.

#### T-0071 — expired model verification

- Arrange: use a deterministic fixture explicitly targeting expired model verification.
- Act: invoke the smallest public domain/application interface that exercises the rule.
- Assert: validate the typed result and stable reason codes.
- Assert: validate database side effects and absence of forbidden duplicate rows.
- Assert: validate emitted audit event and correlation ID.
- Assert: validate external calls against the mock transcript.
- Assert: run twice with the same idempotency key where applicable.
- Evidence: retain failure output as CI artifact, but redact secrets and payload bodies.

#### T-0072 — unknown model price

- Arrange: use a deterministic fixture explicitly targeting unknown model price.
- Act: invoke the smallest public domain/application interface that exercises the rule.
- Assert: validate the typed result and stable reason codes.
- Assert: validate database side effects and absence of forbidden duplicate rows.
- Assert: validate emitted audit event and correlation ID.
- Assert: validate external calls against the mock transcript.
- Assert: run twice with the same idempotency key where applicable.
- Evidence: retain failure output as CI artifact, but redact secrets and payload bodies.

#### T-0073 — secret redaction

- Arrange: use a deterministic fixture explicitly targeting secret redaction.
- Act: invoke the smallest public domain/application interface that exercises the rule.
- Assert: validate the typed result and stable reason codes.
- Assert: validate database side effects and absence of forbidden duplicate rows.
- Assert: validate emitted audit event and correlation ID.
- Assert: validate external calls against the mock transcript.
- Assert: run twice with the same idempotency key where applicable.
- Evidence: retain failure output as CI artifact, but redact secrets and payload bodies.

#### T-0074 — SSE replay

- Arrange: use a deterministic fixture explicitly targeting SSE replay.
- Act: invoke the smallest public domain/application interface that exercises the rule.
- Assert: validate the typed result and stable reason codes.
- Assert: validate database side effects and absence of forbidden duplicate rows.
- Assert: validate emitted audit event and correlation ID.
- Assert: validate external calls against the mock transcript.
- Assert: run twice with the same idempotency key where applicable.
- Evidence: retain failure output as CI artifact, but redact secrets and payload bodies.

#### T-0075 — outbox exactly-once effect

- Arrange: use a deterministic fixture explicitly targeting outbox exactly-once effect.
- Act: invoke the smallest public domain/application interface that exercises the rule.
- Assert: validate the typed result and stable reason codes.
- Assert: validate database side effects and absence of forbidden duplicate rows.
- Assert: validate emitted audit event and correlation ID.
- Assert: validate external calls against the mock transcript.
- Assert: run twice with the same idempotency key where applicable.
- Evidence: retain failure output as CI artifact, but redact secrets and payload bodies.

#### T-0076 — migration upgrade

- Arrange: use a deterministic fixture explicitly targeting migration upgrade.
- Act: invoke the smallest public domain/application interface that exercises the rule.
- Assert: validate the typed result and stable reason codes.
- Assert: validate database side effects and absence of forbidden duplicate rows.
- Assert: validate emitted audit event and correlation ID.
- Assert: validate external calls against the mock transcript.
- Assert: run twice with the same idempotency key where applicable.
- Evidence: retain failure output as CI artifact, but redact secrets and payload bodies.

#### T-0077 — migration downgrade

- Arrange: use a deterministic fixture explicitly targeting migration downgrade.
- Act: invoke the smallest public domain/application interface that exercises the rule.
- Assert: validate the typed result and stable reason codes.
- Assert: validate database side effects and absence of forbidden duplicate rows.
- Assert: validate emitted audit event and correlation ID.
- Assert: validate external calls against the mock transcript.
- Assert: run twice with the same idempotency key where applicable.
- Evidence: retain failure output as CI artifact, but redact secrets and payload bodies.

#### T-0078 — Docker-only host prerequisite

- Arrange: use a deterministic fixture explicitly targeting Docker-only host prerequisite.
- Act: invoke the smallest public domain/application interface that exercises the rule.
- Assert: validate the typed result and stable reason codes.
- Assert: validate database side effects and absence of forbidden duplicate rows.
- Assert: validate emitted audit event and correlation ID.
- Assert: validate external calls against the mock transcript.
- Assert: run twice with the same idempotency key where applicable.
- Evidence: retain failure output as CI artifact, but redact secrets and payload bodies.

#### T-0079 — containerized lint test build parity

- Arrange: use a deterministic fixture explicitly targeting containerized lint test build parity.
- Act: invoke the smallest public domain/application interface that exercises the rule.
- Assert: validate the typed result and stable reason codes.
- Assert: validate database side effects and absence of forbidden duplicate rows.
- Assert: validate emitted audit event and correlation ID.
- Assert: validate external calls against the mock transcript.
- Assert: run twice with the same idempotency key where applicable.
- Evidence: retain failure output as CI artifact, but redact secrets and payload bodies.

#### T-0080 — responsive scan UI

- Arrange: use a deterministic fixture explicitly targeting responsive scan UI.
- Act: invoke the smallest public domain/application interface that exercises the rule.
- Assert: validate the typed result and stable reason codes.
- Assert: validate database side effects and absence of forbidden duplicate rows.
- Assert: validate emitted audit event and correlation ID.
- Assert: validate external calls against the mock transcript.
- Assert: run twice with the same idempotency key where applicable.
- Evidence: retain failure output as CI artifact, but redact secrets and payload bodies.

#### T-0081 — keyboard search

- Arrange: use a deterministic fixture explicitly targeting keyboard search.
- Act: invoke the smallest public domain/application interface that exercises the rule.
- Assert: validate the typed result and stable reason codes.
- Assert: validate database side effects and absence of forbidden duplicate rows.
- Assert: validate emitted audit event and correlation ID.
- Assert: validate external calls against the mock transcript.
- Assert: run twice with the same idempotency key where applicable.
- Evidence: retain failure output as CI artifact, but redact secrets and payload bodies.

#### T-0082 — screen-reader progress

- Arrange: use a deterministic fixture explicitly targeting screen-reader progress.
- Act: invoke the smallest public domain/application interface that exercises the rule.
- Assert: validate the typed result and stable reason codes.
- Assert: validate database side effects and absence of forbidden duplicate rows.
- Assert: validate emitted audit event and correlation ID.
- Assert: validate external calls against the mock transcript.
- Assert: run twice with the same idempotency key where applicable.
- Evidence: retain failure output as CI artifact, but redact secrets and payload bodies.

#### T-0083 — degraded banner

- Arrange: use a deterministic fixture explicitly targeting degraded banner.
- Act: invoke the smallest public domain/application interface that exercises the rule.
- Assert: validate the typed result and stable reason codes.
- Assert: validate database side effects and absence of forbidden duplicate rows.
- Assert: validate emitted audit event and correlation ID.
- Assert: validate external calls against the mock transcript.
- Assert: run twice with the same idempotency key where applicable.
- Evidence: retain failure output as CI artifact, but redact secrets and payload bodies.

#### T-0084 — export reproducibility

- Arrange: use a deterministic fixture explicitly targeting export reproducibility.
- Act: invoke the smallest public domain/application interface that exercises the rule.
- Assert: validate the typed result and stable reason codes.
- Assert: validate database side effects and absence of forbidden duplicate rows.
- Assert: validate emitted audit event and correlation ID.
- Assert: validate external calls against the mock transcript.
- Assert: run twice with the same idempotency key where applicable.
- Evidence: retain failure output as CI artifact, but redact secrets and payload bodies.

### 27.3 Golden fixtures

- Golden payloads are sanitized and committed with provider schema version and capture metadata.
- A golden update requires review of the semantic diff, not blind snapshot acceptance.
- Each provider has success, empty, partial, rate-limit, invalid-auth, and schema-drift fixtures.
- The full golden run uses only mocks and fixed seeds and must be byte-stable where expected.
- Nondeterministic identifiers and times are injected, never scrubbed after the fact.

## 28. Coding Conventions

### 28.1 Python

- Python 3.13; full type hints; `mypy --strict` for domain and application packages.
- Pydantic models are frozen and forbid extra fields by default.
- Use `Decimal` for money, prices, and persisted probabilities.
- Use timezone-aware `datetime`; reject naive values at boundaries.
- Domain functions are pure whenever practical.
- No broad `except Exception` without re-raise classification and audit.
- No provider SDK types outside infrastructure adapters.
- No network or database calls inside Temporal workflow definitions.
- Tests follow Arrange/Act/Assert and name the invariant or behavior.

### 28.2 TypeScript and React

- TypeScript strict mode with no unchecked `any`.
- Generated API types are the only transport contracts.
- Components do not fetch data directly; feature hooks own queries and mutations.
- Server and client components are chosen intentionally; client boundaries remain small.
- Interactive elements use semantic HTML before ARIA.
- All dates enter UI formatting as ISO timestamps with explicit timezone.
- Do not store server truth solely in client state.
- Optimistic updates are forbidden for lock state and budget state.

### 28.3 SQL

- Use lowercase snake_case identifiers.
- Name constraints and indexes explicitly.
- Foreign-key actions are explicit.
- Append-only tables have mutation-denial triggers where risk justifies them.
- Use partial and covering indexes based on measured queries.
- Migration SQL is formatted and explain plans are retained for risky changes.

### 28.4 Requirement traceability

```yaml
requirement_id: INV-003
implementation:
  - apps/api/app/domain/evidence/cutoff.py
  - apps/api/app/application/evidence/packet_builder.py
tests:
  - apps/api/tests/domain/test_cutoff_policy.py
  - tests/backtest/test_no_lookahead.py
evidence:
  - ci://run/1234/artifact/cutoff-tests
status: verified
```

## 29. Architecture Decision Records

### ADR-001 — Monorepo and language split

- Status: accepted for initial implementation.
- Decision: Next.js/TypeScript UI plus FastAPI/Python analysis backend.
- Context: document the forces, constraints, and rejected alternatives.
- Consequences: document operational cost, test obligations, and future escape hatch.
- Revisit trigger: specify a measurable condition, not a date alone.
- File: `docs/adr/adr-001-monorepo-and-language-split.md`.

### ADR-002 — Temporal orchestration

- Status: accepted for initial implementation.
- Decision: Durable workflows instead of in-process background tasks.
- Context: document the forces, constraints, and rejected alternatives.
- Consequences: document operational cost, test obligations, and future escape hatch.
- Revisit trigger: specify a measurable condition, not a date alone.
- File: `docs/adr/adr-002-temporal-orchestration.md`.

### ADR-003 — PostgreSQL system of record

- Status: accepted for initial implementation.
- Decision: Relational core with JSONB, pgvector, and partitions.
- Context: document the forces, constraints, and rejected alternatives.
- Consequences: document operational cost, test obligations, and future escape hatch.
- Revisit trigger: specify a measurable condition, not a date alone.
- File: `docs/adr/adr-003-postgresql-system-of-record.md`.

### ADR-004 — Provider abstraction

- Status: accepted for initial implementation.
- Decision: No vendor SDK in domain or application contracts.
- Context: document the forces, constraints, and rejected alternatives.
- Consequences: document operational cost, test obligations, and future escape hatch.
- Revisit trigger: specify a measurable condition, not a date alone.
- File: `docs/adr/adr-004-provider-abstraction.md`.

### ADR-005 — Bitemporal evidence

- Status: accepted for initial implementation.
- Decision: Knowledge time and effective time are first-class.
- Context: document the forces, constraints, and rejected alternatives.
- Consequences: document operational cost, test obligations, and future escape hatch.
- Revisit trigger: specify a measurable condition, not a date alone.
- File: `docs/adr/adr-005-bitemporal-evidence.md`.

### ADR-006 — Prediction immutability

- Status: accepted for initial implementation.
- Decision: Database trigger plus object manifest lock.
- Context: document the forces, constraints, and rejected alternatives.
- Consequences: document operational cost, test obligations, and future escape hatch.
- Revisit trigger: specify a measurable condition, not a date alone.
- File: `docs/adr/adr-006-prediction-immutability.md`.

### ADR-007 — Model registry

- Status: accepted for initial implementation.
- Decision: Configuration-driven IDs, prices, capabilities, and expiry.
- Context: document the forces, constraints, and rejected alternatives.
- Consequences: document operational cost, test obligations, and future escape hatch.
- Revisit trigger: specify a measurable condition, not a date alone.
- File: `docs/adr/adr-007-model-registry.md`.

### ADR-008 — Agent isolation

- Status: accepted for initial implementation.
- Decision: Separate prompts, schemas, tools, and retrieval per role.
- Context: document the forces, constraints, and rejected alternatives.
- Consequences: document operational cost, test obligations, and future escape hatch.
- Revisit trigger: specify a measurable condition, not a date alone.
- File: `docs/adr/adr-008-agent-isolation.md`.

### ADR-009 — No restricted scraping

- Status: accepted for initial implementation.
- Decision: Allowed API providers only.
- Context: document the forces, constraints, and rejected alternatives.
- Consequences: document operational cost, test obligations, and future escape hatch.
- Revisit trigger: specify a measurable condition, not a date alone.
- File: `docs/adr/adr-009-no-restricted-scraping.md`.

### ADR-010 — Quant before narrative

- Status: accepted for initial implementation.
- Decision: Transparent baselines anchor LLM synthesis.
- Context: document the forces, constraints, and rejected alternatives.
- Consequences: document operational cost, test obligations, and future escape hatch.
- Revisit trigger: specify a measurable condition, not a date alone.
- File: `docs/adr/adr-010-quant-before-narrative.md`.

### ADR-011 — Prediction-forbidden Sonnet committee

- Status: accepted for initial implementation.
- Decision: Four role-specific syntheses cannot emit final probabilities; Chief remains the first LLM forecast stage.
- Context: document the forces, constraints, and rejected alternatives.
- Consequences: document operational cost, test obligations, and future escape hatch.
- Revisit trigger: specify a measurable condition, not a date alone.
- File: `docs/adr/adr-011-prediction-forbidden-sonnet-committee.md`.

### ADR-012 — One revision maximum

- Status: accepted for initial implementation.
- Decision: Prevent critic/revision loops and budget drift.
- Context: document the forces, constraints, and rejected alternatives.
- Consequences: document operational cost, test obligations, and future escape hatch.
- Revisit trigger: specify a measurable condition, not a date alone.
- File: `docs/adr/adr-012-one-revision-maximum.md`.

### ADR-013 — Post-match separation

- Status: accepted for initial implementation.
- Decision: Locked pre-match artifacts remain untouched.
- Context: document the forces, constraints, and rejected alternatives.
- Consequences: document operational cost, test obligations, and future escape hatch.
- Revisit trigger: specify a measurable condition, not a date alone.
- File: `docs/adr/adr-013-post-match-separation.md`.

### ADR-014 — Mock-first local development

- Status: accepted for initial implementation.
- Decision: No API keys required for complete deterministic flow.
- Context: document the forces, constraints, and rejected alternatives.
- Consequences: document operational cost, test obligations, and future escape hatch.
- Revisit trigger: specify a measurable condition, not a date alone.
- File: `docs/adr/adr-014-mock-first-local-development.md`.

### ADR-015 — Personal-use auth boundary

- Status: accepted for initial implementation.
- Decision: Simple secure single-workspace session, upgrade path documented.
- Context: document the forces, constraints, and rejected alternatives.
- Consequences: document operational cost, test obligations, and future escape hatch.
- Revisit trigger: specify a measurable condition, not a date alone.
- File: `docs/adr/adr-015-personal-use-auth-boundary.md`.

## 30. Phased Roadmap

### P00 — Repository bootstrap

- Scope: Workspace, quality gates, CI, Compose, health endpoints.
- Start gate: prior phase acceptance evidence is green or an explicit parallel-safe exception is recorded.
- Deliverable: one demonstrable vertical behavior, migrations, contracts, tests, and documentation.
- Provider behavior: use mocks unless this phase explicitly enables a reviewed provider.
- Data behavior: seed and migration are deterministic from a clean checkout.
- UI behavior: loading, empty, success, degraded, and error states exist for new surfaces.
- Observability: new commands, stages, and external calls emit traces and bounded metrics.
- Security: new trust boundaries have negative tests.
- Cost: external calls remain under a phase-specific test budget.
- Review: requirement ledger links code and tests to this phase.
- Exit: clean bootstrap, lint, typecheck, unit, contract, integration, and relevant E2E tests pass.
- Non-exit: a screenshot, successful compilation alone, or an unverified provider response is insufficient.

### P01 — Canonical time and identity

- Scope: Istanbul window, sport/competition/team/fixture models.
- Start gate: prior phase acceptance evidence is green or an explicit parallel-safe exception is recorded.
- Deliverable: one demonstrable vertical behavior, migrations, contracts, tests, and documentation.
- Provider behavior: use mocks unless this phase explicitly enables a reviewed provider.
- Data behavior: seed and migration are deterministic from a clean checkout.
- UI behavior: loading, empty, success, degraded, and error states exist for new surfaces.
- Observability: new commands, stages, and external calls emit traces and bounded metrics.
- Security: new trust boundaries have negative tests.
- Cost: external calls remain under a phase-specific test budget.
- Review: requirement ledger links code and tests to this phase.
- Exit: clean bootstrap, lint, typecheck, unit, contract, integration, and relevant E2E tests pass.
- Non-exit: a screenshot, successful compilation alone, or an unverified provider response is insufficient.

### P02 — Mock-first scan

- Scope: Three-day mock provider scan and candidate list.
- Start gate: prior phase acceptance evidence is green or an explicit parallel-safe exception is recorded.
- Deliverable: one demonstrable vertical behavior, migrations, contracts, tests, and documentation.
- Provider behavior: use mocks unless this phase explicitly enables a reviewed provider.
- Data behavior: seed and migration are deterministic from a clean checkout.
- UI behavior: loading, empty, success, degraded, and error states exist for new surfaces.
- Observability: new commands, stages, and external calls emit traces and bounded metrics.
- Security: new trust boundaries have negative tests.
- Cost: external calls remain under a phase-specific test budget.
- Review: requirement ledger links code and tests to this phase.
- Exit: clean bootstrap, lint, typecheck, unit, contract, integration, and relevant E2E tests pass.
- Non-exit: a screenshot, successful compilation alone, or an unverified provider response is insufficient.

### P03 — Manual search

- Scope: Search, ambiguity-safe selection, fixture preflight.
- Start gate: prior phase acceptance evidence is green or an explicit parallel-safe exception is recorded.
- Deliverable: one demonstrable vertical behavior, migrations, contracts, tests, and documentation.
- Provider behavior: use mocks unless this phase explicitly enables a reviewed provider.
- Data behavior: seed and migration are deterministic from a clean checkout.
- UI behavior: loading, empty, success, degraded, and error states exist for new surfaces.
- Observability: new commands, stages, and external calls emit traces and bounded metrics.
- Security: new trust boundaries have negative tests.
- Cost: external calls remain under a phase-specific test budget.
- Review: requirement ledger links code and tests to this phase.
- Exit: clean bootstrap, lint, typecheck, unit, contract, integration, and relevant E2E tests pass.
- Non-exit: a screenshot, successful compilation alone, or an unverified provider response is insufficient.

### P04 — Durable run shell

- Scope: Temporal workflow, stages, progress SSE, cancellation.
- Start gate: prior phase acceptance evidence is green or an explicit parallel-safe exception is recorded.
- Deliverable: one demonstrable vertical behavior, migrations, contracts, tests, and documentation.
- Provider behavior: use mocks unless this phase explicitly enables a reviewed provider.
- Data behavior: seed and migration are deterministic from a clean checkout.
- UI behavior: loading, empty, success, degraded, and error states exist for new surfaces.
- Observability: new commands, stages, and external calls emit traces and bounded metrics.
- Security: new trust boundaries have negative tests.
- Cost: external calls remain under a phase-specific test budget.
- Review: requirement ledger links code and tests to this phase.
- Exit: clean bootstrap, lint, typecheck, unit, contract, integration, and relevant E2E tests pass.
- Non-exit: a screenshot, successful compilation alone, or an unverified provider response is insufficient.

### P05 — Evidence ledger

- Scope: Snapshots, sources, claims, freshness, contradictions.
- Start gate: prior phase acceptance evidence is green or an explicit parallel-safe exception is recorded.
- Deliverable: one demonstrable vertical behavior, migrations, contracts, tests, and documentation.
- Provider behavior: use mocks unless this phase explicitly enables a reviewed provider.
- Data behavior: seed and migration are deterministic from a clean checkout.
- UI behavior: loading, empty, success, degraded, and error states exist for new surfaces.
- Observability: new commands, stages, and external calls emit traces and bounded metrics.
- Security: new trust boundaries have negative tests.
- Cost: external calls remain under a phase-specific test budget.
- Review: requirement ledger links code and tests to this phase.
- Exit: clean bootstrap, lint, typecheck, unit, contract, integration, and relevant E2E tests pass.
- Non-exit: a screenshot, successful compilation alone, or an unverified provider response is insufficient.

### P06 — Football structured data

- Scope: Stats, squad, form, fatigue, goalkeeper, set pieces, environment.
- Start gate: prior phase acceptance evidence is green or an explicit parallel-safe exception is recorded.
- Deliverable: one demonstrable vertical behavior, migrations, contracts, tests, and documentation.
- Provider behavior: use mocks unless this phase explicitly enables a reviewed provider.
- Data behavior: seed and migration are deterministic from a clean checkout.
- UI behavior: loading, empty, success, degraded, and error states exist for new surfaces.
- Observability: new commands, stages, and external calls emit traces and bounded metrics.
- Security: new trust boundaries have negative tests.
- Cost: external calls remain under a phase-specific test budget.
- Review: requirement ledger links code and tests to this phase.
- Exit: clean bootstrap, lint, typecheck, unit, contract, integration, and relevant E2E tests pass.
- Non-exit: a screenshot, successful compilation alone, or an unverified provider response is insufficient.

### P07 — Quant baseline

- Scope: Elo, Poisson/Dixon-Coles, calibration, diagnostics.
- Start gate: prior phase acceptance evidence is green or an explicit parallel-safe exception is recorded.
- Deliverable: one demonstrable vertical behavior, migrations, contracts, tests, and documentation.
- Provider behavior: use mocks unless this phase explicitly enables a reviewed provider.
- Data behavior: seed and migration are deterministic from a clean checkout.
- UI behavior: loading, empty, success, degraded, and error states exist for new surfaces.
- Observability: new commands, stages, and external calls emit traces and bounded metrics.
- Security: new trust boundaries have negative tests.
- Cost: external calls remain under a phase-specific test budget.
- Review: requirement ledger links code and tests to this phase.
- Exit: clean bootstrap, lint, typecheck, unit, contract, integration, and relevant E2E tests pass.
- Non-exit: a screenshot, successful compilation alone, or an unverified provider response is insufficient.

### P08 — Allowed odds

- Scope: Provider adapter, snapshots, fair probability, movement.
- Start gate: prior phase acceptance evidence is green or an explicit parallel-safe exception is recorded.
- Deliverable: one demonstrable vertical behavior, migrations, contracts, tests, and documentation.
- Provider behavior: use mocks unless this phase explicitly enables a reviewed provider.
- Data behavior: seed and migration are deterministic from a clean checkout.
- UI behavior: loading, empty, success, degraded, and error states exist for new surfaces.
- Observability: new commands, stages, and external calls emit traces and bounded metrics.
- Security: new trust boundaries have negative tests.
- Cost: external calls remain under a phase-specific test budget.
- Review: requirement ledger links code and tests to this phase.
- Exit: clean bootstrap, lint, typecheck, unit, contract, integration, and relevant E2E tests pass.
- Non-exit: a screenshot, successful compilation alone, or an unverified provider response is insufficient.

### P09 — RAG and case skeleton

- Scope: Chunks, embeddings, retrieval policies, graph edges.
- Start gate: prior phase acceptance evidence is green or an explicit parallel-safe exception is recorded.
- Deliverable: one demonstrable vertical behavior, migrations, contracts, tests, and documentation.
- Provider behavior: use mocks unless this phase explicitly enables a reviewed provider.
- Data behavior: seed and migration are deterministic from a clean checkout.
- UI behavior: loading, empty, success, degraded, and error states exist for new surfaces.
- Observability: new commands, stages, and external calls emit traces and bounded metrics.
- Security: new trust boundaries have negative tests.
- Cost: external calls remain under a phase-specific test budget.
- Review: requirement ledger links code and tests to this phase.
- Exit: clean bootstrap, lint, typecheck, unit, contract, integration, and relevant E2E tests pass.
- Non-exit: a screenshot, successful compilation alone, or an unverified provider response is insufficient.

### P10 — Critics and Sonnet syntheses

- Scope: Independent critics plus four prediction-forbidden Sonnet roles.
- Start gate: prior phase acceptance evidence is green or an explicit parallel-safe exception is recorded.
- Deliverable: one demonstrable vertical behavior, migrations, contracts, tests, and documentation.
- Provider behavior: use mocks unless this phase explicitly enables a reviewed provider.
- Data behavior: seed and migration are deterministic from a clean checkout.
- UI behavior: loading, empty, success, degraded, and error states exist for new surfaces.
- Observability: new commands, stages, and external calls emit traces and bounded metrics.
- Security: new trust boundaries have negative tests.
- Cost: external calls remain under a phase-specific test budget.
- Review: requirement ledger links code and tests to this phase.
- Exit: clean bootstrap, lint, typecheck, unit, contract, integration, and relevant E2E tests pass.
- Non-exit: a screenshot, successful compilation alone, or an unverified provider response is insufficient.

### P11 — Scenarios and finalization

- Scope: Steelman, red team, Chief, final critic, one revision.
- Start gate: prior phase acceptance evidence is green or an explicit parallel-safe exception is recorded.
- Deliverable: one demonstrable vertical behavior, migrations, contracts, tests, and documentation.
- Provider behavior: use mocks unless this phase explicitly enables a reviewed provider.
- Data behavior: seed and migration are deterministic from a clean checkout.
- UI behavior: loading, empty, success, degraded, and error states exist for new surfaces.
- Observability: new commands, stages, and external calls emit traces and bounded metrics.
- Security: new trust boundaries have negative tests.
- Cost: external calls remain under a phase-specific test budget.
- Review: requirement ledger links code and tests to this phase.
- Exit: clean bootstrap, lint, typecheck, unit, contract, integration, and relevant E2E tests pass.
- Non-exit: a screenshot, successful compilation alone, or an unverified provider response is insufficient.

### P12 — Immutable lock

- Scope: Manifest, hashes, database trigger, exports.
- Start gate: prior phase acceptance evidence is green or an explicit parallel-safe exception is recorded.
- Deliverable: one demonstrable vertical behavior, migrations, contracts, tests, and documentation.
- Provider behavior: use mocks unless this phase explicitly enables a reviewed provider.
- Data behavior: seed and migration are deterministic from a clean checkout.
- UI behavior: loading, empty, success, degraded, and error states exist for new surfaces.
- Observability: new commands, stages, and external calls emit traces and bounded metrics.
- Security: new trust boundaries have negative tests.
- Cost: external calls remain under a phase-specific test budget.
- Review: requirement ledger links code and tests to this phase.
- Exit: clean bootstrap, lint, typecheck, unit, contract, integration, and relevant E2E tests pass.
- Non-exit: a screenshot, successful compilation alone, or an unverified provider response is insufficient.

### P13 — Post-match learning

- Scope: Result, autopsy, variance, lesson validation, case memory.
- Start gate: prior phase acceptance evidence is green or an explicit parallel-safe exception is recorded.
- Deliverable: one demonstrable vertical behavior, migrations, contracts, tests, and documentation.
- Provider behavior: use mocks unless this phase explicitly enables a reviewed provider.
- Data behavior: seed and migration are deterministic from a clean checkout.
- UI behavior: loading, empty, success, degraded, and error states exist for new surfaces.
- Observability: new commands, stages, and external calls emit traces and bounded metrics.
- Security: new trust boundaries have negative tests.
- Cost: external calls remain under a phase-specific test budget.
- Review: requirement ledger links code and tests to this phase.
- Exit: clean bootstrap, lint, typecheck, unit, contract, integration, and relevant E2E tests pass.
- Non-exit: a screenshot, successful compilation alone, or an unverified provider response is insufficient.

### P14 — Backtesting and experiments

- Scope: Walk-forward harness, leakage sentinels, shadow routing.
- Start gate: prior phase acceptance evidence is green or an explicit parallel-safe exception is recorded.
- Deliverable: one demonstrable vertical behavior, migrations, contracts, tests, and documentation.
- Provider behavior: use mocks unless this phase explicitly enables a reviewed provider.
- Data behavior: seed and migration are deterministic from a clean checkout.
- UI behavior: loading, empty, success, degraded, and error states exist for new surfaces.
- Observability: new commands, stages, and external calls emit traces and bounded metrics.
- Security: new trust boundaries have negative tests.
- Cost: external calls remain under a phase-specific test budget.
- Review: requirement ledger links code and tests to this phase.
- Exit: clean bootstrap, lint, typecheck, unit, contract, integration, and relevant E2E tests pass.
- Non-exit: a screenshot, successful compilation alone, or an unverified provider response is insufficient.

### P15 — Operational hardening

- Scope: Dashboards, alerts, retention, security tests, runbooks.
- Start gate: prior phase acceptance evidence is green or an explicit parallel-safe exception is recorded.
- Deliverable: one demonstrable vertical behavior, migrations, contracts, tests, and documentation.
- Provider behavior: use mocks unless this phase explicitly enables a reviewed provider.
- Data behavior: seed and migration are deterministic from a clean checkout.
- UI behavior: loading, empty, success, degraded, and error states exist for new surfaces.
- Observability: new commands, stages, and external calls emit traces and bounded metrics.
- Security: new trust boundaries have negative tests.
- Cost: external calls remain under a phase-specific test budget.
- Review: requirement ledger links code and tests to this phase.
- Exit: clean bootstrap, lint, typecheck, unit, contract, integration, and relevant E2E tests pass.
- Non-exit: a screenshot, successful compilation alone, or an unverified provider response is insufficient.

### P16 — Basketball plugin discovery

- Scope: Sport contract gaps and isolated adapter prototype.
- Start gate: prior phase acceptance evidence is green or an explicit parallel-safe exception is recorded.
- Deliverable: one demonstrable vertical behavior, migrations, contracts, tests, and documentation.
- Provider behavior: use mocks unless this phase explicitly enables a reviewed provider.
- Data behavior: seed and migration are deterministic from a clean checkout.
- UI behavior: loading, empty, success, degraded, and error states exist for new surfaces.
- Observability: new commands, stages, and external calls emit traces and bounded metrics.
- Security: new trust boundaries have negative tests.
- Cost: external calls remain under a phase-specific test budget.
- Review: requirement ledger links code and tests to this phase.
- Exit: clean bootstrap, lint, typecheck, unit, contract, integration, and relevant E2E tests pass.
- Non-exit: a screenshot, successful compilation alone, or an unverified provider response is insufficient.

### P17 — Volleyball plugin discovery

- Scope: Sport contract gaps and isolated adapter prototype.
- Start gate: prior phase acceptance evidence is green or an explicit parallel-safe exception is recorded.
- Deliverable: one demonstrable vertical behavior, migrations, contracts, tests, and documentation.
- Provider behavior: use mocks unless this phase explicitly enables a reviewed provider.
- Data behavior: seed and migration are deterministic from a clean checkout.
- UI behavior: loading, empty, success, degraded, and error states exist for new surfaces.
- Observability: new commands, stages, and external calls emit traces and bounded metrics.
- Security: new trust boundaries have negative tests.
- Cost: external calls remain under a phase-specific test budget.
- Review: requirement ledger links code and tests to this phase.
- Exit: clean bootstrap, lint, typecheck, unit, contract, integration, and relevant E2E tests pass.
- Non-exit: a screenshot, successful compilation alone, or an unverified provider response is insufficient.

## 31. Phase Acceptance Criteria

### P00 acceptance checklist — Repository bootstrap

- [ ] P00-AC-01: A clean checkout follows documented setup without manual database edits.
- [ ] P00-AC-02: All new environment variables appear in `.env.example` without secrets.
- [ ] P00-AC-03: All new contracts reject unknown fields.
- [ ] P00-AC-04: All migrations upgrade from the prior released head.
- [ ] P00-AC-05: All migrations are reviewed for destructive or locking behavior.
- [ ] P00-AC-06: Unit tests cover pure domain policies.
- [ ] P00-AC-07: Contract tests cover provider or API boundaries.
- [ ] P00-AC-08: Integration tests cover persistence and workflow effects.
- [ ] P00-AC-09: At least one failure/degraded path is demonstrated.
- [ ] P00-AC-10: Observability spans and metrics are asserted where practical.
- [ ] P00-AC-11: No secret or raw sensitive payload appears in logs or browser bundles.
- [ ] P00-AC-12: Requirement ledger is updated.
- [ ] P00-AC-13: README or runbook reflects operator-facing changes.
- [ ] P00-AC-14: User-visible behavior is verified in Playwright when applicable.
- [ ] P00-AC-15: The result is committed as a narrow, reviewable phase change.

### P01 acceptance checklist — Canonical time and identity

- [ ] P01-AC-01: A clean checkout follows documented setup without manual database edits.
- [ ] P01-AC-02: All new environment variables appear in `.env.example` without secrets.
- [ ] P01-AC-03: All new contracts reject unknown fields.
- [ ] P01-AC-04: All migrations upgrade from the prior released head.
- [ ] P01-AC-05: All migrations are reviewed for destructive or locking behavior.
- [ ] P01-AC-06: Unit tests cover pure domain policies.
- [ ] P01-AC-07: Contract tests cover provider or API boundaries.
- [ ] P01-AC-08: Integration tests cover persistence and workflow effects.
- [ ] P01-AC-09: At least one failure/degraded path is demonstrated.
- [ ] P01-AC-10: Observability spans and metrics are asserted where practical.
- [ ] P01-AC-11: No secret or raw sensitive payload appears in logs or browser bundles.
- [ ] P01-AC-12: Requirement ledger is updated.
- [ ] P01-AC-13: README or runbook reflects operator-facing changes.
- [ ] P01-AC-14: User-visible behavior is verified in Playwright when applicable.
- [ ] P01-AC-15: The result is committed as a narrow, reviewable phase change.

### P02 acceptance checklist — Mock-first scan

- [ ] P02-AC-01: A clean checkout follows documented setup without manual database edits.
- [ ] P02-AC-02: All new environment variables appear in `.env.example` without secrets.
- [ ] P02-AC-03: All new contracts reject unknown fields.
- [ ] P02-AC-04: All migrations upgrade from the prior released head.
- [ ] P02-AC-05: All migrations are reviewed for destructive or locking behavior.
- [ ] P02-AC-06: Unit tests cover pure domain policies.
- [ ] P02-AC-07: Contract tests cover provider or API boundaries.
- [ ] P02-AC-08: Integration tests cover persistence and workflow effects.
- [ ] P02-AC-09: At least one failure/degraded path is demonstrated.
- [ ] P02-AC-10: Observability spans and metrics are asserted where practical.
- [ ] P02-AC-11: No secret or raw sensitive payload appears in logs or browser bundles.
- [ ] P02-AC-12: Requirement ledger is updated.
- [ ] P02-AC-13: README or runbook reflects operator-facing changes.
- [ ] P02-AC-14: User-visible behavior is verified in Playwright when applicable.
- [ ] P02-AC-15: The result is committed as a narrow, reviewable phase change.

### P03 acceptance checklist — Manual search

- [ ] P03-AC-01: A clean checkout follows documented setup without manual database edits.
- [ ] P03-AC-02: All new environment variables appear in `.env.example` without secrets.
- [ ] P03-AC-03: All new contracts reject unknown fields.
- [ ] P03-AC-04: All migrations upgrade from the prior released head.
- [ ] P03-AC-05: All migrations are reviewed for destructive or locking behavior.
- [ ] P03-AC-06: Unit tests cover pure domain policies.
- [ ] P03-AC-07: Contract tests cover provider or API boundaries.
- [ ] P03-AC-08: Integration tests cover persistence and workflow effects.
- [ ] P03-AC-09: At least one failure/degraded path is demonstrated.
- [ ] P03-AC-10: Observability spans and metrics are asserted where practical.
- [ ] P03-AC-11: No secret or raw sensitive payload appears in logs or browser bundles.
- [ ] P03-AC-12: Requirement ledger is updated.
- [ ] P03-AC-13: README or runbook reflects operator-facing changes.
- [ ] P03-AC-14: User-visible behavior is verified in Playwright when applicable.
- [ ] P03-AC-15: The result is committed as a narrow, reviewable phase change.

### P04 acceptance checklist — Durable run shell

- [ ] P04-AC-01: A clean checkout follows documented setup without manual database edits.
- [ ] P04-AC-02: All new environment variables appear in `.env.example` without secrets.
- [ ] P04-AC-03: All new contracts reject unknown fields.
- [ ] P04-AC-04: All migrations upgrade from the prior released head.
- [ ] P04-AC-05: All migrations are reviewed for destructive or locking behavior.
- [ ] P04-AC-06: Unit tests cover pure domain policies.
- [ ] P04-AC-07: Contract tests cover provider or API boundaries.
- [ ] P04-AC-08: Integration tests cover persistence and workflow effects.
- [ ] P04-AC-09: At least one failure/degraded path is demonstrated.
- [ ] P04-AC-10: Observability spans and metrics are asserted where practical.
- [ ] P04-AC-11: No secret or raw sensitive payload appears in logs or browser bundles.
- [ ] P04-AC-12: Requirement ledger is updated.
- [ ] P04-AC-13: README or runbook reflects operator-facing changes.
- [ ] P04-AC-14: User-visible behavior is verified in Playwright when applicable.
- [ ] P04-AC-15: The result is committed as a narrow, reviewable phase change.

### P05 acceptance checklist — Evidence ledger

- [ ] P05-AC-01: A clean checkout follows documented setup without manual database edits.
- [ ] P05-AC-02: All new environment variables appear in `.env.example` without secrets.
- [ ] P05-AC-03: All new contracts reject unknown fields.
- [ ] P05-AC-04: All migrations upgrade from the prior released head.
- [ ] P05-AC-05: All migrations are reviewed for destructive or locking behavior.
- [ ] P05-AC-06: Unit tests cover pure domain policies.
- [ ] P05-AC-07: Contract tests cover provider or API boundaries.
- [ ] P05-AC-08: Integration tests cover persistence and workflow effects.
- [ ] P05-AC-09: At least one failure/degraded path is demonstrated.
- [ ] P05-AC-10: Observability spans and metrics are asserted where practical.
- [ ] P05-AC-11: No secret or raw sensitive payload appears in logs or browser bundles.
- [ ] P05-AC-12: Requirement ledger is updated.
- [ ] P05-AC-13: README or runbook reflects operator-facing changes.
- [ ] P05-AC-14: User-visible behavior is verified in Playwright when applicable.
- [ ] P05-AC-15: The result is committed as a narrow, reviewable phase change.

### P06 acceptance checklist — Football structured data

- [ ] P06-AC-01: A clean checkout follows documented setup without manual database edits.
- [ ] P06-AC-02: All new environment variables appear in `.env.example` without secrets.
- [ ] P06-AC-03: All new contracts reject unknown fields.
- [ ] P06-AC-04: All migrations upgrade from the prior released head.
- [ ] P06-AC-05: All migrations are reviewed for destructive or locking behavior.
- [ ] P06-AC-06: Unit tests cover pure domain policies.
- [ ] P06-AC-07: Contract tests cover provider or API boundaries.
- [ ] P06-AC-08: Integration tests cover persistence and workflow effects.
- [ ] P06-AC-09: At least one failure/degraded path is demonstrated.
- [ ] P06-AC-10: Observability spans and metrics are asserted where practical.
- [ ] P06-AC-11: No secret or raw sensitive payload appears in logs or browser bundles.
- [ ] P06-AC-12: Requirement ledger is updated.
- [ ] P06-AC-13: README or runbook reflects operator-facing changes.
- [ ] P06-AC-14: User-visible behavior is verified in Playwright when applicable.
- [ ] P06-AC-15: The result is committed as a narrow, reviewable phase change.

### P07 acceptance checklist — Quant baseline

- [ ] P07-AC-01: A clean checkout follows documented setup without manual database edits.
- [ ] P07-AC-02: All new environment variables appear in `.env.example` without secrets.
- [ ] P07-AC-03: All new contracts reject unknown fields.
- [ ] P07-AC-04: All migrations upgrade from the prior released head.
- [ ] P07-AC-05: All migrations are reviewed for destructive or locking behavior.
- [ ] P07-AC-06: Unit tests cover pure domain policies.
- [ ] P07-AC-07: Contract tests cover provider or API boundaries.
- [ ] P07-AC-08: Integration tests cover persistence and workflow effects.
- [ ] P07-AC-09: At least one failure/degraded path is demonstrated.
- [ ] P07-AC-10: Observability spans and metrics are asserted where practical.
- [ ] P07-AC-11: No secret or raw sensitive payload appears in logs or browser bundles.
- [ ] P07-AC-12: Requirement ledger is updated.
- [ ] P07-AC-13: README or runbook reflects operator-facing changes.
- [ ] P07-AC-14: User-visible behavior is verified in Playwright when applicable.
- [ ] P07-AC-15: The result is committed as a narrow, reviewable phase change.

### P08 acceptance checklist — Allowed odds

- [ ] P08-AC-01: A clean checkout follows documented setup without manual database edits.
- [ ] P08-AC-02: All new environment variables appear in `.env.example` without secrets.
- [ ] P08-AC-03: All new contracts reject unknown fields.
- [ ] P08-AC-04: All migrations upgrade from the prior released head.
- [ ] P08-AC-05: All migrations are reviewed for destructive or locking behavior.
- [ ] P08-AC-06: Unit tests cover pure domain policies.
- [ ] P08-AC-07: Contract tests cover provider or API boundaries.
- [ ] P08-AC-08: Integration tests cover persistence and workflow effects.
- [ ] P08-AC-09: At least one failure/degraded path is demonstrated.
- [ ] P08-AC-10: Observability spans and metrics are asserted where practical.
- [ ] P08-AC-11: No secret or raw sensitive payload appears in logs or browser bundles.
- [ ] P08-AC-12: Requirement ledger is updated.
- [ ] P08-AC-13: README or runbook reflects operator-facing changes.
- [ ] P08-AC-14: User-visible behavior is verified in Playwright when applicable.
- [ ] P08-AC-15: The result is committed as a narrow, reviewable phase change.

### P09 acceptance checklist — RAG and case skeleton

- [ ] P09-AC-01: A clean checkout follows documented setup without manual database edits.
- [ ] P09-AC-02: All new environment variables appear in `.env.example` without secrets.
- [ ] P09-AC-03: All new contracts reject unknown fields.
- [ ] P09-AC-04: All migrations upgrade from the prior released head.
- [ ] P09-AC-05: All migrations are reviewed for destructive or locking behavior.
- [ ] P09-AC-06: Unit tests cover pure domain policies.
- [ ] P09-AC-07: Contract tests cover provider or API boundaries.
- [ ] P09-AC-08: Integration tests cover persistence and workflow effects.
- [ ] P09-AC-09: At least one failure/degraded path is demonstrated.
- [ ] P09-AC-10: Observability spans and metrics are asserted where practical.
- [ ] P09-AC-11: No secret or raw sensitive payload appears in logs or browser bundles.
- [ ] P09-AC-12: Requirement ledger is updated.
- [ ] P09-AC-13: README or runbook reflects operator-facing changes.
- [ ] P09-AC-14: User-visible behavior is verified in Playwright when applicable.
- [ ] P09-AC-15: The result is committed as a narrow, reviewable phase change.

### P10 acceptance checklist — Critics and Sonnet syntheses

- [ ] P10-AC-01: A clean checkout follows documented setup without manual database edits.
- [ ] P10-AC-02: All new environment variables appear in `.env.example` without secrets.
- [ ] P10-AC-03: All new contracts reject unknown fields.
- [ ] P10-AC-04: All migrations upgrade from the prior released head.
- [ ] P10-AC-05: All migrations are reviewed for destructive or locking behavior.
- [ ] P10-AC-06: Unit tests cover pure domain policies.
- [ ] P10-AC-07: Contract tests cover provider or API boundaries.
- [ ] P10-AC-08: Integration tests cover persistence and workflow effects.
- [ ] P10-AC-09: At least one failure/degraded path is demonstrated.
- [ ] P10-AC-10: Observability spans and metrics are asserted where practical.
- [ ] P10-AC-11: No secret or raw sensitive payload appears in logs or browser bundles.
- [ ] P10-AC-12: Requirement ledger is updated.
- [ ] P10-AC-13: README or runbook reflects operator-facing changes.
- [ ] P10-AC-14: User-visible behavior is verified in Playwright when applicable.
- [ ] P10-AC-15: The result is committed as a narrow, reviewable phase change.

### P11 acceptance checklist — Scenarios and finalization

- [ ] P11-AC-01: A clean checkout follows documented setup without manual database edits.
- [ ] P11-AC-02: All new environment variables appear in `.env.example` without secrets.
- [ ] P11-AC-03: All new contracts reject unknown fields.
- [ ] P11-AC-04: All migrations upgrade from the prior released head.
- [ ] P11-AC-05: All migrations are reviewed for destructive or locking behavior.
- [ ] P11-AC-06: Unit tests cover pure domain policies.
- [ ] P11-AC-07: Contract tests cover provider or API boundaries.
- [ ] P11-AC-08: Integration tests cover persistence and workflow effects.
- [ ] P11-AC-09: At least one failure/degraded path is demonstrated.
- [ ] P11-AC-10: Observability spans and metrics are asserted where practical.
- [ ] P11-AC-11: No secret or raw sensitive payload appears in logs or browser bundles.
- [ ] P11-AC-12: Requirement ledger is updated.
- [ ] P11-AC-13: README or runbook reflects operator-facing changes.
- [ ] P11-AC-14: User-visible behavior is verified in Playwright when applicable.
- [ ] P11-AC-15: The result is committed as a narrow, reviewable phase change.

### P12 acceptance checklist — Immutable lock

- [ ] P12-AC-01: A clean checkout follows documented setup without manual database edits.
- [ ] P12-AC-02: All new environment variables appear in `.env.example` without secrets.
- [ ] P12-AC-03: All new contracts reject unknown fields.
- [ ] P12-AC-04: All migrations upgrade from the prior released head.
- [ ] P12-AC-05: All migrations are reviewed for destructive or locking behavior.
- [ ] P12-AC-06: Unit tests cover pure domain policies.
- [ ] P12-AC-07: Contract tests cover provider or API boundaries.
- [ ] P12-AC-08: Integration tests cover persistence and workflow effects.
- [ ] P12-AC-09: At least one failure/degraded path is demonstrated.
- [ ] P12-AC-10: Observability spans and metrics are asserted where practical.
- [ ] P12-AC-11: No secret or raw sensitive payload appears in logs or browser bundles.
- [ ] P12-AC-12: Requirement ledger is updated.
- [ ] P12-AC-13: README or runbook reflects operator-facing changes.
- [ ] P12-AC-14: User-visible behavior is verified in Playwright when applicable.
- [ ] P12-AC-15: The result is committed as a narrow, reviewable phase change.

### P13 acceptance checklist — Post-match learning

- [ ] P13-AC-01: A clean checkout follows documented setup without manual database edits.
- [ ] P13-AC-02: All new environment variables appear in `.env.example` without secrets.
- [ ] P13-AC-03: All new contracts reject unknown fields.
- [ ] P13-AC-04: All migrations upgrade from the prior released head.
- [ ] P13-AC-05: All migrations are reviewed for destructive or locking behavior.
- [ ] P13-AC-06: Unit tests cover pure domain policies.
- [ ] P13-AC-07: Contract tests cover provider or API boundaries.
- [ ] P13-AC-08: Integration tests cover persistence and workflow effects.
- [ ] P13-AC-09: At least one failure/degraded path is demonstrated.
- [ ] P13-AC-10: Observability spans and metrics are asserted where practical.
- [ ] P13-AC-11: No secret or raw sensitive payload appears in logs or browser bundles.
- [ ] P13-AC-12: Requirement ledger is updated.
- [ ] P13-AC-13: README or runbook reflects operator-facing changes.
- [ ] P13-AC-14: User-visible behavior is verified in Playwright when applicable.
- [ ] P13-AC-15: The result is committed as a narrow, reviewable phase change.

### P14 acceptance checklist — Backtesting and experiments

- [ ] P14-AC-01: A clean checkout follows documented setup without manual database edits.
- [ ] P14-AC-02: All new environment variables appear in `.env.example` without secrets.
- [ ] P14-AC-03: All new contracts reject unknown fields.
- [ ] P14-AC-04: All migrations upgrade from the prior released head.
- [ ] P14-AC-05: All migrations are reviewed for destructive or locking behavior.
- [ ] P14-AC-06: Unit tests cover pure domain policies.
- [ ] P14-AC-07: Contract tests cover provider or API boundaries.
- [ ] P14-AC-08: Integration tests cover persistence and workflow effects.
- [ ] P14-AC-09: At least one failure/degraded path is demonstrated.
- [ ] P14-AC-10: Observability spans and metrics are asserted where practical.
- [ ] P14-AC-11: No secret or raw sensitive payload appears in logs or browser bundles.
- [ ] P14-AC-12: Requirement ledger is updated.
- [ ] P14-AC-13: README or runbook reflects operator-facing changes.
- [ ] P14-AC-14: User-visible behavior is verified in Playwright when applicable.
- [ ] P14-AC-15: The result is committed as a narrow, reviewable phase change.

### P15 acceptance checklist — Operational hardening

- [ ] P15-AC-01: A clean checkout follows documented setup without manual database edits.
- [ ] P15-AC-02: All new environment variables appear in `.env.example` without secrets.
- [ ] P15-AC-03: All new contracts reject unknown fields.
- [ ] P15-AC-04: All migrations upgrade from the prior released head.
- [ ] P15-AC-05: All migrations are reviewed for destructive or locking behavior.
- [ ] P15-AC-06: Unit tests cover pure domain policies.
- [ ] P15-AC-07: Contract tests cover provider or API boundaries.
- [ ] P15-AC-08: Integration tests cover persistence and workflow effects.
- [ ] P15-AC-09: At least one failure/degraded path is demonstrated.
- [ ] P15-AC-10: Observability spans and metrics are asserted where practical.
- [ ] P15-AC-11: No secret or raw sensitive payload appears in logs or browser bundles.
- [ ] P15-AC-12: Requirement ledger is updated.
- [ ] P15-AC-13: README or runbook reflects operator-facing changes.
- [ ] P15-AC-14: User-visible behavior is verified in Playwright when applicable.
- [ ] P15-AC-15: The result is committed as a narrow, reviewable phase change.

### P16 acceptance checklist — Basketball plugin discovery

- [ ] P16-AC-01: A clean checkout follows documented setup without manual database edits.
- [ ] P16-AC-02: All new environment variables appear in `.env.example` without secrets.
- [ ] P16-AC-03: All new contracts reject unknown fields.
- [ ] P16-AC-04: All migrations upgrade from the prior released head.
- [ ] P16-AC-05: All migrations are reviewed for destructive or locking behavior.
- [ ] P16-AC-06: Unit tests cover pure domain policies.
- [ ] P16-AC-07: Contract tests cover provider or API boundaries.
- [ ] P16-AC-08: Integration tests cover persistence and workflow effects.
- [ ] P16-AC-09: At least one failure/degraded path is demonstrated.
- [ ] P16-AC-10: Observability spans and metrics are asserted where practical.
- [ ] P16-AC-11: No secret or raw sensitive payload appears in logs or browser bundles.
- [ ] P16-AC-12: Requirement ledger is updated.
- [ ] P16-AC-13: README or runbook reflects operator-facing changes.
- [ ] P16-AC-14: User-visible behavior is verified in Playwright when applicable.
- [ ] P16-AC-15: The result is committed as a narrow, reviewable phase change.

### P17 acceptance checklist — Volleyball plugin discovery

- [ ] P17-AC-01: A clean checkout follows documented setup without manual database edits.
- [ ] P17-AC-02: All new environment variables appear in `.env.example` without secrets.
- [ ] P17-AC-03: All new contracts reject unknown fields.
- [ ] P17-AC-04: All migrations upgrade from the prior released head.
- [ ] P17-AC-05: All migrations are reviewed for destructive or locking behavior.
- [ ] P17-AC-06: Unit tests cover pure domain policies.
- [ ] P17-AC-07: Contract tests cover provider or API boundaries.
- [ ] P17-AC-08: Integration tests cover persistence and workflow effects.
- [ ] P17-AC-09: At least one failure/degraded path is demonstrated.
- [ ] P17-AC-10: Observability spans and metrics are asserted where practical.
- [ ] P17-AC-11: No secret or raw sensitive payload appears in logs or browser bundles.
- [ ] P17-AC-12: Requirement ledger is updated.
- [ ] P17-AC-13: README or runbook reflects operator-facing changes.
- [ ] P17-AC-14: User-visible behavior is verified in Playwright when applicable.
- [ ] P17-AC-15: The result is committed as a narrow, reviewable phase change.

## 32. Precise Codex Execution Checklist

Codex should execute the following in order and should not ask routine questions already answered by this specification.

- [ ] EXEC-0001: Confirm the workspace is the intended repository and inspect existing changes before editing.
- [ ] EXEC-0002: Read `AGENTS.md`, this specification, existing ADRs, and the requirement ledger.
- [ ] EXEC-0003: Report any direct conflict between repository reality and this specification.
- [ ] EXEC-0004: Create or update the implementation plan with one phase in progress.
- [ ] EXEC-0005: Preserve unrelated user changes.
- [ ] EXEC-0006: Create the monorepo skeleton only if it does not exist.
- [ ] EXEC-0007: Pin runtime versions and package managers.
- [ ] EXEC-0008: Add local dependency services and health checks.
- [ ] EXEC-0009: Add strict formatting, linting, typing, and test commands.
- [ ] EXEC-0010: Implement config loading with strict schemas.
- [ ] EXEC-0011: Implement model registry expiry and unknown-price rejection.
- [ ] EXEC-0012: Implement provider registry deny-by-default behavior.
- [ ] EXEC-0013: Implement injected clock and Istanbul three-day window.
- [ ] EXEC-0014: Write boundary and timezone tests before provider code.
- [ ] EXEC-0015: Implement canonical sport, competition, team, venue, and fixture entities.
- [ ] EXEC-0016: Implement provider mapping and ambiguity quarantine.
- [ ] EXEC-0017: Add fictional deterministic seed data.
- [ ] EXEC-0018: Implement mock fixture provider.
- [ ] EXEC-0019: Implement scan command and idempotency.
- [ ] EXEC-0020: Implement triage features and versioned worthwhile score.
- [ ] EXEC-0021: Implement Dashboard and scan results states.
- [ ] EXEC-0022: Verify scan in Playwright at mobile and desktop sizes.
- [ ] EXEC-0023: Implement local-first fixture search.
- [ ] EXEC-0024: Implement provider fallback search behind quota.
- [ ] EXEC-0025: Implement ambiguity-safe result selection.
- [ ] EXEC-0026: Implement fixture preflight and cost estimate.
- [ ] EXEC-0027: Enable the Dockerized Temporal services after the synchronous vertical slice is proven.
- [ ] EXEC-0028: Implement deterministic workflow and external activities.
- [ ] EXEC-0029: Implement state transition table and outbox.
- [ ] EXEC-0030: Implement SSE replay from persisted events.
- [ ] EXEC-0031: Implement cancellation and reservation release.
- [ ] EXEC-0032: Implement private object storage snapshot writer.
- [ ] EXEC-0033: Implement source snapshot hashing and provenance.
- [ ] EXEC-0034: Implement claim normalization contracts.
- [ ] EXEC-0035: Implement freshness policies and contradiction graph.
- [ ] EXEC-0036: Add prompt-injection isolation tests.
- [ ] EXEC-0037: Implement one specialist vertical slice using only mock structured data.
- [ ] EXEC-0038: Implement feature store with availability timestamps.
- [ ] EXEC-0039: Implement Elo and Poisson baselines.
- [ ] EXEC-0040: Implement probability and calibration contracts.
- [ ] EXEC-0041: Implement walk-forward backtest skeleton and leakage sentinels.
- [ ] EXEC-0042: Add remaining football specialists one at a time.
- [ ] EXEC-0043: Add each specialist critic only after the specialist golden report exists.
- [ ] EXEC-0044: Review odds provider terms before enabling its adapter.
- [ ] EXEC-0045: Implement odds snapshots as append-only partitions.
- [ ] EXEC-0046: Implement market mapping and three margin-removal methods.
- [ ] EXEC-0047: Implement live watch disabled by default.
- [ ] EXEC-0048: Implement RAG document and chunk schemas.
- [ ] EXEC-0049: Implement agent-specific retrieval policy enforcement before embeddings.
- [ ] EXEC-0050: Add pgvector and embedding versioning.
- [ ] EXEC-0051: Implement case retrieval with cutoff and outcome-leakage tests.
- [ ] EXEC-0052: Re-verify Gemini, OpenAI, and Anthropic model catalogs and prices.
- [ ] EXEC-0053: Record verification evidence and expiry.
- [ ] EXEC-0054: Run minimal capability probes with non-sensitive fixtures.
- [ ] EXEC-0055: Implement model gateway with strict routes and budgets.
- [ ] EXEC-0056: Implement schema repair limit and refusal classification.
- [ ] EXEC-0057: Implement independent critic calls.
- [ ] EXEC-0058: Implement the prediction-forbidden Sonnet Evidence Auditor.
- [ ] EXEC-0059: Implement the prediction-forbidden Sonnet Tactical Synthesizer.
- [ ] EXEC-0060: Implement the prediction-forbidden Sonnet Player and Squad Synthesizer.
- [ ] EXEC-0061: Implement the prediction-forbidden Sonnet Quant and Market Interpreter.
- [ ] EXEC-0062: Prove no pre-Chief LLM role can emit the final home/draw/away probability vector.
- [ ] EXEC-0063: Implement independent Home Win, Draw, and Away Win steelman roles.
- [ ] EXEC-0064: Implement equal-strength Scenario Red Team attacks.
- [ ] EXEC-0065: Implement mutually exclusive Scenario Engine branch validation.
- [ ] EXEC-0066: Implement Chief Analyst contract.
- [ ] EXEC-0067: Prove Chief is the first LLM stage allowed to emit final probabilities.
- [ ] EXEC-0068: Implement Final Critic approve/revise/veto contract without direct forecast mutation.
- [ ] EXEC-0069: Implement one Chief revision maximum and visible diff.
- [ ] EXEC-0070: Implement database-level immutable prediction lock.
- [ ] EXEC-0071: Implement content-addressed lock manifest and export.
- [ ] EXEC-0072: Test lock rejection at and after kickoff.
- [ ] EXEC-0073: Implement a separately namespaced LIVE MARKET collector that cannot mutate pre-match evidence.
- [ ] EXEC-0074: Implement post-match provider mock and result correction versioning.
- [ ] EXEC-0075: Implement autopsy with strict pre/post separation.
- [ ] EXEC-0076: Implement variance categories and unknown remainder.
- [ ] EXEC-0077: Implement per-thesis process scoring separately from result correctness.
- [ ] EXEC-0078: Implement versioned, sample-shrunk agent and source reliability scoring.
- [ ] EXEC-0079: Implement lesson proposal and validation.
- [ ] EXEC-0080: Implement case-memory curation and embedding.
- [ ] EXEC-0081: Implement shadow experiment assignment and separate budget.
- [ ] EXEC-0082: Implement observability dashboards and alert runbooks.
- [ ] EXEC-0083: Run full golden pipeline from scan through autopsy.
- [ ] EXEC-0084: Run lint, typecheck, unit, contract, integration, E2E, security, and backtest sentinels only through Docker Compose services.
- [ ] EXEC-0085: Inspect the actual browser UI, not only screenshots or build output.
- [ ] EXEC-0086: Verify a clean Docker-only setup from empty named volumes on a Mac with no host language runtimes.
- [ ] EXEC-0087: Update requirement traceability for every delivered requirement.
- [ ] EXEC-0088: Summarize exact files changed, tests run, known limitations, and next phase.

### 32.1 Per-file implementation loop

1. Inspect the nearest existing pattern and relevant tests.
2. Identify the requirement IDs implemented by the change.
3. Write or update the smallest failing test.
4. Implement the narrowest production change.
5. Run targeted format, lint, type, and test commands.
6. Run a broader package test after targeted success.
7. Inspect generated schemas or migrations for unintended changes.
8. Update the requirement ledger.
9. Keep unrelated files unstaged and unchanged.

## 33. Detailed Acceptance Matrix

### SCAN — three-day scan

- [ ] AC-SCAN-01: three-day scan happy path completes with typed output and audit evidence.
- [ ] AC-SCAN-02: three-day scan empty input produces an honest empty or no-publish state.
- [ ] AC-SCAN-03: three-day scan stale input is labeled and excluded where policy requires.
- [ ] AC-SCAN-04: three-day scan ambiguous input never triggers a silent heuristic decision.
- [ ] AC-SCAN-05: three-day scan provider timeout follows bounded retry policy.
- [ ] AC-SCAN-06: three-day scan idempotent replay creates no duplicate logical effect.
- [ ] AC-SCAN-07: three-day scan cutoff violation is excluded and visible in audit.
- [ ] AC-SCAN-08: three-day scan invalid structured output fails closed after one repair.
- [ ] AC-SCAN-09: three-day scan cancellation preserves completed artifacts and releases budget.
- [ ] AC-SCAN-10: three-day scan UI supports keyboard and 360 px width where applicable.
- [ ] AC-SCAN-11: three-day scan logs and events contain no secrets or raw private reasoning.
- [ ] AC-SCAN-12: three-day scan golden fixture remains deterministic under fixed clock.

### SEARCH — manual fixture search

- [ ] AC-SEARCH-01: manual fixture search happy path completes with typed output and audit evidence.
- [ ] AC-SEARCH-02: manual fixture search empty input produces an honest empty or no-publish state.
- [ ] AC-SEARCH-03: manual fixture search stale input is labeled and excluded where policy requires.
- [ ] AC-SEARCH-04: manual fixture search ambiguous input never triggers a silent heuristic decision.
- [ ] AC-SEARCH-05: manual fixture search provider timeout follows bounded retry policy.
- [ ] AC-SEARCH-06: manual fixture search idempotent replay creates no duplicate logical effect.
- [ ] AC-SEARCH-07: manual fixture search cutoff violation is excluded and visible in audit.
- [ ] AC-SEARCH-08: manual fixture search invalid structured output fails closed after one repair.
- [ ] AC-SEARCH-09: manual fixture search cancellation preserves completed artifacts and releases budget.
- [ ] AC-SEARCH-10: manual fixture search UI supports keyboard and 360 px width where applicable.
- [ ] AC-SEARCH-11: manual fixture search logs and events contain no secrets or raw private reasoning.
- [ ] AC-SEARCH-12: manual fixture search golden fixture remains deterministic under fixed clock.

### IDENTITY — canonical entity resolution

- [ ] AC-IDENTITY-01: canonical entity resolution happy path completes with typed output and audit evidence.
- [ ] AC-IDENTITY-02: canonical entity resolution empty input produces an honest empty or no-publish state.
- [ ] AC-IDENTITY-03: canonical entity resolution stale input is labeled and excluded where policy requires.
- [ ] AC-IDENTITY-04: canonical entity resolution ambiguous input never triggers a silent heuristic decision.
- [ ] AC-IDENTITY-05: canonical entity resolution provider timeout follows bounded retry policy.
- [ ] AC-IDENTITY-06: canonical entity resolution idempotent replay creates no duplicate logical effect.
- [ ] AC-IDENTITY-07: canonical entity resolution cutoff violation is excluded and visible in audit.
- [ ] AC-IDENTITY-08: canonical entity resolution invalid structured output fails closed after one repair.
- [ ] AC-IDENTITY-09: canonical entity resolution cancellation preserves completed artifacts and releases budget.
- [ ] AC-IDENTITY-10: canonical entity resolution UI supports keyboard and 360 px width where applicable.
- [ ] AC-IDENTITY-11: canonical entity resolution logs and events contain no secrets or raw private reasoning.
- [ ] AC-IDENTITY-12: canonical entity resolution golden fixture remains deterministic under fixed clock.

### PROGRESS — job progress UX

- [ ] AC-PROGRESS-01: job progress UX happy path completes with typed output and audit evidence.
- [ ] AC-PROGRESS-02: job progress UX empty input produces an honest empty or no-publish state.
- [ ] AC-PROGRESS-03: job progress UX stale input is labeled and excluded where policy requires.
- [ ] AC-PROGRESS-04: job progress UX ambiguous input never triggers a silent heuristic decision.
- [ ] AC-PROGRESS-05: job progress UX provider timeout follows bounded retry policy.
- [ ] AC-PROGRESS-06: job progress UX idempotent replay creates no duplicate logical effect.
- [ ] AC-PROGRESS-07: job progress UX cutoff violation is excluded and visible in audit.
- [ ] AC-PROGRESS-08: job progress UX invalid structured output fails closed after one repair.
- [ ] AC-PROGRESS-09: job progress UX cancellation preserves completed artifacts and releases budget.
- [ ] AC-PROGRESS-10: job progress UX UI supports keyboard and 360 px width where applicable.
- [ ] AC-PROGRESS-11: job progress UX logs and events contain no secrets or raw private reasoning.
- [ ] AC-PROGRESS-12: job progress UX golden fixture remains deterministic under fixed clock.

### EVIDENCE — provenance and claims

- [ ] AC-EVIDENCE-01: provenance and claims happy path completes with typed output and audit evidence.
- [ ] AC-EVIDENCE-02: provenance and claims empty input produces an honest empty or no-publish state.
- [ ] AC-EVIDENCE-03: provenance and claims stale input is labeled and excluded where policy requires.
- [ ] AC-EVIDENCE-04: provenance and claims ambiguous input never triggers a silent heuristic decision.
- [ ] AC-EVIDENCE-05: provenance and claims provider timeout follows bounded retry policy.
- [ ] AC-EVIDENCE-06: provenance and claims idempotent replay creates no duplicate logical effect.
- [ ] AC-EVIDENCE-07: provenance and claims cutoff violation is excluded and visible in audit.
- [ ] AC-EVIDENCE-08: provenance and claims invalid structured output fails closed after one repair.
- [ ] AC-EVIDENCE-09: provenance and claims cancellation preserves completed artifacts and releases budget.
- [ ] AC-EVIDENCE-10: provenance and claims UI supports keyboard and 360 px width where applicable.
- [ ] AC-EVIDENCE-11: provenance and claims logs and events contain no secrets or raw private reasoning.
- [ ] AC-EVIDENCE-12: provenance and claims golden fixture remains deterministic under fixed clock.

### FRESH — freshness and contradictions

- [ ] AC-FRESH-01: freshness and contradictions happy path completes with typed output and audit evidence.
- [ ] AC-FRESH-02: freshness and contradictions empty input produces an honest empty or no-publish state.
- [ ] AC-FRESH-03: freshness and contradictions stale input is labeled and excluded where policy requires.
- [ ] AC-FRESH-04: freshness and contradictions ambiguous input never triggers a silent heuristic decision.
- [ ] AC-FRESH-05: freshness and contradictions provider timeout follows bounded retry policy.
- [ ] AC-FRESH-06: freshness and contradictions idempotent replay creates no duplicate logical effect.
- [ ] AC-FRESH-07: freshness and contradictions cutoff violation is excluded and visible in audit.
- [ ] AC-FRESH-08: freshness and contradictions invalid structured output fails closed after one repair.
- [ ] AC-FRESH-09: freshness and contradictions cancellation preserves completed artifacts and releases budget.
- [ ] AC-FRESH-10: freshness and contradictions UI supports keyboard and 360 px width where applicable.
- [ ] AC-FRESH-11: freshness and contradictions logs and events contain no secrets or raw private reasoning.
- [ ] AC-FRESH-12: freshness and contradictions golden fixture remains deterministic under fixed clock.

### STATS — statistics

- [ ] AC-STATS-01: statistics happy path completes with typed output and audit evidence.
- [ ] AC-STATS-02: statistics empty input produces an honest empty or no-publish state.
- [ ] AC-STATS-03: statistics stale input is labeled and excluded where policy requires.
- [ ] AC-STATS-04: statistics ambiguous input never triggers a silent heuristic decision.
- [ ] AC-STATS-05: statistics provider timeout follows bounded retry policy.
- [ ] AC-STATS-06: statistics idempotent replay creates no duplicate logical effect.
- [ ] AC-STATS-07: statistics cutoff violation is excluded and visible in audit.
- [ ] AC-STATS-08: statistics invalid structured output fails closed after one repair.
- [ ] AC-STATS-09: statistics cancellation preserves completed artifacts and releases budget.
- [ ] AC-STATS-10: statistics UI supports keyboard and 360 px width where applicable.
- [ ] AC-STATS-11: statistics logs and events contain no secrets or raw private reasoning.
- [ ] AC-STATS-12: statistics golden fixture remains deterministic under fixed clock.

### SQUAD — players and squad

- [ ] AC-SQUAD-01: players and squad happy path completes with typed output and audit evidence.
- [ ] AC-SQUAD-02: players and squad empty input produces an honest empty or no-publish state.
- [ ] AC-SQUAD-03: players and squad stale input is labeled and excluded where policy requires.
- [ ] AC-SQUAD-04: players and squad ambiguous input never triggers a silent heuristic decision.
- [ ] AC-SQUAD-05: players and squad provider timeout follows bounded retry policy.
- [ ] AC-SQUAD-06: players and squad idempotent replay creates no duplicate logical effect.
- [ ] AC-SQUAD-07: players and squad cutoff violation is excluded and visible in audit.
- [ ] AC-SQUAD-08: players and squad invalid structured output fails closed after one repair.
- [ ] AC-SQUAD-09: players and squad cancellation preserves completed artifacts and releases budget.
- [ ] AC-SQUAD-10: players and squad UI supports keyboard and 360 px width where applicable.
- [ ] AC-SQUAD-11: players and squad logs and events contain no secrets or raw private reasoning.
- [ ] AC-SQUAD-12: players and squad golden fixture remains deterministic under fixed clock.

### TACTICS — tactics

- [ ] AC-TACTICS-01: tactics happy path completes with typed output and audit evidence.
- [ ] AC-TACTICS-02: tactics empty input produces an honest empty or no-publish state.
- [ ] AC-TACTICS-03: tactics stale input is labeled and excluded where policy requires.
- [ ] AC-TACTICS-04: tactics ambiguous input never triggers a silent heuristic decision.
- [ ] AC-TACTICS-05: tactics provider timeout follows bounded retry policy.
- [ ] AC-TACTICS-06: tactics idempotent replay creates no duplicate logical effect.
- [ ] AC-TACTICS-07: tactics cutoff violation is excluded and visible in audit.
- [ ] AC-TACTICS-08: tactics invalid structured output fails closed after one repair.
- [ ] AC-TACTICS-09: tactics cancellation preserves completed artifacts and releases budget.
- [ ] AC-TACTICS-10: tactics UI supports keyboard and 360 px width where applicable.
- [ ] AC-TACTICS-11: tactics logs and events contain no secrets or raw private reasoning.
- [ ] AC-TACTICS-12: tactics golden fixture remains deterministic under fixed clock.

### FORM — form

- [ ] AC-FORM-01: form happy path completes with typed output and audit evidence.
- [ ] AC-FORM-02: form empty input produces an honest empty or no-publish state.
- [ ] AC-FORM-03: form stale input is labeled and excluded where policy requires.
- [ ] AC-FORM-04: form ambiguous input never triggers a silent heuristic decision.
- [ ] AC-FORM-05: form provider timeout follows bounded retry policy.
- [ ] AC-FORM-06: form idempotent replay creates no duplicate logical effect.
- [ ] AC-FORM-07: form cutoff violation is excluded and visible in audit.
- [ ] AC-FORM-08: form invalid structured output fails closed after one repair.
- [ ] AC-FORM-09: form cancellation preserves completed artifacts and releases budget.
- [ ] AC-FORM-10: form UI supports keyboard and 360 px width where applicable.
- [ ] AC-FORM-11: form logs and events contain no secrets or raw private reasoning.
- [ ] AC-FORM-12: form golden fixture remains deterministic under fixed clock.

### FATIGUE — fatigue

- [ ] AC-FATIGUE-01: fatigue happy path completes with typed output and audit evidence.
- [ ] AC-FATIGUE-02: fatigue empty input produces an honest empty or no-publish state.
- [ ] AC-FATIGUE-03: fatigue stale input is labeled and excluded where policy requires.
- [ ] AC-FATIGUE-04: fatigue ambiguous input never triggers a silent heuristic decision.
- [ ] AC-FATIGUE-05: fatigue provider timeout follows bounded retry policy.
- [ ] AC-FATIGUE-06: fatigue idempotent replay creates no duplicate logical effect.
- [ ] AC-FATIGUE-07: fatigue cutoff violation is excluded and visible in audit.
- [ ] AC-FATIGUE-08: fatigue invalid structured output fails closed after one repair.
- [ ] AC-FATIGUE-09: fatigue cancellation preserves completed artifacts and releases budget.
- [ ] AC-FATIGUE-10: fatigue UI supports keyboard and 360 px width where applicable.
- [ ] AC-FATIGUE-11: fatigue logs and events contain no secrets or raw private reasoning.
- [ ] AC-FATIGUE-12: fatigue golden fixture remains deterministic under fixed clock.

### KEEPER — goalkeeper

- [ ] AC-KEEPER-01: goalkeeper happy path completes with typed output and audit evidence.
- [ ] AC-KEEPER-02: goalkeeper empty input produces an honest empty or no-publish state.
- [ ] AC-KEEPER-03: goalkeeper stale input is labeled and excluded where policy requires.
- [ ] AC-KEEPER-04: goalkeeper ambiguous input never triggers a silent heuristic decision.
- [ ] AC-KEEPER-05: goalkeeper provider timeout follows bounded retry policy.
- [ ] AC-KEEPER-06: goalkeeper idempotent replay creates no duplicate logical effect.
- [ ] AC-KEEPER-07: goalkeeper cutoff violation is excluded and visible in audit.
- [ ] AC-KEEPER-08: goalkeeper invalid structured output fails closed after one repair.
- [ ] AC-KEEPER-09: goalkeeper cancellation preserves completed artifacts and releases budget.
- [ ] AC-KEEPER-10: goalkeeper UI supports keyboard and 360 px width where applicable.
- [ ] AC-KEEPER-11: goalkeeper logs and events contain no secrets or raw private reasoning.
- [ ] AC-KEEPER-12: goalkeeper golden fixture remains deterministic under fixed clock.

### SETPIECE — set pieces

- [ ] AC-SETPIECE-01: set pieces happy path completes with typed output and audit evidence.
- [ ] AC-SETPIECE-02: set pieces empty input produces an honest empty or no-publish state.
- [ ] AC-SETPIECE-03: set pieces stale input is labeled and excluded where policy requires.
- [ ] AC-SETPIECE-04: set pieces ambiguous input never triggers a silent heuristic decision.
- [ ] AC-SETPIECE-05: set pieces provider timeout follows bounded retry policy.
- [ ] AC-SETPIECE-06: set pieces idempotent replay creates no duplicate logical effect.
- [ ] AC-SETPIECE-07: set pieces cutoff violation is excluded and visible in audit.
- [ ] AC-SETPIECE-08: set pieces invalid structured output fails closed after one repair.
- [ ] AC-SETPIECE-09: set pieces cancellation preserves completed artifacts and releases budget.
- [ ] AC-SETPIECE-10: set pieces UI supports keyboard and 360 px width where applicable.
- [ ] AC-SETPIECE-11: set pieces logs and events contain no secrets or raw private reasoning.
- [ ] AC-SETPIECE-12: set pieces golden fixture remains deterministic under fixed clock.

### ENV — environment

- [ ] AC-ENV-01: environment happy path completes with typed output and audit evidence.
- [ ] AC-ENV-02: environment empty input produces an honest empty or no-publish state.
- [ ] AC-ENV-03: environment stale input is labeled and excluded where policy requires.
- [ ] AC-ENV-04: environment ambiguous input never triggers a silent heuristic decision.
- [ ] AC-ENV-05: environment provider timeout follows bounded retry policy.
- [ ] AC-ENV-06: environment idempotent replay creates no duplicate logical effect.
- [ ] AC-ENV-07: environment cutoff violation is excluded and visible in audit.
- [ ] AC-ENV-08: environment invalid structured output fails closed after one repair.
- [ ] AC-ENV-09: environment cancellation preserves completed artifacts and releases budget.
- [ ] AC-ENV-10: environment UI supports keyboard and 360 px width where applicable.
- [ ] AC-ENV-11: environment logs and events contain no secrets or raw private reasoning.
- [ ] AC-ENV-12: environment golden fixture remains deterministic under fixed clock.

### ODDS — market intelligence

- [ ] AC-ODDS-01: market intelligence happy path completes with typed output and audit evidence.
- [ ] AC-ODDS-02: market intelligence empty input produces an honest empty or no-publish state.
- [ ] AC-ODDS-03: market intelligence stale input is labeled and excluded where policy requires.
- [ ] AC-ODDS-04: market intelligence ambiguous input never triggers a silent heuristic decision.
- [ ] AC-ODDS-05: market intelligence provider timeout follows bounded retry policy.
- [ ] AC-ODDS-06: market intelligence idempotent replay creates no duplicate logical effect.
- [ ] AC-ODDS-07: market intelligence cutoff violation is excluded and visible in audit.
- [ ] AC-ODDS-08: market intelligence invalid structured output fails closed after one repair.
- [ ] AC-ODDS-09: market intelligence cancellation preserves completed artifacts and releases budget.
- [ ] AC-ODDS-10: market intelligence UI supports keyboard and 360 px width where applicable.
- [ ] AC-ODDS-11: market intelligence logs and events contain no secrets or raw private reasoning.
- [ ] AC-ODDS-12: market intelligence golden fixture remains deterministic under fixed clock.

### QUANT — quant models

- [ ] AC-QUANT-01: quant models happy path completes with typed output and audit evidence.
- [ ] AC-QUANT-02: quant models empty input produces an honest empty or no-publish state.
- [ ] AC-QUANT-03: quant models stale input is labeled and excluded where policy requires.
- [ ] AC-QUANT-04: quant models ambiguous input never triggers a silent heuristic decision.
- [ ] AC-QUANT-05: quant models provider timeout follows bounded retry policy.
- [ ] AC-QUANT-06: quant models idempotent replay creates no duplicate logical effect.
- [ ] AC-QUANT-07: quant models cutoff violation is excluded and visible in audit.
- [ ] AC-QUANT-08: quant models invalid structured output fails closed after one repair.
- [ ] AC-QUANT-09: quant models cancellation preserves completed artifacts and releases budget.
- [ ] AC-QUANT-10: quant models UI supports keyboard and 360 px width where applicable.
- [ ] AC-QUANT-11: quant models logs and events contain no secrets or raw private reasoning.
- [ ] AC-QUANT-12: quant models golden fixture remains deterministic under fixed clock.

### SIM — historical similarity

- [ ] AC-SIM-01: historical similarity happy path completes with typed output and audit evidence.
- [ ] AC-SIM-02: historical similarity empty input produces an honest empty or no-publish state.
- [ ] AC-SIM-03: historical similarity stale input is labeled and excluded where policy requires.
- [ ] AC-SIM-04: historical similarity ambiguous input never triggers a silent heuristic decision.
- [ ] AC-SIM-05: historical similarity provider timeout follows bounded retry policy.
- [ ] AC-SIM-06: historical similarity idempotent replay creates no duplicate logical effect.
- [ ] AC-SIM-07: historical similarity cutoff violation is excluded and visible in audit.
- [ ] AC-SIM-08: historical similarity invalid structured output fails closed after one repair.
- [ ] AC-SIM-09: historical similarity cancellation preserves completed artifacts and releases budget.
- [ ] AC-SIM-10: historical similarity UI supports keyboard and 360 px width where applicable.
- [ ] AC-SIM-11: historical similarity logs and events contain no secrets or raw private reasoning.
- [ ] AC-SIM-12: historical similarity golden fixture remains deterministic under fixed clock.

### CRITIC — critics

- [ ] AC-CRITIC-01: critics happy path completes with typed output and audit evidence.
- [ ] AC-CRITIC-02: critics empty input produces an honest empty or no-publish state.
- [ ] AC-CRITIC-03: critics stale input is labeled and excluded where policy requires.
- [ ] AC-CRITIC-04: critics ambiguous input never triggers a silent heuristic decision.
- [ ] AC-CRITIC-05: critics provider timeout follows bounded retry policy.
- [ ] AC-CRITIC-06: critics idempotent replay creates no duplicate logical effect.
- [ ] AC-CRITIC-07: critics cutoff violation is excluded and visible in audit.
- [ ] AC-CRITIC-08: critics invalid structured output fails closed after one repair.
- [ ] AC-CRITIC-09: critics cancellation preserves completed artifacts and releases budget.
- [ ] AC-CRITIC-10: critics UI supports keyboard and 360 px width where applicable.
- [ ] AC-CRITIC-11: critics logs and events contain no secrets or raw private reasoning.
- [ ] AC-CRITIC-12: critics golden fixture remains deterministic under fixed clock.

### COMMITTEE — Sonnet committee

- [ ] AC-COMMITTEE-01: Sonnet committee happy path completes with typed output and audit evidence.
- [ ] AC-COMMITTEE-02: Sonnet committee empty input produces an honest empty or no-publish state.
- [ ] AC-COMMITTEE-03: Sonnet committee stale input is labeled and excluded where policy requires.
- [ ] AC-COMMITTEE-04: Sonnet committee ambiguous input never triggers a silent heuristic decision.
- [ ] AC-COMMITTEE-05: Sonnet committee provider timeout follows bounded retry policy.
- [ ] AC-COMMITTEE-06: Sonnet committee idempotent replay creates no duplicate logical effect.
- [ ] AC-COMMITTEE-07: Sonnet committee cutoff violation is excluded and visible in audit.
- [ ] AC-COMMITTEE-08: Sonnet committee invalid structured output fails closed after one repair.
- [ ] AC-COMMITTEE-09: Sonnet committee cancellation preserves completed artifacts and releases budget.
- [ ] AC-COMMITTEE-10: Sonnet committee UI supports keyboard and 360 px width where applicable.
- [ ] AC-COMMITTEE-11: Sonnet committee logs and events contain no secrets or raw private reasoning.
- [ ] AC-COMMITTEE-12: Sonnet committee golden fixture remains deterministic under fixed clock.

### SCENARIO — scenario steelman

- [ ] AC-SCENARIO-01: scenario steelman happy path completes with typed output and audit evidence.
- [ ] AC-SCENARIO-02: scenario steelman empty input produces an honest empty or no-publish state.
- [ ] AC-SCENARIO-03: scenario steelman stale input is labeled and excluded where policy requires.
- [ ] AC-SCENARIO-04: scenario steelman ambiguous input never triggers a silent heuristic decision.
- [ ] AC-SCENARIO-05: scenario steelman provider timeout follows bounded retry policy.
- [ ] AC-SCENARIO-06: scenario steelman idempotent replay creates no duplicate logical effect.
- [ ] AC-SCENARIO-07: scenario steelman cutoff violation is excluded and visible in audit.
- [ ] AC-SCENARIO-08: scenario steelman invalid structured output fails closed after one repair.
- [ ] AC-SCENARIO-09: scenario steelman cancellation preserves completed artifacts and releases budget.
- [ ] AC-SCENARIO-10: scenario steelman UI supports keyboard and 360 px width where applicable.
- [ ] AC-SCENARIO-11: scenario steelman logs and events contain no secrets or raw private reasoning.
- [ ] AC-SCENARIO-12: scenario steelman golden fixture remains deterministic under fixed clock.

### REDTEAM — red team

- [ ] AC-REDTEAM-01: red team happy path completes with typed output and audit evidence.
- [ ] AC-REDTEAM-02: red team empty input produces an honest empty or no-publish state.
- [ ] AC-REDTEAM-03: red team stale input is labeled and excluded where policy requires.
- [ ] AC-REDTEAM-04: red team ambiguous input never triggers a silent heuristic decision.
- [ ] AC-REDTEAM-05: red team provider timeout follows bounded retry policy.
- [ ] AC-REDTEAM-06: red team idempotent replay creates no duplicate logical effect.
- [ ] AC-REDTEAM-07: red team cutoff violation is excluded and visible in audit.
- [ ] AC-REDTEAM-08: red team invalid structured output fails closed after one repair.
- [ ] AC-REDTEAM-09: red team cancellation preserves completed artifacts and releases budget.
- [ ] AC-REDTEAM-10: red team UI supports keyboard and 360 px width where applicable.
- [ ] AC-REDTEAM-11: red team logs and events contain no secrets or raw private reasoning.
- [ ] AC-REDTEAM-12: red team golden fixture remains deterministic under fixed clock.

### CHIEF — Chief Analyst

- [ ] AC-CHIEF-01: Chief Analyst happy path completes with typed output and audit evidence.
- [ ] AC-CHIEF-02: Chief Analyst empty input produces an honest empty or no-publish state.
- [ ] AC-CHIEF-03: Chief Analyst stale input is labeled and excluded where policy requires.
- [ ] AC-CHIEF-04: Chief Analyst ambiguous input never triggers a silent heuristic decision.
- [ ] AC-CHIEF-05: Chief Analyst provider timeout follows bounded retry policy.
- [ ] AC-CHIEF-06: Chief Analyst idempotent replay creates no duplicate logical effect.
- [ ] AC-CHIEF-07: Chief Analyst cutoff violation is excluded and visible in audit.
- [ ] AC-CHIEF-08: Chief Analyst invalid structured output fails closed after one repair.
- [ ] AC-CHIEF-09: Chief Analyst cancellation preserves completed artifacts and releases budget.
- [ ] AC-CHIEF-10: Chief Analyst UI supports keyboard and 360 px width where applicable.
- [ ] AC-CHIEF-11: Chief Analyst logs and events contain no secrets or raw private reasoning.
- [ ] AC-CHIEF-12: Chief Analyst golden fixture remains deterministic under fixed clock.

### FINAL — Final Critic

- [ ] AC-FINAL-01: Final Critic happy path completes with typed output and audit evidence.
- [ ] AC-FINAL-02: Final Critic empty input produces an honest empty or no-publish state.
- [ ] AC-FINAL-03: Final Critic stale input is labeled and excluded where policy requires.
- [ ] AC-FINAL-04: Final Critic ambiguous input never triggers a silent heuristic decision.
- [ ] AC-FINAL-05: Final Critic provider timeout follows bounded retry policy.
- [ ] AC-FINAL-06: Final Critic idempotent replay creates no duplicate logical effect.
- [ ] AC-FINAL-07: Final Critic cutoff violation is excluded and visible in audit.
- [ ] AC-FINAL-08: Final Critic invalid structured output fails closed after one repair.
- [ ] AC-FINAL-09: Final Critic cancellation preserves completed artifacts and releases budget.
- [ ] AC-FINAL-10: Final Critic UI supports keyboard and 360 px width where applicable.
- [ ] AC-FINAL-11: Final Critic logs and events contain no secrets or raw private reasoning.
- [ ] AC-FINAL-12: Final Critic golden fixture remains deterministic under fixed clock.

### LOCK — prediction lock

- [ ] AC-LOCK-01: prediction lock happy path completes with typed output and audit evidence.
- [ ] AC-LOCK-02: prediction lock empty input produces an honest empty or no-publish state.
- [ ] AC-LOCK-03: prediction lock stale input is labeled and excluded where policy requires.
- [ ] AC-LOCK-04: prediction lock ambiguous input never triggers a silent heuristic decision.
- [ ] AC-LOCK-05: prediction lock provider timeout follows bounded retry policy.
- [ ] AC-LOCK-06: prediction lock idempotent replay creates no duplicate logical effect.
- [ ] AC-LOCK-07: prediction lock cutoff violation is excluded and visible in audit.
- [ ] AC-LOCK-08: prediction lock invalid structured output fails closed after one repair.
- [ ] AC-LOCK-09: prediction lock cancellation preserves completed artifacts and releases budget.
- [ ] AC-LOCK-10: prediction lock UI supports keyboard and 360 px width where applicable.
- [ ] AC-LOCK-11: prediction lock logs and events contain no secrets or raw private reasoning.
- [ ] AC-LOCK-12: prediction lock golden fixture remains deterministic under fixed clock.

### POST — post-match ingestion

- [ ] AC-POST-01: post-match ingestion happy path completes with typed output and audit evidence.
- [ ] AC-POST-02: post-match ingestion empty input produces an honest empty or no-publish state.
- [ ] AC-POST-03: post-match ingestion stale input is labeled and excluded where policy requires.
- [ ] AC-POST-04: post-match ingestion ambiguous input never triggers a silent heuristic decision.
- [ ] AC-POST-05: post-match ingestion provider timeout follows bounded retry policy.
- [ ] AC-POST-06: post-match ingestion idempotent replay creates no duplicate logical effect.
- [ ] AC-POST-07: post-match ingestion cutoff violation is excluded and visible in audit.
- [ ] AC-POST-08: post-match ingestion invalid structured output fails closed after one repair.
- [ ] AC-POST-09: post-match ingestion cancellation preserves completed artifacts and releases budget.
- [ ] AC-POST-10: post-match ingestion UI supports keyboard and 360 px width where applicable.
- [ ] AC-POST-11: post-match ingestion logs and events contain no secrets or raw private reasoning.
- [ ] AC-POST-12: post-match ingestion golden fixture remains deterministic under fixed clock.

### AUTOPSY — autopsy

- [ ] AC-AUTOPSY-01: autopsy happy path completes with typed output and audit evidence.
- [ ] AC-AUTOPSY-02: autopsy empty input produces an honest empty or no-publish state.
- [ ] AC-AUTOPSY-03: autopsy stale input is labeled and excluded where policy requires.
- [ ] AC-AUTOPSY-04: autopsy ambiguous input never triggers a silent heuristic decision.
- [ ] AC-AUTOPSY-05: autopsy provider timeout follows bounded retry policy.
- [ ] AC-AUTOPSY-06: autopsy idempotent replay creates no duplicate logical effect.
- [ ] AC-AUTOPSY-07: autopsy cutoff violation is excluded and visible in audit.
- [ ] AC-AUTOPSY-08: autopsy invalid structured output fails closed after one repair.
- [ ] AC-AUTOPSY-09: autopsy cancellation preserves completed artifacts and releases budget.
- [ ] AC-AUTOPSY-10: autopsy UI supports keyboard and 360 px width where applicable.
- [ ] AC-AUTOPSY-11: autopsy logs and events contain no secrets or raw private reasoning.
- [ ] AC-AUTOPSY-12: autopsy golden fixture remains deterministic under fixed clock.

### VARIANCE — variance analysis

- [ ] AC-VARIANCE-01: variance analysis happy path completes with typed output and audit evidence.
- [ ] AC-VARIANCE-02: variance analysis empty input produces an honest empty or no-publish state.
- [ ] AC-VARIANCE-03: variance analysis stale input is labeled and excluded where policy requires.
- [ ] AC-VARIANCE-04: variance analysis ambiguous input never triggers a silent heuristic decision.
- [ ] AC-VARIANCE-05: variance analysis provider timeout follows bounded retry policy.
- [ ] AC-VARIANCE-06: variance analysis idempotent replay creates no duplicate logical effect.
- [ ] AC-VARIANCE-07: variance analysis cutoff violation is excluded and visible in audit.
- [ ] AC-VARIANCE-08: variance analysis invalid structured output fails closed after one repair.
- [ ] AC-VARIANCE-09: variance analysis cancellation preserves completed artifacts and releases budget.
- [ ] AC-VARIANCE-10: variance analysis UI supports keyboard and 360 px width where applicable.
- [ ] AC-VARIANCE-11: variance analysis logs and events contain no secrets or raw private reasoning.
- [ ] AC-VARIANCE-12: variance analysis golden fixture remains deterministic under fixed clock.

### LESSON — lesson extraction

- [ ] AC-LESSON-01: lesson extraction happy path completes with typed output and audit evidence.
- [ ] AC-LESSON-02: lesson extraction empty input produces an honest empty or no-publish state.
- [ ] AC-LESSON-03: lesson extraction stale input is labeled and excluded where policy requires.
- [ ] AC-LESSON-04: lesson extraction ambiguous input never triggers a silent heuristic decision.
- [ ] AC-LESSON-05: lesson extraction provider timeout follows bounded retry policy.
- [ ] AC-LESSON-06: lesson extraction idempotent replay creates no duplicate logical effect.
- [ ] AC-LESSON-07: lesson extraction cutoff violation is excluded and visible in audit.
- [ ] AC-LESSON-08: lesson extraction invalid structured output fails closed after one repair.
- [ ] AC-LESSON-09: lesson extraction cancellation preserves completed artifacts and releases budget.
- [ ] AC-LESSON-10: lesson extraction UI supports keyboard and 360 px width where applicable.
- [ ] AC-LESSON-11: lesson extraction logs and events contain no secrets or raw private reasoning.
- [ ] AC-LESSON-12: lesson extraction golden fixture remains deterministic under fixed clock.

### MEMORY — case memory

- [ ] AC-MEMORY-01: case memory happy path completes with typed output and audit evidence.
- [ ] AC-MEMORY-02: case memory empty input produces an honest empty or no-publish state.
- [ ] AC-MEMORY-03: case memory stale input is labeled and excluded where policy requires.
- [ ] AC-MEMORY-04: case memory ambiguous input never triggers a silent heuristic decision.
- [ ] AC-MEMORY-05: case memory provider timeout follows bounded retry policy.
- [ ] AC-MEMORY-06: case memory idempotent replay creates no duplicate logical effect.
- [ ] AC-MEMORY-07: case memory cutoff violation is excluded and visible in audit.
- [ ] AC-MEMORY-08: case memory invalid structured output fails closed after one repair.
- [ ] AC-MEMORY-09: case memory cancellation preserves completed artifacts and releases budget.
- [ ] AC-MEMORY-10: case memory UI supports keyboard and 360 px width where applicable.
- [ ] AC-MEMORY-11: case memory logs and events contain no secrets or raw private reasoning.
- [ ] AC-MEMORY-12: case memory golden fixture remains deterministic under fixed clock.

### RAG — retrieval

- [ ] AC-RAG-01: retrieval happy path completes with typed output and audit evidence.
- [ ] AC-RAG-02: retrieval empty input produces an honest empty or no-publish state.
- [ ] AC-RAG-03: retrieval stale input is labeled and excluded where policy requires.
- [ ] AC-RAG-04: retrieval ambiguous input never triggers a silent heuristic decision.
- [ ] AC-RAG-05: retrieval provider timeout follows bounded retry policy.
- [ ] AC-RAG-06: retrieval idempotent replay creates no duplicate logical effect.
- [ ] AC-RAG-07: retrieval cutoff violation is excluded and visible in audit.
- [ ] AC-RAG-08: retrieval invalid structured output fails closed after one repair.
- [ ] AC-RAG-09: retrieval cancellation preserves completed artifacts and releases budget.
- [ ] AC-RAG-10: retrieval UI supports keyboard and 360 px width where applicable.
- [ ] AC-RAG-11: retrieval logs and events contain no secrets or raw private reasoning.
- [ ] AC-RAG-12: retrieval golden fixture remains deterministic under fixed clock.

### BUDGET — cost control

- [ ] AC-BUDGET-01: cost control happy path completes with typed output and audit evidence.
- [ ] AC-BUDGET-02: cost control empty input produces an honest empty or no-publish state.
- [ ] AC-BUDGET-03: cost control stale input is labeled and excluded where policy requires.
- [ ] AC-BUDGET-04: cost control ambiguous input never triggers a silent heuristic decision.
- [ ] AC-BUDGET-05: cost control provider timeout follows bounded retry policy.
- [ ] AC-BUDGET-06: cost control idempotent replay creates no duplicate logical effect.
- [ ] AC-BUDGET-07: cost control cutoff violation is excluded and visible in audit.
- [ ] AC-BUDGET-08: cost control invalid structured output fails closed after one repair.
- [ ] AC-BUDGET-09: cost control cancellation preserves completed artifacts and releases budget.
- [ ] AC-BUDGET-10: cost control UI supports keyboard and 360 px width where applicable.
- [ ] AC-BUDGET-11: cost control logs and events contain no secrets or raw private reasoning.
- [ ] AC-BUDGET-12: cost control golden fixture remains deterministic under fixed clock.

### MODELS — model registry

- [ ] AC-MODELS-01: model registry happy path completes with typed output and audit evidence.
- [ ] AC-MODELS-02: model registry empty input produces an honest empty or no-publish state.
- [ ] AC-MODELS-03: model registry stale input is labeled and excluded where policy requires.
- [ ] AC-MODELS-04: model registry ambiguous input never triggers a silent heuristic decision.
- [ ] AC-MODELS-05: model registry provider timeout follows bounded retry policy.
- [ ] AC-MODELS-06: model registry idempotent replay creates no duplicate logical effect.
- [ ] AC-MODELS-07: model registry cutoff violation is excluded and visible in audit.
- [ ] AC-MODELS-08: model registry invalid structured output fails closed after one repair.
- [ ] AC-MODELS-09: model registry cancellation preserves completed artifacts and releases budget.
- [ ] AC-MODELS-10: model registry UI supports keyboard and 360 px width where applicable.
- [ ] AC-MODELS-11: model registry logs and events contain no secrets or raw private reasoning.
- [ ] AC-MODELS-12: model registry golden fixture remains deterministic under fixed clock.

### PROVIDERS — provider compliance

- [ ] AC-PROVIDERS-01: provider compliance happy path completes with typed output and audit evidence.
- [ ] AC-PROVIDERS-02: provider compliance empty input produces an honest empty or no-publish state.
- [ ] AC-PROVIDERS-03: provider compliance stale input is labeled and excluded where policy requires.
- [ ] AC-PROVIDERS-04: provider compliance ambiguous input never triggers a silent heuristic decision.
- [ ] AC-PROVIDERS-05: provider compliance provider timeout follows bounded retry policy.
- [ ] AC-PROVIDERS-06: provider compliance idempotent replay creates no duplicate logical effect.
- [ ] AC-PROVIDERS-07: provider compliance cutoff violation is excluded and visible in audit.
- [ ] AC-PROVIDERS-08: provider compliance invalid structured output fails closed after one repair.
- [ ] AC-PROVIDERS-09: provider compliance cancellation preserves completed artifacts and releases budget.
- [ ] AC-PROVIDERS-10: provider compliance UI supports keyboard and 360 px width where applicable.
- [ ] AC-PROVIDERS-11: provider compliance logs and events contain no secrets or raw private reasoning.
- [ ] AC-PROVIDERS-12: provider compliance golden fixture remains deterministic under fixed clock.

### SECURITY — security

- [ ] AC-SECURITY-01: security happy path completes with typed output and audit evidence.
- [ ] AC-SECURITY-02: security empty input produces an honest empty or no-publish state.
- [ ] AC-SECURITY-03: security stale input is labeled and excluded where policy requires.
- [ ] AC-SECURITY-04: security ambiguous input never triggers a silent heuristic decision.
- [ ] AC-SECURITY-05: security provider timeout follows bounded retry policy.
- [ ] AC-SECURITY-06: security idempotent replay creates no duplicate logical effect.
- [ ] AC-SECURITY-07: security cutoff violation is excluded and visible in audit.
- [ ] AC-SECURITY-08: security invalid structured output fails closed after one repair.
- [ ] AC-SECURITY-09: security cancellation preserves completed artifacts and releases budget.
- [ ] AC-SECURITY-10: security UI supports keyboard and 360 px width where applicable.
- [ ] AC-SECURITY-11: security logs and events contain no secrets or raw private reasoning.
- [ ] AC-SECURITY-12: security golden fixture remains deterministic under fixed clock.

### OBS — observability

- [ ] AC-OBS-01: observability happy path completes with typed output and audit evidence.
- [ ] AC-OBS-02: observability empty input produces an honest empty or no-publish state.
- [ ] AC-OBS-03: observability stale input is labeled and excluded where policy requires.
- [ ] AC-OBS-04: observability ambiguous input never triggers a silent heuristic decision.
- [ ] AC-OBS-05: observability provider timeout follows bounded retry policy.
- [ ] AC-OBS-06: observability idempotent replay creates no duplicate logical effect.
- [ ] AC-OBS-07: observability cutoff violation is excluded and visible in audit.
- [ ] AC-OBS-08: observability invalid structured output fails closed after one repair.
- [ ] AC-OBS-09: observability cancellation preserves completed artifacts and releases budget.
- [ ] AC-OBS-10: observability UI supports keyboard and 360 px width where applicable.
- [ ] AC-OBS-11: observability logs and events contain no secrets or raw private reasoning.
- [ ] AC-OBS-12: observability golden fixture remains deterministic under fixed clock.

### SETUP — local setup

- [ ] AC-SETUP-01: local setup happy path completes with typed output and audit evidence.
- [ ] AC-SETUP-02: local setup empty input produces an honest empty or no-publish state.
- [ ] AC-SETUP-03: local setup stale input is labeled and excluded where policy requires.
- [ ] AC-SETUP-04: local setup ambiguous input never triggers a silent heuristic decision.
- [ ] AC-SETUP-05: local setup provider timeout follows bounded retry policy.
- [ ] AC-SETUP-06: local setup idempotent replay creates no duplicate logical effect.
- [ ] AC-SETUP-07: local setup cutoff violation is excluded and visible in audit.
- [ ] AC-SETUP-08: local setup invalid structured output fails closed after one repair.
- [ ] AC-SETUP-09: local setup cancellation preserves completed artifacts and releases budget.
- [ ] AC-SETUP-10: local setup UI supports keyboard and 360 px width where applicable.
- [ ] AC-SETUP-11: local setup logs and events contain no secrets or raw private reasoning.
- [ ] AC-SETUP-12: local setup golden fixture remains deterministic under fixed clock.

### SPORT — sport extensibility

- [ ] AC-SPORT-01: sport extensibility happy path completes with typed output and audit evidence.
- [ ] AC-SPORT-02: sport extensibility empty input produces an honest empty or no-publish state.
- [ ] AC-SPORT-03: sport extensibility stale input is labeled and excluded where policy requires.
- [ ] AC-SPORT-04: sport extensibility ambiguous input never triggers a silent heuristic decision.
- [ ] AC-SPORT-05: sport extensibility provider timeout follows bounded retry policy.
- [ ] AC-SPORT-06: sport extensibility idempotent replay creates no duplicate logical effect.
- [ ] AC-SPORT-07: sport extensibility cutoff violation is excluded and visible in audit.
- [ ] AC-SPORT-08: sport extensibility invalid structured output fails closed after one repair.
- [ ] AC-SPORT-09: sport extensibility cancellation preserves completed artifacts and releases budget.
- [ ] AC-SPORT-10: sport extensibility UI supports keyboard and 360 px width where applicable.
- [ ] AC-SPORT-11: sport extensibility logs and events contain no secrets or raw private reasoning.
- [ ] AC-SPORT-12: sport extensibility golden fixture remains deterministic under fixed clock.

## 34. Operational Runbooks

### RB-001 — Expired model verification

- Immediate action: Disable affected route, recheck official catalog/pricing, probe, update config, resume.
- Confirm scope using correlation IDs, provider request IDs, and immutable audit events.
- Preserve forensic evidence without copying secrets or restricted raw content.
- Communicate user-visible impact in plain language.
- Restore service through the narrowest safe change.
- Verify the real end-to-end surface after recovery.
- Record root cause, detection gap, corrective action, owner, and due date.
- File: `docs/runbooks/rb-001-expired-model-verification.md`.

### RB-002 — Provider authentication failure

- Immediate action: Disable adapter, rotate/reconfigure key, probe without logging secret.
- Confirm scope using correlation IDs, provider request IDs, and immutable audit events.
- Preserve forensic evidence without copying secrets or restricted raw content.
- Communicate user-visible impact in plain language.
- Restore service through the narrowest safe change.
- Verify the real end-to-end surface after recovery.
- Record root cause, detection gap, corrective action, owner, and due date.
- File: `docs/runbooks/rb-002-provider-authentication-failure.md`.

### RB-003 — Provider quota exhaustion

- Immediate action: Stop watch/scan calls, expose reset information, preserve budget.
- Confirm scope using correlation IDs, provider request IDs, and immutable audit events.
- Preserve forensic evidence without copying secrets or restricted raw content.
- Communicate user-visible impact in plain language.
- Restore service through the narrowest safe change.
- Verify the real end-to-end surface after recovery.
- Record root cause, detection gap, corrective action, owner, and due date.
- File: `docs/runbooks/rb-003-provider-quota-exhaustion.md`.

### RB-004 — Workflow stuck

- Immediate action: Inspect Temporal history, activity heartbeat, provider status, and cancellation safety.
- Confirm scope using correlation IDs, provider request IDs, and immutable audit events.
- Preserve forensic evidence without copying secrets or restricted raw content.
- Communicate user-visible impact in plain language.
- Restore service through the narrowest safe change.
- Verify the real end-to-end surface after recovery.
- Record root cause, detection gap, corrective action, owner, and due date.
- File: `docs/runbooks/rb-004-workflow-stuck.md`.

### RB-005 — Database migration failure

- Immediate action: Stop deployment, inspect migration transaction and compatibility; never reset data.
- Confirm scope using correlation IDs, provider request IDs, and immutable audit events.
- Preserve forensic evidence without copying secrets or restricted raw content.
- Communicate user-visible impact in plain language.
- Restore service through the narrowest safe change.
- Verify the real end-to-end surface after recovery.
- Record root cause, detection gap, corrective action, owner, and due date.
- File: `docs/runbooks/rb-005-database-migration-failure.md`.

### RB-006 — Object hash mismatch

- Immediate action: Quarantine artifact, block claim/lock use, investigate storage integrity.
- Confirm scope using correlation IDs, provider request IDs, and immutable audit events.
- Preserve forensic evidence without copying secrets or restricted raw content.
- Communicate user-visible impact in plain language.
- Restore service through the narrowest safe change.
- Verify the real end-to-end surface after recovery.
- Record root cause, detection gap, corrective action, owner, and due date.
- File: `docs/runbooks/rb-006-object-hash-mismatch.md`.

### RB-007 — Prediction lock failure

- Immediate action: Do not display locked state; preserve approved forecast and retry only before kickoff.
- Confirm scope using correlation IDs, provider request IDs, and immutable audit events.
- Preserve forensic evidence without copying secrets or restricted raw content.
- Communicate user-visible impact in plain language.
- Restore service through the narrowest safe change.
- Verify the real end-to-end surface after recovery.
- Record root cause, detection gap, corrective action, owner, and due date.
- File: `docs/runbooks/rb-007-prediction-lock-failure.md`.

### RB-008 — Cutoff breach alert

- Immediate action: Block publish, identify affected artifacts, invalidate run, test sentinel.
- Confirm scope using correlation IDs, provider request IDs, and immutable audit events.
- Preserve forensic evidence without copying secrets or restricted raw content.
- Communicate user-visible impact in plain language.
- Restore service through the narrowest safe change.
- Verify the real end-to-end surface after recovery.
- Record root cause, detection gap, corrective action, owner, and due date.
- File: `docs/runbooks/rb-008-cutoff-breach-alert.md`.

### RB-009 — Fixture identity collision

- Immediate action: Quarantine mappings, compare provider evidence, resolve explicitly.
- Confirm scope using correlation IDs, provider request IDs, and immutable audit events.
- Preserve forensic evidence without copying secrets or restricted raw content.
- Communicate user-visible impact in plain language.
- Restore service through the narrowest safe change.
- Verify the real end-to-end surface after recovery.
- Record root cause, detection gap, corrective action, owner, and due date.
- File: `docs/runbooks/rb-009-fixture-identity-collision.md`.

### RB-010 — Unexpected cost spike

- Immediate action: Trip budget breaker, inspect token/tool/provider attribution, disable route.
- Confirm scope using correlation IDs, provider request IDs, and immutable audit events.
- Preserve forensic evidence without copying secrets or restricted raw content.
- Communicate user-visible impact in plain language.
- Restore service through the narrowest safe change.
- Verify the real end-to-end surface after recovery.
- Record root cause, detection gap, corrective action, owner, and due date.
- File: `docs/runbooks/rb-010-unexpected-cost-spike.md`.

### RB-011 — Prompt schema drift

- Immediate action: Pin prompt/schema, reproduce with golden packet, update eval before release.
- Confirm scope using correlation IDs, provider request IDs, and immutable audit events.
- Preserve forensic evidence without copying secrets or restricted raw content.
- Communicate user-visible impact in plain language.
- Restore service through the narrowest safe change.
- Verify the real end-to-end surface after recovery.
- Record root cause, detection gap, corrective action, owner, and due date.
- File: `docs/runbooks/rb-011-prompt-schema-drift.md`.

### RB-012 — SSE outage

- Immediate action: Runs continue; clients poll summary and reconnect from last event ID.
- Confirm scope using correlation IDs, provider request IDs, and immutable audit events.
- Preserve forensic evidence without copying secrets or restricted raw content.
- Communicate user-visible impact in plain language.
- Restore service through the narrowest safe change.
- Verify the real end-to-end surface after recovery.
- Record root cause, detection gap, corrective action, owner, and due date.
- File: `docs/runbooks/rb-012-sse-outage.md`.

### RB-013 — Result correction

- Immediate action: Append corrected result version and rerun autopsy as new version without changing lock.
- Confirm scope using correlation IDs, provider request IDs, and immutable audit events.
- Preserve forensic evidence without copying secrets or restricted raw content.
- Communicate user-visible impact in plain language.
- Restore service through the narrowest safe change.
- Verify the real end-to-end surface after recovery.
- Record root cause, detection gap, corrective action, owner, and due date.
- File: `docs/runbooks/rb-013-result-correction.md`.

### RB-014 — License/terms change

- Immediate action: Disable provider, apply retention policy, select reviewed alternative.
- Confirm scope using correlation IDs, provider request IDs, and immutable audit events.
- Preserve forensic evidence without copying secrets or restricted raw content.
- Communicate user-visible impact in plain language.
- Restore service through the narrowest safe change.
- Verify the real end-to-end surface after recovery.
- Record root cause, detection gap, corrective action, owner, and due date.
- File: `docs/runbooks/rb-014-license-terms-change.md`.

### RB-015 — Secret exposure suspicion

- Immediate action: Revoke, rotate, audit access, scrub allowed caches, document incident.
- Confirm scope using correlation IDs, provider request IDs, and immutable audit events.
- Preserve forensic evidence without copying secrets or restricted raw content.
- Communicate user-visible impact in plain language.
- Restore service through the narrowest safe change.
- Verify the real end-to-end surface after recovery.
- Record root cause, detection gap, corrective action, owner, and due date.
- File: `docs/runbooks/rb-015-secret-exposure-suspicion.md`.

## 35. Sport Extensibility Contract

```python
class SportPlugin(Protocol):
    sport_key: str
    outcome_schema_version: str

    def validate_fixture(self, fixture: CanonicalFixture) -> None: ...
    def canonical_markets(self) -> tuple[MarketDefinition, ...]: ...
    def feature_definitions(self) -> tuple[FeatureDefinition, ...]: ...
    def build_features(self, context: FeatureContext) -> FeatureBundle: ...
    def baseline_models(self) -> tuple[QuantModelDefinition, ...]: ...
    def scenario_taxonomy(self) -> tuple[ScenarioDefinition, ...]: ...
    def result_semantics(self) -> ResultSemantics: ...
    def autopsy_rules(self) -> tuple[AutopsyRule, ...]: ...
```

- Football implements three-way regulation-time outcomes and goal models.
- Basketball will implement two-way winner, spreads, totals, possessions, pace, and overtime semantics.
- Volleyball will implement match/set outcomes, best-of format, rotation, serve/receive, and retirement semantics.
- Core orchestration cannot assume draws, goals, periods, sets, or a particular lineup size.
- UI receives outcome labels and market definitions from the sport plugin.
- Each sport has separate calibration domains and model artifacts.

## 36. Definition of Done for the First Useful Release

- [ ] DOD-001: A clean local setup starts with mock providers and no paid API keys.
- [ ] DOD-002: The Dashboard correctly shows today, tomorrow, and the next day in Europe/Istanbul.
- [ ] DOD-003: The scan ranks fictional seed fixtures with transparent factor contributions.
- [ ] DOD-004: Manual search finds and selects supported fixtures without ambiguity auto-resolution.
- [ ] DOD-005: A full deterministic football analysis proceeds through every named pre-match stage.
- [ ] DOD-006: The UI shows truthful progress, cost, failures, and degraded states.
- [ ] DOD-007: Every material report statement links to evidence or is labeled inference.
- [ ] DOD-008: Quant output includes calibrated three-way probabilities and diagnostics.
- [ ] DOD-009: Allowed mock odds produce timestamped fair probability comparison.
- [ ] DOD-010: All four Sonnet synthesis roles are prediction-forbidden and their disagreement remains visible.
- [ ] DOD-011: Final critic can approve, request one revision, or veto.
- [ ] DOD-012: Approved forecast locks before kickoff with immutable database and object evidence.
- [ ] DOD-013: Exports reproduce the exact locked content and manifest hash.
- [ ] DOD-014: Post-match mock ingestion creates an autopsy, variance decomposition, and validated lesson.
- [ ] DOD-015: No post-match datum appears in the pre-match lock.
- [ ] DOD-016: All required tests, leakage sentinels, security checks, and browser journeys pass.
- [ ] DOD-017: Model and provider routes remain disabled until keys, terms, prices, and capabilities are verified.
- [ ] DOD-018: The small pilot budget cannot be exceeded by concurrency or retries.

## 37. Open Decisions That Do Not Block Mock-First Development

| Decision | Question | Default/non-blocking rule |
| --- | --- | --- |
| OD-001 | Primary licensed football statistics provider | Resolve before P06 production data. |
| OD-002 | Primary fixture provider coverage list | Resolve before enabling real scans. |
| OD-003 | Allowed odds provider and retention terms | Resolve before P08 production adapter. |
| OD-004 | Weather provider | Resolve before real environment stage. |
| OD-005 | Exact monthly pilot cap | Default is $15 until user edits configuration. |
| OD-006 | Authentication when hosted | Local personal session is sufficient for pilot. |
| OD-007 | Signing key custody when hosted | Unsigned hash lock is acceptable only for local prototype. |
| OD-008 | Competition allowlist | Seed competitions suffice for mock-first phases. |
| OD-009 | Whether to enable live odds watching | Disabled by default. |
| OD-010 | Basketball and volleyball launch order | Does not block football plugin purity. |

## 38. Final Implementation Rules for Codex

1. Build one testable vertical slice at a time.
2. Use mocks before spending external budget.
3. Do not ask the user to choose routine library details already prescribed here.
4. Ask only when a paid action, provider legal acceptance, secret entry, or genuinely material product decision is required.
5. Never claim a stage is complete based only on code generation or compilation.
6. Verify database behavior, workflow behavior, and actual browser behavior.
7. Report degraded or unverified external integrations honestly.
8. Preserve exact provenance, cutoff, configuration, prompt, model, and cost metadata.
9. Treat forecasts as probabilistic analytical artifacts, not promises.
10. Keep the UI compact, calm, and progressively enhanceable.
11. Keep football logic inside the football plugin.
12. Do not add basketball or volleyball production code before the football vertical slice is stable.
13. Use ADRs for architectural deviations.
14. Update this canonical specification only through an intentional reviewed version change.

## Appendix A. Requirement-to-Artifact Starter Map

- INV-001 (Istanbul date window)
  - Domain implementation: `apps/api/app/domain/requirements/inv-001.py` or the nearest cohesive module.
  - Primary test: `apps/api/tests/requirements/test_inv_001.py`.
  - Evidence: requirement ledger entry with CI artifact link.
- INV-002 (Fixture identity)
  - Domain implementation: `apps/api/app/domain/requirements/inv-002.py` or the nearest cohesive module.
  - Primary test: `apps/api/tests/requirements/test_inv_002.py`.
  - Evidence: requirement ledger entry with CI artifact link.
- INV-003 (Prediction cutoff)
  - Domain implementation: `apps/api/app/domain/requirements/inv-003.py` or the nearest cohesive module.
  - Primary test: `apps/api/tests/requirements/test_inv_003.py`.
  - Evidence: requirement ledger entry with CI artifact link.
- INV-004 (Immutable lock)
  - Domain implementation: `apps/api/app/domain/requirements/inv-004.py` or the nearest cohesive module.
  - Primary test: `apps/api/tests/requirements/test_inv_004.py`.
  - Evidence: requirement ledger entry with CI artifact link.
- INV-005 (Evidence provenance)
  - Domain implementation: `apps/api/app/domain/requirements/inv-005.py` or the nearest cohesive module.
  - Primary test: `apps/api/tests/requirements/test_inv_005.py`.
  - Evidence: requirement ledger entry with CI artifact link.
- INV-006 (Model configurability)
  - Domain implementation: `apps/api/app/domain/requirements/inv-006.py` or the nearest cohesive module.
  - Primary test: `apps/api/tests/requirements/test_inv_006.py`.
  - Evidence: requirement ledger entry with CI artifact link.
- INV-007 (Price re-verification)
  - Domain implementation: `apps/api/app/domain/requirements/inv-007.py` or the nearest cohesive module.
  - Primary test: `apps/api/tests/requirements/test_inv_007.py`.
  - Evidence: requirement ledger entry with CI artifact link.
- INV-008 (Provider legality)
  - Domain implementation: `apps/api/app/domain/requirements/inv-008.py` or the nearest cohesive module.
  - Primary test: `apps/api/tests/requirements/test_inv_008.py`.
  - Evidence: requirement ledger entry with CI artifact link.
- INV-009 (Budget stop)
  - Domain implementation: `apps/api/app/domain/requirements/inv-009.py` or the nearest cohesive module.
  - Primary test: `apps/api/tests/requirements/test_inv_009.py`.
  - Evidence: requirement ledger entry with CI artifact link.
- INV-010 (Idempotency)
  - Domain implementation: `apps/api/app/domain/requirements/inv-010.py` or the nearest cohesive module.
  - Primary test: `apps/api/tests/requirements/test_inv_010.py`.
  - Evidence: requirement ledger entry with CI artifact link.
- INV-011 (Reproducibility)
  - Domain implementation: `apps/api/app/domain/requirements/inv-011.py` or the nearest cohesive module.
  - Primary test: `apps/api/tests/requirements/test_inv_011.py`.
  - Evidence: requirement ledger entry with CI artifact link.
- INV-012 (No look-ahead)
  - Domain implementation: `apps/api/app/domain/requirements/inv-012.py` or the nearest cohesive module.
  - Primary test: `apps/api/tests/requirements/test_inv_012.py`.
  - Evidence: requirement ledger entry with CI artifact link.
- INV-013 (Uncertainty)
  - Domain implementation: `apps/api/app/domain/requirements/inv-013.py` or the nearest cohesive module.
  - Primary test: `apps/api/tests/requirements/test_inv_013.py`.
  - Evidence: requirement ledger entry with CI artifact link.
- INV-014 (Contradictions)
  - Domain implementation: `apps/api/app/domain/requirements/inv-014.py` or the nearest cohesive module.
  - Primary test: `apps/api/tests/requirements/test_inv_014.py`.
  - Evidence: requirement ledger entry with CI artifact link.
- INV-015 (Degraded honesty)
  - Domain implementation: `apps/api/app/domain/requirements/inv-015.py` or the nearest cohesive module.
  - Primary test: `apps/api/tests/requirements/test_inv_015.py`.
  - Evidence: requirement ledger entry with CI artifact link.
- INV-016 (Sport isolation)
  - Domain implementation: `apps/api/app/domain/requirements/inv-016.py` or the nearest cohesive module.
  - Primary test: `apps/api/tests/requirements/test_inv_016.py`.
  - Evidence: requirement ledger entry with CI artifact link.
- INV-017 (Human control)
  - Domain implementation: `apps/api/app/domain/requirements/inv-017.py` or the nearest cohesive module.
  - Primary test: `apps/api/tests/requirements/test_inv_017.py`.
  - Evidence: requirement ledger entry with CI artifact link.
- INV-018 (Post-match separation)
  - Domain implementation: `apps/api/app/domain/requirements/inv-018.py` or the nearest cohesive module.
  - Primary test: `apps/api/tests/requirements/test_inv_018.py`.
  - Evidence: requirement ledger entry with CI artifact link.
- INV-019 (Auditability)
  - Domain implementation: `apps/api/app/domain/requirements/inv-019.py` or the nearest cohesive module.
  - Primary test: `apps/api/tests/requirements/test_inv_019.py`.
  - Evidence: requirement ledger entry with CI artifact link.
- INV-020 (Secret safety)
  - Domain implementation: `apps/api/app/domain/requirements/inv-020.py` or the nearest cohesive module.
  - Primary test: `apps/api/tests/requirements/test_inv_020.py`.
  - Evidence: requirement ledger entry with CI artifact link.
- INV-021 (Personal data minimization)
  - Domain implementation: `apps/api/app/domain/requirements/inv-021.py` or the nearest cohesive module.
  - Primary test: `apps/api/tests/requirements/test_inv_021.py`.
  - Evidence: requirement ledger entry with CI artifact link.
- INV-022 (No automatic wagering)
  - Domain implementation: `apps/api/app/domain/requirements/inv-022.py` or the nearest cohesive module.
  - Primary test: `apps/api/tests/requirements/test_inv_022.py`.
  - Evidence: requirement ledger entry with CI artifact link.
- INV-023 (Source freshness)
  - Domain implementation: `apps/api/app/domain/requirements/inv-023.py` or the nearest cohesive module.
  - Primary test: `apps/api/tests/requirements/test_inv_023.py`.
  - Evidence: requirement ledger entry with CI artifact link.
- INV-024 (Claim normalization)
  - Domain implementation: `apps/api/app/domain/requirements/inv-024.py` or the nearest cohesive module.
  - Primary test: `apps/api/tests/requirements/test_inv_024.py`.
  - Evidence: requirement ledger entry with CI artifact link.
- INV-025 (Lineup uncertainty)
  - Domain implementation: `apps/api/app/domain/requirements/inv-025.py` or the nearest cohesive module.
  - Primary test: `apps/api/tests/requirements/test_inv_025.py`.
  - Evidence: requirement ledger entry with CI artifact link.
- INV-026 (Odds timestamps)
  - Domain implementation: `apps/api/app/domain/requirements/inv-026.py` or the nearest cohesive module.
  - Primary test: `apps/api/tests/requirements/test_inv_026.py`.
  - Evidence: requirement ledger entry with CI artifact link.
- INV-027 (Fair probabilities)
  - Domain implementation: `apps/api/app/domain/requirements/inv-027.py` or the nearest cohesive module.
  - Primary test: `apps/api/tests/requirements/test_inv_027.py`.
  - Evidence: requirement ledger entry with CI artifact link.
- INV-028 (Independent critics)
  - Domain implementation: `apps/api/app/domain/requirements/inv-028.py` or the nearest cohesive module.
  - Primary test: `apps/api/tests/requirements/test_inv_028.py`.
  - Evidence: requirement ledger entry with CI artifact link.
- INV-029 (Prompt versioning)
  - Domain implementation: `apps/api/app/domain/requirements/inv-029.py` or the nearest cohesive module.
  - Primary test: `apps/api/tests/requirements/test_inv_029.py`.
  - Evidence: requirement ledger entry with CI artifact link.
- INV-030 (Experiment isolation)
  - Domain implementation: `apps/api/app/domain/requirements/inv-030.py` or the nearest cohesive module.
  - Primary test: `apps/api/tests/requirements/test_inv_030.py`.
  - Evidence: requirement ledger entry with CI artifact link.
- INV-031 (Safe retry)
  - Domain implementation: `apps/api/app/domain/requirements/inv-031.py` or the nearest cohesive module.
  - Primary test: `apps/api/tests/requirements/test_inv_031.py`.
  - Evidence: requirement ledger entry with CI artifact link.
- INV-032 (Provider quota)
  - Domain implementation: `apps/api/app/domain/requirements/inv-032.py` or the nearest cohesive module.
  - Primary test: `apps/api/tests/requirements/test_inv_032.py`.
  - Evidence: requirement ledger entry with CI artifact link.
- INV-033 (Search ambiguity)
  - Domain implementation: `apps/api/app/domain/requirements/inv-033.py` or the nearest cohesive module.
  - Primary test: `apps/api/tests/requirements/test_inv_033.py`.
  - Evidence: requirement ledger entry with CI artifact link.
- INV-034 (Timezone display)
  - Domain implementation: `apps/api/app/domain/requirements/inv-034.py` or the nearest cohesive module.
  - Primary test: `apps/api/tests/requirements/test_inv_034.py`.
  - Evidence: requirement ledger entry with CI artifact link.
- INV-035 (Structured output)
  - Domain implementation: `apps/api/app/domain/requirements/inv-035.py` or the nearest cohesive module.
  - Primary test: `apps/api/tests/requirements/test_inv_035.py`.
  - Evidence: requirement ledger entry with CI artifact link.
- INV-036 (No silent coercion)
  - Domain implementation: `apps/api/app/domain/requirements/inv-036.py` or the nearest cohesive module.
  - Primary test: `apps/api/tests/requirements/test_inv_036.py`.
  - Evidence: requirement ledger entry with CI artifact link.
- INV-037 (Data deletion)
  - Domain implementation: `apps/api/app/domain/requirements/inv-037.py` or the nearest cohesive module.
  - Primary test: `apps/api/tests/requirements/test_inv_037.py`.
  - Evidence: requirement ledger entry with CI artifact link.
- INV-038 (Model refusal)
  - Domain implementation: `apps/api/app/domain/requirements/inv-038.py` or the nearest cohesive module.
  - Primary test: `apps/api/tests/requirements/test_inv_038.py`.
  - Evidence: requirement ledger entry with CI artifact link.
- INV-039 (Cost attribution)
  - Domain implementation: `apps/api/app/domain/requirements/inv-039.py` or the nearest cohesive module.
  - Primary test: `apps/api/tests/requirements/test_inv_039.py`.
  - Evidence: requirement ledger entry with CI artifact link.
- INV-040 (Final critic veto)
  - Domain implementation: `apps/api/app/domain/requirements/inv-040.py` or the nearest cohesive module.
  - Primary test: `apps/api/tests/requirements/test_inv_040.py`.
  - Evidence: requirement ledger entry with CI artifact link.
- INV-041 (Docker-only local runtime)
  - Domain implementation: `apps/api/app/domain/requirements/inv-041.py` or the nearest cohesive module.
  - Primary test: `apps/api/tests/requirements/test_inv_041.py`.
  - Evidence: requirement ledger entry with CI artifact link.
- INV-042 (Canonical product identity)
  - Domain implementation: `apps/api/app/domain/requirements/inv-042.py` or the nearest cohesive module.
  - Primary test: `apps/api/tests/requirements/test_inv_042.py`.
  - Evidence: requirement ledger entry with CI artifact link.
- INV-043 (Prediction abstention before Chief)
  - Domain implementation: `apps/api/app/domain/requirements/inv-043.py` or the nearest cohesive module.
  - Primary test: `apps/api/tests/requirements/test_inv_043.py`.
  - Evidence: requirement ledger entry with CI artifact link.
- INV-044 (Live market isolation)
  - Domain implementation: `apps/api/app/domain/requirements/inv-044.py` or the nearest cohesive module.
  - Primary test: `apps/api/tests/requirements/test_inv_044.py`.
  - Evidence: requirement ledger entry with CI artifact link.
- INV-045 (Result versus process)
  - Domain implementation: `apps/api/app/domain/requirements/inv-045.py` or the nearest cohesive module.
  - Primary test: `apps/api/tests/requirements/test_inv_045.py`.
  - Evidence: requirement ledger entry with CI artifact link.
- INV-046 (Evidence-layer separation)
  - Domain implementation: `apps/api/app/domain/requirements/inv-046.py` or the nearest cohesive module.
  - Primary test: `apps/api/tests/requirements/test_inv_046.py`.
  - Evidence: requirement ledger entry with CI artifact link.
- INV-047 (Docker test parity)
  - Domain implementation: `apps/api/app/domain/requirements/inv-047.py` or the nearest cohesive module.
  - Primary test: `apps/api/tests/requirements/test_inv_047.py`.
  - Evidence: requirement ledger entry with CI artifact link.

## Appendix B. Agent Output Common Checklist

- [ ] AGENT-COMMON-001: Run ID matches the workflow input.
- [ ] AGENT-COMMON-002: Fixture ID matches the canonical fixture.
- [ ] AGENT-COMMON-003: Cutoff is timezone-aware.
- [ ] AGENT-COMMON-004: No citation is observed after cutoff.
- [ ] AGENT-COMMON-005: All artifact hashes are lowercase SHA-256.
- [ ] AGENT-COMMON-006: Schema version is supported.
- [ ] AGENT-COMMON-007: Unknown fields are rejected.
- [ ] AGENT-COMMON-008: Status matches payload completeness.
- [ ] AGENT-COMMON-009: Confidence is within zero and one.
- [ ] AGENT-COMMON-010: Limitations are specific.
- [ ] AGENT-COMMON-011: Citations support the associated statement.
- [ ] AGENT-COMMON-012: Observed facts are separated from inference.
- [ ] AGENT-COMMON-013: Contradictions are not silently resolved.
- [ ] AGENT-COMMON-014: Missing data is explicit.
- [ ] AGENT-COMMON-015: Provider names are normalized.
- [ ] AGENT-COMMON-016: Units are canonical.
- [ ] AGENT-COMMON-017: Probabilities are finite.
- [ ] AGENT-COMMON-018: Probability vector sums to one when applicable.
- [ ] AGENT-COMMON-019: Market lines are comparable.
- [ ] AGENT-COMMON-020: Stale sources are labeled.
- [ ] AGENT-COMMON-021: No secrets appear.
- [ ] AGENT-COMMON-022: No raw chain-of-thought appears.
- [ ] AGENT-COMMON-023: No guaranteed-outcome language appears.
- [ ] AGENT-COMMON-024: Cost metadata is attributed.
- [ ] AGENT-COMMON-025: Prompt and model versions are recorded.
- [ ] AGENT-COMMON-026: Retry count is bounded.
- [ ] AGENT-COMMON-027: Idempotency identity is recorded.
- [ ] AGENT-COMMON-028: Output timestamp precedes lock when pre-match.
- [ ] AGENT-COMMON-029: Degraded reasons are stable codes.
- [ ] AGENT-COMMON-030: The report can render without provider SDK types.

## Appendix C. Provider Adapter Common Checklist

- [ ] PROVIDER-COMMON-001: Terms and license review recorded.
- [ ] PROVIDER-COMMON-002: Provider disabled by default.
- [ ] PROVIDER-COMMON-003: Secret name documented.
- [ ] PROVIDER-COMMON-004: Base URL allowlisted.
- [ ] PROVIDER-COMMON-005: TLS required.
- [ ] PROVIDER-COMMON-006: Timeout explicit.
- [ ] PROVIDER-COMMON-007: Retry class mapping explicit.
- [ ] PROVIDER-COMMON-008: 429 handled with Retry-After.
- [ ] PROVIDER-COMMON-009: Quota headers recorded.
- [ ] PROVIDER-COMMON-010: Request IDs recorded.
- [ ] PROVIDER-COMMON-011: User-Agent compliant.
- [ ] PROVIDER-COMMON-012: No credential in query logs.
- [ ] PROVIDER-COMMON-013: Response size bounded.
- [ ] PROVIDER-COMMON-014: JSON schema validated.
- [ ] PROVIDER-COMMON-015: Unknown enums quarantined.
- [ ] PROVIDER-COMMON-016: Provider timestamps preserved.
- [ ] PROVIDER-COMMON-017: Observation timestamp assigned server-side.
- [ ] PROVIDER-COMMON-018: Raw snapshot hashed.
- [ ] PROVIDER-COMMON-019: Raw snapshot stored privately.
- [ ] PROVIDER-COMMON-020: Canonical mapping versioned.
- [ ] PROVIDER-COMMON-021: Pagination tested.
- [ ] PROVIDER-COMMON-022: Empty response tested.
- [ ] PROVIDER-COMMON-023: Partial response tested.
- [ ] PROVIDER-COMMON-024: Duplicate response tested.
- [ ] PROVIDER-COMMON-025: Schema drift tested.
- [ ] PROVIDER-COMMON-026: Invalid authentication tested.
- [ ] PROVIDER-COMMON-027: Quota exhaustion tested.
- [ ] PROVIDER-COMMON-028: Circuit breaker tested.
- [ ] PROVIDER-COMMON-029: Retention job tested.
- [ ] PROVIDER-COMMON-030: Attribution requirement documented.

## Appendix D. UI State Matrix

### Dashboard

- [ ] UI-DASHBOARD-INITIAL: define and test the initial state for `/` when applicable.
- [ ] UI-DASHBOARD-LOADING: define and test the loading state for `/` when applicable.
- [ ] UI-DASHBOARD-PARTIAL-PROGRESS: define and test the partial progress state for `/` when applicable.
- [ ] UI-DASHBOARD-SUCCESS: define and test the success state for `/` when applicable.
- [ ] UI-DASHBOARD-EMPTY: define and test the empty state for `/` when applicable.
- [ ] UI-DASHBOARD-DEGRADED: define and test the degraded state for `/` when applicable.
- [ ] UI-DASHBOARD-RECOVERABLE-ERROR: define and test the recoverable error state for `/` when applicable.
- [ ] UI-DASHBOARD-FATAL-ERROR: define and test the fatal error state for `/` when applicable.
- [ ] UI-DASHBOARD-OFFLINE-RECONNECTING: define and test the offline/reconnecting state for `/` when applicable.
- [ ] UI-DASHBOARD-CANCEL-REQUESTED: define and test the cancel requested state for `/` when applicable.
- [ ] UI-DASHBOARD-CANCELLED: define and test the cancelled state for `/` when applicable.
- [ ] UI-DASHBOARD-BUDGET-PAUSED: define and test the budget paused state for `/` when applicable.
- [ ] UI-DASHBOARD-STALE: define and test the stale state for `/` when applicable.
- [ ] UI-DASHBOARD-LOCKED: define and test the locked state for `/` when applicable.
- [ ] UI-DASHBOARD-POST-MATCH-PENDING: define and test the post-match pending state for `/` when applicable.

### Scan Results

- [ ] UI-SCAN-RESULTS-INITIAL: define and test the initial state for `/scan/[scanId]` when applicable.
- [ ] UI-SCAN-RESULTS-LOADING: define and test the loading state for `/scan/[scanId]` when applicable.
- [ ] UI-SCAN-RESULTS-PARTIAL-PROGRESS: define and test the partial progress state for `/scan/[scanId]` when applicable.
- [ ] UI-SCAN-RESULTS-SUCCESS: define and test the success state for `/scan/[scanId]` when applicable.
- [ ] UI-SCAN-RESULTS-EMPTY: define and test the empty state for `/scan/[scanId]` when applicable.
- [ ] UI-SCAN-RESULTS-DEGRADED: define and test the degraded state for `/scan/[scanId]` when applicable.
- [ ] UI-SCAN-RESULTS-RECOVERABLE-ERROR: define and test the recoverable error state for `/scan/[scanId]` when applicable.
- [ ] UI-SCAN-RESULTS-FATAL-ERROR: define and test the fatal error state for `/scan/[scanId]` when applicable.
- [ ] UI-SCAN-RESULTS-OFFLINE-RECONNECTING: define and test the offline/reconnecting state for `/scan/[scanId]` when applicable.
- [ ] UI-SCAN-RESULTS-CANCEL-REQUESTED: define and test the cancel requested state for `/scan/[scanId]` when applicable.
- [ ] UI-SCAN-RESULTS-CANCELLED: define and test the cancelled state for `/scan/[scanId]` when applicable.
- [ ] UI-SCAN-RESULTS-BUDGET-PAUSED: define and test the budget paused state for `/scan/[scanId]` when applicable.
- [ ] UI-SCAN-RESULTS-STALE: define and test the stale state for `/scan/[scanId]` when applicable.
- [ ] UI-SCAN-RESULTS-LOCKED: define and test the locked state for `/scan/[scanId]` when applicable.
- [ ] UI-SCAN-RESULTS-POST-MATCH-PENDING: define and test the post-match pending state for `/scan/[scanId]` when applicable.

### Match Search

- [ ] UI-MATCH-SEARCH-INITIAL: define and test the initial state for `/search` when applicable.
- [ ] UI-MATCH-SEARCH-LOADING: define and test the loading state for `/search` when applicable.
- [ ] UI-MATCH-SEARCH-PARTIAL-PROGRESS: define and test the partial progress state for `/search` when applicable.
- [ ] UI-MATCH-SEARCH-SUCCESS: define and test the success state for `/search` when applicable.
- [ ] UI-MATCH-SEARCH-EMPTY: define and test the empty state for `/search` when applicable.
- [ ] UI-MATCH-SEARCH-DEGRADED: define and test the degraded state for `/search` when applicable.
- [ ] UI-MATCH-SEARCH-RECOVERABLE-ERROR: define and test the recoverable error state for `/search` when applicable.
- [ ] UI-MATCH-SEARCH-FATAL-ERROR: define and test the fatal error state for `/search` when applicable.
- [ ] UI-MATCH-SEARCH-OFFLINE-RECONNECTING: define and test the offline/reconnecting state for `/search` when applicable.
- [ ] UI-MATCH-SEARCH-CANCEL-REQUESTED: define and test the cancel requested state for `/search` when applicable.
- [ ] UI-MATCH-SEARCH-CANCELLED: define and test the cancelled state for `/search` when applicable.
- [ ] UI-MATCH-SEARCH-BUDGET-PAUSED: define and test the budget paused state for `/search` when applicable.
- [ ] UI-MATCH-SEARCH-STALE: define and test the stale state for `/search` when applicable.
- [ ] UI-MATCH-SEARCH-LOCKED: define and test the locked state for `/search` when applicable.
- [ ] UI-MATCH-SEARCH-POST-MATCH-PENDING: define and test the post-match pending state for `/search` when applicable.

### Fixture Preflight

- [ ] UI-FIXTURE-PREFLIGHT-INITIAL: define and test the initial state for `/fixtures/[fixtureId]` when applicable.
- [ ] UI-FIXTURE-PREFLIGHT-LOADING: define and test the loading state for `/fixtures/[fixtureId]` when applicable.
- [ ] UI-FIXTURE-PREFLIGHT-PARTIAL-PROGRESS: define and test the partial progress state for `/fixtures/[fixtureId]` when applicable.
- [ ] UI-FIXTURE-PREFLIGHT-SUCCESS: define and test the success state for `/fixtures/[fixtureId]` when applicable.
- [ ] UI-FIXTURE-PREFLIGHT-EMPTY: define and test the empty state for `/fixtures/[fixtureId]` when applicable.
- [ ] UI-FIXTURE-PREFLIGHT-DEGRADED: define and test the degraded state for `/fixtures/[fixtureId]` when applicable.
- [ ] UI-FIXTURE-PREFLIGHT-RECOVERABLE-ERROR: define and test the recoverable error state for `/fixtures/[fixtureId]` when applicable.
- [ ] UI-FIXTURE-PREFLIGHT-FATAL-ERROR: define and test the fatal error state for `/fixtures/[fixtureId]` when applicable.
- [ ] UI-FIXTURE-PREFLIGHT-OFFLINE-RECONNECTING: define and test the offline/reconnecting state for `/fixtures/[fixtureId]` when applicable.
- [ ] UI-FIXTURE-PREFLIGHT-CANCEL-REQUESTED: define and test the cancel requested state for `/fixtures/[fixtureId]` when applicable.
- [ ] UI-FIXTURE-PREFLIGHT-CANCELLED: define and test the cancelled state for `/fixtures/[fixtureId]` when applicable.
- [ ] UI-FIXTURE-PREFLIGHT-BUDGET-PAUSED: define and test the budget paused state for `/fixtures/[fixtureId]` when applicable.
- [ ] UI-FIXTURE-PREFLIGHT-STALE: define and test the stale state for `/fixtures/[fixtureId]` when applicable.
- [ ] UI-FIXTURE-PREFLIGHT-LOCKED: define and test the locked state for `/fixtures/[fixtureId]` when applicable.
- [ ] UI-FIXTURE-PREFLIGHT-POST-MATCH-PENDING: define and test the post-match pending state for `/fixtures/[fixtureId]` when applicable.

### Run Overview

- [ ] UI-RUN-OVERVIEW-INITIAL: define and test the initial state for `/runs/[runId]` when applicable.
- [ ] UI-RUN-OVERVIEW-LOADING: define and test the loading state for `/runs/[runId]` when applicable.
- [ ] UI-RUN-OVERVIEW-PARTIAL-PROGRESS: define and test the partial progress state for `/runs/[runId]` when applicable.
- [ ] UI-RUN-OVERVIEW-SUCCESS: define and test the success state for `/runs/[runId]` when applicable.
- [ ] UI-RUN-OVERVIEW-EMPTY: define and test the empty state for `/runs/[runId]` when applicable.
- [ ] UI-RUN-OVERVIEW-DEGRADED: define and test the degraded state for `/runs/[runId]` when applicable.
- [ ] UI-RUN-OVERVIEW-RECOVERABLE-ERROR: define and test the recoverable error state for `/runs/[runId]` when applicable.
- [ ] UI-RUN-OVERVIEW-FATAL-ERROR: define and test the fatal error state for `/runs/[runId]` when applicable.
- [ ] UI-RUN-OVERVIEW-OFFLINE-RECONNECTING: define and test the offline/reconnecting state for `/runs/[runId]` when applicable.
- [ ] UI-RUN-OVERVIEW-CANCEL-REQUESTED: define and test the cancel requested state for `/runs/[runId]` when applicable.
- [ ] UI-RUN-OVERVIEW-CANCELLED: define and test the cancelled state for `/runs/[runId]` when applicable.
- [ ] UI-RUN-OVERVIEW-BUDGET-PAUSED: define and test the budget paused state for `/runs/[runId]` when applicable.
- [ ] UI-RUN-OVERVIEW-STALE: define and test the stale state for `/runs/[runId]` when applicable.
- [ ] UI-RUN-OVERVIEW-LOCKED: define and test the locked state for `/runs/[runId]` when applicable.
- [ ] UI-RUN-OVERVIEW-POST-MATCH-PENDING: define and test the post-match pending state for `/runs/[runId]` when applicable.

### Evidence Ledger

- [ ] UI-EVIDENCE-LEDGER-INITIAL: define and test the initial state for `/runs/[runId]/evidence` when applicable.
- [ ] UI-EVIDENCE-LEDGER-LOADING: define and test the loading state for `/runs/[runId]/evidence` when applicable.
- [ ] UI-EVIDENCE-LEDGER-PARTIAL-PROGRESS: define and test the partial progress state for `/runs/[runId]/evidence` when applicable.
- [ ] UI-EVIDENCE-LEDGER-SUCCESS: define and test the success state for `/runs/[runId]/evidence` when applicable.
- [ ] UI-EVIDENCE-LEDGER-EMPTY: define and test the empty state for `/runs/[runId]/evidence` when applicable.
- [ ] UI-EVIDENCE-LEDGER-DEGRADED: define and test the degraded state for `/runs/[runId]/evidence` when applicable.
- [ ] UI-EVIDENCE-LEDGER-RECOVERABLE-ERROR: define and test the recoverable error state for `/runs/[runId]/evidence` when applicable.
- [ ] UI-EVIDENCE-LEDGER-FATAL-ERROR: define and test the fatal error state for `/runs/[runId]/evidence` when applicable.
- [ ] UI-EVIDENCE-LEDGER-OFFLINE-RECONNECTING: define and test the offline/reconnecting state for `/runs/[runId]/evidence` when applicable.
- [ ] UI-EVIDENCE-LEDGER-CANCEL-REQUESTED: define and test the cancel requested state for `/runs/[runId]/evidence` when applicable.
- [ ] UI-EVIDENCE-LEDGER-CANCELLED: define and test the cancelled state for `/runs/[runId]/evidence` when applicable.
- [ ] UI-EVIDENCE-LEDGER-BUDGET-PAUSED: define and test the budget paused state for `/runs/[runId]/evidence` when applicable.
- [ ] UI-EVIDENCE-LEDGER-STALE: define and test the stale state for `/runs/[runId]/evidence` when applicable.
- [ ] UI-EVIDENCE-LEDGER-LOCKED: define and test the locked state for `/runs/[runId]/evidence` when applicable.
- [ ] UI-EVIDENCE-LEDGER-POST-MATCH-PENDING: define and test the post-match pending state for `/runs/[runId]/evidence` when applicable.

### Specialist Reports

- [ ] UI-SPECIALIST-REPORTS-INITIAL: define and test the initial state for `/runs/[runId]/specialists` when applicable.
- [ ] UI-SPECIALIST-REPORTS-LOADING: define and test the loading state for `/runs/[runId]/specialists` when applicable.
- [ ] UI-SPECIALIST-REPORTS-PARTIAL-PROGRESS: define and test the partial progress state for `/runs/[runId]/specialists` when applicable.
- [ ] UI-SPECIALIST-REPORTS-SUCCESS: define and test the success state for `/runs/[runId]/specialists` when applicable.
- [ ] UI-SPECIALIST-REPORTS-EMPTY: define and test the empty state for `/runs/[runId]/specialists` when applicable.
- [ ] UI-SPECIALIST-REPORTS-DEGRADED: define and test the degraded state for `/runs/[runId]/specialists` when applicable.
- [ ] UI-SPECIALIST-REPORTS-RECOVERABLE-ERROR: define and test the recoverable error state for `/runs/[runId]/specialists` when applicable.
- [ ] UI-SPECIALIST-REPORTS-FATAL-ERROR: define and test the fatal error state for `/runs/[runId]/specialists` when applicable.
- [ ] UI-SPECIALIST-REPORTS-OFFLINE-RECONNECTING: define and test the offline/reconnecting state for `/runs/[runId]/specialists` when applicable.
- [ ] UI-SPECIALIST-REPORTS-CANCEL-REQUESTED: define and test the cancel requested state for `/runs/[runId]/specialists` when applicable.
- [ ] UI-SPECIALIST-REPORTS-CANCELLED: define and test the cancelled state for `/runs/[runId]/specialists` when applicable.
- [ ] UI-SPECIALIST-REPORTS-BUDGET-PAUSED: define and test the budget paused state for `/runs/[runId]/specialists` when applicable.
- [ ] UI-SPECIALIST-REPORTS-STALE: define and test the stale state for `/runs/[runId]/specialists` when applicable.
- [ ] UI-SPECIALIST-REPORTS-LOCKED: define and test the locked state for `/runs/[runId]/specialists` when applicable.
- [ ] UI-SPECIALIST-REPORTS-POST-MATCH-PENDING: define and test the post-match pending state for `/runs/[runId]/specialists` when applicable.

### Quant Models

- [ ] UI-QUANT-MODELS-INITIAL: define and test the initial state for `/runs/[runId]/quant` when applicable.
- [ ] UI-QUANT-MODELS-LOADING: define and test the loading state for `/runs/[runId]/quant` when applicable.
- [ ] UI-QUANT-MODELS-PARTIAL-PROGRESS: define and test the partial progress state for `/runs/[runId]/quant` when applicable.
- [ ] UI-QUANT-MODELS-SUCCESS: define and test the success state for `/runs/[runId]/quant` when applicable.
- [ ] UI-QUANT-MODELS-EMPTY: define and test the empty state for `/runs/[runId]/quant` when applicable.
- [ ] UI-QUANT-MODELS-DEGRADED: define and test the degraded state for `/runs/[runId]/quant` when applicable.
- [ ] UI-QUANT-MODELS-RECOVERABLE-ERROR: define and test the recoverable error state for `/runs/[runId]/quant` when applicable.
- [ ] UI-QUANT-MODELS-FATAL-ERROR: define and test the fatal error state for `/runs/[runId]/quant` when applicable.
- [ ] UI-QUANT-MODELS-OFFLINE-RECONNECTING: define and test the offline/reconnecting state for `/runs/[runId]/quant` when applicable.
- [ ] UI-QUANT-MODELS-CANCEL-REQUESTED: define and test the cancel requested state for `/runs/[runId]/quant` when applicable.
- [ ] UI-QUANT-MODELS-CANCELLED: define and test the cancelled state for `/runs/[runId]/quant` when applicable.
- [ ] UI-QUANT-MODELS-BUDGET-PAUSED: define and test the budget paused state for `/runs/[runId]/quant` when applicable.
- [ ] UI-QUANT-MODELS-STALE: define and test the stale state for `/runs/[runId]/quant` when applicable.
- [ ] UI-QUANT-MODELS-LOCKED: define and test the locked state for `/runs/[runId]/quant` when applicable.
- [ ] UI-QUANT-MODELS-POST-MATCH-PENDING: define and test the post-match pending state for `/runs/[runId]/quant` when applicable.

### Market Intelligence

- [ ] UI-MARKET-INTELLIGENCE-INITIAL: define and test the initial state for `/runs/[runId]/market` when applicable.
- [ ] UI-MARKET-INTELLIGENCE-LOADING: define and test the loading state for `/runs/[runId]/market` when applicable.
- [ ] UI-MARKET-INTELLIGENCE-PARTIAL-PROGRESS: define and test the partial progress state for `/runs/[runId]/market` when applicable.
- [ ] UI-MARKET-INTELLIGENCE-SUCCESS: define and test the success state for `/runs/[runId]/market` when applicable.
- [ ] UI-MARKET-INTELLIGENCE-EMPTY: define and test the empty state for `/runs/[runId]/market` when applicable.
- [ ] UI-MARKET-INTELLIGENCE-DEGRADED: define and test the degraded state for `/runs/[runId]/market` when applicable.
- [ ] UI-MARKET-INTELLIGENCE-RECOVERABLE-ERROR: define and test the recoverable error state for `/runs/[runId]/market` when applicable.
- [ ] UI-MARKET-INTELLIGENCE-FATAL-ERROR: define and test the fatal error state for `/runs/[runId]/market` when applicable.
- [ ] UI-MARKET-INTELLIGENCE-OFFLINE-RECONNECTING: define and test the offline/reconnecting state for `/runs/[runId]/market` when applicable.
- [ ] UI-MARKET-INTELLIGENCE-CANCEL-REQUESTED: define and test the cancel requested state for `/runs/[runId]/market` when applicable.
- [ ] UI-MARKET-INTELLIGENCE-CANCELLED: define and test the cancelled state for `/runs/[runId]/market` when applicable.
- [ ] UI-MARKET-INTELLIGENCE-BUDGET-PAUSED: define and test the budget paused state for `/runs/[runId]/market` when applicable.
- [ ] UI-MARKET-INTELLIGENCE-STALE: define and test the stale state for `/runs/[runId]/market` when applicable.
- [ ] UI-MARKET-INTELLIGENCE-LOCKED: define and test the locked state for `/runs/[runId]/market` when applicable.
- [ ] UI-MARKET-INTELLIGENCE-POST-MATCH-PENDING: define and test the post-match pending state for `/runs/[runId]/market` when applicable.

### Sonnet Committee

- [ ] UI-SONNET-COMMITTEE-INITIAL: define and test the initial state for `/runs/[runId]/committee` when applicable.
- [ ] UI-SONNET-COMMITTEE-LOADING: define and test the loading state for `/runs/[runId]/committee` when applicable.
- [ ] UI-SONNET-COMMITTEE-PARTIAL-PROGRESS: define and test the partial progress state for `/runs/[runId]/committee` when applicable.
- [ ] UI-SONNET-COMMITTEE-SUCCESS: define and test the success state for `/runs/[runId]/committee` when applicable.
- [ ] UI-SONNET-COMMITTEE-EMPTY: define and test the empty state for `/runs/[runId]/committee` when applicable.
- [ ] UI-SONNET-COMMITTEE-DEGRADED: define and test the degraded state for `/runs/[runId]/committee` when applicable.
- [ ] UI-SONNET-COMMITTEE-RECOVERABLE-ERROR: define and test the recoverable error state for `/runs/[runId]/committee` when applicable.
- [ ] UI-SONNET-COMMITTEE-FATAL-ERROR: define and test the fatal error state for `/runs/[runId]/committee` when applicable.
- [ ] UI-SONNET-COMMITTEE-OFFLINE-RECONNECTING: define and test the offline/reconnecting state for `/runs/[runId]/committee` when applicable.
- [ ] UI-SONNET-COMMITTEE-CANCEL-REQUESTED: define and test the cancel requested state for `/runs/[runId]/committee` when applicable.
- [ ] UI-SONNET-COMMITTEE-CANCELLED: define and test the cancelled state for `/runs/[runId]/committee` when applicable.
- [ ] UI-SONNET-COMMITTEE-BUDGET-PAUSED: define and test the budget paused state for `/runs/[runId]/committee` when applicable.
- [ ] UI-SONNET-COMMITTEE-STALE: define and test the stale state for `/runs/[runId]/committee` when applicable.
- [ ] UI-SONNET-COMMITTEE-LOCKED: define and test the locked state for `/runs/[runId]/committee` when applicable.
- [ ] UI-SONNET-COMMITTEE-POST-MATCH-PENDING: define and test the post-match pending state for `/runs/[runId]/committee` when applicable.

### Scenarios

- [ ] UI-SCENARIOS-INITIAL: define and test the initial state for `/runs/[runId]/scenarios` when applicable.
- [ ] UI-SCENARIOS-LOADING: define and test the loading state for `/runs/[runId]/scenarios` when applicable.
- [ ] UI-SCENARIOS-PARTIAL-PROGRESS: define and test the partial progress state for `/runs/[runId]/scenarios` when applicable.
- [ ] UI-SCENARIOS-SUCCESS: define and test the success state for `/runs/[runId]/scenarios` when applicable.
- [ ] UI-SCENARIOS-EMPTY: define and test the empty state for `/runs/[runId]/scenarios` when applicable.
- [ ] UI-SCENARIOS-DEGRADED: define and test the degraded state for `/runs/[runId]/scenarios` when applicable.
- [ ] UI-SCENARIOS-RECOVERABLE-ERROR: define and test the recoverable error state for `/runs/[runId]/scenarios` when applicable.
- [ ] UI-SCENARIOS-FATAL-ERROR: define and test the fatal error state for `/runs/[runId]/scenarios` when applicable.
- [ ] UI-SCENARIOS-OFFLINE-RECONNECTING: define and test the offline/reconnecting state for `/runs/[runId]/scenarios` when applicable.
- [ ] UI-SCENARIOS-CANCEL-REQUESTED: define and test the cancel requested state for `/runs/[runId]/scenarios` when applicable.
- [ ] UI-SCENARIOS-CANCELLED: define and test the cancelled state for `/runs/[runId]/scenarios` when applicable.
- [ ] UI-SCENARIOS-BUDGET-PAUSED: define and test the budget paused state for `/runs/[runId]/scenarios` when applicable.
- [ ] UI-SCENARIOS-STALE: define and test the stale state for `/runs/[runId]/scenarios` when applicable.
- [ ] UI-SCENARIOS-LOCKED: define and test the locked state for `/runs/[runId]/scenarios` when applicable.
- [ ] UI-SCENARIOS-POST-MATCH-PENDING: define and test the post-match pending state for `/runs/[runId]/scenarios` when applicable.

### Final Forecast

- [ ] UI-FINAL-FORECAST-INITIAL: define and test the initial state for `/runs/[runId]/final` when applicable.
- [ ] UI-FINAL-FORECAST-LOADING: define and test the loading state for `/runs/[runId]/final` when applicable.
- [ ] UI-FINAL-FORECAST-PARTIAL-PROGRESS: define and test the partial progress state for `/runs/[runId]/final` when applicable.
- [ ] UI-FINAL-FORECAST-SUCCESS: define and test the success state for `/runs/[runId]/final` when applicable.
- [ ] UI-FINAL-FORECAST-EMPTY: define and test the empty state for `/runs/[runId]/final` when applicable.
- [ ] UI-FINAL-FORECAST-DEGRADED: define and test the degraded state for `/runs/[runId]/final` when applicable.
- [ ] UI-FINAL-FORECAST-RECOVERABLE-ERROR: define and test the recoverable error state for `/runs/[runId]/final` when applicable.
- [ ] UI-FINAL-FORECAST-FATAL-ERROR: define and test the fatal error state for `/runs/[runId]/final` when applicable.
- [ ] UI-FINAL-FORECAST-OFFLINE-RECONNECTING: define and test the offline/reconnecting state for `/runs/[runId]/final` when applicable.
- [ ] UI-FINAL-FORECAST-CANCEL-REQUESTED: define and test the cancel requested state for `/runs/[runId]/final` when applicable.
- [ ] UI-FINAL-FORECAST-CANCELLED: define and test the cancelled state for `/runs/[runId]/final` when applicable.
- [ ] UI-FINAL-FORECAST-BUDGET-PAUSED: define and test the budget paused state for `/runs/[runId]/final` when applicable.
- [ ] UI-FINAL-FORECAST-STALE: define and test the stale state for `/runs/[runId]/final` when applicable.
- [ ] UI-FINAL-FORECAST-LOCKED: define and test the locked state for `/runs/[runId]/final` when applicable.
- [ ] UI-FINAL-FORECAST-POST-MATCH-PENDING: define and test the post-match pending state for `/runs/[runId]/final` when applicable.

### Locked Prediction

- [ ] UI-LOCKED-PREDICTION-INITIAL: define and test the initial state for `/locks/[lockId]` when applicable.
- [ ] UI-LOCKED-PREDICTION-LOADING: define and test the loading state for `/locks/[lockId]` when applicable.
- [ ] UI-LOCKED-PREDICTION-PARTIAL-PROGRESS: define and test the partial progress state for `/locks/[lockId]` when applicable.
- [ ] UI-LOCKED-PREDICTION-SUCCESS: define and test the success state for `/locks/[lockId]` when applicable.
- [ ] UI-LOCKED-PREDICTION-EMPTY: define and test the empty state for `/locks/[lockId]` when applicable.
- [ ] UI-LOCKED-PREDICTION-DEGRADED: define and test the degraded state for `/locks/[lockId]` when applicable.
- [ ] UI-LOCKED-PREDICTION-RECOVERABLE-ERROR: define and test the recoverable error state for `/locks/[lockId]` when applicable.
- [ ] UI-LOCKED-PREDICTION-FATAL-ERROR: define and test the fatal error state for `/locks/[lockId]` when applicable.
- [ ] UI-LOCKED-PREDICTION-OFFLINE-RECONNECTING: define and test the offline/reconnecting state for `/locks/[lockId]` when applicable.
- [ ] UI-LOCKED-PREDICTION-CANCEL-REQUESTED: define and test the cancel requested state for `/locks/[lockId]` when applicable.
- [ ] UI-LOCKED-PREDICTION-CANCELLED: define and test the cancelled state for `/locks/[lockId]` when applicable.
- [ ] UI-LOCKED-PREDICTION-BUDGET-PAUSED: define and test the budget paused state for `/locks/[lockId]` when applicable.
- [ ] UI-LOCKED-PREDICTION-STALE: define and test the stale state for `/locks/[lockId]` when applicable.
- [ ] UI-LOCKED-PREDICTION-LOCKED: define and test the locked state for `/locks/[lockId]` when applicable.
- [ ] UI-LOCKED-PREDICTION-POST-MATCH-PENDING: define and test the post-match pending state for `/locks/[lockId]` when applicable.

### Post-Match Autopsy

- [ ] UI-POST-MATCH-AUTOPSY-INITIAL: define and test the initial state for `/locks/[lockId]/autopsy` when applicable.
- [ ] UI-POST-MATCH-AUTOPSY-LOADING: define and test the loading state for `/locks/[lockId]/autopsy` when applicable.
- [ ] UI-POST-MATCH-AUTOPSY-PARTIAL-PROGRESS: define and test the partial progress state for `/locks/[lockId]/autopsy` when applicable.
- [ ] UI-POST-MATCH-AUTOPSY-SUCCESS: define and test the success state for `/locks/[lockId]/autopsy` when applicable.
- [ ] UI-POST-MATCH-AUTOPSY-EMPTY: define and test the empty state for `/locks/[lockId]/autopsy` when applicable.
- [ ] UI-POST-MATCH-AUTOPSY-DEGRADED: define and test the degraded state for `/locks/[lockId]/autopsy` when applicable.
- [ ] UI-POST-MATCH-AUTOPSY-RECOVERABLE-ERROR: define and test the recoverable error state for `/locks/[lockId]/autopsy` when applicable.
- [ ] UI-POST-MATCH-AUTOPSY-FATAL-ERROR: define and test the fatal error state for `/locks/[lockId]/autopsy` when applicable.
- [ ] UI-POST-MATCH-AUTOPSY-OFFLINE-RECONNECTING: define and test the offline/reconnecting state for `/locks/[lockId]/autopsy` when applicable.
- [ ] UI-POST-MATCH-AUTOPSY-CANCEL-REQUESTED: define and test the cancel requested state for `/locks/[lockId]/autopsy` when applicable.
- [ ] UI-POST-MATCH-AUTOPSY-CANCELLED: define and test the cancelled state for `/locks/[lockId]/autopsy` when applicable.
- [ ] UI-POST-MATCH-AUTOPSY-BUDGET-PAUSED: define and test the budget paused state for `/locks/[lockId]/autopsy` when applicable.
- [ ] UI-POST-MATCH-AUTOPSY-STALE: define and test the stale state for `/locks/[lockId]/autopsy` when applicable.
- [ ] UI-POST-MATCH-AUTOPSY-LOCKED: define and test the locked state for `/locks/[lockId]/autopsy` when applicable.
- [ ] UI-POST-MATCH-AUTOPSY-POST-MATCH-PENDING: define and test the post-match pending state for `/locks/[lockId]/autopsy` when applicable.

### Case Memory

- [ ] UI-CASE-MEMORY-INITIAL: define and test the initial state for `/cases` when applicable.
- [ ] UI-CASE-MEMORY-LOADING: define and test the loading state for `/cases` when applicable.
- [ ] UI-CASE-MEMORY-PARTIAL-PROGRESS: define and test the partial progress state for `/cases` when applicable.
- [ ] UI-CASE-MEMORY-SUCCESS: define and test the success state for `/cases` when applicable.
- [ ] UI-CASE-MEMORY-EMPTY: define and test the empty state for `/cases` when applicable.
- [ ] UI-CASE-MEMORY-DEGRADED: define and test the degraded state for `/cases` when applicable.
- [ ] UI-CASE-MEMORY-RECOVERABLE-ERROR: define and test the recoverable error state for `/cases` when applicable.
- [ ] UI-CASE-MEMORY-FATAL-ERROR: define and test the fatal error state for `/cases` when applicable.
- [ ] UI-CASE-MEMORY-OFFLINE-RECONNECTING: define and test the offline/reconnecting state for `/cases` when applicable.
- [ ] UI-CASE-MEMORY-CANCEL-REQUESTED: define and test the cancel requested state for `/cases` when applicable.
- [ ] UI-CASE-MEMORY-CANCELLED: define and test the cancelled state for `/cases` when applicable.
- [ ] UI-CASE-MEMORY-BUDGET-PAUSED: define and test the budget paused state for `/cases` when applicable.
- [ ] UI-CASE-MEMORY-STALE: define and test the stale state for `/cases` when applicable.
- [ ] UI-CASE-MEMORY-LOCKED: define and test the locked state for `/cases` when applicable.
- [ ] UI-CASE-MEMORY-POST-MATCH-PENDING: define and test the post-match pending state for `/cases` when applicable.

### Providers

- [ ] UI-PROVIDERS-INITIAL: define and test the initial state for `/settings/providers` when applicable.
- [ ] UI-PROVIDERS-LOADING: define and test the loading state for `/settings/providers` when applicable.
- [ ] UI-PROVIDERS-PARTIAL-PROGRESS: define and test the partial progress state for `/settings/providers` when applicable.
- [ ] UI-PROVIDERS-SUCCESS: define and test the success state for `/settings/providers` when applicable.
- [ ] UI-PROVIDERS-EMPTY: define and test the empty state for `/settings/providers` when applicable.
- [ ] UI-PROVIDERS-DEGRADED: define and test the degraded state for `/settings/providers` when applicable.
- [ ] UI-PROVIDERS-RECOVERABLE-ERROR: define and test the recoverable error state for `/settings/providers` when applicable.
- [ ] UI-PROVIDERS-FATAL-ERROR: define and test the fatal error state for `/settings/providers` when applicable.
- [ ] UI-PROVIDERS-OFFLINE-RECONNECTING: define and test the offline/reconnecting state for `/settings/providers` when applicable.
- [ ] UI-PROVIDERS-CANCEL-REQUESTED: define and test the cancel requested state for `/settings/providers` when applicable.
- [ ] UI-PROVIDERS-CANCELLED: define and test the cancelled state for `/settings/providers` when applicable.
- [ ] UI-PROVIDERS-BUDGET-PAUSED: define and test the budget paused state for `/settings/providers` when applicable.
- [ ] UI-PROVIDERS-STALE: define and test the stale state for `/settings/providers` when applicable.
- [ ] UI-PROVIDERS-LOCKED: define and test the locked state for `/settings/providers` when applicable.
- [ ] UI-PROVIDERS-POST-MATCH-PENDING: define and test the post-match pending state for `/settings/providers` when applicable.

### Models

- [ ] UI-MODELS-INITIAL: define and test the initial state for `/settings/models` when applicable.
- [ ] UI-MODELS-LOADING: define and test the loading state for `/settings/models` when applicable.
- [ ] UI-MODELS-PARTIAL-PROGRESS: define and test the partial progress state for `/settings/models` when applicable.
- [ ] UI-MODELS-SUCCESS: define and test the success state for `/settings/models` when applicable.
- [ ] UI-MODELS-EMPTY: define and test the empty state for `/settings/models` when applicable.
- [ ] UI-MODELS-DEGRADED: define and test the degraded state for `/settings/models` when applicable.
- [ ] UI-MODELS-RECOVERABLE-ERROR: define and test the recoverable error state for `/settings/models` when applicable.
- [ ] UI-MODELS-FATAL-ERROR: define and test the fatal error state for `/settings/models` when applicable.
- [ ] UI-MODELS-OFFLINE-RECONNECTING: define and test the offline/reconnecting state for `/settings/models` when applicable.
- [ ] UI-MODELS-CANCEL-REQUESTED: define and test the cancel requested state for `/settings/models` when applicable.
- [ ] UI-MODELS-CANCELLED: define and test the cancelled state for `/settings/models` when applicable.
- [ ] UI-MODELS-BUDGET-PAUSED: define and test the budget paused state for `/settings/models` when applicable.
- [ ] UI-MODELS-STALE: define and test the stale state for `/settings/models` when applicable.
- [ ] UI-MODELS-LOCKED: define and test the locked state for `/settings/models` when applicable.
- [ ] UI-MODELS-POST-MATCH-PENDING: define and test the post-match pending state for `/settings/models` when applicable.

### Budget

- [ ] UI-BUDGET-INITIAL: define and test the initial state for `/settings/budget` when applicable.
- [ ] UI-BUDGET-LOADING: define and test the loading state for `/settings/budget` when applicable.
- [ ] UI-BUDGET-PARTIAL-PROGRESS: define and test the partial progress state for `/settings/budget` when applicable.
- [ ] UI-BUDGET-SUCCESS: define and test the success state for `/settings/budget` when applicable.
- [ ] UI-BUDGET-EMPTY: define and test the empty state for `/settings/budget` when applicable.
- [ ] UI-BUDGET-DEGRADED: define and test the degraded state for `/settings/budget` when applicable.
- [ ] UI-BUDGET-RECOVERABLE-ERROR: define and test the recoverable error state for `/settings/budget` when applicable.
- [ ] UI-BUDGET-FATAL-ERROR: define and test the fatal error state for `/settings/budget` when applicable.
- [ ] UI-BUDGET-OFFLINE-RECONNECTING: define and test the offline/reconnecting state for `/settings/budget` when applicable.
- [ ] UI-BUDGET-CANCEL-REQUESTED: define and test the cancel requested state for `/settings/budget` when applicable.
- [ ] UI-BUDGET-CANCELLED: define and test the cancelled state for `/settings/budget` when applicable.
- [ ] UI-BUDGET-BUDGET-PAUSED: define and test the budget paused state for `/settings/budget` when applicable.
- [ ] UI-BUDGET-STALE: define and test the stale state for `/settings/budget` when applicable.
- [ ] UI-BUDGET-LOCKED: define and test the locked state for `/settings/budget` when applicable.
- [ ] UI-BUDGET-POST-MATCH-PENDING: define and test the post-match pending state for `/settings/budget` when applicable.

## Appendix E. Source Freshness Starter Policy

| Source class | Initial TTL | Stale behavior |
| --- | --- | --- |
| confirmed lineup | 5 minutes | stale; refresh until cutoff |
| expected lineup | 2 hours | decrease confidence |
| injury/suspension official | 6 hours | refresh before committee |
| injury report media | 3 hours | require corroboration |
| odds pre-match | 5 minutes near kickoff; 30 minutes otherwise | exclude stale edge |
| weather forecast | 3 hours | show forecast horizon |
| fixture kickoff/status | 15 minutes | refresh before lock |
| season statistics | 24 hours | allow if no matches occurred since update |
| recent match events | 24 hours after provider finalization | wait for corrections |
| coach/roster identity | 7 days | refresh on contradiction |
| venue metadata | 90 days | refresh on fixture conflict |
| methodology definition | until version change | bind exact version |
| model price/capability | 7 days for active development | block after expiry |

TTL values are starting policy, not universal truth; configure per provider and competition.

## Appendix F. Cost Estimation Formula

```text
estimated_call_cost_usd =
  estimated_input_tokens / 1_000_000 * input_usd_per_mtok
+ estimated_cached_input_tokens / 1_000_000 * cached_input_usd_per_mtok
+ estimated_output_tokens / 1_000_000 * output_usd_per_mtok
+ estimated_tool_calls * tool_usd_per_call
+ estimated_search_queries / 1_000 * search_usd_per_1k
+ provider_quota_units * provider_usd_per_unit

reservation = max(estimated_call_cost_usd * safety_multiplier, configured_minimum_reservation)
```

- Safety multiplier default is 1.25 for known bounded prompts.
- Use 1.75 for first-run unmeasured prompts.
- Unknown price components make the route ineligible.
- Actual usage reconciles from provider-reported token and quota metadata.

## Appendix G. Release Evidence Bundle

- [ ] RELEASE-EVIDENCE-001: attach source commit and clean/dirty status.
- [ ] RELEASE-EVIDENCE-002: attach lockfile checksum.
- [ ] RELEASE-EVIDENCE-003: attach database migration head.
- [ ] RELEASE-EVIDENCE-004: attach resolved config snapshot.
- [ ] RELEASE-EVIDENCE-005: attach model verification ledger.
- [ ] RELEASE-EVIDENCE-006: attach provider compliance ledger.
- [ ] RELEASE-EVIDENCE-007: attach unit test report.
- [ ] RELEASE-EVIDENCE-008: attach contract test report.
- [ ] RELEASE-EVIDENCE-009: attach integration test report.
- [ ] RELEASE-EVIDENCE-010: attach browser E2E report.
- [ ] RELEASE-EVIDENCE-011: attach visual snapshots.
- [ ] RELEASE-EVIDENCE-012: attach security test report.
- [ ] RELEASE-EVIDENCE-013: attach backtest leakage sentinel report.
- [ ] RELEASE-EVIDENCE-014: attach golden full-run manifest.
- [ ] RELEASE-EVIDENCE-015: attach sample prediction lock hash.
- [ ] RELEASE-EVIDENCE-016: attach sample post-match autopsy.
- [ ] RELEASE-EVIDENCE-017: attach observability dashboard screenshots or exports.
- [ ] RELEASE-EVIDENCE-018: attach known limitations.
- [ ] RELEASE-EVIDENCE-019: attach cost report.
- [ ] RELEASE-EVIDENCE-020: attach requirement traceability export.

## Appendix H. Canonical Error Codes

- ERR-001 `AUTOPSY_DEGRADED`: map to a stable problem type URI, safe user message key, retryability flag, and operator runbook where applicable.
- ERR-002 `BLOCKED_PREFLIGHT`: map to a stable problem type URI, safe user message key, retryability flag, and operator runbook where applicable.
- ERR-003 `BUDGET_EXHAUSTED`: map to a stable problem type URI, safe user message key, retryability flag, and operator runbook where applicable.
- ERR-004 `CHIEF_NO_PUBLISH`: map to a stable problem type URI, safe user message key, retryability flag, and operator runbook where applicable.
- ERR-005 `COMMITTEE_INVALID`: map to a stable problem type URI, safe user message key, retryability flag, and operator runbook where applicable.
- ERR-006 `CRITIC_REJECT`: map to a stable problem type URI, safe user message key, retryability flag, and operator runbook where applicable.
- ERR-007 `DEGRADED_ENVIRONMENT`: map to a stable problem type URI, safe user message key, retryability flag, and operator runbook where applicable.
- ERR-008 `DEGRADED_FATIGUE`: map to a stable problem type URI, safe user message key, retryability flag, and operator runbook where applicable.
- ERR-009 `DEGRADED_FORM`: map to a stable problem type URI, safe user message key, retryability flag, and operator runbook where applicable.
- ERR-010 `DEGRADED_GOALKEEPER`: map to a stable problem type URI, safe user message key, retryability flag, and operator runbook where applicable.
- ERR-011 `DEGRADED_MARKET`: map to a stable problem type URI, safe user message key, retryability flag, and operator runbook where applicable.
- ERR-012 `DEGRADED_PROVENANCE`: map to a stable problem type URI, safe user message key, retryability flag, and operator runbook where applicable.
- ERR-013 `DEGRADED_RESEARCH`: map to a stable problem type URI, safe user message key, retryability flag, and operator runbook where applicable.
- ERR-014 `DEGRADED_SET_PIECE`: map to a stable problem type URI, safe user message key, retryability flag, and operator runbook where applicable.
- ERR-015 `DEGRADED_SQUAD`: map to a stable problem type URI, safe user message key, retryability flag, and operator runbook where applicable.
- ERR-016 `DEGRADED_STATS`: map to a stable problem type URI, safe user message key, retryability flag, and operator runbook where applicable.
- ERR-017 `DEGRADED_TACTICS`: map to a stable problem type URI, safe user message key, retryability flag, and operator runbook where applicable.
- ERR-018 `F001`: map to a stable problem type URI, safe user message key, retryability flag, and operator runbook where applicable.
- ERR-019 `F002`: map to a stable problem type URI, safe user message key, retryability flag, and operator runbook where applicable.
- ERR-020 `F003`: map to a stable problem type URI, safe user message key, retryability flag, and operator runbook where applicable.
- ERR-021 `F004`: map to a stable problem type URI, safe user message key, retryability flag, and operator runbook where applicable.
- ERR-022 `F005`: map to a stable problem type URI, safe user message key, retryability flag, and operator runbook where applicable.
- ERR-023 `F006`: map to a stable problem type URI, safe user message key, retryability flag, and operator runbook where applicable.
- ERR-024 `F007`: map to a stable problem type URI, safe user message key, retryability flag, and operator runbook where applicable.
- ERR-025 `F008`: map to a stable problem type URI, safe user message key, retryability flag, and operator runbook where applicable.
- ERR-026 `F009`: map to a stable problem type URI, safe user message key, retryability flag, and operator runbook where applicable.
- ERR-027 `F010`: map to a stable problem type URI, safe user message key, retryability flag, and operator runbook where applicable.
- ERR-028 `F011`: map to a stable problem type URI, safe user message key, retryability flag, and operator runbook where applicable.
- ERR-029 `F012`: map to a stable problem type URI, safe user message key, retryability flag, and operator runbook where applicable.
- ERR-030 `F013`: map to a stable problem type URI, safe user message key, retryability flag, and operator runbook where applicable.
- ERR-031 `F014`: map to a stable problem type URI, safe user message key, retryability flag, and operator runbook where applicable.
- ERR-032 `F015`: map to a stable problem type URI, safe user message key, retryability flag, and operator runbook where applicable.
- ERR-033 `F016`: map to a stable problem type URI, safe user message key, retryability flag, and operator runbook where applicable.
- ERR-034 `F017`: map to a stable problem type URI, safe user message key, retryability flag, and operator runbook where applicable.
- ERR-035 `F018`: map to a stable problem type URI, safe user message key, retryability flag, and operator runbook where applicable.
- ERR-036 `F019`: map to a stable problem type URI, safe user message key, retryability flag, and operator runbook where applicable.
- ERR-037 `F020`: map to a stable problem type URI, safe user message key, retryability flag, and operator runbook where applicable.
- ERR-038 `F021`: map to a stable problem type URI, safe user message key, retryability flag, and operator runbook where applicable.
- ERR-039 `F022`: map to a stable problem type URI, safe user message key, retryability flag, and operator runbook where applicable.
- ERR-040 `F023`: map to a stable problem type URI, safe user message key, retryability flag, and operator runbook where applicable.
- ERR-041 `F024`: map to a stable problem type URI, safe user message key, retryability flag, and operator runbook where applicable.
- ERR-042 `F025`: map to a stable problem type URI, safe user message key, retryability flag, and operator runbook where applicable.
- ERR-043 `FINAL_VETO`: map to a stable problem type URI, safe user message key, retryability flag, and operator runbook where applicable.
- ERR-044 `FIXTURE_AMBIGUOUS`: map to a stable problem type URI, safe user message key, retryability flag, and operator runbook where applicable.
- ERR-045 `FIXTURE_NOT_FOUND`: map to a stable problem type URI, safe user message key, retryability flag, and operator runbook where applicable.
- ERR-046 `IDEMPOTENCY_CONFLICT`: map to a stable problem type URI, safe user message key, retryability flag, and operator runbook where applicable.
- ERR-047 `ILLEGAL_STATE_TRANSITION`: map to a stable problem type URI, safe user message key, retryability flag, and operator runbook where applicable.
- ERR-048 `INVALID_CUTOFF`: map to a stable problem type URI, safe user message key, retryability flag, and operator runbook where applicable.
- ERR-049 `INVALID_TIMEZONE`: map to a stable problem type URI, safe user message key, retryability flag, and operator runbook where applicable.
- ERR-050 `LESSON_REJECTED`: map to a stable problem type URI, safe user message key, retryability flag, and operator runbook where applicable.
- ERR-051 `LIVE_MARKET_UNAVAILABLE`: map to a stable problem type URI, safe user message key, retryability flag, and operator runbook where applicable.
- ERR-052 `LOCK_AFTER_KICKOFF`: map to a stable problem type URI, safe user message key, retryability flag, and operator runbook where applicable.
- ERR-053 `LOCK_FAILED`: map to a stable problem type URI, safe user message key, retryability flag, and operator runbook where applicable.
- ERR-054 `MARKET_MOVEMENT_UNEXPLAINED`: map to a stable problem type URI, safe user message key, retryability flag, and operator runbook where applicable.
- ERR-055 `MEMORY_WRITE_FAILED`: map to a stable problem type URI, safe user message key, retryability flag, and operator runbook where applicable.
- ERR-056 `MODEL_PRICE_UNKNOWN`: map to a stable problem type URI, safe user message key, retryability flag, and operator runbook where applicable.
- ERR-057 `MODEL_VERIFICATION_EXPIRED`: map to a stable problem type URI, safe user message key, retryability flag, and operator runbook where applicable.
- ERR-058 `NO_RELIABLE_ANALOGS`: map to a stable problem type URI, safe user message key, retryability flag, and operator runbook where applicable.
- ERR-059 `NO_VALID_LESSON`: map to a stable problem type URI, safe user message key, retryability flag, and operator runbook where applicable.
- ERR-060 `OWNERSHIP_DENIED`: map to a stable problem type URI, safe user message key, retryability flag, and operator runbook where applicable.
- ERR-061 `PREDICTION_ALREADY_LOCKED`: map to a stable problem type URI, safe user message key, retryability flag, and operator runbook where applicable.
- ERR-062 `PROVIDER_DISABLED`: map to a stable problem type URI, safe user message key, retryability flag, and operator runbook where applicable.
- ERR-063 `PROVIDER_QUOTA_EXHAUSTED`: map to a stable problem type URI, safe user message key, retryability flag, and operator runbook where applicable.
- ERR-064 `QUANT_INVALID`: map to a stable problem type URI, safe user message key, retryability flag, and operator runbook where applicable.
- ERR-065 `QUARANTINED_CLAIMS`: map to a stable problem type URI, safe user message key, retryability flag, and operator runbook where applicable.
- ERR-066 `RATE_LIMITED`: map to a stable problem type URI, safe user message key, retryability flag, and operator runbook where applicable.
- ERR-067 `RED_TEAM_VETO`: map to a stable problem type URI, safe user message key, retryability flag, and operator runbook where applicable.
- ERR-068 `RELIABILITY_SCORING_DEGRADED`: map to a stable problem type URI, safe user message key, retryability flag, and operator runbook where applicable.
- ERR-069 `RESULT_INCOMPLETE`: map to a stable problem type URI, safe user message key, retryability flag, and operator runbook where applicable.
- ERR-070 `REVISION_FAILED`: map to a stable problem type URI, safe user message key, retryability flag, and operator runbook where applicable.
- ERR-071 `SCENARIO_INVALID`: map to a stable problem type URI, safe user message key, retryability flag, and operator runbook where applicable.
- ERR-072 `SCHEMA_VALIDATION_FAILED`: map to a stable problem type URI, safe user message key, retryability flag, and operator runbook where applicable.
- ERR-073 `SOURCE_AFTER_CUTOFF`: map to a stable problem type URI, safe user message key, retryability flag, and operator runbook where applicable.
- ERR-074 `THESIS_SCORING_DEGRADED`: map to a stable problem type URI, safe user message key, retryability flag, and operator runbook where applicable.
- ERR-075 `UNRESOLVED_CONTRADICTION`: map to a stable problem type URI, safe user message key, retryability flag, and operator runbook where applicable.
- ERR-076 `VARIANCE_UNRESOLVED`: map to a stable problem type URI, safe user message key, retryability flag, and operator runbook where applicable.

## Appendix I. Final Self-Audit Before Declaring the Specification Implemented

- [ ] FINAL-AUDIT-001: Scan uses exactly three Istanbul calendar dates.
- [ ] FINAL-AUDIT-002: Manual search works from inside the app.
- [ ] FINAL-AUDIT-003: Ranking precedes deep analysis spend.
- [ ] FINAL-AUDIT-004: All requested specialist stages exist separately.
- [ ] FINAL-AUDIT-005: Current research is grounded and captured.
- [ ] FINAL-AUDIT-006: Sources are verified and normalized.
- [ ] FINAL-AUDIT-007: Contradictions and freshness are explicit.
- [ ] FINAL-AUDIT-008: Statistics and players are separate reports.
- [ ] FINAL-AUDIT-009: Tactics and form are separate reports.
- [ ] FINAL-AUDIT-010: Fatigue, goalkeeper, and set pieces are separate reports.
- [ ] FINAL-AUDIT-011: Environment is a separate report.
- [ ] FINAL-AUDIT-012: Odds use allowed provider abstraction.
- [ ] FINAL-AUDIT-013: Live odds monitoring respects provider limits.
- [ ] FINAL-AUDIT-014: Quant models are reproducible.
- [ ] FINAL-AUDIT-015: Historical similarity is leakage-safe.
- [ ] FINAL-AUDIT-016: Critics are independent.
- [ ] FINAL-AUDIT-017: Sonnet committee is high-value and bounded.
- [ ] FINAL-AUDIT-018: Scenarios are steelmanned.
- [ ] FINAL-AUDIT-019: Red team can veto.
- [ ] FINAL-AUDIT-020: Chief Analyst synthesizes.
- [ ] FINAL-AUDIT-021: Final critic gates publication.
- [ ] FINAL-AUDIT-022: Revision occurs at most once.
- [ ] FINAL-AUDIT-023: Prediction lock is immutable.
- [ ] FINAL-AUDIT-024: Post-match ingestion is separated.
- [ ] FINAL-AUDIT-025: Autopsy and variance are explicit.
- [ ] FINAL-AUDIT-026: Lessons are validated before memory.
- [ ] FINAL-AUDIT-027: RAG retrieval is agent-specific.
- [ ] FINAL-AUDIT-028: SQL, vector, time-series, and graph decisions are explicit.
- [ ] FINAL-AUDIT-029: Model IDs and prices are configuration-driven.
- [ ] FINAL-AUDIT-030: Model data is re-verified before implementation.
- [ ] FINAL-AUDIT-031: Repository structure is prescribed.
- [ ] FINAL-AUDIT-032: Database schemas and contracts exist.
- [ ] FINAL-AUDIT-033: Prompts and system instructions exist per agent.
- [ ] FINAL-AUDIT-034: DAG and state machine are defined.
- [ ] FINAL-AUDIT-035: API routes and UI components are defined.
- [ ] FINAL-AUDIT-036: Retry, caching, idempotency, and dedup are defined.
- [ ] FINAL-AUDIT-037: Tests and golden fixtures are defined.
- [ ] FINAL-AUDIT-038: Observability and security are defined.
- [ ] FINAL-AUDIT-039: Docker, migrations, seed, and mocks are defined.
- [ ] FINAL-AUDIT-040: Failure modes are defined.
- [ ] FINAL-AUDIT-041: Acceptance criteria and roadmap are defined.
- [ ] FINAL-AUDIT-042: Codex checklist is precise.
- [ ] FINAL-AUDIT-043: The real deliverable exceeds 6,000 lines.

---

End of canonical master implementation specification.
Any implementation claim must be backed by code, tests, and runtime evidence.
