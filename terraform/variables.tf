# Variables pour le déploiement multi-cloud

# Variables générales
variable "environment" {
  description = "Environnement de déploiement (dev, staging, prod)"
  type        = string
  default     = "prod"
}

# Variables Google Cloud
variable "gcp_project_id" {
  description = "ID du projet Google Cloud"
  type        = string
}

variable "gcp_primary_region" {
  description = "Région principale pour GCP"
  type        = string
  default     = "europe-west1"
}

variable "gcp_secondary_region" {
  description = "Région secondaire pour GCP (haute disponibilité)"
  type        = string
  default     = "europe-west4"
}

variable "gcp_subnets" {
  description = "Liste des sous-réseaux à créer dans GCP"
  type = list(object({
    name          = string
    ip_cidr_range = string
    region        = string
  }))
  default = [
    {
      name          = "subnet-region1"
      ip_cidr_range = "10.0.1.0/24"
      region        = "europe-west1"
    },
    {
      name          = "subnet-region2"
      ip_cidr_range = "10.0.2.0/24"
      region        = "europe-west4"
    }
  ]
}

# Variables AWS
variable "aws_access_key" {
  description = "Clé d'accès AWS"
  type        = string
  sensitive   = true
}

variable "aws_secret_key" {
  description = "Clé secrète AWS"
  type        = string
  sensitive   = true
}

variable "aws_primary_region" {
  description = "Région principale pour AWS"
  type        = string
  default     = "eu-west-1"
}

variable "aws_secondary_region" {
  description = "Région secondaire pour AWS (haute disponibilité)"
  type        = string
  default     = "eu-central-1"
}

variable "aws_vpc_cidr" {
  description = "CIDR block pour le VPC AWS"
  type        = string
  default     = "10.1.0.0/16"
}

variable "aws_subnets" {
  description = "Liste des sous-réseaux à créer dans AWS"
  type = list(object({
    name          = string
    cidr_block    = string
    az            = string
    public        = bool
  }))
  default = [
    {
      name       = "subnet-public-1"
      cidr_block = "10.1.1.0/24"
      az         = "eu-west-1a"
      public     = true
    },
    {
      name       = "subnet-private-1"
      cidr_block = "10.1.2.0/24"
      az         = "eu-west-1b"
      public     = false
    }
  ]
}

variable "aws_runner_ami" {
  description = "AMI pour les runners AWS"
  type        = string
  default     = "ami-0c55b159cbfafe1f0" # Exemple d'AMI Ubuntu
}

# Variables Azure
variable "azure_subscription_id" {
  description = "ID de souscription Azure"
  type        = string
  sensitive   = true
}

variable "azure_tenant_id" {
  description = "ID de tenant Azure"
  type        = string
  sensitive   = true
}

variable "azure_client_id" {
  description = "ID client Azure"
  type        = string
  sensitive   = true
}

variable "azure_client_secret" {
  description = "Secret client Azure"
  type        = string
  sensitive   = true
}

variable "azure_location" {
  description = "Localisation Azure principale"
  type        = string
  default     = "West Europe"
}

variable "azure_vnet_cidr" {
  description = "CIDR block pour le VNET Azure"
  type        = string
  default     = "10.2.0.0/16"
}

variable "azure_subnets" {
  description = "Liste des sous-réseaux à créer dans Azure"
  type = list(object({
    name           = string
    address_prefix = string
  }))
  default = [
    {
      name           = "subnet-1"
      address_prefix = "10.2.1.0/24"
    },
    {
      name           = "subnet-2"
      address_prefix = "10.2.2.0/24"
    }
  ]
}

# Variables pour GKE
variable "gke_initial_node_count" {
  description = "Nombre initial de nœuds pour le cluster GKE"
  type        = number
  default     = 3
}

variable "gke_machine_type" {
  description = "Type de machine pour les nœuds GKE"
  type        = string
  default     = "e2-medium"
}

variable "gke_min_node_count" {
  description = "Nombre minimum de nœuds pour l'autoscaling GKE"
  type        = number
  default     = 1
}

variable "gke_max_node_count" {
  description = "Nombre maximum de nœuds pour l'autoscaling GKE"
  type        = number
  default     = 5
}

# Variables pour EKS
variable "eks_instance_type" {
  description = "Type d'instance pour les nœuds EKS"
  type        = string
  default     = "t3.medium"
}

variable "eks_desired_capacity" {
  description = "Nombre désiré de nœuds pour le cluster EKS"
  type        = number
  default     = 2
}

variable "eks_min_size" {
  description = "Taille minimale du groupe d'autoscaling EKS"
  type        = number
  default     = 1
}

variable "eks_max_size" {
  description = "Taille maximale du groupe d'autoscaling EKS"
  type        = number
  default     = 5
}

# Variables pour AKS
variable "aks_node_count" {
  description = "Nombre initial de nœuds pour le cluster AKS"
  type        = number
  default     = 2
}

variable "aks_vm_size" {
  description = "Taille de VM pour les nœuds AKS"
  type        = string
  default     = "Standard_DS2_v2"
}

variable "aks_min_count" {
  description = "Nombre minimum de nœuds pour l'autoscaling AKS"
  type        = number
  default     = 1
}

variable "aks_max_count" {
  description = "Nombre maximum de nœuds pour l'autoscaling AKS"
  type        = number
  default     = 5
}

# Variables pour les Runners CI/CD
variable "runner_count" {
  description = "Nombre de runners CI/CD à déployer par cloud"
  type        = number
  default     = 2
}

variable "runner_machine_type" {
  description = "Type de machine pour les runners GCP"
  type        = string
  default     = "e2-standard-2"
}

variable "runner_instance_type" {
  description = "Type d'instance pour les runners AWS"
  type        = string
  default     = "t3.medium"
}
