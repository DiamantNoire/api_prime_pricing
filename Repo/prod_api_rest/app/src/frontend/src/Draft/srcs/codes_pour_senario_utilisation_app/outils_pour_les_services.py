# --- Application de supervision des jeux de données ODRE
# chemin: srcs/codes_pour_senario_utilisation_app/outils_pour_services.py
# ==== coding: utf-8 ====

# === importation de librairies ===
from __future__ import annotations


from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import json
import gzip

import json
from typing import Optional, Tuple
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import pandas as pd
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from typing import List, Dict, Any
from itertools import islice
import pandas as pd
import re
import pandas as pd
import json
from pathlib import Path

from pathlib import Path
from typing import List, Any, Optional
import json
import dataclasses
import os
import tempfile

from typing import List, Dict, Any, Optional
import math

import json
from typing import Any, List, Dict, Optional
from datetime import datetime
import pandas as pd

import pyarrow.parquet as pq
import json
import json
import secrets
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional, List
import streamlit as st
from srcs.configs import Configurations

import json
import secrets
import hashlib


import math
from typing import Any, Optional
from pandas.api.types import is_scalar
import pandas as pd
import numpy as np


# === Importation de modules ===
from srcs.configs import Configurations
from srcs.codes_pour_metier_admin_jdd_odre_app.modelisation_jdd_odre import JddOdre
from srcs.codes_pour_sources_externes_app.outils_pour_sources_externes import(
    alimenter_app_en_data_test
)

# --- utilitaires internes -----------------------------------------------------


# =============================================================================
# Regroupement par type service d'orchestration
#   - Orchestration 1 : Service d'alimentation de l'app en données externes 
#   - Orchestration 2 : Service de lecture des données sauvegardées dans l'app
 
#   - Orchestration 3 : Service de traitement des données pour la page 0
#   - Orchestration 4 : Service de traitement des données pour la page 1
#   - Orchestration 5 : Service de traitement des données pour la page 2
#   - Orchestration 6 : Service de traitement des données pour la page 3
#   - Orchestration 7 : Service de traitement des données pour la page 4
#   - Orchestration 8 : Service de traitement des données pour la page 5
#   - Orchestration 9 : Service de traitement des données pour la page 6
# =============================================================================




# =============================================================================
#   - Orchestration 1 : Service d'alimentation de l'app en données externes 
# =============================================================================
#-----Alimentation manuelle (en option par l'ulisateur) --------------
def declencher(declencheur: Optional[str] = "NON") -> str:
    """
    Alimenter l'application de supervision sous l'action de l'utilisateur.
    - Si declencheur == 'OUI': on alimente
    - Sinon: on ne fait rien.

    :param declencheur: str
    :return: 'OUI' pour déclencher; 'NON' par défaut.
    """
    if declencheur == "NON":
        return "NON"

    les_connecteurs = Configurations.CONNECTEURS
    try:
        _, _, _ = alimenter_app_en_data_test(connecteurs=les_connecteurs)
        return "OUI."
    except Exception as exc:
        print(f"[Couche: cas d'utilisation] | Module : outils_pour_les_services\n")
        print(f"[Couche: cas d'utilisation] | Fonction : declencher\n")
        raise RuntimeError(f"[erreur]: {exc}")



# =============================================================================
#   Orchestration 2 : Service de lecture des données sauvegardées dans l'app 
# =============================================================================
def lire_metadata(chemin_fichier:Optional[str]) -> pd.DataFrame:
    """
        Fonction utilitaire: lecture d'un fichier json depuis l'application
        Retour: dataFrame
    """
    try:
        with open(chemin_fichier, "r", encoding="utf-8") as f:
            sources_externe_metadata = json.load(f)
        return pd.DataFrame(sources_externe_metadata)
    except Exception as e :
            print(f"[Couche: cas d'utilisation] | Module : outils_pour_les_services\n")
            print(f"[Couche: cas d'utilisation] | Fonction : lire_metadata\n")
            raise RuntimeError(f"[erreur]: {e}")
    
def lire_ressources(chemin_fichier:Optional[str]) -> pd.DataFrame:
    """
        Fonction utilitaire: lecture d'un fichier json depuis l'application
        Retour: dataFrame
    """
    try:
        with open(chemin_fichier, "r", encoding="utf-8") as f:
            sources_externe_ressources = json.load(f)
        return pd.DataFrame(sources_externe_ressources)
    except Exception as e :
            print(f"[Couche: cas d'utilisation] | Module : outils_pour_les_services\n")
            print(f"[Couche: cas d'utilisation] | Fonction : lire_ressources\n")
            raise RuntimeError(f"[erreur]: {e}")

def lire_extraction_blob_opendata(chemin_fichier:Optional[str]) -> pd.DataFrame:
    """
        Fonction utilitaire: lecture d'un fichier json depuis l'application
        Retour: dataFrame
    """
    try:
        with open(chemin_fichier, "r", encoding="utf-8") as f:
            sources_externe_blob_opendata = json.load(f)
        return pd.DataFrame(sources_externe_blob_opendata)
    except Exception as e :
            print(f"[Couche: cas d'utilisation] | Module : outils_pour_les_services\n")
            print(f"[Couche: cas d'utilisation] | Fonction : lire_extraction_blob_opendata\n")
            raise RuntimeError(f"[erreur]: {e}")


# =============================================================================
#   - Orchestration 3 : Service de traitement des données pour la page 0
# =============================================================================

# --- Phase de connexion à l'application ---

# ---------- Stockage utilisateurs (utilisateur.json) ----------
def _chemin_vers_utilisateurs_json() -> Path:
    return Path(Configurations.CHEMIN_FICHIER_UTILISATEURS)

def _init_store_dict() -> Dict[str, Any]:
    return {"utilisateur": {}}  

def _charger_utilisateur() -> Dict[str, Any]:

    path = _chemin_vers_utilisateurs_json()
    path.parent.mkdir(parents=True, exist_ok=True)

    # Si le fichier est absent ou vide -> init
    if (not path.exists()) or (path.stat().st_size == 0):
        path.write_text(json.dumps(_init_store_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
        return _init_store_dict()

    # Lecture robuste (utf-8-sig pour absorber un BOM)
    try:
        raw = path.read_text(encoding="utf-8-sig")
        data = json.loads(raw)
        # Sécurité : si la clé 'utilisateur' manque, on la crée
        if "utilisateur" not in data or not isinstance(data["utilisateur"], dict):
            data["utilisateur"] = {}
        return data
    except json.JSONDecodeError:
        # Fichier corrompu -> backup puis réinit
        backup = path.with_suffix(path.suffix + f".bak_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        try:
            path.replace(backup)
        except Exception:
            pass
        path.write_text(json.dumps(_init_store_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
        return _init_store_dict()

def _sauvegarder_utilisateur(store: Dict[str, Any]) -> None:
    path = _chemin_vers_utilisateurs_json()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(store, ensure_ascii=False, indent=2), encoding="utf-8")

# ---------- Hash / Verify (lib standard) ----------
# Format stocké: { "algo": "pbkdf2-sha256", "salt": "<hex>", "iter": 200000, "hash": "<hex>" }
#ITERATIONS = 200_000

def _hacher_mot_de_passe(password: str) -> Dict[str, Any]:
    salt = secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations=Configurations.ITERATIONS)
    return {
        "algo": "pbkdf2-sha256",
        "salt": salt.hex(),
        "iter": Configurations.ITERATIONS,
        "hash": dk.hex(),
    }

def _verifier_mot_de_passe(password: str, meta: Dict[str, Any]) -> bool:
    if not meta or meta.get("algo") != "pbkdf2-sha256":
        return False
    salt = bytes.fromhex(meta.get("salt", ""))
    iters = int(meta.get("iter", Configurations.ITERATIONS))
    expected = bytes.fromhex(meta.get("hash", ""))
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iters)
    return secrets.compare_digest(dk, expected)

# ---------- API simple: signup / login / logout / require_auth ----------
def inscrire_utilisateur(identifiant: str, mot_de_passe: str, intitule: Optional[str]) -> Tuple[bool, str]:
    identifiant = (identifiant or "").strip()
    if not identifiant:
        return False, "Identifiant vide."
    if not mot_de_passe or len(mot_de_passe) < 8:
        return False, "Mot de passe trop court (min 8)."

    # Rôles depuis le mapping
    roles = Configurations.MAPPING_INTITULE_VERS_ROLES.get(intitule or "", [])
    if not roles:
        return False, "Intitulé inconnu. Veuillez choisir un intitulé valide."

    store = _charger_utilisateur()
    if identifiant in store.get("utilisateur", {}):
        return False, "Cet utilisateur existe déjà."

    pwd_meta = _hacher_mot_de_passe(mot_de_passe)
    store["utilisateur"][identifiant] = {
        "password": pwd_meta,
        "roles": roles,
        "intitule": intitule,
    }
    _sauvegarder_utilisateur(store)
    return True, "Inscription réussie. Vous pouvez vous connecter."

def connecter_utilisateur(identifiant: str, mot_de_passe: str) -> Tuple[bool, str, Optional[List[str]]]:
    store = _charger_utilisateur()
    rec = store.get("utilisateur", {}).get(identifiant)
    if not rec:
        return False, "Utilisateur inconnu. Inscrivez-vous si nécessaire.", None

    ok = _verifier_mot_de_passe(mot_de_passe, rec.get("password", {}))
    if not ok:
        return False, "Mot de passe invalide.", None

    # Session Streamlit
    st.session_state["auth_ok"] = True
    st.session_state["utilisateur"] = identifiant
    st.session_state["roles"] = rec.get("roles", [])
    return True, f"Bienvenue {identifiant} !", rec.get("roles", [])

def se_deconnecter() -> None:
    for k in ("auth_ok", "utilisateur", "roles"):
        st.session_state.pop(k, None)


def exiger_auth(roles_requis: Optional[List[str]] = None) -> None:
    if not st.session_state.get("auth_ok"):
        st.warning("Vous devez vous connecter.")
        st.stop()
    if roles_requis:
        user_roles = set(st.session_state.get("roles", []))
        if user_roles.isdisjoint(set(roles_requis)):
            st.error("Accès refusé (rôle requis).")
            st.stop()


# --- helpers robustes ---
def est_null(v: Any) -> bool:
    """
    True uniquement pour les SCALAIRES NA (None, NaN, pd.NA).
    Pour les non-scalaires (list, tuple, dict, np.ndarray, pd.Series), retourne False
    afin d'éviter d'évaluer un tableau dans un contexte booléen.
    """
    # Cas le plus courant
    if v is None:
        return True

    # Si scalaire, on peut utiliser pd.isna en sécurité
    if is_scalar(v):
        try:
            return pd.isna(v)
        except Exception:
            if isinstance(v, float):
                try:
                    return math.isnan(v)
                except Exception:
                    return False
            return False

    # Non-scalaire -> on ne considère pas "null" ici
    return False

def est_vide(v: Any) -> bool:
    """
    Vide si :
      - est_null(v) == True
      - chaîne vide/whitespace
      - conteneur de taille 0 (list/tuple/set/dict)
      - ndarray/Series de taille 0
    Ne tente JAMAIS d'évaluer un array comme booléen.
    """
    if est_null(v):
        return True

    if isinstance(v, str):
        return v.strip() == ""

    # Numpy / pandas : vérifier la taille pour éviter toute ambiguïté
    if isinstance(v, (np.ndarray, pd.Series)):
        return v.size == 0

    # Conteneurs Python usuels
    if isinstance(v, (list, tuple, set, dict)):
        return len(v) == 0

    # Pour le reste, on ne le considère pas vide
    return False

def normaliser(v: Any) -> Optional[Any]:
    """Remplace NaN/pd.NA par None ; laisse le reste tel quel (y compris conteneurs)."""
    return None if est_null(v) else v

def extraction_interne(d: Dict[str, Any], prefix: str) -> Dict[str, Any]:
    """
    Dans tes conteneurs, le contenu réel est sous une clé 'prefix_<position>' :
    - metadata_<n>
    - ressources_<n>
    - blob_<n>
    On récupère ce dict interne proprement.
    """
    for k in d.keys():
        if k.startswith(f"{prefix}_"):
            val = d.get(k, {})
            return val if isinstance(val, dict) else {}
    return {}

# --- assemblage des JDDs selon tes Conditions 1 & 2 ---
def assemblage(
    liste_metadata: List[Dict[str, Any]],
    liste_ressources: List[Dict[str, Any]],
    liste_blob_opendata: List[Dict[str, Any]],
) -> List[JddOdre]:
    # 1) Indexer les ressources par uid_metadata / uid_metadta (tolérance aux deux orthographes)
    ressources_par_uid: Dict[str, List[Dict[str, Any]]] = {}

    for rwrap in liste_ressources:
        r = extraction_interne(rwrap, "ressources")
        # Tenter plusieurs clés possibles pour l'UID des ressources
        uid_r = r.get("uid_metadta")
        if est_vide(uid_r):
            uid_r = r.get("uid_metadata")
        if est_vide(uid_r):
            uid_r = r.get("uid")  # fallback si nomenclature hétérogène

        if not est_vide(uid_r):
            key = str(uid_r)
            ressources_par_uid.setdefault(key, []).append(r)

    # 2) Préparer les blobs (contenu interne + champ FullName_lower en minuscule)
    blobs_prepares: List[Dict[str, Any]] = []
    for bwrap in liste_blob_opendata:
        b = extraction_interne(bwrap, "blob")
        full = str(b.get("FullName_lower", "")).lower()
        blobs_prepares.append({"blob": b, "full_lower": full})

    # 3) Assembler chaque JDD à partir de chaque métadonnée
    jdds: List[JddOdre] = []

    for mwrap in liste_metadata:
        # a) Métadonnée
        m = extraction_interne(mwrap, "metadata")
        numero_metadata = mwrap.get("numero_metadata")
        uid_meta = m.get("uid")
        dataset_id = m.get("dataset_id")

        # b) Ressources (Condition 1 : uid_metadta/uid_metadata == uid de metadata)
        ressources = ressources_par_uid.get(str(uid_meta), [])

        # c) PDA opendata (Condition 2 : display_name ∈ FullName_lower)
        #    On collecte les display_name côté ressources et cherche le premier blob dont FullName_lower contient l'un d'eux (case-insensitive).
        pda = None
        if ressources:
            display_names = [
                str(r.get("display_name")).strip().lower()
                for r in ressources
                if not est_vide(r.get("display_name"))
            ]
            if display_names:
                for bp in blobs_prepares:
                    full = bp["full_lower"]
                    if any(dn in full for dn in display_names):
                        pda = bp["blob"]  # premier match retenu
                        break

        # d) Normalisation (remplacer NaN par None dans les blocs)
        meta_clean = {k: normaliser(v) for k, v in m.items()}
        res_clean: List[Dict[str, Any]] = [
            {k: normaliser(v) for k, v in r.items()} for r in ressources
        ]
        pda_clean = (
            {k: normaliser(v) for k, v in pda.items()} if isinstance(pda, dict) else None
        )

        # e) Construire l'objet JddOdre
        try:
            id_jdd = int(numero_metadata)
        except Exception:
            # fallback sur None si l'index n'est pas entier (tu peux choisir de mettre un compteur)
            id_jdd = None

        nom = dataset_id if not est_vide(dataset_id) else uid_meta
        nom = "" if est_vide(nom) else str(nom)

        jdds.append(
            JddOdre(
                id_jdd_odre=id_jdd,
                nom_jdd_odre=nom,
                metadonnees=meta_clean,
                ressources=res_clean,      # 0..n ressources
                pda_opendata=pda_clean,    # 0..1 blob (selon Condition 2)
            )
        )

    return jdds

def construire_liste_jdds_odre(df_metadata: pd.DataFrame,
                                df_ressources:pd.DataFrame,
                                df_blob_opendata:pd.DataFrame
)-> List[JddOdre]:
    # Préparation des conteneurs
    liste_metadata: List[Dict[str, Any]] = []
    liste_ressources: List[Dict[str, Any]] = []
    liste_blob_opendata: List[Dict[str, Any]] = []

    # Liste qui sera retournée
    liste_jdds_opendata: List[JddOdre] = []  
    try:
        # Itération efficace (évite list(...))
        for position, (index, ligne) in enumerate(df_metadata.iterrows()):
            # Nouveau dict à chaque itération (pas de réutilisation)
            dico_metadata: Dict[str, Any] = {}
            dico_metadata["numero_metadata"] = index
            dico_metadata[f"metadata_{position}"] = ligne.to_dict()
            # Ajout à la liste
            liste_metadata.append(dico_metadata)

        for position, (index, ligne) in enumerate(df_ressources.iterrows()):
            dico_ressources = {}
            dico_ressources["numero_ressource"] = index
            dico_ressources[f"ressources_{position}"] = ligne.to_dict()
            liste_ressources.append(dico_ressources)

        for position, (index, ligne) in enumerate(df_blob_opendata.iterrows()):
            dico_blob_opendata = {}
            dico_blob_opendata["numero_blob"] = index
            dico_blob_opendata[f"blob_{position}"] = ligne.to_dict()
            liste_blob_opendata.append(dico_blob_opendata)
    except Exception as e:
        print(f"[Couche: cas d'utilisation] | Module : outils_pour_les_services\n")
        print(f"[Couche: cas d'utilisation] | Fonction : construire_liste_jdds_odre\n")
        raise RuntimeError(f"[erreur]: {e}")

    try:  
        liste_jdds_opendata = assemblage(liste_metadata=liste_metadata,
                                        liste_ressources=liste_ressources,
                                        liste_blob_opendata=liste_blob_opendata
        )
        return liste_jdds_opendata
    except Exception as e: 
        print(f"[Couche: cas d'utilisation] | Module : outils_pour_les_services\n")
        print(f"[Couche: cas d'utilisation] | Fonction : construire_liste_jdds_odre | sous fonction d'aide: assemblage\n")
        print(f"[Couche: cas d'utilisation] | Erreur: {e}\n")
        return []

# -- Sauvegarde de la liste de jeux de données dans l'application --

# --- helpers robustes ---
def en_json(obj: Any) -> dict:
    """Convertit un objet JddOdre en dict JSONable, quelles que soient ses bases."""
    # dataclass
    if dataclasses.is_dataclass(obj):
        return dataclasses.asdict(obj)
    # pydantic v2
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    # pydantic v1
    if hasattr(obj, "dict"):
        return obj.dict()
    # classe simple
    if hasattr(obj, "__dict__"):
        return obj.__dict__
    # déjà un dict
    if isinstance(obj, dict):
        return obj
    # fallback
    return {"value": str(obj)}

def sauvegarder(liste_jdds: List[JddOdre], 
                path: Path, 
                schema_version: str = "1.0") -> bool:
    """
    Opère une sauvegarde en JSON Lines de la liste des JDDs.
    Écriture atomique : écrit dans un tmp puis renomme.
    """
    try:
        # Sécurité : assurer l'existence du dossier
        path.parent.mkdir(parents=True, exist_ok=True)

        # Fichier temporaire pour écriture atomique
        with tempfile.NamedTemporaryFile("w", delete=False, dir=str(path.parent), encoding="utf-8") as tmp:
            tmp_path = Path(tmp.name)
            for j in liste_jdds:
                payload = en_json(j)
                payload["_schema_version"] = schema_version
                tmp.write(json.dumps(payload, ensure_ascii=False) + "\n")

        # Remplacer atomiquement la cible
        os.replace(tmp_path, path)
        return True

    except Exception as e:
        # Nettoyage du tmp si présent
        try:
            if 'tmp_path' in locals() and tmp_path.exists():
                tmp_path.unlink(missing_ok=True)
        except Exception:
            pass
        print(f"[Couche: cas d'utilisation] | Module : outils_pour_les_services")
        print(f"[Couche: cas d'utilisation] | Fonction : sauvegarder")
        print(f"[Couche: cas d'utilisation] | Erreur : {e}")
        return False


# -- Lecutre de la liste de jeux de données dans l'application --

# --- helpers robustes ---
def charger_jdds_jsonl(path: str | Path,
                       expected_schema_version: Optional[str] = None,
                       compressed: bool = False,
                       strict_schema: bool = False,
) -> Tuple[List[Dict[str, Any]], List[str]]:
    """
    Lit un fichier JSON Lines (.jsonl ou .jsonl.gz) et retourne:
      - payload: List[dict]
      - warnings: List[str] (lignes ignorées, versions inattendues, etc.)

    Paramètres:
      - expected_schema_version: version attendue (ex. "1.0"). Si None, le check est ignoré.
      - compressed: True si le fichier est un .gz
      - strict_schema: si True, rejette les lignes dont la version ne correspond pas exactement.

    Comportement:
      - Ignore les lignes vides/blanches.
      - Loggue les erreurs de parsing avec le numéro de ligne.
      - Supporte BOM via encoding 'utf-8-sig'.
    """
    path = Path(path)
    warnings: List[str] = []
    payload: List[Dict[str, Any]] = []

    if not path.exists():
        msg = f"Fichier introuvable: {path}"
        warnings.append(msg)
        print(msg, flush=True)
        return payload, warnings

    opener = gzip.open if compressed else open

    try:
        with opener(path, "rt", encoding="utf-8-sig") as f:
            for n, line in enumerate(f, start=1):
                if not line.strip():
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError as e:
                    warnings.append(f"[ligne {n}] JSON invalide: {e}")
                    continue

                version = obj.get("_schema_version")
                if expected_schema_version and version != expected_schema_version:
                    msg = (f"[ligne {n}] Version inattendue ({version}); "
                           f"attendu={expected_schema_version}")
                    if strict_schema:
                        warnings.append(msg + " -> ligne ignorée (strict)")
                        continue
                    else:
                        warnings.append(msg + " -> ligne acceptée (non strict)")

                payload.append(obj)

    except Exception as e:
        msg = (
            "[Couche: cas d'utilisation] | Module : outils_pour_les_services\n"
            "[Couche: cas d'utilisation] | Fonction d'aide: charger_jdds_jsonl\n"
            f"[Couche: cas d'utilisation] | Erreur : {e}\n"
        )
        print(msg, flush=True)
        warnings.append(f"Erreur lecture {path}: {e}")
    return payload, warnings

def lire(path: str | Path,
         expected_schema_version: Optional[str] = None,
         compressed: bool = False,
         strict_schema: bool = False,
) -> Tuple[List[JddOdre], List[str]]:
    """
        Effectue une lecture d'une liste de jeux de données de l'opendata depuis l'application
    """
    dicts, warnings = charger_jdds_jsonl(path=path,
                                         expected_schema_version=expected_schema_version,
                                         compressed=compressed,
                                         strict_schema=strict_schema,
    )
    jdds: List[JddOdre] = []
    for n, d in enumerate(dicts, start=1):
        try:
            # Pydantic v2
            if hasattr(JddOdre, "model_validate"):
                jdds.append(JddOdre.model_validate(d))
            else:
                # v1 ou classe simple
                jdds.append(JddOdre(**d))
        except Exception as e:
            msg = (
                "[Couche: cas d'utilisation] | Module : outils_pour_les_services\n"
                "[Couche: cas d'utilisation] | Fonction : lire\n"
                f"[Couche: cas d'utilisation] | Erreur reconstruction à la ligne {n} : {e}\n"
            )
            print(msg, flush=True)
            warnings.append(f"[ligne {n}] Reconstruction JddOdre échouée: {e}")

    return jdds, warnings


def alimenter_app_en_data(connecteurs: Dict[str, Any]
) -> Tuple[List[JddOdre], 
           Dict[str, pq.ParquetFile], 
            Dict[str, pd.DataFrame], 
            Dict[str, Any]
    ]:
    """
    Docstring for alimenter_app_en_data
    
    :param connecteur: Toutes les configurations de branchements aux types de sources
    :type connecteur: Dict[str, str]
        List[JddOdre]
        Dict[str, pq.ParquetFile]
        Dict[str, pd.DataFrame], 
        Dict[str, Any] =  ex 
        {
            "__ALL__": pq.ParquetFile(str(chemin_parquet_unique)),
            "__INDEX__": index_par_dataset_id,  # pour retrouver la position
        }

    """
    # === Sous fonctions utiles pour réaliser un récupération des paramètres de connexion aux sources externes multiples ===
    def _chaine_de_caractere(x, default="") -> str:
        return str(x).strip() if isinstance(x, str) else default
    def _chaine_de_caractere_pour_df(df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df = df.where(pd.notnull(df), "")
        for c in df.columns:
            df[c] = df[c].astype(str)
        return df
    def _entier(x, default=0) -> int:
        try:
            return int(x)
        except Exception:
            return default
    def _normaliser_colonnes(df:pd.DataFrame) -> pd.DataFrame:
        """Remplace '.' et '-' par '_' dans les noms de colonnes."""
        df.columns = [col.replace('.', '_').replace('-', '_') for col in df.columns]
        return df
    def _separation_accents(s: str) -> str:
        """Supprime les accents pour des comparaisons robustes."""
        try:
            return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')
        except Exception:
            return s
    def _premier_sources_externes_pda_opendata(cols_json: str) -> Dict[str, Any]:
        try:
            d = json.loads(cols_json) if isinstance(cols_json, str) else {}
            return d if isinstance(d, dict) else {}
        except Exception:
            return {}  
    def parser_json_dans_le_parquet(value: Any
    ) -> Optional[Any]:
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
    def lire_params_connecteur_racine_v0(connecteurs: Dict[str, Dict[str, Any]],
                                    nom: str
    ) -> Tuple[str, str, Dict[str, str], Any, int, int]:
        """
        Lit proprement les paramètres du sous-dict 'nom' dans un dict de dicts 'connecteurs'.

        Retourne:
        - base_url (str)
        - api_key (str)
        - proxies (dict[str, str])
        - session_cls (class)
        - limit (int)
        - timeout (int)

        Lève une ValueError si 'param1' (base_url) manque ou est vide.
        """
        if nom == "connecteur_api_cataloge":
            bloc = connecteurs.get(nom, {}) or {}
            base_url: str = _chaine_de_caractere(bloc.get("param1"), "")
            api_key: str = _chaine_de_caractere(bloc.get("param2"), "")
            proxies: Dict[str, str] = bloc.get("param3", {}) or {}
            session_cls = bloc.get("param4", requests.Session) or requests.Session
            limit: int = _entier(bloc.get("param5", 1000), 1000)
            timeout: int = _entier(bloc.get("param6", 15), 15)
            if not base_url:
                raise ValueError(f"[connecteur '{nom}'] param1 (base_url) est requis et ne doit pas être vide.")
            return base_url, api_key, proxies, session_cls, limit, timeout
        
        elif nom == "connecteur_api_ressources":
            bloc = connecteurs.get(nom, {}) or {}
            base_url: str = _chaine_de_caractere(bloc.get("param1"), "")
            api_key: str = _chaine_de_caractere(bloc.get("param2"), "")
            proxies: Dict[str, str] = bloc.get("param3", {}) or {}
            session_cls = bloc.get("param4", requests.Session) or requests.Session
            limit: int = _entier(bloc.get("param5", 1000), 1000)
            timeout: int = _entier(bloc.get("param6", 15), 15)
            if not base_url:
                raise ValueError(f"[connecteur '{nom}'] param1 (base_url) est requis et ne doit pas être vide.")
            return base_url, api_key, proxies, session_cls, limit, timeout

        else:
            bloc = connecteurs.get(nom, {}) or {}
            base_url: str = _chaine_de_caractere(bloc.get("param1"), "")
            api_key: str = _chaine_de_caractere(bloc.get("param2"), "")
            proxies: Dict[str, str] = bloc.get("param3", {}) or {}
            session_cls = bloc.get("param4", requests.Session) or requests.Session
            limit: int = _entier(bloc.get("param5", 1000), 1000)
            timeout: int = _entier(bloc.get("param6", 15), 15)
            if not base_url:
                raise ValueError(f"[connecteur '{nom}'] param1 (base_url) est requis et ne doit pas être vide.")
            return base_url, api_key, proxies, session_cls, limit, timeout
    def lire_params_connecteur_racine(connecteurs: Dict[str, Dict[str, Any]],
                                      nom: str
    ) -> Tuple[str, str, Dict[str, str], Any, int, int]:
        """
        Lit proprement les paramètres du sous-dict 'nom' dans un dict de dicts 'connecteurs'.

        Retourne:
        - base_url (str)   -> pour les connecteurs HTTP; pour les connecteurs fichier, peut contenir le chemin
        - api_key (str)    -> vide si non applicable
        - proxies (dict[str, str]) -> {} si non applicable
        - session_cls (class)      -> requests.Session si non applicable
        - limit (int)       -> default 1000 si None
        - timeout (int)     -> default 15 si None

        - Pour les connecteurs HTTP (API): base_url est requis (non vide)
        - Pour les connecteurs FICHIER (Excel/Blob/etc.): base_url peut être un chemin fichier; on ne lève pas d'erreur si vide, mais on le signale en retour.

        Lève ValueError uniquement si le connecteur est HTTP et que base_url manque.
        """
        bloc = connecteurs.get(nom, {}) or {}

        base_url: str = _chaine_de_caractere(bloc.get("param1"), "")
        api_key: str = _chaine_de_caractere(bloc.get("param2"), "")
        proxies: Dict[str, str] = bloc.get("param3") or {}
        session_cls = bloc.get("param4") or requests.Session
        limit: int = _entier(bloc.get("param5"), 1000)
        timeout: int = _entier(bloc.get("param6"), 15)

        # Déterminer si c'est un connecteur de type HTTP (API) ou Fichier
        # -> Ici, on se base sur le nom; adapte la logique si besoin
        CONNECTEURS_HTTP = {"connecteur_api_cataloge", "connecteur_api_ressources"}
        CONNECTEURS_FICHIER = {"connecteur_excel_blob_monitoring"}

        if nom in CONNECTEURS_HTTP:
            if not base_url:
                raise ValueError(f"[connecteur '{nom}'] param1 (base_url) est requis et ne doit pas être vide.")
            # proxies doit être un dict; si None -> {}
            if not isinstance(proxies, dict):
                proxies = {}
            return base_url, api_key, proxies, session_cls, limit, timeout

        elif nom in CONNECTEURS_FICHIER:
            # Ici, 'base_url' est plutôt un chemin fichier; on ne lève pas si vide,
            # mais on renvoie les defaults cohérents (proxies={}, session_cls=requests.Session)
            if not isinstance(proxies, dict):
                proxies = {}
            return base_url, api_key, proxies, session_cls, limit, timeout

        # Par défaut: même traitement que HTTP (si tu préfères plus strict)
        if not base_url:
            # Si tu préfères silencieux:
            # return base_url, api_key, proxies, session_cls, limit, timeout
            raise ValueError(f"[connecteur '{nom}'] param1 (base_url/chemin) est requis et ne doit pas être vide.")
        if not isinstance(proxies, dict):
            proxies = {}
        return base_url, api_key, proxies, session_cls, limit, timeout


    # === SOURCE EXTERNE 1: CATALOGUE METADATA JDD OPENDATA SUR ODRE === #
    try:
        # -- Lecture des params de connexion à la source 1 : Catalogue metadata opendata API -- #
        base_url_meta, api_key_meta, proxies_meta, session_cls_meta, limit_meta, timeout_meta = lire_params_connecteur_racine(connecteurs=connecteurs, 
                                                                                                                              nom="connecteur_api_cataloge"
        )
    except Exception as e:
        # -- Déporter les erreurs en dev dans la conlose -- #
        print(f"[Outils pour sources externes]: \n")
        print(f"[Fonction: alimenter_app_en_data | Lecture de connexion]:\n")
        print(f"{e}")
    try:
        # -- Création d'une sessions de connexion: pour le source externe 1 -- #
        param_session_1: int = 5                                         # Nb tentative
        param_session_2: float = 1                                       # Facteur backoof
        param_session_3: Optional[List[int]] = [429, 500, 502, 503, 504] # Code erreur à éviter
        param_session_4: Optional[List[str]] = ['GET']                   # Méthode
        param_session_5: Optional[bool] = False                          # Lever une erreur
        
        session_montee = session_cls_meta()
        renouveller = Retry(total=param_session_1,
                            read=param_session_1,
                            connect=param_session_1,
                            backoff_factor=param_session_2,
                            status_forcelist=param_session_3,
                            allowed_methods=param_session_4,
                            raise_on_status=param_session_5
        )
        adaptateur = HTTPAdapter(max_retries=renouveller)
        session_montee.mount("http://", adapter=adaptateur)
        session_montee.mount("https://", adapter=adaptateur)
        if proxies_meta:
            session_montee.proxies.update(proxies_meta)
        headers_meta = {}
        if api_key_meta:
            headers_meta["Authorization"] = f"Bearer {api_key_meta}"
    except Exception as e:
        # -- Déporter les erreurs en dev dans la conlose -- #
        print(f"[Outils pour sources externes]: \n")
        print(f"[Fonction: alimenter_app_en_data]:\n")
        print(f"[Création d'une sessions de connexion: pour le source externe 1]:\n")
        print(f"{e}")
    try:
        # -- Source1: Récupération des catalogues métadata pour les jdds odre de l'opendata -- #
        response_meta = session_montee.get(
            url=base_url_meta,
            headers=headers_meta,
            params={"apikey": api_key_meta, "limit": limit_meta},
            timeout=(5.0, float(timeout_meta)) 
        )
        if response_meta.status_code != 200:
            response_meta.raise_for_status()
        data_meta = response_meta.json()
        sources_externes_metadata = pd.json_normalize(data_meta["results"])
        sources_externes_metadata = _normaliser_colonnes(sources_externes_metadata)

    except Exception as e:
        # -- Déporter les erreurs en dev dans la conlose -- #
        print(f"[Outils pour sources externes]: \n")
        print(f"[Fonction: alimenter_app_en_data]:\n")
        print(f"[Source1: Récupération des catalogues métadata pour les jdds odre de l'opendata]:\n")
        print(f"{e}")
    
    # === SOURCE EXTERNE 2: RESSOURCES ASSOCIEES AU METADATA === #
    try:
        # -- Lecture des params de connexion à la source 2 : Ressources assoicées aux metadata opendata API -- #
        base_url_ressource, api_key_ressources, \
            proxies_ressources, session_cls_ressources, \
            limit_ressources, timeout_ressources = lire_params_connecteur_racine(connecteurs=connecteurs, 
                                                                                 nom="connecteur_api_ressources"
        )
    except Exception as e:
        # -- Déporter les erreurs en dev dans la conlose -- #
        print(f"[Outils pour sources externes]: \n")
        print(f"[Fonction: alimenter_app_en_data]:\n")
        print(f"[Lecture des params de connexion à la source 2]:\n")
        print(f"{e}")
    try:
        # -- Création d'une sessions de connexion: pour le source externe 2 -- #
        param_session_1: int = 5                                         # Nb tentative
        param_session_2: float = 1                                       # Facteur backoof
        param_session_3: Optional[List[int]] = [429, 500, 502, 503, 504] # Code erreur à éviter
        param_session_4: Optional[List[str]] = ['GET']                   # Méthode
        param_session_5: Optional[bool] = False                          # Lever une erreur
        
        session_montee = session_cls_ressources()
        renouveller = Retry(total=param_session_1,
                            read=param_session_1,
                            connect=param_session_1,
                            backoff_factor=param_session_2,
                            status_forcelist=param_session_3,
                            allowed_methods=param_session_4,
                            raise_on_status=param_session_5
        )
        adaptateur = HTTPAdapter(max_retries=renouveller)
        session_montee.mount("http://", adapter=adaptateur)
        session_montee.mount("https://", adapter=adaptateur)
        if proxies_ressources:
            session_montee.proxies.update(proxies_ressources)
        headers_ressources = {}
        if api_key_ressources:
            headers_ressources["Authorization"] = f"Bearer {api_key_ressources}"
    except Exception as e:
        # -- Déporter les erreurs en dev dans la conlose -- #
        print(f"[Outils pour sources externes]: \n")
        print(f"[Fonction: alimenter_app_en_data]:\n")
        print(f"[Création d'une sessions de connexion: pour le source externe 2]:\n")
        print(f"{e}")

    try:
        # -- Source2: Récupération Ressources assoicées aux metadata opendata API -- #
        liste_uids_pour_appel_ressources = _normaliser_colonnes(sources_externes_metadata)["uid"]
        liste_data_par_ressources = []
        for uid in liste_uids_pour_appel_ressources:
            try:
                uid_str = str(uid) if uid is not None else ""
                url_ressources = f"{base_url_ressource.rstrip('/')}/{uid_str}/resources"
                params = {"apikey": api_key_ressources} if api_key_ressources else {}

                print(f"[RESSOURCES] UID={uid_str} • GET {url_ressources}")
                response_ressources = session_montee.get(
                    url=url_ressources,
                    headers=headers_ressources,
                    params=params,
                    timeout=(5.0, float(timeout_ressources)),
                )
                response_ressources.raise_for_status()

                data_ressources = response_ressources.json() or {}
                payload = data_ressources.get("results", [])
                if not isinstance(payload, list):
                    # payload inattendu : on log et on continue
                    print(f"[RESSOURCES][UID={uid_str}] 'results' non list: type={type(payload)}")
                    payload = []

                une_externe_ressources = pd.json_normalize(payload)
                # Même si payload vide, on force la présence de la colonne clé
                une_externe_ressources["uid_metadata"] = uid_str

                liste_data_par_ressources.append(une_externe_ressources)

            except Exception as e:
                # On continue la boucle pour ne pas bloquer toute la collecte si un uid échoue
                print(f"[RESSOURCES][UID={uid}] erreur: {e}")
                continue

        # Concat uniquement si on a au moins un DF
        if liste_data_par_ressources:
            sources_externes_ressources = pd.concat(
                liste_data_par_ressources, axis=0, ignore_index=True
            )
        else:
            # DF vide stabilisé avec la colonne clé attendue
            sources_externes_ressources = pd.DataFrame(columns=["uid_metadata"])

        # Normalisation/typage (attention si _normaliser_colonnes modifie 'uid_metadata')
        sources_externes_ressources = _normaliser_colonnes(sources_externes_ressources)
        sources_externes_ressources = _chaine_de_caractere_pour_df(sources_externes_ressources)

        # Vérification utile:
        print("[RESSOURCES] shape:", sources_externes_ressources.shape)
        print("[RESSOURCES] colonnes:", list(sources_externes_ressources.columns))
        print("[RESSOURCES] contient 'uid_metadata' ?",
            "uid_metadata" in sources_externes_ressources.columns)

    except Exception as e:
        # -- Déporter les erreurs en dev dans la conlose -- #
        print(f"[Outils pour sources externes]: \n")
        print(f"[Fonction: alimenter_app_en_data]:\n")
        print(f"[Source2: Récupération Ressources assoicées aux metadata opendata API]:\n")
        print(f"{e}")


    
    # === SOURCE EXTERNE 3: PDA BLOB OPENDATA ASSOCIES AUX RESSOURCES SI DISPO === #
    try:
        # -- Lecture des params de connexion à la source 3 : Blob opendata assoicées aux ressosurces des metadata opendata API -- #
        base_excel, feuille_excel, _, _, _, _ = lire_params_connecteur_racine(connecteurs=connecteurs,
                                                                              nom="connecteur_excel_blob_monitoring"
        )
    except Exception as e:
        # -- Déporter les erreurs en dev dans la conlose -- #
        print(f"[Outils pour sources externes]: \n")
        print(f"[Fonction: alimenter_app_en_data]:\n")
        print(f"[Lecture des params de connexion à la source 3]:\n")
        print(f"{e}")
        
    # -- PAS DE CREATION D'UNE SESSION DE CONNEXION -- #
    try:
        # -- Source3: Récupération Blob assoicées aux ressources des metadata opendata API -- #
        if not isinstance(base_excel, Path):
            base_excel = Path(base_excel)
        if not base_excel.exists():
            print(f"[Source3 | Récupération Blob assoicées aux ressources] \n")  
            print(f"Pas de classeur dans le chemin {base_excel} :\n")  
        try:
            sources_externes_pda_opendata = pd.read_excel(base_excel, 
                               sheet_name=feuille_excel, 
                               engine="openpyxl"
            )
        except FileNotFoundError:
            print(f"[Source3 | Récupération Blob assoicées aux ressources] \n")  
            print(f"Impossible de lire la feuille\n") 

        # FullName_lower: s'il existe déjà, normaliser ; sinon bâtir à partir de FullName si présent
        if "FullName" in sources_externes_pda_opendata.columns:
            sources_externes_pda_opendata["FullName_lower"] = (
                sources_externes_pda_opendata["FullName"].astype(str)
                .str.replace("\\", "/")
                .str.strip().str.lower()
                #.apply(_separation_accents)
            )
        else:
            # si aucune colonne, fournir un champ vide (matching ne trouvera rien)
            sources_externes_pda_opendata["FullName_lower"] = ""

        # Normaliser Name et StorageContainerName (pour fallback)
        sources_externes_pda_opendata["Name_lower"] = sources_externes_pda_opendata.get("Name", 
                                                                                        pd.Series([""] * len(sources_externes_pda_opendata))
                                                                                        ).astype(str
                                                                                                 ).str.strip().str.lower().apply(_separation_accents
        )
        sources_externes_pda_opendata["StorageContainerName_lower"] = sources_externes_pda_opendata.get("StorageContainerName", 
                                                                                                        pd.Series([""] * len(sources_externes_pda_opendata))
                                                                                                        ).astype(str).str.strip().str.lower().apply(_separation_accents
        )
        sources_externes_pda_opendata =_normaliser_colonnes(sources_externes_pda_opendata)

    except Exception as e:
        # -- Déporter les erreurs en dev dans la conlose -- #
        print(f"[Outils pour sources externes]: \n")
        print(f"[Fonction: alimenter_app_en_data]:\n")
        print(f"[Source3: Récupération Blob assoicées aux ressources des metadata opendata API]:\n")
        print(f"{e}")
    

    # === Modélisation de la réunification des trois sources externes ===

    # 1) Copies + normalisation
    sources_externes_metadata = _normaliser_colonnes(sources_externes_metadata.copy())
    sources_externes_ressources = _normaliser_colonnes(sources_externes_ressources.copy())
    sources_externes_pda_opendata = _normaliser_colonnes(sources_externes_pda_opendata.copy())

    # 2) Validation minimale des colonnes clés
    required_meta = {"uid"}
    required_ress = {"uid_metadata", "display_name"}
    missing_meta = required_meta - set(sources_externes_metadata.columns)
    missing_ress = required_ress - set(sources_externes_ressources.columns)
    if missing_meta:
        raise ValueError(f"[META] Colonnes manquantes: {missing_meta} | dispo={sorted(sources_externes_metadata.columns)}")
    if missing_ress:
        raise ValueError(f"[RESSOURCES] Colonnes manquantes: {missing_ress} | dispo={sorted(sources_externes_ressources.columns)}")

    # 3) Renommer la colonne 'uid' côté ressources (évite ambiguïté)
    if "uid" in sources_externes_ressources.columns:
        sources_externes_ressources = sources_externes_ressources.rename(columns={"uid": "uid_ressource"})

    # 4) Cast en str (uniformise)
    sources_externes_metadata = _chaine_de_caractere_pour_df(sources_externes_metadata)
    sources_externes_ressources = _chaine_de_caractere_pour_df(sources_externes_ressources)
    sources_externes_pda_opendata = _chaine_de_caractere_pour_df(sources_externes_pda_opendata)

    # 5) (Optionnel) préfixage des colonnes communes – ici on s’appuie sur les suffixes du merge (_meta/_ressource)
    left_key  = "uid"
    right_key = "uid_metadata"


    # Vérification côté ressources juste avant le merge
    print("[MERGE] shape ressources:", sources_externes_ressources.shape)
    print("[MERGE] colonnes ressources:", list(sources_externes_ressources.columns))
    print("[MERGE] contient 'uid_metadata' ?", "uid_metadata" in sources_externes_ressources.columns)

    # Si tu normalises, refais le check APRÈS normalisation:
    sources_externes_ressources = _normaliser_colonnes(sources_externes_ressources)
    print("[MERGE] colonnes ressources après normalisation:", list(sources_externes_ressources.columns))
    print("[MERGE] contient 'uid_metadata' après normalisation ?",
        "uid_metadata" in sources_externes_ressources.columns)

    # 6) LEFT JOIN depuis META (cardinalité = méta → one_to_many)
    if not sources_externes_ressources.empty and right_key in sources_externes_ressources.columns:
        sources_externes_metadata_et_ressources = sources_externes_metadata.merge(
            sources_externes_ressources,
            left_on=left_key,
            right_on=right_key,
            how="left",
            suffixes=("_meta", "_ressource"),
            validate="one_to_many",
        )
    else:
        # Pas de ressources ou clé absente → on garde le catalogue seul
        sources_externes_metadata_et_ressources = sources_externes_metadata.copy()

    # 7) display_name_lower (pour matching PDA)
    if "display_name" in sources_externes_metadata_et_ressources.columns:
        sources_externes_metadata_et_ressources["display_name_lower"] = (
            sources_externes_metadata_et_ressources["display_name"].astype(str).str.lower().str.strip()
        )
    else:
        sources_externes_metadata_et_ressources["display_name_lower"] = ""

    # 8) Liste des fullnames côté PDA opendata
    blob_fullnames = (
        sources_externes_pda_opendata["FullName_lower"].astype(str).tolist()
        if (not sources_externes_pda_opendata.empty and "FullName_lower" in sources_externes_pda_opendata.columns)
        else []
    )

    # 9) Matching startswith(display_name_lower) → extraction JSON + flags
    matched_sources_externes_pda_opendata_json_list: List[str] = []
    has_sources_externes_pda_opendata_flags: List[str] = []

    for _, r in sources_externes_metadata_et_ressources.iterrows():
        dn = str(r.get("display_name_lower", "") or "")
        has = False
        sources_externes_pda_opendata_row: Dict[str, Any] = {}

        if dn and blob_fullnames:
            mask = [dn.startswith(fn) if isinstance(fn, str) and fn else False for fn in blob_fullnames]
            if any(mask):
                idx_match = mask.index(True)
                if 0 <= idx_match < len(sources_externes_pda_opendata):
                    matched = sources_externes_pda_opendata.iloc[idx_match]
                    sources_externes_pda_opendata_row = matched.to_dict()
                    has = True

        # ⚠️ NOMMAGE aligné avec LISTE_COLS_JSON_PDA par défaut: "matched_blobs_json"
        matched_sources_externes_pda_opendata_json_list.append(
            json.dumps(sources_externes_pda_opendata_row, ensure_ascii=False) if sources_externes_pda_opendata_row else "{}"
        )
        has_sources_externes_pda_opendata_flags.append("True" if has else "False")

    # Injection des champs PDA au niveau des lignes (avant consolidation)
    sources_externes_metadata_et_ressources["matched_blobs_json"] = matched_sources_externes_pda_opendata_json_list
    sources_externes_metadata_et_ressources["has_sources_externes_pda_opendata_monitoring"] = has_sources_externes_pda_opendata_flags

    # 10) Extraction du premier match PDA en dict + mapping de champs synthèse
    premiere_sources_externes_pda_opendata = sources_externes_metadata_et_ressources["matched_blobs_json"].apply(
        _premier_sources_externes_pda_opendata
    )

    # Mappings standards si présents
    sources_externes_metadata_et_ressources["name"] = premiere_sources_externes_pda_opendata.apply(lambda d: d.get("Name") or d.get("name") or "")
    sources_externes_metadata_et_ressources["size"] = premiere_sources_externes_pda_opendata.apply(lambda d: d.get("Size") or d.get("size") or "")
    sources_externes_metadata_et_ressources["lastmodified"] = premiere_sources_externes_pda_opendata.apply(lambda d: d.get("LastModified") or d.get("lastmodified") or "")
    sources_externes_metadata_et_ressources["boolisdeleted"] = premiere_sources_externes_pda_opendata.apply(lambda d: d.get("BoolIsDeleted") or d.get("boolisdeleted") or "")
    sources_externes_metadata_et_ressources["contenttype"] = premiere_sources_externes_pda_opendata.apply(lambda d: d.get("ContentType") or d.get("contenttype") or "")
    sources_externes_metadata_et_ressources["storageaccountname"] = premiere_sources_externes_pda_opendata.apply(lambda d: d.get("StorageAccountName") or d.get("storageaccountname") or "")
    sources_externes_metadata_et_ressources["storagecontainername"] = premiere_sources_externes_pda_opendata.apply(lambda d: d.get("StorageContainerName") or d.get("storagecontainername") or "")
    sources_externes_metadata_et_ressources["FullName"] = premiere_sources_externes_pda_opendata.apply(lambda d: d.get("FullName") or d.get("fullname") or "")

    # 11) Normalisation + cast str (DF intermédiaire post-merge)
    sources_externes_metadata_et_ressources = _normaliser_colonnes(sources_externes_metadata_et_ressources)
    sources_externes_metadata_et_ressources = _chaine_de_caractere_pour_df(sources_externes_metadata_et_ressources)

    # === 12) Consolidation à 1 ligne par UID (agrégations côté ressources) ===

    # Colonnes côté ressources après merge (suffixes "_ressource" + clés utiles)
    ressources_cols = [
        c for c in sources_externes_metadata_et_ressources.columns
        if c.endswith("_ressource") or c in ["uid_metadata", "uid_ressource", "display_name"]
    ]

    # JSON des ressources par UID (toutes les colonnes _ressource + clés utiles)
    def _ressources_json_par_uid(d: pd.DataFrame) -> str:
        d2 = d.drop(columns=["display_name_lower"], errors="ignore")
        return json.dumps(d2.to_dict(orient="records"), ensure_ascii=False)

    ressources_json_per_uid = (
        sources_externes_metadata_et_ressources
        .groupby("uid", dropna=False)[ressources_cols]
        .apply(_ressources_json_par_uid)
        .reset_index()
        .rename(columns={0: "ressources_json"})   # ⚠️ NOMMAGE aligné avec LISTE_COLS_JSON_RESSOURCES
    )

    # Compte de ressources par UID
    def _count_non_null_uid_metadata(d: pd.DataFrame) -> int:
        return int(d["uid_metadata"].notna().sum()) if "uid_metadata" in d.columns else 0

    ressources_count_per_uid = (
        sources_externes_metadata_et_ressources
        .groupby("uid", dropna=False)[["uid_metadata"]]
        .apply(_count_non_null_uid_metadata)
        .reset_index()
        .rename(columns={0: "ressources_count"})
    )

    # Base META unique (1 ligne par uid)
    meta_unique = sources_externes_metadata.drop_duplicates(subset=["uid"], keep="first").copy()

    # Agrégations PDA au niveau UID (on prend la première ligne du groupe)

    # Construction (conseillée) de pda_per_uid
    pda_cols = [
        "matched_blobs_json",
        "has_sources_externes_pda_opendata_monitoring",
        "name", "size", "lastmodified", "boolisdeleted",
        "contenttype", "storageaccountname", "storagecontainername", "FullName",
    ]

    pda_per_uid = (
        sources_externes_metadata_et_ressources
        .groupby("uid", dropna=False)[pda_cols]
        .agg(lambda s: s.iloc[0] if len(s) else "")  # prend la 1ère ligne du groupe
        .reset_index()                                # ← remet 'uid' en colonne
    )

    # Sécurité : si 'uid' est resté index ou a été renommé, on corrige
    if "uid" not in pda_per_uid.columns:
        if pda_per_uid.index.name == "uid":
            pda_per_uid = pda_per_uid.reset_index()
        elif "uid_meta" in pda_per_uid.columns:
            pda_per_uid = pda_per_uid.rename(columns={"uid_meta": "uid"})
        elif "uid_metadata" in pda_per_uid.columns:
            pda_per_uid = pda_per_uid.rename(columns={"uid_metadata": "uid"})
        else:
            raise KeyError("[PDA] 'uid' introuvable dans pda_per_uid. Colonnes: "
                        f"{list(pda_per_uid.columns)} / index={pda_per_uid.index.names}")


    # Jointure finale (1 ligne par UID)
    df_final = (
        meta_unique
        .merge(ressources_json_per_uid, on="uid", how="left")
        .merge(ressources_count_per_uid, on="uid", how="left")
        .merge(pda_per_uid, on="uid", how="left")
    )

    # Normalisation + cast str final
    df_final = _normaliser_colonnes(df_final)
    df_final = _chaine_de_caractere_pour_df(df_final)

    # Colonne booléenne dérivée du has (utile pour filtrage)
    if "has_sources_externes_pda_opendata_monitoring" in df_final.columns:
        df_final["has_sources_externes_pda_opendata_monitoring_bool"] = df_final[
            "has_sources_externes_pda_opendata_monitoring"
        ].map({"True": True, "False": False}).fillna(False)
    else:
        df_final["has_sources_externes_pda_opendata_monitoring_bool"] = False

    # IMPORTANT : c'est ce DF consolidé (≈ 455 lignes) qui doit être utilisé pour les retours suivants
    sources_externes_metadata__ressources_blob = df_final

    # -------------------------------------------------------------------------
    # === Retours imposés (4 valeurs) – bloc conforme à ta signature ===
    # -------------------------------------------------------------------------

    # Initialisations par défaut (en cas de DF vide)
    liste_des_jdds_odre: List[JddOdre] = []
    liste_des_jdds_format_tech_parquet: Dict[str, Any] = {}
    liste_des_jdds_dataframe: Dict[str, pd.DataFrame] = {}
    json_consolide_dict: Dict[str, Any] = {}

    if (
        sources_externes_metadata__ressources_blob is None
        or not isinstance(sources_externes_metadata__ressources_blob, pd.DataFrame)
        or sources_externes_metadata__ressources_blob.empty
    ):
        return (
            liste_des_jdds_odre,
            liste_des_jdds_format_tech_parquet,
            liste_des_jdds_dataframe,
            json_consolide_dict,
        )

    else:
        # === 1er retour : liste des Jeux de données ODRE ===
        # JddOdre supposé dans ton codebase; sinon remplace par dataclass équivalente
        champs_meta_attendus: Set[str] = set(getattr(Configurations, "LISTE_CHAMPS_META", []))
        champs_ress_attendus: Set[str] = set(getattr(Configurations, "LISTE_CHAMPS_RESSOURCES", []))
        champs_blobs_attendus: Set[str] = set(getattr(Configurations, "LISTE_CHAMPS_BLOB_MONITORING", []))

        champs_meta_presents = [c for c in sources_externes_metadata__ressources_blob.columns if c in champs_meta_attendus]
        champs_ress_presents = [c for c in sources_externes_metadata__ressources_blob.columns if c in champs_ress_attendus]
        champs_blobs_presents = [c for c in sources_externes_metadata__ressources_blob.columns if c in champs_blobs_attendus]

        cols_json_ress = set(getattr(Configurations, "LISTE_COLS_JSON_RESSOURCES", ["ressources_json"]))
        cols_json_pda  = set(getattr(Configurations, "LISTE_COLS_JSON_PDA", ["matched_blobs_json"]))

        cols_json_ress_presents = [c for c in sources_externes_metadata__ressources_blob.columns if c in cols_json_ress]
        cols_json_pda_presents  = [c for c in sources_externes_metadata__ressources_blob.columns if c in cols_json_pda]

        uid_col = "uid" if "uid" in sources_externes_metadata__ressources_blob.columns else ("uid_meta" if "uid_meta" in sources_externes_metadata__ressources_blob.columns else None)
        dataset_id_col = "dataset_id" if "dataset_id" in sources_externes_metadata__ressources_blob.columns else None

        resultat_unifications_des_sources: List[Any] = []

        for idx, row in sources_externes_metadata__ressources_blob.iterrows():
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

            # JddOdre : garde ta structure existante
            resultat_unifications_des_sources.append(JddOdre(
                id_jdd_odre=id_jdd_odre,
                nom_jdd_odre=nom_jdd_odre,
                metadonnees=metadonnees or None,
                ressources=ressources,
                PDA_opendata=pda_opendata,
            ))

        liste_des_jdds_odre = resultat_unifications_des_sources

        # === 2e retour : format tech fichier parquet ===
        chemin_parquet_unique: Path = Configurations.SORTIE_PARQUET_JDD_PATH
        try:
            chemin_parquet_unique.parent.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass
        sources_externes_metadata__ressources_blob.to_parquet(chemin_parquet_unique, index=False)

        liste_des_jdds_format_tech_parquet: Dict[str, Any] = {}
        liste_des_jdds_format_tech_parquet["__ALL__"] = pq.ParquetFile(str(chemin_parquet_unique))

        if "dataset_id" in sources_externes_metadata__ressources_blob.columns:
            s = sources_externes_metadata__ressources_blob["dataset_id"].astype(str)
            for pos, dsid in zip(range(len(s)), s.tolist()):
                if dsid:
                    liste_des_jdds_format_tech_parquet[str(dsid)] = int(pos)

        # === 3e retour : format tech fichier dataframe ===
        liste_des_jdds_dataframe = {
            "catalogue": sources_externes_metadata if 'sources_externes_metadata' in locals() else pd.DataFrame(),
            "ressources": sources_externes_ressources if 'sources_externes_ressources' in locals() else pd.DataFrame(),
            "blob_monitoring": sources_externes_pda_opendata if 'sources_externes_pda_opendata' in locals() else pd.DataFrame(),
            "catalogue_ressources_blob": sources_externes_metadata__ressources_blob,
        }

        # === 4e retour : format tech fichier json ===
        liste_jdds_json: List[dict] = sources_externes_metadata__ressources_blob.to_dict(orient="records")

        if hasattr(Configurations, "SORTIE_JSON_JDD_PATH"):
            chemin_json_unique: Path = Configurations.SORTIE_JSON_JDD_PATH
            try:
                chemin_json_unique.parent.mkdir(parents=True, exist_ok=True)
            except Exception:
                pass
            with chemin_json_unique.open("w", encoding="utf-8") as f:
                json.dump(liste_jdds_json, f, ensure_ascii=False, indent=2)

        json_consolide_dict: Dict[str, Any] = {}
        json_consolide_dict["__ALL__"] = liste_jdds_json

        if "dataset_id" in sources_externes_metadata__ressources_blob.columns:
            s = sources_externes_metadata__ressources_blob["dataset_id"].astype(str)
            for pos, dsid in zip(range(len(s)), s.tolist()):
                if dsid:
                    json_consolide_dict[str(dsid)] = int(pos)

        # Retour final
        return (liste_des_jdds_odre, liste_des_jdds_format_tech_parquet, liste_des_jdds_dataframe, json_consolide_dict)









SEMAINE_MAP = {
    # Monday=0 ... Sunday=6 (datetime.weekday())
    "mon": 0,
    "tue": 1,
    "wed": 2,
    "thu": 3,
    "fri": 4,
    "sat": 5,
    "sun": 6,
}

def _temps_actuel() -> datetime:
    """Datetime actuel aware dans le fuseau de l'app."""
    return datetime.now(Configurations.TIME_ZONE)

def _parseur_de_semaine(spec: str) -> set[int]:
    """
    Convertit un spec de type 'mon-fri' ou 'mon,wed,fri' en set({0,1,2,3,4}).
    Accepte aussi un seul jour: 'mon'.
    """
    spec = (spec or "").strip().lower()
    if not spec:
        return set()
    # support "mon-fri"
    if "-" in spec and "," not in spec:
        start, end = spec.split("-", 1)
        s = SEMAINE_MAP.get(start.strip())
        e = SEMAINE_MAP.get(end.strip())
        if s is None or e is None:
            return set()
        # s..e inclus
        if s <= e:
            return set(range(s, e + 1))
        # s > e (ex: "fri-mon") – on boucle via la semaine
        return set(list(range(s, 7)) + list(range(0, e + 1)))
    # support liste "mon,wed,fri"
    parts = [p.strip() for p in spec.split(",")]
    days = {SEMAINE_MAP.get(p) for p in parts}
    return {d for d in days if d is not None}

def _analyse_declencheur_auto(now: datetime) -> bool:
    """
    Détermine si l'on doit déclencher l'alimentation automatique
    selon la configuration (jours/heures/minutes).
    """
    if not Configurations.AUTO_REFRESH_CRON_ENABLED:
        return False

    allowed_days = _parseur_de_semaine(Configurations.AUTO_REFRESH_CRON_WEEKDAYS)
    if now.weekday() not in allowed_days:
        return False

    return (
        now.hour == int(Configurations.AUTO_REFRESH_CRON_HOUR)
        and now.minute == int(Configurations.AUTO_REFRESH_CRON_MINUTE)
    )

def _lire_le_cache_data(cache_path: Path) -> Optional[dict]:
    """Lit le JSON de cache si présent et valide; sinon None."""
    try:
        if cache_path.exists():
            with cache_path.open("r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, dict) else None
    except Exception:
        # on reste silencieux et on renvoie None
        return None
    return None

def _ecrire_dans_le_cache_data(
    cache_path: Path,
    last_refresh_dt: datetime,
    mode: str
) -> None:
    """Écrit le JSON de cache (métadonnées de dernière alimentation)."""
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "last_refresh_iso": last_refresh_dt.isoformat(),
        "mode": mode,
        "source": "alimenter_app_en_data",
        "parquet_path": str(Configurations.SORTIE_PARQUET_JDD_PATH),
    }
    with cache_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

def _age_cache_en_j_h_m_s(total_seconds: int) -> Tuple[int, int, int, int]:
    """
    Convertit un nombre de secondes en (jours, heures, minutes, secondes) tous des int >= 0.
    """
    if total_seconds < 0:
        total_seconds = 0
    jours = total_seconds // 86400
    reste = total_seconds % 86400
    heures = reste // 3600
    reste %= 3600
    minutes = reste // 60
    secondes = reste % 60
    return jours, heures, minutes, secondes


def _parse_datetime_app(val: Any) -> Optional[datetime]:
    """
    Convertit une valeur (str/datetime) en datetime aware selon TIME_ZONE de l'app.
    Supporte ISO 8601 (avec/sans tz) et 'YYYY-MM-DD HH:MM:SS'. Retourne None si invalide.
    """
    tz = getattr(Configurations, "TIME_ZONE", None)
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    if isinstance(val, datetime):
        return val if val.tzinfo else (val.replace(tzinfo=tz) if tz else val)
    s = str(val).strip()
    try:
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        return dt if dt.tzinfo else (dt.replace(tzinfo=tz) if tz else dt)
    except Exception:
        try:
            dt = datetime.strptime(s, "%Y-%m-%d %H:%M:%S")
            return dt.replace(tzinfo=tz) if tz else dt
        except Exception:
            return None

def _parser_ressources_json_app(val: Any) -> List[Dict[str, Any]]:
    """
    Parse 'ressources_json' (str/list) en liste de dicts.
    Normalise 'updated_at' en datetime et 'enabled' en bool.
    """
    if val is None:
        return []
    lst: List[Dict[str, Any]]
    if isinstance(val, list):
        lst = val
    else:
        try:
            obj = json.loads(val)
            lst = obj if isinstance(obj, list) else []
        except Exception:
            lst = []
    for r in lst:
        r["updated_at"] = _parse_datetime_app(r.get("updated_at"))
        enabled = r.get("enabled", True)
        if isinstance(enabled, bool):
            r["enabled"] = enabled
        else:
            r["enabled"] = str(enabled).strip().lower() not in {"false", "0", ""}
    return lst








# --- 1) Fonction utilitaire pour parser JSON ---
def parser_json_dans_le_parquet(val: Any) -> Optional[Any]:
    """Essaie de parser une valeur JSON si c'est une string valide."""
    if isinstance(val, str):
        s = val.strip()
        if (s.startswith("{") and s.endswith("}")) or (s.startswith("[") and s.endswith("]")):
            try:
                return json.loads(s)
            except Exception:
                return None
    return None

# --- 2) Lecture + désérialisation + reconstruction ---
def lire_parquet_et_reconstituer(chemin_parquet: str) -> Tuple[List[Any], pd.DataFrame]:
    """
    Lit le parquet, désérialise les colonnes JSON et reconstruit la liste des JddOdre.
    Retourne (liste_des_jdds_odre, dataframe_enrichi).
    """
    try:
        # Lecture du parquet
        df = pd.read_parquet(chemin_parquet, engine="pyarrow")

        # Colonnes JSON définies dans la config
        cols_json_ress = set(getattr(Configurations, "LISTE_COLS_JSON_RESSOURCES", ["ressources_json"]))
        cols_json_pda  = set(getattr(Configurations, "LISTE_COLS_JSON_PDA", ["matched_blobs_json"]))

        # Désérialisation des colonnes JSON
        for col in df.columns:
            if col in cols_json_ress or col in cols_json_pda:
                df[col] = df[col].apply(parser_json_dans_le_parquet)

        # Reconstruction des objets JddOdre
        champs_meta_attendus = set(getattr(Configurations, "LISTE_CHAMPS_META", []))
        champs_ress_attendus = set(getattr(Configurations, "LISTE_CHAMPS_RESSOURCES", []))
        champs_blobs_attendus = set(getattr(Configurations, "LISTE_CHAMPS_BLOB_MONITORING", []))

        uid_col = "uid" if "uid" in df.columns else ("uid_meta" if "uid_meta" in df.columns else None)
        dataset_id_col = "dataset_id" if "dataset_id" in df.columns else None

        resultat_unifications_des_sources: List[Any] = []

        for idx, row in df.iterrows():
            try:
                id_jdd_odre = idx if isinstance(idx, int) else None
                nom_jdd_odre = str(row.get(dataset_id_col or uid_col, "") or "")

                # Métadonnées
                metadonnees = {col: str(row.get(col, "")) for col in champs_meta_attendus if col in df.columns}

                # Ressources
                ressources = None
                for col in cols_json_ress:
                    if col in df.columns and row.get(col) is not None:
                        ressources = row.get(col)
                        break
                if ressources is None:
                    ressources = {col: str(row.get(col, "")) for col in champs_ress_attendus if col in df.columns}

                # PDA
                pda_opendata = None
                for col in cols_json_pda:
                    if col in df.columns and row.get(col) is not None:
                        pda_opendata = row.get(col)
                        break
                if pda_opendata is None:
                    pda_opendata = {col: str(row.get(col, "")) for col in champs_blobs_attendus if col in df.columns}

                # Ajout à la liste
                resultat_unifications_des_sources.append(JddOdre(
                    id_jdd_odre=id_jdd_odre,
                    nom_jdd_odre=nom_jdd_odre,
                    metadonnees=metadonnees or None,
                    ressources=ressources,
                    PDA_opendata=pda_opendata,
                ))
            except Exception as e:
                print(f"Erreur sur la ligne {idx}: {e}")
                continue

        return resultat_unifications_des_sources, df

    except Exception as e:
        print(f"Erreur lecture parquet ou reconstruction: {e}")
        return [], pd.DataFrame()

def lire_json_en_dataframe(chemin_json: str) -> pd.DataFrame:
    """
    Lit un fichier JSON (liste de dicts) et retourne un DataFrame.
    """
    try:
        # Lecture du fichier JSON
        with open(chemin_json, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Conversion en DataFrame
        if isinstance(data, list):
            return pd.DataFrame(data)
        elif isinstance(data, dict) and "__ALL__" in data:
            # Cas où tu as un dict avec clé "__ALL__"
            return pd.DataFrame(data["__ALL__"])
        else:
            # Cas générique
            return pd.DataFrame([data])

    except Exception as e:
        print(f"Erreur lecture JSON : {e}")
        return pd.DataFrame()


def lire_parquet_direct_v0(chemin_parquet: str):
    """
    Lit un fichier Parquet avec PyArrow et désérialise les colonnes JSON string.
    Retourne une liste de dictionnaires (chaque ligne).
    """
    try:
        # Charger le fichier Parquet
        parquet_file = pq.ParquetFile(chemin_parquet)

        # Lire en batch (table Arrow)
        table = parquet_file.read()

        # Convertir en dictionnaires ligne par ligne
        records = table.to_pylist()  # Liste de dicts natifs Python

        # Désérialiser les colonnes JSON (si présentes)
        colonnes_json = ["ressources_json", "matched_blobs_json"]  # adapte selon ta config
        for row in records:
            for col in colonnes_json:
                if col in row and isinstance(row[col], str):
                    try:
                        row[col] = json.loads(row[col])
                    except Exception:
                        pass  # laisse la valeur telle quelle si parsing échoue

        return records  # Liste de dicts (tu peux ensuite faire ce que tu veux)

    except Exception as e:
        print(f"Erreur lecture Parquet direct: {e}")
        return []


def lire_parquet_direct(chemin_parquet: Path,
                        colonnes_json: List[str] = None) -> List[Dict[str, Any]]:
    """
    Lit un fichier Parquet via PyArrow et renvoie une liste de dicts (une par ligne).
    Désérialise les colonnes JSON stockées en string (si renseignées).
    """
    try:
        if not chemin_parquet.exists():
            return []

        pf = pq.ParquetFile(str(chemin_parquet))
        table = pf.read()                # pyarrow.Table
        records = table.to_pylist()      # liste de dicts Python

        colonnes_json = colonnes_json or (
            list(getattr(Configurations, "LISTE_COLS_JSON_RESSOURCES", ["ressources_json"])) +
            list(getattr(Configurations, "LISTE_COLS_JSON_PDA", ["matched_blobs_json"]))
        )

        # Désérialisation en place des colonnes JSON string
        for rec in records:
            for col in colonnes_json:
                val = rec.get(col)
                if isinstance(val, str):
                    s = val.strip()
                    if (s.startswith("{") and s.endswith("}")) or (s.startswith("[") and s.endswith("]")):
                        try:
                            rec[col] = json.loads(s)
                        except Exception:
                            # On laisse la valeur telle quelle si le parsing échoue
                            pass

        return records

    except Exception as e:
        # En prod: logger
        print(f"[lire_parquet_direct] Erreur: {e}")
        return []


def records_en_dataframe_sur(records: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Convertit une liste de dicts en DataFrame. Gère le cas vide.
    """
    try:
        if not records:
            return pd.DataFrame()
        return pd.DataFrame(records)
    except Exception as e:
        print(f"[records_en_dataframe_sur] Erreur: {e}")
        return pd.DataFrame()



def applatir_jdds(liste_des_jdds_odre) -> pd.DataFrame:
    """
    Aplati une liste de dicts avec imbrication à deux niveaux (ressources_json et matched_blobs_json).
    Chaque ressource devient une ligne avec toutes les clés du niveau racine + clés des ressources + blobs.
    """
    rows_out = []

    for rec in liste_des_jdds_odre:
        # Copie toutes les clés du niveau racine
        dataset_meta = {}
        for k, v in rec.items():
            if k == "ressources_count":
                try:
                    dataset_meta[k] = int(v)
                except:
                    dataset_meta[k] = 0
            elif k == "has_sources_externes_pda_opendata_monitoring":
                dataset_meta[k] = str(v).strip().lower() == "true"
            else:
                dataset_meta[k] = v

        # Déplier matched_blobs_json (dict)
        blobs = rec.get("matched_blobs_json", {})
        if isinstance(blobs, dict):
            for bk, bv in blobs.items():
                dataset_meta[f"blob_{bk}"] = bv

        # Déplier ressources_json (liste)
        ressources_list = rec.get("ressources_json", [])
        if isinstance(ressources_list, list) and len(ressources_list) > 0:
            for res in ressources_list:
                if isinstance(res, dict):
                    row = dataset_meta.copy()
                    for rk, rv in res.items():
                        row[f"ressource_{rk}"] = rv
                    rows_out.append(row)
        else:
            rows_out.append(dataset_meta)

    return pd.DataFrame(rows_out)



def aplatir_jdds_generique(liste_des_jdds_odre):
    """
    Aplati une liste de dicts avec imbrication à deux niveaux (ressources_json et matched_blobs_json).
    - Prend toutes les clés du niveau racine (sans connaître les noms).
    - Déplie matched_blobs_json: ajoute les clés sans préfixe ET avec préfixe 'blob_'.
    - Déplie ressources_json: ajoute les clés sans préfixe ET avec préfixe 'ressource_' pour chaque ressource.
    Retourne un DataFrame plat.
    """
    rows_out = []

    for rec in liste_des_jdds_odre:
        if not isinstance(rec, dict):
            # ignore les éléments non-dict
            continue

        # --- Copie toutes les clés du niveau racine ---
        dataset_meta = {}
        for k, v in rec.items():
            # Conversion légère: ressources_count -> int
            if k == "ressources_count":
                try:
                    dataset_meta[k] = int(v)
                except Exception:
                    dataset_meta[k] = 0
            # Conversion légère: has_sources... -> bool (True si "true")
            elif k == "has_sources_externes_pda_opendata_monitoring":
                dataset_meta[k] = str(v).strip().lower() == "true"
            else:
                dataset_meta[k] = v

        # --- Déplier matched_blobs_json : TOUTES les clés, avec et sans préfixe ---
        blobs = rec.get("matched_blobs_json", {})
        if isinstance(blobs, dict):
            for bk, bv in blobs.items():
                # Sans préfixe (n'écrase pas une clé racine existante)
                if bk not in dataset_meta:
                    dataset_meta[bk] = bv
                # Avec préfixe
                dataset_meta[f"blob_{bk}"] = bv

        # --- Déplier ressources_json : TOUTES les clés de chaque ressource, avec et sans préfixe ---
        ressources_list = rec.get("ressources_json", [])
        if isinstance(ressources_list, list) and len(ressources_list) > 0:
            for res in ressources_list:
                if not isinstance(res, dict):
                    continue

                row = dataset_meta.copy()
                for rk, rv in res.items():
                    # Sans préfixe (n'écrase pas les clés déjà présentes dans row)
                    if rk not in row:
                        row[rk] = rv
                    # Avec préfixe
                    row[f"ressource_{rk}"] = rv

                rows_out.append(row)
        else:
            # Aucune ressource: on garde juste les métadonnées dataset/blobs
            rows_out.append(dataset_meta)

    return pd.DataFrame(rows_out)


def construire_df_0(df1: pd.DataFrame, 
                  df2: pd.DataFrame, 
                  df3: pd.DataFrame,
                  uid_col_df1="uid", 
                  uid_meta_df2="uid_metadata",
                  display_col_df2="display_name",
                  df3_match_col="FullName_lower",
                  df3_prefix="blob_"
    ) -> pd.DataFrame:
    """
    Construit un DataFrame final en combinant df1, df2 et df3 selon la règle décrite.

    - df1 : DataFrame principal (une ligne par uid)
    - df2 : métadonnées liées à df1 (plusieurs lignes possibles par uid, élargies en colonnes numérotées)
    - df3 : annuaire/infos à joindre si FullName_lower contient au moins un display_name_i

    Logique :
    comment construire un df à partir de trois df (1, 2, 3) de la façon suivante:
        autant de ligne que le df1(les lignes sont uniques)
        par ligne toutes les colonnes de df1, autant de cols (prefixées avec des numéros) de df2 
        qui la colonne "uid_metadata" de df2 est dans la liste unique des valeur de la col "uid" du df1, 
        une ligne de df3 avec toutes les cols de df3 lorsque l'une des valeurs de col "display_name" (prefixée avec des numéros) 
        de df2 est contenu dans la liste de valeur unique de la col "FullName_lower de df3 (chaîne de caractère dans un chaîne de caractère plus longue)

    """

    # 1) Lignes du résultat = lignes uniques de df1 (sur uid)
    df1_unique = df1.drop_duplicates(subset=[uid_col_df1]).copy()

    # 2) Filtrer df2 sur les uid présents dans df1
    uid_set = set(df1_unique[uid_col_df1].unique())
    df2_filt = df2[df2[uid_meta_df2].isin(uid_set)].copy()


    # Numérotation des occurrences de df2 par uid (pour élargir en colonnes _1, _2, ...)
    df2_filt["n"] = df2_filt.groupby(uid_meta_df2).cumcount() + 1

    # Passer en large : index (uid_metadata, n) -> unstack sur n -> colonnes numérotées
    df2_wide = (
        df2_filt
        .set_index([uid_meta_df2, "n"])
        .sort_index()
        .unstack("n")  # MultiIndex de colonnes : (col_df2, n)
    )

    # Aplatir les noms de colonnes (colonne -> colonne_n)
    df2_wide.columns = [f"{col}_{n}" for col, n in df2_wide.columns]
    df2_wide = df2_wide.reset_index().rename(columns={uid_meta_df2: uid_col_df1})

    # 3) Merge df1 + df2 (large) sur uid
    df_merged = df1_unique.merge(df2_wide, on=uid_col_df1, how="left")

    # 4) Pour chaque ligne, trouver UNE ligne de df3 si au moins un display_name_i est sous-chaîne de FullName_lower
    #    On récupère toutes les colonnes de df3 avec un préfixe pour éviter les collisions.
    df3_prefixed = df3.add_prefix(df3_prefix)

    # Colonnes display_name numérotées issues de df2 (ex. display_name_1, display_name_2, ...)
    display_cols = [c for c in df_merged.columns if c.startswith(f"{display_col_df2}_")]

    def pick_df3_row(row):
        # Récupérer les display_name_i valides pour la ligne
        names = [str(row[c]).strip() for c in display_cols if pd.notna(row.get(c))]
        names = [n for n in names if n]  # enlever vides

        # Si rien à tester, renvoyer des NaN pour les colonnes df3
        if not names:
            return pd.Series({col: pd.NA for col in df3_prefixed.columns})

        # Construire une regex "OU" en protégeant les caractères spéciaux
        pattern = "|".join(re.escape(n) for n in names)
        # str.contains insensible à la casse (case=False)
        hits = df3[df3[df3_match_col].str.contains(pattern, case=False, na=False)]

        if hits.empty:
            return pd.Series({col: pd.NA for col in df3_prefixed.columns})

        # Prendre la première ligne qui matche et préfixer les colonnes
        first = hits.iloc[0]
        return pd.Series({df3_prefix + col: first[col] for col in df3.columns})

    # Appliquer ligne par ligne pour ajouter les colonnes df3_* au df_merged
    df3_added = df_merged.apply(pick_df3_row, axis=1)
    df_final = pd.concat([df_merged, df3_added], axis=1)


    return df_final


def construire_df(df1: pd.DataFrame, 
                  df2: pd.DataFrame, 
                  df3: pd.DataFrame,
                  uid_col_df1: str = "uid", 
                  uid_meta_df2: str = "uid_metadata",
                  display_col_df2: str = "display_name",
                  df3_match_col: str = "FullName_lower",
                  df3_prefix: str = "blob_"
    ) -> pd.DataFrame:
    """
    Construit un DataFrame final en combinant df1, df2 et df3 selon la règle:
      - Lignes = uids uniques de df1
      - Colonnes = toutes celles de df1 + df2 élargi (colonnes suffixées _1, _2, ...)
      - Ajout d'une ligne de df3 (si match de sous-chaîne sur display_name_i) avec préfixe df3_prefix (ex. 'blob_')
    """

    # 1) Lignes uniques sur uid (df1)
    df1_unique = df1.drop_duplicates(subset=[uid_col_df1]).copy()

    # 2) Filtrer df2 sur les uid présents dans df1
    uid_set = set(df1_unique[uid_col_df1].unique())
    df2_filt = df2[df2[uid_meta_df2].isin(uid_set)].copy()

    # 3) Élargir df2 : numérotation puis unstack -> colonnes suffixées _n
    df2_filt["n"] = df2_filt.groupby(uid_meta_df2).cumcount() + 1
    df2_wide = (
        df2_filt
        .set_index([uid_meta_df2, "n"])
        .sort_index()
        .unstack("n")
    )
    df2_wide.columns = [f"{col}_{n}" for col, n in df2_wide.columns]
    df2_wide = df2_wide.reset_index().rename(columns={uid_meta_df2: uid_col_df1})

    # 4) Merge df1 + df2 (wide) sur uid
    df_merged = df1_unique.merge(df2_wide, on=uid_col_df1, how="left")

    # 5) Ajout des colonnes de df3 (match par sous-chaîne sur display_name_i), préfixées df3_prefix
    df3_prefixed = df3.add_prefix(df3_prefix)
    display_cols = [c for c in df_merged.columns if c.startswith(f"{display_col_df2}_")]

    def pick_df3_row(row: pd.Series) -> pd.Series:
        names = [str(row[c]).strip() for c in display_cols if pd.notna(row.get(c))]
        names = [n for n in names if n]
        if not names:
            return pd.Series({col: pd.NA for col in df3_prefixed.columns})

        pattern = "|".join(re.escape(n) for n in names)
        hits = df3[df3[df3_match_col].str.contains(pattern, case=False, na=False)]
        if hits.empty:
            return pd.Series({col: pd.NA for col in df3_prefixed.columns})

        first = hits.iloc[0]
        return pd.Series({df3_prefix + col: first[col] for col in df3.columns})

    df3_added = df_merged.apply(pick_df3_row, axis=1)
    df_final = pd.concat([df_merged, df3_added], axis=1)

    return df_final


