# ===============================
# Dockerfile (propre, commenté)
# ===============================
FROM python:3.11-slim AS base

# Répertoire de travail
WORKDIR /app

# Installation uv (gestionnaire de paquets rapide)
RUN pip install --no-cache-dir uv

# Copie et installation des dépendances
COPY requirements.txt ./
RUN uv pip install --system -r requirements.txt

# Copie de tout le code source
COPY . .

# Exposition du port de l'API
EXPOSE 8000

# Commande de lancement — PORT injecté par Render (défaut 8000 en local)
CMD uvicorn src.api.backend.server:app --host 0.0.0.0 --port ${PORT:-8000}
