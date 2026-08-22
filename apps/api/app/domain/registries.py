from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ModelRoute(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    provider: str
    model_id: str
    capabilities: frozenset[str]
    input_usd_per_mtok: Decimal | None = Field(default=None, ge=0)
    cached_input_usd_per_mtok: Decimal | None = Field(default=None, ge=0)
    output_usd_per_mtok: Decimal | None = Field(default=None, ge=0)
    max_calls_per_run: int = Field(ge=1, le=100)


class ModelRegistry(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    schema_version: Literal["model-registry.v1"]
    verified_at: datetime | None
    verification_expires_at: datetime | None
    currency: Literal["USD"]
    routes: dict[str, ModelRoute]
    policies: dict[str, bool]

    def assert_route_eligible(
        self, route_key: str, required_capabilities: set[str], now: datetime
    ) -> ModelRoute:
        route = self.routes.get(route_key)
        if route is None:
            raise ValueError("MODEL_ROUTE_UNAVAILABLE")
        if (
            self.verified_at is None
            or self.verification_expires_at is None
            or self.verification_expires_at <= now
        ):
            raise ValueError("MODEL_VERIFICATION_EXPIRED")
        if not required_capabilities.issubset(route.capabilities):
            raise ValueError("MODEL_CAPABILITY_MISSING")
        if route.input_usd_per_mtok is None or route.output_usd_per_mtok is None:
            raise ValueError("MODEL_PRICE_UNKNOWN")
        return route


class ProviderPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    provider_type: str
    enabled: bool
    approval_status: str
    allowed_methods: frozenset[str]
    forbidden_actions: frozenset[str]


class ProviderRegistry(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    schema_version: Literal["provider-registry.v1"]
    providers: dict[str, ProviderPolicy]

    @model_validator(mode="after")
    def wagering_is_always_forbidden(self) -> "ProviderRegistry":
        for provider in self.providers.values():
            if "bet_placement" not in provider.forbidden_actions:
                raise ValueError("all providers must forbid bet placement")
        return self

    def require_enabled(self, provider_id: str, method: str) -> ProviderPolicy:
        provider = self.providers.get(provider_id)
        if provider is None or not provider.enabled:
            raise PermissionError("PROVIDER_DISABLED")
        if method not in provider.allowed_methods:
            raise PermissionError("PROVIDER_METHOD_FORBIDDEN")
        return provider
