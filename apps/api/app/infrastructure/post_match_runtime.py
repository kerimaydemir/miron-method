from app.application.analysis_runs import utc_now
from app.application.post_match import NullPostMatchRepository, PostMatchService
from app.infrastructure.post_match_repository import PostgresPostMatchRepository
from app.settings import get_settings

settings = get_settings()
post_match_repository = (
    PostgresPostMatchRepository(settings.DATABASE_URL)
    if settings.PERSISTENCE_ENABLED
    else NullPostMatchRepository()
)
post_match_service = PostMatchService(utc_now, post_match_repository)
