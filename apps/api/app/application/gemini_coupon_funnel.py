import json
from datetime import UTC, datetime
from decimal import ROUND_HALF_UP, Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.domain.auto_coupon import AutoCandidate, FunnelDecision
from app.domain.registries import ModelRegistry, ModelRoute, ProviderRegistry
from app.infrastructure.gemini_client import GeminiClient, GeminiJsonRequest, GeminiJsonResult


class _FunnelOutput(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    selected_fixture_ids: list[UUID] = Field(min_length=0, max_length=6)
    rationale: str = Field(min_length=12, max_length=800)


class GeminiCouponFunnel:
    def __init__(
        self,
        *,
        api_key: str,
        base_url: str,
        model_registry: ModelRegistry,
        provider_registry: ProviderRegistry,
    ) -> None:
        self._api_key = api_key
        self._base_url = base_url
        self._models = model_registry
        self._providers = provider_registry

    async def select(
        self,
        candidates: tuple[AutoCandidate, ...],
        memory_context: tuple[str, ...],
    ) -> tuple[FunnelDecision, FunnelDecision, Decimal]:
        if not candidates:
            raise ValueError("AUTO_COUPON_NO_CANDIDATES")
        self._providers.require_enabled("google_gemini", "POST")
        rough_route = self._models.assert_route_eligible(
            "normalization", {"structured_output"}, datetime.now(UTC)
        )
        critic_route = self._models.assert_route_eligible(
            "critic", {"structured_output"}, datetime.now(UTC)
        )
        client = GeminiClient(self._api_key, self._base_url)
        try:
            rough_result = await client.generate_json(
                self._request(
                    route=rough_route,
                    candidates=candidates,
                    memory_context=memory_context,
                    stage="rough",
                    target=(
                        "0 ile 6 arasında maç seç. Kota doldurma; fiyat, veri veya belirsizlik "
                        "yeterli değilse boş liste döndür."
                    ),
                    thinking_level="minimal",
                )
            )
            rough_output = _FunnelOutput.model_validate(rough_result.output)
            rough_ids = self._validated_ids(
                rough_output.selected_fixture_ids,
                candidates,
                minimum=0,
                maximum=min(6, len(candidates)),
            )
            rough_candidates = tuple(item for item in candidates if item.fixture.id in rough_ids)
            if rough_candidates:
                critic_result = await client.generate_json(
                    self._request(
                        route=critic_route,
                        candidates=rough_candidates,
                        memory_context=memory_context,
                        stage="critic",
                        target=(
                            "0 ile 3 arasında maç seç. Popülerlik veya günlük hedef sayı için "
                            "seçim yapma; yalnız kanıt ve fiyat birlikte değer sunuyorsa geçir."
                        ),
                        thinking_level="low",
                    )
                )
                critic_output = _FunnelOutput.model_validate(critic_result.output)
                critic_ids = self._validated_ids(
                    critic_output.selected_fixture_ids,
                    rough_candidates,
                    minimum=0,
                    maximum=min(3, len(rough_candidates)),
                )
            else:
                critic_result = None
                critic_output = _FunnelOutput(
                    selected_fixture_ids=[],
                    rationale="Kaba elemede kanıt ve fiyat eşiğini geçen maç bulunmadı.",
                )
                critic_ids = ()
        finally:
            await client.close()

        initial_ids = tuple(item.fixture.id for item in candidates)
        rough = FunnelDecision(
            stage="rough",
            input_count=len(candidates),
            selected_fixture_ids=rough_ids,
            eliminated_fixture_ids=tuple(item for item in initial_ids if item not in rough_ids),
            rationale=rough_output.rationale,
            model_id=rough_route.model_id,
        )
        critic = FunnelDecision(
            stage="critic",
            input_count=len(rough_candidates),
            selected_fixture_ids=critic_ids,
            eliminated_fixture_ids=tuple(item for item in rough_ids if item not in critic_ids),
            rationale=critic_output.rationale,
            model_id=critic_route.model_id,
        )
        cost = self._cost(rough_route, rough_result)
        if critic_result is not None:
            cost += self._cost(critic_route, critic_result)
        return rough, critic, cost.quantize(Decimal(".000001"), rounding=ROUND_HALF_UP)

    @staticmethod
    def _request(
        *,
        route: ModelRoute,
        candidates: tuple[AutoCandidate, ...],
        memory_context: tuple[str, ...],
        stage: str,
        target: str,
        thinking_level: str,
    ) -> GeminiJsonRequest:
        packet = json.dumps(
            {
                "stage": stage,
                "selection_rule": target,
                "candidates": [item.model_dump(mode="json") for item in candidates],
                "validated_case_memory": memory_context,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
        return GeminiJsonRequest(
            model_id=route.model_id,
            system_instruction=(
                "Sen MİRON BABA otomatik maç eleme kurulundasın. Yalnızca verilen sekiz lig "
                "izin listesindeki maçları değerlendir. Meksika, Kolombiya veya başka lig ekleme. "
                "Eksik veriyi uydurma. Oran varsa zaman damgalı piyasa görüşü olarak kullan; kesinlik "
                "sayma. Günlük seçim kotası yoktur ve boş liste geçerli sonuçtur. 1.10 civarı açık "
                "favori galibiyetini yalnız popüler olduğu için seçme; fiyatın taşıdığı riske karşı "
                "ölçülebilir üstünlük ara. Geçmiş vaka hafızasını sonuç kopyalamak için değil hata "
                "mekanizmasını görmek için kullan. Türkçe ve kısa yaz."
            ),
            prompt=f"Aday havuzunu ele:\n{packet}",
            response_schema=_FunnelOutput.model_json_schema(),
            max_output_tokens=2_048,
            thinking_level=thinking_level,
        )

    @staticmethod
    def _validated_ids(
        output_ids: list[UUID],
        candidates: tuple[AutoCandidate, ...],
        *,
        minimum: int,
        maximum: int,
    ) -> tuple[UUID, ...]:
        unique_ids = tuple(dict.fromkeys(output_ids))
        allowed = {item.fixture.id for item in candidates}
        if not set(unique_ids).issubset(allowed):
            raise ValueError("AUTO_COUPON_UNKNOWN_FIXTURE")
        if not minimum <= len(unique_ids) <= maximum:
            raise ValueError("AUTO_COUPON_INVALID_SELECTION_COUNT")
        return unique_ids

    @staticmethod
    def _cost(route: ModelRoute, result: GeminiJsonResult) -> Decimal:
        if route.input_usd_per_mtok is None or route.output_usd_per_mtok is None:
            raise ValueError("MODEL_PRICE_UNKNOWN")
        output_tokens = result.candidates_token_count + result.thoughts_token_count
        return (
            Decimal(result.prompt_token_count) * route.input_usd_per_mtok
            + Decimal(output_tokens) * route.output_usd_per_mtok
        ) / Decimal("1000000")
