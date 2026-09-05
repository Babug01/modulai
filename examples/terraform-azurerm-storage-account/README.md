# terraform-azurerm-storage-account

Manages a single Azure Storage Account. Generated from `azurerm_storage_account`'s
real provider schema and documentation, pinned to **azurerm v5.4.0**.

## Usage

```hcl
module "storage" {
  source = "./terraform-azurerm-storage-account"

  name                      = "stexample01"
  resource_group_name       = azurerm_resource_group.example.name
  location                  = azurerm_resource_group.example.location
  account_tier              = "Standard"
  account_replication_type  = "GRS"

  tags = {
    environment = "staging"
  }
}
```

## Creating multiple accounts

This module manages **one** storage account. Need three? Don't copy-paste
the `module` block three times with different values — that's what
`for_each` replaces:

```hcl
# The boring way — repeat the block per account, only values differ:
module "storage_logs" {
  source                    = "./terraform-azurerm-storage-account"
  name                      = "stlogs"
  resource_group_name       = azurerm_resource_group.example.name
  location                  = azurerm_resource_group.example.location
  account_tier              = "Standard"
  account_replication_type  = "LRS"
}
module "storage_assets" {
  source                    = "./terraform-azurerm-storage-account"
  name                       = "stassets"
  # ...same fields again...
}
```

```hcl
# The for_each way — one block, one variable (a map), as many accounts as it has entries:
variable "storage_accounts" {
  type    = map(object({ tier = string, replication = string }))
  default = {
    logs   = { tier = "Standard", replication = "LRS" }
    assets = { tier = "Standard", replication = "GRS" }
  }
}

module "storage" {
  source   = "./terraform-azurerm-storage-account"
  for_each = var.storage_accounts

  name                      = "st${each.key}"
  resource_group_name       = azurerm_resource_group.example.name
  location                  = azurerm_resource_group.example.location
  account_tier              = each.value.tier
  account_replication_type  = each.value.replication
}
```

This creates `module.storage["logs"]` and `module.storage["assets"]` from
one block. `each.key` is the map key; `each.value` is that entry's object.
Add a third account by adding a third entry to `var.storage_accounts` — no
new `module` block needed. The module's own `variables.tf` doesn't change
either way; `for_each` just calls it repeatedly, once per map entry.

## Alerts

`null` (the default) or omitting `alert_rules` entirely creates no alerts.
This is a generic pass-through — you supply real Azure Monitor criteria:

```hcl
module "storage" {
  source = "./terraform-azurerm-storage-account"
  # ...required fields...

  alert_rules = {
    availability = {
      metric_namespace = "Microsoft.Storage/storageAccounts"
      metric_name      = "Availability"
      aggregation      = "Average"
      operator         = "LessThan"
      threshold        = 99
      severity         = 1
    }
  }
}
```

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