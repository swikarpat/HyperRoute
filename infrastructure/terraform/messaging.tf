# ==============================================================================
# AWS SQS (Simple Queue Service) & SNS (Simple Notification Service)
# Enterprise Asynchronous Decoupling & Dead Letter Queue (DLQ) Architecture
# Eligible for AWS Free Tier (1M SQS requests/mo + 1M SNS publishes/mo)
# ==============================================================================

# 1. Dead Letter Queue (DLQ) for poisoned or unprocessable anomaly alerts
resource "aws_sqs_queue" "alert_dlq" {
  name                      = "hyperroute-alerts-dlq-${var.environment}"
  message_retention_seconds = 1209600 # 14 days retention for post-mortem analysis
  receive_wait_time_seconds = 20      # Long polling

  tags = {
    Name        = "hyperroute-alerts-dlq"
    Environment = var.environment
  }
}

# 2. Main Alert Ingest Queue with automated DLQ Redrive Policy
resource "aws_sqs_queue" "alert_ingest" {
  name                       = "hyperroute-alerts-ingest-${var.environment}"
  visibility_timeout_seconds = 60
  message_retention_seconds  = 345600 # 4 days
  receive_wait_time_seconds  = 20     # Long polling enabled for zero empty-receive waste

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.alert_dlq.arn
    maxReceiveCount     = 3 # Route to DLQ after 3 failed agent processing attempts
  })

  tags = {
    Name        = "hyperroute-alerts-ingest"
    Environment = var.environment
  }
}

# 3. SNS Topic for Human-in-the-Loop Compliance Escalations & PagerDuty/Email
resource "aws_sns_topic" "compliance_alerts" {
  name = "hyperroute-compliance-alerts-${var.environment}"

  tags = {
    Name        = "hyperroute-compliance-alerts"
    Environment = var.environment
  }
}

# 4. SQS Queue Subscription to SNS Topic (Pub/Sub Fan-Out Architecture)
resource "aws_sqs_queue" "compliance_audit_queue" {
  name                      = "hyperroute-compliance-audit-${var.environment}"
  message_retention_seconds = 604800 # 7 days
  receive_wait_time_seconds = 20

  tags = {
    Name        = "hyperroute-compliance-audit"
    Environment = var.environment
  }
}

resource "aws_sns_topic_subscription" "audit_queue_subscription" {
  topic_arn = aws_sns_topic.compliance_alerts.arn
  protocol  = "sqs"
  endpoint  = aws_sqs_queue.compliance_audit_queue.arn
}

resource "aws_sqs_queue_policy" "compliance_audit_policy" {
  queue_url = aws_sqs_queue.compliance_audit_queue.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowSNSFanOut"
        Effect = "Allow"
        Principal = {
          Service = "sns.amazonaws.com"
        }
        Action   = "sqs:SendMessage"
        Resource = aws_sqs_queue.compliance_audit_queue.arn
        Condition = {
          ArnEquals = {
            "aws:SourceArn" = aws_sns_topic.compliance_alerts.arn
          }
        }
      }
    ]
  })
}

