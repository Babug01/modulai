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
    condition     = azurerm_storage_account.this.account_replication_type == "LRS"
    error_message = "account_replication_type should be LRS"
  }

  assert {
    condition     = azurerm_storage_account.this.min_tls_version == "TLS1_2"
    error_message = "min_tls_version should default to TLS1_2"
  }

  assert {
    condition     = azurerm_storage_account.this.https_traffic_only_enabled == true
    error_message = "https_traffic_only_enabled should default to true"
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

run "network_rules_plan" {
  command = plan

  variables {
    network_rules = {
      default_action = "Deny"
      ip_rules       = ["203.0.113.4"]
    }
  }

  assert {
    condition     = azurerm_storage_account.this.network_rules[0].default_action == "Deny"
    error_message = "network_rules.default_action should be Deny when explicitly set"
  }

  assert {
    condition     = contains(azurerm_storage_account.this.network_rules[0].ip_rules, "203.0.113.4")
    error_message = "network_rules.ip_rules should contain the configured CIDR"
  }
}

run "identity_and_blob_versioning_plan" {
  command = plan

  variables {
    identity = {
      type = "SystemAssigned"
    }
    blob_properties = {
      versioning_enabled = true
      delete_retention_policy = {
        days = 14
      }
    }
  }

  assert {
    condition     = azurerm_storage_account.this.identity[0].type == "SystemAssigned"
    error_message = "identity.type should be SystemAssigned"
  }

  assert {
    condition     = azurerm_storage_account.this.blob_properties[0].versioning_enabled == true
    error_message = "blob_properties.versioning_enabled should be true"
  }

  assert {
    condition     = azurerm_storage_account.this.blob_properties[0].delete_retention_policy[0].days == 14
    error_message = "blob_properties.delete_retention_policy.days should be 14"
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
