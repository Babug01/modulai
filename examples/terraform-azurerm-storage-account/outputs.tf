#------------------------------------------------------------------------------------------------------------------------------------------
/*
  Outputs

  Curated to the commonly consumed subset of the resource's ~60 exported
  attributes. azurerm_storage_account also exports a full primary/secondary
  x blob/queue/table/file/dfs/web x standard/internet/microsoft-routing
  endpoint matrix (~48 additional endpoint/host attributes) — not duplicated
  here to avoid output sprawl. Reference azurerm_storage_account.this.<attribute>
  directly from a consuming module if one of those is needed.
*/
#------------------------------------------------------------------------------------------------------------------------------------------
output "id" {
  description = "The resource ID of the storage account."
  value       = azurerm_storage_account.this.id
}

output "name" {
  description = "The name of the storage account."
  value       = azurerm_storage_account.this.name
}

output "primary_location" {
  description = "The primary location of the storage account."
  value       = azurerm_storage_account.this.primary_location
}

output "secondary_location" {
  description = "The secondary location of the storage account (only set for geo-redundant replication types)."
  value       = azurerm_storage_account.this.secondary_location
}

output "primary_blob_endpoint" {
  description = "The endpoint URL for blob storage in the primary location."
  value       = azurerm_storage_account.this.primary_blob_endpoint
}

output "primary_blob_host" {
  description = "The hostname (with port if applicable) for blob storage in the primary location."
  value       = azurerm_storage_account.this.primary_blob_host
}

output "primary_access_key" {
  description = "The primary access key for the storage account."
  value       = azurerm_storage_account.this.primary_access_key
  sensitive   = true
}

output "secondary_access_key" {
  description = "The secondary access key for the storage account."
  value       = azurerm_storage_account.this.secondary_access_key
  sensitive   = true
}

output "primary_connection_string" {
  description = "The connection string associated with the primary location."
  value       = azurerm_storage_account.this.primary_connection_string
  sensitive   = true
}

output "secondary_connection_string" {
  description = "The connection string associated with the secondary location."
  value       = azurerm_storage_account.this.secondary_connection_string
  sensitive   = true
}

output "primary_blob_connection_string" {
  description = "The connection string associated with the primary blob location."
  value       = azurerm_storage_account.this.primary_blob_connection_string
  sensitive   = true
}

output "account_replication_type_migration_in_progress" {
  description = "Whether a replication type migration is currently in progress."
  value       = azurerm_storage_account.this.account_replication_type_migration_in_progress
}

output "identity" {
  description = "The managed identity block (principal_id, tenant_id), if var.identity was set."
  value       = try(azurerm_storage_account.this.identity, null)
}
