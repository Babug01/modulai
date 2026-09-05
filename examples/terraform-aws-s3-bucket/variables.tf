#------------------------------------------------------------------------------------------------------------------------------------------
/*
  Variables

  Design: flat variables for top-level scalars. No nested-block variables —
  the only nested block left on this resource's real schema after excluding
  deprecated ones (`timeouts`) carries zero configurable attributes at this
  provider version, so there's nothing to expose.
*/
#------------------------------------------------------------------------------------------------------------------------------------------
variable "bucket" {
  description = "(Optional, Forces new resource) Name of the bucket. If omitted, Terraform will assign a random, unique name. Must be lowercase and less than or equal to 63 characters. Conflicts with bucket_prefix."
  type        = string
  default     = null

  validation {
    condition     = var.bucket == null || var.bucket_prefix == null
    error_message = "bucket and bucket_prefix are mutually exclusive — set at most one."
  }
}

variable "bucket_prefix" {
  description = "(Optional, Forces new resource) Creates a unique bucket name beginning with this prefix. Conflicts with bucket. Must be lowercase and less than or equal to 37 characters."
  type        = string
  default     = null
}

variable "bucket_namespace" {
  description = "(Optional, Forces new resource) Namespace for the bucket, determining bucket naming scope. Valid values: `account-regional`, `global`. Defaults to `global`."
  type        = string
  default     = null

  validation {
    condition     = var.bucket_namespace == null || contains(["account-regional", "global"], var.bucket_namespace)
    error_message = "bucket_namespace must be account-regional or global."
  }
}

variable "force_destroy" {
  description = "(Optional) Boolean that indicates all objects (including locked ones) should be deleted from the bucket when the bucket is destroyed, so the destroy doesn't fail. These objects are not recoverable. Defaults to `false`."
  type        = bool
  default     = false
}

variable "object_lock_enabled" {
  description = "(Optional) Whether this bucket has an Object Lock configuration enabled. This argument is not supported in all regions or partitions."
  type        = bool
  default     = null
}

variable "region" {
  description = "(Optional) Region where this resource will be managed. Defaults to the Region set in the provider configuration."
  type        = string
  default     = null
}

variable "tags" {
  description = "(Optional) Map of tags to assign to the bucket. Defaults to `{}`."
  type        = map(string)
  default     = {}
}

variable "alert_rules" {
  description = "(Optional) CloudWatch metric alarms to create, keyed by a name you choose (used as alarm_name). Generic pass-through — you supply real namespace/metric_name/dimensions (or a metric_query/evaluation_criteria for metric-math or PromQL alarms), matching aws_cloudwatch_metric_alarm's own schema. Set to `null` (the default) or omit entirely for no alerts."
  type = map(object({
    alarm_description                     = optional(string)
    actions_enabled                       = optional(bool)
    comparison_operator                   = optional(string)
    evaluation_periods                    = optional(number)
    metric_name                           = optional(string)
    namespace                             = optional(string)
    period                                = optional(number)
    statistic                             = optional(string)
    extended_statistic                    = optional(string)
    threshold                             = optional(number)
    threshold_metric_id                   = optional(string)
    unit                                  = optional(string)
    dimensions                            = optional(map(string))
    datapoints_to_alarm                   = optional(number)
    evaluation_interval                   = optional(number)
    evaluate_low_sample_count_percentiles = optional(string)
    treat_missing_data                    = optional(string)
    region                                = optional(string)
    tags                                  = optional(map(string))
    alarm_actions                         = optional(list(string), [])
    ok_actions                            = optional(list(string), [])
    insufficient_data_actions             = optional(list(string), [])
    metric_query = optional(list(object({
      id          = string
      account_id  = optional(string)
      expression  = optional(string)
      label       = optional(string)
      period      = optional(number)
      return_data = optional(bool)
      metric = optional(object({
        metric_name = string
        namespace   = optional(string)
        period      = number
        stat        = string
        unit        = optional(string)
        dimensions  = optional(map(string))
      }))
    })), [])
    evaluation_criteria = optional(object({
      promql_criteria = object({
        query           = string
        pending_period  = optional(number)
        recovery_period = optional(number)
      })
    }))
  }))
  default = null
}