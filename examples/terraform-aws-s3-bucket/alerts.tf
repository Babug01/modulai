#------------------------------------------------------------------------------------------------------------------------------------------
/*
  Alerts

  Generic pass-through, not a curated per-resource menu — this module doesn't
  know which S3 metrics are worth alerting on, only how to wire up whatever
  criteria you supply. Unlike Azure's metric alert, aws_cloudwatch_metric_alarm
  has no dedicated "target resource" field (no equivalent of `scopes`) — you
  point it at this bucket yourself, typically via `dimensions = { BucketName =
  module.bucket.id }` in the alert_rules entry.
*/
#------------------------------------------------------------------------------------------------------------------------------------------
resource "aws_cloudwatch_metric_alarm" "this" {
  for_each = var.alert_rules != null ? var.alert_rules : {}

  alarm_name          = each.key
  alarm_description   = each.value.alarm_description
  actions_enabled     = each.value.actions_enabled
  comparison_operator = each.value.comparison_operator
  evaluation_periods  = each.value.evaluation_periods
  metric_name         = each.value.metric_name
  namespace           = each.value.namespace
  period              = each.value.period
  statistic           = each.value.statistic
  extended_statistic  = each.value.extended_statistic
  threshold           = each.value.threshold
  threshold_metric_id = each.value.threshold_metric_id
  unit                = each.value.unit
  dimensions          = each.value.dimensions

  datapoints_to_alarm                   = each.value.datapoints_to_alarm
  evaluation_interval                   = each.value.evaluation_interval
  evaluate_low_sample_count_percentiles = each.value.evaluate_low_sample_count_percentiles
  treat_missing_data                    = each.value.treat_missing_data
  region                                = each.value.region
  tags                                  = each.value.tags

  alarm_actions             = each.value.alarm_actions
  ok_actions                = each.value.ok_actions
  insufficient_data_actions = each.value.insufficient_data_actions

  dynamic "metric_query" {
    for_each = each.value.metric_query
    content {
      id          = metric_query.value.id
      account_id  = metric_query.value.account_id
      expression  = metric_query.value.expression
      label       = metric_query.value.label
      period      = metric_query.value.period
      return_data = metric_query.value.return_data

      dynamic "metric" {
        for_each = metric_query.value.metric != null ? [metric_query.value.metric] : []
        content {
          metric_name = metric.value.metric_name
          namespace   = metric.value.namespace
          period      = metric.value.period
          stat        = metric.value.stat
          unit        = metric.value.unit
          dimensions  = metric.value.dimensions
        }
      }
    }
  }

  dynamic "evaluation_criteria" {
    for_each = each.value.evaluation_criteria != null ? [each.value.evaluation_criteria] : []
    content {
      promql_criteria {
        query           = evaluation_criteria.value.promql_criteria.query
        pending_period  = evaluation_criteria.value.promql_criteria.pending_period
        recovery_period = evaluation_criteria.value.promql_criteria.recovery_period
      }
    }
  }
}