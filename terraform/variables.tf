# Variables Terraform pour l'écosystème cloud automatisé

# Variables AWS
variable "aws_region" {
  description = "Région AWS principale pour le déploiement"
  type        = string
  default     = "eu-west-1"
}

variable "aws_availability_zones" {
  description = "Zones de disponibilité à utiliser dans la région AWS"
  type        = list(string)
  default     = ["eu-west-1a", "eu-west-1b", "eu-west-1c"]
}

# Variables Google Cloud
variable "gcp_project_id" {
  description = "ID du projet Google Cloud"
  type        = string
}

variable "gcp_region" {
  description = "Région Google Cloud principale pour le déploiement"
  type        = string
  default     = "europe-west1"
}

variable "gcp_zones" {
  description = "Zones à utiliser dans la région GCP"
  type        = list(string)
  default     = ["europe-west1-b", "europe-west1-c", "europe-west1-d"]
}

# Variables Azure
variable "azure_location" {
  description = "Région Azure principale pour le déploiement"
  type        = string
  default     = "westeurope"
}

# Variables Kubernetes
variable "k8s_version" {
  description = "Version de Kubernetes à déployer"
  type        = string
  default     = "1.25"
}

variable "node_count" {
  description = "Nombre de nœuds par défaut dans chaque cluster"
  type        = number
  default     = 3
}

variable "node_size" {
  description = "Taille des nœuds par défaut (varie selon le fournisseur cloud)"
  type = object({
    aws   = string
    gcp   = string
    azure = string
  })
  default = {
    aws   = "t3.large"
    gcp   = "e2-standard-4"
    azure = "Standard_D4_v3"
  }
}

# Variables pour les environnements
variable "environments" {
  description = "Environnements à déployer"
  type        = list(string)
  default     = ["development", "staging", "production"]
}

# Variables pour le monitoring
variable "prometheus_retention" {
  description = "Durée de rétention des données Prometheus en jours"
  type        = number
  default     = 15
}

# Variables pour les tags communs
variable "common_tags" {
  description = "Tags communs à appliquer à toutes les ressources"
  type        = map(string)
  default = {
    Project     = "CloudEcosystem"
    ManagedBy   = "Terraform"
    Environment = "Production"
  }
}