"""Pin an exact provider version and introspect its real schema.

This is the ground-truth source for argument names, types, and required/
optional/nested-block structure — not the rendered registry page. The pin is
always exact (e.g. '= 5.4.0'), never a range: generating "for 5.4.0" must be
reproducible, not silently drift to whatever a range resolves to later.

fetch_provider_schema/resource_schema verified live against azurerm v5.4.0 —
102 top-level attributes on azurerm_storage_account, 11 nested block types,
matching the hand-built reference module. input_schema() is a direct
consequence of that same run: 74 of those 102 attributes are computed-only
exports (e.g. primary_blob_endpoint), not inputs — passing the raw schema to
the model and trusting a prompt instruction to skip them is exactly the kind
of thing this tool exists to not do.
"""

from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

# The alerting/monitoring resource type differs completely per cloud — both
# the resource name and its argument shape (Azure's `criteria` block vs AWS's
# flat statistic/comparison_operator/period fields vs GCP's condition_threshold
# with a filter string) are cloud-specific. Fetching *this* resource's own
# schema the same way as the primary resource — rather than hand-describing
# one cloud's shape in the generation prompt and assuming it fits all three —
# is what makes alerts.tf schema-grounded instead of guessed for AWS/GCP.
ALERT_RESOURCE_TYPE_BY_PROVIDER = {
    "azurerm": "azurerm_monitor_metric_alert",
    "aws": "aws_cloudwatch_metric_alarm",
    "google": "google_monitoring_alert_policy",
}

PROVIDERS_TF = """\
terraform {{
  required_providers {{
    {provider_source_name} = {{
      source  = "{provider_source}"
      version = "= {version}"
    }}
  }}
}}

provider "{provider_source_name}" {{
  features {{}}
  skip_provider_registration = true
}}
"""


class SchemaFetchError(RuntimeError):
    pass


def fetch_provider_schema(
    version: str,
    provider_source: str = "hashicorp/azurerm",
    provider_source_name: str = "azurerm",
    terraform_bin: str = "terraform",
) -> dict:
    """Run `terraform init` + `terraform providers schema -json` for an exact
    pinned provider version, in a throwaway workspace. Returns the parsed
    schema JSON for the whole provider (caller narrows to one resource type).
    """
    with tempfile.TemporaryDirectory(prefix="modulai_schema_") as tmpdir:
        tf_dir = Path(tmpdir)
        (tf_dir / "providers.tf").write_text(
            PROVIDERS_TF.format(
                provider_source_name=provider_source_name,
                provider_source=provider_source,
                version=version,
            ),
            encoding="utf-8",
        )

        init = subprocess.run(
            [terraform_bin, "init", "-input=false", "-backend=false"],
            cwd=tf_dir, capture_output=True, text=True, timeout=120,
        )
        if init.returncode != 0:
            raise SchemaFetchError(
                f"terraform init failed for {provider_source_name} {version}:\n{init.stdout}\n{init.stderr}"
            )

        schema = subprocess.run(
            [terraform_bin, "providers", "schema", "-json"],
            cwd=tf_dir, capture_output=True, text=True, timeout=60,
        )
        if schema.returncode != 0:
            raise SchemaFetchError(f"providers schema -json failed:\n{schema.stderr}")

        return json.loads(schema.stdout)


def resource_schema(full_schema: dict, resource_type: str, provider_source: str = "hashicorp/azurerm") -> dict:
    """Narrow the full provider schema down to one resource type's block."""
    provider_schemas = full_schema.get("provider_schemas", {})
    for key, entry in provider_schemas.items():
        if key.endswith(provider_source) or key == provider_source:
            resources = entry.get("resource_schemas", {})
            if resource_type in resources:
                return resources[resource_type]
    raise SchemaFetchError(f"{resource_type} not found in schema for {provider_source}")


def _filter_block(block: dict, is_top_level: bool = False) -> dict:
    attributes = {
        name: attr
        for name, attr in block.get("attributes", {}).items()
        if (attr.get("required") or attr.get("optional"))
        # `id` is every resource's implicit, provider-assigned identifier.
        # It's often marked optional+computed in newer provider schemas for
        # framework-internal reasons, but it is never a real settable input —
        # only excluded at the resource's own top level, since a nested block
        # could theoretically have a genuine field literally named `id`.
        and not (is_top_level and name == "id")
    }
    block_types = {
        name: {
            "nesting_mode": bt.get("nesting_mode"),
            "min_items": bt.get("min_items"),
            "max_items": bt.get("max_items"),
            "block": _filter_block(bt.get("block", {})),
        }
        for name, bt in block.get("block_types", {}).items()
    }
    return {"attributes": attributes, "block_types": block_types}


def input_schema(resource_schema_entry: dict) -> dict:
    """Recursively strip computed-only attributes (true outputs) from a
    resource schema, at every nesting level, keeping only what should become
    a module variable (required or optional). Without this, a computed-only
    export like `primary_blob_endpoint` — or `identity.principal_id` nested
    inside the `identity` block — sits in the same attribute list as real
    inputs, with only an easy-to-miss `computed: true` flag distinguishing it.
    Also drops the top-level `id` attribute — every resource's implicit,
    provider-assigned identifier, sometimes marked optional+computed in newer
    provider schemas, but never a real settable input (found live on
    azurerm_key_vault @ v5.4.0: `id` had `optional: true, computed: true`).
    """
    return _filter_block(resource_schema_entry.get("block", {}), is_top_level=True)


def cross_reference_with_docs(filtered: dict, documented_names: set[str]) -> dict:
    """Drop anything input_schema() kept that never actually appears
    documented as a settable (Required/Optional) argument anywhere in the
    provider's own docs (see docs.documented_argument_names).

    The `id` carve-out in _filter_block covers one universal, provider-wide
    case cheaply and without needing the docs at all. This covers everything
    else — found live: AWS's `tags_all` is optional+computed in the real
    schema exactly like `id` was, but it's provider-specific (a tag-merge
    output, not a real input), so a fixed name list doesn't generalize across
    providers the way cross-referencing against each provider's own docs does.
    """
    attributes = {name: attr for name, attr in filtered["attributes"].items() if name in documented_names}
    block_types = {
        name: {**bt, "block": cross_reference_with_docs(bt["block"], documented_names)}
        for name, bt in filtered["block_types"].items()
    }
    return {"attributes": attributes, "block_types": block_types}
