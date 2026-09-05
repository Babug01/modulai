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


def test_openai_provider_reads_its_own_env_var(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "openai-key")
    assert resolve_api_key(None, model_provider="openai") == "openai-key"


def test_providers_dont_cross_read_each_others_env_var(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "anthropic-key")
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    with pytest.raises(MissingApiKeyError):
        resolve_api_key(None, model_provider="google")


def test_unrecognized_provider_still_works_with_an_explicit_key():
    # The whole point of going through litellm: any provider it supports
    # (Groq, Mistral, Bedrock, ...) works via an explicit key even though
    # this tool has no built-in env-var name for it.
    assert resolve_api_key("groq-key", model_provider="groq") == "groq-key"


def test_unrecognized_provider_without_explicit_key_raises_a_clear_error(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    with pytest.raises(MissingApiKeyError, match="no known env var"):
        resolve_api_key(None, model_provider="groq")
