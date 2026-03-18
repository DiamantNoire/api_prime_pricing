# ===============================
# Dockerfile (propre, commenté)
# ===============================
FROM python:3.11-slim AS base

# Définir le répertoire de travail
WORKDIR /app

# Installer uv (gestionnaire de paquets rapide)
RUN pip install --no-cache-dir uv

# Copier et installer les dépendances
COPY requirements.txt ./
RUN uv pip install -r requirements.txt

# Copier tout le code source
COPY . .

# Exposer le port de l'API
EXPOSE 8000

# Commande de lancement par défaut (FastAPI via Uvicorn)
CMD ["uvicorn", "src/api/backend/server:app", "--host", "0.0.0.0", "--port", "8000"]
