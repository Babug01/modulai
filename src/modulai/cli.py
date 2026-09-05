"""modulai CLI — resource name in, tested module out.

    modulai generate azurerm_storage_account
    modulai generate azurerm_storage_account --provider-version 5.4.0 --out ./modules
    modulai generate azurerm_storage_account --model-provider google       # Gemini free tier
    modulai generate azurerm_storage_account --model-provider groq --model groq/llama-3.1-70b-versatile --api-key ...

`--model-provider` isn't restricted to a fixed list — it's whatever litellm
supports, addressed by name. anthropic/google/openai have a built-in default
model; anything else needs `--model` given explicitly.

Not runnable as-is in an environment without `terraform`, `checkov`, and the
`litellm`/`click`/`requests` packages installed — none of this has been
executed end-to-end yet. See README.md's "Status" section.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import click

from modulai.core.auth import MissingApiKeyError, resolve_api_key
from modulai.core.docs import deprecated_argument_names, documented_argument_names, fetch_resource_doc, latest_provider_version
from modulai.core.generate import generate_module
from modulai.core.schema import (
    ALERT_RESOURCE_TYPE_BY_PROVIDER,
    cross_reference_with_docs,
    exclude_deprecated,
    fetch_provider_schema,
    input_schema,
    resource_schema,
)
from modulai.core.validate import run_validation_pipeline


@click.group()
def main() -> None:
    """modulai — schema-grounded Terraform module generator."""


@main.command()
@click.argument("resource_type")
@click.option("--provider-version", default=None, help="Exact provider version, e.g. 5.4.0. Defaults to latest.")
@click.option("--provider-source", default="hashicorp/azurerm", help="Provider source address.")
@click.option("--out", "out_dir", default=None, help="Output directory. Defaults to ./terraform-<provider>-<resource>.")
@click.option(
    "--model-provider",
    default="anthropic",
    help="Which AI provider generates the module — any litellm-supported provider name (anthropic, google, openai, groq, mistral, ...), not restricted to a fixed list. 'google' is Gemini's free tier (aistudio.google.com) — no billing needed.",
)
@click.option("--model", default=None, help="Exact litellm model string, e.g. 'groq/llama-3.1-70b-versatile'. Only needed for providers without a built-in default — see the error message if omitted.")
@click.option("--api-key", default=None, help="Overrides the model provider's env var for this run. Required for providers modulai doesn't know a conventional env var name for.")
@click.option("--skip-validate", is_flag=True, help="Skip the fmt/init/validate/test/checkov pipeline after generation.")
def generate(
    resource_type: str,
    provider_version: str | None,
    provider_source: str,
    out_dir: str | None,
    model_provider: str,
    model: str | None,
    api_key: str | None,
    skip_validate: bool,
) -> None:
    """Generate a module for RESOURCE_TYPE, e.g. azurerm_storage_account."""
    provider_name = provider_source.split("/")[-1]

    alert_resource_type = ALERT_RESOURCE_TYPE_BY_PROVIDER.get(provider_name)
    if alert_resource_type is None:
        click.echo(
            f"No known alert resource type for provider '{provider_name}' — "
            f"supported: {', '.join(ALERT_RESOURCE_TYPE_BY_PROVIDER)}",
            err=True,
        )
        sys.exit(1)

    try:
        key = resolve_api_key(api_key, model_provider)
    except MissingApiKeyError as e:
        click.echo(str(e), err=True)
        sys.exit(1)

    version = provider_version or latest_provider_version(provider_name)
    click.echo(f"Pinning {provider_source} @ {version}")

    click.echo("Fetching provider schema (terraform init + providers schema -json)...")
    full_schema = fetch_provider_schema(version=version, provider_source=provider_source, provider_source_name=provider_name)
    raw_resource_schema = resource_schema(full_schema, resource_type, provider_source)
    filtered_schema = input_schema(raw_resource_schema)

    click.echo("Fetching provider docs (pinned to the same version)...")
    docs_markdown = fetch_resource_doc(resource_type, version, provider_name)

    # Schema alone marks some attributes optional+computed despite them never
    # being real inputs (id, AWS's tags_all) — cross-reference against what's
    # actually documented as settable before this goes anywhere near the model.
    filtered_schema = cross_reference_with_docs(filtered_schema, documented_argument_names(docs_markdown))
    # Then drop anything documented as settable but deprecated (found live:
    # most of aws_s3_bucket's arguments/blocks point to a separate dedicated
    # resource instead) — a freshly generated module should never expose a
    # deprecated argument as if it were current best practice.
    filtered_schema = exclude_deprecated(filtered_schema, deprecated_argument_names(docs_markdown))
    resource_schema_json = json.dumps(filtered_schema)

    click.echo(f"Fetching alert resource schema+docs ({alert_resource_type})...")
    raw_alert_schema = resource_schema(full_schema, alert_resource_type, provider_source)
    filtered_alert_schema = input_schema(raw_alert_schema)
    alert_docs_markdown = fetch_resource_doc(alert_resource_type, version, provider_name)
    filtered_alert_schema = cross_reference_with_docs(filtered_alert_schema, documented_argument_names(alert_docs_markdown))
    filtered_alert_schema = exclude_deprecated(filtered_alert_schema, deprecated_argument_names(alert_docs_markdown))
    alert_schema_json = json.dumps(filtered_alert_schema)

    click.echo("Generating module...")
    files = generate_module(
        api_key=key,
        resource_type=resource_type,
        version=version,
        schema_json=resource_schema_json,
        docs_markdown=docs_markdown,
        alert_resource_type=alert_resource_type,
        alert_schema_json=alert_schema_json,
        alert_docs_markdown=alert_docs_markdown,
        provider_source=provider_source,
        model_provider=model_provider,
        model=model,
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
