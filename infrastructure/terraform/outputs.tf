output "vpc_id" {
  description = "VPC ID"
  value       = aws_vpc.main.id
}

output "eks_cluster_endpoint" {
  description = "EKS Cluster API endpoint"
  value       = aws_eks_cluster.core.endpoint
}

output "eks_cluster_name" {
  description = "EKS Cluster Name"
  value       = aws_eks_cluster.core.name
}

output "fsm_node_group_arn" {
  description = "EKS FSM AVX-512 Node Group ARN"
  value       = aws_eks_node_group.fsm_agent_pool.arn
}

output "msk_bootstrap_brokers_tls" {
  description = "Amazon MSK TLS bootstrap brokers (null if enable_msk=false)"
  value       = try(aws_msk_cluster.event_ledger[0].bootstrap_brokers_tls, null)
}

output "redis_primary_endpoint" {
  description = "Amazon ElastiCache Redis primary endpoint (null if enable_elasticache=false)"
  value       = try(aws_elasticache_replication_group.semantic_cache[0].primary_endpoint_address, null)
}

output "rds_postgres_endpoint" {
  description = "Amazon RDS PostgreSQL endpoint"
  value       = try(aws_db_instance.postgres[0].endpoint, null)
}

output "sqs_alerts_ingest_url" {
  description = "Amazon SQS Ingestion Queue URL"
  value       = aws_sqs_queue.alert_ingest.url
}

output "sqs_alerts_dlq_url" {
  description = "Amazon SQS Dead Letter Queue URL"
  value       = aws_sqs_queue.alert_dlq.url
}

output "sns_compliance_alerts_arn" {
  description = "Amazon SNS Compliance Alerts Topic ARN"
  value       = aws_sns_topic.compliance_alerts.arn
}

output "cloudfront_distribution_domain" {
  description = "CloudFront Mission Control UI Distribution Domain Name"
  value       = aws_cloudfront_distribution.cdn.domain_name
}

output "s3_ui_bucket_name" {
  description = "S3 UI Hosting Bucket Name"
  value       = aws_s3_bucket.ui_hosting.bucket
}