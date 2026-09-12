# ==============================================================================
# HyperRoute Zero-Dollar ($0.00) AWS Free Tier Deployment Profile
# Use this tfvars profile with:
#   terraform plan -var-file=free-tier.tfvars
#   terraform apply -var-file=free-tier.tfvars
# ==============================================================================

aws_region   = "us-east-1"
environment  = "free-tier"
cluster_name = "hyperroute-free-cluster"

# Disable expensive multi-broker managed clusters (Self-hosted Kafka / SQS replaces MSK)
enable_msk = false

# Disable expensive multi-node ElastiCache (Local in-memory / container Redis replaces ElastiCache)
enable_elasticache = false

# Enable 100% Free-Tier eligible PostgreSQL DB (750 hours/mo free on db.t4g.micro + 20GB gp3)
enable_rds            = true
rds_instance_class    = "db.t4g.micro"
rds_allocated_storage = 20

# Standard development compute instance types
gateway_instance_type = "t3.medium"
fsm_instance_type     = "t3.medium"

