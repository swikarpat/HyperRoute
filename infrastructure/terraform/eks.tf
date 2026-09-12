resource "aws_iam_role" "eks_cluster" {
  name = "HyperRoute-EKS-ClusterRole-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "eks.amazonaws.com" }
    }]
  })

  tags = {
    Environment = var.environment
  }
}

resource "aws_iam_role_policy_attachment" "eks_cluster_policy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSClusterPolicy"
  role       = aws_iam_role.eks_cluster.name
}

resource "aws_eks_cluster" "core" {
  name     = var.cluster_name
  version  = "1.30"
  role_arn = aws_iam_role.eks_cluster.arn

  vpc_config {
    subnet_ids              = aws_subnet.private_app[*].id
    endpoint_private_access = true
    endpoint_public_access  = true
  }

  depends_on = [aws_iam_role_policy_attachment.eks_cluster_policy]

  tags = {
    Environment = var.environment
  }
}

resource "aws_iam_role" "eks_nodes" {
  name = "HyperRoute-EKS-NodeRole-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "ec2.amazonaws.com" }
    }]
  })

  tags = {
    Environment = var.environment
  }
}

resource "aws_iam_role_policy_attachment" "node_worker" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy"
  role       = aws_iam_role.eks_nodes.name
}

resource "aws_iam_role_policy_attachment" "node_cni" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy"
  role       = aws_iam_role.eks_nodes.name
}

resource "aws_iam_role_policy_attachment" "node_registry" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
  role       = aws_iam_role.eks_nodes.name
}

# Node Group 1: General Gateway Tier (Java 21 Spring Boot WebFlux Ingress)
resource "aws_eks_node_group" "gateway_pool" {
  cluster_name    = aws_eks_cluster.core.name
  node_group_name = "gateway-ingress-pool"
  node_role_arn   = aws_iam_role.eks_nodes.arn
  subnet_ids      = aws_subnet.private_app[*].id
  instance_types  = [var.gateway_instance_type]

  scaling_config {
    desired_size = 2
    max_size     = 6
    min_size     = 1
  }

  labels = {
    role = "gateway-ingress"
  }

  tags = {
    Environment = var.environment
  }

  depends_on = [aws_iam_role_policy_attachment.node_worker]
}

# Node Group 2: Native FSM & Agent Mesh (Intel Sapphire Rapids with AVX-512)
resource "aws_eks_node_group" "fsm_agent_pool" {
  cluster_name    = aws_eks_cluster.core.name
  node_group_name = "fsm-avx512-agent-pool"
  node_role_arn   = aws_iam_role.eks_nodes.arn
  subnet_ids      = aws_subnet.private_app[*].id
  instance_types  = [var.fsm_instance_type]

  scaling_config {
    desired_size = 2
    max_size     = 10
    min_size     = 1
  }

  labels = {
    role          = "native-fsm-engine"
    simd_support  = "avx512"
    storage_class = "ephemeral-nvme"
  }

  taint {
    key    = "dedicated"
    value  = "fsm-engine"
    effect = "NO_SCHEDULE"
  }

  tags = {
    Environment = var.environment
  }

  depends_on = [aws_iam_role_policy_attachment.node_worker]
}