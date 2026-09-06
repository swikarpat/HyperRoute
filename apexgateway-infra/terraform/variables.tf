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
  default     = "apexgateway-core-prod"
}