# Guide de Déploiement de l'Écosystème Cloud Ultime Automatisé

Ce document explique en détail les étapes à suivre pour déployer l'infrastructure complète de l'écosystème cloud ultime.

## 🔒 Conformité avec la Charte d'Intégrité Systémique

Toutes les procédures de déploiement sont strictement conformes à la Charte Universelle d'Intégrité Systémique. Aucune simulation fictive n'est utilisée dans ce processus, à l'exception des simulations quantiques pour l'optimisation basées sur des données réelles.

## Prérequis

Avant de commencer, assurez-vous d'avoir :

1. **Comptes cloud actifs** sur AWS, GCP et Azure avec droits administratifs
2. **CLI installés et configurés** :
   - AWS CLI
   - Google Cloud SDK
   - Azure CLI
   - kubectl
   - Helm (v3+)
   - Terraform
   - Python 3.8+ (avec pyyaml installé)

3. **Clés API** pour les services de fallback :
   - Anthropic API
   - OpenAI API (optionnel, comme alternative)

4. **Compte Docker Hub** pour le stockage des images

## Configuration des Identifiants

1. **Remplissez le fichier de configuration** : Éditez le fichier `config/credentials.yaml` pour y ajouter tous vos identifiants :

```yaml
aws:
  access_key_id: "votre-access-key-id"
  secret_access_key: "votre-secret-access-key"
  region: "eu-west-1"

gcp:
  project_id: "votre-projet-id"
  service_account_key_path: "./gcp-key.json"
  region: "europe-west1"

azure:
  subscription_id: "votre-subscription-id"
  tenant_id: "votre-tenant-id"
  client_id: "votre-client-id"
  client_secret: "votre-client-secret"
  location: "westeurope"

# ... autres sections
```

2. **Clé de service GCP** : Placez votre fichier de clé de service GCP JSON à l'emplacement spécifié dans la configuration.

3. **Vérifiez l'intégrité de la configuration** :
```bash
python scripts/verify_config_integrity.py config/credentials.yaml
```

## Déploiement de l'Infrastructure

### Option 1 : Déploiement Automatisé Complet

Utilisez le script de déploiement automatisé qui exécute toutes les étapes nécessaires :

```bash
chmod +x scripts/deploy_infrastructure.sh
./scripts/deploy_infrastructure.sh
```

Ce script :
1. Vérifie l'intégrité de la configuration
2. Déploie l'infrastructure avec Terraform
3. Configure kubectl pour accéder aux clusters
4. Déploie les composants essentiels (Vault, Istio, Prometheus, etc.)
5. Déploie l'agent de fallback et le module d'optimisation quantique
6. Effectue les vérifications d'intégrité post-déploiement

### Option 2 : Déploiement Manuel Par Étapes

Si vous préférez déployer étape par étape :

#### 1. Déploiement Terraform

```bash
cd terraform
terraform init
terraform plan -out=tf_plan
terraform apply -auto-approve tf_plan
cd ..
```

#### 2. Configuration de kubectl

```bash
# GKE
gcloud container clusters get-credentials --project YOUR_GCP_PROJECT_ID --zone YOUR_GCP_REGION-a ultimate-cluster-gcp

# EKS
aws eks update-kubeconfig --name ultimate-cluster-aws --region YOUR_AWS_REGION

# AKS
az aks get-credentials --resource-group ultimate-resource-group --name ultimate-cluster-azure
```

#### 3. Déploiement des Composants de Base

```bash
# HashiCorp Vault
helm repo add hashicorp https://helm.releases.hashicorp.com
helm repo update
helm install vault hashicorp/vault -f security/vault-values.yaml --namespace vault --create-namespace

# Istio pour Zero Trust
kubectl apply -f security/istio/zero-trust-config.yaml

# Prometheus et Grafana
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update
helm install prometheus prometheus-community/prometheus -f monitoring/prometheus-values.yaml --namespace monitoring --create-namespace
helm install grafana grafana/grafana -f monitoring/grafana-values.yaml --namespace monitoring
```

#### 4. Déploiement des Composants Principaux

```bash
# Agent de fallback
helm install fallback-agent ./helm/fallback-agent -f helm/fallback-agent/values.yaml --namespace production --create-namespace

# Module d'optimisation quantique
helm install quantum-sim ./helm/quantum-sim -f helm/quantum-sim/values.yaml --namespace production

# Application principale
helm install cloud-app ./helm/app -f helm/app/values.yaml --namespace production
```

#### 5. Vérification de l'Intégrité

```bash
python scripts/verify_integrity.py
```

## Accès aux Dashboards

- **Grafana** : `kubectl port-forward svc/grafana 3000:80 -n monitoring`
  Accédez à http://localhost:3000

- **Prometheus** : `kubectl port-forward svc/prometheus-server 9090:80 -n monitoring` 
  Accédez à http://localhost:9090

- **Application** : L'URL d'accès sera affichée à la fin du déploiement

## Gestion du Système de Fallback

Le système de fallback est configuré pour surveiller automatiquement l'état de Claude Desktop et basculer si nécessaire.

Pour forcer le mode fallback (tests) :
```bash
kubectl set env deployment/fallback-agent -n production FALLBACK_MODE=forced
```

Pour revenir au mode automatique :
```bash
kubectl set env deployment/fallback-agent -n production FALLBACK_MODE=auto
```

## Optimisation Quantique

Le module d'optimisation quantique s'exécutera automatiquement en production pour optimiser les ressources cloud.

Pour consulter les résultats de l'optimisation :
```bash
kubectl logs -l app=quantum-sim -n production
```

## Dépannage

Si vous rencontrez des problèmes lors du déploiement :

1. Vérifiez les logs du déploiement dans `./logs/`
2. Exécutez les scripts de vérification d'intégrité
3. Consultez la documentation spécifique à chaque composant

En cas de problème persistant, référez-vous aux manifestes Kubernetes et aux charts Helm pour les configurations détaillées.

## Nettoyage (Suppression)

Pour supprimer complètement l'infrastructure :

```bash
cd terraform
terraform destroy -auto-approve
cd ..
```

**ATTENTION : Cette opération est irréversible et supprimera toutes les ressources cloud déployées.**