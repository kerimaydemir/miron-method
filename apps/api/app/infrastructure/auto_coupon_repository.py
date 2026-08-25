from datetime import UTC, datetime
from decimal import ROUND_HALF_UP, Decimal
from typing import Any, NamedTuple, Protocol, cast
from uuid import NAMESPACE_URL, UUID, uuid5

from sqlalchemy import Engine, create_engine, text

from app.domain.auto_coupon import (
    AutoCouponPerformance,
    AutoCouponRun,
    CalibrationBand,
    MarketPerformance,
)
from app.infrastructure.analysis_repository import canonical_json, sha256_text


class PendingSelection(NamedTuple):
    auto_run_id: UUID
    fixture_id: UUID
    lock_id: UUID
    pick: str


class AutoCouponRepository(Protocol):
    def save(self, run: AutoCouponRun) -> None: ...

    def load(self, run_id: UUID) -> AutoCouponRun | None: ...

    def latest(self) -> AutoCouponRun | None: ...

    def recent(self, limit: int = 30) -> tuple[AutoCouponRun, ...]: ...

    def memory_context(self, query: str, limit: int = 8) -> tuple[str, ...]: ...

    def list_pending(self) -> tuple[PendingSelection, ...]: ...

    def mark_settled(
        self,
        *,
        auto_run_id: UUID,
        fixture_id: UUID,
        status: str,
        autopsy_id: UUID | None,
        home_score: int,
        away_score: int,
        post_match: dict[str, object],
    ) -> None: ...

    def update_run(self, run: AutoCouponRun) -> None: ...

    def performance(self) -> AutoCouponPerformance: ...


class NullAutoCouponRepository:
    def __init__(self) -> None:
        self._runs: dict[UUID, AutoCouponRun] = {}

    def save(self, run: AutoCouponRun) -> None:
        self._runs.setdefault(run.run_id, run)

    def load(self, run_id: UUID) -> AutoCouponRun | None:
        return self._runs.get(run_id)

    def latest(self) -> AutoCouponRun | None:
        return max(self._runs.values(), key=lambda run: run.observed_at, default=None)

    def recent(self, limit: int = 30) -> tuple[AutoCouponRun, ...]:
        return tuple(
            sorted(self._runs.values(), key=lambda run: run.observed_at, reverse=True)[:limit]
        )

    def memory_context(self, query: str, limit: int = 8) -> tuple[str, ...]:
        del query, limit
        return ()

    def list_pending(self) -> tuple[PendingSelection, ...]:
        return tuple(
            PendingSelection(run.run_id, item.fixture.id, item.lock_id, item.pick)
            for run in self._runs.values()
            for item in run.selections
            if item.settlement_status == "pending"
        )

    def mark_settled(
        self,
        *,
        auto_run_id: UUID,
        fixture_id: UUID,
        status: str,
        autopsy_id: UUID | None,
        home_score: int,
        away_score: int,
        post_match: dict[str, object],
    ) -> None:
        del autopsy_id, home_score, away_score, post_match
        run = self._runs.get(auto_run_id)
        if run is None:
            return
        selections = tuple(
            item.model_copy(
                update={
                    "settlement_status": status,
                    "process_verdict": _process_verdict(item, status),
                }
            )
            if item.fixture.id == fixture_id
            else item
            for item in run.selections
        )
        state = (
            "settled"
            if all(item.settlement_status != "pending" for item in selections)
            else run.state
        )
        self._runs[auto_run_id] = run.model_copy(update={"state": state, "selections": selections})

    def update_run(self, run: AutoCouponRun) -> None:
        self._runs[run.run_id] = run

    def performance(self) -> AutoCouponPerformance:
        selections = [
            item
            for run in self._runs.values()
            for item in run.selections
            if item.settlement_status != "pending"
        ]
        return _performance_from_records(
            [
                {
                    "market_key": item.market_key,
                    "settlement_status": item.settlement_status,
                    "probability": item.probability,
                    "market_decimal_odds": item.market_decimal_odds,
                    "process_verdict": item.process_verdict,
                }
                for item in selections
            ]
        )


class PostgresAutoCouponRepository:
    def __init__(self, database_url: str) -> None:
        self._engine: Engine = create_engine(database_url, pool_pre_ping=True)

    def save(self, run: AutoCouponRun) -> None:
        payload = canonical_json(run.model_dump(mode="json"))
        with self._engine.begin() as connection:
            connection.execute(
                text("""
                INSERT INTO auto_coupon_runs (
                  id, state, source_mode, run_json, actual_cost_usd, created_at, updated_at
                ) VALUES (
                  :id, :state, :source_mode, CAST(:payload AS jsonb), :cost, :created_at, :created_at
                ) ON CONFLICT (id) DO NOTHING
                """),
                {
                    "id": run.run_id,
                    "state": run.state,
                    "source_mode": run.source_mode,
                    "payload": payload,
                    "cost": run.actual_cost_usd,
                    "created_at": run.observed_at,
                },
            )
            if not run.selections:
                return
            self._ensure_fixture_refs(connection, run)
            self._ensure_forced_analysis_refs(connection, run)
            connection.execute(
                text("""
                INSERT INTO coupon_selections (
                  auto_coupon_run_id, fixture_id, analysis_run_id, prediction_lock_id,
                  pick, probability, model_fair_odds, market_decimal_odds
                  , market_key, market_label, outcome_label, line,
                  market_fair_probability, edge, bookmaker_count, price_observed_at,
                  value_score, rationale_json
                ) VALUES (
                  :auto_run_id, :fixture_id, :analysis_run_id, :lock_id,
                  :pick, :probability, :model_fair_odds, :market_odds,
                  :market_key, :market_label, :outcome_label, :line,
                  :market_fair_probability, :edge, :bookmaker_count, :price_observed_at,
                  :value_score, CAST(:rationale_json AS jsonb)
                ) ON CONFLICT (auto_coupon_run_id, fixture_id) DO NOTHING
                    """),
                [
                    {
                        "auto_run_id": run.run_id,
                        "fixture_id": item.fixture.id,
                        "analysis_run_id": item.analysis_run_id,
                        "lock_id": item.lock_id,
                        "pick": item.pick,
                        "probability": item.probability,
                        "model_fair_odds": item.model_fair_odds,
                        "market_odds": item.market_decimal_odds,
                        "market_key": item.market_key,
                        "market_label": item.market_label,
                        "outcome_label": item.outcome_label,
                        "line": item.line,
                        "market_fair_probability": item.market_fair_probability,
                        "edge": item.edge,
                        "bookmaker_count": item.bookmaker_count,
                        "price_observed_at": item.price_observed_at,
                        "value_score": item.value_score,
                        "rationale_json": canonical_json(
                            item.rationale.model_dump(mode="json")
                            if item.rationale is not None
                            else {}
                        ),
                    }
                    for item in run.selections
                ],
            )

    @staticmethod
    def _ensure_fixture_refs(connection: Any, run: AutoCouponRun) -> None:
        sport_id = UUID("92e3fa97-f0c3-5298-83f7-1bf958ad4879")
        connection.execute(
            text("""
            INSERT INTO sports (id, sport_key, plugin_key)
            VALUES (:id, 'football', 'football.v1')
            ON CONFLICT (sport_key) DO NOTHING
            """),
            {"id": sport_id},
        )
        for item in run.selections:
            competition_id = uuid5(
                NAMESPACE_URL,
                f"miron-baba-ai:competition:{item.fixture.competition_key}",
            )
            home_team_id = uuid5(
                NAMESPACE_URL,
                f"miron-baba-ai:team:{item.fixture.source_provider}:{item.fixture.home_team}",
            )
            away_team_id = uuid5(
                NAMESPACE_URL,
                f"miron-baba-ai:team:{item.fixture.source_provider}:{item.fixture.away_team}",
            )
            connection.execute(
                text("""
                INSERT INTO competitions (id, sport_id, competition_key, name)
                VALUES (:id, :sport_id, :competition_key, :name)
                ON CONFLICT (sport_id, competition_key)
                DO UPDATE SET name = EXCLUDED.name, updated_at = now()
                """),
                {
                    "id": competition_id,
                    "sport_id": sport_id,
                    "competition_key": item.fixture.competition_key,
                    "name": item.fixture.competition_name,
                },
            )
            connection.execute(
                text("""
                INSERT INTO teams (id, sport_id, name)
                VALUES (:id, :sport_id, :name)
                ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, updated_at = now()
                """),
                [
                    {"id": home_team_id, "sport_id": sport_id, "name": item.fixture.home_team},
                    {"id": away_team_id, "sport_id": sport_id, "name": item.fixture.away_team},
                ],
            )
            connection.execute(
                text("""
                INSERT INTO fixtures (
                  id, sport_id, competition_id, home_team_id, away_team_id,
                  kickoff_at, status
                ) VALUES (
                  :id, :sport_id, :competition_id, :home_team_id, :away_team_id,
                  :kickoff_at, :status
                ) ON CONFLICT (id) DO UPDATE SET
                  competition_id = EXCLUDED.competition_id,
                  home_team_id = EXCLUDED.home_team_id,
                  away_team_id = EXCLUDED.away_team_id,
                  kickoff_at = EXCLUDED.kickoff_at,
                  status = EXCLUDED.status,
                  updated_at = now(),
                  row_version = fixtures.row_version + 1
                """),
                {
                    "id": item.fixture.id,
                    "sport_id": sport_id,
                    "competition_id": competition_id,
                    "home_team_id": home_team_id,
                    "away_team_id": away_team_id,
                    "kickoff_at": item.fixture.kickoff_at,
                    "status": item.fixture.status,
                },
            )
            connection.execute(
                text("""
                INSERT INTO fixture_versions (
                  fixture_id, version, kickoff_at, status, observed_at
                ) VALUES (:fixture_id, 1, :kickoff_at, :status, :observed_at)
                ON CONFLICT (fixture_id, version) DO UPDATE SET
                  kickoff_at = EXCLUDED.kickoff_at,
                  status = EXCLUDED.status,
                  observed_at = EXCLUDED.observed_at
                """),
                {
                    "fixture_id": item.fixture.id,
                    "kickoff_at": item.fixture.kickoff_at,
                    "status": item.fixture.status,
                    "observed_at": item.fixture.observed_at or run.observed_at,
                },
            )

    @staticmethod
    def _ensure_forced_analysis_refs(connection: Any, run: AutoCouponRun) -> None:
        config = {
            "schema_version": "config-snapshot.v1",
            "mode": "forced_daily_banko",
            "model_ids": ["market-journal-forced"],
        }
        config_json = canonical_json(config)
        config_sha256 = sha256_text(config_json)
        config_snapshot_id = uuid5(NAMESPACE_URL, f"miron-baba-ai:config:{config_sha256}")
        connection.execute(
            text("""
            INSERT INTO config_snapshots (id, schema_version, config_json, sha256)
            VALUES (:id, 'config-snapshot.v1', CAST(:payload AS jsonb), :sha256)
            ON CONFLICT DO NOTHING
            """),
            {"id": config_snapshot_id, "payload": config_json, "sha256": config_sha256},
        )
        for item in run.selections:
            forecast_id = uuid5(
                NAMESPACE_URL, f"miron-baba-ai:forced-forecast:{item.analysis_run_id}"
            )
            forecast_json = canonical_json(
                {
                    "fixture_id": str(item.fixture.id),
                    "market_key": item.market_key,
                    "pick": item.pick,
                    "probability": str(item.probability),
                    "market_decimal_odds": str(item.market_decimal_odds),
                    "mode": "forced_daily_banko",
                }
            )
            manifest_json = canonical_json(
                {
                    "analysis_run_id": str(item.analysis_run_id),
                    "fixture_id": str(item.fixture.id),
                    "lock_id": str(item.lock_id),
                    "pick": item.pick,
                    "mode": "forced_daily_banko",
                }
            )
            manifest_sha256 = sha256_text(manifest_json)
            connection.execute(
                text("""
                INSERT INTO analysis_runs (
                  id, fixture_id, state, cutoff_at, kickoff_at_snapshot,
                  config_snapshot_id, prompt_bundle_version, actual_cost_usd,
                  correlation_id, created_at, updated_at
                ) VALUES (
                  :id, :fixture_id, 'LOCKED', :cutoff_at, :kickoff_at,
                  :config_id, 'forced-daily-banko.v1', 0,
                  :correlation_id, :created_at, :created_at
                ) ON CONFLICT (id) DO NOTHING
                """),
                {
                    "id": item.analysis_run_id,
                    "fixture_id": item.fixture.id,
                    "cutoff_at": run.observed_at,
                    "kickoff_at": item.fixture.kickoff_at,
                    "config_id": config_snapshot_id,
                    "correlation_id": uuid5(
                        NAMESPACE_URL,
                        f"miron-baba-ai:forced-correlation:{run.run_id}:{item.fixture.id}",
                    ),
                    "created_at": run.observed_at,
                },
            )
            connection.execute(
                text("""
                INSERT INTO forecast_versions (
                  id, analysis_run_id, version, forecast_json, forecast_sha256
                ) VALUES (
                  :id, :run_id, 1, CAST(:forecast AS jsonb), :sha256
                ) ON CONFLICT DO NOTHING
                """),
                {
                    "id": forecast_id,
                    "run_id": item.analysis_run_id,
                    "forecast": forecast_json,
                    "sha256": sha256_text(forecast_json),
                },
            )
            connection.execute(
                text("""
                INSERT INTO prediction_locks (
                  id, analysis_run_id, forecast_version_id, cutoff_at,
                  locked_at, kickoff_at_snapshot, manifest_json,
                  manifest_sha256, object_uri
                ) VALUES (
                  :id, :run_id, :forecast_id, :cutoff_at,
                  :locked_at, :kickoff_at, CAST(:manifest AS jsonb),
                  :sha256, :object_uri
                ) ON CONFLICT (id) DO NOTHING
                """),
                {
                    "id": item.lock_id,
                    "run_id": item.analysis_run_id,
                    "forecast_id": forecast_id,
                    "cutoff_at": run.observed_at,
                    "locked_at": run.observed_at,
                    "kickoff_at": item.fixture.kickoff_at,
                    "manifest": manifest_json,
                    "sha256": manifest_sha256,
                    "object_uri": f"forced://daily-banko/{item.lock_id}",
                },
            )

    def load(self, run_id: UUID) -> AutoCouponRun | None:
        with self._engine.connect() as connection:
            row = (
                connection.execute(
                    text("SELECT run_json, state FROM auto_coupon_runs WHERE id = :id"),
                    {"id": run_id},
                )
                .mappings()
                .one_or_none()
            )
            if row is None:
                return None
            statuses = {
                cast(UUID, item["fixture_id"]): (
                    str(item["settlement_status"]),
                    str(item["process_verdict"]),
                )
                for item in connection.execute(
                    text("""
                    SELECT fixture_id, settlement_status, process_verdict FROM coupon_selections
                    WHERE auto_coupon_run_id = :id
                    """),
                    {"id": run_id},
                ).mappings()
            }
        run = AutoCouponRun.model_validate(row["run_json"])
        selections = tuple(
            item.model_copy(
                update={
                    "settlement_status": statuses.get(item.fixture.id, ("pending", "pending"))[0],
                    "process_verdict": statuses.get(item.fixture.id, ("pending", "pending"))[1],
                }
            )
            for item in run.selections
        )
        return run.model_copy(update={"state": str(row["state"]), "selections": selections})

    def latest(self) -> AutoCouponRun | None:
        with self._engine.connect() as connection:
            run_id = connection.execute(
                text("SELECT id FROM auto_coupon_runs ORDER BY created_at DESC LIMIT 1")
            ).scalar_one_or_none()
        return self.load(cast(UUID, run_id)) if run_id is not None else None

    def recent(self, limit: int = 30) -> tuple[AutoCouponRun, ...]:
        with self._engine.connect() as connection:
            run_ids = tuple(
                connection.execute(
                    text("""
                    SELECT id FROM auto_coupon_runs
                    ORDER BY created_at DESC LIMIT :limit
                    """),
                    {"limit": limit},
                ).scalars()
            )
        return tuple(
            run for run_id in run_ids if (run := self.load(cast(UUID, run_id))) is not None
        )

    def memory_context(self, query: str, limit: int = 8) -> tuple[str, ...]:
        normalized = " ".join(query.split())
        with self._engine.connect() as connection:
            if normalized:
                statement = text("""
                SELECT search_text FROM case_memory_chunks
                WHERE to_tsvector('simple', search_text)
                      @@ plainto_tsquery('simple', :query)
                ORDER BY created_at DESC
                LIMIT :limit
                """)
                params: dict[str, object] = {"query": normalized, "limit": limit}
            else:
                statement = text("""
                SELECT search_text FROM case_memory_chunks
                ORDER BY created_at DESC LIMIT :limit
                """)
                params = {"limit": limit}
            rows = connection.execute(statement, params).scalars()
        return tuple(str(item) for item in rows)

    def list_pending(self) -> tuple[PendingSelection, ...]:
        with self._engine.connect() as connection:
            rows = connection.execute(
                text("""
                SELECT auto_coupon_run_id, fixture_id, prediction_lock_id, pick
                FROM coupon_selections WHERE settlement_status = 'pending'
                ORDER BY created_at
                """)
            ).mappings()
            return tuple(
                PendingSelection(
                    auto_run_id=cast(UUID, row["auto_coupon_run_id"]),
                    fixture_id=cast(UUID, row["fixture_id"]),
                    lock_id=cast(UUID, row["prediction_lock_id"]),
                    pick=str(row["pick"]),
                )
                for row in rows
            )

    def mark_settled(
        self,
        *,
        auto_run_id: UUID,
        fixture_id: UUID,
        status: str,
        autopsy_id: UUID | None,
        home_score: int,
        away_score: int,
        post_match: dict[str, object],
    ) -> None:
        now = datetime.now(UTC)
        with self._engine.begin() as connection:
            connection.execute(
                text("""
                UPDATE coupon_selections
                SET settlement_status = :status,
                    process_verdict = CASE
                      WHEN :status = 'void' THEN 'insufficient_data'
                      WHEN :status = 'won' AND edge >= 0.02 AND bookmaker_count >= 2
                        THEN 'sound_win'
                      WHEN :status = 'won' THEN 'lucky_win'
                      WHEN :status = 'lost' AND edge >= 0.02 AND bookmaker_count >= 2
                        THEN 'sound_but_unlucky_loss'
                      ELSE 'bad_process_loss'
                    END,
                    autopsy_id = :autopsy_id, settled_at = :now,
                    final_home_score = :home_score, final_away_score = :away_score,
                    post_match_json = CAST(:post_match AS jsonb)
                WHERE auto_coupon_run_id = :auto_run_id AND fixture_id = :fixture_id
                  AND settlement_status = 'pending'
                """),
                {
                    "status": status,
                    "autopsy_id": autopsy_id,
                    "now": now,
                    "home_score": home_score,
                    "away_score": away_score,
                    "post_match": canonical_json(post_match),
                    "auto_run_id": auto_run_id,
                    "fixture_id": fixture_id,
                },
            )
            pending = connection.execute(
                text("""
                SELECT count(*) FROM coupon_selections
                WHERE auto_coupon_run_id = :auto_run_id AND settlement_status = 'pending'
                """),
                {"auto_run_id": auto_run_id},
            ).scalar_one()
            if int(pending) == 0:
                connection.execute(
                    text("""
                    UPDATE auto_coupon_runs SET state = 'settled', updated_at = :now
                    WHERE id = :auto_run_id
                    """),
                    {"auto_run_id": auto_run_id, "now": now},
                )

    def update_run(self, run: AutoCouponRun) -> None:
        with self._engine.begin() as connection:
            connection.execute(
                text("""
                UPDATE auto_coupon_runs
                SET state = :state,
                    run_json = CAST(:payload AS jsonb),
                    actual_cost_usd = :cost,
                    updated_at = :updated_at
                WHERE id = :id
                """),
                {
                    "id": run.run_id,
                    "state": run.state,
                    "payload": canonical_json(run.model_dump(mode="json")),
                    "cost": run.actual_cost_usd,
                    "updated_at": datetime.now(UTC),
                },
            )

    def performance(self) -> AutoCouponPerformance:
        with self._engine.connect() as connection:
            rows = connection.execute(
                text("""
                SELECT market_key, settlement_status, probability,
                       market_decimal_odds, process_verdict
                FROM coupon_selections
                WHERE settlement_status <> 'pending'
                ORDER BY settled_at
                """)
            ).mappings()
            records = [dict(row) for row in rows]
        return _performance_from_records(records)


def _process_verdict(selection: object, status: str) -> str:
    if status == "void":
        return "insufficient_data"
    edge = getattr(selection, "edge", None)
    bookmaker_count = int(getattr(selection, "bookmaker_count", 0))
    sound = edge is not None and Decimal(edge) >= Decimal(".02") and bookmaker_count >= 2
    if status == "won":
        return "sound_win" if sound else "lucky_win"
    return "sound_but_unlucky_loss" if sound else "bad_process_loss"


def _performance_from_records(records: list[dict[str, object]]) -> AutoCouponPerformance:
    settled = len(records)
    wins = sum(1 for item in records if item["settlement_status"] == "won")
    losses = sum(1 for item in records if item["settlement_status"] == "lost")
    voids = sum(1 for item in records if item["settlement_status"] == "void")
    decided = wins + losses
    odds = [
        Decimal(str(item["market_decimal_odds"]))
        for item in records
        if item.get("market_decimal_odds") is not None
    ]
    probabilities = [Decimal(str(item["probability"])) for item in records]
    brier_items = [
        (
            Decimal(str(item["probability"]))
            - (Decimal("1") if item["settlement_status"] == "won" else Decimal("0"))
        )
        ** 2
        for item in records
        if item["settlement_status"] in ("won", "lost")
    ]
    profit = sum(
        [
            Decimal(str(item["market_decimal_odds"])) - Decimal("1")
            if item["settlement_status"] == "won"
            else Decimal("0")
            if item["settlement_status"] == "void"
            else Decimal("-1")
            for item in records
            if item.get("market_decimal_odds") is not None
        ],
        Decimal("0"),
    )
    process: dict[str, int] = {}
    for item in records:
        verdict = str(item.get("process_verdict") or "insufficient_data")
        process[verdict] = process.get(verdict, 0) + 1
    markets: list[MarketPerformance] = []
    for market_key in sorted({str(item["market_key"]) for item in records}):
        group = [item for item in records if str(item["market_key"]) == market_key]
        group_wins = sum(1 for item in group if item["settlement_status"] == "won")
        group_losses = sum(1 for item in group if item["settlement_status"] == "lost")
        group_voids = sum(1 for item in group if item["settlement_status"] == "void")
        group_odds = [
            Decimal(str(item["market_decimal_odds"]))
            for item in group
            if item.get("market_decimal_odds") is not None
        ]
        group_profit = sum(
            [
                Decimal(str(item["market_decimal_odds"])) - Decimal("1")
                if item["settlement_status"] == "won"
                else Decimal("0")
                if item["settlement_status"] == "void"
                else Decimal("-1")
                for item in group
                if item.get("market_decimal_odds") is not None
            ],
            Decimal("0"),
        )
        group_decided = group_wins + group_losses
        markets.append(
            MarketPerformance(
                market_key=market_key,
                settled=len(group),
                wins=group_wins,
                losses=group_losses,
                voids=group_voids,
                hit_rate=(Decimal(group_wins) / Decimal(group_decided)).quantize(
                    Decimal(".0001"), rounding=ROUND_HALF_UP
                )
                if group_decided
                else None,
                average_odds=(sum(group_odds, Decimal("0")) / len(group_odds)).quantize(
                    Decimal(".001"), rounding=ROUND_HALF_UP
                )
                if group_odds
                else None,
                equal_stake_roi=(group_profit / len(group_odds)).quantize(
                    Decimal(".0001"), rounding=ROUND_HALF_UP
                )
                if group_odds
                else None,
            )
        )
    sample_status = (
        "empty"
        if settled == 0
        else "early"
        if settled < 30
        else "monitor"
        if settled < 100
        else "meaningful"
    )
    calibration = _calibration_from_records(records)
    return AutoCouponPerformance(
        settled=settled,
        wins=wins,
        losses=losses,
        voids=voids,
        hit_rate=(Decimal(wins) / Decimal(decided)).quantize(
            Decimal(".0001"), rounding=ROUND_HALF_UP
        )
        if decided
        else None,
        average_odds=(sum(odds, Decimal("0")) / len(odds)).quantize(
            Decimal(".001"), rounding=ROUND_HALF_UP
        )
        if odds
        else None,
        average_predicted_probability=(
            sum(probabilities, Decimal("0")) / len(probabilities)
        ).quantize(Decimal(".0001"), rounding=ROUND_HALF_UP)
        if probabilities
        else None,
        brier_score=(sum(brier_items, Decimal("0")) / len(brier_items)).quantize(
            Decimal(".0001"), rounding=ROUND_HALF_UP
        )
        if brier_items
        else None,
        equal_stake_roi=(profit / len(odds)).quantize(Decimal(".0001"), rounding=ROUND_HALF_UP)
        if odds
        else None,
        process_verdicts=process,
        by_market=tuple(markets),
        calibration=calibration,
        sample_size_status=sample_status,
        notice=(
            "En az 30 sonuçlanmış seçimden önce oranlar yalnız erken sinyaldir; sistem gerçek para yatırmaz."
            if settled < 30
            else "Metrikler kilitli ön-maç tahminleri ve eşit birim simülasyonu üzerinden hesaplanır."
        ),
    )


def _calibration_from_records(records: list[dict[str, object]]) -> tuple[CalibrationBand, ...]:
    bands = (
        ("0.50-0.60", Decimal(".50"), Decimal(".60")),
        ("0.60-0.70", Decimal(".60"), Decimal(".70")),
        ("0.70-0.80", Decimal(".70"), Decimal(".80")),
        ("0.80-0.90", Decimal(".80"), Decimal(".90")),
        ("0.90-1.00", Decimal(".90"), Decimal("1.00")),
    )
    decided = [item for item in records if item["settlement_status"] in ("won", "lost")]
    result: list[CalibrationBand] = []
    for label, lower, upper in bands:
        group = [
            item
            for item in decided
            if lower <= Decimal(str(item["probability"]))
            and (Decimal(str(item["probability"])) < upper or upper == Decimal("1.00"))
        ]
        wins = sum(1 for item in group if item["settlement_status"] == "won")
        losses = sum(1 for item in group if item["settlement_status"] == "lost")
        settled = len(group)
        average_probability = (
            (
                sum((Decimal(str(item["probability"])) for item in group), Decimal("0"))
                / Decimal(settled)
            ).quantize(Decimal(".0001"), rounding=ROUND_HALF_UP)
            if settled
            else None
        )
        hit_rate = (
            (Decimal(wins) / Decimal(settled)).quantize(Decimal(".0001"), rounding=ROUND_HALF_UP)
            if settled
            else None
        )
        result.append(
            CalibrationBand(
                label=label,
                lower=lower,
                upper=upper,
                settled=settled,
                wins=wins,
                losses=losses,
                hit_rate=hit_rate,
                average_predicted_probability=average_probability,
                calibration_error=(
                    abs(hit_rate - average_probability).quantize(
                        Decimal(".0001"), rounding=ROUND_HALF_UP
                    )
                    if hit_rate is not None and average_probability is not None
                    else None
                ),
            )
        )
    return tuple(result)
