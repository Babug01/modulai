# terraform-azurerm-key-vault

Manages a single Azure Key Vault. Generated from `azurerm_key_vault`'s real
provider documentation and schema, pinned to **azurerm v5.4.0**.

## Usage

```hcl
data "azurerm_client_config" "current" {}

module "key_vault" {
  source = "./terraform-azurerm-key-vault"

  name                        = "examplekeyvault"
  location                    = azurerm_resource_group.example.location
  resource_group_name         = azurerm_resource_group.example.name
  tenant_id                   = data.azurerm_client_config.current.tenant_id
  sku_name                    = "standard"
  rbac_authorization_enabled  = true

  purge_protection_enabled    = false
  soft_delete_retention_days  = 7

  tags = {
    environment = "staging"
  }
}
```

Using access policies instead of RBAC:

```hcl
module "key_vault" {
  source = "./terraform-azurerm-key-vault"

  name                        = "examplekeyvault"
  location                    = azurerm_resource_group.example.location
  resource_group_name         = azurerm_resource_group.example.name
  tenant_id                   = data.azurerm_client_config.current.tenant_id
  sku_name                    = "standard"
  rbac_authorization_enabled  = false

  access_policy = [
    {
      tenant_id       = data.azurerm_client_config.current.tenant_id
      object_id       = data.azurerm_client_config.current.object_id
      key_permissions = ["Get", "List"]
    }
  ]
}
```

## Creating multiple key vaults

This module manages **one** Key Vault. Need three? Don't copy-paste the
`module` block three times with different values — that's what `for_each`
replaces:

```hcl
# The boring way — repeat the block per vault, only values differ:
module "key_vault_dev" {
  source                     = "./terraform-azurerm-key-vault"
  name                       = "kvdev"
  location                   = azurerm_resource_group.example.location
  resource_group_name        = azurerm_resource_group.example.name
  tenant_id                  = data.azurerm_client_config.current.tenant_id
  sku_name                   = "standard"
  rbac_authorization_enabled = true
}
module "key_vault_prod" {
  source                     = "./terraform-azurerm-key-vault"
  name                       = "kvprod"
  # ...same fields again...
}
```

```hcl
# The for_each way — one block, one variable (a map), as many vaults as it has entries:
variable "key_vaults" {
  type    = map(object({ sku_name = string }))
  default = {
    dev  = { sku_name = "standard" }
    prod = { sku_name = "premium" }
  }
}

module "key_vault" {
  source   = "./terraform-azurerm-key-vault"
  for_each = var.key_vaults

  name                       = "kv${each.key}"
  location                   = azurerm_resource_group.example.location
  resource_group_name        = azurerm_resource_group.example.name
  tenant_id                  = data.azurerm_client_config.current.tenant_id
  sku_name                   = each.value.sku_name
  rbac_authorization_enabled = true
}
```

This creates `module.key_vault["dev"]` and `module.key_vault["prod"]` from
one block. `each.key` is the map key (`"dev"`, `"prod"`); `each.value` is
that entry's object. Add a third vault by adding a third entry to
`var.key_vaults` — no new `module` block needed. The module's own
`variables.tf` doesn't change either way; `for_each` just calls it
repeatedly, once per map entry.

## Alerts

`null` (the default) or omitting `alert_rules` entirely creates no alerts —
this module never assumes you want monitoring. This is a **generic
pass-through**, not a curated list of "recommended" Key Vault alerts: the
module doesn't know which metrics matter for your setup, only how to wire up
whatever criteria you supply. Find real metric names/namespaces in
[Microsoft's supported-metrics reference](https://learn.microsoft.com/en-us/azure/azure-monitor/reference/supported-metrics/microsoft-keyvault-vaults-metrics).

```hcl
module "key_vault" {
  source = "./terraform-azurerm-key-vault"
  # ...required fields...

  alert_rules = {
    availability = {
      metric_namespace = "Microsoft.KeyVault/vaults"
      metric_name       = "Availability"
      aggregation        = "Average"
      operator            = "LessThan"
      threshold           = 99
      severity            = 1
      action_group_ids    = [azurerm_monitor_action_group.example.id]
    }
  }
}
```

Each map entry becomes one `azurerm_monitor_metric_alert`, named after its
key (`"availability"` above). Add as many entries as you need; remove the
variable (or set it to `null`) to disable alerting entirely.

## Requirements

| Name | Version |
|---|---|
| terraform | >= 1.7.0 |
| azurerm | >= 5.4.0, < 6.0.0 |

## Testing

```bash
terraform init
terraform test
```

Runs entirely offline via `mock_provider` — no Azure subscription required.
Covers: minimal creation, an invalid `sku_name` rejection, and an access-policy
scenario.
