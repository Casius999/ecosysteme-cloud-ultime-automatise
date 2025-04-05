#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script de vérification d'intégrité systémique
Ce script vérifie que tous les composants de l'écosystème cloud respectent
les principes d'intégrité définis dans la Charte Universelle d'Intégrité Systémique.
"""

import os
import sys
import yaml
import json
import logging
import hashlib
import argparse
import datetime
import requests
from pathlib import Path
import subprocess
import re
import time

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("integrity_verification.log")
    ]
)

logger = logging.getLogger("IntegrityVerification")

class IntegrityVerifier:
    """Classe principale pour vérifier l'intégrité systémique"""
    
    def __init__(self, config_path="config/integrity.yaml"):
        """Initialisation du vérificateur d'intégrité"""
        self.config_path = config_path
        self.load_config()
        self.violation_count = 0
        self.timestamp = datetime.datetime.now().isoformat()
        self.verification_id = hashlib.sha256(self.timestamp.encode()).hexdigest()[:16]
        self.report_data = {
            "verification_id": self.verification_id,
            "timestamp": self.timestamp,
            "violations": [],
            "checks_performed": []
        }
        
        logger.info(f"Démarrage de la vérification d'intégrité [ID: {self.verification_id}]")
    
    def load_config(self):
        """Chargement de la configuration d'intégrité"""
        try:
            # Si le fichier de configuration n'existe pas, créer un fichier par défaut
            if not os.path.exists(self.config_path):
                config_dir = os.path.dirname(self.config_path)
                if not os.path.exists(config_dir):
                    os.makedirs(config_dir)
                
                default_config = {
                    "version": "3.0",
                    "status": "CONTRAIGNANT",
                    "verification": {
                        "data_integrity": {
                            "enabled": True,
                            "methods": [
                                {"type": "cryptographic_hash", "algorithm": "sha256"},
                                {"type": "digital_signature", "algorithm": "rsa"}
                            ]
                        }
                    },
                    "component_implementation": {
                        "terraform": {
                            "integrity_validation": {"enabled": True}
                        },
                        "kubernetes": {
                            "integrity_validation": {"enabled": True}
                        },
                        "quantum_optimization": {
                            "integrity_validation": {"enabled": True}
                        },
                        "fallback_agent": {
                            "integrity_validation": {"enabled": True}
                        }
                    }
                }
                
                with open(self.config_path, 'w') as f:
                    yaml.dump(default_config, f, default_flow_style=False)
                
                logger.info(f"Fichier de configuration créé avec des valeurs par défaut : {self.config_path}")
                self.config = default_config
            else:
                with open(self.config_path, 'r') as f:
                    self.config = yaml.safe_load(f)
                
                logger.info(f"Configuration d'intégrité chargée depuis {self.config_path}")
            
            # Vérifier l'intégrité de la configuration elle-même
            if self.config.get('version') != "3.0" or self.config.get('status') != "CONTRAIGNANT":
                logger.error(f"La configuration d'intégrité n'est pas valide : version={self.config.get('version')}, status={self.config.get('status')}")
                self.record_violation("config", "invalid_config", "Critique", 
                                    f"Configuration d'intégrité non valide : version={self.config.get('version')}, status={self.config.get('status')}")
        
        except Exception as e:
            logger.error(f"Erreur lors du chargement de la configuration : {str(e)}")
            self.record_violation("config", "load_error", "Critique", str(e))
    
    def verify_all(self):
        """Exécute toutes les vérifications d'intégrité"""
        logger.info("Démarrage de la vérification complète")
        
        try:
            # Vérifier la présence de la Charte d'Intégrité
            self.verify_charter_presence()
            
            # Vérifier les répertoires essentiels
            self.verify_essential_directories()
            
            # Vérifier les différents aspects
            self.verify_data_integrity()
            self.verify_terraform_integrity()
            self.verify_kubernetes_integrity()
            self.verify_quantum_integrity()
            self.verify_fallback_integrity()
            
            # Vérifier l'absence de simulations fictives
            self.verify_no_fictional_simulations()
            
            # Vérifier la sécurité
            self.verify_security()
            
            # Génération du rapport final
            self.generate_report()
            
            # Journalisation du résumé
            if self.violation_count == 0:
                logger.info("✅ Vérification d'intégrité réussie : aucune violation détectée")
            else:
                logger.error(f"❌ Échec de la vérification d'intégrité : {self.violation_count} violation(s) détectée(s)")
        
        except Exception as e:
            logger.error(f"Erreur lors de la vérification d'intégrité : {str(e)}")
            self.record_violation("verification", "general_error", "Critique", str(e))
        
        return self.violation_count == 0
    
    def verify_charter_presence(self):
        """Vérifie la présence et le contenu de la Charte d'Intégrité"""
        logger.info("Vérification de la Charte d'Intégrité Systémique")
        
        charter_path = "INTEGRITY_CHARTER.md"
        if not os.path.exists(charter_path):
            logger.error(f"Charte d'Intégrité non trouvée : {charter_path}")
            self.record_violation("charter", "missing_charter", "Critique", "Charte d'Intégrité Systémique manquante")
            return
        
        try:
            with open(charter_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Vérification des sections essentielles
            required_sections = [
                "CHARTE UNIVERSELLE D'INTÉGRITÉ SYSTÉMIQUE",
                "VÉRACITÉ TOTALE",
                "INTÉGRITÉ ABSOLUE DES DONNÉES",
                "INTERDICTION CATÉGORIQUE DE LA SIMULATION"
            ]
            
            missing_sections = []
            for section in required_sections:
                if section.lower() not in content.lower():
                    missing_sections.append(section)
            
            if missing_sections:
                logger.error(f"Sections essentielles manquantes dans la Charte d'Intégrité : {', '.join(missing_sections)}")
                self.record_violation("charter", "incomplete_charter", "Critique", 
                                     f"Sections essentielles manquantes dans la Charte d'Intégrité : {', '.join(missing_sections)}")
            else:
                logger.info("✅ Charte d'Intégrité Systémique valide")
                self.report_data["checks_performed"].append({
                    "check": "charter_presence",
                    "status": "success",
                    "timestamp": datetime.datetime.now().isoformat()
                })
        
        except Exception as e:
            logger.error(f"Erreur lors de la vérification de la Charte d'Intégrité : {str(e)}")
            self.record_violation("charter", "charter_verification_error", "Critique", str(e))
    
    def verify_essential_directories(self):
        """Vérifie la présence des répertoires essentiels"""
        logger.info("Vérification des répertoires essentiels")
        
        essential_dirs = [
            "app", "terraform", "quantum-sim", "fallback-agent", 
            "helm", "scripts", "config", "security"
        ]
        
        missing_dirs = []
        for directory in essential_dirs:
            if not os.path.exists(directory):
                missing_dirs.append(directory)
        
        if missing_dirs:
            logger.error(f"Répertoires essentiels manquants : {', '.join(missing_dirs)}")
            self.record_violation("structure", "missing_directories", "Critique", 
                                f"Répertoires essentiels manquants : {', '.join(missing_dirs)}")
        else:
            logger.info("✅ Tous les répertoires essentiels sont présents")
            self.report_data["checks_performed"].append({
                "check": "essential_directories",
                "status": "success",
                "timestamp": datetime.datetime.now().isoformat()
            })
    
    def verify_data_integrity(self):
        """Vérifie l'intégrité des données"""
        logger.info("Vérification de l'intégrité des données")
        
        if not self.config.get('verification', {}).get('data_integrity', {}).get('enabled', True):
            logger.warning("La vérification d'intégrité des données est désactivée")
            return
        
        # Vérification de la journalisation des opérations
        logs_dir = "logs"
        if not os.path.exists(logs_dir):
            logger.warning(f"Répertoire de logs non trouvé : {logs_dir}")
            self.record_violation("data_integrity", "missing_logs_directory", "Moyenne", 
                                f"Répertoire de journalisation manquant : {logs_dir}")
        
        # Vérification des archives pour traçabilité
        archives_dir = "archives"
        if not os.path.exists(archives_dir):
            logger.warning(f"Répertoire d'archives non trouvé : {archives_dir}")
            self.record_violation("data_integrity", "missing_archives_directory", "Moyenne", 
                                f"Répertoire d'archives manquant : {archives_dir}")
        
        # Ajout à la liste des vérifications effectuées
        self.report_data["checks_performed"].append({
            "check": "data_integrity",
            "status": "completed",
            "timestamp": datetime.datetime.now().isoformat()
        })
        
        logger.info("Vérification de l'intégrité des données terminée")
    
    def verify_terraform_integrity(self):
        """Vérifie l'intégrité des fichiers Terraform"""
        logger.info("Vérification de l'intégrité des fichiers Terraform")
        
        if not self.config.get('component_implementation', {}).get('terraform', {}).get('integrity_validation', {}).get('enabled', True):
            logger.warning("La vérification d'intégrité Terraform est désactivée")
            return
        
        terraform_dir = "terraform"
        if not os.path.exists(terraform_dir):
            logger.error(f"Répertoire Terraform non trouvé : {terraform_dir}")
            self.record_violation("terraform", "missing_directory", "Critique", 
                                f"Répertoire Terraform manquant : {terraform_dir}")
            return
        
        # Vérifier la présence des fichiers essentiels
        essential_files = ["main.tf", "variables.tf"]
        missing_files = []
        for file in essential_files:
            file_path = os.path.join(terraform_dir, file)
            if not os.path.exists(file_path):
                missing_files.append(file)
        
        if missing_files:
            logger.error(f"Fichiers Terraform essentiels manquants : {', '.join(missing_files)}")
            self.record_violation("terraform", "missing_files", "Élevée", 
                                f"Fichiers Terraform essentiels manquants : {', '.join(missing_files)}")
        
        # Vérifier l'absence de credentials en clair
        self.check_credentials_exposure(terraform_dir)
        
        # Ajout à la liste des vérifications effectuées
        self.report_data["checks_performed"].append({
            "check": "terraform_integrity",
            "status": "completed",
            "timestamp": datetime.datetime.now().isoformat()
        })
        
        logger.info("Vérification de l'intégrité Terraform terminée")
    
    def verify_kubernetes_integrity(self):
        """Vérifie l'intégrité des fichiers Kubernetes/Helm"""
        logger.info("Vérification de l'intégrité des fichiers Kubernetes/Helm")
        
        if not self.config.get('component_implementation', {}).get('kubernetes', {}).get('integrity_validation', {}).get('enabled', True):
            logger.warning("La vérification d'intégrité Kubernetes est désactivée")
            return
        
        helm_dir = "helm"
        if not os.path.exists(helm_dir):
            logger.error(f"Répertoire Helm non trouvé : {helm_dir}")
            self.record_violation("kubernetes", "missing_directory", "Critique", 
                                f"Répertoire Helm manquant : {helm_dir}")
            return
        
        # Vérifier que les charts Helm requis sont présents
        required_charts = ["app", "fallback-agent", "quantum-optimizer"]
        missing_charts = []
        for chart in required_charts:
            chart_path = os.path.join(helm_dir, chart)
            if not os.path.exists(chart_path):
                missing_charts.append(chart)
        
        if missing_charts:
            logger.error(f"Charts Helm requis manquants : {', '.join(missing_charts)}")
            self.record_violation("kubernetes", "missing_charts", "Élevée", 
                                f"Charts Helm requis manquants : {', '.join(missing_charts)}")
        
        # Vérifier que les déploiements incluent les sondes de santé
        for chart in required_charts:
            if chart not in missing_charts:
                self.verify_health_probes(os.path.join(helm_dir, chart))
        
        # Ajout à la liste des vérifications effectuées
        self.report_data["checks_performed"].append({
            "check": "kubernetes_integrity",
            "status": "completed",
            "timestamp": datetime.datetime.now().isoformat()
        })
        
        logger.info("Vérification de l'intégrité Kubernetes terminée")
    
    def verify_quantum_integrity(self):
        """Vérifie l'intégrité du module d'optimisation quantique"""
        logger.info("Vérification de l'intégrité du module d'optimisation quantique")
        
        if not self.config.get('component_implementation', {}).get('quantum_optimization', {}).get('integrity_validation', {}).get('enabled', True):
            logger.warning("La vérification d'intégrité quantique est désactivée")
            return
        
        quantum_dir = "quantum-sim"
        if not os.path.exists(quantum_dir):
            logger.error(f"Répertoire d'optimisation quantique non trouvé : {quantum_dir}")
            self.record_violation("quantum", "missing_directory", "Critique", 
                                f"Répertoire d'optimisation quantique manquant : {quantum_dir}")
            return
        
        # Vérifier la présence des fichiers essentiels
        essential_files = ["simulate.py", "Dockerfile"]
        missing_files = []
        for file in essential_files:
            file_path = os.path.join(quantum_dir, file)
            if not os.path.exists(file_path):
                missing_files.append(file)
        
        if missing_files:
            logger.error(f"Fichiers d'optimisation quantique essentiels manquants : {', '.join(missing_files)}")
            self.record_violation("quantum", "missing_files", "Élevée", 
                                f"Fichiers d'optimisation quantique essentiels manquants : {', '.join(missing_files)}")
        
        # Vérifier que le module n'utilise pas de simulations fictives
        self.verify_no_fictional_simulations(quantum_dir)
        
        # Ajout à la liste des vérifications effectuées
        self.report_data["checks_performed"].append({
            "check": "quantum_integrity",
            "status": "completed",
            "timestamp": datetime.datetime.now().isoformat()
        })
        
        logger.info("Vérification de l'intégrité quantique terminée")
    
    def verify_fallback_integrity(self):
        """Vérifie l'intégrité de l'agent de fallback"""
        logger.info("Vérification de l'intégrité de l'agent de fallback")
        
        if not self.config.get('component_implementation', {}).get('fallback_agent', {}).get('integrity_validation', {}).get('enabled', True):
            logger.warning("La vérification d'intégrité de l'agent de fallback est désactivée")
            return
        
        fallback_dir = "fallback-agent"
        if not os.path.exists(fallback_dir):
            logger.error(f"Répertoire de l'agent de fallback non trouvé : {fallback_dir}")
            self.record_violation("fallback", "missing_directory", "Critique", 
                                f"Répertoire de l'agent de fallback manquant : {fallback_dir}")
            return
        
        # Vérifier la présence des fichiers essentiels
        essential_files = ["app.py", "Dockerfile"]
        missing_files = []
        for file in essential_files:
            file_path = os.path.join(fallback_dir, file)
            if not os.path.exists(file_path):
                missing_files.append(file)
        
        if missing_files:
            logger.error(f"Fichiers de l'agent de fallback essentiels manquants : {', '.join(missing_files)}")
            self.record_violation("fallback", "missing_files", "Élevée", 
                                f"Fichiers de l'agent de fallback essentiels manquants : {', '.join(missing_files)}")
        
        # Vérifier que l'agent préserve le contexte lors des transitions
        self.verify_context_preservation(fallback_dir)
        
        # Ajout à la liste des vérifications effectuées
        self.report_data["checks_performed"].append({
            "check": "fallback_integrity",
            "status": "completed",
            "timestamp": datetime.datetime.now().isoformat()
        })
        
        logger.info("Vérification de l'intégrité de l'agent de fallback terminée")
    
    def verify_no_fictional_simulations(self, directory=None):
        """Vérifie l'absence de simulations fictives dans le code"""
        if directory:
            logger.info(f"Vérification de l'absence de simulations fictives dans {directory}")
            directories = [directory]
        else:
            logger.info("Vérification de l'absence de simulations fictives dans tout le code")
            directories = ["app", "quantum-sim", "fallback-agent", "scripts", "terraform"]
        
        problematic_patterns = [
            "fake_data", "mock_data", "fictional", "simulated_environment",
            "dummy_data", "faux_data", "donnees_fictives", "simulation_fictive"
        ]
        
        exempted_contexts = [
            "test", "unit_test", "pytest", "unittest", 
            "reproduce", "seed", "for reproducibility",
            "# Simulation autorisée pour l'optimisation quantique"
        ]
        
        violations_found = False
        
        for dir_path in directories:
            if not os.path.exists(dir_path):
                continue
            
            for root, _, files in os.walk(dir_path):
                for file in files:
                    if file.endswith(('.py', '.ipynb', '.js', '.tf', '.sh')):
                        file_path = os.path.join(root, file)
                        try:
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                content = f.read().lower()
                                
                                for pattern in problematic_patterns:
                                    if pattern.lower() in content:
                                        # Vérifier si c'est dans un contexte exempté
                                        is_exempted = False
                                        for context in exempted_contexts:
                                            if context.lower() in content:
                                                is_exempted = True
                                                break
                                        
                                        # Exemption spéciale pour le module quantique
                                        is_quantum_optimization = "quantum" in file_path.lower() and "optimis" in content
                                        
                                        if not is_exempted and not is_quantum_optimization:
                                            logger.error(f"Potentielle simulation fictive dans {file_path} (pattern: {pattern})")
                                            self.record_violation("simulation", "fictional_simulation", "Critique", 
                                                               f"Simulation fictive détectée dans {file_path} (pattern: {pattern})")
                                            violations_found = True
                        except Exception as e:
                            logger.warning(f"Impossible de lire {file_path}: {str(e)}")
        
        if not violations_found:
            logger.info("✅ Aucune simulation fictive détectée")
            self.report_data["checks_performed"].append({
                "check": "no_fictional_simulations",
                "status": "success",
                "timestamp": datetime.datetime.now().isoformat()
            })
    
    def verify_security(self):
        """Vérifie les aspects de sécurité"""
        logger.info("Vérification des aspects de sécurité")
        
        # Vérification du répertoire de sécurité
        security_dir = "security"
        if not os.path.exists(security_dir):
            logger.error(f"Répertoire de sécurité non trouvé : {security_dir}")
            self.record_violation("security", "missing_directory", "Critique", 
                                f"Répertoire de sécurité manquant : {security_dir}")
        
        # Vérification des fichiers de configuration de sécurité
        security_files = [
            os.path.join(security_dir, "istio", "zero-trust-config.yaml"),
            os.path.join(security_dir, "SECRETS_MANAGEMENT.md")
        ]
        
        for file_path in security_files:
            if not os.path.exists(file_path):
                logger.warning(f"Fichier de sécurité manquant : {file_path}")
                self.record_violation("security", "missing_security_file", "Moyenne", 
                                    f"Fichier de sécurité manquant : {file_path}")
        
        # Vérification de l'exposition de credentials dans tout le code
        self.check_credentials_exposure()
        
        # Ajout à la liste des vérifications effectuées
        self.report_data["checks_performed"].append({
            "check": "security",
            "status": "completed",
            "timestamp": datetime.datetime.now().isoformat()
        })
        
        logger.info("Vérification de la sécurité terminée")
    
    def check_credentials_exposure(self, directory=None):
        """Vérifie l'exposition de credentials dans les fichiers"""
        if directory:
            logger.info(f"Vérification de l'exposition de credentials dans {directory}")
            directories = [directory]
        else:
            logger.info("Vérification de l'exposition de credentials dans tout le code")
            directories = ["app", "quantum-sim", "fallback-agent", "scripts", "terraform", "helm"]
        
        patterns = [
            "password", "secret", "key", "token", "credential",
            "ACCESS_KEY", "SECRET_KEY", "API_KEY", "mot_de_passe",
            "clé_secrete", "clé_privée"
        ]
        
        for dir_path in directories:
            if not os.path.exists(dir_path):
                continue
            
            for root, _, files in os.walk(dir_path):
                for file in files:
                    if file.endswith(('.py', '.js', '.sh', '.tf', '.tfvars', '.yaml', '.yml', '.json')):
                        file_path = os.path.join(root, file)
                        try:
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                content = f.read()
                                
                                for pattern in patterns:
                                    if pattern.lower() in content.lower():
                                        # Vérifier si c'est une référence à une variable ou un secret géré
                                        secure_patterns = [
                                            "var.", "secrets.", "vault.", "encrypted", "ssm:", 
                                            "secretsmanager:", "${var", "process.env", "os.environ",
                                            "secret_manager", "keychain", "masked"
                                        ]
                                        
                                        if not any(secure_pattern in content.lower() for secure_pattern in secure_patterns):
                                            # Vérifier si c'est un credential réel (pattern de caractères aléatoires)
                                            credential_patterns = [
                                                r'[A-Za-z0-9+/]{40,}',  # Base64
                                                r'[A-Za-z0-9]{20,}',    # Alphanumeric keys
                                                r'[0-9a-f]{32,}',       # Hex (md5, etc)
                                                r'-----BEGIN .* KEY-----'  # PEM keys
                                            ]
                                            
                                            for cred_pattern in credential_patterns:
                                                if re.search(cred_pattern, content):
                                                    logger.error(f"Exposition de credentials dans {file_path} (pattern: {pattern})")
                                                    self.record_violation("security", "credentials_exposure", "Critique", 
                                                                        f"Credentials exposés dans {file_path} (pattern: {pattern})")
                        except Exception as e:
                            logger.warning(f"Impossible de lire {file_path}: {str(e)}")
    
    def verify_health_probes(self, directory):
        """Vérifie la présence de sondes de santé dans les déploiements Kubernetes"""
        logger.info(f"Vérification des sondes de santé dans {directory}")
        
        # Chemin du répertoire templates
        templates_dir = os.path.join(directory, "templates")
        if not os.path.exists(templates_dir):
            logger.warning(f"Répertoire templates non trouvé : {templates_dir}")
            return
        
        # Rechercher les fichiers de déploiement
        deployment_files = []
        for root, _, files in os.walk(templates_dir):
            for file in files:
                if file.endswith(('.yaml', '.yml')) and ("deployment" in file.lower() or "statefulset" in file.lower()):
                    deployment_files.append(os.path.join(root, file))
        
        if not deployment_files:
            logger.warning(f"Aucun fichier de déploiement trouvé dans {templates_dir}")
            return
        
        for file_path in deployment_files:
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                    
                    # Vérifier si les sondes sont présentes
                    if "livenessProbe" not in content or "readinessProbe" not in content:
                        logger.warning(f"Sondes de santé manquantes dans {file_path}")
                        self.record_violation("kubernetes", "missing_health_probes", "Moyenne", 
                                           f"Sondes de santé (liveness/readiness) manquantes dans {file_path}")
            except Exception as e:
                logger.warning(f"Impossible de lire {file_path}: {str(e)}")
    
    def verify_context_preservation(self, directory):
        """Vérifie la préservation du contexte dans l'agent de fallback"""
        logger.info(f"Vérification de la préservation du contexte dans {directory}")
        
        app_file = os.path.join(directory, "app.py")
        if not os.path.exists(app_file):
            logger.error(f"Fichier principal de l'agent manquant : {app_file}")
            self.record_violation("fallback", "missing_main_file", "Critique", 
                                f"Fichier principal de l'agent manquant : {app_file}")
            return
        
        try:
            with open(app_file, 'r') as f:
                content = f.read().lower()
                
                # Vérifier la présence de fonctionnalités de préservation du contexte
                context_features = {
                    "context storage": "context" in content and ("save" in content or "store" in content),
                    "context restoration": "context" in content and ("restore" in content or "load" in content),
                    "session management": "session" in content,
                    "persistence": "redis" in content or "database" in content or "persist" in content,
                    "transition logging": "transition" in content and "log" in content
                }
                
                missing_features = [feature for feature, present in context_features.items() if not present]
                
                if missing_features:
                    logger.warning(f"Fonctionnalités de préservation du contexte manquantes : {', '.join(missing_features)}")
                    self.record_violation("fallback", "incomplete_context_preservation", "Élevée", 
                                        f"Fonctionnalités de préservation du contexte manquantes : {', '.join(missing_features)}")
                else:
                    logger.info("✅ Préservation du contexte correctement implémentée")
        except Exception as e:
            logger.warning(f"Impossible de lire {app_file}: {str(e)}")
    
    def record_violation(self, component, issue, severity, details=None):
        """Enregistre une violation d'intégrité"""
        self.violation_count += 1
        
        violation = {
            "id": f"VIO-{self.violation_count:04d}",
            "timestamp": datetime.datetime.now().isoformat(),
            "component": component,
            "issue": issue,
            "severity": severity,
            "details": details,
            "verification_id": self.verification_id
        }
        
        logger.error(f"Violation d'intégrité: {violation}")
        
        # Ajout au rapport
        self.report_data["violations"].append(violation)
    
    def generate_report(self):
        """Génère un rapport de vérification d'intégrité"""
        logger.info("Génération du rapport de vérification")
        
        report = {
            "verification_id": self.verification_id,
            "timestamp": self.timestamp,
            "config_version": self.config.get('version'),
            "violations_count": self.violation_count,
            "status": "CONFORME" if self.violation_count == 0 else "NON CONFORME",
            "components_checked": [
                "data_integrity",
                "terraform",
                "kubernetes",
                "quantum_optimization",
                "fallback_agent"
            ],
            "violations": self.report_data["violations"],
            "checks_performed": self.report_data["checks_performed"]
        }
        
        # Calcul d'une empreinte cryptographique du rapport
        report_hash = hashlib.sha256(json.dumps(report, sort_keys=True).encode()).hexdigest()
        report["integrity_hash"] = report_hash
        
        # Enregistrement du rapport
        report_dir = "reports"
        os.makedirs(report_dir, exist_ok=True)
        
        report_path = os.path.join(report_dir, f"integrity_report_{self.verification_id}.json")
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Rapport de vérification enregistré dans {report_path}")
        
        # Création d'un rapport Markdown pour lecture humaine
        report_md_path = os.path.join(report_dir, f"integrity_report_{self.verification_id}.md")
        with open(report_md_path, 'w') as f:
            f.write(f"# Rapport de Vérification d'Intégrité Systémique\n\n")
            f.write(f"ID: `{self.verification_id}`\n\n")
            f.write(f"Date: {self.timestamp}\n\n")
            f.write(f"Statut: **{report['status']}**\n\n")
            f.write(f"Violations: {self.violation_count}\n\n")
            
            if self.violation_count > 0:
                f.write("## Violations Détectées\n\n")
                for violation in self.report_data["violations"]:
                    f.write(f"### {violation['id']} - {violation['component']} ({violation['severity']})\n")
                    f.write(f"Issue: {violation['issue']}\n\n")
                    if violation.get('details'):
                        f.write(f"Détails: {violation['details']}\n\n")
            
            f.write(f"## Composants Vérifiés\n\n")
            for component in report["components_checked"]:
                f.write(f"- {component}\n")
            
            f.write(f"\n## Empreinte d'Intégrité\n\n")
            f.write(f"`{report_hash}`\n")
        
        logger.info(f"Rapport Markdown enregistré dans {report_md_path}")
        
        # Affichage du résumé
        print("\n========== RAPPORT DE VÉRIFICATION D'INTÉGRITÉ ==========")
        print(f"ID: {self.verification_id}")
        print(f"Date: {self.timestamp}")
        print(f"Violations: {self.violation_count}")
        print(f"Statut: {report['status']}")
        print(f"Rapport: {report_path}")
        print("=========================================================\n")
        
        if self.violation_count > 0:
            print("⚠️  DES VIOLATIONS D'INTÉGRITÉ ONT ÉTÉ DÉTECTÉES")
            print("   Consultez le rapport pour plus de détails")
            print("=========================================================\n")


def main():
    """Fonction principale"""
    parser = argparse.ArgumentParser(description="Vérificateur d'intégrité systémique")
    parser.add_argument('--config', default='config/integrity.yaml', help='Chemin vers le fichier de configuration')
    args = parser.parse_args()
    
    # Créer les répertoires nécessaires s'ils n'existent pas
    os.makedirs("reports", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    os.makedirs(os.path.dirname(args.config), exist_ok=True)
    
    # Exécuter le vérificateur d'intégrité
    verifier = IntegrityVerifier(config_path=args.config)
    result = verifier.verify_all()
    
    # Code de retour basé sur le résultat
    sys.exit(0 if result else 1)


if __name__ == "__main__":
    main()
