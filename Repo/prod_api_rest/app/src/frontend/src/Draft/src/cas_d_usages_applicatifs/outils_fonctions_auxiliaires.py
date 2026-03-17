# src/cas_d_usages_applicatifs/outils_fonctions_auxiliaires.py

# Importation de librairies
from __future__ import annotations

import re
import json
import pandas as pd

from pathlib import Path
from pandas import DataFrame
from typing import List, Dict, Optional, Set, Union, Any

# Importation de modules
from src.config import Config
from src.domaine_fonctionnel.entites import JddOdre

from src.infrastructure_technique.boite_a_outils_de_fonctions_auxiliaires import(
    lecture_du_parquet,
    parser_json_dans_le_parquet,
)
from src.infrastructure_technique.correspondances import(
    lier_sources_jdds_modelises
)



# ===== Fonctions auxilaires | Cas d'usage: Actualisation des données ====== #

def normaliser_cle_chemin(cle: str, *, conserver_indices: bool = False, prefix: Optional[str] = None) -> str:
    """
        Normalise une clé de chemin aplatie en un identifiant simple pour colonnes/attributs.

        Exemples :
        - "ressources[11].uid_metadata" -> "ressources_uid_metadata" (conserver_indices=False)
        - "ressources[11].uid_metadata" -> "ressources_11_uid_metadata" (conserver_indices=True)
        - "PDA[0].FullName_lower"       -> "PDA_FullName_lower" (conserver_indices=False)
        - "PDA[0].FullName_lower"       -> "PDA_0_FullName_lower" (conserver_indices=True)

        Règles :
        - Remplace "." par "_"
        - Remplace les indices [i] par soit rien (si conserver_indices=False) soit "_i"
        - Supprime les doubles underscores éventuels
        - Optionnel: force un prefix au début (ex. 'ressources'), ajouté s'il n'est pas déjà présent

        :param cle: chemin aplati
        :param conserver_indices: True pour garder les indices, False pour les supprimer
        :param prefix: impose un préfixe au début si non présent (ex. "ressources")
        :return: clé normalisée
    """
    if not isinstance(cle, str) or not cle:
        return ""

    s = cle.strip()

    # Remplacer '.' par '_'
    s = s.replace(".", "_")

    # Traiter les indices [i]
    if conserver_indices:
        # "[11]" -> "_11"
        s = re.sub(r"\[(\d+)\]", r"_\1", s)
    else:
        # "[11]" -> "" (on supprime)
        s = re.sub(r"\[(\d+)\]", "", s)

    # Nettoyage: underscores multiples -> un seul
    s = re.sub(r"_+", "_", s)

    # Retire un underscore en fin/début si présent
    s = s.strip("_")

    # Option: forcer un préfixe si non présent en début
    if prefix:
        # Si la clé ne commence pas déjà par le prefix (exact match au début)
        if not s.startswith(prefix + "_") and s != prefix:
            s = f"{prefix}_{s}"

    return s


def extraire_cles_normalisees_depuis_objet(obj: Any,
                                           *,
                                           prefix: Optional[str] = None,
                                           conserver_indices: bool = False
) -> List[str]:
    """
    Aplatie les clés d'un dict/list imbriqué puis normalise chaque clé.
    Retourne une liste dédupliquée triée (ordre stable).
    """
    brutes: Set[str] = set()

    def _rec(x: Any, p: str):
        if isinstance(x, dict):
            if p: brutes.add(p)
            for k, v in x.items():
                np = f"{p}.{k}" if p else str(k)
                brutes.add(np); _rec(v, np)
        elif isinstance(x, list):
            if p: brutes.add(p)
            for i, v in enumerate(x):
                np = f"{p}[{i}]" if p else f"[{i}]"
                brutes.add(np); _rec(v, np)
        else:
            # scalaire -> rien de plus
            pass

    _rec(obj, prefix or "")
    normalisees = [normaliser_cle_chemin(k, conserver_indices=conserver_indices) for k in brutes]
    return sorted(set(normalisees))

# -- Fonction principale pour faire correspondre les sources récupérées avec la modélisation des jdds

def lier_sources_jdds_modelises_0(sources: DataFrame) -> List[JddOdre]:
    """
    Traduire les extractions de sources en liste d'objets JddOdre (Option B):
    - metadonnees: dict à plat (str/scalaires)
    - ressources: JSON désérialisé (dict ou list) si présent, sinon dict à plat
    - PDA_opendata: JSON désérialisé (dict ou list) si présent, sinon dict à plat

    Hypothèses d'entrée:
    - 'sources' contient au moins les colonnes méta définies dans Config.LISTE_CHAMPS_META.
    - Optionnellement, 'sources' peut contenir:
        - colonnes JSON pour ressources (ex: 'ressources_json')
        - colonnes JSON pour PDA/monitoring (ex: 'matched_blobs_json', 'PDA', 'PDA_opendata_json')

    Sortie:
    - Liste d'instances JddOdre peuplées.
    """

    if sources is None or not isinstance(sources, pd.DataFrame) or sources.empty:
        return []

    # Colonnes attendues (à plat)
    champs_meta_attendus: Set[str] = set(getattr(Config, "LISTE_CHAMPS_META", []))
    champs_ress_attendus: Set[str] = set(getattr(Config, "LISTE_CHAMPS_RESSOURCES", []))
    champs_blobs_attendus: Set[str] = set(getattr(Config, "LISTE_CHAMPS_BLOB_MONITORING", []))

    champs_meta_presents: List[str] = [c for c in sources.columns if c in champs_meta_attendus]
    champs_ress_presents: List[str] = [c for c in sources.columns if c in champs_ress_attendus]
    champs_blobs_presents: List[str] = [c for c in sources.columns if c in champs_blobs_attendus]

    # Colonnes JSON potentielles (configurables)
    cols_json_ress: Set[str] = set(getattr(Config, "LISTE_COLS_JSON_RESSOURCES", ["ressources_json"]))
    cols_json_pda: Set[str] = set(getattr(Config, "LISTE_COLS_JSON_PDA", ["matched_blobs_json", "PDA", "PDA_opendata_json"]))

    cols_json_ress_presents: List[str] = [c for c in sources.columns if c in cols_json_ress]
    cols_json_pda_presents: List[str] = [c for c in sources.columns if c in cols_json_pda]

    # Colonnes utiles pour l'identification
    uid_col: Optional[str] = "uid" if "uid" in sources.columns else ("uid_meta" if "uid_meta" in sources.columns else None)
    dataset_id_col: Optional[str] = "dataset_id" if "dataset_id" in sources.columns else None

    resultat: List[JddOdre] = []

    for idx, row in sources.iterrows():
        # id_jdd_odre: utiliser l'index si entier, sinon None
        id_jdd_odre: Optional[int] = idx if isinstance(idx, int) else None

        # nom_jdd_odre: privilégier dataset_id, sinon uid, sinon ""
        nom_jdd_odre: Optional[str]
        if dataset_id_col:
            nom_jdd_odre = str(row.get(dataset_id_col, "") or "")
        elif uid_col:
            nom_jdd_odre = str(row.get(uid_col, "") or "")
        else:
            nom_jdd_odre = ""

        # 1) Métadonnées à plat (str/scalaires convertis en str)
        metadonnees: Dict[str, Any] = {}
        for col in champs_meta_presents:
            try:
                val = row.get(col)
            except Exception:
                val = None
            # Conserver une représentation lisible (string) pour les méta
            metadonnees[col] = "" if (val is None or (isinstance(val, float) and pd.isna(val))) else str(val)

        # 2) Ressources: priorité au JSON désérialisé si dispo, sinon dict à plat
        ressources: Any = None
        for col in cols_json_ress_presents:
            parsed = parse_json(row.get(col))
            if parsed is not None:
                ressources = parsed
                break  # prend la première colonne JSON valide

        if ressources is None:
            # Fallback: prendre les colonnes "ressources" à plat si tu en as (46 colonnes)
            ress_flat: Dict[str, Any] = {}
            for col in champs_ress_presents:
                try:
                    val = row.get(col)
                except Exception:
                    val = None
                ress_flat[col] = "" if (val is None or (isinstance(val, float) and pd.isna(val))) else str(val)
            # Si rien trouvé du tout, mettre {} plutôt que None pour rester uniforme
            ressources = ress_flat if ress_flat else {}

        # 3) PDA/Monitoring: priorité au JSON désérialisé si dispo, sinon dict à plat
        pda_opendata: Any = None
        for col in cols_json_pda_presents:
            parsed = parse_json(row.get(col))
            if parsed is not None:
                pda_opendata = parsed
                break

        if pda_opendata is None:
            blobs_flat: Dict[str, Any] = {}
            for col in champs_blobs_presents:
                try:
                    val = row.get(col)
                except Exception:
                    val = None
                blobs_flat[col] = "" if (val is None or (isinstance(val, float) and pd.isna(val))) else str(val)
            pda_opendata = blobs_flat if blobs_flat else {}

        # 4) Création de l'objet JddOdre (Option B)
        jdd = JddOdre(
            id_jdd_odre=id_jdd_odre,
            nom_jdd_odre=nom_jdd_odre,
            metadonnees=metadonnees or None,   # dict à plat
            ressources=ressources,             # dict/list désérialisé OU dict à plat
            PDA_opendata=pda_opendata,         # dict/list désérialisé OU dict à plat
        )

        resultat.append(jdd)

    return resultat


def lier_sources_jdds_modelises(sources: DataFrame) -> List[JddOdre]:
    """
    Option B: Désérialise les colonnes JSON pour remplir `ressources` et `PDA_opendata`
    avec des objets Python (dict/list). Conserve `metadonnees` à plat (str).
    """

    if sources is None or not isinstance(sources, pd.DataFrame) or sources.empty:
        return []

    # Colonnes à plat attendues (métadonnées/ressources/PDA à plat)
    champs_meta_attendus: Set[str] = set(getattr(Config, "LISTE_CHAMPS_META", []))
    champs_ress_attendus: Set[str] = set(getattr(Config, "LISTE_CHAMPS_RESSOURCES", []))
    champs_blobs_attendus: Set[str] = set(getattr(Config, "LISTE_CHAMPS_BLOB_MONITORING", []))

    champs_meta_presents: List[str] = [c for c in sources.columns if c in champs_meta_attendus]
    champs_ress_presents: List[str] = [c for c in sources.columns if c in champs_ress_attendus]
    champs_blobs_presents: List[str] = [c for c in sources.columns if c in champs_blobs_attendus]

    # Colonnes JSON configurables
    cols_json_ress: Set[str] = set(getattr(Config, "LISTE_COLS_JSON_RESSOURCES", ["ressources_json"]))
    cols_json_pda: Set[str] = set(getattr(Config, "LISTE_COLS_JSON_PDA", ["matched_blobs_json"]))

    cols_json_ress_presents: List[str] = [c for c in sources.columns if c in cols_json_ress]
    cols_json_pda_presents: List[str] = [c for c in sources.columns if c in cols_json_pda]

    # Identifiants
    uid_col: Optional[str] = "uid" if "uid" in sources.columns else ("uid_meta" if "uid_meta" in sources.columns else None)
    dataset_id_col: Optional[str] = "dataset_id" if "dataset_id" in sources.columns else None

    resultat: List[JddOdre] = []

    for idx, row in sources.iterrows():
        # id
        id_jdd_odre: Optional[int] = idx if isinstance(idx, int) else None

        # nom
        if dataset_id_col:
            nom_jdd_odre = str(row.get(dataset_id_col, "") or "")
        elif uid_col:
            nom_jdd_odre = str(row.get(uid_col, "") or "")
        else:
            nom_jdd_odre = ""

        # 1) métadonnées à plat (str pour stabilité)
        metadonnees: Dict[str, Any] = {}
        for col in champs_meta_presents:
            try:
                val = row.get(col)
            except Exception:
                val = None
            if val is None or (isinstance(val, float) and pd.isna(val)):
                metadonnees[col] = ""
            else:
                metadonnees[col] = str(val)

        # 2) ressources : priorité au JSON
        ressources: Any = None
        for col in cols_json_ress_presents:
            parsed = parse_json(row.get(col))
            if parsed is not None:
                ressources = parsed  # list[dict] ou dict
                break

        if ressources is None:
            # Fallback: colonnes à plat "ressources"
            ress_flat: Dict[str, Any] = {}
            for col in champs_ress_presents:
                try:
                    val = row.get(col)
                except Exception:
                    val = None
                ress_flat[col] = "" if (val is None or (isinstance(val, float) and pd.isna(val))) else str(val)
            ressources = ress_flat if ress_flat else {}

        # 3) PDA : priorité au JSON
        pda_opendata: Any = None
        for col in cols_json_pda_presents:
            parsed = parse_json(row.get(col))
            if parsed is not None:
                pda_opendata = parsed
                break

        if pda_opendata is None:
            blobs_flat: Dict[str, Any] = {}
            for col in champs_blobs_presents:
                try:
                    val = row.get(col)
                except Exception:
                    val = None
                blobs_flat[col] = "" if (val is None or (isinstance(val, float) and pd.isna(val))) else str(val)
            pda_opendata = blobs_flat if blobs_flat else {}

        # 4) JDD final
        jdd = JddOdre(
            id_jdd_odre=id_jdd_odre,
            nom_jdd_odre=nom_jdd_odre,
            metadonnees=metadonnees or None,
            ressources=ressources,          # JSON désérialisé si présent
            PDA_opendata=pda_opendata,      # JSON désérialisé si présent
        )
        resultat.append(jdd)

    return resultat


def charger_parquet_utile(
    parquet_path: Union[str, Path],
    champs_meta_attendus: Set[str],
    champs_ress_attendus: Set[str],
    champs_blobs_attendus: Set[str],
) -> pd.DataFrame:
    """
    Lit un fichier Parquet en ne chargeant que les colonnes utiles (meta/ressources/blobs).
    Retourne un DataFrame (vide si échec).
    """
    try:
        path = Path(parquet_path)
        if not path.exists():
            print(f"[charger_parquet_utile] Fichier introuvable: {path}")
            return pd.DataFrame()

        colonnes_a_lire = list(champs_meta_attendus | champs_ress_attendus | champs_blobs_attendus)
        df = pd.read_parquet(path, columns=colonnes_a_lire, engine="pyarrow")  
        return df
    except Exception as e:
        print(f"[charger_parquet_utile] Erreur lecture Parquet: {e}")
        return pd.DataFrame()

def lire_parquet_en_jdd_odre(parquet_path: str) -> List[JddOdre]:
    """
    Prend le chemin d'un Parquet où chaque ligne représente un JDD ODRE,
    et retourne une liste d'objets JddOdre (Pydantic).

    Cette fonction réutilise la logique existante de lier_sources_jdds_modelises().
    """
    Listes_jdds_odre = []
    parquet_path = Path(Config.JDD_ODRE_PATH_PARQUET)
    if not parquet_path.exists():
        return pd.DataFrame()
    df = pd.read_parquet(parquet_path, engine="pyarrow")
    Listes_jdds_odre = lier_sources_jdds_modelises(df)
    return Listes_jdds_odre


