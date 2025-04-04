#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script de vérification d'intégrité du fichier de configuration des credentials.
Ce script s'assure que toutes les informations nécessaires sont présentes
et correctement formatées dans le fichier de configuration.
"""

import os
import sys
import yaml
import re
import logging
from datetime import datetime


# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f"config_integrity_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    ]
)

logger = logging.getLogger("ConfigIntegrityChecker")


class ConfigIntegrityChecker:
    """Classe pour vérifier l'intégrité du fichier de configuration."""
    
    def __init__(self, config_path):
        """Initialisation du vérificateur d'intégrité."""
        self.config_path = config_path
        self.config = None
        self.violation_count = 0
    
    def check_integrity(self):
        """Exécute toutes les vérifications d'intégrité sur le fichier de configuration."""
        try:
            self._load_config()
            
            # Exécuter les vérifications
            self._check_aws_credentials()
            self._check_gcp_credentials()
            self._check_azure_credentials()
            self._check_llm_credentials()
            self._check_docker_credentials()
            self._check_network_config()
            self._check_cluster_config()
            
            if self.violation_count > 0:
                logger.error(f"Vérification d'intégrité terminée avec {self.violation_count} violation(s).")
                return False
            else:
                logger.info("Vérification d'intégrité réussie. La configuration est valide.")
                return True
                
        except Exception as e:
            logger.error(f"Erreur lors de la vérification d'intégrité: {str(e)}")
            return False
    
    def _load_config(self):
        """Charge le fichier de configuration YAML."""
        try:
            with open(self.config_path, 'r') as f:
                self.config = yaml.safe_load(f)
            logger.info(f"Configuration chargée depuis {self.config_path}")
        except Exception as e:
            logger.error(f"Impossible de charger le fichier de configuration: {str(e)}")
            raise
    
    def _check_required_section(self, section_name):
        """Vérifie si une section requise est présente dans la configuration."""
        if section_name not in self.config:
            self._log_violation(f"Section requise '{section_name}' manquante")
            return False
        return True
    
    def _check_aws_credentials(self):
        """Vérifie les identifiants AWS."""
        if not self._check_required_section('aws'):
            return
        
        # Vérifier les champs requis
        required_fields = ['access_key_id', 'secret_access_key', 'region']
        for field in required_fields:
            if field not in self.config['aws']:
                self._log_violation(f"Champ requis 'aws.{field}' manquant")
        
        # Vérifier le format des identifiants
        if 'access_key_id' in self.config['aws'] and not re.match(r'^[A-Z0-9]{20}$', self.config['aws']['access_key_id']):
            if self.config['aws']['access_key_id'] == "VOTRE_AWS_ACCESS_KEY_ID":
                self._log_violation("La clé d'accès AWS n'a pas été configurée")
            else:
                self._log_violation("Format de la clé d'accès AWS invalide")
        
        if 'region' in self.config['aws'] and not re.match(r'^[a-z]{2}-[a-z]+-\d$', self.config['aws']['region']):
            self._log_violation("Format de la région AWS invalide")
    
    def _check_gcp_credentials(self):
        """Vérifie les identifiants GCP."""
        if not self._check_required_section('gcp'):
            return
        
        # Vérifier les champs requis
        required_fields = ['project_id', 'service_account_key_path', 'region']
        for field in required_fields:
            if field not in self.config['gcp']:
                self._log_violation(f"Champ requis 'gcp.{field}' manquant")
        
        # Vérifier l'existence du fichier de clé de service
        if 'service_account_key_path' in self.config['gcp']:
            key_path = self.config['gcp']['service_account_key_path']
            if key_path != "./gcp-key.json" and not os.path.exists(key_path):
                self._log_violation(f"Le fichier de clé de service GCP '{key_path}' n'existe pas")
    
    def _check_azure_credentials(self):
        """Vérifie les identifiants Azure."""
        if not self._check_required_section('azure'):
            return
        
        # Vérifier les champs requis
        required_fields = ['subscription_id', 'tenant_id', 'client_id', 'client_secret', 'location']
        for field in required_fields:
            if field not in self.config['azure']:
                self._log_violation(f"Champ requis 'azure.{field}' manquant")
        
        # Vérifier le format des identifiants
        id_fields = ['subscription_id', 'tenant_id', 'client_id']
        for field in id_fields:
            if field in self.config['azure'] and not re.match(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', self.config['azure'][field]):
                if self.config['azure'][field].startswith("VOTRE_"):
                    self._log_violation(f"L'identifiant Azure '{field}' n'a pas été configuré")
                else:
                    self._log_violation(f"Format de l'identifiant Azure '{field}' invalide")
    
    def _check_llm_credentials(self):
        """Vérifie les identifiants des API LLM."""
        if not self._check_required_section('llm'):
            return
        
        # Vérifier qu'au moins une clé API est configurée
        api_keys = ['anthropic_api_key', 'openai_api_key']
        if not any(key in self.config['llm'] for key in api_keys):
            self._log_violation("Au moins une clé API LLM doit être configurée")
        
        # Vérifier le format des clés API
        if 'anthropic_api_key' in self.config['llm'] and self.config['llm']['anthropic_api_key'] == "VOTRE_CLE_API_ANTHROPIC":
            self._log_violation("La clé API Anthropic n'a pas été configurée")
        
        if 'openai_api_key' in self.config['llm'] and self.config['llm']['openai_api_key'] == "VOTRE_CLE_API_OPENAI":
            self._log_violation("La clé API OpenAI n'a pas été configurée")
    
    def _check_docker_credentials(self):
        """Vérifie les identifiants Docker Hub."""
        if not self._check_required_section('docker'):
            return
        
        # Vérifier les champs requis
        required_fields = ['username', 'password', 'email']
        for field in required_fields:
            if field not in self.config['docker']:
                self._log_violation(f"Champ requis 'docker.{field}' manquant")
            elif self.config['docker'][field].startswith("VOTRE_"):
                self._log_violation(f"L'identifiant Docker '{field}' n'a pas été configuré")
    
    def _check_network_config(self):
        """Vérifie la configuration réseau."""
        if not self._check_required_section('network'):
            return
        
        # Vérifier les champs et formats CIDR
        cidr_fields = ['aws_vpc_cidr', 'azure_vnet_cidr']
        for field in cidr_fields:
            if field not in self.config['network']:
                self._log_violation(f"Champ réseau '{field}' manquant")
            elif not re.match(r'^(\d{1,3}\.){3}\d{1,3}\/\d{1,2}$', self.config['network'][field]):
                self._log_violation(f"Format CIDR '{self.config['network'][field]}' invalide pour '{field}'")
    
    def _check_cluster_config(self):
        """Vérifie la configuration des clusters."""
        if not self._check_required_section('cluster'):
            return
        
        # Vérifier la présence des configurations pour chaque fournisseur
        providers = ['gke', 'eks', 'aks']
        for provider in providers:
            if provider not in self.config['cluster']:
                self._log_violation(f"Configuration du cluster '{provider}' manquante")
                continue
            
            # Vérifier les paramètres de base pour chaque fournisseur
            base_params = ['node_count', 'min_nodes', 'max_nodes']
            for param in base_params:
                if param not in self.config['cluster'][provider]:
                    self._log_violation(f"Paramètre '{param}' manquant pour le cluster '{provider}'")
            
            # Vérifier les paramètres spécifiques à chaque fournisseur
            if provider == 'gke':
                if 'machine_type' not in self.config['cluster'][provider]:
                    self._log_violation("Paramètre 'machine_type' manquant pour GKE")
            elif provider == 'eks':
                if 'instance_type' not in self.config['cluster'][provider]:
                    self._log_violation("Paramètre 'instance_type' manquant pour EKS")
            elif provider == 'aks':
                if 'vm_size' not in self.config['cluster'][provider]:
                    self._log_violation("Paramètre 'vm_size' manquant pour AKS")
    
    def _log_violation(self, message):
        """Enregistre une violation d'intégrité."""
        self.violation_count += 1
        logger.error(f"VIOLATION {self.violation_count}: {message}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python verify_config_integrity.py <chemin_du_fichier_config>")
        sys.exit(1)
    
    config_path = sys.argv[1]
    checker = ConfigIntegrityChecker(config_path)
    
    if checker.check_integrity():
        sys.exit(0)
    else:
        sys.exit(1)
