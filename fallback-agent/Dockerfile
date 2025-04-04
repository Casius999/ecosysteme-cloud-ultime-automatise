FROM python:3.9-slim

LABEL maintainer="Cloud Automation Team"
LABEL description="Agent de fallback pour remplacer Claude Desktop en cas de défaillance"

# Installation des dépendances système
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Mise à jour de pip et installation des dépendances Python
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
    fastapi==0.109.2 \
    uvicorn==0.27.1 \
    httpx==0.26.0 \
    redis==5.0.1 \
    pydantic==2.5.2 \
    prometheus-client==0.17.1 \
    openai==1.3.4 \
    anthropic==0.8.0 \
    python-dotenv==1.0.0 \
    cryptography==41.0.5 \
    PyJWT==2.8.0 \
    requests==2.31.0 \
    tenacity==8.2.3 \
    tiktoken==0.5.1

# Création du répertoire de travail
WORKDIR /app

# Copie des fichiers de code source
COPY app.py /app/
COPY api.py /app/
COPY models.py /app/
COPY utils.py /app/
COPY config.yaml /app/

# Copie des fichiers de conversion et de compatibilité
COPY compatibility/ /app/compatibility/

# Création des répertoires pour les logs et les données en cache
RUN mkdir -p /app/logs /app/cache

# Définition des variables d'environnement
ENV PYTHONUNBUFFERED=1 \
    LOG_LEVEL=INFO \
    PROMETHEUS_PORT=8000 \
    FALLBACK_MODE=auto \
    REDIS_URL="" \
    ANTHROPIC_API_KEY="" \
    OPENAI_API_KEY="" \
    MODEL_PREFERENCE="anthropic" \
    CLAUDE_ENDPOINT="http://claude-service:8080" \
    PORT=8080

# Exposition des ports pour l'API et les métriques
EXPOSE 8080 8000

# Script d'entrée
COPY entrypoint.sh /app/
RUN chmod +x /app/entrypoint.sh

# Commande par défaut
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]
