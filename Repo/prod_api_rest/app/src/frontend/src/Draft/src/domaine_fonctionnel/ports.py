# src/domaine_fonctionnel/ports.py

# Importation de librairies
from datetime import datetime
from dataclasses import dataclass
from typing import List, Optional, Dict, Tuple
from abc import ABC, abstractmethod

# Importation de modules
from src.domaine_fonctionnel.entites import JddOdre

@dataclass
class PortdeRecuperationJDD(ABC):
    """Port abstrait de récupération des jdd ODRE"""
    @abstractmethod
    def brancher_le_port(self) -> List[JddOdre]:
        """Brancher un connecteur api: par défaut retourne tous les JDDs"""
        pass

@dataclass
class CacheSources:
    """Port pour la persistance / inspection des métadonnées de cache (dernière prise de sources)."""
    @abstractmethod
    def inspecter_les_sources(self) -> Tuple[Optional[datetime], Optional[str], Dict]:
        """
        Retourne un tuple:
        - last_dt: datetime de la dernière prise de sources (timezone Config.TIME_ZONE) ou None
        - age_str: âge 'humain' en français (ex: '2 h 13 min') ou None
        - meta: dict brut des métadonnées lues (ex: {"last_refresh_at": "...", "status": "...", "duration_sec": ..., "items": ...})
        """
        pass

    @abstractmethod
    def enregistrer_rafraichissement(self, *, status: str, duration_sec: float, items: int) -> Dict:
        """Enregistre un événement de rafraîchissement (prise de sources) dans les métadonnées et retourne le dict écrit."""
        pass
