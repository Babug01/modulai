"""modulai CLI — resource name in, tested module out.

    modulai generate azurerm_storage_account
    modulai generate azurerm_storage_account --provider-version 5.4.0 --out ./modules

Not runnable as-is in an environment without `terraform`, `checkov`, and the
`anthropic`/`click`/`requests` packages installed — none of this has been
executed end-to-end yet. See README.md's "Status" section.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import click

from modulai.core.auth import MissingApiKeyError, resolve_api_key
from modulai.core.docs import fetch_resource_doc, latest_provider_version
from modulai.core.generate import generate_module
from modulai.core.schema import fetch_provider_schema, input_schema, resource_schema
from modulai.core.validate import run_validation_pipeline


@click.group()
def main() -> None:
    """modulai — schema-grounded Terraform module generator."""


@main.command()
@click.argument("resource_type")
@click.option("--provider-version", default=None, help="Exact provider version, e.g. 5.4.0. Defaults to latest.")
@click.option("--provider-source", default="hashicorp/azurerm", help="Provider source address.")
@click.option("--out", "out_dir", default=None, help="Output directory. Defaults to ./terraform-<provider>-<resource>.")
@click.option("--api-key", default=None, help="Overrides ANTHROPIC_API_KEY for this run.")
@click.option("--skip-validate", is_flag=True, help="Skip the fmt/init/validate/test/checkov pipeline after generation.")
def generate(
    resource_type: str,
    provider_version: str | None,
    provider_source: str,
    out_dir: str | None,
    api_key: str | None,
    skip_validate: bool,
) -> None:
    """Generate a module for RESOURCE_TYPE, e.g. azurerm_storage_account."""
    provider_name = provider_source.split("/")[-1]

    try:
        key = resolve_api_key(api_key)
    except MissingApiKeyError as e:
        click.echo(str(e), err=True)
        sys.exit(1)

    version = provider_version or latest_provider_version(provider_name)
    click.echo(f"Pinning {provider_source} @ {version}")

    click.echo("Fetching provider schema (terraform init + providers schema -json)...")
    full_schema = fetch_provider_schema(version=version, provider_source=provider_source, provider_source_name=provider_name)
    raw_resource_schema = resource_schema(full_schema, resource_type, provider_source)
    resource_schema_json = json.dumps(input_schema(raw_resource_schema))

    click.echo("Fetching provider docs (pinned to the same version)...")
    docs_markdown = fetch_resource_doc(resource_type, version, provider_name)

    click.echo("Generating module...")
    files = generate_module(
        api_key=key,
        resource_type=resource_type,
        version=version,
        schema_json=resource_schema_json,
        docs_markdown=docs_markdown,
        provider_source=provider_source,
    )

    resource_suffix = resource_type.removeprefix(f"{provider_name}_")
    target = Path(out_dir or f"terraform-{provider_name}-{resource_suffix.replace('_', '-')}")
    for f in files:
        dest = target / f.path
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(f.content, encoding="utf-8")
    click.echo(f"Wrote {len(files)} files to {target}/")

    if skip_validate:
        return

    click.echo("Running validation pipeline (fmt, init, validate, test, checkov)...")
    report = run_validation_pipeline(target)
    for step in report.steps:
        status = "PASS" if step.passed else "FAIL"
        click.echo(f"  [{status}] {step.name}")
        if not step.passed:
            click.echo(step.output)

    if not report.all_passed:
        sys.exit(1)


if __name__ == "__main__":
    main()
