output "vpc_id" {
  value = aws_vpc.main.id
}

output "eks_cluster_endpoint" {
  value = aws_eks_cluster.core.endpoint
}

output "eks_cluster_name" {
  value = aws_eks_cluster.core.name
}

output "fsm_node_group_arn" {
  value = aws_eks_node_group.fsm_agent_pool.arn
}

output "msk_bootstrap_brokers_tls" {
  value = aws_msk_cluster.event_ledger.bootstrap_brokers_tls
}

output "redis_primary_endpoint" {
  value = aws_elasticache_replication_group.semantic_cache.primary_endpoint_address
}