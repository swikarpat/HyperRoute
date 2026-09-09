data "tls_certificate" "eks" {
  url = aws_eks_cluster.core.identity[0].oidc[0].issuer
}

resource "aws_iam_openid_connect_provider" "eks" {
  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = [data.tls_certificate.eks.certificates[0].sha1_fingerprint]
  url             = aws_eks_cluster.core.identity[0].oidc[0].issuer
}

# IRSA: Pod-level IAM role for Python ADK agent runtime
resource "aws_iam_role" "agent_runtime_pod" {
  name = "ApexGateway-AgentRuntime-PodRole"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRoleWithWebIdentity"
      Effect = "Allow"
      Principal = {
        Federated = aws_iam_openid_connect_provider.eks.arn
      }
      Condition = {
        StringEquals = {
          "${replace(aws_iam_openid_connect_provider.eks.url, "https://", "")}:sub" : "system:serviceaccount:apexgateway:agent-runtime-sa"
        }
      }
    }]
  })
}

resource "aws_iam_policy" "agent_least_privilege" {
  name        = "ApexGateway-AgentRuntimePolicy"
  description = "Granular least-privilege permissions for Agent runtime telemetry and caching"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["secretsmanager:GetSecretValue"]
        Resource = "arn:aws:secretsmanager:${var.aws_region}:*:secret:apexgateway/*"
      },
      {
        Effect   = "Allow"
        Action   = ["kafka-cluster:Connect", "kafka-cluster:DescribeTopic", "kafka-cluster:WriteData"]
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "attach_agent_policy" {
  role       = aws_iam_role.agent_runtime_pod.name
  policy_arn = aws_iam_policy.agent_least_privilege.arn
}