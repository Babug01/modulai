"""Turn a pinned schema + docs into module files, via the caller's own API key.

This is the one place a model call happens. Everything upstream (schema.py,
docs.py) is deterministic and model-free by design — the model only sees
already-verified structural facts, it never invents them.

Not runnable without the `anthropic` package installed and a real API key —
this module has not been executed against the live API yet.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

import anthropic

DEFAULT_MODEL = "claude-sonnet-5"

SYSTEM_PROMPT = """\
You generate a single Terraform module for one Azure resource type, following \
these non-negotiable rules:

1. Module manages exactly one resource instance. Never build for_each into the \
   module itself — multiplicity is the caller's responsibility. Document a \
   caller-side for_each example in the README instead.
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

Generate: main.tf, variables.tf, outputs.tf, README.md, tests/defaults.tftest.hcl
"""

_FILE_BLOCK_RE = re.compile(r'<file path="([^"]+)">\n(.*?)\n</file>', re.DOTALL)


@dataclass
class GeneratedFile:
    path: str
    content: str


def generate_module(
    api_key: str,
    resource_type: str,
    version: str,
    schema_json: str,
    docs_markdown: str,
    provider_source: str = "hashicorp/azurerm",
    model: str = DEFAULT_MODEL,
) -> list[GeneratedFile]:
    client = anthropic.Anthropic(api_key=api_key)

    response = client.messages.create(
        model=model,
        max_tokens=8000,
        system=SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": USER_PROMPT_TEMPLATE.format(
                resource_type=resource_type,
                provider_source=provider_source,
                version=version,
                schema_json=schema_json,
                docs_markdown=docs_markdown,
            ),
        }],
    )

    text = "".join(block.text for block in response.content if block.type == "text")
    files = [GeneratedFile(path=m.group(1), content=m.group(2)) for m in _FILE_BLOCK_RE.finditer(text)]

    if not files:
        raise ValueError("Model response contained no <file> blocks — nothing to write.")

    return files
