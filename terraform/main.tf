# Infrastructure as Code (IaC) - Provisionnement Multi-Cloud et Multi-Région
# Configuration Terraform pour un déploiement multi-cloud et multi-région

# Configuration du provider Google Cloud
provider "google" {
  project = var.gcp_project_id
  region  = var.gcp_primary_region
}

# Configuration du provider AWS
provider "aws" {
  region     = var.aws_primary_region
  access_key = var.aws_access_key
  secret_key = var.aws_secret_key
}

# Configuration du provider Azure
provider "azurerm" {
  features {}
  subscription_id = var.azure_subscription_id
  tenant_id       = var.azure_tenant_id
  client_id       = var.azure_client_id
  client_secret   = var.azure_client_secret
}

# Module VPC pour Google Cloud
module "gcp_vpc" {
  source = "./modules/gcp/vpc"
  
  vpc_name          = "ultimate-vpc-gcp"
  subnets           = var.gcp_subnets
  auto_create_subnetworks = false
}

# Module VPC pour AWS
module "aws_vpc" {
  source = "./modules/aws/vpc"
  
  vpc_name = "ultimate-vpc-aws"
  cidr_block = var.aws_vpc_cidr
  subnets    = var.aws_subnets
}

# Module VNET pour Azure
module "azure_vnet" {
  source = "./modules/azure/vnet"
  
  resource_group_name = "ultimate-resource-group"
  vnet_name           = "ultimate-vnet-azure"
  vnet_cidr           = var.azure_vnet_cidr
  subnets             = var.azure_subnets
}

# Module GKE (Google Kubernetes Engine)
module "gke_cluster" {
  source = "./modules/gcp/gke"
  
  cluster_name     = "ultimate-cluster-gcp"
  location         = var.gcp_primary_region
  node_count       = var.gke_initial_node_count
  machine_type     = var.gke_machine_type
  preemptible      = true
  network          = module.gcp_vpc.vpc_id
  subnetwork       = module.gcp_vpc.subnet_ids[0]
  min_node_count   = var.gke_min_node_count
  max_node_count   = var.gke_max_node_count
}

# Module EKS (Elastic Kubernetes Service)
module "eks_cluster" {
  source = "./modules/aws/eks"
  
  cluster_name    = "ultimate-cluster-aws"
  vpc_id          = module.aws_vpc.vpc_id
  subnets         = module.aws_vpc.subnet_ids
  instance_type   = var.eks_instance_type
  desired_capacity = var.eks_desired_capacity
  min_size        = var.eks_min_size
  max_size        = var.eks_max_size
}

# Module AKS (Azure Kubernetes Service)
module "aks_cluster" {
  source = "./modules/azure/aks"
  
  cluster_name        = "ultimate-cluster-azure"
  location            = var.azure_location
  resource_group_name = module.azure_vnet.resource_group_name
  vnet_id             = module.azure_vnet.vnet_id
  subnet_id           = module.azure_vnet.subnet_ids[0]
  node_count          = var.aks_node_count
  vm_size             = var.aks_vm_size
  min_count           = var.aks_min_count
  max_count           = var.aks_max_count
}

# Instances pour Runners CI/CD sur Google Cloud
resource "google_compute_instance" "gcp_runner" {
  count        = var.runner_count
  name         = "runner-gcp-${count.index}"
  machine_type = var.runner_machine_type
  zone         = "${var.gcp_primary_region}-a"

  boot_disk {
    initialize_params {
      image = "debian-cloud/debian-11"
      size  = 100
    }
  }

  network_interface {
    network    = module.gcp_vpc.vpc_id
    subnetwork = module.gcp_vpc.subnet_ids[0]
    access_config {}
  }
  
  metadata_startup_script = file("${path.module}/scripts/setup_runner.sh")
  
  service_account {
    scopes = ["cloud-platform"]
  }
  
  tags = ["runner", "ci-cd"]
}

# Instances pour Runners CI/CD sur AWS
resource "aws_instance" "aws_runner" {
  count         = var.runner_count
  ami           = var.aws_runner_ami
  instance_type = var.runner_instance_type
  subnet_id     = module.aws_vpc.subnet_ids[0]
  
  root_block_device {
    volume_size = 100
  }

  user_data = file("${path.module}/scripts/setup_runner.sh")
  
  tags = {
    Name = "runner-aws-${count.index}"
  }
}

# Bastion Host pour accès sécurisé
resource "google_compute_instance" "bastion" {
  name         = "bastion-host"
  machine_type = "e2-micro"
  zone         = "${var.gcp_primary_region}-a"

  boot_disk {
    initialize_params {
      image = "debian-cloud/debian-11"
    }
  }

  network_interface {
    network    = module.gcp_vpc.vpc_id
    subnetwork = module.gcp_vpc.subnet_ids[0]
    access_config {}
  }
  
  tags = ["bastion"]
}

# Outputs
output "gke_cluster_endpoint" {
  value = module.gke_cluster.endpoint
}

output "eks_cluster_endpoint" {
  value = module.eks_cluster.endpoint
}

output "aks_cluster_endpoint" {
  value = module.aks_cluster.endpoint
}

output "bastion_ip" {
  value = google_compute_instance.bastion.network_interface[0].access_config[0].nat_ip
}

output "runner_ips" {
  value = {
    gcp = google_compute_instance.gcp_runner.*.network_interface.0.access_config.0.nat_ip
    aws = aws_instance.aws_runner.*.public_ip
  }
}
