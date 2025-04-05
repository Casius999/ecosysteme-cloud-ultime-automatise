#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script de vérification d'intégrité des fichiers de configuration
Ce script vérifie que les fichiers de configuration ne contiennent pas de secrets exposés
et sont conformes aux principes de la Charte Universelle d'Intégrité Systémique.
"""

import os
import sys
import yaml
import json
import logging
import hashlib
import argparse
import re
from pathlib import Path

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("config_integrity_verification.log")
    ]
)

logger = logging.getLogger("ConfigIntegrityVerification")

class ConfigIntegrityVerifier:
    """Classe pour vérifier l'intégrité des fichiers de configuration"""
    
    def __init__(self, config_path):
        """Initialisation du vérificateur d'intégrité de configuration"""
        self.config_path = config_path
        self.violations = []
        
        logger.info(f"Démarrage de la vérification d'intégrité de configuration: {config_path}")
    
    def verify(self):
        """Exécute toutes les vérifications d'intégrité de configuration"""
        if not os.path.exists(self.config_path):
            logger.error(f"Fichier de configuration non trouvé: {self.config_path}")
            return False
        
        try:
            # Déterminer le type de fichier de configuration
            if self.config_path.endswith(('.yaml', '.yml')):
                with open(self.config_path, 'r') as f:
                    config_data = yaml.safe_load(f)
                file_type = "YAML"
            elif self.config_path.endswith('.json'):
                with open(self.config_path, 'r') as f:
                    config_data = json.load(f)
                file_type = "JSON"
            else:
                logger.error(f"Type de fichier de configuration non supporté: {self.config_path}")
                return False
            
            logger.info(f"Fichier de configuration {file_type} chargé: {self.config_path}")
            
            # Vérifier l'absence de secrets exposés
            self.check_secrets_exposure(config_data)
            
            # Vérifier la structure de la configuration
            self.check_config_structure(config_data)
            
            # Vérifier la cohérence des valeurs
            self.check_value_consistency(config_data)
            
            # Afficher le résultat
            if not self.violations:
                logger.info(f"✅ Vérification d'intégrité de la configuration réussie: {self.config_path}")
                return True
            else:
                logger.error(f"❌ Échec de la vérification d'intégrité de la configuration: {len(self.violations)} violation(s)")
                for violation in self.violations:
                    logger.error(f"- {violation}")
                return False
            
        except Exception as e:
            logger.error(f"Erreur lors de la vérification du fichier de configuration: {str(e)}")
            return False
    
    def check_secrets_exposure(self, config_data, path=""):
        """Vérifie l'absence de secrets exposés dans la configuration"""
        if isinstance(config_data, dict):
            for key, value in config_data.items():
                current_path = f"{path}.{key}" if path else key
                
                # Vérifier si la clé suggère un secret
                secret_keys = ["password", "secret", "key", "token", "credential", "pwd", "auth"]
                is_secret_key = any(secret_word in key.lower() for secret_word in secret_keys)
                
                if is_secret_key and isinstance(value, str) and value:
                    # Vérifier si la valeur ressemble à un vrai secret (pas un placeholder)
                    placeholders = ["$", "{", "%%", "<<", "PLACEHOLDER", "CHANGE_ME", "<your"]
                    if not any(placeholder in value for placeholder in placeholders):
                        # Vérifier si la valeur ressemble à un token/clé
                        secret_patterns = [
                            r'[A-Za-z0-9+/]{40,}',  # Base64
                            r'[A-Za-z0-9]{20,}',    # Alphanumeric keys
                            r'[0-9a-f]{32,}',       # Hex (md5, etc)
                            r'-----BEGIN .* KEY-----'  # PEM keys
                        ]
                        
                        if any(re.search(pattern, value) for pattern in secret_patterns):
                            violation = f"Secret exposé détecté dans la configuration: {current_path}"
                            logger.error(violation)
                            self.violations.append(violation)
                
                # Récursion pour les valeurs imbriquées
                if isinstance(value, (dict, list)):
                    self.check_secrets_exposure(value, current_path)
        
        elif isinstance(config_data, list):
            for i, item in enumerate(config_data):
                current_path = f"{path}[{i}]"
                if isinstance(item, (dict, list)):
                    self.check_secrets_exposure(item, current_path)
    
    def check_config_structure(self, config_data):
        """Vérifie la structure de base de la configuration"""
        # Vérifier que la configuration est bien un dictionnaire
        if not isinstance(config_data, dict):
            violation = "Le fichier de configuration doit contenir un objet JSON/YAML (dictionnaire)"
            logger.error(violation)
            self.violations.append(violation)
            return
        
        # Vérifier les sections requises en fonction du nom du fichier
        filename = os.path.basename(self.config_path)
        
        if "credentials" in filename.lower():
            required_sections = []
            
            # Vérifier les sections selon les fournisseurs cloud potentiels
            cloud_providers = ["aws", "gcp", "azure"]
            found_providers = []
            
            for provider in cloud_providers:
                if provider in config_data:
                    found_providers.append(provider)
                    
                    # Vérifier les champs requis pour chaque fournisseur
                    if provider == "aws":
                        if not all(key in config_data[provider] for key in ["access_key_id", "secret_access_key", "region"]):
                            violation = f"Champs requis manquants dans la section AWS"
                            logger.error(violation)
                            self.violations.append(violation)
                    
                    elif provider == "gcp":
                        if not all(key in config_data[provider] for key in ["project_id", "service_account_key_path", "region"]):
                            violation = f"Champs requis manquants dans la section GCP"
                            logger.error(violation)
                            self.violations.append(violation)
                    
                    elif provider == "azure":
                        if not all(key in config_data[provider] for key in ["subscription_id", "tenant_id", "client_id", "location"]):
                            violation = f"Champs requis manquants dans la section Azure"
                            logger.error(violation)
                            self.violations.append(violation)
            
            if not found_providers:
                violation = "Aucun fournisseur cloud (AWS, GCP, Azure) trouvé dans le fichier de credentials"
                logger.error(violation)
                self.violations.append(violation)
        
        elif "integrity" in filename.lower():
            required_fields = ["version", "status"]
            missing_fields = [field for field in required_fields if field not in config_data]
            
            if missing_fields:
                violation = f"Champs requis manquants dans la configuration d'intégrité: {', '.join(missing_fields)}"
                logger.error(violation)
                self.violations.append(violation)
    
    def check_value_consistency(self, config_data):
        """Vérifie la cohérence des valeurs dans la configuration"""
        if not isinstance(config_data, dict):
            return
        
        # Vérifier les valeurs de région
        regions = []
        
        # Extraire les régions AWS
        if "aws" in config_data and "region" in config_data["aws"]:
            regions.append(("AWS", config_data["aws"]["region"]))
        
        # Extraire les régions GCP
        if "gcp" in config_data and "region" in config_data["gcp"]:
            regions.append(("GCP", config_data["gcp"]["region"]))
        
        # Extraire les régions Azure
        if "azure" in config_data and "location" in config_data["azure"]:
            regions.append(("Azure", config_data["azure"]["location"]))
        
        # Vérifier la validité des régions
        for provider, region in regions:
            if provider == "AWS":
                valid_regions = ["us-east-1", "us-east-2", "us-west-1", "us-west-2", 
                                "eu-west-1", "eu-west-2", "eu-west-3", "eu-central-1",
                                "ap-northeast-1", "ap-northeast-2", "ap-southeast-1", "ap-southeast-2"]
                if region not in valid_regions:
                    logger.warning(f"Région AWS potentiellement invalide: {region}")
            
            elif provider == "GCP":
                valid_regions = ["us-central1", "us-east1", "us-east4", "us-west1", "us-west2",
                                "europe-west1", "europe-west2", "europe-west3", "europe-west4"]
                if not any(region.startswith(valid_region) for valid_region in valid_regions):
                    logger.warning(f"Région GCP potentiellement invalide: {region}")
            
            elif provider == "Azure":
                valid_regions = ["eastus", "eastus2", "westus", "westus2", "centralus",
                                "westeurope", "northeurope", "uksouth", "southeastasia"]
                if region not in valid_regions:
                    logger.warning(f"Région Azure potentiellement invalide: {region}")
        
        # Vérifier la validité des versions
        if "version" in config_data:
            version = config_data["version"]
            if not (isinstance(version, (str, int, float)) and str(version).replace(".", "").isdigit()):
                violation = f"Format de version invalide: {version}"
                logger.error(violation)
                self.violations.append(violation)


def calculate_file_hash(file_path):
    """Calcule le hash SHA-256 d'un fichier"""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def log_config_state(config_path):
    """Enregistre l'état actuel de la configuration pour audit"""
    if not os.path.exists(config_path):
        return
    
    hash_value = calculate_file_hash(config_path)
    filename = os.path.basename(config_path)
    
    log_dir = "logs/config"
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = os.path.join(log_dir, "config_state.log")
    with open(log_file, "a") as f:
        f.write(f"{hash_value},{filename},{os.path.getsize(config_path)},{os.path.getmtime(config_path)}\n")
    
    logger.info(f"État de la configuration enregistré: {filename} (SHA-256: {hash_value})")


def main():
    """Fonction principale"""
    parser = argparse.ArgumentParser(description="Vérificateur d'intégrité des fichiers de configuration")
    parser.add_argument('config_path', help='Chemin vers le fichier de configuration à vérifier')
    args = parser.parse_args()
    
    # Enregistrer l'état actuel de la configuration pour audit
    log_config_state(args.config_path)
    
    # Vérifier l'intégrité de la configuration
    verifier = ConfigIntegrityVerifier(args.config_path)
    result = verifier.verify()
    
    # Code de retour basé sur le résultat
    sys.exit(0 if result else 1)


if __name__ == "__main__":
    main()
