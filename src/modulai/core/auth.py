"""BYOK key resolution — every caller (CLI, MCP server) goes through this.

The key is never written to disk, logged, or sent anywhere except directly to
the Anthropic SDK client for the current invocation.
"""

from __future__ import annotations

import os

ENV_VAR = "ANTHROPIC_API_KEY"


class MissingApiKeyError(RuntimeError):
    pass


def resolve_api_key(explicit: str | None = None) -> str:
    """Resolve the caller's own Anthropic API key.

    Precedence: an explicitly passed value (e.g. --api-key) beats the
    environment variable, so a one-off override never requires unsetting
    the env var first.
    """
    key = explicit or os.environ.get(ENV_VAR)
    if not key:
        raise MissingApiKeyError(
            f"No API key found. Set {ENV_VAR} or pass --api-key. "
            "This is your own Anthropic key, billed to your own account — "
            "modulai never uses a shared or bundled key."
        )
    return key
