#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script de parsing du fichier credentials.yaml pour l'exportation
des variables d'environnement nécessaires au déploiement.
"""

import os
import sys
import yaml


def parse_credentials_file(file_path):
    """
    Analyse le fichier de credentials et génère les variables d'environnement.
    
    Args:
        file_path (str): Chemin vers le fichier de credentials YAML
        
    Returns:
        str: Variables d'environnement formatées pour export shell
    """
    try:
        with open(file_path, 'r') as f:
            config = yaml.safe_load(f)
        
        env_vars = []
        
        # AWS
        if 'aws' in config:
            env_vars.append(f"AWS_ACCESS_KEY_ID={config['aws']['access_key_id']}")
            env_vars.append(f"AWS_SECRET_ACCESS_KEY={config['aws']['secret_access_key']}")
            env_vars.append(f"AWS_REGION={config['aws']['region']}")
        
        # GCP
        if 'gcp' in config:
            env_vars.append(f"GCP_PROJECT_ID={config['gcp']['project_id']}")
            env_vars.append(f"GOOGLE_APPLICATION_CREDENTIALS={config['gcp']['service_account_key_path']}")
            env_vars.append(f"GCP_REGION={config['gcp']['region']}")
        
        # Azure
        if 'azure' in config:
            env_vars.append(f"AZURE_SUBSCRIPTION_ID={config['azure']['subscription_id']}")
            env_vars.append(f"AZURE_TENANT_ID={config['azure']['tenant_id']}")
            env_vars.append(f"AZURE_CLIENT_ID={config['azure']['client_id']}")
            env_vars.append(f"AZURE_CLIENT_SECRET={config['azure']['client_secret']}")
            env_vars.append(f"AZURE_LOCATION={config['azure']['location']}")
        
        # LLM APIs
        if 'llm' in config:
            if 'anthropic_api_key' in config['llm']:
                env_vars.append(f"ANTHROPIC_API_KEY={config['llm']['anthropic_api_key']}")
            if 'openai_api_key' in config['llm']:
                env_vars.append(f"OPENAI_API_KEY={config['llm']['openai_api_key']}")
        
        # Docker Hub
        if 'docker' in config:
            env_vars.append(f"DOCKER_USERNAME={config['docker']['username']}")
            env_vars.append(f"DOCKER_PASSWORD={config['docker']['password']}")
            env_vars.append(f"DOCKER_EMAIL={config['docker']['email']}")
        
        # Network
        if 'network' in config:
            if 'aws_vpc_cidr' in config['network']:
                env_vars.append(f"AWS_VPC_CIDR={config['network']['aws_vpc_cidr']}")
            if 'azure_vnet_cidr' in config['network']:
                env_vars.append(f"AZURE_VNET_CIDR={config['network']['azure_vnet_cidr']}")
        
        # Cluster configurations
        if 'cluster' in config:
            for provider, settings in config['cluster'].items():
                for key, value in settings.items():
                    env_name = f"{provider.upper()}_{key.upper()}"
                    env_vars.append(f"{env_name}={value}")
        
        return " ".join(env_vars)
        
    except Exception as e:
        print(f"ERREUR lors du parsing du fichier de credentials: {str(e)}", file=sys.stderr)
        return ""


if __name__ == "__main__":
    credentials_file = 'config/credentials.yaml'
    
    if len(sys.argv) > 1:
        credentials_file = sys.argv[1]
    
    formatted_vars = parse_credentials_file(credentials_file)
    print(formatted_vars)
