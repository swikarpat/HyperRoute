variable "aws_region" {
  description = "Target AWS deployment region"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Execution environment name"
  type        = string
  default     = "production"
}

variable "vpc_cidr" {
  description = "Base CIDR block for the dedicated 3-tier VPC"
  type        = string
  default     = "10.100.0.0/16"
}

variable "cluster_name" {
  description = "EKS cluster identifier for the polyglot mesh"
  type        = string
  default     = "hyperroute-core-prod"
}

variable "enable_msk" {
  description = "Toggle Amazon MSK deployment (disable in free-tier to avoid charges)"
  type        = bool
  default     = true
}

variable "enable_elasticache" {
  description = "Toggle Amazon ElastiCache cluster (disable in free-tier to avoid charges)"
  type        = bool
  default     = true
}

variable "enable_rds" {
  description = "Toggle Amazon RDS PostgreSQL database"
  type        = bool
  default     = true
}

variable "rds_instance_class" {
  description = "RDS instance class (db.t4g.micro / db.t3.micro are AWS Free Tier eligible)"
  type        = string
  default     = "db.t4g.micro"
}

variable "rds_allocated_storage" {
  description = "Allocated storage in GB for RDS PostgreSQL (up to 20GB is free tier eligible)"
  type        = number
  default     = 20
}

variable "gateway_instance_type" {
  description = "EC2 instance type for Spring Cloud Gateway pool"
  type        = string
  default     = "m7i.xlarge"
}

variable "fsm_instance_type" {
  description = "EC2 instance type for native C++20 FSM & Agent mesh pool"
  type        = string
  default     = "c7i.2xlarge"
}