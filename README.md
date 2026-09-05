# modulai

Give it a resource name — `azurerm_storage_account` — and get back a complete,
parameterized Terraform module: grounded in the provider's real schema, not
its prose docs, with generated tests and a security scan already run.

```bash
export ANTHROPIC_API_KEY=sk-ant-...   # your own key, billed to your own account
modulai generate azurerm_storage_account
```

No hosting, no server, no account with us — it's BYOK: every generation call
uses your own Anthropic API key, run locally. See
`src/modulai/core/auth.py`.

## How it works

1. Resolve the resource type (exact type, or a plain description).
2. Pin the exact provider version and run `terraform init` + `terraform providers schema -json` — the real ground truth for arguments, types, required/optional, nested blocks.
3. Fetch the provider's descriptive docs from GitHub, pinned to the matching release tag — used for descriptions only, never structure.
4. Generate the module: one resource per module, `for_each` left to the caller, flat variables for scalars + one object variable per nested block, AVM-aligned.
5. Validate before handing it back: `fmt` → `init` → `validate` → `test` (mock provider, zero cloud credentials) → `checkov`.

## Status — what's actually verified here, and what isn't

Built incrementally, and this section is kept honest rather than aspirational:

| Module | Verified | How |
|---|---|---|
| `core/auth.py` (BYOK key resolution) | **Yes** | `tests/test_auth.py`, 3/3 passing |
| `core/docs.py` (pinned provider docs fetch + settable-argument parsing) | **Yes** | Live-tested against the real GitHub API for **azurerm, AWS, and GCP** — all three fetch correctly. `documented_argument_names()` covered by `tests/test_docs.py`, 4/4 passing, handling both azurerm's plural heading/bare-qualifier style and AWS's singular heading/compound-qualifier style |
| `core/schema.py` (schema introspection + input filtering) | **Yes, multi-cloud** | Live-tested against real `terraform` v1.16.1 against **azurerm and AWS** (GCP's provider binary hit an unrelated, environment-specific exec failure on this machine — not a code issue, schema fetching is provider-agnostic by construction). `input_schema()` + `cross_reference_with_docs()` covered by `tests/test_schema.py`, 12/12 passing |
| `core/generate.py` (the model call) | **Partially** | The SDK call itself is untested by design (needs your real API key, never run here) — but the *rules* it enforces were exercised by hand-generating a real `azurerm_key_vault` module against this exact system prompt, which then passed the full pipeline below. The prompt's AVM-alignment rule is still Azure-only — no AWS/GCP module-convention equivalent yet |
| `core/validate.py` (fmt/init/validate/test/checkov) | **Yes** | Live end-to-end against the hand-generated `azurerm_key_vault` module: `fmt`, `init`, `validate`, and `test` (3/3 scenarios, via `mock_provider`, zero cloud credentials) all pass; `checkov` (3.3.16) ran for real and found genuine findings — see below |
| `mcp_server.py` | **No** | Needs the `mcp` package and a real MCP host to connect to |

**Multi-cloud reality check**: asked directly whether this works for AWS/GCP/other clouds, not just Azure — the honest answer, backed by live testing rather than assumption: the *grounding mechanism* (schema + docs fetching) generalizes cleanly, proven live against AWS. That same AWS check also caught a real bug — `tags_all` has the identical `optional: true, computed: true` shape `id` did on Azure, but it's a provider-specific tag-merge output, not a real input. Fixed generally (cross-referencing every attribute against what the provider's own docs actually document as settable, not a hardcoded name list) rather than patched as a one-off. What's *not* yet generalized: the generation prompt's structural conventions (AVM is Azure-specific) and alerts/monitoring (deliberately out of scope for now — see the project discussion for why).

Two real bugs were found and fixed by that end-to-end run, not by inspection:

1. **`fmt` was gating the whole pipeline on cosmetic formatting.** `terraform fmt -check` failed over a spacing misalignment in hand-written HCL and stopped `init`/`validate`/`test` from running at all. Changed to apply formatting (`terraform fmt -recursive`) instead of gating on it — a spacing issue is trivially self-healing and shouldn't block generation the way a real validation failure should.
2. **A missing binary crashed the whole report.** Passing an unavailable `checkov_bin` raised an uncaught `FileNotFoundError`, discarding the already-passed fmt/init/validate/test results. Now caught and reported as a normal failed step. This also surfaced a genuine Windows-specific gap: pip-installed console scripts are sometimes `.cmd` wrappers rather than `.exe`, which `subprocess.run` can't launch directly via `CreateProcess` — fixed by routing `.cmd`/`.bat` targets through `cmd /c` (no-op on non-Windows).

**Checkov's real findings** on the generated `azurerm_key_vault` module: 2 passed (public network access posture, soft delete enabled), 3 failed — purge protection off, key vault not "recoverable," no private endpoint configured. All genuine, all things a user would want to know before deploying — exactly the value this tool is meant to add over generating HCL that merely looks plausible.

Both worked examples live in `examples/`: `terraform-azurerm-storage-account/`
(the earlier, hand-built one) and `terraform-azurerm-key-vault/` (the one that
actually passed the full live pipeline above).

**Why `input_schema()` exists**: the raw schema interleaves true inputs with
computed-only exports, distinguished only by a `computed: true` flag that's
easy to miss — `generate.py`'s prompt alone asking the model to "respect
required/optional" isn't a strong enough guarantee. Filtering it out in code
before the schema ever reaches the model closes that gap structurally instead
of hoping the prompt is followed. Also drops the top-level `id` attribute
specifically — found live on `azurerm_key_vault` marked `optional: true,
computed: true`, which would otherwise pass the optional/required check
despite never being a real settable input.

## Install

```bash
pip install -e ".[dev,mcp]"
```

## Use as an MCP server

Register with any MCP-speaking host (Claude Code, Cursor, etc.):

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

## License

MIT — see `LICENSE`. Fill in the copyright holder before publishing.
