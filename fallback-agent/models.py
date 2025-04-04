#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Modèles de données pour l'agent de fallback.
Ces modèles définissent les structures de requêtes et de réponses
compatibles avec l'API Claude Desktop.
"""

from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field


class Message(BaseModel):
    """
    Un message dans une conversation avec Claude.
    """
    role: str = Field(..., description="Rôle de l'auteur du message (user ou assistant)")
    content: str = Field(..., description="Contenu textuel du message")


class Conversation(BaseModel):
    """
    Une conversation complète avec Claude.
    """
    id: Optional[str] = Field(None, description="Identifiant unique de la conversation")
    messages: List[Message] = Field(default_factory=list, description="Liste des messages")
    system: Optional[str] = Field(None, description="Message système pour contexte")


class FallbackRequest(BaseModel):
    """
    Requête de traitement pour l'agent de fallback.
    Compatible avec le format d'API de Claude Desktop.
    """
    messages: List[Message] = Field(..., description="Liste des messages de la conversation")
    system: Optional[str] = Field(None, description="Message système optionnel")
    max_tokens: Optional[int] = Field(4096, description="Nombre maximal de tokens à générer")
    temperature: Optional[float] = Field(0.7, description="Température pour la génération")
    top_p: Optional[float] = Field(0.9, description="Paramètre top_p pour la génération")
    top_k: Optional[int] = Field(None, description="Paramètre top_k pour la génération")
    stop_sequences: Optional[List[str]] = Field(None, description="Séquences pour arrêter la génération")
    stream: Optional[bool] = Field(False, description="Activer le streaming de la réponse")
    model: Optional[str] = Field("claude-3-sonnet-20240229", description="Modèle à utiliser")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Métadonnées additionnelles")


class UsageInfo(BaseModel):
    """
    Informations sur l'utilisation des tokens.
    """
    prompt_tokens: int = Field(..., description="Nombre de tokens dans le prompt")
    completion_tokens: int = Field(..., description="Nombre de tokens dans la complétion")
    total_tokens: int = Field(..., description="Nombre total de tokens")


class FallbackResponse(BaseModel):
    """
    Réponse de l'agent de fallback.
    Compatible avec le format d'API de Claude Desktop.
    """
    id: str = Field(..., description="Identifiant unique de la réponse")
    model: str = Field(..., description="Modèle utilisé pour la génération")
    content: str = Field(..., description="Contenu de la réponse générée")
    stop_reason: Optional[str] = Field(None, description="Raison de l'arrêt de la génération")
    stop_sequence: Optional[str] = Field(None, description="Séquence qui a causé l'arrêt")
    usage: UsageInfo = Field(..., description="Informations sur l'utilisation des tokens")
    type: str = Field("message", description="Type de la réponse")
    role: str = Field("assistant", description="Rôle de l'auteur du message")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Métadonnées additionnelles")


class HealthResponse(BaseModel):
    """
    Réponse pour les vérifications de santé.
    """
    status: str = Field(..., description="Statut du service (OK ou ERROR)")
    version: str = Field(..., description="Version de l'agent de fallback")


class StatusResponse(BaseModel):
    """
    Réponse pour le statut détaillé de l'agent.
    """
    status: str = Field(..., description="Statut de l'agent (OK ou ERROR)")
    claude_status: str = Field(..., description="Statut de Claude Desktop (UP ou DOWN)")
    fallback_mode: str = Field(..., description="Mode de fallback (auto, forced, disabled)")
    model_preference: str = Field(..., description="Préférence de modèle (anthropic ou openai)")
    anthropic_available: bool = Field(..., description="Disponibilité de l'API Anthropic")
    openai_available: bool = Field(..., description="Disponibilité de l'API OpenAI")
    redis_available: bool = Field(..., description="Disponibilité de Redis")


class ErrorResponse(BaseModel):
    """
    Réponse d'erreur standardisée.
    """
    error: str = Field(..., description="Message d'erreur")
    detail: Optional[str] = Field(None, description="Détails supplémentaires sur l'erreur")
    status_code: int = Field(..., description="Code HTTP de l'erreur")
    timestamp: str = Field(..., description="Horodatage de l'erreur")


class TokenRequest(BaseModel):
    """
    Requête d'authentification pour obtenir un token JWT.
    """
    username: str = Field(..., description="Nom d'utilisateur")
    password: str = Field(..., description="Mot de passe")


class TokenResponse(BaseModel):
    """
    Réponse contenant un token JWT.
    """
    access_token: str = Field(..., description="Token JWT d'accès")
    token_type: str = Field("bearer", description="Type de token")
    expires_in: int = Field(3600, description="Durée de validité en secondes")


class StatisticsResponse(BaseModel):
    """
    Statistiques d'utilisation de l'agent de fallback.
    """
    total_fallbacks: int = Field(..., description="Nombre total d'activations du fallback")
    active_fallbacks: int = Field(..., description="Nombre de fallbacks actuellement actifs")
    claude_health_checks: int = Field(..., description="Nombre total de vérifications de santé")
    claude_failures: int = Field(..., description="Nombre total de défaillances détectées")
    average_latency: float = Field(..., description="Latence moyenne en secondes")
