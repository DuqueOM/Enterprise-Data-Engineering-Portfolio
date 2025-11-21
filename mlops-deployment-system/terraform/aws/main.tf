# Terraform configuration for MLOps deployment on AWS
# Creates EKS cluster, RDS, ElastiCache, S3, and supporting infrastructure

terraform {
  required_version = ">= 1.5.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.23"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.11"
    }
  }
  
  # Remote state management
  backend "s3" {
    bucket         = "mlops-terraform-state"
    key            = "mlops/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-lock"
  }
}

provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = {
      Project     = "MLOps"
      Environment = var.environment
      ManagedBy   = "Terraform"
      Owner       = var.owner_email
    }
  }
}

# Data sources
data "aws_availability_zones" "available" {
  state = "available"
}

data "aws_caller_identity" "current" {}

# Local variables
locals {
  cluster_name = "${var.project_name}-${var.environment}"
  
  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
  
  azs = slice(data.aws_availability_zones.available.names, 0, 3)
}

#######################
# VPC and Networking
#######################

module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"
  
  name = "${local.cluster_name}-vpc"
  cidr = var.vpc_cidr
  
  azs             = local.azs
  private_subnets = var.private_subnet_cidrs
  public_subnets  = var.public_subnet_cidrs
  
  enable_nat_gateway   = true
  single_nat_gateway   = var.environment == "dev" ? true : false
  enable_dns_hostnames = true
  enable_dns_support   = true
  
  # Kubernetes tags for subnet discovery
  public_subnet_tags = {
    "kubernetes.io/role/elb"                    = "1"
    "kubernetes.io/cluster/${local.cluster_name}" = "shared"
  }
  
  private_subnet_tags = {
    "kubernetes.io/role/internal-elb"           = "1"
    "kubernetes.io/cluster/${local.cluster_name}" = "shared"
  }
  
  tags = local.common_tags
}

#######################
# EKS Cluster
#######################

module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 19.0"
  
  cluster_name    = local.cluster_name
  cluster_version = var.kubernetes_version
  
  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets
  
  # Cluster endpoint access
  cluster_endpoint_public_access  = true
  cluster_endpoint_private_access = true
  
  # OIDC provider for IAM roles for service accounts
  enable_irsa = true
  
  # Cluster addons
  cluster_addons = {
    coredns = {
      most_recent = true
    }
    kube-proxy = {
      most_recent = true
    }
    vpc-cni = {
      most_recent = true
    }
    aws-ebs-csi-driver = {
      most_recent              = true
      service_account_role_arn = module.ebs_csi_driver_irsa.iam_role_arn
    }
  }
  
  # Managed node groups
  eks_managed_node_groups = {
    # General purpose nodes
    general = {
      name = "${local.cluster_name}-general"
      
      instance_types = var.node_instance_types
      capacity_type  = var.environment == "prod" ? "ON_DEMAND" : "SPOT"
      
      min_size     = var.node_group_min_size
      max_size     = var.node_group_max_size
      desired_size = var.node_group_desired_size
      
      disk_size = 50
      
      labels = {
        role = "general"
      }
      
      tags = merge(
        local.common_tags,
        {
          Name = "${local.cluster_name}-general-node"
        }
      )
    }
    
    # GPU nodes for ML inference (optional)
    gpu = {
      name = "${local.cluster_name}-gpu"
      
      instance_types = ["g4dn.xlarge"]
      capacity_type  = "SPOT"
      
      min_size     = 0
      max_size     = 3
      desired_size = 0
      
      disk_size = 100
      
      labels = {
        role     = "ml-inference"
        gpu      = "true"
        workload = "ml"
      }
      
      taints = [
        {
          key    = "nvidia.com/gpu"
          value  = "true"
          effect = "NoSchedule"
        }
      ]
      
      tags = merge(
        local.common_tags,
        {
          Name = "${local.cluster_name}-gpu-node"
        }
      )
    }
  }
  
  # Cluster security group rules
  cluster_security_group_additional_rules = {
    ingress_nodes_ephemeral_ports_tcp = {
      description                = "Nodes to cluster API"
      protocol                   = "tcp"
      from_port                  = 1025
      to_port                    = 65535
      type                       = "ingress"
      source_node_security_group = true
    }
  }
  
  # Node security group rules
  node_security_group_additional_rules = {
    ingress_self_all = {
      description = "Node to node all ports/protocols"
      protocol    = "-1"
      from_port   = 0
      to_port     = 0
      type        = "ingress"
      self        = true
    }
  }
  
  tags = local.common_tags
}

# EBS CSI Driver IAM role
module "ebs_csi_driver_irsa" {
  source  = "terraform-aws-modules/iam/aws//modules/iam-role-for-service-accounts-eks"
  version = "~> 5.0"
  
  role_name = "${local.cluster_name}-ebs-csi-driver"
  
  attach_ebs_csi_policy = true
  
  oidc_providers = {
    main = {
      provider_arn               = module.eks.oidc_provider_arn
      namespace_service_accounts = ["kube-system:ebs-csi-controller-sa"]
    }
  }
  
  tags = local.common_tags
}

#######################
# RDS PostgreSQL
#######################

module "rds" {
  source  = "terraform-aws-modules/rds/aws"
  version = "~> 6.0"
  
  identifier = "${local.cluster_name}-db"
  
  engine               = "postgres"
  engine_version       = "15.4"
  family               = "postgres15"
  major_engine_version = "15"
  instance_class       = var.db_instance_class
  
  allocated_storage     = var.db_allocated_storage
  max_allocated_storage = var.db_max_allocated_storage
  storage_encrypted     = true
  
  db_name  = var.db_name
  username = var.db_username
  port     = 5432
  
  # Auto-generate and store password in Secrets Manager
  manage_master_user_password = true
  
  multi_az               = var.environment == "prod" ? true : false
  db_subnet_group_name   = module.vpc.database_subnet_group_name
  vpc_security_group_ids = [aws_security_group.rds.id]
  
  backup_retention_period = var.environment == "prod" ? 30 : 7
  skip_final_snapshot     = var.environment != "prod"
  deletion_protection     = var.environment == "prod"
  
  enabled_cloudwatch_logs_exports = ["postgresql", "upgrade"]
  
  performance_insights_enabled = var.environment == "prod"
  
  tags = local.common_tags
}

# RDS Security Group
resource "aws_security_group" "rds" {
  name_prefix = "${local.cluster_name}-rds-"
  vpc_id      = module.vpc.vpc_id
  description = "Security group for RDS PostgreSQL"
  
  ingress {
    description     = "PostgreSQL from EKS nodes"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [module.eks.node_security_group_id]
  }
  
  egress {
    description = "Allow all outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  tags = merge(
    local.common_tags,
    { Name = "${local.cluster_name}-rds-sg" }
  )
}

#######################
# ElastiCache Redis
#######################

module "redis" {
  source  = "terraform-aws-modules/elasticache/aws"
  version = "~> 1.0"
  
  cluster_id      = "${local.cluster_name}-redis"
  engine          = "redis"
  engine_version  = "7.0"
  node_type       = var.redis_node_type
  num_cache_nodes = var.environment == "prod" ? 2 : 1
  
  subnet_group_name = module.vpc.elasticache_subnet_group_name
  security_group_ids = [aws_security_group.redis.id]
  
  at_rest_encryption_enabled = true
  transit_encryption_enabled = true
  auth_token_enabled         = true
  
  parameter_group_family = "redis7"
  
  snapshot_retention_limit = var.environment == "prod" ? 5 : 1
  
  tags = local.common_tags
}

# Redis Security Group
resource "aws_security_group" "redis" {
  name_prefix = "${local.cluster_name}-redis-"
  vpc_id      = module.vpc.vpc_id
  description = "Security group for ElastiCache Redis"
  
  ingress {
    description     = "Redis from EKS nodes"
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [module.eks.node_security_group_id]
  }
  
  egress {
    description = "Allow all outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  tags = merge(
    local.common_tags,
    { Name = "${local.cluster_name}-redis-sg" }
  )
}

#######################
# S3 Buckets
#######################

# Model artifacts bucket
module "s3_models" {
  source  = "terraform-aws-modules/s3-bucket/aws"
  version = "~> 3.0"
  
  bucket = "${local.cluster_name}-models"
  
  versioning = {
    enabled = true
  }
  
  server_side_encryption_configuration = {
    rule = {
      apply_server_side_encryption_by_default = {
        sse_algorithm = "AES256"
      }
    }
  }
  
  lifecycle_rule = [
    {
      id      = "archive-old-versions"
      enabled = true
      
      noncurrent_version_transition = [
        {
          days          = 90
          storage_class = "GLACIER"
        }
      ]
      
      noncurrent_version_expiration = {
        days = 365
      }
    }
  ]
  
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
  
  tags = local.common_tags
}

# Data bucket
module "s3_data" {
  source  = "terraform-aws-modules/s3-bucket/aws"
  version = "~> 3.0"
  
  bucket = "${local.cluster_name}-data"
  
  versioning = {
    enabled = false
  }
  
  server_side_encryption_configuration = {
    rule = {
      apply_server_side_encryption_by_default = {
        sse_algorithm = "AES256"
      }
    }
  }
  
  lifecycle_rule = [
    {
      id      = "delete-old-data"
      enabled = true
      
      expiration = {
        days = 90
      }
    }
  ]
  
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
  
  tags = local.common_tags
}

#######################
# IAM Roles for Pods
#######################

# IAM role for MLOps application (IRSA)
module "mlops_app_irsa" {
  source  = "terraform-aws-modules/iam/aws//modules/iam-role-for-service-accounts-eks"
  version = "~> 5.0"
  
  role_name = "${local.cluster_name}-mlops-app"
  
  role_policy_arns = {
    s3_access = aws_iam_policy.mlops_s3_access.arn
  }
  
  oidc_providers = {
    main = {
      provider_arn               = module.eks.oidc_provider_arn
      namespace_service_accounts = ["mlops:mlops-app"]
    }
  }
  
  tags = local.common_tags
}

# S3 access policy
resource "aws_iam_policy" "mlops_s3_access" {
  name        = "${local.cluster_name}-s3-access"
  description = "S3 access for MLOps application"
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Resource = [
          module.s3_models.s3_bucket_arn,
          "${module.s3_models.s3_bucket_arn}/*",
          module.s3_data.s3_bucket_arn,
          "${module.s3_data.s3_bucket_arn}/*"
        ]
      }
    ]
  })
  
  tags = local.common_tags
}

#######################
# CloudWatch Log Groups
#######################

resource "aws_cloudwatch_log_group" "eks_cluster" {
  name              = "/aws/eks/${local.cluster_name}/cluster"
  retention_in_days = var.environment == "prod" ? 90 : 30
  
  tags = local.common_tags
}

resource "aws_cloudwatch_log_group" "application" {
  name              = "/aws/eks/${local.cluster_name}/application"
  retention_in_days = var.environment == "prod" ? 90 : 30
  
  tags = local.common_tags
}
