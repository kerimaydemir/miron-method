import pytest
from pydantic import ValidationError

from app.settings import Settings


@pytest.fixture(autouse=True)
def isolated_ai_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in (
        "AI_PROVIDER", "GEMINI_ENABLED", "GEMINI_API_KEY", "NVIDIA_ENABLED", "NVIDIA_API_KEY"
    ):
        monkeypatch.delenv(name, raising=False)


def test_key_alone_does_not_enable_model_spending() -> None:
    settings = Settings(NVIDIA_API_KEY="test-nvidia-key", GEMINI_API_KEY="test-gemini-key")

    assert settings.selected_ai_provider is None
    assert "test-nvidia-key" not in repr(settings)
    assert "test-gemini-key" not in repr(settings)


def test_explicit_nvidia_provider_requires_and_selects_nvidia() -> None:
    settings = Settings(
        AI_PROVIDER="nvidia_nim", NVIDIA_ENABLED=True, NVIDIA_API_KEY="test-nvidia-key"
    )

    assert settings.selected_ai_provider == "nvidia_nim"
    assert settings.GEMINI_ENABLED is False


def test_auto_provider_selects_only_enabled_provider() -> None:
    settings = Settings(NVIDIA_ENABLED=True, NVIDIA_API_KEY="test-nvidia-key")
    assert settings.selected_ai_provider == "nvidia_nim"


@pytest.mark.parametrize(
    "provider,enabled_field,key_error",
    [
        ("nvidia_nim", "NVIDIA_ENABLED", "NVIDIA_API_KEY_MISSING"),
        ("google_gemini", "GEMINI_ENABLED", "GEMINI_API_KEY_MISSING"),
    ],
)
def test_enabled_provider_without_key_fails_closed(
    provider: str, enabled_field: str, key_error: str
) -> None:
    with pytest.raises(ValidationError, match=key_error):
        Settings(**{"AI_PROVIDER": provider, enabled_field: True})


def test_enabling_two_providers_is_rejected() -> None:
    with pytest.raises(ValidationError, match="MULTIPLE_AI_PROVIDERS_ENABLED"):
        Settings(
            GEMINI_ENABLED=True,
            GEMINI_API_KEY="test-gemini-key",
            NVIDIA_ENABLED=True,
            NVIDIA_API_KEY="test-nvidia-key",
        )


def test_disabled_provider_cannot_be_overridden_by_enabled_flag() -> None:
    with pytest.raises(ValidationError, match="AI_PROVIDER_DISABLED_BUT_PROVIDER_ENABLED"):
        Settings(AI_PROVIDER="disabled", NVIDIA_ENABLED=True, NVIDIA_API_KEY="test-key")


def test_explicit_provider_with_disabled_flag_is_rejected() -> None:
    with pytest.raises(ValidationError, match="AI_PROVIDER_NOT_ENABLED"):
        Settings(AI_PROVIDER="nvidia_nim", NVIDIA_API_KEY="test-key")
