from app.application.analysis_runs import AnalysisRunService, utc_now
from app.application.gemini_analysis import GeminiAnalysisService
from app.domain.deep_evidence import DeepEvidenceProvider
from app.infrastructure.analysis_repository import (
    NullAnalysisRepository,
    PostgresAnalysisRepository,
)
from app.infrastructure.api_football_provider import ApiFootballProvider
from app.infrastructure.composite_deep_evidence_provider import CompositeDeepEvidenceProvider
from app.infrastructure.config_loader import load_model_registry, load_provider_registry
from app.infrastructure.fixture_runtime import analysis_fixture_provider, rapidapi_provider
from app.infrastructure.lock_object_store import S3LockObjectStore
from app.infrastructure.open_meteo_provider import OpenMeteoProvider
from app.infrastructure.sportmonks_provider import SportmonksProvider
from app.settings import get_settings

settings = get_settings()

analysis_repository = (
    PostgresAnalysisRepository(
        settings.DATABASE_URL,
        S3LockObjectStore(
            endpoint_url=settings.S3_ENDPOINT_URL,
            bucket=settings.S3_BUCKET_SNAPSHOTS,
            access_key_id=settings.S3_ACCESS_KEY_ID,
            secret_access_key=settings.S3_SECRET_ACCESS_KEY,
        ),
    )
    if settings.PERSISTENCE_ENABLED
    else NullAnalysisRepository()
)

gemini_analyzer = (
    GeminiAnalysisService(
        api_key=settings.GEMINI_API_KEY.get_secret_value(),
        base_url=settings.GEMINI_API_BASE_URL,
        model_registry=load_model_registry(settings.CONFIG_DIR / "models.yaml"),
        provider_registry=load_provider_registry(settings.CONFIG_DIR / "providers.yaml"),
        run_hard_cap_usd=settings.RUN_HARD_CAP_USD,
    )
    if settings.GEMINI_ENABLED
    else None
)

configured_deep_evidence_providers: list[DeepEvidenceProvider] = []
if settings.sportmonks_enabled:
    configured_deep_evidence_providers.append(
        SportmonksProvider(
            api_key=settings.SPORTMONKS_API_KEY.get_secret_value(),
            base_url=settings.SPORTMONKS_BASE_URL,
            requests_per_minute=settings.API_FOOTBALL_REQUESTS_PER_MINUTE,
        )
    )
if settings.api_football_enabled:
    configured_deep_evidence_providers.append(
        ApiFootballProvider(
            api_key=settings.API_FOOTBALL_API_KEY.get_secret_value(),
            base_url=settings.API_FOOTBALL_BASE_URL,
            requests_per_minute=settings.API_FOOTBALL_REQUESTS_PER_MINUTE,
            weather_provider=OpenMeteoProvider(
                forecast_base_url=settings.OPEN_METEO_FORECAST_BASE_URL,
                geocoding_base_url=settings.OPEN_METEO_GEOCODING_BASE_URL,
            ),
        )
    )
if rapidapi_provider is not None:
    configured_deep_evidence_providers.append(rapidapi_provider)

deep_evidence_provider = (
    CompositeDeepEvidenceProvider(tuple(configured_deep_evidence_providers))
    if len(configured_deep_evidence_providers) > 1
    else configured_deep_evidence_providers[0]
    if len(configured_deep_evidence_providers) == 1
    else None
)

analysis_service = AnalysisRunService(
    utc_now,
    analysis_repository,
    gemini_analyzer,
    analysis_fixture_provider,
    deep_evidence_provider,
)


async def stop_analysis_runtime() -> None:
    if isinstance(deep_evidence_provider, (ApiFootballProvider, SportmonksProvider)):
        await deep_evidence_provider.close()
    if isinstance(deep_evidence_provider, CompositeDeepEvidenceProvider):
        await deep_evidence_provider.close()
