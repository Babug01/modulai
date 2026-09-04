"""modulai — consumable by Claude Code, Cursor, or any MCP host.

No separate VS Code extension needed: a host that already speaks MCP gets this
for free once the server is registered in its config, e.g. (Claude Code):

    {
      "mcpServers": {
        "modulai": {
          "command": "modulai-mcp",
          "env": { "ANTHROPIC_API_KEY": "<your own key>" }
        }
      }
    }

Not runnable without the `mcp` package installed — this has not been connected
to a real MCP host yet.
"""

from __future__ import annotations

import json

from mcp.server.fastmcp import FastMCP

from modulai.core.auth import resolve_api_key
from modulai.core.docs import fetch_resource_doc, latest_provider_version
from modulai.core.generate import generate_module
from modulai.core.schema import fetch_provider_schema, input_schema, resource_schema
from modulai.core.validate import run_validation_pipeline

mcp = FastMCP("modulai")


@mcp.tool()
def generate_terraform_module(
    resource_type: str,
    provider_version: str | None = None,
    provider_source: str = "hashicorp/azurerm",
    out_dir: str = ".",
) -> str:
    """Generate a schema-grounded, tested Terraform module for one resource type.

    resource_type: e.g. 'azurerm_storage_account'.
    provider_version: exact version, e.g. '5.4.0'. Omit for latest.
    out_dir: directory to write the module into.
    """
    provider_name = provider_source.split("/")[-1]
    key = resolve_api_key()
    version = provider_version or latest_provider_version(provider_name)

    full_schema = fetch_provider_schema(version=version, provider_source=provider_source, provider_source_name=provider_name)
    raw_resource_schema = resource_schema(full_schema, resource_type, provider_source)
    resource_schema_json = json.dumps(input_schema(raw_resource_schema))
    docs_markdown = fetch_resource_doc(resource_type, version, provider_name)

    files = generate_module(
        api_key=key,
        resource_type=resource_type,
        version=version,
        schema_json=resource_schema_json,
        docs_markdown=docs_markdown,
        provider_source=provider_source,
    )

    from pathlib import Path
    target = Path(out_dir)
    for f in files:
        dest = target / f.path
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(f.content, encoding="utf-8")

    return f"Generated {len(files)} files in {target}: " + ", ".join(f.path for f in files)


@mcp.tool()
def validate_terraform_module(module_dir: str) -> str:
    """Run fmt/init/validate/test/checkov against an existing module directory."""
    from pathlib import Path
    report = run_validation_pipeline(Path(module_dir))
    lines = [f"[{'PASS' if s.passed else 'FAIL'}] {s.name}" for s in report.steps]
    return "\n".join(lines)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
