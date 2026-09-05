#------------------------------------------------------------------------------------------------------------------------------------------
/*
  Variables

  Flat variables for top-level scalars; one optional object (or list-of-object)
  variable per nested structure, mirroring the resource's own schema shape
  (provider docs, azurerm v5.4.0).
*/
#------------------------------------------------------------------------------------------------------------------------------------------
/*
  Identity and Location
*/
#------------------------------------------------------------------------------------------------------------------------------------------
variable "name" {
  description = "(Required) The name of the Key Vault. Must be globally unique across Azure. Changing this forces a new resource."
  type        = string
  nullable    = false
}

variable "location" {
  description = "(Required) The Azure region where the Key Vault should exist. Changing this forces a new resource."
  type        = string
  nullable    = false
}

variable "resource_group_name" {
  description = "(Required) The name of the resource group in which to create the Key Vault. Changing this forces a new resource."
  type        = string
  nullable    = false
}

variable "tenant_id" {
  description = "(Required) The Azure Active Directory tenant ID used for authenticating requests to the key vault."
  type        = string
  nullable    = false
}

variable "sku_name" {
  description = "(Required) The SKU for this Key Vault. One of `standard` or `premium`."
  type        = string
  nullable    = false

  validation {
    condition     = contains(["standard", "premium"], var.sku_name)
    error_message = "sku_name must be standard or premium."
  }
}

variable "tags" {
  description = "(Optional) A mapping of tags to assign to the resource. Defaults to `{}`."
  type        = map(string)
  default     = {}
}

#------------------------------------------------------------------------------------------------------------------------------------------
/*
  Authorization and Access Policies
*/
#------------------------------------------------------------------------------------------------------------------------------------------
variable "rbac_authorization_enabled" {
  description = "(Required) Should this Key Vault use Azure RBAC for authorization of data actions, instead of access policies?"
  type        = bool
  nullable    = false
}

variable "access_policy" {
  description = "(Optional) Up to 1024 access policy entries. Ignored when rbac_authorization_enabled is true. Defaults to `[]`. Set explicitly to `[]` to remove existing policies — omitting the argument does not clear them (provider requirement, since access policies can also be managed by the separate azurerm_key_vault_access_policy resource)."
  type = list(object({
    tenant_id               = string
    object_id               = string
    application_id          = optional(string)
    certificate_permissions = optional(list(string), [])
    key_permissions         = optional(list(string), [])
    secret_permissions      = optional(list(string), [])
    storage_permissions     = optional(list(string), [])
  }))
  default = []
}

#------------------------------------------------------------------------------------------------------------------------------------------
/*
  Network Access
*/
#------------------------------------------------------------------------------------------------------------------------------------------
variable "public_network_access_enabled" {
  description = "(Optional) Whether public network access is allowed for this Key Vault. Defaults to `true`."
  type        = bool
  default     = true
}

variable "network_acls" {
  description = "(Optional) Network ACL rules. When set, both bypass and default_action are required by the provider. Set to `null` to omit (default = no network restriction)."
  type = object({
    bypass                     = string
    default_action             = string
    ip_rules                   = optional(list(string), [])
    virtual_network_subnet_ids = optional(list(string), [])
  })
  default = null

  validation {
    condition     = var.network_acls == null || contains(["AzureServices", "None"], var.network_acls.bypass)
    error_message = "network_acls.bypass must be AzureServices or None."
  }

  validation {
    condition     = var.network_acls == null || contains(["Allow", "Deny"], var.network_acls.default_action)
    error_message = "network_acls.default_action must be Allow or Deny."
  }
}

#------------------------------------------------------------------------------------------------------------------------------------------
/*
  Deletion Protection and Deployment Access
*/
#------------------------------------------------------------------------------------------------------------------------------------------
variable "purge_protection_enabled" {
  description = "(Optional) Is Purge Protection enabled for this Key Vault? Cannot be disabled once enabled. Defaults to `false`."
  type        = bool
  default     = false
}

variable "soft_delete_retention_days" {
  description = "(Optional) Days that soft-deleted items are retained, between 7 and 90. Can only be set at creation, never updated afterwards. Defaults to `90`."
  type        = number
  default     = 90

  validation {
    condition     = var.soft_delete_retention_days >= 7 && var.soft_delete_retention_days <= 90
    error_message = "soft_delete_retention_days must be between 7 and 90."
  }
}

variable "enabled_for_deployment" {
  description = "(Optional) May Azure Virtual Machines retrieve certificates stored as secrets from the vault? Defaults to `false`."
  type        = bool
  default     = false
}

variable "enabled_for_disk_encryption" {
  description = "(Optional) May Azure Disk Encryption retrieve secrets from the vault and unwrap keys? Defaults to `false`."
  type        = bool
  default     = false
}

variable "enabled_for_template_deployment" {
  description = "(Optional) May Azure Resource Manager retrieve secrets from the vault? Defaults to `false`."
  type        = bool
  default     = false
}

#------------------------------------------------------------------------------------------------------------------------------------------
/*
  Alerts
*/
#------------------------------------------------------------------------------------------------------------------------------------------
variable "alert_rules" {
  description = "(Optional) Metric alert rules to create for this Key Vault, keyed by a name you choose. This is a generic pass-through — the module doesn't curate which Key Vault metrics matter, you supply real Azure Monitor criteria (metric_namespace/metric_name/aggregation/operator). Set to `null` (the default) or omit entirely for no alerts."
  type = map(object({
    metric_namespace = string
    metric_name      = string
    aggregation      = string
    operator         = string
    threshold        = number
    severity         = optional(number, 3)
    frequency        = optional(string, "PT5M")
    window_size      = optional(string, "PT15M")
    action_group_ids = optional(list(string), [])
    description      = optional(string)
  }))
  default = null
}
