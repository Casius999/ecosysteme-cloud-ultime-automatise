# Infrastructure as Code - Configuration principale
# Ce fichier définit l'infrastructure multi-cloud pour l'écosystème cloud automatisé

terraform {
  required_version = ">= 1.0.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.0"
    }
    google = {
      source  = "hashicorp/google"
      version = "~> 4.0"
    }
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }
  
  backend "s3" {
    # Les paramètres réels du backend seront fournis dans une configuration séparée
    # ou via des variables d'environnement pour assurer la sécurité des identifiants
  }
}

# Provider AWS
provider "aws" {
  region = var.aws_region
  # Les identifiants sont fournis via des variables d'environnement
  # AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY
}

# Provider Google Cloud
provider "google" {
  project = var.gcp_project_id
  region  = var.gcp_region
  # Les identifiants sont fournis via GOOGLE_APPLICATION_CREDENTIALS
}

# Provider Azure
provider "azurerm" {
  features {}
  # Les identifiants sont fournis via variables d'environnement
}

# Modules d'infrastructure
module "networking" {
  source = "./modules/networking"
  
  # Variables passées au module
  aws_region = var.aws_region
  gcp_region = var.gcp_region
  azure_location = var.azure_location
}

module "kubernetes" {
  source = "./modules/kubernetes"
  
  # Dépendance sur le module de réseau
  depends_on = [module.networking]
  
  # Variables passées au module
  aws_region = var.aws_region
  gcp_region = var.gcp_region
  azure_location = var.azure_location
}

module "monitoring" {
  source = "./modules/monitoring"
  
  # Dépendance sur le module Kubernetes
  depends_on = [module.kubernetes]
}