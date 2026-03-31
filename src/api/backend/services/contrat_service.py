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
        """
        Initialise le service métier pour la gestion des contrats.

        Args:
            repository (ContratRepository | None): Instance de repository à utiliser (par défaut ContratRepository).
        """
        self.repository = repository or ContratRepository()

    @staticmethod
    def _normalize_payload(payload: dict[str, Any]) -> dict[str, Any]:
        """
        Normalise le dictionnaire de payload pour la création/mise à jour d'un contrat.
        Neutralise les champs du second conducteur si non présent.

        Args:
            payload (dict[str, Any]): Données du contrat à normaliser.

        Returns:
            dict[str, Any]: Payload normalisé.
        """
        normalized = dict(payload)

        # Si pas de second conducteur, neutraliser les champs associés.
        if normalized.get("conducteur2") == "No":
            normalized["age_conducteur2"] = 0
            normalized["sex_conducteur2"] = ""
            normalized["anciennete_permis2"] = 0

        return normalized

    def list_recent(self, limit: int = 20) -> list[dict[str, Any]]:
        """
        Retourne les derniers contrats insérés.

        Args:
            limit (int): Nombre maximum de contrats à retourner (défaut 20).

        Returns:
            list[dict[str, Any]]: Liste des contrats récents.
        """
        logger.info("Lecture des %s derniers contrats", limit)
        return self.repository.find_recent(limit=limit)

    def get_by_id_contrat(self, id_contrat: str) -> dict[str, Any] | None:
        """
        Récupère un contrat par son identifiant unique.

        Args:
            id_contrat (str): Identifiant du contrat recherché.

        Returns:
            dict[str, Any] | None: Contrat trouvé ou None si absent.
        """
        logger.info("Lecture contrat id_contrat=%s", id_contrat)
        return self.repository.find_by_id_contrat(id_contrat)

    def create(self, dto: ContratCreateDTO) -> dict[str, Any]:
        """
        Crée un nouveau contrat à partir d'un DTO.

        Args:
            dto (ContratCreateDTO): Données du contrat à créer.

        Returns:
            dict[str, Any]: Contrat créé.

        Raises:
            ValueError: Si le contrat existe déjà.
        """
        payload = self._normalize_payload(dto.model_dump())
        existing = self.repository.find_by_id_contrat(payload["id_contrat"])
        if existing:
            raise ValueError(f"Le contrat '{payload['id_contrat']}' existe déjà")

        logger.info("Création contrat id_contrat=%s", payload["id_contrat"])
        return self.repository.insert(payload)

    def update(self, id_contrat: str, dto: ContratUpdateDTO) -> dict[str, Any]:
        """
        Met à jour un contrat existant à partir de son identifiant et d'un DTO.

        Args:
            id_contrat (str): Identifiant du contrat à mettre à jour.
            dto (ContratUpdateDTO): Données de mise à jour.

        Returns:
            dict[str, Any]: Contrat mis à jour.

        Raises:
            LookupError: Si le contrat n'existe pas ou n'est pas retrouvé après update.
        """
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
