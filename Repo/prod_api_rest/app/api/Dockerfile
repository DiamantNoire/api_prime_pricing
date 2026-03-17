FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

# Copie uv depuis l'image officielle Astral
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

WORKDIR /opt/app

# Copie des sources
COPY dev_build_models /opt/app/dev_build_models
COPY prod_api_rest/app/api /opt/app/api

# Installation des dépendances via uv (sans créer de venv, directement dans l'image)
WORKDIR /opt/app/api
RUN uv sync --no-dev --frozen 2>/dev/null || uv pip install --system \
    fastapi==0.115.6 \
    "uvicorn[standard]==0.34.0" \
    pandas==2.2.3 \
    numpy==1.26.4 \
    scikit-learn==1.5.2 \
    pydantic==2.10.4

ENV PYTHONPATH=/opt/app/api:/opt/app/dev_build_models

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
