# Terraform outputs for GCP MLOps deployment

#######################
# Network
#######################

output "network_name" {
  description = "VPC network name"
  value       = google_compute_network.vpc.name
}

output "network_id" {
  description = "VPC network ID"
  value       = google_compute_network.vpc.id
}

output "subnet_name" {
  description = "Subnet name"
  value       = google_compute_subnetwork.subnet.name
}

output "subnet_cidr" {
  description = "Subnet CIDR range"
  value       = google_compute_subnetwork.subnet.ip_cidr_range
}

#######################
# GKE
#######################

output "cluster_name" {
  description = "GKE cluster name"
  value       = google_container_cluster.primary.name
}

output "cluster_endpoint" {
  description = "GKE cluster endpoint"
  value       = google_container_cluster.primary.endpoint
  sensitive   = true
}

output "cluster_ca_certificate" {
  description = "GKE cluster CA certificate"
  value       = google_container_cluster.primary.master_auth[0].cluster_ca_certificate
  sensitive   = true
}

output "cluster_location" {
  description = "GKE cluster location"
  value       = google_container_cluster.primary.location
}

output "kubectl_config_command" {
  description = "Command to configure kubectl"
  value       = "gcloud container clusters get-credentials ${google_container_cluster.primary.name} --region ${var.region} --project ${var.project_id}"
}

#######################
# Node Pools
#######################

output "node_pool_general" {
  description = "General purpose node pool details"
  value = {
    name       = google_container_node_pool.general.name
    node_count = google_container_node_pool.general.node_count
  }
}

output "node_pool_gpu" {
  description = "GPU node pool details"
  value = var.enable_gpu_nodes ? {
    name       = google_container_node_pool.gpu[0].name
    node_count = google_container_node_pool.gpu[0].node_count
  } : null
}

#######################
# Cloud SQL
#######################

output "db_instance_name" {
  description = "Cloud SQL instance name"
  value       = google_sql_database_instance.postgres.name
}

output "db_connection_name" {
  description = "Cloud SQL connection name"
  value       = google_sql_database_instance.postgres.connection_name
}

output "db_private_ip" {
  description = "Cloud SQL private IP address"
  value       = google_sql_database_instance.postgres.private_ip_address
  sensitive   = true
}

output "db_name" {
  description = "Database name"
  value       = google_sql_database.database.name
}

output "database_url" {
  description = "PostgreSQL connection URL"
  value       = "postgresql://${var.db_username}:${var.db_password}@${google_sql_database_instance.postgres.private_ip_address}:5432/${google_sql_database.database.name}"
  sensitive   = true
}

#######################
# Memorystore Redis
#######################

output "redis_host" {
  description = "Redis instance host"
  value       = google_redis_instance.cache.host
}

output "redis_port" {
  description = "Redis instance port"
  value       = google_redis_instance.cache.port
}

output "redis_connection_string" {
  description = "Redis connection string"
  value       = "redis://${google_redis_instance.cache.host}:${google_redis_instance.cache.port}"
  sensitive   = true
}

output "redis_auth_string" {
  description = "Redis AUTH string"
  value       = google_redis_instance.cache.auth_string
  sensitive   = true
}

#######################
# Cloud Storage
#######################

output "models_bucket_name" {
  description = "Cloud Storage bucket name for models"
  value       = google_storage_bucket.models.name
}

output "models_bucket_url" {
  description = "Cloud Storage bucket URL for models"
  value       = google_storage_bucket.models.url
}

output "data_bucket_name" {
  description = "Cloud Storage bucket name for data"
  value       = google_storage_bucket.data.name
}

output "data_bucket_url" {
  description = "Cloud Storage bucket URL for data"
  value       = google_storage_bucket.data.url
}

#######################
# IAM
#######################

output "mlops_app_service_account_email" {
  description = "MLOps application service account email"
  value       = google_service_account.mlops_app.email
}

output "mlops_app_service_account_id" {
  description = "MLOps application service account ID"
  value       = google_service_account.mlops_app.id
}

#######################
# Setup Instructions
#######################

output "setup_instructions" {
  description = "Instructions to set up and access the cluster"
  value = <<-EOT
    
    # MLOps Deployment Setup Instructions (GCP)
    
    ## 1. Configure gcloud
    gcloud config set project ${var.project_id}
    gcloud config set compute/region ${var.region}
    
    ## 2. Configure kubectl
    ${google_container_cluster.primary.name != "" ? "gcloud container clusters get-credentials ${google_container_cluster.primary.name} --region ${var.region} --project ${var.project_id}" : ""}
    
    ## 3. Verify cluster access
    kubectl cluster-info
    kubectl get nodes
    
    ## 4. Create Kubernetes namespace
    kubectl create namespace mlops
    
    ## 5. Configure Workload Identity
    # Annotate the Kubernetes service account to use Workload Identity
    kubectl create serviceaccount mlops-app -n mlops
    kubectl annotate serviceaccount mlops-app -n mlops \
      iam.gke.io/gcp-service-account=${google_service_account.mlops_app.email}
    
    ## 6. Create Kubernetes secrets
    # Database password
    kubectl create secret generic db-credentials -n mlops \
      --from-literal=password='${var.db_password}'
    
    # Redis auth string
    kubectl create secret generic redis-credentials -n mlops \
      --from-literal=auth-string='${google_redis_instance.cache.auth_string}'
    
    # See terraform/gcp/README.md for detailed instructions
    
    ## 7. Deploy application
    kubectl apply -f ../../k8s/
    
    ## 8. Verify deployment
    kubectl get pods -n mlops
    kubectl get svc -n mlops
    
    ## Infrastructure Details
    - Project: ${var.project_id}
    - Cluster: ${google_container_cluster.primary.name}
    - Region: ${var.region}
    - VPC: ${google_compute_network.vpc.name}
    - Database: ${google_sql_database_instance.postgres.connection_name}
    - Redis: ${google_redis_instance.cache.host}:${google_redis_instance.cache.port}
    - Storage Models: gs://${google_storage_bucket.models.name}
    - Storage Data: gs://${google_storage_bucket.data.name}
    
    ## Accessing Cloud SQL from GKE
    # Use Cloud SQL Proxy sidecar in your pod or connect via private IP
    # Private IP: ${google_sql_database_instance.postgres.private_ip_address}
    
  EOT
}
