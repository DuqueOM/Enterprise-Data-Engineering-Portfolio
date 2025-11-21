# Terraform outputs for AWS MLOps deployment

#######################
# VPC
#######################

output "vpc_id" {
  description = "VPC ID"
  value       = module.vpc.vpc_id
}

output "vpc_cidr_block" {
  description = "VPC CIDR block"
  value       = module.vpc.vpc_cidr_block
}

output "private_subnet_ids" {
  description = "Private subnet IDs"
  value       = module.vpc.private_subnets
}

output "public_subnet_ids" {
  description = "Public subnet IDs"
  value       = module.vpc.public_subnets
}

#######################
# EKS
#######################

output "cluster_id" {
  description = "EKS cluster ID"
  value       = module.eks.cluster_id
}

output "cluster_endpoint" {
  description = "EKS cluster endpoint"
  value       = module.eks.cluster_endpoint
}

output "cluster_security_group_id" {
  description = "Security group ID attached to the EKS cluster"
  value       = module.eks.cluster_security_group_id
}

output "cluster_oidc_issuer_url" {
  description = "The URL on the EKS cluster OIDC Issuer"
  value       = module.eks.cluster_oidc_issuer_url
}

output "cluster_certificate_authority_data" {
  description = "Base64 encoded certificate data required to communicate with the cluster"
  value       = module.eks.cluster_certificate_authority_data
  sensitive   = true
}

output "kubectl_config_command" {
  description = "Command to update kubeconfig"
  value       = "aws eks update-kubeconfig --region ${var.aws_region} --name ${module.eks.cluster_name}"
}

#######################
# Node Groups
#######################

output "node_security_group_id" {
  description = "Security group ID attached to the EKS nodes"
  value       = module.eks.node_security_group_id
}

output "eks_managed_node_groups" {
  description = "EKS managed node groups"
  value       = module.eks.eks_managed_node_groups
  sensitive   = true
}

#######################
# RDS
#######################

output "db_instance_endpoint" {
  description = "RDS instance endpoint"
  value       = module.rds.db_instance_endpoint
}

output "db_instance_address" {
  description = "RDS instance address"
  value       = module.rds.db_instance_address
}

output "db_instance_port" {
  description = "RDS instance port"
  value       = module.rds.db_instance_port
}

output "db_instance_name" {
  description = "RDS instance database name"
  value       = module.rds.db_instance_name
}

output "db_master_user_secret_arn" {
  description = "ARN of the secret storing the DB master password"
  value       = module.rds.db_instance_master_user_secret_arn
  sensitive   = true
}

output "database_url" {
  description = "PostgreSQL connection URL (without password)"
  value       = "postgresql://${var.db_username}@${module.rds.db_instance_address}:${module.rds.db_instance_port}/${module.rds.db_instance_name}"
  sensitive   = true
}

#######################
# ElastiCache Redis
#######################

output "redis_endpoint" {
  description = "ElastiCache Redis endpoint"
  value       = module.redis.primary_endpoint_address
}

output "redis_port" {
  description = "ElastiCache Redis port"
  value       = module.redis.port
}

output "redis_connection_string" {
  description = "Redis connection string"
  value       = "redis://${module.redis.primary_endpoint_address}:${module.redis.port}"
  sensitive   = true
}

#######################
# S3 Buckets
#######################

output "s3_models_bucket_id" {
  description = "S3 bucket ID for model artifacts"
  value       = module.s3_models.s3_bucket_id
}

output "s3_models_bucket_arn" {
  description = "S3 bucket ARN for model artifacts"
  value       = module.s3_models.s3_bucket_arn
}

output "s3_data_bucket_id" {
  description = "S3 bucket ID for data"
  value       = module.s3_data.s3_bucket_id
}

output "s3_data_bucket_arn" {
  description = "S3 bucket ARN for data"
  value       = module.s3_data.s3_bucket_arn
}

#######################
# IAM
#######################

output "mlops_app_role_arn" {
  description = "IAM role ARN for MLOps application"
  value       = module.mlops_app_irsa.iam_role_arn
}

output "ebs_csi_driver_role_arn" {
  description = "IAM role ARN for EBS CSI driver"
  value       = module.ebs_csi_driver_irsa.iam_role_arn
}

#######################
# CloudWatch
#######################

output "application_log_group_name" {
  description = "CloudWatch log group name for application logs"
  value       = aws_cloudwatch_log_group.application.name
}

output "cluster_log_group_name" {
  description = "CloudWatch log group name for cluster logs"
  value       = aws_cloudwatch_log_group.eks_cluster.name
}

#######################
# Setup Instructions
#######################

output "setup_instructions" {
  description = "Instructions to set up and access the cluster"
  value = <<-EOT
    
    # MLOps Deployment Setup Instructions
    
    ## 1. Configure kubectl
    ${module.eks.cluster_name != "" ? "aws eks update-kubeconfig --region ${var.aws_region} --name ${module.eks.cluster_name}" : ""}
    
    ## 2. Verify cluster access
    kubectl cluster-info
    kubectl get nodes
    
    ## 3. Retrieve database password from Secrets Manager
    aws secretsmanager get-secret-value \
      --secret-id ${module.rds.db_instance_master_user_secret_arn} \
      --region ${var.aws_region} \
      --query SecretString \
      --output text | jq -r .password
    
    ## 4. Create Kubernetes namespace
    kubectl create namespace mlops
    
    ## 5. Create Kubernetes secrets with database and Redis credentials
    # See terraform/aws/README.md for detailed instructions
    
    ## 6. Deploy application
    kubectl apply -f ../../k8s/
    
    ## 7. Verify deployment
    kubectl get pods -n mlops
    kubectl get svc -n mlops
    
    ## Infrastructure Details
    - Cluster: ${module.eks.cluster_name}
    - Region: ${var.aws_region}
    - VPC: ${module.vpc.vpc_id}
    - Database: ${module.rds.db_instance_address}
    - Redis: ${module.redis.primary_endpoint_address}
    - S3 Models: ${module.s3_models.s3_bucket_id}
    - S3 Data: ${module.s3_data.s3_bucket_id}
    
  EOT
}
