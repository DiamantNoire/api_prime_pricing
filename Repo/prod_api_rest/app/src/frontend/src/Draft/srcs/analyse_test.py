
# fichier: compter_uid_parquet.py
import sys
import pandas as pd
from pathlib import Path

def compter_uid(parquet_path: str, colonne: str = "uid") -> None:
    p = Path(parquet_path)
    if not p.exists():
        print(f"❌ Fichier introuvable: {p}")
        return

    # Lecture du parquet (Pandas choisira l’engine disponible, pyarrow ou fastparquet)
    df = pd.read_parquet(p)

    if colonne not in df.columns:
        print(f"❌ Colonne '{colonne}' absente. Colonnes disponibles: {list(df.columns)}")
        return

    total_lignes = len(df)
    non_nuls = df[colonne].notna().sum()
    nuls = df[colonne].isna().sum()
    uniques = df[colonne].nunique(dropna=True)

    print(f"📄 Fichier: {p}")
    print(f"🧮 Lignes totales                 : {total_lignes}")
    print(f"✅ Valeurs non nulles '{colonne}' : {non_nuls}")
    print(f"∅  Valeurs nulles '{colonne}'     : {nuls}")
    print(f"🔑 Valeurs uniques '{colonne}'    : {uniques}")

    # Optionnel: aperçu de quelques valeurs (non nulles)
    apercu = df[colonne].dropna().astype(str).head(10).tolist()
    if apercu:
        print(f"👀 Aperçu des 10 premières valeurs non nulles: {apercu}")

if __name__ == "__main__":
    # Utilisation:
    #   python compter_uid_parquet.py srcs/data/JDD_ODRE.parquet
    #   python compter_uid_parquet.py srcs/data/JDD_ODRE.parquet id_colonne

    chemin = r"C:\Users\\0471IA\OneDrive - NaTran\_1_Outils de supervision JDD ODRE\_7_Streamlit_app\srcs\data\JDD_ODRE.parquet"
    col = "uid"
    compter_uid(chemin, col)



from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import pandas as pd
import pyarrow.parquet as pq  # utilisé pour liste_des_jdds_format_tech_parquet["__ALL__"]

from srcs.configs import Configurations

# Helpers supposés présents dans ton codebase
# - _normaliser_colonnes(df): normalise les noms de colonnes
# - _chaine_de_caractere_pour_df(df): cast str pour toutes colonnes
# - _premier_sources_externes_pda_opendata(json_str): retourne dict (premier match)
# - parser_json_dans_le_parquet(x): parse un champ JSON (string) -> dict|list ou None

def reunifier_et_consolider_sources(
    sources_externes_metadata: pd.DataFrame,
    sources_externes_ressources: pd.DataFrame,
    sources_externes_pda_opendata: pd.DataFrame,
) -> Tuple[
    List[Any],                # liste_des_jdds_odre
    Dict[str, Any],           # liste_des_jdds_format_tech_parquet
    Dict[str, pd.DataFrame],  # liste_des_jdds_dataframe
    Dict[str, Any],           # json_consolide_dict
]:
    """
    Réunifie META + RESSOURCES + PDA et consolide à 1 ligne par UID (≈ 455).
    Retourne 4 éléments selon la signature imposée.
    """

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
        # garder une seule clé – supprime la clé droite
        if right_key in sources_externes_metadata_et_ressources.columns:
            sources_externes_metadata_et_ressources = sources_externes_metadata_et_ressources.drop(columns=[right_key])
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
    pda_cols = [
        "matched_blobs_json",
        "has_sources_externes_pda_opendata_monitoring",
        "name", "size", "lastmodified", "boolisdeleted",
        "contenttype", "storageaccountname", "storagecontainername", "FullName",
    ]
    pda_per_uid = (
        sources_externes_metadata_et_ressources
        .groupby("uid", dropna=False)[pda_cols]
        .nth(0)
        .reset_index()
    )

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

    # ⚠️ IMPORTANT : c'est ce DF consolidé (≈ 455 lignes) qui doit être utilisé pour les retours suivants
    sources_externes_metadata__ressources_blob = df_final

    # -------------------------------------------------------------------------
    # === Retours imposés (4 valeurs) – bloc conforme à ta signature ===
    # -------------------------------------------------------------------------

    # Initialisations par défaut (en cas de DF vide)
    liste_des_jdds_odre: List[Any] = []
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
