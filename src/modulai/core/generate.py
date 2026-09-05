"""Turn a pinned schema + docs into module files, via the caller's own API key.

This is the one place a model call happens. Everything upstream (schema.py,
docs.py) is deterministic and model-free by design — the model only sees
already-verified structural facts, it never invents them.

Not restricted to a hand-picked list of providers: the actual call goes
through litellm, which normalizes 100+ providers (Anthropic, Gemini, OpenAI,
Groq, Mistral, Bedrock, local Ollama, ...) behind one interface, addressed by
a "<provider>/<model>" string — so whichever provider a user already has a
key for works, not just the ones this file happens to hardcode. Verified
live: litellm installs and imports cleanly, and its completion() signature
has the model/messages/api_key/max_tokens parameters this code relies on.
The DEFAULT_MODEL_BY_PROVIDER map below is only a convenience for the common
case (--model-provider anthropic with no --model given) — pass --model
explicitly for anything not in it.

litellm's completion() call itself has not been executed against a live
provider from this environment — needs a real key, by design, since this
tool never holds one.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# Found live: 8000 was too low. A full 6-file module (main.tf's many dynamic
# blocks + variables.tf + outputs.tf + alerts.tf + README.md + tests) needs
# more than that in visible output alone, and finish_reason='length' showed
# Gemini getting cut off well before the format's opening tag even survived
# in the response — some of the budget likely went to internal reasoning
# before visible output started. Generous headroom, not a tight estimate.
MAX_OUTPUT_TOKENS = 32000

DEFAULT_MODEL_BY_PROVIDER = {
    "anthropic": "anthropic/claude-sonnet-5",
    # gemini-2.5-flash was retired for new users as of live testing (Sept 2026)
    # — Google's own 404 response named gemini-3.6-flash as the replacement.
    # Model names drift; override with --model if this one goes stale too.
    "google": "gemini/gemini-3.6-flash",
    "openai": "openai/gpt-4o",
}

SYSTEM_PROMPT = """\
You generate a single Terraform module for one cloud resource type, following \
these non-negotiable rules:

1. Module manages exactly one resource instance. Never build for_each into the \
   module itself — multiplicity is the caller's responsibility. Document this in \
   the README as a "boring way" vs "for_each way" BEFORE/AFTER pair, not just the \
   final for_each snippet alone — show 2+ copy-pasted module blocks first, then the \
   single for_each block replacing them, then one sentence naming what each.key and \
   each.value are. A reader unfamiliar with for_each must see why it's better, not \
   just what it looks like.
2. Variable shape: top-level scalar arguments (name, location, simple flags) \
   are individual variables. Every nested block in the schema becomes its own \
   optional object-typed variable using `optional()` attributes, defaulting to \
   null when the whole block is omittable. Never one mega-object for everything, \
   never one variable per leaf attribute of a nested block.
3. Ground every argument, type, and required/optional flag in the schema JSON \
   provided below — never invent an argument that isn't in it. Use the provider \
   docs markdown only for human-readable descriptions.
4. required_providers version constraint: the exact version this was generated \
   against as the floor, with a ceiling at the next major version.
5. Generate tests/defaults.tftest.hcl using `mock_provider` (Terraform 1.7+) so \
   it runs with zero real cloud credentials. Cover: a minimal creation scenario, \
   one scenario exercising a commonly-used optional nested block, and one \
   scenario asserting a validation block correctly rejects bad input.
6. Follow Azure Verified Modules (AVM) structural conventions where they apply.
7. Generate alerts.tf: one resource of the ALERT RESOURCE TYPE given below — its \
   own schema is provided the same way as the primary resource's, ground every \
   argument in it exactly per rule 3, never assume it looks like any other cloud's \
   alerting resource (Azure nests criteria in a block, AWS is mostly flat top-level \
   fields, GCP uses a filter string — use whichever this schema actually shows). \
   `for_each` over a single `alert_rules` variable: `type = map(object({...}))` \
   mirroring that alert resource's own real inputs, EXCLUDING whatever identifies \
   which resource is being alerted on (name/scopes/target — that comes from the \
   loop context: each.key as the name, the primary resource's own `.id` as the \
   target) — `default = null`. The `for_each` expression MUST be \
   `var.alert_rules != null ? var.alert_rules : {}` — `for_each` errors on a bare \
   null, so guarding it in the expression itself is not optional. Never invent a \
   metric/filter value yourself — this is a generic pass-through, the caller \
   supplies real monitoring criteria for whichever cloud this module targets, not \
   a curated per-resource menu (that needs grounding this tool doesn't have yet). \
   Document in the README, explicitly, that `null` or omitting the variable both \
   mean "no alerts."
8. outputs.tf: every output is an individually named, curated value — the same \
   discipline as rule 2's variables, applied to outputs. NEVER emit a single output \
   that dumps an entire resource object (e.g. `output "resource" { value = \
   azurerm_storage_account.this }`) — found live: this fails Terraform's own \
   sensitive-value check the moment the resource has ANY sensitive attribute \
   anywhere in it, since the whole object inherits that sensitivity, and it defeats \
   the point of curated outputs regardless. Mark an individual output `sensitive = \
   true` whenever its value is a credential, key, connection string, or password.

Output each file wrapped exactly like this, one block per file, nothing else \
outside the blocks:

<file path="main.tf">
...content...
</file>
"""

USER_PROMPT_TEMPLATE = """\
Resource type: {resource_type}
Provider: {provider_source} @ {version} (exact pin)

Provider schema (ground truth for structure/types):
{schema_json}

Provider documentation (ground truth for descriptions only):
{docs_markdown}

Alert resource type for this cloud: {alert_resource_type}

Alert resource schema (ground truth for alerts.tf structure/types — same rules as above):
{alert_schema_json}

Alert resource documentation (ground truth for descriptions only):
{alert_docs_markdown}

Generate: main.tf, variables.tf, outputs.tf, alerts.tf, README.md, tests/defaults.tftest.hcl
"""

_FILE_BLOCK_RE = re.compile(r'<file path="([^"]+)">\n(.*?)\n</file>', re.DOTALL)


@dataclass
class GeneratedFile:
    path: str
    content: str


@dataclass
class _ModelCallResult:
    text: str
    finish_reason: str | None
    provider_specific_fields: dict | None


def _call_litellm(api_key: str, model: str, system_prompt: str, user_prompt: str) -> _ModelCallResult:
    import litellm  # lazy: only actually needed when generating, not for schema/docs/validate use

    response = litellm.completion(
        model=model,
        api_key=api_key,
        max_tokens=MAX_OUTPUT_TOKENS,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    choice = response.choices[0]
    return _ModelCallResult(
        text=choice.message.content,
        finish_reason=getattr(choice, "finish_reason", None),
        provider_specific_fields=getattr(choice, "provider_specific_fields", None),
    )


def generate_module(
    api_key: str,
    resource_type: str,
    version: str,
    schema_json: str,
    docs_markdown: str,
    alert_resource_type: str,
    alert_schema_json: str,
    alert_docs_markdown: str,
    provider_source: str = "hashicorp/azurerm",
    model_provider: str = "anthropic",
    model: str | None = None,
) -> list[GeneratedFile]:
    resolved_model = model or DEFAULT_MODEL_BY_PROVIDER.get(model_provider)
    if resolved_model is None:
        raise ValueError(
            f"No default model known for model_provider '{model_provider}' — "
            f"pass --model explicitly as a litellm model string, e.g. 'groq/llama-3.1-70b-versatile'. "
            f"Providers with a built-in default: {', '.join(DEFAULT_MODEL_BY_PROVIDER)}"
        )

    user_prompt = USER_PROMPT_TEMPLATE.format(
        resource_type=resource_type,
        provider_source=provider_source,
        version=version,
        schema_json=schema_json,
        docs_markdown=docs_markdown,
        alert_resource_type=alert_resource_type,
        alert_schema_json=alert_schema_json,
        alert_docs_markdown=alert_docs_markdown,
    )

    result = _call_litellm(api_key, resolved_model, SYSTEM_PROMPT, user_prompt)
    text = result.text
    files = [GeneratedFile(path=m.group(1), content=m.group(2)) for m in _FILE_BLOCK_RE.finditer(text)]

    if not files:
        # Found live on Gemini: a response that starts mid-word, mid-attribute
        # ("_policy.value.expiration_period" — missing the "sas" and
        # everything before it), well past where <file path="main.tf"> and
        # several earlier dynamic blocks should be. Whatever litellm handed
        # back had already lost its beginning — not a formatting mismatch,
        # not the model ignoring instructions. finish_reason and
        # provider_specific_fields are the two things that can actually
        # explain a gap like that (e.g. MAX_TOKENS with content dropped, or a
        # multi-part response where an earlier part went missing).
        import tempfile

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
            f.write(text)
            dump_path = f.name

        tag_index = text.find('<file path="')
        tag_diagnosis = (
            f"'<file path=\"' appears at character {tag_index} of {len(text)} total — "
            "regex likely failed to match its exact formatting (see the dump)."
            if tag_index != -1
            else f"'<file path=\"' does not appear anywhere in the {len(text)}-character response — "
            "either the model didn't use the required format, or (seen live on Gemini) "
            "the response is missing its own beginning."
        )
        length_hint = (
            f" finish_reason='length' means the response was cut off by the {MAX_OUTPUT_TOKENS}-token "
            "limit before completing — this resource's full module needs more room than that."
            if result.finish_reason == "length"
            else ""
        )
        raise ValueError(
            f"Model response contained no <file> blocks — nothing to write. "
            f"{tag_diagnosis} finish_reason={result.finish_reason!r}, "
            f"provider_specific_fields={result.provider_specific_fields!r}.{length_hint} "
            f"Full response saved to {dump_path}"
        )

    return files
