# Crypto Sentinel - Dockerfile
# Image Docker pour le déploiement de Crypto Sentinel

# Utiliser Python 3.11 slim comme image de base
FROM python:3.11-slim

# Métadonnées
LABEL maintainer="Crypto Sentinel Team"
LABEL version="1.0.0"
LABEL description="Crypto Sentinel - Assistant IA pour l'analyse de tokens ERC20"

# Variables d'environnement
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VENV_IN_PROJECT=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

# Installer les dépendances système
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Créer un utilisateur non-root pour la sécurité
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Définir le répertoire de travail
WORKDIR /app

# Copier les fichiers de dépendances
COPY requirements.txt .

# Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code source
COPY app/ ./app/
COPY tests/ ./tests/
COPY pytest.ini .
COPY README.md .

# Créer les répertoires nécessaires
RUN mkdir -p /app/logs /app/data

# Changer la propriété des fichiers
RUN chown -R appuser:appuser /app

# Passer à l'utilisateur non-root
USER appuser

# Exposer le port de l'application
EXPOSE 8000

# Vérification de santé
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Commande par défaut
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]