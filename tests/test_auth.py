import pytest

from modulai.core.auth import MissingApiKeyError, resolve_api_key


def test_explicit_key_wins_over_env(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "env-key")
    assert resolve_api_key("explicit-key") == "explicit-key"


def test_falls_back_to_env(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "env-key")
    assert resolve_api_key(None) == "env-key"


def test_raises_when_neither_set(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(MissingApiKeyError):
        resolve_api_key(None)


def test_google_provider_reads_its_own_env_var(monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "gemini-key")
    assert resolve_api_key(None, model_provider="google") == "gemini-key"


def test_providers_dont_cross_read_each_others_env_var(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "anthropic-key")
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    with pytest.raises(MissingApiKeyError):
        resolve_api_key(None, model_provider="google")


def test_unknown_provider_rejected():
    with pytest.raises(ValueError):
        resolve_api_key("some-key", model_provider="openai")
