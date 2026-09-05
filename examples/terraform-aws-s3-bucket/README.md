# terraform-aws-s3-bucket

Manages a single S3 bucket. Generated from `aws_s3_bucket`'s real provider
schema and documentation, pinned to **aws v6.63.0**.

## Usage

```hcl
module "bucket" {
  source = "./terraform-aws-s3-bucket"

  bucket = "my-example-bucket"

  tags = {
    environment = "staging"
  }
}
```

## Composing the rest of the bucket

At this provider version, nearly every "classic" S3 feature is documented as
**Deprecated** directly on `aws_s3_bucket` — versioning, server-side
encryption, lifecycle rules, access logging, replication, CORS, website
hosting, and ACLs/grants all point to a separate dedicated resource instead.
This module deliberately generates variables only for what's still current
(`bucket`, `bucket_namespace`, `bucket_prefix`, `force_destroy`,
`object_lock_enabled`, `region`, `tags`) rather than exposing a dozen
deprecated arguments as if they were best practice. Add the features you need
as their own resources/modules alongside this one, e.g.:

```hcl
resource "aws_s3_bucket_versioning" "this" {
  bucket = module.bucket.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "this" {
  bucket = module.bucket.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}
```

## Creating multiple buckets

This module manages **one** bucket. Need three? Don't copy-paste the
`module` block three times with different values — that's what `for_each`
replaces:

```hcl
# The boring way — repeat the block per bucket, only values differ:
module "bucket_logs" {
  source = "./terraform-aws-s3-bucket"
  bucket = "my-app-logs"
}
module "bucket_assets" {
  source = "./terraform-aws-s3-bucket"
  bucket = "my-app-assets"
}
```

```hcl
# The for_each way — one block, one variable (a map), as many buckets as it has entries:
variable "buckets" {
  type    = map(object({ force_destroy = optional(bool, false) }))
  default = {
    logs   = { force_destroy = true }
    assets = {}
  }
}

module "bucket" {
  source   = "./terraform-aws-s3-bucket"
  for_each = var.buckets

  bucket        = "my-app-${each.key}"
  force_destroy = each.value.force_destroy
}
```

This creates `module.bucket["logs"]` and `module.bucket["assets"]` from one
block. `each.key` is the map key; `each.value` is that entry's object. Add a
third bucket by adding a third entry to `var.buckets` — no new `module`
block needed. The module's own `variables.tf` doesn't change either way;
`for_each` just calls it repeatedly, once per map entry.

## Alerts

`null` (the default) or omitting `alert_rules` entirely creates no alarms.
This is a generic pass-through — you supply real CloudWatch criteria, and
point it at this bucket yourself (there's no `scopes`-style target field on
this alarm resource):

```hcl
module "bucket" {
  source = "./terraform-aws-s3-bucket"
  bucket = "my-example-bucket"

  alert_rules = {
    no_requests = {
      namespace           = "AWS/S3"
      metric_name         = "NumberOfObjects"
      statistic           = "Average"
      comparison_operator = "LessThanThreshold"
      threshold           = 1
      period              = 86400
      evaluation_periods  = 1
      dimensions = {
        BucketName  = module.bucket.id
        StorageType = "AllStorageTypes"
      }
    }
  }
}
```

## Requirements

| Name | Version |
|---|---|
| terraform | >= 1.9.0 |
| aws | >= 6.63.0, < 7.0.0 |

## Testing

```bash
terraform init
terraform test
```

Runs entirely offline via `mock_provider` — no AWS account required.