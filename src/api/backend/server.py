"""
Serveur FastAPI principal pour l'API Prime Pricing.

Ce module instancie l'application FastAPI, inclut les routers principaux,
et expose les endpoints racine, health et favicon.
"""
# --*- coding: utf-8 -*-
# =============================================
#------ IMPORTATIONS DES LIBRAIRIES ----------#
# =============================================
from fastapi import FastAPI
from fastapi.responses import Response

from src.api.backend.controllers.controller_severite import router as severite_router
from src.api.backend.controllers.controller_frequence import router as frequence_router
from src.api.backend.controllers.contrat_controller import contrat_router

# =============================================
#------ AJOUT DES ENDPOINTS ----------#
# =============================================
app = FastAPI(
    title="API Prime Pricing",
    version="1.0.0"
)

app.include_router(severite_router)
app.include_router(frequence_router)
app.include_router(contrat_router)


@app.get("/", summary="Racine API", tags=["root"])
def read_root():
    """
    Endpoint racine de l'API.

    Returns:
        dict: Message de statut de l'API.
    """
    return {"message": "API Prime Pricing is running"}



@app.get("/health", summary="Healthcheck", tags=["monitoring"])
def health():
    """
    Endpoint de vérification de santé de l'API.

    Returns:
        dict: Statut de santé.
    """
    return {"status": "ok"}


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    """
    Endpoint favicon (évite les erreurs 404 navigateur).

    Returns:
        Response: Réponse vide avec code 204.
    """
    return Response(status_code=204)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.api.backend.server:app", host="127.0.0.1", port=8000, reload=True)
