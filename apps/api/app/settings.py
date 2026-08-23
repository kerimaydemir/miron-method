from decimal import Decimal
from functools import lru_cache
from pathlib import Path
from zoneinfo import ZoneInfo

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore", case_sensitive=True)

    PRODUCT_NAME: str = "MİRON BABA AI"
    APP_ENV: str = "local"
    APP_TIMEZONE: str = "Europe/Istanbul"
    DATABASE_URL: str = "postgresql+psycopg://miron_baba_ai:local_only@postgres:5432/miron_baba_ai"
    REDIS_URL: str = "redis://redis:6379/0"
    TEMPORAL_ADDRESS: str = "temporal:7233"
    TEMPORAL_NAMESPACE: str = "miron-baba-ai"
    PERSISTENCE_ENABLED: bool = False
    S3_ENDPOINT_URL: str = "http://minio:9000"
    S3_BUCKET_SNAPSHOTS: str = "miron-baba-ai-snapshots"
    S3_ACCESS_KEY_ID: str = ""
    S3_SECRET_ACCESS_KEY: str = ""
    GEMINI_API_KEY: SecretStr = SecretStr("")
    GEMINI_API_BASE_URL: str = "https://generativelanguage.googleapis.com/v1beta"
    GEMINI_ENABLED: bool = False
    CONFIG_DIR: Path = Path("/workspace/config")
    LIVE_FIXTURES_ENABLED: bool = False
    OPENLIGADB_BASE_URL: str = "https://api.openligadb.de"
    OPENLIGADB_LEAGUES: str = "la1,dfb,bl1,bl2,bl3,ucl"
    OPENLIGADB_REFRESH_SECONDS: int = Field(default=60, ge=30, le=3_600)
    FOOTBALL_DATA_API_KEY: SecretStr = SecretStr("")
    FOOTBALL_DATA_BASE_URL: str = "https://api.football-data.org/v4"
    FOOTBALL_DATA_REFRESH_SECONDS: int = Field(default=300, ge=60, le=3_600)
    API_FOOTBALL_API_KEY: SecretStr = SecretStr("")
    API_FOOTBALL_BASE_URL: str = "https://v3.football.api-sports.io"
    API_FOOTBALL_REQUESTS_PER_MINUTE: int = Field(default=10, ge=1, le=1_200)
    API_FOOTBALL_CURRENT_ODDS_ENABLED: bool = False
    SPORTMONKS_API_KEY: SecretStr = SecretStr("")
    SPORTMONKS_BASE_URL: str = "https://api.sportmonks.com/v3/football"
    RAPIDAPI_KEY: SecretStr = SecretStr("")
    RAPIDAPI_HOST: str = "free-api-live-football-data.p.rapidapi.com"
    RAPIDAPI_REFRESH_SECONDS: int = Field(default=900, ge=300, le=86_400)
    RAPIDAPI_DEEP_REQUEST_LIMIT: int = Field(default=4, ge=1, le=8)
    OPEN_METEO_FORECAST_BASE_URL: str = "https://api.open-meteo.com/v1"
    OPEN_METEO_GEOCODING_BASE_URL: str = "https://geocoding-api.open-meteo.com/v1"
    THESPORTSDB_API_KEY: SecretStr = SecretStr("123")
    THESPORTSDB_BASE_URL: str = "https://www.thesportsdb.com/api/v1/json"
    SCOREBAT_API_KEY: SecretStr = SecretStr("")
    SCOREBAT_BASE_URL: str = "https://www.scorebat.com/video-api/v3"
    THE_ODDS_API_KEY: SecretStr = SecretStr("")
    THE_ODDS_API_BASE_URL: str = "https://api.the-odds-api.com/v4"
    THE_ODDS_WIDE_MARKETS: str = "h2h,totals"
    ODDS_API_IO_KEY: SecretStr = SecretStr("")
    ODDS_API_IO_BASE_URL: str = "https://api.odds-api.io/v3"
    ODDS_API_IO_BOOKMAKERS: str = "Bet365,Unibet"
    ODDS_API_IO_EVENTS_PER_LEAGUE: int = Field(default=3, ge=1, le=10)
    ODDS_REFRESH_SECONDS: int = Field(default=300, ge=60, le=3_600)
    AUTO_COUPON_WINDOW_DAYS: int = Field(default=1, ge=1, le=3)
    AUTO_COUPON_REUSE_SECONDS: int = Field(default=21_600, ge=60, le=86_400)
    AUTO_COUPON_SETTLEMENT_SECONDS: int = Field(default=300, ge=60, le=3_600)
    AUTOMATION_TOKEN: SecretStr = SecretStr("")
    MONTHLY_BUDGET_USD: Decimal = Field(default=Decimal("10.00"), ge=0)
    RUN_SOFT_CAP_USD: Decimal = Field(default=Decimal("0.50"), ge=0)
    RUN_HARD_CAP_USD: Decimal = Field(default=Decimal("2.00"), ge=0)

    @field_validator("PRODUCT_NAME")
    @classmethod
    def canonical_product_name(cls, value: str) -> str:
        if value != "MİRON BABA AI":
            raise ValueError("PRODUCT_NAME must be exactly MİRON BABA AI")
        return value

    @field_validator("APP_TIMEZONE")
    @classmethod
    def valid_timezone(cls, value: str) -> str:
        ZoneInfo(value)
        return value

    @field_validator("RUN_HARD_CAP_USD")
    @classmethod
    def hard_cap_positive(cls, value: Decimal) -> Decimal:
        if value <= 0:
            raise ValueError("RUN_HARD_CAP_USD must be positive")
        return value

    @property
    def openligadb_leagues(self) -> tuple[str, ...]:
        return tuple(
            item.strip().casefold() for item in self.OPENLIGADB_LEAGUES.split(",") if item.strip()
        )

    @property
    def odds_enabled(self) -> bool:
        return bool(self.THE_ODDS_API_KEY.get_secret_value())

    @property
    def odds_api_io_enabled(self) -> bool:
        return bool(self.ODDS_API_IO_KEY.get_secret_value())

    @property
    def football_data_enabled(self) -> bool:
        return bool(self.FOOTBALL_DATA_API_KEY.get_secret_value())

    @property
    def api_football_enabled(self) -> bool:
        return bool(self.API_FOOTBALL_API_KEY.get_secret_value())

    @property
    def api_football_current_odds_enabled(self) -> bool:
        return bool(
            self.API_FOOTBALL_CURRENT_ODDS_ENABLED and self.API_FOOTBALL_API_KEY.get_secret_value()
        )

    @property
    def rapidapi_enabled(self) -> bool:
        return bool(self.RAPIDAPI_KEY.get_secret_value() and self.RAPIDAPI_HOST)


@lru_cache
def get_settings() -> Settings:
    return Settings()
