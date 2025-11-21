# MLOps Infrastructure as Code (Terraform)

Complete Terraform configurations for deploying the MLOps system to AWS and GCP with production-grade infrastructure.

## 📁 Directory Structure

```
terraform/
├── aws/                    # AWS deployment (EKS, RDS, ElastiCache, S3)
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   ├── terraform.tfvars.example
│   └── README.md
├── gcp/                    # GCP deployment (GKE, Cloud SQL, Memorystore, GCS)
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   ├── terraform.tfvars.example
│   └── README.md
└── README.md               # This file
```

## 🎯 Features

### AWS Infrastructure
- **EKS Cluster**: Multi-AZ Kubernetes cluster with managed node groups
- **RDS PostgreSQL**: Managed database with automated backups and encryption
- **ElastiCache Redis**: In-memory caching with cluster mode
- **S3 Buckets**: Model artifacts and data storage with lifecycle policies
- **IAM Roles**: IRSA (IAM Roles for Service Accounts) for secure pod access
- **VPC**: Custom VPC with public/private subnets across 3 AZs
- **CloudWatch**: Logging and monitoring integration

### GCP Infrastructure
- **GKE Cluster**: Regional Kubernetes cluster with autoscaling
- **Cloud SQL**: High-availability PostgreSQL with automated backups
- **Memorystore**: Managed Redis with persistence
- **Cloud Storage**: Buckets for models and data with versioning
- **Workload Identity**: Secure service account binding
- **VPC**: Custom VPC with Cloud NAT
- **Cloud Monitoring**: Integrated logging and metrics

## 🚀 Quick Start

### Prerequisites

1. **Install Terraform** (>= 1.5.0)
   ```bash
   # macOS
   brew install terraform
   
   # Linux
   wget https://releases.hashicorp.com/terraform/1.6.0/terraform_1.6.0_linux_amd64.zip
   unzip terraform_1.6.0_linux_amd64.zip
   sudo mv terraform /usr/local/bin/
   ```

2. **Cloud Provider CLI**
   
   **AWS:**
   ```bash
   # Install AWS CLI
   pip install awscli
   
   # Configure credentials
   aws configure
   ```
   
   **GCP:**
   ```bash
   # Install gcloud CLI
   curl https://sdk.cloud.google.com | bash
   
   # Authenticate
   gcloud auth application-default login
   gcloud config set project YOUR_PROJECT_ID
   ```

3. **kubectl**
   ```bash
   # macOS
   brew install kubectl
   
   # Linux
   curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
   chmod +x kubectl
   sudo mv kubectl /usr/local/bin/
   ```

### AWS Deployment

```bash
cd aws/

# Copy and customize variables
cp terraform.tfvars.example terraform.tfvars
vim terraform.tfvars

# Initialize Terraform
terraform init

# Preview changes
terraform plan

# Deploy infrastructure
terraform apply

# Get outputs
terraform output

# Configure kubectl
aws eks update-kubeconfig --region us-east-1 --name mlops-deployment-prod
```

### GCP Deployment

```bash
cd gcp/

# Copy and customize variables
cp terraform.tfvars.example terraform.tfvars
vim terraform.tfvars

# Initialize Terraform
terraform init

# Preview changes
terraform plan

# Deploy infrastructure
terraform apply

# Get outputs
terraform output

# Configure kubectl
gcloud container clusters get-credentials mlops-deployment-prod --region us-central1
```

## 🔒 Security Best Practices

### Secret Management

**DO NOT** commit sensitive values to git. Use one of these approaches:

1. **Environment Variables**
   ```bash
   export TF_VAR_db_password="your_password"
   terraform apply
   ```

2. **AWS Secrets Manager / GCP Secret Manager**
   - Store secrets in cloud provider's secret management service
   - Reference them using data sources in Terraform

3. **HashiCorp Vault**
   - Centralized secret management
   - Dynamic credentials

4. **terraform.tfvars (gitignored)**
   ```hcl
   # terraform.tfvars (NEVER commit this file)
   db_password     = "actual_password"
   db_username     = "admin"
   owner_email     = "you@example.com"
   ```

### State Management

**Remote State** is configured by default:

**AWS:** S3 backend with DynamoDB locking
```hcl
backend "s3" {
  bucket         = "mlops-terraform-state"
  key            = "mlops/terraform.tfstate"
  region         = "us-east-1"
  encrypt        = true
  dynamodb_table = "terraform-lock"
}
```

**GCP:** GCS backend
```hcl
backend "gcs" {
  bucket = "mlops-terraform-state"
  prefix = "mlops/state"
}
```

**Setup Remote State:**

**AWS:**
```bash
# Create S3 bucket for state
aws s3 mb s3://mlops-terraform-state --region us-east-1
aws s3api put-bucket-versioning --bucket mlops-terraform-state \
  --versioning-configuration Status=Enabled

# Create DynamoDB table for locking
aws dynamodb create-table \
  --table-name terraform-lock \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5
```

**GCP:**
```bash
# Create GCS bucket for state
gsutil mb gs://mlops-terraform-state
gsutil versioning set on gs://mlops-terraform-state
```

## 📊 Cost Estimation

### Development Environment
- **AWS**: ~$150-300/month
  - EKS: $72/month (cluster fee)
  - EC2: $50-100/month (2-3 t3.large nodes)
  - RDS: $30-50/month (db.t3.medium)
  - Other: $20/month

- **GCP**: ~$120-250/month
  - GKE: $72/month (cluster fee)
  - Compute: $40-80/month (2-3 n1-standard-4 nodes)
  - Cloud SQL: $30-40/month
  - Other: $20/month

### Production Environment
- **AWS**: ~$500-1500/month
- **GCP**: ~$450-1400/month

See [../../docs/COSTS.md](../../docs/COSTS.md) for detailed breakdown.

## 🔧 Customization

### Scaling Configuration

Edit `variables.tf` or `terraform.tfvars`:

```hcl
# AWS
node_group_min_size     = 3
node_group_max_size     = 20
node_group_desired_size = 5
db_instance_class       = "db.r5.xlarge"

# GCP
min_node_count    = 2
max_node_count    = 15
node_count_per_zone = 2
db_tier          = "db-custom-4-15360"
```

### Multi-Environment Setup

Create separate tfvars files:

```bash
# Development
terraform apply -var-file="dev.tfvars"

# Staging
terraform apply -var-file="staging.tfvars"

# Production
terraform apply -var-file="prod.tfvars"
```

## 🧪 Testing

```bash
# Validate configuration
terraform validate

# Format code
terraform fmt -recursive

# Security scan
tfsec .
checkov -d .

# Cost estimation
infracost breakdown --path .
```

## 📚 Post-Deployment

After successful deployment:

1. **Configure Kubernetes Secrets**
   ```bash
   kubectl create namespace mlops
   kubectl create secret generic mlops-secrets -n mlops \
     --from-literal=WANDB_API_KEY=your_key \
     --from-literal=SLACK_WEBHOOK=your_webhook
   ```

2. **Deploy Application**
   ```bash
   kubectl apply -f ../k8s/
   ```

3. **Verify Deployment**
   ```bash
   kubectl get pods -n mlops
   kubectl get svc -n mlops
   kubectl logs -f deployment/qna-v1 -n mlops
   ```

4. **Access Application**
   ```bash
   # Get load balancer URL
   kubectl get ingress -n mlops
   
   # Port forward for local testing
   kubectl port-forward svc/qna-svc 8080:80 -n mlops
   curl http://localhost:8080/health
   ```

## 🔄 Updates and Maintenance

### Updating Infrastructure

```bash
# Pull latest changes
git pull

# Review changes
terraform plan

# Apply updates
terraform apply

# Rolling update for nodes
terraform apply -target=module.eks.eks_managed_node_groups
```

### Backup and Disaster Recovery

**AWS:**
- RDS automated backups (30 days retention in prod)
- S3 versioning enabled
- EBS snapshots via AWS Backup

**GCP:**
- Cloud SQL automated backups (30 days retention in prod)
- Cloud Storage versioning enabled
- Persistent disk snapshots

### Monitoring

Access monitoring dashboards:

**AWS:**
- CloudWatch: `https://console.aws.amazon.com/cloudwatch`
- Container Insights

**GCP:**
- Cloud Console: `https://console.cloud.google.com/monitoring`
- GKE Dashboard

## 🗑️ Cleanup

**⚠️ WARNING:** This will destroy all infrastructure and data!

```bash
# Destroy infrastructure
terraform destroy

# Confirm by typing 'yes'

# Clean up state
rm -rf .terraform terraform.tfstate*
```

## 📖 Additional Resources

- [AWS EKS Best Practices](https://aws.github.io/aws-eks-best-practices/)
- [GKE Best Practices](https://cloud.google.com/kubernetes-engine/docs/best-practices)
- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [Terraform GCP Provider](https://registry.terraform.io/providers/hashicorp/google/latest/docs)
- [Kubernetes Documentation](https://kubernetes.io/docs/)

## 🆘 Troubleshooting

### Common Issues

1. **Insufficient Permissions**
   ```bash
   # AWS: Ensure IAM user has necessary permissions
   aws iam get-user
   
   # GCP: Enable required APIs
   gcloud services enable container.googleapis.com
   gcloud services enable compute.googleapis.com
   ```

2. **State Lock Error**
   ```bash
   # AWS: Force unlock
   terraform force-unlock LOCK_ID
   
   # Manually delete lock from DynamoDB if needed
   ```

3. **Quota Limits**
   - AWS: Request quota increases via AWS Support
   - GCP: Request quota increases via Cloud Console

## 📞 Support

For issues or questions:
- GitHub Issues: [Portfolio Issues](https://github.com/youruser/Portfolio/issues)
- Documentation: [Main README](../../README.md)
- Architecture: [ARCHITECTURE.md](../../docs/ARCHITECTURE.md)
