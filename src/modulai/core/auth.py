"""BYOK key resolution — every caller (CLI, MCP server) goes through this.

The key is never written to disk, logged, or sent anywhere except directly to
litellm for the current invocation, which forwards it to whichever provider
model_provider names.
"""

from __future__ import annotations

import os

# Convenience only, for the common providers — not an allowlist. An unknown
# model_provider still works fine via an explicit --api-key; this dict only
# supplies the env-var name to check when no explicit key was given, so an
# arbitrary litellm-supported provider (Groq, Mistral, Bedrock, ...) works
# too as long as its key is passed explicitly rather than left to an env var
# this tool wouldn't know the conventional name for.
ENV_VAR_BY_PROVIDER = {
    "anthropic": "ANTHROPIC_API_KEY",
    "google": "GOOGLE_API_KEY",
    "openai": "OPENAI_API_KEY",
}


class MissingApiKeyError(RuntimeError):
    pass


def resolve_api_key(explicit: str | None = None, model_provider: str = "anthropic") -> str:
    """Resolve the caller's own API key for the given provider.

    Precedence: an explicitly passed value (e.g. --api-key) beats the
    environment variable, so a one-off override never requires unsetting
    the env var first. Works for any model_provider when a key is passed
    explicitly; env-var auto-detection only works for the providers in
    ENV_VAR_BY_PROVIDER, since that's the only place a conventional name is
    known.
    """
    env_var = ENV_VAR_BY_PROVIDER.get(model_provider)

    key = explicit or (os.environ.get(env_var) if env_var else None)
    if not key:
        hint = f"Set {env_var} or pass --api-key." if env_var else (
            f"'{model_provider}' has no known env var — pass --api-key explicitly."
        )
        raise MissingApiKeyError(
            f"No API key found. {hint} "
            f"This is your own {model_provider} key, billed to your own account — "
            "modulai never uses a shared or bundled key."
        )
    return key
