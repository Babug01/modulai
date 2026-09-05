# modulai

## Terraform Module Generator (Azure, AWS, GCP)

Give it a resource type — `azurerm_storage_account`, `aws_s3_bucket`,
`google_storage_bucket` — and get back a complete, parameterized Terraform
module: grounded in the provider's real schema and real documentation, not
a model's memory of them, with generated tests and a security scan already
run against the output before you ever see it.

No hosting, no account with us, no server to operate. It's BYOK — every
generation call uses your own API key, run entirely on your own machine.
Not restricted to one AI vendor: model calls go through
[litellm](https://github.com/BerriAI/litellm), which normalizes 100+
providers behind one interface, so whichever one you already have a key for
works — **Anthropic**, **Google Gemini** (genuinely free tier via Google AI
Studio, no billing account needed), **OpenAI**, Groq, Mistral, Bedrock, local
Ollama, and more. Anthropic/Google/OpenAI have a built-in default model;
anything else just needs `--model` given explicitly.

---

## Requirements

| Tool | Why |
|---|---|
| **Terraform >= 1.7** | Schema introspection (`terraform providers schema -json`) and the generated tests' `mock_provider` support both need this version or later |
| **Python >= 3.10** | Runtime for the CLI/MCP server |
| **An API key for one AI provider** | Any litellm-supported provider — Anthropic and OpenAI are billed, Google's Gemini free tier needs no card at all (aistudio.google.com). Yours, never stored or transmitted anywhere except directly to that provider for the current run |
| **Checkov** *(optional)* | The security-scan step. Skippable with `--skip-validate`, or the pipeline just reports that step as failed/missing rather than blocking generation |

## Install

```bash
pip install -e ".[dev,mcp]"
```

`litellm` is a base dependency now — no per-provider install step, since one
library covers all of them. This installs two console scripts: `modulai`
(the CLI) and `modulai-mcp` (the MCP server). `[mcp]` is only needed if you
plan to use the MCP server; omit it for CLI-only use.

**If `modulai` fails to launch at all** (`Access is denied` / `ResourceUnavailable` trying to start `modulai.exe`) — found live, on a locked-down Windows machine: some AV/EDR software blocks freshly pip-created `.exe` launcher stubs from running, even though `python.exe` itself runs fine. Use `python -m modulai` instead of the bare `modulai` command — same CLI, routes through `python.exe` directly instead of the stub:

```bash
python -m modulai generate azurerm_storage_account
```

---

## How to run it

### Option 1 — CLI

```bash
export ANTHROPIC_API_KEY=sk-ant-...     # your own key — set in your own shell, never share it
modulai generate azurerm_storage_account
```

That's the entire interaction for Azure, since `hashicorp/azurerm` is the
default provider. For AWS or GCP, say so explicitly:

```bash
modulai generate aws_s3_bucket --provider-source hashicorp/aws
modulai generate google_storage_bucket --provider-source hashicorp/google
```

**Using Gemini's free tier instead** (no billing account needed at all):

```bash
export GOOGLE_API_KEY=...     # from aistudio.google.com — free, no card required
modulai generate azurerm_storage_account --model-provider google
```

**Using any other litellm-supported provider** — `--model-provider` isn't a
fixed list, it's whatever litellm recognizes. Providers without a built-in
default need `--model` (the exact litellm model string) and `--api-key`
(since this tool won't know that provider's conventional env var name):

```bash
modulai generate azurerm_storage_account \
  --model-provider groq --model groq/llama-3.1-70b-versatile --api-key gsk_...
```

`--api-key` always overrides whichever env var a provider reads, for a
single run, for any provider.

What happens, in order: pin the exact provider version → fetch its real
schema via `terraform init` + `providers schema -json` → fetch its real docs
from GitHub, pinned to the same version tag → generate the module → run
`fmt` → `init` → `validate` → `test` → `checkov` against the result → report
pass/fail per step. Output lands in `./terraform-<provider>-<resource>/`
unless `--out` says otherwise.

### Option 2 — MCP server

Register it with any MCP-speaking host (Claude Code, Cursor, etc.) instead of
running the CLI directly:

```json
{
  "mcpServers": {
    "modulai": {
      "command": "modulai-mcp",
      "env": { "ANTHROPIC_API_KEY": "<your own key>" }
    }
  }
}
```

Swap the env var for whichever provider you're using (`GOOGLE_API_KEY`,
`OPENAI_API_KEY`, ...) and pass `model_provider`/`model` as tool call
arguments when invoking `generate_terraform_module`.

This exposes two tools the host's assistant can call directly in
conversation — no separate VS Code extension needed, since any MCP-aware
editor assistant already gets this for free once registered:

- **`generate_terraform_module`** — same generation flow as the CLI
- **`validate_terraform_module`** — run just the fmt/init/validate/test/checkov pipeline against a module directory you already have, without generating anything new

---

## Inputs it accepts

| Input | Where | Required | Default | Notes |
|---|---|---|---|---|
| `resource_type` | CLI positional arg / MCP param | **Yes** | — | Full type, e.g. `azurerm_storage_account`. Must start with the provider's short name followed by `_` (see restrictions) |
| `--provider-version` / `provider_version` | flag / MCP param | No | latest published release | Exact version only (e.g. `5.4.0`), never a range — see the versioning policy below |
| `--provider-source` / `provider_source` | flag / MCP param | No | `hashicorp/azurerm` | Must be overridden for AWS (`hashicorp/aws`) or GCP (`hashicorp/google`) — see restrictions |
| `--out` / `out_dir` | flag / MCP param | No | `./terraform-<provider>-<resource>` | Output directory |
| `--model-provider` / `model_provider` | flag / MCP param | No | `anthropic` | Any litellm-supported provider name, not a fixed list — `anthropic`, `google`, `openai`, `groq`, `mistral`, etc. |
| `--model` / `model` | flag / MCP param | No | built-in default for anthropic/google/openai only | Exact litellm model string (e.g. `groq/llama-3.1-70b-versatile`) — required for any provider without a built-in default |
| `--api-key` | CLI flag only | No | that provider's conventional env var, if known (`$ANTHROPIC_API_KEY` / `$GOOGLE_API_KEY` / `$OPENAI_API_KEY`) | Overrides the env var for a single run; required outright for providers with no known conventional env var name. The MCP server only reads env vars, by design (no key is ever passed through a conversation) |
| `--skip-validate` | CLI flag only | No | off | Skips the fmt/init/validate/test/checkov pass entirely |

**No other input is accepted, deliberately** — the whole point is that a
resource name (plus, optionally, a provider and version) is enough. Anything
about the resource's actual shape comes from its own schema and docs, never
from the user having to describe it.

### Versioning policy

`--provider-version 5.4.0` pins the **exact** version for schema
introspection — deterministic, reproducible, never silently drifts to a
newer patch. The *generated module's own* `required_providers` constraint
then declares `>= 5.4.0, < 6.0.0` — a floor at the version actually
generated against (not a loose major-version floor that could reference
arguments an earlier patch doesn't have yet) with a ceiling at the next
major, since that's typically where a provider's breaking changes land.

## Restrictions and known limitations

- **Only providers published under the `hashicorp` GitHub org resolve docs automatically.** The docs-fetch URL is hardcoded to `github.com/hashicorp/terraform-provider-<name>` — third-party providers (Cloudflare, Datadog, etc., anything not published by HashiCorp itself) aren't supported yet.
- **One resource per module, by design** — not a limitation to fix, a deliberate choice. See "Module design" below for why, and how to still create many resources from one module reference.
- **Requires outbound internet access** to GitHub (raw content + API), `registry.terraform.io` (via `terraform init`), and whichever AI provider's API you use. No offline/air-gapped mode.
- **litellm is a real dependency trade-off, made deliberately.** Every other piece of this tool fetches its own ground truth directly (real schema JSON, real docs markdown) rather than trusting an abstraction. The model call is the one exception: instead of hand-writing a call function per provider, it goes through litellm, which normalizes 100+ providers behind one interface. That's what makes "whichever provider you already have a key for" possible without writing a new function per vendor — but it does mean one more layer between this tool and the actual API call that isn't independently re-verified here. Confirmed live: litellm installs and imports cleanly, and its `completion()` signature has the `model`/`messages`/`api_key`/`max_tokens` parameters this code relies on — the call itself hasn't been exercised against a real provider from this environment.
- **The doc-filename derivation is a simple prefix strip** (`resource_type` minus `<provider>_`) — this holds for the overwhelming majority of resources but isn't guaranteed for every one; a mismatch raises a clear `FileNotFoundError` rather than failing silently or guessing.
- **AWS/GCP generation quality is grounding-verified, not output-verified.** The schema+docs fetching mechanism is proven live against real AWS and GCP data (see Status below). The generation prompt's structural rules are provider-agnostic *except* one: it explicitly targets Azure Verified Modules (AVM) conventions, which have no AWS/GCP equivalent wired in yet.
- **Deeply nested "NestedType" attributes aren't recursively filtered.** Newer provider schemas sometimes represent a nested structure as a single attribute with an inline object type (e.g. `access_policy` on `azurerm_key_vault`) rather than a classic `block_types` entry. `input_schema()`'s computed-only stripping only recurses into `block_types` — if a NestedType attribute's *inner* shape ever contains its own computed-only sub-field, it wouldn't be caught. Not hit in testing so far, but a known structural gap, not a verified-safe case.
- **Alerts are generated (`alerts.tf`), but only as a generic pass-through.** Every module gets a single `alert_rules` variable (`map(object({...})`, default `null`) driving one alert resource via `for_each = var.alert_rules != null ? var.alert_rules : {}` — the null-guard matters: `for_each` errors on a bare `null`, so `null`/omitted alone would break, not just "create nothing." The alert resource type is resolved per cloud, not hardcoded — `azurerm_monitor_metric_alert` for Azure, `aws_cloudwatch_metric_alarm` for AWS, `google_monitoring_alert_policy` for GCP — and its own real schema is fetched and passed to the model the same way as the primary resource's, since the three clouds' alerting APIs have genuinely different shapes (Azure nests everything in a `criteria` block; AWS is mostly flat top-level fields; GCP uses a filter string), not just different names for the same fields. What's *not* included is a curated, per-resource menu of "recommended" metrics with correct names pre-filled in — that would need a new grounding source (a supported-metrics reference per resource type, a different one entirely per cloud) that hasn't been built. You supply real monitoring criteria yourself.
- **Windows-specific handling included, not a restriction**: pip-installed console scripts that ship as `.cmd`/`.bat` wrappers (checkov does, on Windows) are routed through `cmd /c` automatically, since Python's `subprocess` can't launch those directly.

---

## Module design: flat + per-block variables, not one single variable

This comes up often enough to state plainly, once, as the documented answer:

**The generator never produces a module with one mega-object variable
holding everything.** Top-level scalars (`name`, `location`,
`resource_group_name`, ...) are individual variables; every nested block in
the schema (`network_rules`, `access_policy`, `identity`, ...) becomes its
own `optional()`-typed object variable, defaulting to `null`/`[]` when
omittable. Two reasons:

1. **Scoped validation.** Each variable can carry its own `validation` block with a specific error message. A single object variable can only be validated as one lump, so a bad value anywhere produces a generic, unhelpful failure instead of pointing at the actual field.
2. **Discoverability.** Separate variables show up individually in `terraform plan`, IDE autocomplete, and generated docs. A single object variable hides its entire shape behind one name.

**This costs nothing for `for_each`.** Whether a *module* takes many small
variables or one big object is completely independent of whether the
*caller* wants to create many instances of it — `for_each` operates on
whatever variable the caller's own root module defines, then maps each
entry's fields into the module call:

```hcl
variable "storage_accounts" {
  type = map(object({
    location            = string
    resource_group_name = string
    account_tier         = string
    replication_type     = string
  }))
}

module "storage" {
  source   = "./terraform-azurerm-storage-account"
  for_each = var.storage_accounts

  name                      = "st${each.key}"
  location                  = each.value.location
  resource_group_name       = each.value.resource_group_name
  account_tier              = each.value.account_tier
  account_replication_type  = each.value.replication_type
}
```

One variable (a map) at the call site, one `module` block in the source
code, as many resources as the map has entries — `module.storage["logs"]`,
`module.storage["assets"]`, etc. You never write the module block twice, and
the module's own internals stay simple: one resource, one clean test suite,
no doubled logic to cover both a singular and a looped code path. This is
also why every generated module documents this exact pattern in its own
README under "Creating multiple `<resources>`."

---

## Status — what's actually verified here, and what isn't

Built and tested incrementally; kept honest rather than aspirational.

| Module | Verified | How |
|---|---|---|
| `core/auth.py` (BYOK key resolution) | **Yes, any provider** | `tests/test_auth.py`, 8/8 passing — including that known providers only read their own env var (`ANTHROPIC_API_KEY`/`GOOGLE_API_KEY`/`OPENAI_API_KEY`, never cross-reading), and that an unrecognized provider name still works correctly when a key is passed explicitly |
| `core/docs.py` (pinned docs fetch + settable-argument parsing) | **Yes, multi-cloud** | Live-tested against the real GitHub API for **azurerm, AWS, and GCP** — all three fetch correctly. `documented_argument_names()` covered by `tests/test_docs.py`, 4/4 passing, handling both azurerm's and AWS's heading/qualifier styles |
| `core/schema.py` (schema introspection + input filtering) | **Yes, multi-cloud** | Live-tested against real `terraform` v1.16.1 for **azurerm and AWS** (GCP hit an unrelated, environment-specific binary-exec failure on this particular machine — not a code issue, since schema introspection is provider-agnostic by construction). `input_schema()` + `cross_reference_with_docs()` covered by `tests/test_schema.py`, 12/12 passing |
| `core/generate.py` (the model call) | **Partially** | The actual `litellm.completion()` call hasn't been run against any live provider from this environment — needs a real key, by design, since this tool never holds one. What *is* verified live: litellm installs and imports cleanly with no other provider SDK needed, and its `completion()` signature has exactly the `model`/`messages`/`api_key`/`max_tokens` parameters this code calls it with. The generation *rules* (schema-grounding, alerts.tf, for_each guidance) were separately exercised by hand-generating a real `azurerm_key_vault` module against this exact system prompt, which then passed the full pipeline below — that used Claude directly, not litellm, so it doesn't verify the litellm call path itself |
| `core/validate.py` (fmt/init/validate/test/checkov) | **Yes** | Live end-to-end against the hand-generated `azurerm_key_vault` module: `fmt`/`init`/`validate`/`test` (3/3 scenarios via `mock_provider`, zero cloud credentials) all pass; `checkov` (3.3.16) ran for real and found genuine findings |
| `mcp_server.py` | **No** | Needs the `mcp` package and a real MCP host to connect to |

Two worked examples live in `examples/`: `terraform-azurerm-storage-account/`
and `terraform-azurerm-key-vault/` — the latter is the one that actually
passed the full live validation pipeline above, not just a description of
what it should do.

## License

MIT — see `LICENSE`. Fill in the copyright holder before publishing.
