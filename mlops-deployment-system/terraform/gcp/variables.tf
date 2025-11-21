# Terraform variables for GCP MLOps deployment

#######################
# General
#######################

variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "mlops-deployment"
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
  
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}

variable "region" {
  description = "GCP region"
  type        = string
  default     = "us-central1"
}

variable "node_zones" {
  description = "Zones for GKE nodes"
  type        = list(string)
  default     = ["us-central1-a", "us-central1-b", "us-central1-c"]
}

#######################
# Network
#######################

variable "subnet_cidr" {
  description = "CIDR block for primary subnet"
  type        = string
  default     = "10.0.0.0/20"
}

variable "pods_cidr" {
  description = "CIDR block for GKE pods"
  type        = string
  default     = "10.1.0.0/16"
}

variable "services_cidr" {
  description = "CIDR block for GKE services"
  type        = string
  default     = "10.2.0.0/20"
}

#######################
# GKE
#######################

variable "release_channel" {
  description = "GKE release channel (RAPID, REGULAR, STABLE)"
  type        = string
  default     = "REGULAR"
  
  validation {
    condition     = contains(["RAPID", "REGULAR", "STABLE"], var.release_channel)
    error_message = "Release channel must be RAPID, REGULAR, or STABLE."
  }
}

variable "node_machine_type" {
  description = "Machine type for GKE nodes"
  type        = string
  default     = "n1-standard-4"
}

variable "node_count_per_zone" {
  description = "Initial number of nodes per zone"
  type        = number
  default     = 1
}

variable "min_node_count" {
  description = "Minimum number of nodes per zone"
  type        = number
  default     = 1
}

variable "max_node_count" {
  description = "Maximum number of nodes per zone"
  type        = number
  default     = 5
}

#######################
# GPU Nodes
#######################

variable "enable_gpu_nodes" {
  description = "Enable GPU node pool"
  type        = bool
  default     = false
}

variable "gpu_machine_type" {
  description = "Machine type for GPU nodes"
  type        = string
  default     = "n1-standard-4"
}

#######################
# Cloud SQL
#######################

variable "db_tier" {
  description = "Cloud SQL instance tier"
  type        = string
  default     = "db-custom-2-7680"  # 2 vCPUs, 7.5 GB RAM
}

variable "db_disk_size" {
  description = "Database disk size in GB"
  type        = number
  default     = 50
}

variable "db_name" {
  description = "Database name"
  type        = string
  default     = "mlops"
}

variable "db_username" {
  description = "Database username"
  type        = string
  default     = "mlops_admin"
  sensitive   = true
}

variable "db_password" {
  description = "Database password"
  type        = string
  sensitive   = true
}

#######################
# Memorystore Redis
#######################

variable "redis_memory_size" {
  description = "Redis instance memory size in GB"
  type        = number
  default     = 5
}

#######################
# Monitoring
#######################

variable "enable_cloud_monitoring" {
  description = "Enable Cloud Monitoring and Logging"
  type        = bool
  default     = true
}

#######################
# Tags
#######################

variable "additional_labels" {
  description = "Additional labels to apply to resources"
  type        = map(string)
  default     = {}
}
