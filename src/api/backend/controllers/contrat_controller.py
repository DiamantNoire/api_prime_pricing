from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Query

from src.api.backend.dto.contrat_dto import (
    ContratCreateDTO,
    ContratReadDTO,
    ContratResponseDTO,
    ContratUpdateDTO,
)
from src.api.backend.services.contrat_service import ContratService

logger = logging.getLogger(__name__)

contrat_router = APIRouter(tags=["contrats"])
contrat_service = ContratService()


@contrat_router.get("/contrats", response_model=list[ContratReadDTO])
def get_recent_contrats(limit: int = Query(default=20, ge=1, le=200)):
    """Retourne les derniers contrats enregistrés."""
    try:
        rows = contrat_service.list_recent(limit=limit)
        return [ContratReadDTO(**row) for row in rows]
    except Exception as exc:
        logger.exception("Erreur lecture des contrats")
        raise HTTPException(status_code=500, detail=f"Erreur lecture contrats: {exc}")


@contrat_router.get("/contrats/{id_contrat}", response_model=ContratReadDTO)
def get_contrat(id_contrat: str):
    """Retourne un contrat par son identifiant métier id_contrat."""
    try:
        row = contrat_service.get_by_id_contrat(id_contrat)
        if row is None:
            raise HTTPException(status_code=404, detail=f"Contrat '{id_contrat}' introuvable")
        return ContratReadDTO(**row)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Erreur lecture contrat")
        raise HTTPException(status_code=500, detail=f"Erreur lecture contrat: {exc}")


@contrat_router.post("/contrats", response_model=ContratResponseDTO, status_code=201)
def create_contrat(payload: ContratCreateDTO):
    """Crée un contrat dans historique_contrats."""
    try:
        created = contrat_service.create(payload)
        return ContratResponseDTO(**created)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except Exception as exc:
        logger.exception("Erreur création contrat")
        raise HTTPException(status_code=500, detail=f"Erreur création contrat: {exc}")


@contrat_router.put("/contrats/{id_contrat}", response_model=ContratResponseDTO)
def update_contrat(id_contrat: str, payload: ContratUpdateDTO):
    """Met à jour un contrat de manière complète (PUT)."""
    try:
        updated = contrat_service.update(id_contrat=id_contrat, dto=payload)
        return ContratResponseDTO(**updated)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except Exception as exc:
        logger.exception("Erreur mise à jour contrat")
        raise HTTPException(status_code=500, detail=f"Erreur mise à jour contrat: {exc}")


