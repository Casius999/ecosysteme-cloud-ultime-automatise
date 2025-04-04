# 🔒 Gestion des Secrets pour l'Écosystème Cloud Automatisé

Ce document explique les pratiques sécurisées pour la gestion des secrets dans l'écosystème cloud automatisé, conformément à la Charte Universelle d'Intégrité Systémique.

## Principes Fondamentaux

1. **Aucun secret n'est stocké dans le code source ou les fichiers de configuration**
2. **Tous les secrets sont chiffrés au repos et en transit**
3. **L'accès aux secrets est strictement contrôlé selon le principe du moindre privilège**
4. **Rotation automatique des secrets selon une politique définie**
5. **Auditabilité complète de l'accès aux secrets**

## Solutions de Gestion des Secrets

### 1. HashiCorp Vault (Solution Principale)

HashiCorp Vault est utilisé comme système principal de gestion des secrets pour l'écosystème cloud.

**Configuration:**
- Déploiement en mode haute disponibilité sur Kubernetes
- Authentification mutuelle TLS
- Stockage backend sur etcd chiffré
- Auto-unsealing via KMS cloud-native

**Utilisation:**
```bash
# Exemple d'accès à un secret (ne PAS inclure de vrais secrets dans les exemples)
vault kv get secret/production/api_keys/anthropic
```

### 2. Gestionnaires de Secrets Cloud-Natives

Pour la redondance et l'intégration avec les services cloud spécifiques:

#### GCP Secret Manager
```bash
# Accès aux secrets GCP
gcloud secrets versions access latest --secret=anthropic-api-key
```

#### AWS Secrets Manager
```bash
# Accès aux secrets AWS
aws secretsmanager get-secret-value --secret-id openai-api-key
```

#### Azure Key Vault
```bash
# Accès aux secrets Azure
az keyvault secret show --name claude-api-key --vault-name ultimate-keyvault
```

### 3. Secrets Kubernetes pour l'Environnement d'Exécution

```yaml
# Exemple de création de secret (NE JAMAIS inclure de vrais secrets dans les fichiers)
apiVersion: v1
kind: Secret
metadata:
  name: api-keys
  namespace: production
type: Opaque
stringData:
  # Référence aux valeurs à obtenir depuis un système externe, NE JAMAIS mettre de valeurs réelles
  anthropic_api_key: ${VAULT:secret/production/api_keys/anthropic}
  openai_api_key: ${VAULT:secret/production/api_keys/openai}
```

## Intégration avec le CI/CD

### GitHub Actions Secrets

Les workflows GitHub Actions utilisent les secrets sécurisés de GitHub:

```yaml
# Exemple d'utilisation SANS exposer de valeurs réelles
- name: Deploy with API Keys
  env:
    ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
  run: deploy-script.sh
```

### Secrets Injection avec External Secrets Operator

Nous utilisons External Secrets Operator pour synchroniser les secrets entre HashiCorp Vault et Kubernetes:

```yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: api-keys
  namespace: production
spec:
  refreshInterval: "1h"
  secretStoreRef:
    name: vault-backend
    kind: ClusterSecretStore
  target:
    name: api-keys
  data:
  - secretKey: anthropic_api_key
    remoteRef:
      key: secret/production/api_keys/anthropic
  - secretKey: openai_api_key
    remoteRef:
      key: secret/production/api_keys/openai
```

## Rotation des Secrets

### Politique de Rotation

| Type de Secret           | Fréquence de Rotation | Méthode                          |
|--------------------------|----------------------|----------------------------------|
| API Keys (LLM services)  | 90 jours             | Automatique avec notification    |
| Certificats TLS          | 60 jours             | Automatique avec cert-manager    |
| Tokens d'accès CI/CD     | 30 jours             | Semi-automatique avec notification |
| Credentials de base de données | 180 jours      | Orchestrée avec période de chevauchement |

### Processus Automatisé de Rotation

Nous utilisons un opérateur personnalisé Kubernetes pour la rotation des secrets:

```yaml
apiVersion: secretsmanagement.cloud.ecosystem/v1
kind: SecretRotation
metadata:
  name: api-keys-rotation
spec:
  targetSecret: api-keys
  schedule: "0 0 1 */3 *"  # Tous les 3 mois
  provider: anthropic
  notifyEmailOnRotation: security-team@example.com
```

## Vérification d'Intégrité des Secrets

Conformément à la Charte d'Intégrité Systémique, tous les accès aux secrets sont:

1. **Authentifiés** - Identité vérifiée avec authentification multi-facteurs
2. **Autorisés** - Contrôle d'accès basé sur les rôles (RBAC)
3. **Audités** - Journalisation complète de tous les accès
4. **Alertés** - Détection d'anomalies et alertes en temps réel

## Récupération et Sauvegarde

### Plan de Récupération des Secrets

En cas de compromission:

1. Révoquer immédiatement tous les secrets compromis
2. Activer les secrets de secours depuis un système isolé
3. Générer de nouveaux secrets avec une nouvelle entropie
4. Mettre à jour tous les systèmes dépendants
5. Analyser la cause première et mettre à jour les procédures

### Sauvegarde Sécurisée

Les sauvegardes des secrets sont:
- Chiffrées avec une clé maître protégée par HSM
- Stockées dans au moins trois régions géographiques distinctes
- Vérifiées mensuellement pour la restauration
- Accessibles uniquement via un processus break-glass audité

## Architecture de Référence

```
                   ┌─────────────────┐
                   │  HashiCorp Vault │
                   │    (Primary)    │
                   └────────┬────────┘
                            │
          ┌─────────────────┼─────────────────┐
          │                 │                 │
┌─────────▼────────┐ ┌──────▼───────┐ ┌───────▼──────┐
│   GCP Secret     │ │   AWS Secret  │ │  Azure Key   │
│    Manager       │ │    Manager    │ │    Vault     │
└─────────┬────────┘ └──────┬───────┘ └───────┬──────┘
          │                 │                 │
          └─────────────────┼─────────────────┘
                            │
                   ┌────────▼────────┐
                   │ External Secrets │
                   │    Operator     │
                   └────────┬────────┘
                            │
                   ┌────────▼────────┐
                   │   Kubernetes    │
                   │     Secrets     │
                   └────────┬────────┘
                            │
          ┌─────────────────┼─────────────────┐
          │                 │                 │
┌─────────▼────────┐ ┌──────▼───────┐ ┌───────▼──────┐
│   Application    │ │   Fallback   │ │   Quantum    │
│     Pods         │ │    Agent     │ │  Optimizer   │
└──────────────────┘ └──────────────┘ └──────────────┘
```

## Template pour les Secrets de Production

> ⚠️ **AVERTISSEMENT** : Ce fichier ne contient PAS de vrais secrets. Il s'agit d'un TEMPLATE à compléter par le processus de déploiement sécurisé.

Créez un fichier `production-secrets.env` en utilisant ce template:

```
# API Keys pour les services LLM
ANTHROPIC_API_KEY=
OPENAI_API_KEY=

# Credentials pour les services cloud
GCP_SERVICE_ACCOUNT_KEY=
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AZURE_CLIENT_ID=
AZURE_CLIENT_SECRET=

# Credentials pour la base de données
DB_USERNAME=
DB_PASSWORD=

# Certificats et clés privées
TLS_PRIVATE_KEY=
TLS_CERTIFICATE=

# Tokens d'authentification
GITHUB_ACCESS_TOKEN=
```

Ce fichier doit être rempli par le processus de déploiement qui récupère les secrets depuis HashiCorp Vault ou un système de gestion de secrets équivalent. Il ne doit JAMAIS être commité dans le dépôt de code.

## Vérification de Conformité

Pour vérifier la conformité de la gestion des secrets avec la Charte d'Intégrité Systémique, exécutez:

```bash
./scripts/verify_secrets_compliance.sh
```

Ce script vérifie:
- L'absence de secrets codés en dur dans le code
- La configuration correcte des intégrations avec les gestionnaires de secrets
- La rotation appropriée des secrets selon la politique définie

---

**Statut de ce document**: CONTRAIGNANT  
**Version**: 1.0  
**Date**: 2025-04-04