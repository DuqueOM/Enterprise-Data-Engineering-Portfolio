# Terraform configuration for MLOps deployment on GCP
# Creates GKE cluster, Cloud SQL, Memorystore, Cloud Storage, and supporting infrastructure

terraform {
  required_version = ">= 1.5.0"
  
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
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
  backend "gcs" {
    bucket = "mlops-terraform-state"
    prefix = "mlops/state"
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

provider "google-beta" {
  project = var.project_id
  region  = var.region
}

# Local variables
locals {
  cluster_name = "${var.project_name}-${var.environment}"
  
  common_labels = {
    project     = var.project_name
    environment = var.environment
    managed-by  = "terraform"
  }
}

#######################
# VPC Network
#######################

resource "google_compute_network" "vpc" {
  name                    = "${local.cluster_name}-vpc"
  auto_create_subnetworks = false
  routing_mode            = "REGIONAL"
  
  project = var.project_id
}

resource "google_compute_subnetwork" "subnet" {
  name          = "${local.cluster_name}-subnet"
  ip_cidr_range = var.subnet_cidr
  region        = var.region
  network       = google_compute_network.vpc.id
  
  # Secondary IP ranges for GKE pods and services
  secondary_ip_range {
    range_name    = "pods"
    ip_cidr_range = var.pods_cidr
  }
  
  secondary_ip_range {
    range_name    = "services"
    ip_cidr_range = var.services_cidr
  }
  
  private_ip_google_access = true
  
  project = var.project_id
}

#######################
# Cloud NAT
#######################

resource "google_compute_router" "router" {
  name    = "${local.cluster_name}-router"
  region  = var.region
  network = google_compute_network.vpc.id
  
  project = var.project_id
}

resource "google_compute_router_nat" "nat" {
  name   = "${local.cluster_name}-nat"
  router = google_compute_router.router.name
  region = var.region
  
  nat_ip_allocate_option             = "AUTO_ONLY"
  source_subnetwork_ip_ranges_to_nat = "ALL_SUBNETWORKS_ALL_IP_RANGES"
  
  log_config {
    enable = true
    filter = "ERRORS_ONLY"
  }
  
  project = var.project_id
}

#######################
# GKE Cluster
#######################

resource "google_container_cluster" "primary" {
  name     = local.cluster_name
  location = var.region
  
  # Regional cluster for high availability
  node_locations = var.node_zones
  
  # We can't create a cluster with no node pool, so we create the smallest possible default
  # node pool and immediately delete it.
  remove_default_node_pool = true
  initial_node_count       = 1
  
  network    = google_compute_network.vpc.name
  subnetwork = google_compute_subnetwork.subnet.name
  
  # IP allocation for pods and services
  ip_allocation_policy {
    cluster_secondary_range_name  = "pods"
    services_secondary_range_name = "services"
  }
  
  # Workload Identity
  workload_identity_config {
    workload_pool = "${var.project_id}.svc.id.goog"
  }
  
  # Network policy
  network_policy {
    enabled  = true
    provider = "CALICO"
  }
  
  # Addons
  addons_config {
    http_load_balancing {
      disabled = false
    }
    
    horizontal_pod_autoscaling {
      disabled = false
    }
    
    network_policy_config {
      disabled = false
    }
    
    gcp_filestore_csi_driver_config {
      enabled = true
    }
  }
  
  # Maintenance window
  maintenance_policy {
    daily_maintenance_window {
      start_time = "03:00"
    }
  }
  
  # Binary authorization for security
  binary_authorization {
    evaluation_mode = var.environment == "prod" ? "PROJECT_SINGLETON_POLICY_ENFORCE" : "DISABLED"
  }
  
  # Master authorized networks (restrict access)
  master_authorized_networks_config {
    cidr_blocks {
      cidr_block   = "0.0.0.0/0"  # Change to specific IPs in production
      display_name = "All"
    }
  }
  
  # Release channel
  release_channel {
    channel = var.release_channel
  }
  
  # Logging and monitoring
  logging_config {
    enable_components = ["SYSTEM_COMPONENTS", "WORKLOADS"]
  }
  
  monitoring_config {
    enable_components = ["SYSTEM_COMPONENTS"]
    
    managed_prometheus {
      enabled = true
    }
  }
  
  # Resource labels
  resource_labels = local.common_labels
  
  project = var.project_id
}

#######################
# Node Pools
#######################

# General purpose node pool
resource "google_container_node_pool" "general" {
  name       = "${local.cluster_name}-general"
  location   = var.region
  cluster    = google_container_cluster.primary.name
  node_count = var.node_count_per_zone
  
  autoscaling {
    min_node_count = var.min_node_count
    max_node_count = var.max_node_count
  }
  
  management {
    auto_repair  = true
    auto_upgrade = true
  }
  
  node_config {
    machine_type = var.node_machine_type
    disk_size_gb = 50
    disk_type    = "pd-standard"
    
    # OAuth scopes
    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform"
    ]
    
    # Workload Identity
    workload_metadata_config {
      mode = "GKE_METADATA"
    }
    
    # Labels
    labels = merge(
      local.common_labels,
      {
        role = "general"
      }
    )
    
    # Tags for firewall rules
    tags = ["gke-node", "${local.cluster_name}-node"]
    
    # Metadata
    metadata = {
      disable-legacy-endpoints = "true"
    }
    
    # Shielded instance config
    shielded_instance_config {
      enable_secure_boot          = true
      enable_integrity_monitoring = true
    }
  }
  
  project = var.project_id
}

# GPU node pool for ML inference
resource "google_container_node_pool" "gpu" {
  count = var.enable_gpu_nodes ? 1 : 0
  
  name       = "${local.cluster_name}-gpu"
  location   = var.region
  cluster    = google_container_cluster.primary.name
  node_count = 0
  
  autoscaling {
    min_node_count = 0
    max_node_count = 3
  }
  
  management {
    auto_repair  = true
    auto_upgrade = true
  }
  
  node_config {
    machine_type = var.gpu_machine_type
    disk_size_gb = 100
    disk_type    = "pd-ssd"
    
    # GPU configuration
    guest_accelerator {
      type  = "nvidia-tesla-t4"
      count = 1
      
      gpu_driver_installation_config {
        gpu_driver_version = "DEFAULT"
      }
    }
    
    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform"
    ]
    
    workload_metadata_config {
      mode = "GKE_METADATA"
    }
    
    labels = merge(
      local.common_labels,
      {
        role     = "ml-inference"
        gpu      = "true"
        workload = "ml"
      }
    )
    
    tags = ["gke-node", "${local.cluster_name}-gpu-node"]
    
    metadata = {
      disable-legacy-endpoints = "true"
    }
    
    # Taints for GPU nodes
    taint {
      key    = "nvidia.com/gpu"
      value  = "true"
      effect = "NO_SCHEDULE"
    }
    
    shielded_instance_config {
      enable_secure_boot          = true
      enable_integrity_monitoring = true
    }
  }
  
  project = var.project_id
}

#######################
# Cloud SQL (PostgreSQL)
#######################

resource "google_sql_database_instance" "postgres" {
  name             = "${local.cluster_name}-db"
  database_version = "POSTGRES_15"
  region           = var.region
  
  settings {
    tier              = var.db_tier
    availability_type = var.environment == "prod" ? "REGIONAL" : "ZONAL"
    disk_size         = var.db_disk_size
    disk_autoresize   = true
    disk_type         = "PD_SSD"
    
    # Backup configuration
    backup_configuration {
      enabled                        = true
      start_time                     = "03:00"
      point_in_time_recovery_enabled = var.environment == "prod"
      
      backup_retention_settings {
        retained_backups = var.environment == "prod" ? 30 : 7
      }
    }
    
    # IP configuration
    ip_configuration {
      ipv4_enabled    = false
      private_network = google_compute_network.vpc.id
      require_ssl     = true
    }
    
    # Maintenance window
    maintenance_window {
      day          = 7  # Sunday
      hour         = 3
      update_track = "stable"
    }
    
    # Insights config
    insights_config {
      query_insights_enabled  = true
      query_string_length     = 1024
      record_application_tags = true
      record_client_address   = true
    }
    
    # Database flags
    database_flags {
      name  = "max_connections"
      value = "100"
    }
    
    database_flags {
      name  = "log_checkpoints"
      value = "on"
    }
    
    user_labels = local.common_labels
  }
  
  deletion_protection = var.environment == "prod"
  
  project = var.project_id
  
  depends_on = [google_service_networking_connection.private_vpc_connection]
}

# Private VPC connection for Cloud SQL
resource "google_compute_global_address" "private_ip_address" {
  name          = "${local.cluster_name}-private-ip"
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 16
  network       = google_compute_network.vpc.id
  
  project = var.project_id
}

resource "google_service_networking_connection" "private_vpc_connection" {
  network                 = google_compute_network.vpc.id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.private_ip_address.name]
}

# Database
resource "google_sql_database" "database" {
  name     = var.db_name
  instance = google_sql_database_instance.postgres.name
  
  project = var.project_id
}

# Database user
resource "google_sql_user" "user" {
  name     = var.db_username
  instance = google_sql_database_instance.postgres.name
  password = var.db_password  # Use Secrets Manager in production
  
  project = var.project_id
}

#######################
# Memorystore Redis
#######################

resource "google_redis_instance" "cache" {
  name           = "${local.cluster_name}-redis"
  tier           = var.environment == "prod" ? "STANDARD_HA" : "BASIC"
  memory_size_gb = var.redis_memory_size
  region         = var.region
  
  authorized_network = google_compute_network.vpc.id
  connect_mode       = "PRIVATE_SERVICE_ACCESS"
  
  redis_version = "REDIS_7_0"
  
  # Maintenance policy
  maintenance_policy {
    weekly_maintenance_window {
      day = "SUNDAY"
      start_time {
        hours   = 3
        minutes = 0
      }
    }
  }
  
  # Auth
  auth_enabled = true
  
  # Persistence (for Standard tier)
  dynamic "persistence_config" {
    for_each = var.environment == "prod" ? [1] : []
    content {
      persistence_mode    = "RDB"
      rdb_snapshot_period = "TWELVE_HOURS"
    }
  }
  
  labels = local.common_labels
  
  project = var.project_id
  
  depends_on = [google_service_networking_connection.private_vpc_connection]
}

#######################
# Cloud Storage
#######################

# Model artifacts bucket
resource "google_storage_bucket" "models" {
  name          = "${var.project_id}-${local.cluster_name}-models"
  location      = var.region
  storage_class = "STANDARD"
  
  uniform_bucket_level_access = true
  
  versioning {
    enabled = true
  }
  
  lifecycle_rule {
    condition {
      num_newer_versions = 3
      age                = 90
    }
    action {
      type          = "SetStorageClass"
      storage_class = "NEARLINE"
    }
  }
  
  lifecycle_rule {
    condition {
      age = 365
    }
    action {
      type = "Delete"
    }
  }
  
  labels = local.common_labels
  
  project = var.project_id
}

# Data bucket
resource "google_storage_bucket" "data" {
  name          = "${var.project_id}-${local.cluster_name}-data"
  location      = var.region
  storage_class = "STANDARD"
  
  uniform_bucket_level_access = true
  
  lifecycle_rule {
    condition {
      age = 90
    }
    action {
      type = "Delete"
    }
  }
  
  labels = local.common_labels
  
  project = var.project_id
}

#######################
# IAM for Workload Identity
#######################

# Service account for MLOps application
resource "google_service_account" "mlops_app" {
  account_id   = "${local.cluster_name}-app"
  display_name = "MLOps Application Service Account"
  description  = "Service account for MLOps application with Workload Identity"
  
  project = var.project_id
}

# Bind Kubernetes SA to GCP SA
resource "google_service_account_iam_member" "mlops_app_workload_identity" {
  service_account_id = google_service_account.mlops_app.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "serviceAccount:${var.project_id}.svc.id.goog[mlops/mlops-app]"
}

# Grant permissions to service account
resource "google_project_iam_member" "mlops_app_storage" {
  project = var.project_id
  role    = "roles/storage.objectAdmin"
  member  = "serviceAccount:${google_service_account.mlops_app.email}"
}

resource "google_project_iam_member" "mlops_app_sql" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.mlops_app.email}"
}

resource "google_project_iam_member" "mlops_app_monitoring" {
  project = var.project_id
  role    = "roles/monitoring.metricWriter"
  member  = "serviceAccount:${google_service_account.mlops_app.email}"
}

#######################
# Firewall Rules
#######################

# Allow internal communication
resource "google_compute_firewall" "allow_internal" {
  name    = "${local.cluster_name}-allow-internal"
  network = google_compute_network.vpc.name
  
  allow {
    protocol = "tcp"
    ports    = ["0-65535"]
  }
  
  allow {
    protocol = "udp"
    ports    = ["0-65535"]
  }
  
  allow {
    protocol = "icmp"
  }
  
  source_ranges = [var.subnet_cidr, var.pods_cidr, var.services_cidr]
  
  project = var.project_id
}
