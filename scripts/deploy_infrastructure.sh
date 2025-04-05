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

# Vérification d'intégrité
echo -e "${GREEN}Vérification d'intégrité de la configuration...${NC}"
if [ -f "scripts/verify_config_integrity.py" ]; then
    python scripts/verify_config_integrity.py "$CREDENTIALS_FILE"
    if [ $? -ne 0 ]; then
        echo -e "${RED}ERREUR: Échec de la vérification d'intégrité de la configuration.${NC}"
        exit 1
    fi
else
    echo -e "${RED}ERREUR: Script de vérification d'intégrité manquant.${NC}"
    exit 1
fi

# Journalisation des opérations
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
DEPLOY_LOG="logs/deploy_${TIMESTAMP}.log"
mkdir -p logs

echo -e "${GREEN}Journalisation des opérations dans $DEPLOY_LOG${NC}"
# Fonction pour journaliser les commandes et leur sortie
execute_and_log() {
    command=$1
    echo "Exécution de : $command" >> "$DEPLOY_LOG"
    echo -e "${YELLOW}Exécution de : $command${NC}"
    
    # Exécute la commande et capture sa sortie + son code de retour
    output=$(eval "$command" 2>&1)
    exit_code=$?
    
    echo "$output" >> "$DEPLOY_LOG"
    echo "$output"
    
    if [ $exit_code -ne 0 ]; then
        echo -e "${RED}La commande a échoué avec le code $exit_code${NC}" | tee -a "$DEPLOY_LOG"
        return $exit_code
    fi
    
    return 0
}

# Charger les variables d'environnement depuis le fichier YAML
echo -e "${GREEN}Chargement des identifiants...${NC}" | tee -a "$DEPLOY_LOG"
if [ -f "scripts/parse_credentials.py" ]; then
    execute_and_log "export \$(python scripts/parse_credentials.py)"
else
    echo -e "${RED}ERREUR: Script de parsing des credentials manquant.${NC}" | tee -a "$DEPLOY_LOG"
    exit 1
fi

# Archivage pour audit et traçabilité
echo -e "${GREEN}Archivage de la configuration pour audit...${NC}" | tee -a "$DEPLOY_LOG"
mkdir -p archives/configurations
cp "$CREDENTIALS_FILE" "archives/configurations/credentials_${TIMESTAMP}.yaml"
# Rendre anonyme la copie archivée pour la sécurité
if [ -f "scripts/anonymize_credentials.py" ]; then
    execute_and_log "python scripts/anonymize_credentials.py archives/configurations/credentials_${TIMESTAMP}.yaml"
fi

# Vérification des outils requis
echo -e "${GREEN}Vérification des outils requis...${NC}" | tee -a "$DEPLOY_LOG"
REQUIRED_TOOLS=("terraform" "kubectl" "helm" "gcloud" "aws" "az")
MISSING_TOOLS=0

for tool in "${REQUIRED_TOOLS[@]}"; do
    if ! command -v "$tool" &> /dev/null; then
        echo -e "${RED}Outil requis non installé: $tool${NC}" | tee -a "$DEPLOY_LOG"
        MISSING_TOOLS=$((MISSING_TOOLS+1))
    else
        echo -e "${GREEN}✓ $tool trouvé${NC}" | tee -a "$DEPLOY_LOG"
    fi
done

if [ $MISSING_TOOLS -gt 0 ]; then
    echo -e "${RED}ERREUR: $MISSING_TOOLS outil(s) requis manquant(s). Veuillez les installer avant de continuer.${NC}" | tee -a "$DEPLOY_LOG"
    exit 1
fi

# Déployer l'infrastructure avec Terraform
echo -e "${GREEN}Déploiement de l'infrastructure Terraform...${NC}" | tee -a "$DEPLOY_LOG"
cd terraform
execute_and_log "terraform init"
execute_and_log "terraform plan -out=tf_plan"
execute_and_log "terraform apply -auto-approve tf_plan"
cd ..

# Configurer kubectl pour accéder aux clusters
echo -e "${GREEN}Configuration de kubectl pour les clusters Kubernetes...${NC}" | tee -a "$DEPLOY_LOG"
# GKE
execute_and_log "gcloud container clusters get-credentials --project $GCP_PROJECT_ID --zone $GCP_REGION-a ultimate-cluster-gcp"
# EKS
execute_and_log "aws eks update-kubeconfig --name ultimate-cluster-aws --region $AWS_REGION"
# AKS
execute_and_log "az aks get-credentials --resource-group ultimate-resource-group --name ultimate-cluster-azure"

# Vérification des connexions aux clusters
echo -e "${GREEN}Vérification des connexions aux clusters...${NC}" | tee -a "$DEPLOY_LOG"
for context in $(kubectl config get-contexts -o name); do
    echo -e "Vérification du contexte Kubernetes: $context" | tee -a "$DEPLOY_LOG"
    if ! execute_and_log "kubectl --context $context get nodes"; then
        echo -e "${RED}ERREUR: Impossible de se connecter au cluster $context${NC}" | tee -a "$DEPLOY_LOG"
        exit 1
    fi
done

# Déployer HashiCorp Vault pour la gestion des secrets
echo -e "${GREEN}Déploiement de HashiCorp Vault pour la gestion des secrets...${NC}" | tee -a "$DEPLOY_LOG"
execute_and_log "helm repo add hashicorp https://helm.releases.hashicorp.com"
execute_and_log "helm repo update"
execute_and_log "helm install vault hashicorp/vault -f security/vault-values.yaml --namespace vault --create-namespace"

# Déployer Istio pour Zero Trust
echo -e "${GREEN}Déploiement d'Istio pour la sécurité Zero Trust...${NC}" | tee -a "$DEPLOY_LOG"
execute_and_log "kubectl apply -f security/istio/zero-trust-config.yaml"

# Déployer Prometheus et Grafana pour le monitoring
echo -e "${GREEN}Déploiement de Prometheus et Grafana...${NC}" | tee -a "$DEPLOY_LOG"
execute_and_log "helm repo add prometheus-community https://prometheus-community.github.io/helm-charts"
execute_and_log "helm repo add grafana https://grafana.github.io/helm-charts"
execute_and_log "helm repo update"
execute_and_log "helm install prometheus prometheus-community/prometheus -f monitoring/prometheus-values.yaml --namespace monitoring --create-namespace"
execute_and_log "helm install grafana grafana/grafana -f monitoring/grafana-values.yaml --namespace monitoring"

# Déployer les composants principaux avec Helm
echo -e "${GREEN}Déploiement de l'agent de fallback...${NC}" | tee -a "$DEPLOY_LOG"
execute_and_log "helm install fallback-agent ./helm/fallback-agent -f helm/fallback-agent/values.yaml --namespace production --create-namespace"

echo -e "${GREEN}Déploiement du module d'optimisation quantique...${NC}" | tee -a "$DEPLOY_LOG"
execute_and_log "helm install quantum-sim ./helm/quantum-sim -f helm/quantum-sim/values.yaml --namespace production"

echo -e "${GREEN}Déploiement de l'application principale...${NC}" | tee -a "$DEPLOY_LOG"
execute_and_log "helm install cloud-app ./helm/app -f helm/app/values.yaml --namespace production"

# Vérification post-déploiement des pods
echo -e "${GREEN}Vérification post-déploiement des pods...${NC}" | tee -a "$DEPLOY_LOG"
execute_and_log "kubectl get pods -n production"
execute_and_log "kubectl get pods -n monitoring"
execute_and_log "kubectl get pods -n vault"

# Exécuter les vérifications d'intégrité
echo -e "${GREEN}Vérification de l'intégrité du système...${NC}" | tee -a "$DEPLOY_LOG"
execute_and_log "python scripts/verify_integrity.py"

# Horodatage de fin de déploiement pour traçabilité
END_TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
DEPLOY_DURATION=$(($(date -d "$END_TIMESTAMP" +%s) - $(date -d "$TIMESTAMP" +%s)))
echo -e "Déploiement terminé à $END_TIMESTAMP (durée: $DEPLOY_DURATION secondes)" | tee -a "$DEPLOY_LOG"

# Archiver le log de déploiement avec signature pour audit
echo -e "${GREEN}Archivage du log de déploiement pour audit...${NC}" | tee -a "$DEPLOY_LOG"
if command -v gpg &> /dev/null; then
    if [ -n "$GPG_KEY_ID" ]; then
        echo "Signature du log de déploiement avec la clé GPG $GPG_KEY_ID" | tee -a "$DEPLOY_LOG"
        gpg --batch --yes --default-key "$GPG_KEY_ID" --detach-sign "$DEPLOY_LOG"
    else
        echo "Clé GPG non configurée, le log ne sera pas signé" | tee -a "$DEPLOY_LOG"
    fi
fi

# Calcul du hash du log pour vérification ultérieure
LOG_HASH=$(sha256sum "$DEPLOY_LOG" | cut -d ' ' -f 1)
echo "Hash SHA-256 du log de déploiement: $LOG_HASH" | tee -a "$DEPLOY_LOG"
echo "$LOG_HASH" > "${DEPLOY_LOG}.sha256"

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
