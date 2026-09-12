# ==============================================================================
# AWS RDS (Relational Database Service) - PostgreSQL
# Enterprise Relational Store with Automatic AWS Secrets Manager Password Management
# 100% Free Tier Eligible (750 hours/month db.t4g.micro or db.t3.micro + 20GB storage)
# ==============================================================================

resource "aws_db_subnet_group" "rds" {
  count      = var.enable_rds ? 1 : 0
  name       = "hyperroute-rds-subnet-group-${var.environment}"
  subnet_ids = aws_subnet.private_data[*].id

  tags = {
    Name        = "hyperroute-rds-subnet-group"
    Environment = var.environment
  }
}

resource "aws_security_group" "rds" {
  count       = var.enable_rds ? 1 : 0
  name        = "hyperroute-rds-sg-${var.environment}"
  description = "Allow inbound PostgreSQL traffic from EKS worker nodes only"
  vpc_id      = aws_vpc.main.id

  ingress {
    description = "PostgreSQL from EKS App Subnets"
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = aws_subnet.private_app[*].cidr_block
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "hyperroute-rds-sg"
    Environment = var.environment
  }
}

resource "aws_db_instance" "postgres" {
  count                       = var.enable_rds ? 1 : 0
  identifier                  = "hyperroute-postgres-${var.environment}"
  engine                      = "postgres"
  engine_version              = "16.3"
  instance_class              = var.rds_instance_class
  allocated_storage           = var.rds_allocated_storage
  max_allocated_storage       = 20 # Keep within Free Tier limits
  storage_type                = "gp3"
  db_name                     = "hyperroute"
  username                    = "hyperroute_admin"
  manage_master_user_password = true # Auto-generates and rotates secret in AWS Secrets Manager

  db_subnet_group_name   = aws_db_subnet_group.rds[0].name
  vpc_security_group_ids = [aws_security_group.rds[0].id]
  publicly_accessible    = false
  skip_final_snapshot    = true
  deletion_protection    = false

  tags = {
    Name        = "hyperroute-postgres"
    Environment = var.environment
  }
}

