# Terraform Module Generator (Azure, AWS, GCP)

Give it a resource type — `azurerm_storage_account`, `aws_s3_bucket`,
`google_storage_bucket` — and get back a complete, parameterized Terraform
module: grounded in the provider's real schema and real documentation, not
a model's memory of them, with generated tests and a security scan already
run against the output before you ever see it.

No hosting, no account with us, no server to operate. It's BYOK — every
generation call uses your own API key, run entirely on your own machine.
Model calls go through [litellm](https://github.com/BerriAI/litellm), so
whichever AI provider you already have a key for works — **Anthropic**,
**Google Gemini** (free tier via Google AI Studio, no billing account
needed), **OpenAI**, Groq, Mistral, Bedrock, local Ollama, and more.

## Requirements

| Tool | Why |
|---|---|
| **Terraform >= 1.7** | Schema introspection and the generated tests' `mock_provider` both need this |
| **Python >= 3.10** | Runtime for the CLI/MCP server |
| **An API key for one AI provider** | Anthropic and OpenAI are billed; Google's Gemini free tier needs no card (aistudio.google.com). Never stored or transmitted anywhere except directly to that provider |
| **Checkov** *(optional)* | Security-scan step. Skippable with `--skip-validate` |

## Install

```bash
pip install -e ".[dev,mcp]"
```

Installs two console scripts: `modulai` (CLI) and `modulai-mcp` (MCP
server). `[mcp]` is only needed for the MCP server.

**If `modulai` fails to launch** (`Access is denied` trying to start
`modulai.exe`) — some Windows AV/EDR software blocks freshly pip-created
`.exe` launcher stubs. Use `python -m modulai` instead:

```bash
python -m modulai generate azurerm_storage_account
```

## How to run it

### CLI

```bash
export ANTHROPIC_API_KEY=sk-ant-...
modulai generate azurerm_storage_account
```

`hashicorp/azurerm` is the default provider. For AWS or GCP:

```bash
modulai generate aws_s3_bucket --provider-source hashicorp/aws
modulai generate google_storage_bucket --provider-source hashicorp/google
```

Using Gemini's free tier instead:

```bash
export GOOGLE_API_KEY=...
modulai generate azurerm_storage_account --model-provider google
```

Any other litellm provider needs `--model` and `--api-key` explicitly:

```bash
modulai generate azurerm_storage_account \
  --model-provider groq --model groq/llama-3.1-70b-versatile --api-key gsk_...
```

What happens, in order: pin the exact provider version → fetch its real
schema (`terraform providers schema -json`) → fetch its real docs from
GitHub, pinned to the same version → generate the module → run
`fmt`/`init`/`validate`/`test`/`checkov` against the result → report
pass/fail per step. Output lands in `./terraform-<provider>-<resource>/`
unless `--out` says otherwise.

### MCP server

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

Exposes two tools to any MCP-speaking host (Claude Code, Cursor, etc.):

- **`generate_terraform_module`** — same generation flow as the CLI
- **`validate_terraform_module`** — run the fmt/init/validate/test/checkov pipeline against a module you already have

## Inputs

| Input | Required | Default | Notes |
|---|---|---|---|
| `resource_type` | **Yes** | — | e.g. `azurerm_storage_account` |
| `--provider-version` | No | latest release | Exact version only (e.g. `5.4.0`), never a range |
| `--provider-source` | No | `hashicorp/azurerm` | Override for AWS (`hashicorp/aws`) or GCP (`hashicorp/google`) |
| `--out` | No | `./terraform-<provider>-<resource>` | Output directory |
| `--model-provider` | No | `anthropic` | Any litellm-supported provider name |
| `--model` | No | built-in default for anthropic/google/openai only | Required for any other provider |
| `--api-key` | No | that provider's conventional env var, if known | Overrides the env var for one run |
| `--skip-validate` | No | off | Skips the fmt/init/validate/test/checkov pass |

The generated module's `required_providers` constraint floors at the
version actually generated against, with a ceiling at the next major
version.

## Restrictions and known limitations

- Docs only resolve automatically for providers published under the `hashicorp` GitHub org — third-party providers (Cloudflare, Datadog, etc.) aren't supported yet.
- One resource per module, by design — multiplicity is the caller's job via `for_each`, not the module's.
- Requires outbound internet access (GitHub, `registry.terraform.io`, and whichever AI provider you use). No offline mode.
- Arguments documented as **Deprecated** in the provider's own docs are excluded from generated variables, even if the schema itself doesn't flag them.
- AVM (Azure Verified Modules) conventions are applied for Azure; no equivalent convention set is wired in for AWS/GCP yet.
- Alerts (`alerts.tf`) are a generic pass-through — one `alert_rules` variable driving the right alert resource per cloud, with real schema grounding, but no curated per-resource menu of recommended metrics.

## License

MIT — see `LICENSE`. Fill in the copyright holder before publishing.
