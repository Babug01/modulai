#------------------------------------------------------------------------------------------------------------------------------------------
/*
  Outputs

  None of aws_s3_bucket's exports are credentials/keys — unlike many other
  resources, nothing here needs `sensitive = true`.
*/
#------------------------------------------------------------------------------------------------------------------------------------------
output "id" {
  description = "Name of the bucket (aws_s3_bucket's id is its bucket name)."
  value       = aws_s3_bucket.this.id
}

output "arn" {
  description = "ARN of the bucket."
  value       = aws_s3_bucket.this.arn
}

output "bucket_domain_name" {
  description = "Bucket domain name, e.g. bucketname.s3.amazonaws.com."
  value       = aws_s3_bucket.this.bucket_domain_name
}

output "bucket_region" {
  description = "AWS region this bucket actually resides in."
  value       = aws_s3_bucket.this.bucket_region
}

output "bucket_regional_domain_name" {
  description = "Bucket region-specific domain name."
  value       = aws_s3_bucket.this.bucket_regional_domain_name
}

output "hosted_zone_id" {
  description = "Route 53 Hosted Zone ID for this bucket's region."
  value       = aws_s3_bucket.this.hosted_zone_id
}

output "tags_all" {
  description = "Map of tags assigned to the bucket, including those inherited from the provider's default_tags configuration block."
  value       = aws_s3_bucket.this.tags_all
}