#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Agent de substitution (fallback) pour Claude Desktop
Ce service permet de remplacer automatiquement Claude Desktop 3.7 Sonnet
en cas de défaillance ou de limitation, en redirigeant les requêtes
vers d'autres LLMs tout en maintenant la compatibilité.
"""

import os
import sys
import time
import json
import logging
import yaml
import httpx
import redis
import uuid
from typing import Dict, List, Optional, Any, Union
from fastapi import FastAPI, Request, Response, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from prometheus_client import start_http_server, Counter, Gauge, Histogram
import anthropic
import openai
from tenacity import retry, stop_after_attempt, wait_exponential

# Import des modules internes
from models import Message, Conversation, FallbackRequest, FallbackResponse
from api import router as api_router
from utils import setup_logging, load_config, validate_token

# Configuration du logging
logger = setup_logging()

# Configuration de l'application
config = load_config('config.yaml')

# Configuration des clients d'API
anthropic_client = None
openai_client = None

# Métriques Prometheus
FALLBACK_ACTIVATIONS = Counter('fallback_activations_total', 'Nombre total d'activations du fallback')
CLAUDE_HEALTH_CHECKS = Counter('claude_health_checks_total', 'Nombre total de vérifications de santé de Claude')
CLAUDE_FAILURES = Counter('claude_failures_total', 'Nombre total de défaillances de Claude détectées')
REQUEST_LATENCY = Histogram('fallback_request_latency_seconds', 'Latence des requêtes de fallback')
ACTIVE_FALLBACKS = Gauge('active_fallbacks', 'Nombre de fallbacks actuellement actifs')

# Initialisation de FastAPI
app = FastAPI(
    title="Claude Fallback Agent",
    description="Agent de substitution pour Claude Desktop 3.7 Sonnet",
    version="1.0.0"
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclusion du router API
app.include_router(api_router, prefix="/api")

# Connexion Redis si configurée
redis_client = None
redis_url = os.environ.get('REDIS_URL')
if redis_url:
    try:
        redis_client = redis.from_url(redis_url)
        logger.info(f"Connexion Redis établie: {redis_url}")
    except Exception as e:
        logger.warning(f"Impossible de se connecter à Redis: {str(e)}")

@app.on_event("startup")
async def startup_event():
    """Initialisation au démarrage de l'application."""
    global anthropic_client, openai_client
    
    # Démarrer le serveur Prometheus
    prometheus_port = int(os.environ.get('PROMETHEUS_PORT', 8000))
    start_http_server(prometheus_port)
    logger.info(f"Serveur Prometheus démarré sur le port {prometheus_port}")
    
    # Initialiser le client Anthropic si la clé est présente
    anthropic_api_key = os.environ.get('ANTHROPIC_API_KEY')
    if anthropic_api_key:
        anthropic_client = anthropic.Anthropic(api_key=anthropic_api_key)
        logger.info("Client Anthropic initialisé")
    
    # Initialiser le client OpenAI si la clé est présente
    openai_api_key = os.environ.get('OPENAI_API_KEY')
    if openai_api_key:
        openai_client = openai.OpenAI(api_key=openai_api_key)
        logger.info("Client OpenAI initialisé")
    
    # Vérifier que nous avons au moins un client
    if not anthropic_client and not openai_client:
        logger.warning("Aucun client LLM initialisé. Configurez ANTHROPIC_API_KEY ou OPENAI_API_KEY")
    
    # Vérifier la santé de Claude au démarrage
    await check_claude_health()
    
    logger.info("Agent de fallback démarré et prêt")

@app.get("/health")
async def health_check():
    """Endpoint de vérification de santé."""
    return {"status": "OK", "version": "1.0.0"}

@app.get("/status")
async def status():
    """Obtenir le statut de l'agent de fallback."""
    claude_status = "UNKNOWN"
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{os.environ.get('CLAUDE_ENDPOINT', 'http://claude-service:8080')}/health")
            if response.status_code == 200:
                claude_status = "UP"
            else:
                claude_status = "DOWN"
    except Exception:
        claude_status = "DOWN"
    
    return {
        "status": "OK",
        "claude_status": claude_status,
        "fallback_mode": os.environ.get('FALLBACK_MODE', 'auto'),
        "model_preference": os.environ.get('MODEL_PREFERENCE', 'anthropic'),
        "anthropic_available": anthropic_client is not None,
        "openai_available": openai_client is not None,
        "redis_available": redis_client is not None,
    }

@app.post("/api/v1/messages")
async def handle_messages(request: FallbackRequest, background_tasks: BackgroundTasks):
    """
    Point d'entrée principal pour les requêtes de messages.
    Ce handler tentera d'abord de rediriger vers Claude, puis passera en fallback si nécessaire.
    """
    request_id = str(uuid.uuid4())
    logger.info(f"Requête reçue [ID: {request_id}]")
    
    # Vérifier le statut de Claude
    claude_status = await check_claude_health()
    
    # Mode de fallback
    fallback_mode = os.environ.get('FALLBACK_MODE', 'auto')
    
    # Si Claude est disponible et que nous ne sommes pas en mode forcé
    if claude_status == "UP" and fallback_mode != "forced":
        try:
            logger.info(f"Tentative de transfert vers Claude [ID: {request_id}]")
            
            # Redirection vers Claude
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{os.environ.get('CLAUDE_ENDPOINT', 'http://claude-service:8080')}/api/v1/messages",
                    json=request.dict(),
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    logger.info(f"Réponse de Claude reçue avec succès [ID: {request_id}]")
                    return Response(content=response.content, media_type="application/json")
        except Exception as e:
            logger.error(f"Erreur lors de la communication avec Claude: {str(e)} [ID: {request_id}]")
    
    # Si nous arrivons ici, c'est que Claude n'est pas disponible ou a échoué
    if claude_status == "DOWN" or fallback_mode == "forced":
        FALLBACK_ACTIVATIONS.inc()
        ACTIVE_FALLBACKS.inc()
        
        logger.info(f"Activation du fallback [ID: {request_id}]")
        
        # Stocker la conversation dans Redis si disponible
        if redis_client:
            try:
                redis_client.setex(
                    f"fallback:conversation:{request_id}",
                    3600,  # TTL: 1 heure
                    json.dumps(request.dict())
                )
                logger.debug(f"Conversation stockée dans Redis [ID: {request_id}]")
            except Exception as e:
                logger.warning(f"Impossible de stocker la conversation dans Redis: {str(e)} [ID: {request_id}]")
        
        # Traiter la requête avec le LLM alternatif
        try:
            with REQUEST_LATENCY.time():
                response = await process_fallback(request)
            
            # Planifier la décrémentation du compteur de fallbacks actifs
            background_tasks.add_task(decrement_active_fallbacks)
            
            logger.info(f"Fallback traité avec succès [ID: {request_id}]")
            return response
        
        except Exception as e:
            ACTIVE_FALLBACKS.dec()
            logger.error(f"Erreur lors du traitement du fallback: {str(e)} [ID: {request_id}]")
            raise HTTPException(status_code=500, detail=f"Erreur de fallback: {str(e)}")
    
    # Si nous arrivons ici, c'est que quelque chose d'imprévu s'est produit
    logger.error(f"Situation inattendue dans le traitement de la requête [ID: {request_id}]")
    raise HTTPException(status_code=500, detail="Erreur inattendue dans le traitement de la requête")

async def check_claude_health() -> str:
    """
    Vérifie la santé de Claude et retourne son statut.
    
    Returns:
        str: "UP" si Claude est disponible, "DOWN" sinon
    """
    CLAUDE_HEALTH_CHECKS.inc()
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{os.environ.get('CLAUDE_ENDPOINT', 'http://claude-service:8080')}/health")
            if response.status_code == 200:
                return "UP"
    except Exception as e:
        logger.warning(f"Erreur lors de la vérification de santé de Claude: {str(e)}")
        CLAUDE_FAILURES.inc()
    
    return "DOWN"

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def process_fallback(request: FallbackRequest) -> FallbackResponse:
    """
    Traite une requête de fallback en utilisant un LLM alternatif.
    
    Args:
        request: Requête à traiter
    
    Returns:
        FallbackResponse: Réponse du LLM alternatif
    """
    model_preference = os.environ.get('MODEL_PREFERENCE', 'anthropic')
    
    # Convertir la requête au format du LLM choisi
    if model_preference == 'anthropic' and anthropic_client:
        return await process_with_anthropic(request)
    elif model_preference == 'openai' and openai_client:
        return await process_with_openai(request)
    elif anthropic_client:
        return await process_with_anthropic(request)
    elif openai_client:
        return await process_with_openai(request)
    else:
        logger.error("Aucun client LLM disponible pour le fallback")
        raise Exception("Aucun client LLM disponible pour le fallback")

async def process_with_anthropic(request: FallbackRequest) -> FallbackResponse:
    """
    Traite une requête avec l'API Anthropic.
    """
    logger.info("Traitement de la requête avec Anthropic")
    
    # Convertir les messages au format Anthropic
    messages = []
    for msg in request.messages:
        role = "user" if msg.role == "user" else "assistant"
        messages.append({"role": role, "content": msg.content})
    
    # Paramètres système si présents
    system = request.system if hasattr(request, 'system') and request.system else None
    
    # Appel API
    try:
        response = anthropic_client.messages.create(
            model="claude-3-opus-20240229",  # Utiliser le meilleur modèle disponible
            messages=messages,
            system=system,
            max_tokens=request.max_tokens if hasattr(request, 'max_tokens') else 4096,
            temperature=request.temperature if hasattr(request, 'temperature') else 0.7
        )
        
        # Formater la réponse
        return FallbackResponse(
            id=response.id,
            model=response.model,
            content=response.content[0].text,
            stop_reason=response.stop_reason,
            stop_sequence=response.stop_sequence,
            usage={
                "prompt_tokens": response.usage.input_tokens,
                "completion_tokens": response.usage.output_tokens,
                "total_tokens": response.usage.input_tokens + response.usage.output_tokens
            }
        )
    except Exception as e:
        logger.error(f"Erreur Anthropic: {str(e)}")
        raise

async def process_with_openai(request: FallbackRequest) -> FallbackResponse:
    """
    Traite une requête avec l'API OpenAI.
    """
    logger.info("Traitement de la requête avec OpenAI")
    
    # Convertir les messages au format OpenAI
    messages = []
    
    # Ajouter le message système si présent
    if hasattr(request, 'system') and request.system:
        messages.append({"role": "system", "content": request.system})
    
    # Ajouter les autres messages
    for msg in request.messages:
        role = "user" if msg.role == "user" else "assistant"
        messages.append({"role": role, "content": msg.content})
    
    # Appel API
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4-turbo",  # Utiliser le meilleur modèle disponible
            messages=messages,
            max_tokens=request.max_tokens if hasattr(request, 'max_tokens') else 4096,
            temperature=request.temperature if hasattr(request, 'temperature') else 0.7
        )
        
        # Formater la réponse
        return FallbackResponse(
            id=response.id,
            model=response.model,
            content=response.choices[0].message.content,
            stop_reason=response.choices[0].finish_reason,
            stop_sequence=None,
            usage={
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
        )
    except Exception as e:
        logger.error(f"Erreur OpenAI: {str(e)}")
        raise

def decrement_active_fallbacks():
    """Décrémente le compteur de fallbacks actifs."""
    ACTIVE_FALLBACKS.dec()

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=False)
