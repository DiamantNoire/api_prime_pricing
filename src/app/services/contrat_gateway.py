"""Client API pour la gestion des contrats depuis Streamlit."""

from __future__ import annotations

import logging
from typing import Any

import requests

logger = logging.getLogger(__name__)


class ContratGateway:
    """Encapsule les appels HTTP vers les endpoints contrats."""

    def __init__(self, base_endpoint: str, timeout: int = 10):
        self.base_endpoint = base_endpoint
        self.timeout = timeout

    def list_recent(self, limit: int = 10) -> list[dict[str, Any]]:
        try:
            resp = requests.get(
                self.base_endpoint,
                params={"limit": limit},
                timeout=self.timeout,
            )
            resp.raise_for_status()
            return resp.json()
        except Exception:
            logger.exception("Echec récupération des contrats récents")
            raise

    def get_by_id(self, id_contrat: str) -> dict[str, Any]:
        try:
            resp = requests.get(
                f"{self.base_endpoint}/{id_contrat}",
                timeout=self.timeout,
            )
            resp.raise_for_status()
            return resp.json()
        except Exception:
            logger.exception("Echec récupération contrat id=%s", id_contrat)
            raise

    def create(self, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            resp = requests.post(
                self.base_endpoint,
                json=payload,
                timeout=self.timeout,
            )
            resp.raise_for_status()
            return resp.json()
        except Exception:
            logger.exception("Echec création contrat")
            raise

    def update(self, id_contrat: str, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            resp = requests.put(
                f"{self.base_endpoint}/{id_contrat}",
                json=payload,
                timeout=self.timeout,
            )
            resp.raise_for_status()
            return resp.json()
        except Exception:
            logger.exception("Echec mise à jour contrat id=%s", id_contrat)
            raise
