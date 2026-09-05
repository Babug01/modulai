#------------------------------------------------------------------------------------------------------------------------------------------
/*
  Sets Providers and Versions

  Generated against aws v6.63.0 (latest at generation time).
*/
#------------------------------------------------------------------------------------------------------------------------------------------
terraform {
  required_version = ">= 1.9.0" # variables.tf's bucket/bucket_prefix cross-variable validation requires 1.9+
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 6.63.0, < 7.0.0"
    }
  }
}

#------------------------------------------------------------------------------------------------------------------------------------------
/*
  Module Logic
  - aws_s3_bucket.this: single S3 bucket instance.
    Multiplicity is the caller's responsibility via `for_each` on the module
    block — see README.md "Creating multiple buckets".

  Nearly every classic S3 "feature" (versioning, encryption, lifecycle rules,
  logging, replication, CORS, website hosting, ACLs/grants) is documented as
  **Deprecated** on this resource in the AWS provider's own docs, each in
  favor of a separate dedicated resource (aws_s3_bucket_versioning,
  aws_s3_bucket_server_side_encryption_configuration, etc.) — deliberately
  excluded here rather than generated as first-class variables. See
  README.md "Composing the rest of the bucket".
*/
#------------------------------------------------------------------------------------------------------------------------------------------
resource "aws_s3_bucket" "this" {
  bucket              = var.bucket
  bucket_namespace    = var.bucket_namespace
  bucket_prefix       = var.bucket_prefix
  force_destroy       = var.force_destroy
  object_lock_enabled = var.object_lock_enabled
  region              = var.region
  tags                = var.tags
}