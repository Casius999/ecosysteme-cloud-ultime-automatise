#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Agent de fallback intelligent pour l'écosystème cloud automatisé.
Assure la continuité des services en cas de défaillance de Claude Desktop.
"""

import os
import sys
import json
import time
import logging
import requests
import redis
from datetime import datetime

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("fallback.log")
    ]
)

logger = logging.getLogger("FallbackAgent")

# Configuration de Redis pour la persistance et la préservation du contexte
REDIS_HOST = os.environ.get('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.environ.get('REDIS_PORT', 6379))
REDIS_DB = int(os.environ.get('REDIS_DB', 0))
REDIS_PASSWORD = os.environ.get('REDIS_PASSWORD', None)

# Configuration des services
CLAUDE_SERVICE_URL = os.environ.get('CLAUDE_SERVICE_URL', 'http://claude-service/v1')
FALLBACK_MODE = os.environ.get('FALLBACK_MODE', 'auto')  # 'auto', 'forced', 'disabled'
FALLBACK_SERVICES = json.loads(os.environ.get('FALLBACK_SERVICES', '["anthropic", "openai"]'))

class FallbackAgent:
    """Agent principal de fallback qui gère la transition entre les services."""
    
    def __init__(self):
        """Initialisation de l'agent de fallback."""
        self.redis_client = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            password=REDIS_PASSWORD
        )
        
        self.fallback_mode = FALLBACK_MODE
        self.active_service = "claude"  # Claude est le service par défaut
        self.fallback_services = FALLBACK_SERVICES
        self.fallback_index = 0
        
        logger.info(f"Agent de fallback initialisé en mode {self.fallback_mode}")
        
        # Vérification initiale du service principal
        self._check_primary_service()
    
    def _check_primary_service(self):
        """Vérifie l'état du service principal (Claude Desktop)."""
        if self.fallback_mode == 'forced':
            # En mode forcé, on bascule directement sur le service de fallback
            self._activate_fallback()
            return
        
        if self.fallback_mode == 'disabled':
            # En mode désactivé, on reste sur le service principal
            self.active_service = "claude"
            return
        
        # En mode auto, on vérifie l'état du service principal
        try:
            response = requests.get(f"{CLAUDE_SERVICE_URL}/health", timeout=5)
            if response.status_code == 200:
                logger.info("Service principal (Claude Desktop) opérationnel")
                self.active_service = "claude"
            else:
                logger.warning(f"Service principal non opérationnel (code: {response.status_code})")
                self._activate_fallback()
        except Exception as e:
            logger.error(f"Erreur lors de la vérification du service principal: {str(e)}")
            self._activate_fallback()
    
    def _activate_fallback(self):
        """Active le service de fallback."""
        if self.fallback_index >= len(self.fallback_services):
            self.fallback_index = 0
        
        self.active_service = self.fallback_services[self.fallback_index]
        logger.info(f"Service de fallback activé: {self.active_service}")
        
        # Préservation du contexte - récupération depuis Redis
        self._restore_context()
    
    def _restore_context(self):
        """Restaure le contexte utilisateur depuis Redis pour assurer la continuité des interactions."""
        logger.info("Restauration du contexte utilisateur")
        
        # Récupération des sessions actives
        active_sessions = self.redis_client.keys("session:*")
        logger.info(f"Sessions actives trouvées: {len(active_sessions)}")
        
        for session_key in active_sessions:
            try:
                session_id = session_key.decode('utf-8').split(':')[1]
                session_data = self.redis_client.get(session_key)
                
                if session_data:
                    session = json.loads(session_data)
                    logger.info(f"Contexte restauré pour la session {session_id}: {len(session.get('history', []))} messages")
                    
                    # Mise à jour du contexte dans le service de fallback
                    self._synchronize_context(session_id, session)
            except Exception as e:
                logger.error(f"Erreur lors de la restauration du contexte pour {session_key}: {str(e)}")
    
    def _synchronize_context(self, session_id, session_data):
        """Synchronise le contexte avec le service de fallback."""
        logger.info(f"Synchronisation du contexte pour la session {session_id} avec {self.active_service}")
        
        # Cette méthode enverrait le contexte au service de fallback
        # Le format exact dépendrait de l'API du service utilisé
        
        # Journalisation de la transition pour audit
        transition_log = {
            "timestamp": datetime.now().isoformat(),
            "session_id": session_id,
            "from_service": "claude",
            "to_service": self.active_service,
            "context_preserved": True,
            "message_count": len(session_data.get("history", [])),
        }
        
        # Enregistrement du log de transition dans Redis pour traçabilité
        self.redis_client.lpush(f"transition_logs:{session_id}", json.dumps(transition_log))
        
        logger.info(f"Transition enregistrée pour audit: {transition_log}")

    def process_request(self, request_data):
        """Traite une requête entrante et la dirige vers le service approprié."""
        session_id = request_data.get("session_id", "unknown")
        logger.info(f"Traitement de la requête pour la session {session_id}")
        
        # Vérification périodique du service principal
        self._check_primary_service()
        
        # Préservation du contexte - sauvegarde dans Redis
        self._save_context(session_id, request_data)
        
        # Transmission de la requête au service actif
        return self._forward_request(request_data)
    
    def _save_context(self, session_id, request_data):
        """Sauvegarde le contexte utilisateur dans Redis."""
        logger.info(f"Sauvegarde du contexte pour la session {session_id}")
        
        # Récupération du contexte existant
        existing_context = self.redis_client.get(f"session:{session_id}")
        if existing_context:
            context = json.loads(existing_context)
        else:
            context = {"history": []}
        
        # Mise à jour du contexte avec la nouvelle requête
        if "message" in request_data:
            context["history"].append({
                "role": "user",
                "content": request_data["message"],
                "timestamp": datetime.now().isoformat()
            })
        
        # Sauvegarde du contexte mis à jour
        self.redis_client.set(f"session:{session_id}", json.dumps(context))
        
        # Configuration de l'expiration (24 heures par défaut)
        self.redis_client.expire(f"session:{session_id}", 86400)
    
    def _forward_request(self, request_data):
        """Transmet la requête au service actif."""
        logger.info(f"Transmission de la requête à {self.active_service}")
        
        # La logique d'appel au service approprié serait implémentée ici
        # Le format exact dépendrait de l'API du service utilisé
        
        response = {
            "service": self.active_service,
            "status": "processed",
            "timestamp": datetime.now().isoformat()
        }
        
        return response

# Si exécuté directement
if __name__ == "__main__":
    agent = FallbackAgent()
    
    # En production, cette partie serait remplacée par un serveur web (Flask, FastAPI, etc.)
    while True:
        logger.info("Agent de fallback en attente...")
        time.sleep(60)
        
        # Vérification périodique de l'état du service principal
        agent._check_primary_service()