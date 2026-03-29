"""Service métier pour la gestion des contrats."""

from __future__ import annotations

import logging
from typing import Any

from src.api.backend.dto.contrat_dto import ContratCreateDTO, ContratUpdateDTO
from src.api.backend.repositories.contrat_repository import ContratRepository

logger = logging.getLogger(__name__)


class ContratService:
    """Orchestre les opérations de contrats et applique les règles métier."""

    def __init__(self, repository: ContratRepository | None = None):
        self.repository = repository or ContratRepository()

    @staticmethod
    def _normalize_payload(payload: dict[str, Any]) -> dict[str, Any]:
        normalized = dict(payload)

        # Si pas de second conducteur, neutraliser les champs associés.
        if normalized.get("conducteur2") == "No":
            normalized["age_conducteur2"] = 0
            normalized["sex_conducteur2"] = ""
            normalized["anciennete_permis2"] = 0

        return normalized

    def list_recent(self, limit: int = 20) -> list[dict[str, Any]]:
        logger.info("Lecture des %s derniers contrats", limit)
        return self.repository.find_recent(limit=limit)

    def get_by_id_contrat(self, id_contrat: str) -> dict[str, Any] | None:
        logger.info("Lecture contrat id_contrat=%s", id_contrat)
        return self.repository.find_by_id_contrat(id_contrat)

    def create(self, dto: ContratCreateDTO) -> dict[str, Any]:
        payload = self._normalize_payload(dto.model_dump())
        existing = self.repository.find_by_id_contrat(payload["id_contrat"])
        if existing:
            raise ValueError(f"Le contrat '{payload['id_contrat']}' existe déjà")

        logger.info("Création contrat id_contrat=%s", payload["id_contrat"])
        return self.repository.insert(payload)

    def update(self, id_contrat: str, dto: ContratUpdateDTO) -> dict[str, Any]:
        payload = self._normalize_payload(dto.model_dump())
        current = self.repository.find_by_id_contrat(id_contrat)
        if current is None:
            raise LookupError(f"Contrat '{id_contrat}' introuvable")

        # Le path id_contrat est la référence de mise à jour (pas de renommage ici).
        payload["id_contrat"] = id_contrat

        logger.info("Mise à jour contrat id_contrat=%s", id_contrat)
        updated = self.repository.update_by_id_contrat(id_contrat, payload)
        if updated is None:
            raise LookupError(f"Contrat '{id_contrat}' introuvable après mise à jour")
        return updated
