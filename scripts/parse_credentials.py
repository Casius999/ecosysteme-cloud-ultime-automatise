#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script pour extraire les variables d'environnement depuis le fichier de credentials YAML
Ce script lit le fichier credentials.yaml et produit des variables d'environnement
au format shell qui peuvent être utilisées par d'autres scripts.
"""

import os
import sys
import yaml
import logging
from pathlib import Path

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("credential_parsing.log")
    ]
)

logger = logging.getLogger("CredentialParser")

def flatten_dict(d, parent_key='', sep='_'):
    """
    Aplatit un dictionnaire imbriqué en un dictionnaire à un seul niveau.
    
    Args:
        d (dict): Le dictionnaire à aplatir
        parent_key (str): La clé parente (utilisée pour la récursion)
        sep (str): Le séparateur entre les niveaux de clés
        
    Returns:
        dict: Un dictionnaire aplati
    """
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)

def generate_env_vars(yaml_file='config/credentials.yaml'):
    """
    Génère des variables d'environnement à partir d'un fichier YAML.
    
    Args:
        yaml_file (str): Chemin vers le fichier YAML
        
    Returns:
        str: Variables d'environnement au format shell
    """
    try:
        # Vérifier que le fichier existe
        if not os.path.exists(yaml_file):
            logger.error(f"Le fichier {yaml_file} n'existe pas.")
            return ""
        
        # Charger le contenu YAML
        with open(yaml_file, 'r') as f:
            config = yaml.safe_load(f)
        
        if not config:
            logger.error(f"Le fichier {yaml_file} est vide ou mal formaté.")
            return ""
        
        # Aplatir le dictionnaire imbriqué
        flattened_config = flatten_dict(config)
        
        # Convertir en variables d'environnement
        env_vars = []
        for key, value in flattened_config.items():
            # Créer une clé compatible avec les variables d'environnement shell
            env_key = key.upper().replace('-', '_')
            
            # Formater la valeur en fonction de son type
            if isinstance(value, (int, float)):
                env_var = f"{env_key}={value}"
            elif isinstance(value, bool):
                env_var = f"{env_key}={'true' if value else 'false'}"
            elif isinstance(value, str):
                # Échapper les caractères spéciaux pour le shell
                escaped_value = value.replace('"', '\\"').replace('$', '\\$')
                env_var = f"{env_key}=\"{escaped_value}\""
            else:
                # Ignorer les types non supportés
                logger.warning(f"Type non supporté pour la clé {key}: {type(value)}")
                continue
            
            env_vars.append(env_var)
        
        # Journalisation
        logger.info(f"Extraction réussie de {len(env_vars)} variables d'environnement depuis {yaml_file}")
        
        # Retourner les variables d'environnement au format shell
        return "\n".join(env_vars)
    
    except Exception as e:
        logger.error(f"Erreur lors de la génération des variables d'environnement: {str(e)}")
        return ""

def main():
    """Fonction principale"""
    # Par défaut, utiliser le fichier credentials.yaml dans le répertoire config
    default_yaml_file = 'config/credentials.yaml'
    
    # Permettre de spécifier un fichier différent via l'argument de ligne de commande
    yaml_file = sys.argv[1] if len(sys.argv) > 1 else default_yaml_file
    
    # Générer et afficher les variables d'environnement
    env_vars = generate_env_vars(yaml_file)
    print(env_vars)

if __name__ == "__main__":
    main()
