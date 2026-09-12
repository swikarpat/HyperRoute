# S3 Bucket for Static Mission Control UI Assets
resource "aws_s3_bucket" "ui_hosting" {
  bucket        = "hyperroute-mission-control-${var.environment}"
  force_destroy = true

  tags = {
    Name        = "hyperroute-mission-control-ui"
    Environment = var.environment
  }
}

resource "aws_s3_bucket_public_access_block" "ui_hosting_block" {
  bucket                  = aws_s3_bucket.ui_hosting.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# CloudFront Origin Access Control (OAC) for Zero-Trust S3 Origin
resource "aws_cloudfront_origin_access_control" "oac" {
  name                              = "hyperroute-oac-${var.environment}"
  description                       = "OAC Policy for HyperRoute S3 UI Distribution"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

# CloudFront Distribution (Edge TLS 1.3 Termination)
resource "aws_cloudfront_distribution" "cdn" {
  enabled             = true
  is_ipv6_enabled     = true
  default_root_object = "index.html"

  origin {
    domain_name              = aws_s3_bucket.ui_hosting.bucket_regional_domain_name
    origin_id                = "S3-HyperRoute-UI"
    origin_access_control_id = aws_cloudfront_origin_access_control.oac.id
  }

  default_cache_behavior {
    allowed_methods  = ["GET", "HEAD", "OPTIONS"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "S3-HyperRoute-UI"

    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }

    viewer_protocol_policy = "redirect-to-https"
    min_ttl                = 0
    default_ttl            = 86400
    max_ttl                = 31536000
    compress               = true
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    cloudfront_default_certificate = true
  }

  tags = {
    Environment = var.environment
  }
}

# CloudFront OAC S3 Bucket Policy (Zero-Trust S3 Origin Access)
resource "aws_s3_bucket_policy" "ui_hosting_oac_policy" {
  bucket = aws_s3_bucket.ui_hosting.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowCloudFrontServicePrincipalReadOnly"
        Effect = "Allow"
        Principal = {
          Service = "cloudfront.amazonaws.com"
        }
        Action   = "s3:GetObject"
        Resource = "${aws_s3_bucket.ui_hosting.arn}/*"
        Condition = {
          StringEquals = {
            "AWS:SourceArn" = aws_cloudfront_distribution.cdn.arn
          }
        }
      }
    ]
  })
}
