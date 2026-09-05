#------------------------------------------------------------------------------------------------------------------------------------------
/*
  Test Suite for azurerm_storage_account Module

  Uses mock_provider — no real Azure credentials or resources involved.
  Requires Terraform >= 1.7.
*/
#------------------------------------------------------------------------------------------------------------------------------------------
mock_provider "azurerm" {}

variables {
  name                     = "sttfgentest001"
  resource_group_name      = "rg-tfgen-test"
  location                 = "westeurope"
  account_tier             = "Standard"
  account_replication_type = "LRS"
}

run "minimal_creation_plan" {
  command = plan

  assert {
    condition     = azurerm_storage_account.this.account_tier == "Standard"
    error_message = "account_tier should be Standard"
  }

  assert {
    condition     = length(azurerm_monitor_metric_alert.this) == 0
    error_message = "no alerts should be created when alert_rules is left at its null default"
  }
}

run "invalid_account_tier_rejected" {
  command = plan

  variables {
    account_tier = "Basic"
  }

  expect_failures = [
    var.account_tier,
  ]
}

run "network_rules_and_alert_plan" {
  command = plan

  variables {
    network_rules = {
      default_action = "Deny"
      ip_rules       = ["203.0.113.4"]
    }
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

  assert {
    condition     = azurerm_storage_account.this.network_rules[0].default_action == "Deny"
    error_message = "network_rules.default_action should be Deny when explicitly set"
  }

  assert {
    condition     = length(azurerm_monitor_metric_alert.this) == 1
    error_message = "alert_rules with one entry should create exactly one alert"
  }
}