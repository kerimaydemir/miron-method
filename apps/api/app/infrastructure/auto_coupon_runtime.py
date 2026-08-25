import asyncio
import logging
from contextlib import suppress

from app.application.auto_coupons import AutoCouponService
from app.application.gemini_coupon_funnel import GeminiCouponFunnel
from app.infrastructure.analysis_runtime import analysis_service
from app.infrastructure.auto_coupon_repository import (
    NullAutoCouponRepository,
    PostgresAutoCouponRepository,
)
from app.infrastructure.config_loader import load_model_registry, load_provider_registry
from app.infrastructure.fixture_runtime import (
    analysis_fixture_provider,
    fixture_provider,
    odds_provider,
)
from app.infrastructure.post_match_runtime import post_match_service
from app.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

auto_coupon_repository = (
    PostgresAutoCouponRepository(settings.DATABASE_URL)
    if settings.PERSISTENCE_ENABLED
    else NullAutoCouponRepository()
)
coupon_funnel = (
    GeminiCouponFunnel(
        api_key=settings.GEMINI_API_KEY.get_secret_value(),
        base_url=settings.GEMINI_API_BASE_URL,
        model_registry=load_model_registry(settings.CONFIG_DIR / "models.yaml"),
        provider_registry=load_provider_registry(settings.CONFIG_DIR / "providers.yaml"),
    )
    if settings.GEMINI_ENABLED
    else None
)
auto_coupon_service = AutoCouponService(
    fixtures=fixture_provider,
    analysis_fixtures=analysis_fixture_provider,
    odds=odds_provider,
    analysis=analysis_service,
    post_match=post_match_service,
    repository=auto_coupon_repository,
    funnel=coupon_funnel,
    live_fixtures_available=settings.LIVE_FIXTURES_ENABLED,
    window_days=settings.AUTO_COUPON_WINDOW_DAYS,
    reuse_seconds=settings.AUTO_COUPON_REUSE_SECONDS,
    finalist_analysis_timeout_seconds=settings.AUTO_COUPON_FINALIST_ANALYSIS_TIMEOUT_SECONDS,
    force_daily_ticket=settings.AUTO_COUPON_FORCE_DAILY_TICKET,
    forced_min_combined_odds=settings.AUTO_COUPON_FORCED_MIN_COMBINED_ODDS,
    forced_max_combined_odds=settings.AUTO_COUPON_FORCED_MAX_COMBINED_ODDS,
    app_timezone=settings.APP_TIMEZONE,
)

_stop_event: asyncio.Event | None = None
_settlement_task: asyncio.Task[None] | None = None


async def start_auto_coupon_runtime() -> None:
    global _settlement_task, _stop_event
    if _settlement_task is None:
        _stop_event = asyncio.Event()
        _settlement_task = asyncio.create_task(
            _settlement_loop(_stop_event), name="auto-coupon-settlement"
        )


async def stop_auto_coupon_runtime() -> None:
    global _settlement_task, _stop_event
    if _stop_event is not None:
        _stop_event.set()
    if _settlement_task is not None:
        _settlement_task.cancel()
        with suppress(asyncio.CancelledError):
            await _settlement_task
        _settlement_task = None
    _stop_event = None


async def _settlement_loop(stop_event: asyncio.Event) -> None:
    while not stop_event.is_set():
        try:
            # Settlement depends on final fixture results, not on the pre-match
            # bookmaker feed still being configured or reachable.
            settled = await auto_coupon_service.settle_pending()
            reviewed = await auto_coupon_service.review_daily_predictions()
            if settled or reviewed:
                logger.info(
                    "Automatic coupon journal updated",
                    extra={"settled": settled, "reviewed": reviewed},
                )
        except Exception as error:
            logger.warning(
                "Automatic coupon settlement failed",
                extra={"error_type": type(error).__name__},
            )
        try:
            await asyncio.wait_for(
                stop_event.wait(), timeout=settings.AUTO_COUPON_SETTLEMENT_SECONDS
            )
        except TimeoutError:
            continue
