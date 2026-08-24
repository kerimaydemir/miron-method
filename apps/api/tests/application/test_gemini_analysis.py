import re
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest

from app.application.gemini_analysis import GeminiAnalysisService
from app.domain.deep_evidence import DeepFootballEvidence, EvidenceArtifact
from app.infrastructure.config_loader import load_model_registry, load_provider_registry
from app.infrastructure.gemini_client import GeminiJsonRequest, GeminiJsonResult
from app.infrastructure.mock_fixture_provider import FEATURES, FIXTURES


class FakeGeminiClient:
    def __init__(self) -> None:
        self.model_ids: list[str] = []

    async def generate_json(self, request: GeminiJsonRequest) -> GeminiJsonResult:
        self.model_ids.append(request.model_id)
        properties = request.response_schema.get("properties", {})
        if "reports" in properties:
            stage_clause = re.search(
                r"Yalnızca aşağıdaki aşamaları.*?Kanıt paketi", request.prompt, re.DOTALL
            )
            assert stage_clause is not None
            stage_ids = re.findall(r"S\d{2}", stage_clause.group(0))
            output: dict[str, object] = {
                "reports": [
                    {
                        "stage_id": stage_id,
                        "summary": f"{stage_id} kanıtları eksikler belirtilerek denetlendi.",
                    }
                    for stage_id in stage_ids
                ]
            }
        elif "counter_evidence" in properties:
            output: dict[str, object] = {
                "summary": "Sağlanan sinyaller üzerinden kanıt dengesi çıkarıldı.",
                "decisive_evidence": ["Kapsama yüksek", "Güncellik sinyali güçlü"],
                "counter_evidence": ["Kadro belirsizliği sürüyor"],
                "data_limitations": ["Dış dünya takım verisi kullanılmadı"],
            }
        elif "requested_adjustments" in properties:
            output = {
                "summary": "Nihai tahmin aşırı güven ve tutarlılık açısından denetlendi.",
                "strongest_objection": "Eksik kadro kanıtı güven seviyesini sınırlamalıdır.",
                "requested_adjustments": ["Güven seviyesini temkinli tut"],
            }
        else:
            output = {
                "summary": "Kanıt zinciri temkinli nihai dağılımda sentezlendi.",
                "home_probability": 0.45,
                "draw_probability": 0.30,
                "away_probability": 0.25,
                "expected_home_goals": 1.4,
                "expected_away_goals": 1.1,
                "confidence": 0.58,
                "decisive_evidence": ["Kapsama sinyali yüksek", "Güncellik sinyali güçlü"],
                "uncertainty_drivers": ["Kadro verisi yok", "Takımlar pilot veridir"],
                "dissent_summary": ["Beraberlik senaryosu göz ardı edilmemeli"],
                "market_probabilities": [
                    {
                        "market_key": "totals",
                        "outcome_key": "over",
                        "probability": 0.64,
                        "line": 2.5,
                        "rationale": "xG toplamı ve maç akışı 2.5 üst senaryosunu destekliyor.",
                    },
                    {
                        "market_key": "btts",
                        "outcome_key": "yes",
                        "probability": 0.57,
                        "rationale": "İki takımın gol üretim kanalları dengeli görünüyor.",
                    },
                ],
            }
        return GeminiJsonResult(
            model_id=request.model_id,
            provider_request_id=f"request-{len(self.model_ids)}",
            output=output,
            prompt_token_count=1_000,
            candidates_token_count=300,
            thoughts_token_count=100,
        )

    async def close(self) -> None:
        return None


@pytest.mark.asyncio
async def test_three_gemini_models_fill_all_deep_stages_with_valid_costs() -> None:
    client = FakeGeminiClient()
    service = GeminiAnalysisService(
        api_key="test-key",
        base_url="https://example.invalid/v1beta",
        model_registry=load_model_registry(Path("/workspace/config/models.yaml")),
        provider_registry=load_provider_registry(Path("/workspace/config/providers.yaml")),
        run_hard_cap_usd=Decimal("2"),
        clock=lambda: datetime(2026, 8, 22, tzinfo=UTC),
        client=client,
    )

    result = await service.analyze(FIXTURES[0], FEATURES[0], datetime(2026, 8, 22, 8, tzinfo=UTC))

    assert set(client.model_ids) == {
        "gemini-3.5-flash-lite",
        "gemini-3.6-flash",
        "gemini-3.5-flash",
    }
    assert len(client.model_ids) == 11
    assert result.forecast.analysis_provider == "google_gemini"
    assert len(result.forecast.market_probabilities) == 2
    assert result.forecast.market_probabilities[0].market_key == "totals"
    assert len(result.forecast.model_ids) == 11
    assert sum(item.probability for item in result.forecast.outcome_probabilities) == Decimal("1")
    assert result.actual_cost_usd > 0
    assert result.actual_cost_usd <= Decimal("2")
    assert set(result.stage_costs) == {f"S{stage:02d}" for stage in range(1, 30)}
    assert set(result.stage_summaries) == {f"S{stage:02d}" for stage in range(1, 30)}
    assert "sentezlendi" in result.stage_summaries["S29"]


def test_deep_evidence_packet_is_compacted_for_gemini_prompt_limit() -> None:
    observed_at = datetime(2026, 8, 22, 8, tzinfo=UTC)
    large_record = {
        "headline": "Team news",
        "body": "Osasuna Levante " * 20_000,
        "players": [{"name": f"Player {index}", "note": "available"} for index in range(100)],
    }
    evidence = DeepFootballEvidence(
        provider="espn_public_soccer+api_football",
        provider_fixture_id="fixture-1",
        observed_at=observed_at,
        home_team_id=1,
        away_team_id=2,
        league_id=140,
        season=2026,
        artifacts=tuple(
            EvidenceArtifact(
                kind=f"artifact_{index}",
                endpoint=f"/endpoint/{index}",
                observed_at=observed_at,
                records=(large_record, large_record, large_record),
            )
            for index in range(45)
        ),
        coverage={"fixture": True, "news": True, "rosters": True},
    )

    packet = GeminiAnalysisService._evidence_packet(
        FIXTURES[0], FEATURES[0], observed_at, evidence
    )

    assert len(packet) < 200_000
    assert "prompt_compaction_note" in packet
    assert "record_count" in packet
