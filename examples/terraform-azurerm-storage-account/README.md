# terraform-azurerm-storage-account

Manages a single Azure Storage Account. Generated from `azurerm_storage_account`'s
real provider documentation, pinned to **azurerm v5.4.0** (latest release at
generation time — see `main.tf`'s version constraint for the exact floor).

Grounded in the provider's own docs (`hashicorp/terraform-provider-azurerm`,
tag `v5.4.0`), not paraphrased from memory. Terraform CLI and Checkov were not
available in the environment this was generated in, so `fmt`/`init`/`validate`/
`test`/`checkov` have **not actually been executed** against this module yet —
run them before relying on it. `tests/defaults.tftest.hcl` is written against
Terraform's native mock-provider testing (1.7+), so once run it needs no real
Azure credentials.

## Usage

```hcl
module "storage" {
  source = "./terraform-azurerm-storage-account"

  name                      = "sttfgenexample01"
  resource_group_name       = azurerm_resource_group.example.name
  location                  = azurerm_resource_group.example.location
  account_tier              = "Standard"
  account_replication_type  = "GRS"

  network_rules = {
    default_action = "Deny"
    ip_rules       = ["203.0.113.4"]
  }

  blob_properties = {
    versioning_enabled = true
    delete_retention_policy = {
      days = 14
    }
  }

  tags = {
    environment = "staging"
  }
}
```

## Creating multiple accounts

This module manages **one** storage account. Multiplicity is the caller's
decision — wrap the module in `for_each`, not the other way around:

```hcl
locals {
  storage_accounts = {
    logs   = { replication = "LRS", tier = "Standard" }
    assets = { replication = "GRS", tier = "Standard" }
  }
}

module "storage" {
  source   = "./terraform-azurerm-storage-account"
  for_each = local.storage_accounts

  name                      = "sttfgen${each.key}"
  resource_group_name       = azurerm_resource_group.example.name
  location                  = azurerm_resource_group.example.location
  account_tier              = each.value.tier
  account_replication_type  = each.value.replication
}
```

## Variable shape

Top-level scalars (`name`, `resource_group_name`, `location`, `account_tier`, ...)
are individual variables. Every nested block in the provider schema
(`network_rules`, `blob_properties`, `identity`, `customer_managed_key`,
`share_properties`, `azure_files_authentication`, `routing`,
`immutability_policy`, `sas_policy`, `custom_domain`) is its own optional
object-typed variable, defaulting to `null` (omitted). See `variables.tf` for
full per-field descriptions and validation rules.

## Requirements

| Name | Version |
|---|---|
| terraform | >= 1.7.0 |
| azurerm | >= 5.4.0, < 6.0.0 |

The azurerm floor is the exact version this module was generated and grounded
against — not a loose major-version floor. An earlier 5.x patch may not expose
every argument used here.

## Testing

```bash
terraform init
terraform test
```

Runs entirely offline via `mock_provider` — no Azure subscription or credentials
required. Covers: minimal creation, an invalid `account_tier` rejection, network
rules, and identity + blob versioning.

## Security scanning

```bash
checkov -d . --framework terraform
```

Not run in this environment (Checkov unavailable) — run before merging.
