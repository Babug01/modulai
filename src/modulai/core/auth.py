"""BYOK key resolution — every caller (CLI, MCP server) goes through this.

The key is never written to disk, logged, or sent anywhere except directly to
the chosen provider's SDK client for the current invocation.
"""

from __future__ import annotations

import os

ENV_VAR_BY_PROVIDER = {
    "anthropic": "ANTHROPIC_API_KEY",
    "google": "GOOGLE_API_KEY",
}


class MissingApiKeyError(RuntimeError):
    pass


def resolve_api_key(explicit: str | None = None, model_provider: str = "anthropic") -> str:
    """Resolve the caller's own API key for the given provider.

    Precedence: an explicitly passed value (e.g. --api-key) beats the
    environment variable, so a one-off override never requires unsetting
    the env var first.
    """
    env_var = ENV_VAR_BY_PROVIDER.get(model_provider)
    if env_var is None:
        raise ValueError(f"Unknown model_provider '{model_provider}' — supported: {', '.join(ENV_VAR_BY_PROVIDER)}")

    key = explicit or os.environ.get(env_var)
    if not key:
        raise MissingApiKeyError(
            f"No API key found. Set {env_var} or pass --api-key. "
            f"This is your own {model_provider} key, billed to your own account — "
            "modulai never uses a shared or bundled key."
        )
    return key
