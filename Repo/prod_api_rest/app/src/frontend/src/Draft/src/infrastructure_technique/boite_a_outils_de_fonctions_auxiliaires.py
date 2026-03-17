# src/infrastructure_technique/boite_a_outils_de_fonctions_auxiliaires.py
# ==== coding: utf-8 ====


# Importation de librairies
from __future__ import annotations

import os
import time
import json
import logging
import requests
import unicodedata
import pyarrow as ds
import pandas as pd

from pathlib import Path

from pandas import DataFrame
from datetime import datetime
from zoneinfo import ZoneInfo
from datetime import timedelta
from typing import List, Optional
from urllib3.util.retry import Retry
from pyarrow.dataset import dataset 
from requests.adapters import HTTPAdapter
from typing import List, Optional, Any, Dict, Set, Tuple

logger = logging.getLogger(__name__)


# Importation des modules
from src.config import Config
from src.domaine_fonctionnel.entites import JddOdre


# ===== Fonctions auxilaires | Fonction pour connecteur ====== #
#        BUT: Récupérer les sources (2 APIs ODRE + 1 Extract local du blob monitoring Opendata) 

# --------- Fonctions auxiliaires pour appel API
def _normaliser_colonnes(df:DataFrame) -> DataFrame:
    """Remplace '.' et '-' par '_' dans les noms de colonnes."""
    df.columns = [col.replace('.', '_').replace('-', '_') for col in df.columns]
    return df

def _typer_en_str(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df = df.where(pd.notnull(df), "")
    for c in df.columns:
        df[c] = df[c].astype(str)
    return df

def _match_blobs_pour_ressources(
    display_names: List[str],
    blob_fullnames: List[str],
    blob: pd.DataFrame
) -> Tuple[str, bool]:
    """
    Retourne (matched_blobs_json, has_blob) pour chaque ressources en se servant de la colonne display_name,
    en appliquant la logique de prefix:
        display_name_lower.startswith(FullName_lower)

    - matched_blobs_json: liste JSON des blobs qui matchent, ou "{}" si aucun
    - has_blob: booléen indicateur de présence (True/False)
    """
    if not display_names:
        return "{}", False

    masks = []
    for dn in display_names:
        if not dn:
            continue
        # Construit un masque des prefix pour ce display_name
        masks.append([dn.startswith(fn) for fn in blob_fullnames])

    if not masks:
        return "{}", False

    # OR logique des masques
    import numpy as np
    combined_mask = np.any(np.array(masks), axis=0)
    if not combined_mask.any():
        return "{}", False

    matched = blob.loc[combined_mask]
    matched_json = json.dumps(matched.to_dict(orient="records"), ensure_ascii=False)
    return matched_json, True

def _separation_accents(s: str) -> str:
    """Supprime les accents pour des comparaisons robustes."""
    try:
        return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')
    except Exception:
        return s

def creer_session_http(
    nb_reessais: int = 5,
    facteur_backoff: float = 1,
    codes_a_reessayer: Optional[List[int]] = None,
    ) -> requests.Session:
    """
    Crée une session HTTP Requests avec stratégie de réessai (retry).
    """
    if codes_a_reessayer is None:
        codes_a_reessayer = [429, 500, 502, 503, 504]

    session = requests.Session()
    retry = Retry(
        total=nb_reessais,
        read=nb_reessais,
        connect=nb_reessais,
        backoff_factor=facteur_backoff,
        status_forcelist=codes_a_reessayer,
        allowed_methods=["GET"],
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

# --------- Contexte projet + lecture unifiée des sources
def detecter_racine_projet(point_depart: Optional[Path] = None) -> Path:
    """Détecte la racine du projet (dossier Projet_3/) en remontant
    depuis un point de départ ou le fichier courant, en cherchant un marqueur
    tel que "pyproject.toml" ou "README.md".

    Retourne la racine détectée, ou le dossier parent immédiat si aucun marqueur n'est trouvé.
    """
    if point_depart is None:
        point_depart = Path(__file__).resolve()

    candidates: List[str] = ["pyproject.toml", "README.md", "workspace_5_.code-workspace"]
    p = point_depart
    for parent in [p] + list(p.parents):
        try:
            if parent.is_dir():
                for marker in candidates:
                    if (parent / marker).exists():
                        return parent
                # Heuristique: le nom du dossier correspond à "Projet_3"
                if parent.name.lower() == "projet_3":
                    return parent
        except Exception:
            continue
    # Fallback: racine du disque/dossier au-dessus
    return p.parent

def lire_sources_depuis_projet(
    feuille_excel_blob: Optional[str] = None,
    limit: Optional[int] = None,
    timeout_connect_read: Optional[Tuple[float, float]] = None,
    session: Optional[requests.Session] = None,
) -> Dict[str, pd.DataFrame]:
    """Lit les différentes sources (ODRE: métadata + ressources, et Excel Blob monitoring)
    en se basant sur le contexte global du projet (racine Projet_3/).

    - Détection de la racine du projet
    - Construction des chemins relatifs (input/MonitorBlob.xlsx) si disponible
    - Utilisation des constantes de `Config` (BASE_URL, API_KEY, LIMIT, TIMEOUT)

    Retour:
        dict avec clés: "meta", "ressources", "blob" (DataFrames éventuellement vides si échec)
    """
    # 1) Détecter la racine du projet
    racine = detecter_racine_projet()

    # 2) Préparer la session HTTP avec retries
    if session is None:
        session = creer_session_http(
            nb_reessais=getattr(Config, "TRY_CALL", 3),
            facteur_backoff=getattr(Config, "BACKOFT_FACT", 0.5),
            codes_a_reessayer=getattr(Config, "TRY_CODE", [429, 500, 502, 503, 504]),
        )

    # 3) Paramètres
    base_url_meta: str = getattr(Config, "BASE_URL", "").rstrip("/")
    base_url_res: str = base_url_meta  # même base, on ajoute /{uid}/resources
    api_key: str = getattr(Config, "API_KEY", "")
    limit = limit if limit is not None else getattr(Config, "LIMIT", 1000)
    timeout_connect_read = (
        timeout_connect_read if timeout_connect_read is not None else getattr(Config, "TIMEOUT_CONNECT", (15.0, 20.0))
    )

    # 4) Résoudre le chemin de l'extraction Blob
    #    Priorité au chemin relatif du projet (input/MonitorBlob.xlsx), sinon fallback Config.PATH_BLOB_MONITORING
    path_blob_rel = racine / "input" / "MonitorBlob.xlsx"
    if path_blob_rel.exists():
        path_excel_blob = str(path_blob_rel)
    else:
        path_excel_blob = getattr(Config, "PATH_BLOB_MONITORING", "")

    feuille_excel_blob = (
        feuille_excel_blob if feuille_excel_blob else getattr(Config, "FEUILLE_CIBLE_BLOB_MONITORING", "MonitorBlob(app)")
    )

    # 5) Appels ODRE: métadata
    meta_df: pd.DataFrame = pd.DataFrame()
    try:
        url_meta = f"{base_url_meta}?apikey={api_key}&limit={limit}"
        yes_no, payload_meta, _ = charger_metadata(
            url=url_meta,
            timeout_connect_read=timeout_connect_read,
            session=session,
        )
        if yes_no == "YES":
            meta_df = _normaliser_colonnes(payload_meta)
    except Exception as e:
        logging.error(f"Lecture métadata ODRE échouée: {e}")

    # 6) Appels ODRE: ressources
    ress_df: pd.DataFrame = pd.DataFrame()
    try:
        if not meta_df.empty and "uid" in meta_df.columns:
            liste_uids = (
                meta_df["uid"].dropna().astype(str).str.strip().unique().tolist()
            )
            yes_no, payload_ress, _ = charger_ressources(
                url=base_url_res,
                liste_uid=liste_uids,
                apikey=api_key,
                timeout=timeout_connect_read,
                proxies=getattr(Config, "PROXIES", {}),
                session=session,
            )
            if yes_no == "YES" and isinstance(payload_ress, pd.DataFrame):
                ress_df = _normaliser_colonnes(payload_ress)
    except Exception as e:
        logging.error(f"Lecture ressources ODRE échouée: {e}")

    # 7) Lecture Blob monitoring Excel
    blob_df: pd.DataFrame = pd.DataFrame()
    try:
        blob_df = charger_blob_excel_en_dataframe(
            path_excel=path_excel_blob,
            feuille_cible=feuille_excel_blob,
        )
        if not blob_df.empty:
            blob_df = _normaliser_colonnes(blob_df)
    except Exception as e:
        logging.error(f"Lecture Blob monitoring échouée: {e}")

    return {"meta": meta_df, "ressources": ress_df, "blob": blob_df}

# --------- Fonction d'appel API
def charger_blob_excel_en_dataframe(path_excel, 
                                    feuille_cible
    ) -> pd.DataFrame:
    "Chargement de la feuille excel + normalisation des colonnes blob"
    try:
        logging.info(f"Lecture extraction du Blob {feuille_cible} en cours...")
        print(f"Chargement données du blob en cours...")
        if not isinstance(path_excel, Path):
            path_excel = Path(path_excel)
        if not path_excel.exists():
            logging.error(f"Fichier excel introuvable: {path_excel}")
            return pd.DataFrame()

        try:
            df = pd.read_excel(path_excel, 
                               sheet_name=feuille_cible, 
                               engine="openpyxl"
                )
        except FileNotFoundError:
            logging.error(f"Classeur Excel introuvable: {path_excel}")
            return pd.DataFrame()

        # FullName_lower: s'il existe déjà, normaliser ; sinon bâtir à partir de FullName si présent
        if "FullName" in df.columns:
            df["FullName_lower"] = (
                df["FullName"].astype(str)
                .str.replace("\\", "/")
                .str.strip().str.lower()
                #.apply(_separation_accents)
            )
        else:
            # si aucune colonne, fournir un champ vide (matching ne trouvera rien)
            df["FullName_lower"] = ""

        # Normaliser Name et StorageContainerName (pour fallback)
        df["Name_lower"] = df.get("Name", pd.Series([""] * len(df))
                                  ).astype(str
                                           ).str.strip().str.lower().apply(_separation_accents)
        df["StorageContainerName_lower"] = df.get("StorageContainerName", pd.Series([""] * len(df))).astype(str).str.strip().str.lower().apply(_separation_accents)

        print(f"Données blob chargées avec succès!")
        return df

    except Exception as e:
        logging.error(f"Erreur dans la fonction [charger_blob_excel_en_dataframe]: {e}")

def charger_metadata(url: str,
                    timeout_connect_read: Tuple[float, float] = (5.0, 15.0),
                    session: Optional[requests.Session] = None,    
    
    ) -> Tuple[str, DataFrame, Optional[str]]:
    
    """
        Vérifie que l'endpoint ODRÉ renvoie du JSON exploitable et retourne le payload.
        
        :param url: URL de base de l'API (endpoint)
        :param timeout_connect_read: (connect_timeout, read_timeout)
        :param session: Session requests (avec retries), sinon créée par défaut

        :retour Typle: ("YES/NO", reponse_api, "Raison echec éventuel")
    """
    
    try:
        # Création de session si absente
        print(f"Chargement dondnées métadata encours...")
        if session is None:
            session = creer_session_http()
        response = session.get(url, timeout=timeout_connect_read)
        if response.status_code != 200:
            response.raise_for_status()
            return "NON", pd.DataFrame(), "Erreur HTTPS"
        data = response.json()
        payload = pd.json_normalize(data["results"])
        # Succès
        print(f"Données métadata chargée avec succès!")
        return "YES", payload, "Appel API réussi!"

    except requests.RequestException as e:
        logging.error(f"Erreur appel api: {e}")
        return "NO", pd.DataFrame(), "Raison: {e}"

def charger_ressources(url:str,
                        liste_uid:list[str],
                        apikey: str,
                        timeout: Tuple[float, float],
                        proxies: Optional[dict],
                        session: Optional[requests.Session] = None,
    
    )-> Tuple[str, DataFrame, Optional[str]]:
    
    """
        Description: Fonction auxiliaire qui retourne toutes les ressources pour chaque métada.
        Lien: uid dans métadata_odre et dans la construction d'un appel api pour les ressources
        
        :params  
                    url:str,
                    liste_uid:list[str],
                    apikey: str,
                    timeout: Tuple[float, float],
                    proxies: Optional[dict],
                    cles_canditates,
                    session: requests.Session,

        :retour Typle: ("YES/NO", reponse_api, "Raison echec éventuel")
    """
    try:
        # 0) Création de session si absente
        if session is None:
            session = creer_session_http()

        # 1) Requête + contrôle statut HTTP + construction de dataFrame
        liste_data_par_ressources = []
       
        for uid in liste_uid:
            # URL sécurisée (évite les doubles /)
            url_ressources = f"{url.rstrip('/')}/{uid}/resources?apikey={apikey}"
            print(f"UID-RESSOURCES: {uid} - {url}")
            response = session.get(url=url_ressources)
            if response.status_code != 200:
                logging.error(f"Erreur API_RESSOURCES: {response.status_code} - { response.text}")
                return "NO", None, f"Raison:{response.status_code}"
            
            data_ressources = response.json()
            
            # Normalisation en DataFrame

            payload = pd.json_normalize(data_ressources["results"])
            # Ajout de l'UID (de la métadata qui a permis la construction de la ressource)
            payload["uid_metadata"] = uid
            liste_data_par_ressources.append(payload)

        # Succès
        df_retourne = pd.concat(liste_data_par_ressources, axis=0, ignore_index=True)

        print(f"Données ressources chargées avec succès...")
        return "YES", df_retourne, f"Appel API Ressources réussi!"
    
    except Exception as e:
        logging.error(f"Erreur appel api: {e}")

# -- Fonction principale de construction et de modélisation des jdd ODRE
def construire_df_final_et_ecrire_fichiers(
    df_meta: pd.DataFrame,
    df_ressources: pd.DataFrame,
    df_blob: pd.DataFrame,
    out_parquet_path: str,
    out_csv_path: str = None,
    out_json_path: str = None,
) -> Dict[str, str]:
    """
    Docstring for construire_df_final_et_ecrire_fichiers 
    
    :param df_meta: Description
    :type df_meta: pd.DataFrame
    :param df_ressources: Description
    :type df_ressources: pd.DataFrame
    :param df_blob: Description
    :type df_blob: pd.DataFrame
    :param out_parquet_path: Description
    :type out_parquet_path: str
    :param out_csv_path: Description
    :type out_csv_path: str
    :param out_json_path: Description
    :type out_json_path: str
    :return: Description
    :rtype: Dict[str, str]
    """

    t0 = time.perf_counter()

    try:
        # --- Copies + normalisation
        meta = _normaliser_colonnes(df_meta.copy())
        ressources = _normaliser_colonnes(df_ressources.copy())
        blob = _normaliser_colonnes(df_blob.copy())

        # --- Validation colonnes
        required_meta = {"uid"}
        required_ress = {"uid_metadata", "display_name"}
        missing_meta = required_meta - set(meta.columns)
        if missing_meta:
            raise ValueError(f"Colonnes manquantes dans meta: {missing_meta} | dispo={sorted(meta.columns)}")
        missing_ress = required_ress - set(ressources.columns)
        if missing_ress:
            raise ValueError(f"Colonnes manquantes dans ressources: {missing_ress} | dispo={sorted(ressources.columns)}")

        # --- Renommer le UID propre aux ressources pour éviter conflit après merge
        if "uid" in ressources.columns:
            ressources = ressources.rename(columns={"uid": "uid_ressource"})

        # --- Blob fullname_lower
        if "Fullname_lower" not in blob.columns:
            if "FullName" in blob.columns:
                blob["FullName_lower"] = blob["FullName"].astype(str).str.lower().str.strip()
            else:
                raise ValueError(f"Blob doit contenir 'FullName_lower' ou 'FullName' | dispo={sorted(blob.columns)}")

        # --- Cast str partout
        meta = _typer_en_str(meta)
        ressources = _typer_en_str(ressources)
        blob = _typer_en_str(blob)

        # --- LEFT JOIN depuis META (cardinalité = méta)
        df_mr = meta.merge(
            ressources,
            left_on="uid",
            right_on="uid_metadata",
            how="left",
            suffixes=("_meta", "_ressource")
        )

        # --- Clé méta stable (au cas où)
        meta_uid_col = "uid" if "uid" in df_mr.columns else ("uid_meta" if "uid_meta" in df_mr.columns else None)
        if meta_uid_col is None:
            raise KeyError(f"Impossible de trouver la clé UID méta dans df_mr. Colonnes: {sorted(df_mr.columns)}")

        # --- display_name_lower
        df_mr["display_name_lower"] = df_mr["display_name"].astype(str).str.lower().str.strip()

        # --- Regroupement par méta : liste des display_name_lower
        grouped = (
            df_mr.groupby(meta_uid_col, dropna=False)["display_name_lower"]
                 .apply(lambda s: [d for d in s.tolist() if d])  # filtre vides
                 .reset_index()
        )
        uid_to_displaynames: Dict[str, List[str]] = dict(zip(grouped[meta_uid_col], grouped["display_name_lower"]))

        # --- ressources_json par méta (toutes les colonnes ressources)
        ressources_cols = [
            c for c in df_mr.columns
            if c.endswith("_ressource") or c in ["uid_metadata", "display_name", "display_name_lower"]
        ]
        ressources_per_uid = (
            df_mr.groupby(meta_uid_col, dropna=False)[ressources_cols]
                .apply(lambda d: json.dumps(
                    d.drop(columns=["display_name_lower"], errors="ignore").to_dict(orient="records"),
                    ensure_ascii=False
                ))
                .reset_index()
                .rename(columns={0: "ressources_json"})
        )
        uid_to_ressources_json: Dict[str, str] = dict(zip(ressources_per_uid[meta_uid_col], ressources_per_uid["ressources_json"]))

        # --- Prépare données blobs
        blob_fullnames: List[str] = blob["FullName_lower"].tolist()

        # --- df_final : une ligne par méta
        df_final = meta.copy()
        meta_key_col = "uid" if "uid" in df_final.columns else ("uid_meta" if "uid_meta" in df_final.columns else None)
        if meta_key_col is None:
            raise KeyError(f"Impossible de déterminer la clé UID dans meta. Colonnes: {sorted(meta.columns)}")

        df_final["ressources_json"] = df_final[meta_key_col].map(uid_to_ressources_json).fillna("[]")

        # --- matched_blobs_json + has_blob_monitoring (via helper extrait)
        df_final["matched_blobs_json"] = df_final[meta_key_col].map(
            lambda u: _match_blobs_pour_ressources(uid_to_displaynames.get(u, []), blob_fullnames, blob)[0]
        )
        df_final["has_blob_monitoring"] = df_final[meta_key_col].map(
            lambda u: "True" if _match_blobs_pour_ressources(uid_to_displaynames.get(u, []), blob_fullnames, blob)[1] else "False"
        )

        # --- Normalisation + cast str final
        df_final = _normaliser_colonnes(df_final)
        df_final = _typer_en_str(df_final)
        df_final["has_blob_monitoring"] = df_final["has_blob_monitoring"].str.lower()

        # --- Logs récap (matching réel)
        total_true = (df_final["has_blob_monitoring"] == "True").sum()
        logging.info(f"[BLOB] JDD monitorés (matching réel): {total_true} / {len(df_final)}")

        # --- Écritures
        for p in [out_parquet_path, out_csv_path, out_json_path]:
            if p:
                Path(p).parent.mkdir(parents=True, exist_ok=True)

        df_final.to_parquet(out_parquet_path, index=False)
        taille_bytes = os.path.getsize(out_parquet_path)
        taille_Ko = round(taille_bytes / 1024, 4)
        taille_Mo = round(taille_bytes / (1024 * 1024), 4)

        logging.info(
            " Parquet JDD final écrit: %s | lignes = %d | Taille(Mo) = %.4f | en %.3f seconde(s)",
            out_parquet_path,
            len(df_final),
            taille_Mo,
            time.perf_counter() - t0
        )

        if out_csv_path:
            df_final.to_csv(out_csv_path, index=False, encoding="utf-8")
        if out_json_path:
            df_final.to_json(out_json_path, orient="records", force_ascii=False)

        return {
            "df_final" : df_final,
            "rows": str(len(df_final)),                # <-- devrait valoir 454 (cardinalité méta)
            "size_bytes": str(taille_bytes),
            "size_Ko": str(taille_Ko),
            "size_Mo": str(taille_Mo),
            "Temps": str(round(time.perf_counter() - t0, 3))
        }

    except Exception as e:
        logging.exception("Erreur sortie (Exception): %s", e)
        raise


    except Exception as e:
        logging.exception("Erreur sortie (Exception): %s", e)
        raise

# -- Fonction principale pour faire correspondre les sources récupérées avec la modélisation des jdds
def lier_sources_jdds_modelises_0(sources: DataFrame) -> List[JddOdre]:

    """Traduire les extractions de sources en liste d'objets JddOdre.

    Hypothèses d'entrée:
    - sources contient au moins les colonnes méta définies dans Config.LISTE_CHAMPS_META.
    - Optionnellement, sources peut contenir ressources_json (liste d'objets JSON) et
      matched_blobs_json (liste d'objets JSON) produits par construire_df_final_et_ecrire_fichiers.

    Sortie:
    - Liste d'instances JddOdre peuplées à partir des lignes de sources.
    """

    if sources is None or not isinstance(sources, pd.DataFrame) or sources.empty:
        return []

    # Colonnes méta attendues et présentes
    champs_meta_attendus: Set[str] = set(getattr(Config, "LISTE_CHAMPS_META", []))
    champs_ress_attendus: Set[str] = set(getattr(Config, "LISTE_CHAMPS_RESSOURCES", []))
    champs_blobs_attendus: Set[str] = set(getattr(Config, "LISTE_CHAMPS_BLOB_MONITORING", []))

    champs_meta_presents: List[str] = [c for c in sources.columns if c in champs_meta_attendus]
    champs_ress_presents: List[str] = [c for c in sources.columns if c in champs_ress_attendus]
    champs_blobs_presents: List[str] = [c for c in sources.columns if c in champs_blobs_attendus]

    # Colonnes utiles
    uid_col: Optional[str] = "uid" if "uid" in sources.columns else ("uid_meta" if "uid_meta" in sources.columns else None)
    dataset_id_col: Optional[str] = "dataset_id" if "dataset_id" in sources.columns else None

    resultat: List[JddOdre] = []

    for idx, row in sources.iterrows():
        # id_jdd_odre: utiliser l'index si entier, sinon None
        id_jdd_odre: Optional[int] = idx if isinstance(idx, int) else None

        # nom_jdd_odre: privilégier dataset_id
        nom_jdd_odre: Optional[str] = None
        if dataset_id_col:
            nom_jdd_odre = str(row.get(dataset_id_col, ""))
        else:
            # fallback: uid
            if uid_col:
                nom_jdd_odre = str(row.get(uid_col, ""))
            else:
                nom_jdd_odre = ""

        # Métadonnées: prendre les colonnes méta présentes
        metadonnees: Dict[str, str] = {}
        for col in champs_meta_presents:
            try:
                val = row.get(col)
            except Exception:
                val = None
            metadonnees[col] = "" if pd.isna(val) else str(val)

    # Ressources: prendre les colonnes ressources présentes
        ressources: Dict[str, str] = {}
        for col in champs_ress_presents:
            try:
                val = row.get(col)
            except Exception:
                val = None
            ressources[col] = "" if pd.isna(val) else str(val)

    # Blobs monitoring: prendre les colonnes blobs présentes
        blobs_monitoring: Dict[str, str] = {}
        for col in champs_blobs_presents:
            try:
                val = row.get(col)
            except Exception:
                val = None
            blobs_monitoring[col] = "" if pd.isna(val) else str(val)

        # Création de l'objet JddOdre
        jdd = JddOdre(
            id_jdd_odre=id_jdd_odre,
            nom_jdd_odre=nom_jdd_odre,
            metadonnees=metadonnees or None,
            ressources=ressources,
            PDA_opendata=blobs_monitoring,
        )

        resultat.append(jdd)

    return resultat


def lier_sources_jdds_modelises(sources: DataFrame) -> List[JddOdre]:
    if sources is None or not isinstance(sources, pd.DataFrame) or sources.empty:
        return []

    champs_meta_attendus: Set[str] = set(getattr(Config, "LISTE_CHAMPS_META", []))
    champs_ress_attendus: Set[str] = set(getattr(Config, "LISTE_CHAMPS_RESSOURCES", []))
    champs_blobs_attendus: Set[str] = set(getattr(Config, "LISTE_CHAMPS_BLOB_MONITORING", []))

    champs_meta_presents = [c for c in sources.columns if c in champs_meta_attendus]
    champs_ress_presents = [c for c in sources.columns if c in champs_ress_attendus]
    champs_blobs_presents = [c for c in sources.columns if c in champs_blobs_attendus]

    cols_json_ress = set(getattr(Config, "LISTE_COLS_JSON_RESSOURCES", ["ressources_json"]))
    cols_json_pda  = set(getattr(Config, "LISTE_COLS_JSON_PDA", ["matched_blobs_json"]))

    cols_json_ress_presents = [c for c in sources.columns if c in cols_json_ress]
    cols_json_pda_presents  = [c for c in sources.columns if c in cols_json_pda]

    uid_col = "uid" if "uid" in sources.columns else ("uid_meta" if "uid_meta" in sources.columns else None)
    dataset_id_col = "dataset_id" if "dataset_id" in sources.columns else None

    resultat: List[JddOdre] = []

    for idx, row in sources.iterrows():
        id_jdd_odre: Optional[int] = idx if isinstance(idx, int) else None
        nom_jdd_odre = str(row.get(dataset_id_col or uid_col, "") or "")

        # Métadonnées à plat
        metadonnees: Dict[str, Any] = {}
        for col in champs_meta_presents:
            val = row.get(col)
            metadonnees[col] = "" if (val is None or (isinstance(val, float) and pd.isna(val))) else str(val)

        # Ressources : priorité au JSON
        ressources: Any = None
        for col in cols_json_ress_presents:
            parsed = parser_json_dans_le_parquet(row.get(col))
            if parsed is not None:
                ressources = parsed
                break
        if ressources is None:
            ress_flat: Dict[str, Any] = {}
            for col in champs_ress_presents:
                val = row.get(col)
                ress_flat[col] = "" if (val is None or (isinstance(val, float) and pd.isna(val))) else str(val)
            ressources = ress_flat if ress_flat else {}

        # PDA : priorité au JSON
        pda_opendata: Any = None
        for col in cols_json_pda_presents:
            parsed = parser_json_dans_le_parquet(row.get(col))
            if parsed is not None:
                pda_opendata = parsed
                break
        if pda_opendata is None:
            blobs_flat: Dict[str, Any] = {}
            for col in champs_blobs_presents:
                val = row.get(col)
                blobs_flat[col] = "" if (val is None or (isinstance(val, float) and pd.isna(val))) else str(val)
            pda_opendata = blobs_flat if blobs_flat else {}

        resultat.append(JddOdre(
            id_jdd_odre=id_jdd_odre,
            nom_jdd_odre=nom_jdd_odre,
            metadonnees=metadonnees or None,
            ressources=ressources,
            PDA_opendata=pda_opendata,
        ))

    return resultat


# ========> Application 1 en une seule fonction : Pour récupérer les sources externes
def construire_parquet_jdd_odre_en_direct_0(
        base_url_meta:str,
        base_url_res: str,
        api_key: str,
        chemin_parquet_final: str,
        chemin_csv_final: str,
        chemin_json_final: str,
        path_excel_blob: str,
        feuille_excel_blob: str,
        proxies: Optional[dict],
        timeout: Tuple[float, float],
        session: requests.Session,
        limit: int
    #) -> Tuple[DataFrame, DataFrame, DataFrame]:
    ) -> Tuple[dict, pd.DataFrame, pd.DataFrame]:
    
    """
        Description: Construit le Parquet final 'JDD ODRE" en une seule passe et avec des auxiliaires lisibles.
        :params  
                base_rul_meta:str,
                base_url_res: str,
                api_key: str,
                chemin_parquet_final: str,
                path_excel_blob: str,
                feuille_excel_blob: str,
                cles_candidates: list,
                proxies: Optional[dict],
                timeout: Tuple[float, float],
                session: requests.Session,
                limit: int

        :retour pd.DataFrame1, pd.DataFrame2, pd.DataFrame3
    """
    try:
        t0 = time.perf_counter()
        url_meta = f"{base_url_meta}?apikey={api_key}&limit={limit}"
        yes_no, reponse_api_metadata, raison = charger_metadata(url=url_meta,
                                                            timeout_connect_read=timeout,
                                                            session=session
        )
        reponse_api_metadata_norm = _normaliser_colonnes(reponse_api_metadata)

        # récupération des ressources associées aux metadata_odre
        liste_uids = (
            reponse_api_metadata_norm["uid"].
            dropna()
            .astype(str)
            .str.strip()
            .unique()
            .tolist()

        )
        yes_no, reponse_api_ressources, raison = charger_ressources(base_url_res,
                                                                    liste_uids,
                                                                    api_key,
                                                                    timeout,
                                                                    proxies,
                                                                    session=session
        )
        reponse_api_ressources_norm = _normaliser_colonnes(reponse_api_ressources)

        df_extraction_blob_monitoring = charger_blob_excel_en_dataframe(path_excel=path_excel_blob,
                                    feuille_cible=feuille_excel_blob
        )
        extraction_blob_monitoring_norm = _normaliser_colonnes(df_extraction_blob_monitoring)

        
        constructions = construire_df_final_et_ecrire_fichiers(reponse_api_metadata_norm,
                                                                reponse_api_ressources_norm,
                                                                extraction_blob_monitoring_norm,
                                                                chemin_parquet_final,
                                                                chemin_csv_final,
                                                                chemin_json_final,
        )

        return constructions, reponse_api_ressources_norm, extraction_blob_monitoring_norm
    
    except Exception as e:
        logging.error(f"Erreur sortie: {e}")
        return {}, pd.DataFrame(), pd.DataFrame()

# ========> Copie étendue: construit et retourne un DataFrame "sources" complet sans écrire de fichiers
def lecture_du_parquet(path: Path) -> Optional[pd.DataFrame]:
    """
    Lecture robuste:
    - Fichier .parquet : pd.read_parquet
    - Dossier partitionné : pyarrow.dataset.dataset (si dispo), sinon fallback
    Retourne None en cas d'erreur (la couche appelante loguera).
    """
    try:
        if path.is_file():
            return pd.read_parquet(path)
        if path.is_dir():
            try:
                df = dataset(str(path), format="parquet")
                table = df.to_table()
                return table.to_pandas()
            except ImportError:
                # Fallback : selon les versions, pandas peut lire un dossier si pyarrow est dispo
                return pd.read_parquet(path)
        return None
    except Exception as e:
        logger.exception(f"Erreur lecture parquet sur '{path}': {e}")
        return None


def parser_json_dans_le_parquet(value: Any) -> Optional[Any]:
    """
    Tente de parser une valeur JSON.
    - Retourne dict/list si succès
    - Retourne None si value est None ou parsing échoue
    - Si value est déjà dict/list, le retourne tel quel
    - Supporte bytes/bytearray (decode utf-8)
    """
    if value is None:
        return None
    if isinstance(value, (dict, list)):
        return value
    if isinstance(value, (bytes, bytearray)):
        try:
            value = value.decode("utf-8")
        except Exception:
            return None
    if isinstance(value, str):
        txt = value.strip()
        if not txt:
            return None
        try:
            return json.loads(txt)
        except Exception:
            return None
    return None

def construire_sources_jdd_odre_en_direct(
        base_url_meta: str,
        base_url_res: str,
        api_key: str,
        path_excel_blob: str,
        feuille_excel_blob: str,
        proxies: Optional[dict],
        timeout: Tuple[float, float],
        session: Optional[requests.Session],
        limit: int
    ) -> pd.DataFrame:
    """
    Construit un DataFrame "sources" réunissant:
    - colonnes de métadonnées (selon Config.LISTE_CHAMPS_META)
    - colonnes de ressources (selon Config.LISTE_CHAMPS_RESSOURCES)
    - colonnes de blobs (selon Config.LISTE_CHAMPS_BLOB_MONITORING)

    La forme résultante est destinée à lier_sources_jdds_modelises (couche domaine).
    """
    try:
        # 1) Métadonnées
        url_meta = f"{base_url_meta}?apikey={api_key}&limit={limit}"
        yes_no, df_meta, _ = charger_metadata(
            url=url_meta,
            timeout_connect_read=timeout,
            session=session,
        )
        meta = _normaliser_colonnes(df_meta) if yes_no == "YES" else pd.DataFrame()

        # 2) Ressources associées aux métadonnées
        ressources = pd.DataFrame()
        if not meta.empty and "uid" in meta.columns:
            liste_uids = (
                meta["uid"].dropna().astype(str).str.strip().unique().tolist()
            )
            yes_no_r, df_ress, _ = charger_ressources(
                url=base_url_res,
                liste_uid=liste_uids,
                apikey=api_key,
                timeout=timeout,
                proxies=proxies,
                session=session,
            )
            if yes_no_r == "YES" and isinstance(df_ress, pd.DataFrame):
                ressources = _normaliser_colonnes(df_ress)

        # 3) Blob monitoring (Excel)
        blob = charger_blob_excel_en_dataframe(
            path_excel=path_excel_blob,
            feuille_cible=feuille_excel_blob,
        )
        blob = _normaliser_colonnes(blob) if isinstance(blob, pd.DataFrame) else pd.DataFrame()

        if meta.empty:
            return pd.DataFrame()

        # 4) Préparation des colonnes auxiliaires
        #    a) ressources: s'assurer qu'on a la clé de jointure 'uid_metadata'
        if not ressources.empty and "uid" in ressources.columns:
            ressources = ressources.rename(columns={"uid": "uid_ressource"})
        # La clé d'association descendante est déjà "uid_metadata" côté ressources

        #    b) blob: assurer la présence des colonnes en minuscules attendues
        #       en les mappant depuis les colonnes Excel si nécessaire
        if "FullName_lower" in blob.columns and "fullName_lower" not in blob.columns:
            blob["FullName_lower"] = blob["FullName_lower"].astype(str)
        elif "FullName_lower" not in blob.columns:
            blob["FullName_lower"] = ""

        if "Name_lower" in blob.columns and "name_lower" not in blob.columns:
            blob["name_lower"] = blob["Name_lower"].astype(str)
        elif "name_lower" not in blob.columns:
            blob["name_lower"] = ""

        if "StorageContainerName_lower" in blob.columns and "storagecontainername_lower" not in blob.columns:
            blob["storagecontainername_lower"] = blob["StorageContainerName_lower"].astype(str)
        elif "storagecontainername_lower" not in blob.columns:
            blob["storagecontainername_lower"] = ""

        # 5) Merge META x RESSOURCES (une ligne par ressource; meta répliqué)
        if not ressources.empty and "uid_metadata" in ressources.columns:
            df_mr = meta.merge(
                ressources,
                left_on="uid",
                right_on="uid_metadata",
                how="left",
                suffixes=("", ""),
            )
        else:
            # Pas de ressources: sources = meta uniquement
            df_mr = meta.copy()

        # 6) Matching blobs par RESSOURCE (logique prefix sur display_name)
        if "display_name" in df_mr.columns:
            df_mr["display_name_lower"] = df_mr["display_name"].astype(str).str.lower().str.strip()
        else:
            df_mr["display_name_lower"] = ""

        blob_fullnames = blob["FullName_lower"].astype(str).tolist() if not blob.empty else []

        matched_blob_json_list: List[str] = []
        has_blob_flags: List[str] = []

        for _, r in df_mr.iterrows():
            dn = str(r.get("display_name_lower", "") or "")
            has = False
            blob_row: Dict[str, Any] = {}
            if dn and blob_fullnames:
                mask = [dn.startswith(fn) if isinstance(fn, str) and fn else False for fn in blob_fullnames]
                if any(mask):
                    idx_match = mask.index(True)
                    matched = blob.iloc[idx_match]
                    blob_row = matched.to_dict()
                    has = True
            matched_blob_json_list.append(json.dumps(blob_row, ensure_ascii=False) if blob_row else "{}")
            has_blob_flags.append("True" if has else "False")

        df_mr["matched_blobs_json"] = matched_blob_json_list
        df_mr["has_blob_monitoring"] = has_blob_flags

        # 7) Extraire (premier) blob match en colonnes de synthèse attendues par Config
        def _premier_blob(cols_json: str) -> Dict[str, Any]:
            try:
                lst = json.loads(cols_json) if isinstance(cols_json, str) else []
                return lst[0] if lst else {}
            except Exception:
                return {}

        premiere_blob = df_mr["matched_blobs_json"].apply(_premier_blob)
        # Mapper quelques champs standards si disponibles
        df_mr["name"] = premiere_blob.apply(lambda d: d.get("Name") or d.get("name") or "")
        df_mr["size"] = premiere_blob.apply(lambda d: d.get("Size") or d.get("size") or "")
        df_mr["lastmodified"] = premiere_blob.apply(lambda d: d.get("LastModified") or d.get("lastmodified") or "")
        df_mr["boolisdeleted"] = premiere_blob.apply(lambda d: d.get("BoolIsDeleted") or d.get("boolisdeleted") or "")
        df_mr["contenttype"] = premiere_blob.apply(lambda d: d.get("ContentType") or d.get("contenttype") or "")
        df_mr["storageaccountname"] = premiere_blob.apply(lambda d: d.get("StorageAccountName") or d.get("storageaccountname") or "")
        df_mr["storagecontainername"] = premiere_blob.apply(lambda d: d.get("StorageContainerName") or d.get("storagecontainername") or "")
        df_mr["FullName"] = premiere_blob.apply(lambda d: d.get("FullName") or d.get("FullName") or "")

        # 8) Normaliser colonnes (remplacement . et -) et typer en str
        sources_df = _normaliser_colonnes(df_mr)
        sources_df = _typer_en_str(sources_df)

        return sources_df

    except Exception as e:
        logging.error(f"Erreur construire_sources_jdd_odre_en_direct: {e}")
        return pd.DataFrame()

# ========> Connecteur concret implémentant le port PortdeRecuperationJDD
def _is_cache_fresh(file_path: str, ttl_minutes: int) -> bool:
    """Retourne True si le fichier de cache existe et est plus récent que le TTL."""
    try:
        p = Path(file_path)
        if not p.exists():
            return False
        mtime = datetime.fromtimestamp(p.stat().st_mtime)
        now = datetime.now()
        return (now - mtime) <= timedelta(minutes=max(ttl_minutes, 0))
    except Exception:
        return False



# ===== Fonctions auxilaires | Fonction pour inspecter les métadonnées des sources ====== #
#       BUT:  inspecter les sources en local pour les recharger au besoin (par l'utilisateur de l'application)

# --------- Fonctions auxiliaires
def _conversion_horaire(iso_ts: str,
                       tz: Optional[ZoneInfo]=None
    ) -> str:
    """
    Docstring for conversion_horaire
        Convertit un timestamp ISO en âge horaire
    :param iso_ts: Description
    :type iso_ts: str
    :param tz: Description
    :type tz: Optional[ZoneInfo]
    :return: Description
    :rtype: str
    """
    try:
        dt = datetime.fromisoformat(iso_ts)
    except Exception:
        return "inconnue"
    tz = tz or dt.tzinfo or Config.TIME_ZONE
    now = datetime.now(tz)
    delta = now - dt.astimezone(tz)
    s = int(delta.total_seconds)
    if s < 60:
        return f"{s} s"
    m, s = divmod(s, 60)
    if m < 60:
        return f"{m} min"
    h, m = divmod(m, 60)
    if h < 24:
        return f"{h} h - {m} min"
    d, h = divmod(h, 24)
    return f"{d} j - {h} h"

def _securisation_dossier_cache_sources(p: str) -> Path:
    """
    Docstring for securisation_dossier_cache_sources
        Sécurise de chemin défin dans Config
    :param p: Description
    :type p: str
    :return: Description
    :rtype: Path
    """
    chemin = Path(p)
    chemin.parent.mkdir(parents=True, exist_ok=True)
    return chemin

def _securisation_dossier_cache_sources(chemin: str | Path) -> Path:
    """
    Normalise le chemin sous forme Path et garantit que le dossier parent existe.
    """
    p = Path(chemin)
    p.parent.mkdir(parents=True, exist_ok=True)
    return p

def _conversion_horaire(iso_ts: str, tz: Optional[ZoneInfo] = None) -> str:
    """
    Convertit un timestamp ISO en 'âge' humain (fr) : '2 h 13 min', '3 j 1 h', etc.
    """
    try:
        dt = datetime.fromisoformat(iso_ts)
    except Exception:
        return "inconnue"

    tz = tz or dt.tzinfo or Config.TIME_ZONE
    now = datetime.now(tz)
    delta = now - dt.astimezone(tz)
    s = int(delta.total_seconds())
    if s < 60:
        return f"{s} s"
    m, s = divmod(s, 60)
    if m < 60:
        return f"{m} min"
    h, m = divmod(m, 60)
    if h < 24:
        return f"{h} h {m} min"
    d, h = divmod(h, 24)
    return f"{d} j {h} h"


# =============== Pré-chargement / lecture des sources ===============
#       BUT: charger les sources pour le demarrage de l'application
def lecture_des_donnees_sources() -> pd.DataFrame:
    """
    Lecture simple du parquet ODRE depuis Config.JDD_ODRE_PATH_PARQUET.
    - Retourne un DataFrame (vide si fichier absent/erreur).
    - À étendre si tu ajoutes d'autres sources (2 APIs + blob local).
    """
    try:
        parquet_path = Path(Config.JDD_ODRE_PATH_PARQUET)
        if not parquet_path.exists():
            return pd.DataFrame()
        # Lecture du parquet (pyarrow requis si gros fichiers ; ici on se contente du défaut)
        df = pd.read_parquet(parquet_path, engine="pyarrow")
        return df
    except Exception:
        return pd.DataFrame()

def _normaliser_df_metadata(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalise les colonnes minimales attendues par l'UI/Service (création vide si absentes).
    """
    if df is None or df.empty:
        return pd.DataFrame()
    df = df.copy()
    expected_cols = [
        "uid", "title", "publisher",
        "created_at", "updated_at",
        "dataset_id", "asset_type", "modified", "language",
        "description", "maille_geographique", "pas_temporel",
        "profondeur_dhistorique", "reseaux", "energie",
        "gestionnaire_technique_de_la_donnee", "gestionnaire_metier_de_la_donnee",
        "direction_metier_concernee", "tags",
        "type_de_source_de_donnees", "source_de_la_donnee",
        "sla", "enjeux", "theme"
    ]
    for c in expected_cols:
        if c not in df.columns:
            df[c] = ""
    return df


