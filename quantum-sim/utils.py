#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Fonctions utilitaires pour le module d'optimisation quantique.
"""

import os
import json
import logging
import yaml
from datetime import datetime


def setup_logging(log_level=None):
    """
    Configure le système de logging.
    
    Args:
        log_level: Niveau de logging (optionnel, par défaut: INFO)
    
    Returns:
        logging.Logger: Logger configuré
    """
    if log_level is None:
        log_level = os.environ.get('LOG_LEVEL', 'INFO').upper()
    
    # Convertir le niveau de log
    numeric_level = getattr(logging, log_level, None)
    if not isinstance(numeric_level, int):
        raise ValueError(f'Niveau de log invalide: {log_level}')
    
    # Configurer le formatteur
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'
    
    # Configurer le handler pour la sortie console
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(log_format, date_format))
    
    # Configurer le logger principal
    logger = logging.getLogger()
    logger.setLevel(numeric_level)
    
    # Supprimer les handlers existants
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    logger.addHandler(console_handler)
    
    # Configurer également un fichier de log si le chemin est spécifié
    log_file = os.environ.get('LOG_FILE')
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter(log_format, date_format))
        logger.addHandler(file_handler)
    
    return logger


def load_config(config_path):
    """
    Charge un fichier de configuration YAML.
    
    Args:
        config_path: Chemin vers le fichier de configuration
    
    Returns:
        dict: Configuration chargée
    """
    try:
        with open(config_path, 'r') as file:
            config = yaml.safe_load(file)
        return config
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Erreur lors du chargement de la configuration: {str(e)}")
        logger.info("Utilisation de la configuration par défaut")
        return {}


def save_results(results, output_file):
    """
    Sauvegarde les résultats de la simulation dans un fichier JSON.
    
    Args:
        results: Résultats à sauvegarder
        output_file: Chemin du fichier de sortie
    """
    # Créer le répertoire de sortie s'il n'existe pas
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    try:
        with open(output_file, 'w') as file:
            json.dump(results, file, indent=2)
        
        logger = logging.getLogger(__name__)
        logger.info(f"Résultats sauvegardés dans {output_file}")
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Erreur lors de la sauvegarde des résultats: {str(e)}")


def get_execution_id():
    """
    Génère un identifiant unique pour l'exécution en cours.
    
    Returns:
        str: Identifiant d'exécution
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    random_suffix = os.urandom(2).hex()
    return f"exec_{timestamp}_{random_suffix}"


def parse_simulation_params(params_str):
    """
    Parse une chaîne de paramètres de simulation.
    
    Args:
        params_str: Chaîne JSON des paramètres
    
    Returns:
        dict: Paramètres parsés
    """
    logger = logging.getLogger(__name__)
    
    try:
        if not params_str:
            return {}
        
        params = json.loads(params_str)
        return params
    except json.JSONDecodeError as e:
        logger.error(f"Erreur lors du parsing des paramètres: {str(e)}")
        return {}


def format_quantum_state(state_vector, num_qubits):
    """
    Formate un vecteur d'état quantique pour l'affichage.
    
    Args:
        state_vector: Vecteur d'état quantique
        num_qubits: Nombre de qubits
    
    Returns:
        str: Représentation formatée
    """
    output = "État quantique:\n"
    
    # Trouver les états avec des amplitudes significatives
    for i, amplitude in enumerate(state_vector):
        if abs(amplitude) > 0.001:  # Seuil pour filtrer les petites amplitudes
            # Convertir l'index en une représentation binaire
            binary = format(i, f'0{num_qubits}b')
            # Ajouter à la sortie
            output += f"|{binary}⟩: {amplitude:.4f}\n"
    
    return output


def calculate_metrics(results):
    """
    Calcule des métriques supplémentaires à partir des résultats.
    
    Args:
        results: Résultats de la simulation
    
    Returns:
        dict: Métriques calculées
    """
    metrics = {}
    
    if "optimization_score" in results:
        # Normaliser le score d'optimisation sur une échelle de 0 à 100
        raw_score = results["optimization_score"]
        normalized_score = min(max(raw_score * 10, 0), 100)
        metrics["normalized_score"] = normalized_score
    
    if "resource_savings" in results:
        # Calculer le retour sur investissement basé sur les économies
        savings_percent = results["resource_savings"]
        roi = savings_percent / 100 * 1.5  # Facteur ROI hypothétique
        metrics["estimated_roi"] = roi
    
    return metrics


def validate_solution(solution, constraints):
    """
    Valide si une solution respecte les contraintes.
    
    Args:
        solution: Solution à valider
        constraints: Liste de contraintes
    
    Returns:
        bool: True si toutes les contraintes sont respectées
    """
    logger = logging.getLogger(__name__)
    
    for constraint in constraints:
        constraint_type = constraint.get("type")
        
        if constraint_type == "max_resources":
            # Vérifier si les ressources utilisées ne dépassent pas le maximum
            resource_type = constraint.get("resource")
            max_value = constraint.get("max")
            
            if resource_type and max_value is not None:
                used_value = sum(solution.get("allocations", {}).get(resource_type, []))
                
                if used_value > max_value:
                    logger.warning(f"Contrainte violée: {resource_type} utilisé ({used_value}) > maximum ({max_value})")
                    return False
        
        elif constraint_type == "min_performance":
            # Vérifier si la performance est au moins égale au minimum requis
            min_value = constraint.get("min")
            performance = solution.get("performance", 0)
            
            if min_value is not None and performance < min_value:
                logger.warning(f"Contrainte violée: Performance ({performance}) < minimum requis ({min_value})")
                return False
    
    return True


def serialize_complex(obj):
    """
    Fonction d'aide pour sérialiser des objets contenant des nombres complexes.
    
    Args:
        obj: Objet à sérialiser
    
    Returns:
        object: Objet sérialisable
    """
    if isinstance(obj, complex):
        return (obj.real, obj.imag)
    elif isinstance(obj, list):
        return [serialize_complex(item) for item in obj]
    elif isinstance(obj, dict):
        return {key: serialize_complex(value) for key, value in obj.items()}
    else:
        return obj
