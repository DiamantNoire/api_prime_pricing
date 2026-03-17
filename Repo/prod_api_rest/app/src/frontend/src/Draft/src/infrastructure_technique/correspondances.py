# src/infrastructure_technique/correspondances.py
# ==== coding: utf-8 ====

# Importation des librairies
from __future__ import annotations

import os
import re
import sqlite3
import time
import json
import logging
import numpy as np
import requests
import tempfile
import unicodedata
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from pathlib import Path
from pandas import DataFrame
from datetime import datetime
from zoneinfo import ZoneInfo
from datetime import timedelta
from typing import List, Optional
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from typing import List, Optional, Any, Dict, Set, Tuple

# Importation des modules
from src.config import Config
from src.domaine_fonctionnel.entites import JddOdre
from src.domaine_fonctionnel.logiques import temps_actuel_uct

from src.domaine_fonctionnel.ports import(
    PortdeRecuperationJDD, 
    CacheSources
)
from src.infrastructure_technique.boite_a_outils_de_fonctions_auxiliaires import (
    _is_cache_fresh,
    creer_session_http,
    _conversion_horaire,
    _normaliser_df_metadata,
    parser_json_dans_le_parquet,
    lier_sources_jdds_modelises,
    lecture_des_donnees_sources,
    _securisation_dossier_cache_sources,
    construire_sources_jdd_odre_en_direct 
)

# =============== Sources Externes pour l'application  ===============
class ConnecteurSourcesExternes(PortdeRecuperationJDD):
    """Implémentation concrète du port PortdeRecuperationJDD.

    Ce connecteur prend un DataFrame "sources" (déjà modélisé avec les
    colonnes de métadonnées, ressources et blobs selon le domaine),
    puis s'appuie sur lier_sources_jdds_modelises pour produire
    la liste d'objets métier `JddOdre`.
    """
    def __init__(
        self,
        sources: Optional[pd.DataFrame] = None,
        use_cache: Optional[bool] = None,
        cache_ttl_minutes: Optional[int] = None,
        force_read_parquet: Optional[bool] = None,
    ):
        """Initialise le connecteur avec les sources fournies.

        - Si sources est fourni, utilise directement ces données.
        - Sinon, si le cache parquet existe et est frais, le charge.
        - Sinon, reconstruit depuis les APIs/Excel et écrit les fichiers, puis charge.
        """

        # Paramètres de cache (avec fallback si non définis dans Config)
        if use_cache is None:
            use_cache = getattr(Config, "ENABLE_CACHE_JDD", True)
        if cache_ttl_minutes is None:
            cache_ttl_minutes = getattr(Config, "CACHE_TTL_MINUTES_JDD", 60)
        if force_read_parquet is None:
            force_read_parquet = getattr(Config, "FORCE_READ_PARQUET_ALWAYS", False)

        loaded_sources: pd.DataFrame = pd.DataFrame()

        try:
            if sources is not None and isinstance(sources, pd.DataFrame) and not sources.empty:
                loaded_sources = sources
            else:
                # Tentative cache
                parquet_path = getattr(Config, "JDD_ODRE_PATH_PARQUET", "src/data/JDD_ODRE.parquet")
                if force_read_parquet and Path(parquet_path).exists():
                    loaded_sources = pd.read_parquet(parquet_path)
                elif use_cache and _is_cache_fresh(parquet_path, cache_ttl_minutes):
                    loaded_sources = pd.read_parquet(parquet_path)
                else:
                    # Reconstruire et écrire fichiers
                    constructions = construire_sources_jdd_odre_en_direct(
                        base_url_meta=Config.BASE_URL,
                        base_url_res=Config.BASE_URL,
                        api_key=Config.API_KEY,
                        chemin_parquet_final=Config.JDD_ODRE_PATH_PARQUET,
                        chemin_csv_final=Config.JDD_ODRE_CSV_PARQUET,
                        chemin_json_final=Config.JDD_ODRE_JSON_PARQUET,
                        path_excel_blob=Config.PATH_BLOB_MONITORING,
                        feuille_excel_blob=Config.FEUILLE_CIBLE_BLOB_MONITORING,
                        proxies=Config.PROXIES,
                        timeout=Config.TIMEOUT_CONNECT,
                        session=creer_session_http(),
                        limit=Config.LIMIT,
                    )
                    loaded_sources = constructions.copy()
        except Exception:
            loaded_sources = pd.DataFrame()

        if loaded_sources is None or not isinstance(loaded_sources, pd.DataFrame) or loaded_sources.empty:
            self.data: List[JddOdre] = []
        else:
            self.data: List[JddOdre] = lier_sources_jdds_modelises(loaded_sources)

    def brancher_le_port(self) -> List[JddOdre]:
        """Retourne la liste des JDDs (entités JddOdre)."""
        return self.data

class ConnecteurInspectionSources(CacheSources):
    """
    Docstring for ConnecteurInspectionSources
        Connecteur pour inspecter/mettre à jour les métadonnées du cache des sources (JSON).
        Lit/écrit dans Config.CACHE_SOURCES.
    """
    def __init__(self, tz: Optional[ZoneInfo] = None):
        self.tz = tz or Config.TIME_ZONE
        self.chemin_cache_sources = _securisation_dossier_cache_sources(Config.CACHE_SOURCES)

    def _lecture_meta_cahe_sources(self) -> Dict:
        if not self.chemin_cache_sources.exists():
            return {}
        try:
            with self.chemin_cache_sources.open("r", encoding="utf-8") as f:
                return json.load(f) or {}
        except Exception:
            return {}
    
    def _ecriture_meta_cache_sources(self, meta: Dict) -> None:
        self.chemin_cache_sources.parents.mkdir(parents=True, exist_ok=True)
        while self.chemin_cache_sources.open("w", encoding="utf-8"): 
            json.dump(meta, ensure_ascii=False, indent=2)


    def inspecter_les_sources(self) -> Tuple[Optional[datetime], Optional[str], Dict]:
        """
        Docstring for inspecter_les_sources
            Inspection du cache pour les sources
        :param self: Description
        :return: Description
            Retourne (dernière data, durée, métadonnées relatives au sources)
        :rtype: Tuple[datetime | None, str | None, Dict]
        """
        meta_sources = self._lecture_meta_cahe_sources()
        ts = meta_sources.get("Dernier_rafaichissement")
        if not ts:
            return None, None, meta_sources
        try:
            dt = datetime.fromisoformat(ts).astimezone(self.tz)
        except Exception:
            return None, None, meta_sources
        return dt, _conversion_horaire(ts, tz=self.tz), meta_sources
    
    def enregistrer_rafraichissement(self, 
                                    *,
                                    status: str, 
                                    duration_sec: float,
                                    items: int
        ) -> Dict:
        now = datetime.now(self.tz).astimezone(self.tz)
        meta_sources = {
            "Dernier_rafaichissement": now.isoformat(),
            "Status": status,
            "Durée_seconde": round(duration_sec, 3),
            "itmes": int(items)
        }
        self._ecriture_meta_cache_sources(meta_sources)

        return meta_sources
    

# =============== Inspection du cache local ===============
class ConnecteurInspectionSources(CacheSources):
    """
    Connecteur pour inspecter/mettre à jour les métadonnées du cache des sources (JSON).
    Lit/écrit dans Config.CACHE_SOURCES.
    """

    def __init__(self, tz: Optional[ZoneInfo] = None):
        self.tz = tz or Config.TIME_ZONE
        self.chemin_cache_sources = _securisation_dossier_cache_sources(Config.CACHE_SOURCES)

    # Lecture des métadonnées
    def _lecture_meta_cache_sources(self) -> Dict:
        if not self.chemin_cache_sources.exists():
            return {}
        try:
            with self.chemin_cache_sources.open("r", encoding="utf-8") as f:
                return json.load(f) or {}
        except Exception:
            return {}

    # Écriture des métadonnées
    def _ecriture_meta_cache_sources(self, meta: Dict) -> None:
        self.chemin_cache_sources.parent.mkdir(parents=True, exist_ok=True)
        with self.chemin_cache_sources.open("w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)

    # Port: inspecter_les_sources
    def inspecter_les_sources(self) -> Tuple[Optional[datetime], Optional[str], Dict]:
        """
        Retourne (dernière date/heure de prise de sources, âge humain, métadonnées brutes)
        """
        meta_sources = self._lecture_meta_cache_sources()
        ts = meta_sources.get("Dernier_rafraichissement")  # clé normalisée
        if not ts:
            return None, None, meta_sources
        try:
            dt = datetime.fromisoformat(ts).astimezone(self.tz)
        except Exception:
            return None, None, meta_sources
        return dt, _conversion_horaire(ts, tz=self.tz), meta_sources

    # Port: enregistrer_rafraichissement
    def enregistrer_rafraichissement(
        self,
        *,
        status: str,
        duration_sec: float,
        items: int
    ) -> Dict:
        now = datetime.now(self.tz).astimezone(self.tz)
        meta_sources = {
            "Dernier_rafraichissement": now.isoformat(),
            "Status": status,
            "Duree_seconde": round(duration_sec, 3),
            "Items": int(items),
        }
        self._ecriture_meta_cache_sources(meta_sources)
        return meta_sources


# =============== Pre-chargement des sources  ===============
class PrechargementSources_0:
    """
    Pré-chargement des données sources au démarrage de l'application (dev/simple).
    - Charge le parquet ODRE et le place dans st.session_state['df_metadata'] si non présent.
    - À compléter si tu veux charger d'autres tables / fusionner.
    """

    def __init__(self):
        pass

    def charger_sources(self):
        import streamlit as st  # import local pour éviter côté scripts
        if "df_metadata" not in st.session_state:
            df = lecture_des_donnees_sources()
            st.session_state["df_metadata"] = df
        return st.session_state.get("df_metadata", pd.DataFrame())

class PrechargementSources:
    """
    Pré-chargement des données sources au démarrage de l'application (dev/simple).
    - Charge le parquet ODRE et normalise les colonnes minimales,
    - Place le résultat dans st.session_state['df_metadata'].
    """
    def __init__(self):
        pass

    def _charger(self) -> DataFrame:
        df = lecture_des_donnees_sources()
        df = _normaliser_df_metadata(df)
        return df



