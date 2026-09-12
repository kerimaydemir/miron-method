import json
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from uuid import NAMESPACE_URL, UUID, uuid5

import pytest

from app.application.gemini_coupon_funnel import GeminiCouponFunnel
from app.domain.auto_coupon import TOP_LEAGUES, AutoCandidate, MarketOdds, MarketQuote
from app.domain.fixtures import CanonicalFixture
from app.domain.registries import ModelRegistry, ModelRoute
from app.infrastructure.config_loader import load_model_registry, load_provider_registry
from app.infrastructure.gemini_client import GeminiJsonRequest, GeminiJsonResult

NOW = datetime(2026, 8, 22, 9, 0, tzinfo=UTC)


class _FunnelClient:
    def __init__(self, selected_ids: tuple[UUID, ...]) -> None:
        self.selected_ids = selected_ids
        self.requests: list[GeminiJsonRequest] = []
        self.closed = False

    async def generate_json(self, request: GeminiJsonRequest) -> GeminiJsonResult:
        self.requests.append(request)
        return GeminiJsonResult(
            model_id=request.model_id,
            provider_request_id=f"funnel-request-{len(self.requests)}",
            output={
                "selected_fixture_ids": [str(item) for item in self.selected_ids],
                "rationale": "Güncel fiyat ve veri kapsamı belirsizlik sınırlarıyla değerlendirildi.",
            },
            prompt_token_count=900,
            candidates_token_count=100,
        )

    async def close(self) -> None:
        self.closed = True


def _candidate() -> AutoCandidate:
    return AutoCandidate(
        fixture=CanonicalFixture(
            id=uuid5(NAMESPACE_URL, "nvidia-funnel-fixture"),
            competition_key="oddsapiio:england-premier-league",
            competition_name="Premier League",
            home_team="Fulham FC",
            away_team="Chelsea FC",
            kickoff_at=NOW + timedelta(hours=8),
            source_provider="odds_api_io",
        ),
        league=TOP_LEAGUES[0],
        auto_score=80,
        memory_case_count=0,
        positive_factors=("İzinli lig",),
        risk_flags=("Doğrulanmış ilk 11 bekleniyor",),
    )


def _current_registry() -> ModelRegistry:
    registry = load_model_registry(Path("/workspace/config/models.yaml"))
    now = datetime.now(UTC)
    return registry.model_copy(
        update={"verified_at": now, "verification_expires_at": now + timedelta(days=1)}
    )


@pytest.mark.asyncio
async def test_nvidia_funnel_uses_injected_client_and_separate_model_routes() -> None:
    candidate = _candidate()
    client = _FunnelClient((candidate.fixture.id,))
    funnel = GeminiCouponFunnel(
        api_key="test-key",
        base_url="https://example.invalid/v1",
        model_registry=_current_registry(),
        provider_registry=load_provider_registry(Path("/workspace/config/providers.yaml")),
        provider_id="nvidia_nim",
        client=client,
    )

    rough, critic, cost = await funnel.select((candidate,), ())

    assert rough.selected_fixture_ids == (candidate.fixture.id,)
    assert critic.selected_fixture_ids == (candidate.fixture.id,)
    assert rough.model_id == "nvidia/nemotron-3.5-lightning-30b-a3b"
    assert critic.model_id == "nvidia/nemotron-3-super-120b-a12b"
    assert [request.model_id for request in client.requests] == [rough.model_id, critic.model_id]
    assert not any(request.enable_google_search for request in client.requests)
    assert cost == Decimal("0")
    assert client.closed is False
    await funnel.close()
    assert client.closed is True


@pytest.mark.asyncio
async def test_nvidia_funnel_preserves_no_selection_without_forced_model_call() -> None:
    client = _FunnelClient(())
    funnel = GeminiCouponFunnel(
        api_key="test-key",
        base_url="https://example.invalid/v1",
        model_registry=_current_registry(),
        provider_registry=load_provider_registry(Path("/workspace/config/providers.yaml")),
        provider_id="nvidia_nim",
        client=client,
    )

    rough, critic, _ = await funnel.select((_candidate(),), ())

    assert rough.selected_fixture_ids == ()
    assert critic.selected_fixture_ids == ()
    assert critic.input_count == 0
    assert len(client.requests) == 1


@pytest.mark.asyncio
async def test_funnel_refuses_mismatched_provider_before_calling_injected_client() -> None:
    registry = _current_registry()
    routes = dict(registry.routes)
    routes["critic"] = routes["critic"].model_copy(update={"provider": "google_gemini"})
    client = _FunnelClient(())
    funnel = GeminiCouponFunnel(
        api_key="test-key",
        base_url="https://example.invalid/v1",
        model_registry=registry.model_copy(update={"routes": routes}),
        provider_registry=load_provider_registry(Path("/workspace/config/providers.yaml")),
        provider_id="nvidia_nim",
        client=client,
    )

    with pytest.raises(ValueError, match="MODEL_PROVIDER_MISMATCH"):
        await funnel.select((_candidate(),), ())

    assert client.requests == []


@pytest.mark.asyncio
async def test_funnel_rejects_model_invented_fixture() -> None:
    client = _FunnelClient((uuid5(NAMESPACE_URL, "not-in-candidate-pool"),))
    funnel = GeminiCouponFunnel(
        api_key="test-key",
        base_url="https://example.invalid/v1",
        model_registry=_current_registry(),
        provider_registry=load_provider_registry(Path("/workspace/config/providers.yaml")),
        provider_id="nvidia_nim",
        client=client,
    )

    with pytest.raises(ValueError, match="AUTO_COUPON_UNKNOWN_FIXTURE"):
        await funnel.select((_candidate(),), ())

    assert len(client.requests) == 1


def test_funnel_request_uses_compact_market_snapshot_for_large_quote_sets() -> None:
    fixture = CanonicalFixture(
        id=uuid5(NAMESPACE_URL, "large-funnel-fixture"),
        competition_key="oddsapiio:england-premier-league",
        competition_name="Premier League",
        home_team="Fulham FC",
        away_team="Chelsea FC",
        kickoff_at=NOW + timedelta(hours=8),
        source_provider="odds_api_io",
        provider_fixture_id="72221172",
    )
    quotes = tuple(
        MarketQuote(
            provider="odds_api_io",
            observed_at=NOW,
            market_key="totals" if index % 2 else "spread",
            market_label="Toplam gol" if index % 2 else "Handikap",
            outcome_key="over" if index % 2 else "home",
            outcome_label="Üst" if index % 2 else "Ev sahibi",
            point=Decimal("2.5") if index % 2 else Decimal("-0.5"),
            decimal_odds=Decimal("1.80") + Decimal(index % 50) / Decimal("100"),
            fair_probability=Decimal(".45") + Decimal(index % 20) / Decimal("1000"),
            bookmaker_count=2 + index % 4,
        )
        for index in range(140)
    )
    candidate = AutoCandidate(
        fixture=fixture,
        league=TOP_LEAGUES[0],
        auto_score=91,
        market_odds=MarketOdds(
            provider="odds_api_io",
            event_id="72221172",
            observed_at=NOW,
            bookmaker_count=4,
            home_decimal=Decimal("3.80"),
            draw_decimal=Decimal("4.10"),
            away_decimal=Decimal("1.87"),
            fair_home_probability=Decimal(".25"),
            fair_draw_probability=Decimal(".24"),
            fair_away_probability=Decimal(".51"),
            quotes=quotes,
        ),
        memory_case_count=0,
        positive_factors=("Premier League izin listesinde",),
        risk_flags=("Kadro kapanışa kadar değişebilir",),
    )
    route = ModelRoute(
        provider="google_gemini",
        model_id="gemini-test",
        capabilities=frozenset({"structured_output"}),
        input_usd_per_mtok=Decimal(".10"),
        output_usd_per_mtok=Decimal(".40"),
        max_calls_per_run=1,
    )

    request = GeminiCouponFunnel._request(
        route=route,
        candidates=(candidate,),
        memory_context=tuple(f"case-{index}" for index in range(30)),
        stage="rough",
        target="test target",
        thinking_level="minimal",
    )
    packet = json.loads(request.prompt.split("\n", maxsplit=1)[1])

    assert len(request.prompt) < 200_000
    assert len(packet["candidates"][0]["market"]["quotes"]) == 24
    assert len(packet["validated_case_memory"]) == 12
