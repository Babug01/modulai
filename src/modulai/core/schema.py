"""Pin an exact provider version and introspect its real schema.

This is the ground-truth source for argument names, types, and required/
optional/nested-block structure — not the rendered registry page. The pin is
always exact (e.g. '= 5.4.0'), never a range: generating "for 5.4.0" must be
reproducible, not silently drift to whatever a range resolves to later.

Not runnable in an environment without the terraform CLI installed — this
module has not been executed against a real Terraform binary yet.
"""

from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

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
