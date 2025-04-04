#!/bin/bash
# Script de déploiement de l'infrastructure cloud complète
# Ce script utilise le fichier de configuration des credentials pour déployer l'écosystème

set -e  # Arrêt en cas d'erreur

# Couleurs pour les messages
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}=============================================${NC}"
echo -e "${BLUE}= DÉPLOIEMENT DE L'ÉCOSYSTÈME CLOUD ULTIME =${NC}"
echo -e "${BLUE}=============================================${NC}"

# Vérification du fichier de credentials
CREDENTIALS_FILE="config/credentials.yaml"
if [ ! -f "$CREDENTIALS_FILE" ]; then
    echo -e "${RED}ERREUR: Le fichier $CREDENTIALS_FILE est manquant.${NC}"
    echo -e "Veuillez créer ce fichier en vous basant sur l'exemple fourni."
    exit 1
fi

echo -e "${GREEN}Vérification d'intégrité de la configuration...${NC}"
python scripts/verify_config_integrity.py "$CREDENTIALS_FILE"
if [ $? -ne 0 ]; then
    echo -e "${RED}ERREUR: Échec de la vérification d'intégrité de la configuration.${NC}"
    exit 1
fi

# Charger les variables d'environnement depuis le fichier YAML
echo -e "${GREEN}Chargement des identifiants...${NC}"
export $(python scripts/parse_credentials.py)

# Déployer l'infrastructure avec Terraform
echo -e "${GREEN}Déploiement de l'infrastructure Terraform...${NC}"
cd terraform
terraform init
terraform plan -out=tf_plan
terraform apply -auto-approve tf_plan
cd ..

# Configurer kubectl pour accéder aux clusters
echo -e "${GREEN}Configuration de kubectl pour les clusters Kubernetes...${NC}"
# GKE
gcloud container clusters get-credentials --project $GCP_PROJECT_ID --zone $GCP_REGION-a ultimate-cluster-gcp
# EKS
aws eks update-kubeconfig --name ultimate-cluster-aws --region $AWS_REGION
# AKS
az aks get-credentials --resource-group ultimate-resource-group --name ultimate-cluster-azure

# Déployer HashiCorp Vault pour la gestion des secrets
echo -e "${GREEN}Déploiement de HashiCorp Vault pour la gestion des secrets...${NC}"
helm repo add hashicorp https://helm.releases.hashicorp.com
helm repo update
helm install vault hashicorp/vault -f security/vault-values.yaml --namespace vault --create-namespace

# Déployer Istio pour Zero Trust
echo -e "${GREEN}Déploiement d'Istio pour la sécurité Zero Trust...${NC}"
kubectl apply -f security/istio/zero-trust-config.yaml

# Déployer Prometheus et Grafana pour le monitoring
echo -e "${GREEN}Déploiement de Prometheus et Grafana...${NC}"
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update
helm install prometheus prometheus-community/prometheus -f monitoring/prometheus-values.yaml --namespace monitoring --create-namespace
helm install grafana grafana/grafana -f monitoring/grafana-values.yaml --namespace monitoring

# Déployer les composants principaux avec Helm
echo -e "${GREEN}Déploiement de l'agent de fallback...${NC}"
helm install fallback-agent ./helm/fallback-agent -f helm/fallback-agent/values.yaml --namespace production --create-namespace

echo -e "${GREEN}Déploiement du module d'optimisation quantique...${NC}"
helm install quantum-sim ./helm/quantum-sim -f helm/quantum-sim/values.yaml --namespace production

echo -e "${GREEN}Déploiement de l'application principale...${NC}"
helm install cloud-app ./helm/app -f helm/app/values.yaml --namespace production

# Exécuter les vérifications d'intégrité
echo -e "${GREEN}Vérification de l'intégrité du système...${NC}"
python scripts/verify_integrity.py

echo -e "${BLUE}=============================================${NC}"
echo -e "${GREEN}DÉPLOIEMENT RÉUSSI !${NC}"
echo -e "${BLUE}=============================================${NC}"
echo -e "${YELLOW}Points d'accès:${NC}"
echo -e "- Console GCP: https://console.cloud.google.com/kubernetes/list?project=$GCP_PROJECT_ID"
echo -e "- Console AWS: https://console.aws.amazon.com/eks/home?region=$AWS_REGION#/clusters/ultimate-cluster-aws"
echo -e "- Console Azure: https://portal.azure.com/#blade/HubsExtension/BrowseResource/resourceType/Microsoft.ContainerService%2FmanagedClusters"
echo -e "${YELLOW}Pour accéder au dashboard Grafana:${NC}"
echo -e "kubectl port-forward svc/grafana 3000:80 -n monitoring"
echo -e "${YELLOW}URL: http://localhost:3000${NC}"
echo -e "${BLUE}=============================================${NC}"