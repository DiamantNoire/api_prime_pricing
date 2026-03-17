# --- Application de supervision des jeux de données ODRE | chemin: srcs/codes_pour_sources_externes_app/ouitils_pour_sources_externes.py

# === Importation librairies ===
import re
import json
import math
import requests
import unicodedata
import dataclasses
import pandas as pd
from pathlib import Path
import pyarrow.parquet as pq
from pandas.api.types import is_scalar


from typing import Set
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from typing import Dict, List, Tuple, Any, Optional


# === Importation de modules ===
from srcs.configs import Configurations
from srcs.codes_pour_metier_admin_jdd_odre_app.modelisation_jdd_odre import(
    JddOdre
)



# =============================================================================
# Regroupement par appel dans les autres modules de cette couche (technique) 
#   - Appel 1 : Module: entrees_sorties_app 
#   - Appel 2 : Module: mapping
# =============================================================================


# =============================================================================
# Appel 1 : Module: entrees_sorties_app 
# =============================================================================

# Codes pour les fonctions auxiliaires | Un peu long car regroupe toutes les sources (2 API + EXTRACT EXCEL)== #

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
    # === Retours imposés (4 valeurs) – bloc conforme à la signature ===
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

def alimenter_app_en_data_test(connecteurs: Dict[str, Any]) -> Tuple[pd.DataFrame, 
                                                                     pd.DataFrame, 
                                                                     pd.DataFrame
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
        Tuple[List[JddOdre], Dict[str, pq.ParquetFile], 
            Dict[str, pd.DataFrame], Dict[str, Any]
    ]

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

    # === Sauvegarde pour modélisation : Evite de charger à nouveau ===

    if hasattr(Configurations, "SORTIE_JSON_SOURCE_EXTERNE_METADTA"):
        chemin_source_externe_metadata: Path = Configurations.SORTIE_JSON_SOURCE_EXTERNE_METADTA
        try:
            chemin_source_externe_metadata.parent.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass
        with chemin_source_externe_metadata.open("w", encoding="utf-8") as f:
            dict_source_externe_metadta = sources_externes_metadata.to_dict(orient="records")
            json.dump(dict_source_externe_metadta, f, ensure_ascii=False, indent=2)

    if hasattr(Configurations, "SORTIE_JSON_SOURCE_EXTERNE_RESSOURCES"):
        chemin_source_externe_ressources: Path = Configurations.SORTIE_JSON_SOURCE_EXTERNE_RESSOURCES
        try:
            chemin_source_externe_ressources.parent.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass
        with chemin_source_externe_ressources.open("w", encoding="utf-8") as f:
            dict_sources_externes_ressources = sources_externes_ressources.to_dict(orient="records")
            json.dump(dict_sources_externes_ressources, f, ensure_ascii=False, indent=2)

    if hasattr(Configurations, "SORTIE_JSON_SOURCE_EXTERNE_PDA"):
        chemin_source_externe_pda: Path = Configurations.SORTIE_JSON_SOURCE_EXTERNE_PDA
        try:
            chemin_source_externe_pda.parent.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass
        with chemin_source_externe_pda.open("w", encoding="utf-8") as f:
            dict_sources_externes_pda_opendata = sources_externes_pda_opendata.to_dict(orient="records")
            json.dump(dict_sources_externes_pda_opendata, f, ensure_ascii=False, indent=2)

    return (sources_externes_metadata, sources_externes_ressources, sources_externes_pda_opendata)





# =============================================================================
# Appel 2 : Module: mapping
# =============================================================================

# Codes pour les fonctions auxiliaires | Manipulation autour d'une liste de jeux de données == #
# ---- But: Mettre en place une lecture rapide de cette liste dans l'application  ---
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

def _construire_entites_depuis_df(self, df_consolide: pd.DataFrame) -> List[JddOdre]:
    """
    Construit une liste d'entités JddOdre à partir du DataFrame consolidé.
    - Métadonnées : lookup direct des champs listés (sans suffixe/préfixe).
    - Ressources : multiplicité fidèle -> liste d'objets ressource (regroupés par suffixe _n).
    - PDA OpenData : lookup sur colonnes préfixées 'blob_' dans le DF, exposées sans préfixe dans l'entité.
    - Isolation : dicts NEUFS par entité, pas de partage de références.
    - Normalisation : NaN / pd.NA -> None ; containers vides ignorés.
    """

    if df_consolide is None or df_consolide.empty:
        return []

    # Raccourcis de configuration (noms SANS suffixe ni préfixe)
    liste_metadta   = Configurations.LISTE_CHAMPS_META                 # ex: ["uid", "dataset_id", "title", ...]
    liste_ressource = Configurations.LISTE_CHAMPS_RESSOURCES          # ex: ["resource_url", "format", "title", "size"]
    liste_blob      = Configurations.LISTE_CHAMPS_BLOB_MONITORING      # ex: ["FullName_lower", "team", ...]
    blob_prefix     = "blob_"  # doit correspondre au préfixe utilisé dans construire_df

    all_cols = list(df_consolide.columns)
    suffix_re = re.compile(r"_(\d+)$")

    # --- Utilitaires robustes (évite l'ambiguïté booléenne des arrays/Series) ---

    def is_na(v: Any) -> bool:
        """
        True pour scalaires NA (None, NaN, pd.NA).
        False pour non-scalaires (list, dict, np.ndarray, etc.) -> on gère via is_empty().
        """
        if is_scalar(v):
            return pd.isna(v)
        return v is None

    def is_empty(v: Any) -> bool:
        """
        Détermine si une valeur est 'vide' :
          - scalaires NA -> vide
          - chaîne vide / whitespace -> vide
          - conteneurs (list/tuple/set/dict) longueur 0 -> vide
          - np.ndarray longueur 0 -> vide
        """
        if is_na(v):
            return True
        if isinstance(v, str):
            return v.strip() == ""
        if isinstance(v, (list, tuple, set, dict)):
            return len(v) == 0
        # np.ndarray / pandas types : essayer len()
        try:
            return len(v) == 0
        except Exception:
            return False

    def normalize(v: Any) -> Optional[Any]:
        """Remplace NaN/pd.NA par None ; conserve les autres valeurs (y compris conteneurs non vides)."""
        return None if is_na(v) else v

    def collect_suffixes_for_base(base: str) -> List[int]:
        """
        Retourne la liste triée des indices suffixes disponibles pour ce 'base'
        en scannant les colonnes du DF: base_1, base_2, ... ; ignore les colonnes non conformes.
        """
        suffixes = set()
        prefix = f"{base}_"
        for col in all_cols:
            if col.startswith(prefix):
                m = suffix_re.search(col)
                if m:
                    try:
                        suffixes.add(int(m.group(1)))
                    except Exception:
                        # colonne non conforme -> ignorer poliment
                        pass
        return sorted(suffixes)

    def to_int_or_pos(idx: Any, pos: int) -> int:
        """Essaye de caster l'index en int ; sinon, fallback sur la position de boucle."""
        try:
            return int(idx)
        except Exception:
            return pos

    jdds: List[JddOdre] = []

    for pos, (idx, lig) in enumerate(df_consolide.iterrows()):
        # --- Isolation: dictionnaires NEUFS par ligne
        metadonnees: Dict[str, Any] = {}
        pda_opendata: Dict[str, Any] = {}

        # --- 1) Métadonnées (lookup direct sur noms identiques dans le DF)
        for champ in liste_metadta:
            if champ in all_cols:
                val = normalize(lig.get(champ))
                if not is_empty(val):
                    metadonnees[champ] = val

        # --- 2) Ressources (liste d'objets ressource regroupés par suffixe)
        # Bases réellement présentes (au moins une colonne 'base_n' existe dans le DF)
        bases_presentes = [b for b in liste_ressource if any(c.startswith(f"{b}_") for c in all_cols)]
        # Union des suffixes disponibles sur toutes les bases
        suffixes_union = set()
        for base in bases_presentes:
            suffixes_union.update(collect_suffixes_for_base(base))

        ressources: List[Dict[str, Any]] = []
        for n in sorted(suffixes_union):
            res_obj: Dict[str, Any] = {}
            for base in bases_presentes:
                coln = f"{base}_{n}"
                if coln in all_cols:
                    v = normalize(lig.get(coln))
                    if not is_empty(v):
                        res_obj[base] = v
            # Ajouter l'objet ressource uniquement s'il contient au moins un champ non vide
            if res_obj:
                ressources.append(res_obj)

        # --- 3) PDA OpenData (lookup sur blob_<champ> dans le DF, exposé sans 'blob_' dans l'entité)
        for champ in liste_blob:
            blob_col = f"{blob_prefix}{champ}"
            if blob_col in all_cols:
                v = normalize(lig.get(blob_col))
                if not is_empty(v):
                    pda_opendata[champ] = v

        # --- 4) Identité de l'entité
        uid = normalize(lig.get("uid"))
        dataset_id = normalize(lig.get("dataset_id"))
        id_jdd = to_int_or_pos(idx, pos)

        jdds.append(
            JddOdre(
                id_jdd_odre=id_jdd,
                nom_jdd_odre=str(dataset_id) if not is_empty(dataset_id) else str(uid),
                metadonnees=metadonnees,
                ressources=ressources,           # multiplicité fidèle -> liste d'objets ressource
                pda_opendata=pda_opendata,       # optionnelle -> dict éventuellement vide
            )
        )

    return jdds

# ----- Sous fonction utiles | transformer tes objets en dictionnaires sérialisables (JSON) ------
def to_jsonable(obj):
        """
            Petite fonction utilitaire pour transformer tes objets en dictionnaires sérialisables (JSON).
        """
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
        # sinon, tenter un fallback sûr
        return obj

# ----- Sous fonction utiles | Cette fonction te permettra d’écrire une ligne JSON pour chaque JddOdre. ------
def save_jdds_jsonl(liste_jdds, path="jdds.jsonl"):
    """Écrit un fichier JSON Lines : une ligne par JDD."""
    with open(path, "w", encoding="utf-8") as f:
        for j in liste_jdds:
            line = json.dumps(to_jsonable(j), ensure_ascii=False)
            f.write(line + "\n")

# ----- Sous fonction utiles | Cette fonction lis en JSONL. ------
def load_jdds_jsonl_as_dicts(path:Optional[str]):
    """Retourne une List[dict] lue depuis JSONL."""
    data = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                data.append(json.loads(line))
    return data


