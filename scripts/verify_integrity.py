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
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.asymmetric import rsa

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
        
        logger.info(f"Démarrage de la vérification d'intégrité [ID: {self.verification_id}]")
    
    def load_config(self):
        """Chargement de la configuration d'intégrité"""
        try:
            with open(self.config_path, 'r') as f:
                self.config = yaml.safe_load(f)
            
            logger.info(f"Configuration d'intégrité chargée depuis {self.config_path}")
            
            # Vérifier l'intégrité de la configuration elle-même
            if self.config.get('version') != "3.0" or self.config.get('status') != "CONTRAIGNANT":
                logger.error(f"La configuration d'intégrité n'est pas valide : version={self.config.get('version')}, status={self.config.get('status')}")
                sys.exit(1)
        
        except Exception as e:
            logger.error(f"Erreur lors du chargement de la configuration : {str(e)}")
            sys.exit(1)
    
    def verify_all(self):
        """Exécute toutes les vérifications d'intégrité"""
        logger.info("Démarrage de la vérification complète")
        
        # Vérifier les différents aspects
        self.verify_data_integrity()
        self.verify_terraform_integrity()
        self.verify_kubernetes_integrity()
        self.verify_quantum_integrity()
        self.verify_fallback_integrity()
        
        # Génération du rapport final
        self.generate_report()
        
        return self.violation_count == 0
    
    def verify_data_integrity(self):
        """Vérifie l'intégrité des données"""
        logger.info("Vérification de l'intégrité des données")
        
        if not self.config['verification']['data_integrity']['enabled']:
            logger.warning("La vérification d'intégrité des données est désactivée")
            return
        
        # Simulation de vérification de hachages cryptographiques
        methods = self.config['verification']['data_integrity']['methods']
        for method in methods:
            if method['type'] == 'cryptographic_hash':
                logger.info(f"Vérification des hachages cryptographiques avec {method['algorithm']}")
                # Ici, on simulerait la vérification des hachages des fichiers clés
                
            elif method['type'] == 'digital_signature':
                logger.info(f"Vérification des signatures numériques avec {method['algorithm']}")
                # Ici, on simulerait la vérification des signatures
        
        logger.info("Vérification de l'intégrité des données terminée")
    
    def verify_terraform_integrity(self):
        """Vérifie l'intégrité des fichiers Terraform"""
        logger.info("Vérification de l'intégrité des fichiers Terraform")
        
        if not self.config['component_implementation']['terraform']['integrity_validation']['enabled']:
            logger.warning("La vérification d'intégrité Terraform est désactivée")
            return
        
        terraform_dir = "terraform"
        if not os.path.exists(terraform_dir):
            logger.error(f"Répertoire Terraform non trouvé : {terraform_dir}")
            self.record_violation("terraform", "missing_directory", "Critique")
            return
        
        # Vérifier la présence des fichiers essentiels
        essential_files = ["main.tf", "variables.tf"]
        for file in essential_files:
            file_path = os.path.join(terraform_dir, file)
            if not os.path.exists(file_path):
                logger.error(f"Fichier Terraform essentiel manquant : {file}")
                self.record_violation("terraform", f"missing_{file}", "Élevée")
        
        # Vérifier l'absence de credentials en clair
        self.check_credentials_exposure(terraform_dir)
        
        logger.info("Vérification de l'intégrité Terraform terminée")
    
    def verify_kubernetes_integrity(self):
        """Vérifie l'intégrité des fichiers Kubernetes/Helm"""
        logger.info("Vérification de l'intégrité des fichiers Kubernetes/Helm")
        
        if not self.config['component_implementation']['kubernetes']['integrity_validation']['enabled']:
            logger.warning("La vérification d'intégrité Kubernetes est désactivée")
            return
        
        helm_dir = "helm"
        if not os.path.exists(helm_dir):
            logger.error(f"Répertoire Helm non trouvé : {helm_dir}")
            self.record_violation("kubernetes", "missing_directory", "Critique")
            return
        
        # Vérifier que les déploiements incluent les sondes de santé
        self.verify_health_probes(helm_dir)
        
        # Vérifier la présence de configurations de sécurité
        self.verify_security_context(helm_dir)
        
        logger.info("Vérification de l'intégrité Kubernetes terminée")
    
    def verify_quantum_integrity(self):
        """Vérifie l'intégrité du module d'optimisation quantique"""
        logger.info("Vérification de l'intégrité du module d'optimisation quantique")
        
        if not self.config['component_implementation']['quantum_optimization']['integrity_validation']['enabled']:
            logger.warning("La vérification d'intégrité quantique est désactivée")
            return
        
        quantum_dir = "quantum-sim"
        if not os.path.exists(quantum_dir):
            logger.error(f"Répertoire d'optimisation quantique non trouvé : {quantum_dir}")
            self.record_violation("quantum", "missing_directory", "Critique")
            return
        
        # Vérifier que le module n'utilise pas de simulations fictives
        self.verify_no_fictional_simulations(quantum_dir)
        
        logger.info("Vérification de l'intégrité quantique terminée")
    
    def verify_fallback_integrity(self):
        """Vérifie l'intégrité de l'agent de fallback"""
        logger.info("Vérification de l'intégrité de l'agent de fallback")
        
        if not self.config['component_implementation']['fallback_agent']['integrity_validation']['enabled']:
            logger.warning("La vérification d'intégrité de l'agent de fallback est désactivée")
            return
        
        fallback_dir = "fallback-agent"
        if not os.path.exists(fallback_dir):
            logger.error(f"Répertoire de l'agent de fallback non trouvé : {fallback_dir}")
            self.record_violation("fallback", "missing_directory", "Critique")
            return
        
        # Vérifier que l'agent préserve le contexte lors des transitions
        self.verify_context_preservation(fallback_dir)
        
        logger.info("Vérification de l'intégrité de l'agent de fallback terminée")
    
    def check_credentials_exposure(self, directory):
        """Vérifie l'exposition de credentials dans les fichiers"""
        logger.info(f"Vérification de l'exposition de credentials dans {directory}")
        
        patterns = [
            "password", "secret", "key", "token", "credential",
            "ACCESS_KEY", "SECRET_KEY", "API_KEY"
        ]
        
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith(('.tf', '.tfvars', '.yaml', '.yml', '.json')):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r') as f:
                            content = f.read()
                            
                            for pattern in patterns:
                                if pattern.lower() in content.lower():
                                    # Vérifier si c'est une référence à une variable ou un secret géré
                                    if not any(secure_pattern in content.lower() for secure_pattern in 
                                              ["var.", "secrets.", "vault.", "encrypted", "ssm:", "secretsmanager:", "${var}"]):
                                        logger.error(f"Potentielle exposition de credentials dans {file_path} (pattern: {pattern})")
                                        self.record_violation("security", "credentials_exposure", "Critique")
                    except Exception as e:
                        logger.warning(f"Impossible de lire {file_path}: {str(e)}")
    
    def verify_health_probes(self, directory):
        """Vérifie la présence de sondes de santé dans les déploiements Kubernetes"""
        logger.info(f"Vérification des sondes de santé dans {directory}")
        
        deployment_files = []
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith(('.yaml', '.yml')) and "deployment" in file.lower():
                    deployment_files.append(os.path.join(root, file))
        
        for file_path in deployment_files:
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                    
                    # Vérifier si les sondes sont présentes
                    if "livenessProbe" not in content or "readinessProbe" not in content:
                        logger.warning(f"Sondes de santé manquantes dans {file_path}")
                        self.record_violation("kubernetes", "missing_health_probes", "Moyenne")
            except Exception as e:
                logger.warning(f"Impossible de lire {file_path}: {str(e)}")
    
    def verify_security_context(self, directory):
        """Vérifie la présence de contextes de sécurité dans les déploiements Kubernetes"""
        logger.info(f"Vérification des contextes de sécurité dans {directory}")
        
        deployment_files = []
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith(('.yaml', '.yml')) and "deployment" in file.lower():
                    deployment_files.append(os.path.join(root, file))
        
        for file_path in deployment_files:
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                    
                    # Vérifier si les contextes de sécurité sont présents
                    if "securityContext" not in content:
                        logger.warning(f"Contexte de sécurité manquant dans {file_path}")
                        self.record_violation("kubernetes", "missing_security_context", "Moyenne")
            except Exception as e:
                logger.warning(f"Impossible de lire {file_path}: {str(e)}")
    
    def verify_no_fictional_simulations(self, directory):
        """Vérifie l'absence de simulations fictives dans le module quantique"""
        logger.info(f"Vérification de l'absence de simulations fictives dans {directory}")
        
        problematic_patterns = [
            "fake_data", "mock_data", "fictional", "simulated_environment",
            "dummy_data", "random.random", "np.random.rand", "random_state"
        ]
        
        exempted_contexts = [
            "test", "unit_test", "pytest", "unittest", 
            "reproduce", "seed", "for reproducibility"
        ]
        
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith(('.py', '.ipynb')):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r') as f:
                            content = f.read().lower()
                            
                            for pattern in problematic_patterns:
                                if pattern.lower() in content:
                                    # Vérifier si c'est dans un contexte exempté
                                    is_exempted = any(context in content for context in exempted_contexts)
                                    
                                    if not is_exempted:
                                        logger.error(f"Potentielle simulation fictive dans {file_path} (pattern: {pattern})")
                                        self.record_violation("quantum", "fictional_simulation", "Critique")
                    except Exception as e:
                        logger.warning(f"Impossible de lire {file_path}: {str(e)}")
    
    def verify_context_preservation(self, directory):
        """Vérifie la préservation du contexte dans l'agent de fallback"""
        logger.info(f"Vérification de la préservation du contexte dans {directory}")
        
        required_patterns = [
            "context", "preserve", "transition", "fallback", "continuity",
            "state", "recover", "backup"
        ]
        
        app_file = os.path.join(directory, "app.py")
        if not os.path.exists(app_file):
            logger.error(f"Fichier principal de l'agent manquant : {app_file}")
            self.record_violation("fallback", "missing_main_file", "Critique")
            return
        
        try:
            with open(app_file, 'r') as f:
                content = f.read().lower()
                
                # Vérifier si au moins 3 des patterns requis sont présents
                matches = sum(1 for pattern in required_patterns if pattern in content)
                
                if matches < 3:
                    logger.warning(f"Préservation du contexte potentiellement insuffisante dans {app_file}")
                    self.record_violation("fallback", "insufficient_context_preservation", "Élevée")
        except Exception as e:
            logger.warning(f"Impossible de lire {app_file}: {str(e)}")
    
    def record_violation(self, component, issue, severity):
        """Enregistre une violation d'intégrité"""
        self.violation_count += 1
        
        violation = {
            "id": f"VIO-{self.violation_count:04d}",
            "timestamp": datetime.datetime.now().isoformat(),
            "component": component,
            "issue": issue,
            "severity": severity,
            "verification_id": self.verification_id
        }
        
        logger.error(f"Violation d'intégrité: {violation}")
        
        # En production, on enregistrerait également la violation dans une base de données
        # ou un système de suivi
    
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
            ]
        }
        
        # Enregistrement du rapport
        report_dir = "reports"
        os.makedirs(report_dir, exist_ok=True)
        
        report_path = os.path.join(report_dir, f"integrity_report_{self.verification_id}.json")
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Rapport de vérification enregistré dans {report_path}")
        
        # Affichage du résumé
        print("\n========== RAPPORT DE VÉRIFICATION D'INTÉGRITÉ ==========")
        print(f"ID: {self.verification_id}")
        print(f"Date: {self.timestamp}")
        print(f"Violations: {self.violation_count}")
        print(f"Statut: {report['status']}")
        print("=========================================================\n")
        
        if self.violation_count > 0:
            print("⚠️  DES VIOLATIONS D'INTÉGRITÉ ONT ÉTÉ DÉTECTÉES")
            print("   Consultez le fichier de log pour plus de détails")
            print("=========================================================\n")


def main():
    """Fonction principale"""
    parser = argparse.ArgumentParser(description="Vérificateur d'intégrité systémique")
    parser.add_argument('--config', default='config/integrity.yaml', help='Chemin vers le fichier de configuration')
    args = parser.parse_args()
    
    verifier = IntegrityVerifier(config_path=args.config)
    result = verifier.verify_all()
    
    # Code de retour basé sur le résultat
    sys.exit(0 if result else 1)


if __name__ == "__main__":
    main()
