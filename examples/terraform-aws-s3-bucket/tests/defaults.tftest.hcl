#------------------------------------------------------------------------------------------------------------------------------------------
/*
  Test Suite for aws_s3_bucket Module

  Uses mock_provider — no real AWS credentials or resources involved.
  Requires Terraform >= 1.9 (variables.tf's cross-variable validation).
*/
#------------------------------------------------------------------------------------------------------------------------------------------
mock_provider "aws" {}

variables {
  bucket = "modulai-tfgen-test-bucket"
}

run "minimal_creation_plan" {
  command = plan

  assert {
    condition     = aws_s3_bucket.this.bucket == "modulai-tfgen-test-bucket"
    error_message = "bucket should match the value supplied"
  }

  assert {
    condition     = aws_s3_bucket.this.force_destroy == false
    error_message = "force_destroy should default to false"
  }

  assert {
    condition     = length(aws_cloudwatch_metric_alarm.this) == 0
    error_message = "no alarms should be created when alert_rules is left at its null default"
  }
}

run "bucket_and_bucket_prefix_both_set_rejected" {
  command = plan

  variables {
    bucket        = "modulai-tfgen-test-bucket"
    bucket_prefix = "modulai-"
  }

  expect_failures = [
    var.bucket,
  ]
}

# This module's own resource has no surviving optional nested block (every one
# in the real schema is deprecated — see main.tf) — this scenario exercises
# alerts.tf's metric_query dynamic block instead, the only nested-block surface
# left in the module.
run "alert_with_metric_query_plan" {
  command = plan

  variables {
    alert_rules = {
      high_error_rate = {
        comparison_operator = "GreaterThanOrEqualToThreshold"
        evaluation_periods  = 2
        threshold           = 10
        metric_query = [
          {
            id          = "e1"
            expression  = "m1"
            return_data = true
          }
        ]
      }
    }
  }

  assert {
    condition     = length(aws_cloudwatch_metric_alarm.this) == 1
    error_message = "alert_rules with one entry should create exactly one alarm"
  }

  assert {
    condition     = length(aws_cloudwatch_metric_alarm.this["high_error_rate"].metric_query) == 1
    error_message = "the metric_query block should be passed through onto the alarm"
  }
}