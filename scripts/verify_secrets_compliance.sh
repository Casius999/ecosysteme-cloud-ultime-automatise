#!/bin/bash
# Script de vérification de la conformité des secrets
# Ce script vérifie que la gestion des secrets respecte la Charte d'Intégrité Systémique

set -e

# Couleurs pour l'affichage
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}===== Vérification de la Conformité des Secrets =====${NC}"
echo "Date: $(date '+%Y-%m-%d %H:%M:%S')"
echo "Conformité à la Charte Universelle d'Intégrité Systémique"
echo ""

# Variables pour le suivi des résultats
ISSUES_FOUND=0
WARNINGS=0

# Répertoires à scanner
DIRS_TO_SCAN=("terraform" "helm" "quantum-sim" "fallback-agent" ".github")

# Modèles de secrets potentiels à rechercher
SECRET_PATTERNS=(
  "api[_-]key"
  "access[_-]key"
  "auth[_-]token"
  "password"
  "secret"
  "credential"
  "private[_-]key"
  "token"
  "client[_-]secret"
)

# Modèles de fichiers à exclure
EXCLUDE_PATTERNS=(
  "verify_secrets_compliance.sh"
  "SECRETS_MANAGEMENT.md"
  ".gitignore"
  "package-lock.json"
  "*/node_modules/*"
)

# Fonction pour vérifier les secrets codés en dur
check_hardcoded_secrets() {
  echo -e "${BLUE}Vérification des secrets codés en dur...${NC}"
  
  exclude_args=""
  for pattern in "${EXCLUDE_PATTERNS[@]}"; do
    exclude_args="$exclude_args --exclude=$pattern"
  done
  
  for dir in "${DIRS_TO_SCAN[@]}"; do
    if [ -d "$dir" ]; then
      echo "Scan du répertoire: $dir"
      
      for pattern in "${SECRET_PATTERNS[@]}"; do
        # Recherche les motifs de secrets dans les fichiers
        results=$(grep -r -i -E "(${pattern})(.*?)=(.{8,})" $exclude_args "$dir" 2>/dev/null || true)
        
        if [ ! -z "$results" ]; then
          # Filtrer les faux positifs (références aux systèmes de gestion de secrets)
          filtered_results=$(echo "$results" | grep -v -E "(\$\{|vault:|secretsmanager:|key-vault:|env\.)" || true)
          
          if [ ! -z "$filtered_results" ]; then
            echo -e "${RED}Potential secret found with pattern '$pattern':${NC}"
            echo "$filtered_results" | while read -r line; do
              file=$(echo "$line" | cut -d: -f1)
              echo -e "${YELLOW}  $file${NC}"
            done
            ISSUES_FOUND=$((ISSUES_FOUND + 1))
          fi
        fi
      done
    fi
  done
  
  if [ $ISSUES_FOUND -eq 0 ]; then
    echo -e "${GREEN}✅ Aucun secret codé en dur détecté${NC}"
  else
    echo -e "${RED}❌ $ISSUES_FOUND problèmes potentiels de secrets codés en dur détectés${NC}"
  fi
  echo ""
}

# Fonction pour vérifier la configuration du gestionnaire de secrets externe
check_external_secrets_config() {
  echo -e "${BLUE}Vérification de la configuration du gestionnaire de secrets externe...${NC}"
  
  # Vérifier si des fichiers de configuration pour External Secrets existent
  if find . -name "*externalsecret*" -o -name "*secret-store*" | grep -q .; then
    echo -e "${GREEN}✅ Configuration de l'opérateur External Secrets détectée${NC}"
  else
    echo -e "${YELLOW}⚠️ Aucune configuration d'External Secrets trouvée - vérifiez l'intégration avec HashiCorp Vault${NC}"
    WARNINGS=$((WARNINGS + 1))
  fi
  
  # Vérifier la présence de fichiers de configuration Vault
  if find . -name "*vault*" | grep -q .; then
    echo -e "${GREEN}✅ Configuration de HashiCorp Vault détectée${NC}"
  else
    echo -e "${YELLOW}⚠️ Aucune configuration HashiCorp Vault trouvée - vérifiez le système de gestion des secrets${NC}"
    WARNINGS=$((WARNINGS + 1))
  fi
  
  echo ""
}

# Fonction pour vérifier les configurations Kubernetes Secrets
check_kubernetes_secrets() {
  echo -e "${BLUE}Vérification des configurations Kubernetes Secrets...${NC}"
  
  INSECURE_SECRETS=0
  SECRET_CONFIGS=$(find helm -name "*.yaml" -o -name "*.yml" | xargs grep -l "kind: Secret" 2>/dev/null || true)
  
  if [ -z "$SECRET_CONFIGS" ]; then
    echo -e "${YELLOW}⚠️ Aucun fichier de configuration Secret Kubernetes trouvé${NC}"
    WARNINGS=$((WARNINGS + 1))
  else
    echo "Configurations Secret trouvées:"
    
    for config in $SECRET_CONFIGS; do
      echo "  Vérification: $config"
      
      # Vérifier si des données sont codées en dur dans les secrets
      if grep -q "stringData:" "$config" && grep -q -v "stringData: {}" "$config"; then
        if grep -q -E "stringData:([^$]|$\{[^V])" "$config"; then
          echo -e "${RED}❌ Potentielle valeur de secret codée en dur dans $config${NC}"
          INSECURE_SECRETS=$((INSECURE_SECRETS + 1))
          ISSUES_FOUND=$((ISSUES_FOUND + 1))
        fi
      fi
      
      # Vérifier si des références externes sont utilisées pour les secrets
      if grep -q -E "\$\{VAULT:|secretsmanager:|key-vault:" "$config"; then
        echo -e "${GREEN}✅ Références externes à un système de gestion de secrets détectées${NC}"
      else
        echo -e "${YELLOW}⚠️ Aucune référence à un système externe de gestion de secrets dans $config${NC}"
        WARNINGS=$((WARNINGS + 1))
      fi
    done
    
    if [ $INSECURE_SECRETS -eq 0 ]; then
      echo -e "${GREEN}✅ Aucun secret codé en dur détecté dans les configurations Kubernetes${NC}"
    fi
  fi
  
  echo ""
}

# Fonction pour vérifier la politique de rotation des secrets
check_secret_rotation() {
  echo -e "${BLUE}Vérification de la politique de rotation des secrets...${NC}"
  
  # Vérifier si des configurations de rotation sont présentes
  ROTATION_CONFIGS=$(find . -name "*.yaml" -o -name "*.yml" | xargs grep -l "SecretRotation" 2>/dev/null || true)
  
  if [ -z "$ROTATION_CONFIGS" ]; then
    echo -e "${YELLOW}⚠️ Aucune configuration de rotation automatique des secrets trouvée${NC}"
    echo "  Assurez-vous que la rotation des secrets est configurée conformément à la Charte d'Intégrité"
    WARNINGS=$((WARNINGS + 1))
  else
    echo -e "${GREEN}✅ Configurations de rotation des secrets trouvées:${NC}"
    for config in $ROTATION_CONFIGS; do
      echo "  $config"
    done
  fi
  
  # Vérifier si des mécanismes de notification pour la rotation sont en place
  NOTIFICATION_CONFIGS=$(find . -name "*.yaml" -o -name "*.yml" | xargs grep -l "notifyEmail\|notification" 2>/dev/null || true)
  
  if [ -z "$NOTIFICATION_CONFIGS" ]; then
    echo -e "${YELLOW}⚠️ Aucune configuration de notification pour la rotation des secrets trouvée${NC}"
    WARNINGS=$((WARNINGS + 1))
  else
    echo -e "${GREEN}✅ Configurations de notification pour la rotation des secrets trouvées${NC}"
  fi
  
  echo ""
}

# Fonction pour vérifier l'intégration avec le système CI/CD
check_cicd_integration() {
  echo -e "${BLUE}Vérification de l'intégration des secrets avec le CI/CD...${NC}"
  
  GITHUB_WORKFLOWS=$(find .github/workflows -name "*.yml" -o -name "*.yaml" 2>/dev/null || true)
  
  if [ -z "$GITHUB_WORKFLOWS" ]; then
    echo -e "${YELLOW}⚠️ Aucun workflow GitHub Actions trouvé${NC}"
    WARNINGS=$((WARNINGS + 1))
  else
    SECURE_SECRET_USAGE=0
    INSECURE_SECRET_USAGE=0
    
    for workflow in $GITHUB_WORKFLOWS; do
      echo "  Vérification: $workflow"
      
      # Vérifier l'utilisation sécurisée des secrets GitHub Actions
      if grep -q "\${{ secrets\." "$workflow"; then
        echo -e "${GREEN}    ✅ Utilisation des secrets GitHub Actions détectée${NC}"
        SECURE_SECRET_USAGE=$((SECURE_SECRET_USAGE + 1))
      fi
      
      # Vérifier si des secrets sont définis directement dans le workflow
      if grep -q -E "(password|token|key|secret|credential):.{8,}" "$workflow"; then
        echo -e "${RED}    ❌ Potentiel secret défini directement dans le workflow${NC}"
        INSECURE_SECRET_USAGE=$((INSECURE_SECRET_USAGE + 1))
        ISSUES_FOUND=$((ISSUES_FOUND + 1))
      fi
    done
    
    if [ $SECURE_SECRET_USAGE -gt 0 ] && [ $INSECURE_SECRET_USAGE -eq 0 ]; then
      echo -e "${GREEN}✅ Intégration sécurisée des secrets avec GitHub Actions${NC}"
    fi
  fi
  
  echo ""
}

# Exécution des vérifications
check_hardcoded_secrets
check_external_secrets_config
check_kubernetes_secrets
check_secret_rotation
check_cicd_integration

# Rapport final
echo -e "${BLUE}===== Rapport de Conformité des Secrets =====${NC}"

if [ $ISSUES_FOUND -eq 0 ] && [ $WARNINGS -eq 0 ]; then
  echo -e "${GREEN}✅ CONFORMITÉ TOTALE: Aucun problème ou avertissement détecté${NC}"
  echo -e "${GREEN}La gestion des secrets est conforme à la Charte Universelle d'Intégrité Systémique${NC}"
  exit 0
elif [ $ISSUES_FOUND -eq 0 ]; then
  echo -e "${YELLOW}⚠️ CONFORMITÉ PARTIELLE: $WARNINGS avertissements détectés${NC}"
  echo -e "${YELLOW}Vérifiez les avertissements pour améliorer la conformité à la Charte d'Intégrité${NC}"
  exit 0
else
  echo -e "${RED}❌ NON-CONFORMITÉ: $ISSUES_FOUND problèmes et $WARNINGS avertissements détectés${NC}"
  echo -e "${RED}Corrigez les problèmes pour assurer la conformité à la Charte d'Intégrité${NC}"
  exit 1
fi
