"""Fetch provider documentation pinned to an exact release tag.

Used only for descriptive text (variable descriptions, README prose) — never
for structural facts (types, required/optional). Structure comes from
schema.py's `terraform providers schema -json`, which is the actual ground
truth; this module is deliberately not authoritative on its own.
"""

from __future__ import annotations

import re

import requests

GITHUB_RAW = "https://raw.githubusercontent.com/hashicorp/terraform-provider-{provider}/v{version}/website/docs/r/{doc_name}.html.markdown"
GITHUB_RELEASES_LATEST = "https://api.github.com/repos/hashicorp/terraform-provider-{provider}/releases/latest"

# Matches `* \`name\` - (Required) ...` and `* \`name\` - (Optional, **Deprecated**) ...`
# — the qualifier after Required/Optional varies (AWS adds ", Forces new resource",
# ", **Deprecated**", etc.), so only the leading word is matched, not the whole parenthetical.
_ARG_BULLET_RE = re.compile(r"^\*\s+`([a-zA-Z0-9_]+)`\s+-\s+\((?:Required|Optional)\b", re.MULTILINE)

# Section heading naming varies by provider: azurerm uses the plural "Attributes
# Reference" / "Arguments Reference", AWS uses the singular "Attribute Reference" /
# "Argument Reference" — found live, checking both providers' actual docs.
_ATTRIBUTES_HEADING_RE = re.compile(r"^## .*Attributes? Reference", re.MULTILINE)

# Matches the same bullet as _ARG_BULLET_RE but only when its qualifier includes
# **Deprecated** — found live on aws_s3_bucket: most of its arguments/blocks
# (cors_rule, versioning, lifecycle_rule, logging, acl, ...) are marked exactly
# this way in the docs, with AWS steering users to a separate dedicated resource
# instead. The schema itself doesn't mark nested blocks deprecated (only some
# top-level attributes do), so the docs are the only reliable signal for this.
_DEPRECATED_BULLET_RE = re.compile(r"^\*\s+`([a-zA-Z0-9_]+)`\s+-\s+\((?:Required|Optional)[^)]*\*\*Deprecated\*\*", re.MULTILINE)

# Same bullet shape, but only when the qualifier does NOT contain **Deprecated**
# — needed to resolve a name collision found live on aws_s3_bucket's own doc:
# the top-level `object_lock_enabled` argument is current and NOT deprecated,
# but the doc also has a *different*, nested `object_lock_configuration` block
# whose own inner argument happens to share the exact same name and IS marked
# **Deprecated**. Both are plain "* `object_lock_enabled` - (Optional...)"
# bullets with no structural marker distinguishing which scope they belong to,
# so a flat by-name regex conflates them. See deprecated_argument_names below.
_NON_DEPRECATED_BULLET_RE = re.compile(
    r"^\*\s+`([a-zA-Z0-9_]+)`\s+-\s+\((?:Required|Optional)(?:(?!\*\*Deprecated\*\*)[^)])*\)", re.MULTILINE
)


def latest_provider_version(provider: str = "azurerm") -> str:
    """Return the latest published version tag (e.g. '5.4.0'), no leading 'v'."""
    resp = requests.get(GITHUB_RELEASES_LATEST.format(provider=provider), timeout=15)
    resp.raise_for_status()
    tag = resp.json()["tag_name"]
    return tag.lstrip("v")


def fetch_resource_doc(resource_type: str, version: str, provider: str = "azurerm") -> str:
    """Fetch the markdown doc for a resource, pinned to an exact provider version.

    resource_type: full type, e.g. 'azurerm_storage_account'.
    version: exact version without leading 'v', e.g. '5.4.0'.
    """
    doc_name = resource_type.removeprefix(f"{provider}_")
    url = GITHUB_RAW.format(provider=provider, version=version, doc_name=doc_name)
    resp = requests.get(url, timeout=15)
    if resp.status_code == 404:
        raise FileNotFoundError(
            f"No doc found at {url} — the resource may have a different doc filename "
            "than its resource type suggests; check the provider's website/docs/r/ listing."
        )
    resp.raise_for_status()
    return resp.text


def documented_argument_names(doc_markdown: str) -> set[str]:
    """Names actually documented as settable (Required/Optional) anywhere in
    the doc — the main arguments section and every "A `<block>` block
    supports the following:" subsection use the same bullet format, at every
    nesting level, in one flat set.

    Exists because the schema alone isn't sufficient to tell a real input
    from a computed/merged value that happens to also be marked optional:
    found live, not by inspection — azurerm's `id` and AWS's `tags_all` both
    show `optional: true, computed: true` in the real schema despite neither
    ever being documented as something a user sets. Cross-referencing against
    the docs generalizes that fix instead of growing a per-provider name list.
    """
    heading = _ATTRIBUTES_HEADING_RE.search(doc_markdown)
    scoped = doc_markdown[: heading.start()] if heading else doc_markdown
    return set(_ARG_BULLET_RE.findall(scoped))


def deprecated_argument_names(doc_markdown: str) -> set[str]:
    """Names documented as settable but marked **Deprecated** — a freshly
    generated module should never expose these as first-class variables,
    since the provider itself is telling users to use something else instead.
    Subtract this from documented_argument_names()'s result (via
    schema.exclude_deprecated) before anything reaches the model.

    Only counts a name as deprecated if EVERY bulleted occurrence of it in the
    doc is marked deprecated. Found live on aws_s3_bucket: `object_lock_enabled`
    is a genuine, current top-level argument, but the same name also appears,
    marked **Deprecated**, inside the separate `object_lock_configuration`
    block's own doc section — a name collision across two different scopes,
    not one argument that's actually deprecated. Requiring unanimity means a
    collision like this is resolved by keeping the name (a real current
    argument is worse to silently drop than a deprecated one is to keep).
    """
    heading = _ATTRIBUTES_HEADING_RE.search(doc_markdown)
    scoped = doc_markdown[: heading.start()] if heading else doc_markdown
    deprecated = set(_DEPRECATED_BULLET_RE.findall(scoped))
    non_deprecated = set(_NON_DEPRECATED_BULLET_RE.findall(scoped))
    return deprecated - non_deprecated
