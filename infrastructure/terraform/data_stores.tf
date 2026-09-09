# Security Group for Data Tier
resource "aws_security_group" "data_tier_sg" {
  name        = "apexgateway-data-tier-sg"
  description = "Allow inbound traffic from EKS worker nodes only"
  vpc_id      = aws_vpc.main.id

  ingress {
    description = "Kafka Plaintext / TLS from EKS App Subnets"
    from_port   = 9092
    to_port     = 9094
    protocol    = "tcp"
    cidr_blocks = aws_subnet.private_app[*].cidr_block
  }

  ingress {
    description = "Redis from EKS App Subnets"
    from_port   = 6379
    to_port     = 6379
    protocol    = "tcp"
    cidr_blocks = aws_subnet.private_app[*].cidr_block
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# 1. Amazon MSK (Apache Kafka Event Ledger)
resource "aws_msk_cluster" "event_ledger" {
  cluster_name           = "apexgateway-kafka-ledger"
  kafka_version          = "3.6.0"
  number_of_broker_nodes = 3

  broker_node_group_info {
    instance_type   = "kafka.m7g.large"
    client_subnets  = aws_subnet.private_data[*].id
    security_groups = [aws_security_group.data_tier_sg.id]

    storage_info {
      ebs_storage_info {
        volume_size = 500
      }
    }
  }

  encryption_info {
    encryption_in_transit {
      client_broker = "TLS"
      in_cluster    = true
    }
  }
}

# 2. Amazon ElastiCache (Valkey / Redis Semantic Cache)
resource "aws_elasticache_subnet_group" "redis" {
  name       = "apexgateway-redis-subnet-group"
  subnet_ids = aws_subnet.private_data[*].id
}

resource "aws_elasticache_replication_group" "semantic_cache" {
  replication_group_id = "apexgateway-cache"
  description          = "Multi-AZ Semantic Cache with Vector Similarity capabilities"
  node_type            = "cache.r7g.large"
  num_cache_clusters   = 2
  port                 = 6379
  parameter_group_name = "default.redis7"
  subnet_group_name    = aws_elasticache_subnet_group.redis.name
  security_group_ids   = [aws_security_group.data_tier_sg.id]

  automatic_failover_enabled = true
  at_rest_encryption_enabled = true
  transit_encryption_enabled = true
}