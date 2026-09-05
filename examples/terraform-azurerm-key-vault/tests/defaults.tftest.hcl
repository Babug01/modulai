#------------------------------------------------------------------------------------------------------------------------------------------
/*
  Test Suite for azurerm_key_vault Module

  Uses mock_provider — no real Azure credentials or resources involved.
  Requires Terraform >= 1.7.
*/
#------------------------------------------------------------------------------------------------------------------------------------------
mock_provider "azurerm" {}

variables {
  name                       = "kvtfgentest001"
  location                   = "westeurope"
  resource_group_name        = "rg-tfgen-test"
  tenant_id                  = "00000000-0000-0000-0000-000000000000"
  sku_name                   = "standard"
  rbac_authorization_enabled = true
}

run "minimal_creation_plan" {
  command = plan

  assert {
    condition     = azurerm_key_vault.this.sku_name == "standard"
    error_message = "sku_name should be standard"
  }

  assert {
    condition     = azurerm_key_vault.this.rbac_authorization_enabled == true
    error_message = "rbac_authorization_enabled should be true"
  }

  assert {
    condition     = azurerm_key_vault.this.purge_protection_enabled == false
    error_message = "purge_protection_enabled should default to false"
  }

  assert {
    condition     = azurerm_key_vault.this.soft_delete_retention_days == 90
    error_message = "soft_delete_retention_days should default to 90"
  }

  assert {
    condition     = length(azurerm_monitor_metric_alert.this) == 0
    error_message = "no alerts should be created when alert_rules is left at its null default"
  }
}

run "invalid_sku_name_rejected" {
  command = plan

  variables {
    sku_name = "basic"
  }

  expect_failures = [
    var.sku_name,
  ]
}

run "access_policy_plan" {
  command = plan

  variables {
    rbac_authorization_enabled = false
    access_policy = [
      {
        tenant_id       = "00000000-0000-0000-0000-000000000000"
        object_id       = "11111111-1111-1111-1111-111111111111"
        key_permissions = ["Get", "List"]
      }
    ]
  }

  assert {
    condition     = length(azurerm_key_vault.this.access_policy) == 1
    error_message = "access_policy should have exactly one entry"
  }

  assert {
    condition     = contains(azurerm_key_vault.this.access_policy[0].key_permissions, "Get")
    error_message = "access_policy key_permissions should contain Get"
  }
}

run "explicit_null_alert_rules_creates_nothing" {
  command = plan

  variables {
    alert_rules = null
  }

  assert {
    condition     = length(azurerm_monitor_metric_alert.this) == 0
    error_message = "explicitly passing null for alert_rules must still create zero alerts, not error"
  }
}

run "alert_rules_plan" {
  command = plan

  variables {
    alert_rules = {
      availability = {
        metric_namespace = "Microsoft.KeyVault/vaults"
        metric_name      = "Availability"
        aggregation      = "Average"
        operator         = "LessThan"
        threshold        = 99
        severity         = 1
      }
    }
  }

  assert {
    condition     = length(azurerm_monitor_metric_alert.this) == 1
    error_message = "alert_rules with one entry should create exactly one alert"
  }

  assert {
    condition     = azurerm_monitor_metric_alert.this["availability"].criteria[0].metric_name == "Availability"
    error_message = "the alert's metric_name should match what was passed in"
  }

  assert {
    condition     = azurerm_monitor_metric_alert.this["availability"].severity == 1
    error_message = "the alert's severity should match what was passed in"
  }
}
