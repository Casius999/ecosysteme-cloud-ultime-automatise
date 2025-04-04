FROM python:3.9-slim

LABEL maintainer="Cloud Automation Team"
LABEL description="Module d'optimisation quantique basé sur Qiskit AER pour l'écosystème cloud automatisé"

# Installation des dépendances système
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    libopenblas-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Mise à jour de pip et installation des dépendances Python
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
    qiskit==0.44.2 \
    qiskit-aer==0.12.2 \
    qiskit-terra==0.24.1 \
    matplotlib==3.7.3 \
    numpy==1.24.3 \
    pandas==2.0.3 \
    scipy==1.10.1 \
    pyyaml==6.0.1 \
    prometheus-client==0.17.1 \
    pyarrow==14.0.1 \
    requests==2.31.0

# Création du répertoire de travail
WORKDIR /app

# Copie des fichiers de code source
COPY simulate.py /app/
COPY optimization.py /app/
COPY utils.py /app/
COPY models/ /app/models/
COPY config.yaml /app/

# Création des répertoires pour les résultats et les données
RUN mkdir -p /app/results /app/data

# Définition des variables d'environnement
ENV PYTHONUNBUFFERED=1 \
    SIMULATION_TYPE=resource_optimization \
    SIMULATION_PARAMS="{}" \
    OPTIMIZATION_ITERATIONS=1000 \
    LOG_LEVEL=INFO \
    PROMETHEUS_PORT=8000

# Exposition du port pour Prometheus metrics
EXPOSE 8000

# Commande par défaut
CMD ["python", "simulate.py"]
