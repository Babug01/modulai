#------------------------------------------------------------------------------------------------------------------------------------------
/*
  Outputs
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

output "primary_blob_endpoint" {
  description = "The endpoint URL for blob storage in the primary location."
  value       = azurerm_storage_account.this.primary_blob_endpoint
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

output "identity_principal_id" {
  description = "The Principal ID of the storage account's managed identity, if var.identity was set."
  value       = try(azurerm_storage_account.this.identity[0].principal_id, null)
}

output "identity_tenant_id" {
  description = "The Tenant ID of the storage account's managed identity, if var.identity was set."
  value       = try(azurerm_storage_account.this.identity[0].tenant_id, null)
}