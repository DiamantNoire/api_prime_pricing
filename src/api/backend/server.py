"""
Serveur FastAPI principal pour l'API Prime Pricing.

Ce module instancie l'application FastAPI, inclut les routers principaux,
et expose les endpoints racine, health et favicon.
"""

# --*- coding: utf-8 -*-
# =============================================
# ------ IMPORTATIONS DES LIBRAIRIES ----------#
# =============================================

from fastapi import FastAPI, Request
from fastapi.responses import Response, JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from src.api.backend.log_api.logger import get_logger

from src.api.backend.controllers.controller_severite import router as severite_router
from src.api.backend.controllers.controller_frequence import router as frequence_router
from src.api.backend.controllers.contrat_controller import contrat_router

# =============================================
# ------ AJOUT DES ENDPOINTS ----------#
# =============================================
app = FastAPI(title="API Prime Pricing", version="1.0.0")

logger = get_logger("api_global")


# Handler global pour toutes les exceptions
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Exception non gérée: {exc}")
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


# Handler pour les erreurs de validation (422)
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"Erreur de validation 422: {exc}")
    return JSONResponse(
        status_code=422, content={"detail": exc.errors(), "body": exc.body}
    )


# Handler pour les erreurs HTTP (ex: 404, 403...)
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    logger.error(f"Erreur HTTP {exc.status_code}: {exc.detail}")
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


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
