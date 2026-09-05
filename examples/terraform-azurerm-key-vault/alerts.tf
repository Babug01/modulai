#------------------------------------------------------------------------------------------------------------------------------------------
/*
  Alerts

  Generic pass-through, not a curated per-resource menu — this module doesn't
  know which Key Vault metrics are worth alerting on, only how to wire up
  whatever criteria you supply. See README.md "Alerts" for real metric names.
*/
#------------------------------------------------------------------------------------------------------------------------------------------
resource "azurerm_monitor_metric_alert" "this" {
  for_each = var.alert_rules != null ? var.alert_rules : {}

  name                = each.key
  resource_group_name = var.resource_group_name
  scopes              = [azurerm_key_vault.this.id]
  description         = each.value.description
  severity            = each.value.severity
  frequency           = each.value.frequency
  window_size         = each.value.window_size

  criteria {
    metric_namespace = each.value.metric_namespace
    metric_name      = each.value.metric_name
    aggregation      = each.value.aggregation
    operator         = each.value.operator
    threshold        = each.value.threshold
  }

  dynamic "action" {
    for_each = each.value.action_group_ids
    content {
      action_group_id = action.value
    }
  }
}
