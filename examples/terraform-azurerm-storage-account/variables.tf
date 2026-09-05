#------------------------------------------------------------------------------------------------------------------------------------------
/*
  Variables

  Design: flat variables for top-level scalars; one optional object variable
  per nested block, mirroring the resource's own schema shape.
*/
#------------------------------------------------------------------------------------------------------------------------------------------
variable "name" {
  description = "(Required) The name of the storage account. Must be globally unique across Azure, lowercase alphanumeric only. Changing this forces a new resource."
  type        = string
  nullable    = false

  validation {
    condition     = can(regex("^[a-z0-9]{3,24}$", var.name))
    error_message = "name must be 3-24 lowercase alphanumeric characters."
  }
}

variable "resource_group_name" {
  description = "(Required) The name of the resource group in which to create the storage account. Changing this forces a new resource."
  type        = string
  nullable    = false
}

variable "location" {
  description = "(Required) The Azure region where the storage account should exist. Changing this forces a new resource."
  type        = string
  nullable    = false
}

variable "tags" {
  description = "(Optional) A mapping of tags to assign to the resource. Defaults to `{}`."
  type        = map(string)
  default     = {}
}

variable "account_kind" {
  description = "(Optional) The kind of storage account. One of `BlobStorage`, `BlockBlobStorage`, `FileStorage`, `Storage`, `StorageV2`. Defaults to `StorageV2`."
  type        = string
  default     = "StorageV2"

  validation {
    condition     = contains(["BlobStorage", "BlockBlobStorage", "FileStorage", "Storage", "StorageV2"], var.account_kind)
    error_message = "account_kind must be one of BlobStorage, BlockBlobStorage, FileStorage, Storage, StorageV2."
  }
}

variable "account_tier" {
  description = "(Required) The performance tier. `Standard` or `Premium`. Changing this forces a new resource."
  type        = string
  nullable    = false

  validation {
    condition     = contains(["Standard", "Premium"], var.account_tier)
    error_message = "account_tier must be Standard or Premium."
  }
}

variable "account_replication_type" {
  description = "(Required) The replication type. One of `LRS`, `GRS`, `RAGRS`, `ZRS`, `GZRS`, `RAGZRS`."
  type        = string
  nullable    = false

  validation {
    condition     = contains(["LRS", "GRS", "RAGRS", "ZRS", "GZRS", "RAGZRS"], var.account_replication_type)
    error_message = "account_replication_type must be one of LRS, GRS, RAGRS, ZRS, GZRS, RAGZRS."
  }
}

variable "access_tier" {
  description = "(Optional) Access tier for BlobStorage/FileStorage/StorageV2 kinds. Defaults to `Hot`."
  type        = string
  default     = "Hot"
}

variable "edge_zone" {
  description = "(Optional) The Edge Zone within the Azure region where this storage account should exist. Changing this forces a new resource."
  type        = string
  default     = null
}

variable "provisioned_billing_model_version" {
  description = "(Optional) Version of the provisioned billing model, e.g. when account_kind is FileStorage. Changing this forces a new resource."
  type        = string
  default     = null
}

variable "cross_tenant_replication_enabled" {
  description = "(Optional) Should cross-tenant replication be enabled? Defaults to `false`."
  type        = bool
  default     = false
}

variable "https_traffic_only_enabled" {
  description = "(Optional) Forces HTTPS if enabled. Defaults to `true`."
  type        = bool
  default     = true
}

variable "min_tls_version" {
  description = "(Optional) Minimum supported TLS version. Defaults to `TLS1_2`."
  type        = string
  default     = "TLS1_2"
}

variable "allow_nested_items_to_be_public" {
  description = "(Optional) Allow nested items (containers, blobs) to opt into public access. Defaults to `false`."
  type        = bool
  default     = false
}

variable "shared_access_key_enabled" {
  description = "(Optional) Permit requests authorized with the account access key (Shared Key). Defaults to `true`."
  type        = bool
  default     = true
}

variable "public_network_access_enabled" {
  description = "(Optional) Whether public network access is enabled. Defaults to `true`."
  type        = bool
  default     = true
}

variable "default_to_oauth_authentication" {
  description = "(Optional) Default to Azure AD authorization in the Azure portal when accessing the storage account. Defaults to `false`."
  type        = bool
  default     = false
}

variable "is_hns_enabled" {
  description = "(Optional) Enable Hierarchical Namespace (Data Lake Storage Gen2). Changing this forces a new resource."
  type        = bool
  default     = false
}

variable "nfsv3_enabled" {
  description = "(Optional) Enable NFSv3 protocol. Changing this forces a new resource. Defaults to `false`."
  type        = bool
  default     = false
}

variable "local_user_enabled" {
  description = "(Optional) Is local user (SFTP-style) authentication enabled? Defaults to `true`."
  type        = bool
  default     = true
}

variable "sftp_enabled" {
  description = "(Optional) Enable SFTP for the storage account. Defaults to `false`."
  type        = bool
  default     = false
}

variable "large_file_share_enabled" {
  description = "(Optional) Are Large File Shares enabled? Defaults to `false`."
  type        = bool
  default     = false
}

variable "queue_encryption_key_type" {
  description = "(Optional) Encryption type for the queue service. Defaults to `Service`."
  type        = string
  default     = "Service"
}

variable "table_encryption_key_type" {
  description = "(Optional) Encryption type for the table service. Defaults to `Service`."
  type        = string
  default     = "Service"
}

variable "infrastructure_encryption_enabled" {
  description = "(Optional) Enable infrastructure-level encryption. Changing this forces a new resource. Defaults to `false`."
  type        = bool
  default     = false
}

variable "allowed_copy_scope" {
  description = "(Optional) Permitted scope for copy operations between storage accounts. One of `AAD`, `PrivateLink`, `All`."
  type        = string
  default     = null
}

variable "dns_endpoint_type" {
  description = "(Optional) DNS endpoint type. Changing this forces a new resource. Defaults to `Standard`."
  type        = string
  default     = "Standard"
}

variable "custom_domain" {
  description = "(Optional) Custom domain configuration. Set to `null` to omit (default)."
  type = object({
    name          = string
    use_subdomain = optional(bool)
  })
  default = null
}

variable "customer_managed_key" {
  description = "(Optional) Customer-managed key configuration. Set to `null` to omit (default)."
  type = object({
    key_vault_key_id          = string
    user_assigned_identity_id = string
  })
  default = null
}

variable "identity" {
  description = "(Optional) Managed identity configuration. Set to `null` to omit (default)."
  type = object({
    type         = string
    identity_ids = optional(list(string), [])
  })
  default = null

  validation {
    condition     = var.identity == null || contains(["SystemAssigned", "UserAssigned", "SystemAssigned, UserAssigned"], var.identity.type)
    error_message = "identity.type must be SystemAssigned, UserAssigned, or \"SystemAssigned, UserAssigned\"."
  }
}

variable "blob_properties" {
  description = "(Optional) Blob service properties. Set to `null` to omit (default)."
  type = object({
    versioning_enabled            = optional(bool, false)
    change_feed_enabled           = optional(bool, false)
    change_feed_retention_in_days = optional(number)
    default_service_version       = optional(string)
    last_access_time_enabled      = optional(bool, false)
    cors_rule = optional(list(object({
      allowed_headers    = list(string)
      allowed_methods    = list(string)
      allowed_origins    = list(string)
      exposed_headers    = list(string)
      max_age_in_seconds = number
    })), [])
    delete_retention_policy = optional(object({
      days                     = optional(number, 7)
      permanent_delete_enabled = optional(bool, false)
    }))
    restore_policy = optional(object({
      days = number
    }))
    container_delete_retention_policy = optional(object({
      days = optional(number, 7)
    }))
  })
  default = null
}

variable "share_properties" {
  description = "(Optional) File share service properties. Set to `null` to omit (default)."
  type = object({
    cors_rule = optional(list(object({
      allowed_headers    = list(string)
      allowed_methods    = list(string)
      allowed_origins    = list(string)
      exposed_headers    = list(string)
      max_age_in_seconds = number
    })), [])
    retention_policy = optional(object({
      days = optional(number, 7)
    }))
    smb = optional(object({
      versions                        = optional(list(string))
      authentication_types            = optional(list(string))
      kerberos_ticket_encryption_type = optional(list(string))
      channel_encryption_type         = optional(list(string))
      multichannel_enabled            = optional(bool, false)
    }))
  })
  default = null
}

variable "network_rules" {
  description = "(Optional) Network access rules. Set to `null` to omit (default = fully open)."
  type = object({
    default_action             = string
    bypass                     = optional(list(string), [])
    ip_rules                   = optional(list(string), [])
    virtual_network_subnet_ids = optional(list(string), [])
    private_link_access = optional(list(object({
      endpoint_resource_id = string
      endpoint_tenant_id   = optional(string)
    })), [])
  })
  default = null

  validation {
    condition     = var.network_rules == null || contains(["Allow", "Deny"], var.network_rules.default_action)
    error_message = "network_rules.default_action must be Allow or Deny."
  }
}

variable "azure_files_authentication" {
  description = "(Optional) Azure Files identity-based authentication. Set to `null` to omit (default)."
  type = object({
    directory_type = string
    active_directory = optional(object({
      domain_name         = string
      domain_guid         = string
      domain_sid          = optional(string)
      storage_sid         = optional(string)
      forest_name         = optional(string)
      netbios_domain_name = optional(string)
    }))
    default_share_level_permission = optional(string)
  })
  default = null

  validation {
    condition     = var.azure_files_authentication == null || contains(["AADDS", "AD", "AADKERB"], var.azure_files_authentication.directory_type)
    error_message = "azure_files_authentication.directory_type must be AADDS, AD, or AADKERB."
  }
}

variable "routing" {
  description = "(Optional) Storage endpoint routing preference. Set to `null` to omit (default)."
  type = object({
    publish_internet_endpoints  = optional(bool, false)
    publish_microsoft_endpoints = optional(bool, false)
    choice                      = optional(string, "MicrosoftRouting")
  })
  default = null
}

variable "immutability_policy" {
  description = "(Optional) Account-level default immutability policy. Changing this forces a new resource. Set to `null` to omit (default)."
  type = object({
    allow_protected_append_writes = bool
    state                         = string
    period_since_creation_in_days = number
  })
  default = null

  validation {
    condition     = var.immutability_policy == null || contains(["Disabled", "Unlocked", "Locked"], var.immutability_policy.state)
    error_message = "immutability_policy.state must be Disabled, Unlocked, or Locked."
  }
}

variable "sas_policy" {
  description = "(Optional) Account SAS expiration policy. Set to `null` to omit (default)."
  type = object({
    expiration_period = string
    expiration_action = optional(string, "Log")
  })
  default = null
}

variable "alert_rules" {
  description = "(Optional) Metric alert rules to create for this storage account, keyed by a name you choose. Generic pass-through — you supply real Azure Monitor criteria. Set to `null` (the default) or omit entirely for no alerts."
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