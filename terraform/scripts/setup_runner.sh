#!/bin/bash
# Script d'installation et de configuration d'un GitHub Actions Runner auto-hébergé
# Ce script sera exécuté au démarrage des instances déployées par Terraform

set -e

# Variables d'environnement (à remplacer par vos valeurs ou à injecter via cloud-init)
GITHUB_ORG="Casius999"
REPO_NAME="ecosysteme-cloud-ultime-automatise"
RUNNER_VERSION="2.311.0"
INSTANCE_NAME=$(curl -s "http://metadata.google.internal/computeMetadata/v1/instance/name" -H "Metadata-Flavor: Google" || hostname)

# Installation des prérequis
apt-get update
apt-get install -y curl jq docker.io docker-compose git unzip

# Activer et démarrer le service Docker
systemctl enable docker
systemctl start docker

# Créer l'utilisateur runner
useradd -m -s /bin/bash runner
usermod -aG docker runner

# Créer le répertoire pour le runner
mkdir -p /home/runner/actions-runner
cd /home/runner/actions-runner

# Télécharger le runner
curl -o actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz -L https://github.com/actions/runner/releases/download/v${RUNNER_VERSION}/actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz
tar xzf actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz
chown -R runner:runner /home/runner/actions-runner

# Installer Docker Compose v2
mkdir -p /usr/local/lib/docker/cli-plugins
curl -SL https://github.com/docker/compose/releases/download/v2.23.3/docker-compose-linux-x86_64 -o /usr/local/lib/docker/cli-plugins/docker-compose
chmod +x /usr/local/lib/docker/cli-plugins/docker-compose

# Installer kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
chmod +x kubectl
mv kubectl /usr/local/bin/

# Installer Helm
curl -fsSL -o get_helm.sh https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3
chmod 700 get_helm.sh
./get_helm.sh

# Installer Python, pip et les dépendances pour Qiskit
apt-get install -y python3 python3-pip
pip3 install qiskit qiskit-aer numpy pandas

# Créer le service systemd pour le runner
cat > /etc/systemd/system/actions-runner.service << EOF
[Unit]
Description=GitHub Actions Runner
After=network.target

[Service]
User=runner
WorkingDirectory=/home/runner/actions-runner
ExecStart=/home/runner/actions-runner/bin/runsvc.sh
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Pour un déploiement en production, vous devriez obtenir le token d'authentification
# via un mécanisme sécurisé comme Secret Manager ou un processus d'initialisation séparé
# Ici, nous créons un script d'initialisation à exécuter manuellement avec le token

cat > /home/runner/init_runner.sh << EOF
#!/bin/bash
# Ce script doit être exécuté manuellement pour configurer le runner avec un token valide

if [ -z "\$1" ]; then
  echo "Usage: \$0 <runner_token>"
  exit 1
fi

TOKEN=\$1

cd /home/runner/actions-runner
./config.sh --url https://github.com/${GITHUB_ORG}/${REPO_NAME} --token \$TOKEN --name "${INSTANCE_NAME}" --labels "cloud,k8s,docker,quantum" --work "_work" --unattended

systemctl enable actions-runner
systemctl start actions-runner
systemctl status actions-runner
EOF

chmod +x /home/runner/init_runner.sh
chown runner:runner /home/runner/init_runner.sh

# Installation d'outils de surveillance
apt-get install -y prometheus-node-exporter

# Installation de l'agent Cloud Operations (Stackdriver) pour Google Cloud
curl -sSO https://dl.google.com/cloudagents/add-google-cloud-ops-agent-repo.sh
bash add-google-cloud-ops-agent-repo.sh --also-install

# Installation de l'agent AWS CloudWatch pour AWS
if [ -f /sys/hypervisor/uuid ] && [ `head -c 3 /sys/hypervisor/uuid` == "ec2" ]; then
  wget https://s3.amazonaws.com/amazoncloudwatch-agent/debian/amd64/latest/amazon-cloudwatch-agent.deb
  dpkg -i -E ./amazon-cloudwatch-agent.deb
fi

# Installation de l'agent Azure Monitor pour Azure
if [ -d /var/lib/waagent ]; then
  wget https://raw.githubusercontent.com/Azure/azure-linux-extensions/master/AzureMonitorAgent/HandlerManifest.json
  # Configuration supplémentaire pour Azure Monitor...
fi

echo "Installation terminée ! Exécutez /home/runner/init_runner.sh avec le token du runner pour finaliser la configuration."
