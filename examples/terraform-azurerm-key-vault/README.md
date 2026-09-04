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

This module manages **one** Key Vault. Multiplicity is the caller's decision:

```hcl
module "key_vault" {
  source   = "./terraform-azurerm-key-vault"
  for_each = local.key_vaults

  name                       = "kv${each.key}"
  location                   = azurerm_resource_group.example.location
  resource_group_name        = azurerm_resource_group.example.name
  tenant_id                  = data.azurerm_client_config.current.tenant_id
  sku_name                   = "standard"
  rbac_authorization_enabled = true
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
Covers: minimal creation, an invalid `sku_name` rejection, and an access-policy
scenario.
