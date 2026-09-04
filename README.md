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
| `core/docs.py` (pinned provider docs fetch) | **Yes** | Live-tested against the real GitHub API — fetched v5.4.0 and `azurerm_storage_account`'s actual doc |
| `core/schema.py` (schema introspection) | **No** | Needs a local `terraform` binary; not available in the environment this was built in |
| `core/generate.py` (the model call) | **No** | Needs the `anthropic` package and a real API key — untested by design, since this tool never holds your key for you |
| `core/validate.py` (fmt/init/validate/test/checkov) | **No** | Needs `terraform` and `checkov` binaries, neither available here |
| `mcp_server.py` | **No** | Needs the `mcp` package and a real MCP host to connect to |

A hand-built module following this exact design (`azurerm_storage_account`,
pinned to v5.4.0) exists as a worked example — see the separate
`terraform-azurerm-storage-account/` output for what this pipeline is meant
to produce, itself not yet run through a real `terraform validate`/`test`
either.

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
