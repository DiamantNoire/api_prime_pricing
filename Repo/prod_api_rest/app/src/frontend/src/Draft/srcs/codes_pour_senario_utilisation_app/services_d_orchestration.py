# --- Application de supervision des jeux de données ODRE
# chemin: srcs/codes_pour_senario_utilisation_app/service_d_orchestration.py
# ==== coding: utf-8 ====

# === Importation de librairies ===
from __future__ import annotations

import re
import json
import math
import unicodedata
import pandas as pd
import streamlit as st
import pyarrow.parquet as pq

from pathlib import Path
from dataclasses import dataclass
from pandas.api.types import is_scalar
from datetime import datetime, timedelta, timezone
from typing import Callable, Optional, Tuple, List, Dict, Any



# === Importation de modules ===
from srcs.configs import Configurations
from srcs.codes_pour_metier_admin_jdd_odre_app.modelisation_jdd_odre import JddOdre

from srcs.codes_pour_metier_admin_jdd_odre_app.logiques_metier import(
    EtatActualisationJdd
)
from srcs.codes_pour_metier_admin_jdd_odre_app.ports_abstraits_connexions_aux_sources_externes import(
    PortAbstraitRecupererJdd0dre
)
from srcs.codes_pour_sources_externes_app.entrees_sorties_app import(
    AdaptateurSourcesExternes
)

from srcs.codes_pour_sources_externes_app.mapping import(
    ConvertirSourcesenJddOdre
)


from srcs.codes_pour_metier_admin_jdd_odre_app.logiques_metier import (
    AnalyseActualisationJdd, ServiceActualisationDomaine, 
    calculer_indicateurs_globaux
)
from srcs.codes_pour_sources_externes_app.entrees_sorties_app import (
    alimenter_app_en_data,
    alimenter_app_en_data_test
)
from  srcs.codes_pour_senario_utilisation_app.outils_pour_les_services import (
    lire,
    _temps_actuel,
    _lire_le_cache_data,
    _age_cache_en_j_h_m_s,
    _analyse_declencheur_auto,
    _ecrire_dans_le_cache_data,
    lire_parquet_direct,
    construire_df,
    lire_metadata,
    lire_ressources,
    declencher,
    lire_extraction_blob_opendata,
    construire_liste_jdds_odre,
    sauvegarder
)



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
#   Orchestration 1 : Service d'alimentation de l'app en données externes 
# =============================================================================
#-----Alimentation automatique | Page: connexion --------------
class ServiceSourcesExternes:
    def __init__(self,
                 port_de_connexion: PortAbstraitRecupererJdd0dre
    ):
        self.port_de_connexion = port_de_connexion
    
    def alimenter_l_application(self) -> bool:
        """
        Orchestration: 
        
            - Connexion aux sources externes

            - Téléchargement des données externes

            - Mise en forme des données (modélisation en jeux de données)

            - sauvegarde des données (3 fichiers json dans l'application)

                fichier1 : catalogue des métadonnées pour les jeux de données sur odre

                fichier2 : ressources associées aux jeux de données 
                
                fichier3 : ressources pointant vers le blob opendata de la pda

        """
        try:
            return self.port_de_connexion.brancher_le_port()
        except Exception as e :
            print(f"[Couche: cas d'utilisation] | Module : service_d_orchestration\n")
            print(f"[Couche: cas d'utilisation] | Classe : ServiceSourcesExternes\n")
            raise RuntimeError(f"[erreur]: {e}")

    #-----Alimentation manuelle (en option par l'ulisateur) --------------
    def alimenter_manuellement(self, declencheur:Optional[str]="NON") -> bool:
        """
            Orchestrattion:
                - Alimenter l'application manuellement
                - Sur sollicitation de l'utisateur
                - Déclencheur mise à NON par défaut

        """
        try:
            if declencheur=="OUI":
                valeur = declencher(declencheur=declencher)
                if valeur == "OUI":
                    return True
        except Exception as e :
            print(f"[Couche: cas d'utilisation] | Module : service_d_orchestration\n")
            print(f"[Couche: cas d'utilisation] | Classe : ServiceSourcesExternes\n")
            print(f"[Couche: cas d'utilisation] | Fonction : alimenter_manuellement\n")
            print(f"[Couche: cas d'utilisation] | Erreur : {e}\n")
            return False



# =============================================================================
#   Orchestration 2 : Service de lecture des données sauvegardées dans l'app 
# =============================================================================
@dataclass
class ServiceDemarrage:
    def __init__(self,
                 chemins_fichiers_ds_app: dict[str, str]
    ):
        self.chemins_fichiers_ds_app = chemins_fichiers_ds_app
    
    def lire_les_sources_depuis_app(self) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
            Orchestration:
                Lecture des données sauvegardées dans l'application
                - Lecture du fichier catalogue des métadonnées pour les jeux de données de l'opendata
                - Lecture du fichier ressources associées aux jeux de données de l'opendata
                - Lecture du fichier blob opendata pour les ressources qui pontent sur la pda

        """
        chemin_vers_metadata = self.chemins_fichiers_ds_app.get("catalogue_metadata")
        chemin_vers_ressources = self.chemins_fichiers_ds_app.get("ressources_des_jdds")
        chemin_vers_blob_opendata = self.chemins_fichiers_ds_app.get("blob_opendata")
        try:
            sources_externe_metadata = lire_metadata(chemin_fichier=chemin_vers_metadata)
            sources_externe_ressources = lire_ressources(chemin_fichier=chemin_vers_ressources)
            sources_externe_pda = lire_extraction_blob_opendata(chemin_fichier=chemin_vers_blob_opendata)

            return (sources_externe_metadata, sources_externe_ressources, sources_externe_pda)
        
        except Exception as e :
            print(f"[Couche: cas d'utilisation] | Module : service_d_orchestration\n")
            print(f"[Couche: cas d'utilisation] | Classe : ServiceSourcesExternes\n")
            print(f"[Couche: cas d'utilisation] | Fonction : lire_les_sources_depuis_app\n")
            print(f"[Couche: cas d'utilisation] | Erreur : {e}\n")
            return (pd.DataFrame(), pd.DataFrame(), pd.DataFrame())


# =============================================================================
#   Orchestration 3 : Service de traitement des données pour la page 0
# =============================================================================
#--Alimentation toutes les pages avec un modèle de jeux de données opendtat ---
@dataclass
class ServiceJeuxDonneesOpendata:
    def __init__(self): pass
    def construire_et_sauvegarder(self) -> List[JddOdre]:
        """
            Orchestration:
                - Diffusion de la liste des jeux de données opendata à toutes les pages de l'application
                - A partir des sources téléchargées dans l'application automatiquement
                - Sauvegarde de cette liste de jeux de données odre dans l'application (important)

        """
        les_chemins_des_fichiers = Configurations.SERIES_CHEMINS_VERS_FICHIERS
        appel_au_service_de_lecture = ServiceDemarrage(chemins_fichiers_ds_app=les_chemins_des_fichiers)
        df_sources_externes_metadta, df_sources_externes_ressources, df_sources_externes_pda = appel_au_service_de_lecture.lire_les_sources_depuis_app()
        liste_des_jdds_odre = []
        try:

            liste_des_jdds_odre = construire_liste_jdds_odre(df_metadata=df_sources_externes_metadta,
                                                             df_ressources=df_sources_externes_ressources,
                                                             df_blob_opendata=df_sources_externes_pda
            )
            chemin_liste_jdds = Configurations.SERIES_CHEMINS_VERS_FICHIERS.get("liste_des_jdd_opendata", "")
            ok = sauvegarder(liste_jdds=liste_des_jdds_odre,
                        path=Path(chemin_liste_jdds),
                        schema_version="1.0")
            return liste_des_jdds_odre
        
        except Exception as e:
            print(f"[Couche: cas d'utilisation] | Module : service_d_orchestration\n")
            print(f"[Couche: cas d'utilisation] | Classe : ServiceJeuxDonneesOpendata\n")
            print(f"[Couche: cas d'utilisation] | Fonction : difuser_a_toutes_les_pages\n")
            print(f"[Couche: cas d'utilisation] | Erreur : {e}\n")
            return []
    
    @st.cache_data(show_spinner=True)
    def lire_la_liste(self) -> Tuple[List[JddOdre], List[str]]:
        """
            Orchestration:
                - Lecture d'une liste de jeux de données sauvegardée dans l'application
                - Diffusion à toutes les pages de l'application (fait dans les pages)
        """
        try:
            chemin_vers_jdds_app = Path(Configurations.SERIES_CHEMINS_VERS_FICHIERS.get("liste_des_jdd_opendata", ""))
            liste_jdds_opendata, infos = lire(path=chemin_vers_jdds_app,
                                              expected_schema_version="1.0",
                                              compressed=False,
                                              strict_schema=False
            )
            return liste_jdds_opendata, infos
        
        except Exception as e:
            msg = (
                "[Couche: cas d'utilisation] | Module : service_d_orchestration\n"
                "[Couche: cas d'utilisation] | Classe : ServiceJeuxDonneesOpendata\n"
                "[Couche: cas d'utilisation] | Fonction : lire\n"
                f"[Couche: cas d'utilisation] | Erreur : {e}\n"
            )
            print(msg, flush=True)
            # la signature: retourner (liste, infos)
            return [], [msg]



# =============================================================================
#   Orchestration 4 : Service de traitement des données pour la page 1
# =============================================================================

# =============================================================================
#   Orchestration 5 : Service de traitement des données pour la page 2
# =============================================================================

# =============================================================================
#   Orchestration 6 : Service de traitement des données pour la page 3
# =============================================================================

# =============================================================================
#   Orchestration 7 : Service de traitement des données pour la page 4
# =============================================================================


class ServiceActualisationJdds:
    """
    Service applicatif minimal pour la page 'Actualisation des JDDs'.

    Une seule méthode publique :
      - analyser_liste(...): renvoie {"items": <list[dict]>, "df": <pd.DataFrame>}
    """

    def __init__(self, horloge: Optional[Callable[[], datetime]] = None):
        # Timezone de l'app si dispo, sinon UTC
        self._tz = None
        try:
            self._tz = getattr(Configurations, "TIME_ZONE", None)
        except Exception:
            self._tz = None

        # Horloge : callable -> datetime
        if horloge is not None:
            self._now = horloge
        else:
            if self._tz is not None:
                self._now = lambda: datetime.now(self._tz)
            else:
                self._now = lambda: datetime.now(timezone.utc)


    # ----------------- MÉTHODE PUBLIQUE (UI) -----------------
    def analyser_liste_0(
        self,
        jdds: List[Any],
        frequence_defaut_clef: str = "Mensuel",
        tolerance_override: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Calcule un résumé d'actualisation pour chaque JDD puis retourne :
          - items : liste de dicts 'prêts-UI'
          - df    : DataFrame (une ligne par JDD)

        Règles :
          - Ressource ignorée si 'enabled' ∈ {False, 'false', '0', 'no', 'non'}
          - 'updated_at' en str ISO est parsée (support 'Z', et datetimes naïves rendues aware)
          - Statut = 'à jour' si (maintenant - max(updated_at_actives)) <= période * (1 + tolérance)
          - Tolérance : REGLES_FREQUENCES[clé]['attention'] - 1.0 (sauf si override)
        """
        maintenant = self._now()
        items: List[Dict[str, Any]] = []

        # -------- PROJECTION INLINE (allègement) ----------
        jdds_min: List[Dict[str, Any]] = []
        for j in jdds:
            # lecture sécurisée quel que soit le type (pydantic, dataclass, dict-like)
            id_jdd = getattr(j, "id_jdd_odre", None) if not isinstance(j, dict) else j.get("id_jdd_odre")
            nom_jdd = getattr(j, "nom_jdd_odre", None) if not isinstance(j, dict) else j.get("nom_jdd_odre")
            meta = (getattr(j, "metadonnees", None) if not isinstance(j, dict) else j.get("metadonnees")) or {}
            ressources = (getattr(j, "ressources", None) if not isinstance(j, dict) else j.get("ressources")) or []

            # projection des ressources (aucun traitement, juste les clés utiles)
            res_min = []
            for r in ressources:
                if not isinstance(r, dict):
                    continue
                res_min.append({
                    "uid": r.get("uid"),
                    "title": r.get("title"),
                    "updated_at": r.get("updated_at", r.get("update_at")),
                    "origin_type": r.get("origin_type"),
                    "enabled": r.get("enabled", True),
                })

            jdds_min.append({
                "id_jdd_odre": id_jdd,
                "nom_jdd_odre": nom_jdd,
                "metadonnees": {
                    "uid": meta.get("uid"),
                    "created_at": meta.get("created_at"),
                    "metadata_custom_pas_temporel_value": meta.get("metadata_custom_pas_temporel_value"),
                    "metadata_dcat_accrualperiodicity_value": meta.get("metadata_dcat_accrualperiodicity_value"),
                    "metadata_default_publisher_value": meta.get("metadata_default_publisher_value"),
                    "is_restricted" : meta.get("is_restricted")
                },
                "ressources": res_min,
            })
        # ---------------------------------------------------

        # Helpers locaux
        def _parse_iso(dt_str: Optional[str]) -> Optional[datetime]:
            """Parse ISO (supporte 'Z'); si naïf et TZ connue -> l'attache pour éviter les erreurs d'arithmétique."""
            if not dt_str or not isinstance(dt_str, str):
                return None
            s = dt_str.strip()
            if s.endswith("Z"):
                s = s.replace("Z", "+00:00")
            try:
                dt = datetime.fromisoformat(s)
                # si naïf et on a un TZ, on attache le TZ de l'app
                if dt.tzinfo is None and self._tz is not None:
                    dt = dt.replace(tzinfo=self._tz)
                return dt
            except Exception:
                return None

        # On boucle maintenant sur la liste allégée
        for j in jdds_min:
            meta: Dict[str, Any] = j.get("metadonnees") or {}
            ressources: List[Dict[str, Any]] = j.get("ressources") or []

            # 1) clé de fréquence depuis métadonnées
            clef_freq_meta_en = str(meta.get("metadata_dcat_accrualperiodicity_value") or "").strip().lower()
            clef_freq_meta_fr = str(meta.get("metadata_custom_pas_temporel_value") or "").strip()

            clef_frequence = None
            if clef_freq_meta_en in getattr(Configurations, "TYPE_FREQUENCE", {}):
                clef_frequence = clef_freq_meta_fr

            # 2) période & tolérance
            periode, tolerance = self._periode_et_tolerance_depuis_config(
                clef_frequence or frequence_defaut_clef,
                frequence_defaut_clef=frequence_defaut_clef,
                tolerance_override=tolerance_override,
            )

            # 3) dernières MAJ parmi ressources actives
            dates_upd: List[datetime] = []
            nb_ress_non_a_jour = 0
            delai_ok = periode * (1.0 + max(0.0, tolerance))

            for r in ressources:
                upd = _parse_iso(r.get("updated_at"))
                if upd is not None:
                    dates_upd.append(upd)
                    if (maintenant - upd) > delai_ok:
                        nb_ress_non_a_jour += 1
                else:
                    nb_ress_non_a_jour += 1

            derniere_maj = max(dates_upd) if dates_upd else None
            delta_maj = (maintenant - derniere_maj) if derniere_maj else None
            est_a_jour = (delta_maj is not None) and (delta_maj <= delai_ok)
            prochaine = (derniere_maj + periode) if derniere_maj else None

            # 5) création (str ou datetime)
            date_creation = meta.get("created_at")
            dt_creation = _parse_iso(date_creation) if isinstance(date_creation, str) else (
                date_creation if isinstance(date_creation, datetime) else None
            )
            age_jours = (maintenant.date() - dt_creation.date()).days if dt_creation else None

            # 6) format deltas
            def _delta_en_j_h_m(td: Optional[timedelta]) -> Dict[str, Optional[int]]:
                if td is None:
                    return {"jours": None, "heures": None, "minutes": None}
                total_minutes = int(td.total_seconds() // 60)
                jrs = total_minutes // (24 * 60)
                hrs = (total_minutes % (24 * 60)) // 60
                mins = total_minutes % 60
                return {"jours": jrs, "heures": hrs, "minutes": mins}

            delta_fmt = _delta_en_j_h_m(delta_maj)
            a_jour_depuis = delta_fmt if est_a_jour else {"jours": None, "heures": None, "minutes": None}
            pas_a_jour_depuis = delta_fmt if not est_a_jour else {"jours": None, "heures": None, "minutes": None}

            items.append({
                "uid": meta.get("uid"),
                "nom": j.get("nom_jdd_odre"),
                "producteur": meta.get("metadata_default_publisher_value"),
                "restriction": meta.get("is_restricted"),
                "clef_frequence": clef_frequence or frequence_defaut_clef,
                "periode_jours": int(periode.total_seconds() // 86400),
                "tolerance_ratio": float(tolerance),
                "statut": "à jour" if est_a_jour else "pas à jour",
                "derniere_mise_a_jour": derniere_maj.isoformat() if derniere_maj else None,
                "prochaine_mise_a_jour": prochaine.isoformat() if prochaine else None,
                "a_jour_depuis": a_jour_depuis,
                "pas_a_jour_depuis": pas_a_jour_depuis,
                "age_jdd_jours": age_jours,
                "ressources_total": len(ressources),
                "ressources_non_a_jour": nb_ress_non_a_jour,
            })

        df:pd.DataFrame = self._vers_dataframe(items)
        return {"items": items, "df": df}


    def analyser_liste_1(
        self,
        jdds: List[JddOdre],
    ) -> Dict[str, Any]:
        """
        Analyse une liste de JDD et retourne :
        - items : liste de dicts prêts pour l'UI
        - df    : DataFrame (une ligne par JDD)

        Règles :
        - Ressource ignorée si 'enabled' est falsy (False, 'false', '0', 'no', 'non', 0)
        - Parsing 'updated_at' : support 'Z', datetimes naïves → timezone de l'app si dispo
        - Statut = 'à jour' si (maintenant - max(updated_at_actives)) <= période * (1 + tolérance)
        - Tolérance = REGLES_FREQUENCES[clé]['attention'] - 1.0 (si présente), sinon 0
        - La projection des métadonnées est conservée à l'identique (pas de **meta)
        """

        maintenant = self._now()
        liste_jdds: List[Dict[str, Any]] = []

        # ---------------- Helpers locaux ----------------


        def _formater_date_lisible(dt: Optional[datetime]) -> Optional[str]:
            """
            Retourne une date formatée proprement sous la forme 'JJ/MM/AAAA HH:MM'.
            Si dt est None → retourne None.
            Si dt est naïve et self._tz existe → attache le fuseau horaire de l'application.
            """
            if not dt:
                return None

            # Attache la TZ si datetime naïve
            if dt.tzinfo is None and getattr(self, "_tz", None):
                dt = dt.replace(tzinfo=self._tz)

            # Convertit vers la timezone applicative
            if getattr(self, "_tz", None):
                dt = dt.astimezone(self._tz)

            return dt.strftime("%d/%m/%Y %H:%M")

        def _parse_iso(dt_str: Optional[str]) -> Optional[datetime]:
            if not dt_str or not isinstance(dt_str, str):
                return None
            s = dt_str.strip()
            if s.endswith("Z"):
                s = s[:-1] + "+00:00"
            try:
                dt = datetime.fromisoformat(s)
                if dt.tzinfo is None and getattr(self, "_tz", None) is not None:
                    dt = dt.replace(tzinfo=self._tz)
                return dt
            except Exception:
                return None

        def _delta_en_j_h_m(td: Optional[timedelta]) -> Dict[str, Optional[int]]:
            if td is None:
                return {"jours": None, "heures": None, "minutes": None}
            total_minutes = int(td.total_seconds() // 60)
            jrs = total_minutes // (24 * 60)
            hrs = (total_minutes % (24 * 60)) // 60
            mins = total_minutes % 60
            return {"jours": jrs, "heures": hrs, "minutes": mins}

        # -------- PROJECTION INLINE (allègement) ----------
        jdds_min: List[Dict[str, Any]] = []
        for j in jdds:
            id_jdd = j.id_jdd_odre
            nom_jdd = j.nom_jdd_odre
            meta = j.metadonnees
            ressources = j.ressources
            ressources_pda_dict = j.pda_opendata or {}

            # projection minimale des ressources pertinentes
            res_min = []
            for r in ressources:
                if not isinstance(r, dict):
                    continue
                res_min.append({
                    "uid_ressource": r.get("uid"),
                    "title": r.get("title"),
                    "updated_at": r.get("updated_at", r.get("update_at")),
                    "origin_type": r.get("origin_type"),
                    "enabled": r.get("enabled", True),
                })
            
            
            # 1) Extraction correcte du flag
            flag_has_pda = False

            if "has_sources_externes_pda_opendata_monitoring_bool" in ressources_pda_dict:
                flag_has_pda = bool(ressources_pda_dict["has_sources_externes_pda_opendata_monitoring_bool"])


            # 2) Construction du résultat
            if flag_has_pda:
                res_pda = {
                    "Elements": "Oui",
                    "Name": ressources_pda_dict.get("name", ressources_pda_dict.get("Name", "")),
                    "Size": ressources_pda_dict.get("size", ressources_pda_dict.get("Size", "")),
                    "LastModified": ressources_pda_dict.get("lastmodified", ressources_pda_dict.get("LastModified", "")),
                    "BoolIsDeleted": ressources_pda_dict.get("boolisdeleted", ressources_pda_dict.get("BoolIsDeleted", "")),
                    "ContentType": ressources_pda_dict.get("contenttype", ressources_pda_dict.get("ContentType", "")),
                    "StorageAccountName": ressources_pda_dict.get("storageaccountname", ressources_pda_dict.get("StorageAccountName", "")),
                    "StorageContainerName": ressources_pda_dict.get("storagecontainername", ressources_pda_dict.get("StorageContainerName", "")),
                    "FullName": ressources_pda_dict.get("FullName", ""),
                    "pda_dispo" : "Oui"
                }
            else:
                res_pda = {
                    "Elements": "Non",
                    "Name": "",
                    "Size": "",
                    "LastModified": "",
                    "BoolIsDeleted": "",
                    "ContentType": "",
                    "StorageAccountName": "",
                    "StorageContainerName": "",
                    "FullName": "",
                    "pda_dispo" : "Non"
                }

            # Ajout par boucle d'itération
            jdds_min.append({
                "id_jdd_odre": id_jdd,
                "nom_jdd_odre": nom_jdd,

                "metadonnees": {
                    # Identifiants
                    "uid": meta.get("uid"),
                    "created_at": meta.get("created_at"),

                    # Valeurs par défaut / description
                    "metadata_default_title_value": meta.get("metadata_default_title_value"),
                    "metadata_dcat_accrualperiodicity_value": meta.get("metadata_dcat_accrualperiodicity_value"),
                    "metadata_default_description_value": meta.get("metadata_default_description_value"),
                    "metadata_default_publisher_value": meta.get("metadata_default_publisher_value"),

                    # Contact / DCAT
                    "metadata_dcat_accrualperiodicity_value": meta.get("metadata_dcat_accrualperiodicity_value"),
                    "metadata_dcat_contact_name_value": meta.get("metadata_dcat_contact_name_value"),
                    "metadata_dcat_contact_email_value": meta.get("metadata_dcat_contact_email_value"),

                    # Administration / Gouvernance
                    "metadata_admin_source_de_la_donnee_value": meta.get("metadata_admin_source_de_la_donnee_value"),
                    "metadata_admin_gestionnaire_technique_de_la_donnee_value": meta.get("metadata_admin_gestionnaire_technique_de_la_donnee_value"),
                    "metadata_admin_gestionnaire_metier_de_la_donnee_value": meta.get("metadata_admin_gestionnaire_metier_de_la_donnee_value"),
                    "metadata_admin_direction_metier_concernee_value": meta.get("metadata_admin_direction_metier_concernee_value"),
                    "metadata_admin_type_de_source_de_donnees_value": meta.get("metadata_admin_type_de_source_de_donnees_value"),
                    "metadata_admin_sla_value": meta.get("metadata_admin_sla_value"),
                    "metadata_admin_enjeux_value": meta.get("metadata_admin_enjeux_value"),

                    # Restrictions
                    "is_restricted": meta.get("is_restricted"),
                },

                "ressources": res_min,

                "ressources_pda_opendata": res_pda
            })
        # ---------------------------------------------------
        def analyse_fines_sur_1_jdd(val_date_creation:str,
                                    val_freq:str,
            ) -> Dict[str, Any]:
            """
            """
            try:
                valeur_freq_meta = val_freq
                TYPE_FREQUENCE_EN_FR = Configurations.TYPE_FREQUENCE_EN_FR
                # Si valeur manquante → valeur par défaut
                if valeur_freq_meta is None:
                    clef_frequence = "-- Aucune --"
                else:
                    # Normalisation de la valeur
                    valeur_norm = str(valeur_freq_meta).strip().lower()
                    # Conversion via dict
                    clef_frequence = TYPE_FREQUENCE_EN_FR.get(valeur_norm)

                # 2) Période & tolérance
                periode, tolerance = self._periode_et_tolerance_depuis_config(clef_frequence)

                # 4) Création / âge
                date_creation = val_date_creation
                dt_creation = (
                    _parse_iso(date_creation)
                    if isinstance(date_creation, str)
                    else (date_creation if isinstance(date_creation, datetime) else None)
                )
                age_jours = (maintenant.date() - dt_creation.date()).days if dt_creation else None

                dico_retour= {"clef_frequence":clef_frequence,
                                "periode_jours": int(periode.total_seconds() // 86400) if isinstance(periode, timedelta) else 0,
                                "tolerance_ratio": float(tolerance),
                                "age_jdd_jours": age_jours,
                }       
                return dico_retour
            
            except Exception as e:
                st.error(f"Erreur sur l'analyse fine: e")
                return {}

        # --------- Analyse fine ----------
        for j in jdds_min:
            # Prise des paramètres:
            meta: Dict[str, Any] = j.get("metadonnees") or {}
            ressources: List[Dict[str, Any]] = j.get("ressources") or []
            pda : Dict[str, Any] = j.get('ressources_pda_opendata') or {}
            
            date_creation = meta.get("created_at")
            valeur_freq_meta = meta.get("metadata_dcat_accrualperiodicity_value")

            dates_upd: List[datetime] = []
            if len(ressources) > 0:
                for r in ressources:
                    update_ressource = r.get("updated_at")

                    # Retour de l'analyse fine :
                    dict_analyse_fine = analyse_fines_sur_1_jdd(val_date_creation=date_creation,
                                                                val_freq=valeur_freq_meta
                    )
                    periode = dict_analyse_fine.get("periode_jours")
                    tolerance = dict_analyse_fine.get("tolerance_ratio")

                    # MAJ des ressources ACTIVES uniquement
                    nb_ress_non_a_jour = 0
                    delai_ok = periode * (1.0 + max(0.0, tolerance))
                    upd = _parse_iso(update_ressource)

                    if upd is not None:
                        dates_upd.append(upd)
                        if (maintenant - upd) > delai_ok:
                            nb_ress_non_a_jour += 1
                    else:
                        nb_ress_non_a_jour += 1

                    res_derniere_maj = upd if upd else None
                    res_delta_maj = (maintenant - res_derniere_maj) if res_derniere_maj else None
                    res_est_a_jour = (res_delta_maj is not None) and (res_delta_maj <= delai_ok)
                    res_prochaine = (res_derniere_maj + periode) if res_derniere_maj else None

                    def _none_delta():
                        return {"jours": None, "heures": None, "minutes": None}

                    res_delta_fmt = _delta_en_j_h_m(res_derniere_maj)
                    res_a_jour_depuis = res_delta_fmt if res_est_a_jour else _none_delta()
                    res_pas_a_jour_depuis = res_delta_fmt if not res_est_a_jour else _none_delta()

                    # Petite étape de normalisation des dates de mise à jour
                    res_derniere_maj_lisible = _formater_date_lisible(dt=res_derniere_maj)
                    res_prochaine_maj_lisible = _formater_date_lisible(dt=res_prochaine)

                    # Ajout des ressource dans la liste final d'un jdd
                    liste_jdds.append({
                        # Ressources / Quelques colonnes 
                        # Champs principaux
                        "res_uid_metadata": r.get("uid_metadata"),
                        "res_uid": r.get("uid"),
                        "res_title": r.get("title"),
                        "res_type": r.get("type"),
                        "res_updated_at": r.get("res_updated_at"),
                        "res_display_name": r.get("display_name"),

                        # Champs datasource
                        "res_datasource_file_uid": r.get("datasource_file_uid"),
                        "res_datasource_type": r.get("datasource_type"),

                        # Champs params
                        "res_params_doublequote": r.get("params_doublequote"),
                        "res_params_encoding": r.get("params_encoding"),
                        "res_params_first_row_no": r.get("params_first_row_no"),
                        "res_params_headers_first_row": r.get("params_headers_first_row"),
                        "res_params_separator": r.get("params_separator"),

                        # Champs origin
                        "res_origin_label": r.get("origin_label"),
                        "res_origin_type": r.get("origin_type"),

                        # Champs extraction_infos
                        "res_extraction_infos_label": r.get("extraction_infos_label"),
                        "res_extraction_infos_type": r.get("extraction_infos_type"),

                        # Analyse fine des ressource 
                        "res_periode_jours": int(periode.total_seconds() // 86400) if isinstance(periode, timedelta) else 0,
                        "res_tolerance_ratio": float(tolerance),
                        "res_statut": "à jour" if res_est_a_jour else "pas à jour",
                        "res_derniere_mise_a_jour": res_derniere_maj_lisible,
                        "res_prochaine_mise_a_jour": res_prochaine_maj_lisible,
                        "res_a_jour_depuis": res_a_jour_depuis,
                        "res_pas_a_jour_depuis": res_pas_a_jour_depuis,
                    })
                
                # Analyse sur l'ensemble des ressources lève l'alerte si au moins une ressource tombe: 
                derniere_maj = max(dates_upd) if dates_upd else None
                delta_maj = (maintenant - derniere_maj) if derniere_maj else None
                est_a_jour = (delta_maj is not None) and (delta_maj <= delai_ok)
                prochaine = (derniere_maj + periode) if derniere_maj else None
                
                def _none_delta():
                    return {"jours": None, "heures": None, "minutes": None}

                delta_fmt = _delta_en_j_h_m(delta_maj)
                a_jour_depuis = delta_fmt if est_a_jour else _none_delta()
                pas_a_jour_depuis = delta_fmt if not est_a_jour else _none_delta()

                # Petite étape de normalisation des dates de mise à jour
                derniere_maj_lisible = _formater_date_lisible(dt=derniere_maj)
                prochaine_maj_lisible = _formater_date_lisible(dt=prochaine)
                
            elif pda["pda_dispo"] == "Oui":
                update_ressource = pda["LastModified"]
                nb_ress_non_a_jour = 0

                # Retour de l'analyse fine :
                dict_analyse_fine = analyse_fines_sur_1_jdd(val_date_creation=date_creation,
                                                            val_freq=valeur_freq_meta
                )
                periode = dict_analyse_fine.get("periode_jours")
                tolerance = dict_analyse_fine.get("tolerance_ratio")
                delai_ok = periode * (1.0 + max(0.0, tolerance))
                upd = _parse_iso(update_ressource)

                if upd is not None:
                    if (maintenant - upd) > delai_ok:
                        nb_ress_non_a_jour += 1

                pda_derniere_maj = upd if upd else None
                pda_delta_maj = (maintenant - pda_derniere_maj) if pda_derniere_maj else None
                pda_est_a_jour = (pda_delta_maj is not None) and (pda_delta_maj <= delai_ok)
                pda_prochaine = (pda_derniere_maj + periode) if pda_derniere_maj else None

                def _none_delta():
                    return {"jours": None, "heures": None, "minutes": None}

                pda_delta_fmt = _delta_en_j_h_m(pda_derniere_maj)
                pda_a_jour_depuis = pda_delta_fmt if pda_est_a_jour else _none_delta()
                pda_pas_a_jour_depuis = pda_delta_fmt if not pda_est_a_jour else _none_delta()

                # Petite étape de normalisation des dates de mise à jour
                pda_derniere_maj_lisible = _formater_date_lisible(dt=pda_derniere_maj)
                pda_prochaine_maj_lisible = _formater_date_lisible(dt=pda_prochaine)

                # Ajout spécifique de ressource de type pda dans un jdd
                liste_jdds.append({
                    # Propore à la ressource pda
                    "Name": pda.get("name"),
                    "Size": pda.get("size"),
                    "LastModified": pda.get("lastmodified"),
                    "BoolIsDeleted": pda.get("boolisdeleted"),
                    "ContentType": pda.get("contenttype"),
                    "StorageAccountName": pda.get("storageaccountname"),
                    "StorageContainerName": pda.get("storagecontainername"),
                    "FullName": pda.get("FullName", ""),
                    "pda_dispo" : "Oui",

                    # Analyse fine sur le type de ressource pda
                        "pda_tolerance_ratio": float(tolerance),
                        "pda_statut": "à jour" if pda_est_a_jour else "pas à jour",
                        "pda_derniere_mise_a_jour": pda_derniere_maj_lisible,
                        "pda_prochaine_mise_a_jour": pda_prochaine_maj_lisible,
                        "pda_a_jour_depuis": pda_a_jour_depuis,
                        "pda_pas_a_jour_depuis": pda_pas_a_jour_depuis,
                })


                # == Analyse sur le jeu de donnée qui a une ressource pda: == #
                derniere_maj = max(dates_upd) if dates_upd else None
                delta_maj = (maintenant - derniere_maj) if derniere_maj else None
                est_a_jour = (delta_maj is not None) and (delta_maj <= delai_ok)
                prochaine = (derniere_maj + periode) if derniere_maj else None
                
                def _none_delta():
                    return {"jours": None, "heures": None, "minutes": None}

                delta_fmt = _delta_en_j_h_m(delta_maj)
                a_jour_depuis = delta_fmt if est_a_jour else _none_delta()
                pas_a_jour_depuis = delta_fmt if not est_a_jour else _none_delta()

                # Petite étape de normalisation des dates de mise à jour
                derniere_maj_lisible = _formater_date_lisible(dt=derniere_maj)
                prochaine_maj_lisible = _formater_date_lisible(dt=prochaine)


            # 6) item final (on garde la projection des métadonnées telle quelle)
            liste_jdds.append({
                # Identifiants
                "id_jdd_odre": j.get("id_jdd_odre"),
                "nom_jdd_odre": j.get("nom_jdd_odre"),

                # Valeurs par défaut / description
                "metadata_default_title_value": meta.get("metadata_default_title_value"),
                "metadata_default_description_value": meta.get("metadata_default_description_value"),
                "metadata_default_publisher_value": meta.get("metadata_default_publisher_value"),

                # Contact / DCAT
                "metadata_dcat_accrualperiodicity_value": dict_analyse_fine.get("clef_frequence"),
                "metadata_dcat_contact_name_value": meta.get("metadata_dcat_contact_name_value"),
                "metadata_dcat_contact_email_value": meta.get("metadata_dcat_contact_email_value"),

                # Administration / Gouvernance
                "metadata_admin_source_de_la_donnee_value": meta.get("metadata_admin_source_de_la_donnee_value"),
                "metadata_admin_gestionnaire_technique_de_la_donnee_value": meta.get("metadata_admin_gestionnaire_technique_de_la_donnee_value"),
                "metadata_admin_gestionnaire_metier_de_la_donnee_value": meta.get("metadata_admin_gestionnaire_metier_de_la_donnee_value"),
                "metadata_admin_direction_metier_concernee_value": meta.get("metadata_admin_direction_metier_concernee_value"),
                "metadata_admin_type_de_source_de_donnees_value": meta.get("metadata_admin_type_de_source_de_donnees_value"),
                "metadata_admin_sla_value": meta.get("metadata_admin_sla_value"),
                "metadata_admin_enjeux_value": meta.get("metadata_admin_enjeux_value"),

                # Identifiants / restrictions issus des meta
                "uid": meta.get("uid"),
                "created_at": dict_analyse_fine.get("dt_creation_lisible"),
                "is_restricted": meta.get("is_restricted"),


                # Analyse
                "clef_frequence": dict_analyse_fine.get("clef_frequence"),
                "periode_jours": dict_analyse_fine.get("periode_jours") ,
                "tolerance_ratio": dict_analyse_fine.get("tolerance_ratio") ,

                "statut": "à jour" if est_a_jour else "pas à jour",
                "derniere_mise_a_jour": derniere_maj_lisible ,
                "prochaine_mise_a_jour": prochaine_maj_lisible ,
                "a_jour_depuis": a_jour_depuis ,
                "pas_a_jour_depuis": pas_a_jour_depuis,

                "age_jdd_jours": dict_analyse_fine.get("age_jdd_jours") ,

                "ressources_total": len(ressources) ,
                "ressources_non_a_jour":  nb_ress_non_a_jour
            })

        df: pd.DataFrame = self._vers_dataframe(items=liste_jdds)
        return {"items": liste_jdds, "df": df}






    def analyser_liste(
        self,
        jdds: List[JddOdre],
    ) -> Dict[str, Any]:
        """
        Retourne:
        - items : liste (1 ligne / JDD) prête pour l'UI (KPI, Top)
        - df    : DataFrame correspondant à items
        - df_ressources : DataFrame (1 ligne / ressource standard) pour le bloc "Détails"
        """

        maintenant = self._now()

        # -------- Helpers --------
        def _enabled_truthy(v: Any) -> bool:
            if v is True:
                return True
            if v in (False, 0, None, ""):
                return False
            s = str(v).strip().lower()
            return s not in {"false", "0", "no", "non", "off"}

        def _formater_date_lisible(dt: Optional[datetime]) -> Optional[str]:
            if not dt:
                return None
            if dt.tzinfo is None and getattr(self, "_tz", None):
                dt = dt.replace(tzinfo=self._tz)
            if getattr(self, "_tz", None):
                dt = dt.astimezone(self._tz)
            return dt.strftime("%d/%m/%Y %H:%M")

        def _parse_iso(dt_str: Optional[str]) -> Optional[datetime]:
            if not dt_str or not isinstance(dt_str, str):
                return None
            s = dt_str.strip()
            if s.endswith("Z"):
                s = s[:-1] + "+00:00"
            try:
                dt = datetime.fromisoformat(s)
                if dt.tzinfo is None and getattr(self, "_tz", None) is not None:
                    dt = dt.replace(tzinfo=self._tz)
                return dt
            except Exception:
                return None

        def _delta_en_j_h_m(td: Optional[timedelta]) -> Dict[str, Optional[int]]:
            if td is None:
                return {"jours": None, "heures": None, "minutes": None}
            total_minutes = int(td.total_seconds() // 60)
            jrs = total_minutes // (24 * 60)
            hrs = (total_minutes % (24 * 60)) // 60
            mins = total_minutes % 60
            return {"jours": jrs, "heures": hrs, "minutes": mins}

        def _periode_et_seuils(valeur_freq_meta: Optional[str]) -> Dict[str, Any]:
            """
            Construit:
            - clef_frequence  (clé normalisée telle que lue dans Configurations)
            - periode_td      (timedelta)
            - facteur_attention, facteur_critique (float)
            - seuil_attention_td, seuil_critique_td (timedelta)
            - tolerance (= facteur_attention - 1.0)  [compat historique]
            """
            tf = getattr(Configurations, "TYPE_FREQUENCE", {})
            rf = getattr(Configurations, "REGLES_FREQUENCES", {})

            if valeur_freq_meta is None:
                clef = None
            else:
                # on essaie la valeur brute d'abord
                clef = valeur_freq_meta if valeur_freq_meta in tf else str(valeur_freq_meta).strip()

            # période
            periode = tf.get(clef, timedelta(0))  # None -> timedelta(0) comme tu le fais
            if periode is None:
                periode = timedelta(0)

            # règles
            regle = rf.get(clef, {"attention": 1.0, "critique": 1.5})
            facteur_attention = float(regle.get("attention", 1.0))
            facteur_critique  = float(regle.get("critique", 1.5))

            seuil_attention_td = periode * facteur_attention
            seuil_critique_td  = periode * facteur_critique
            tolerance = max(0.0, facteur_attention - 1.0)  # compat historique

            return {
                "clef_frequence": clef,
                "periode_td": periode,
                "facteur_attention": facteur_attention,
                "facteur_critique": facteur_critique,
                "seuil_attention_td": seuil_attention_td,
                "seuil_critique_td":  seuil_critique_td,
                "tolerance": tolerance,
            }

        # -------- Projection & Analyse --------
        items_jdd: List[Dict[str, Any]] = []   # 1 ligne / JDD
        items_res: List[Dict[str, Any]] = []   # 1 ligne / ressource standard

        for j in jdds:
            # === Métadonnées JDD ===
            id_jdd = j.id_jdd_odre
            nom_jdd = j.nom_jdd_odre or ""
            meta = j.metadonnees or {}
            ressources_src = j.ressources or []
            pda = j.pda_opendata or {}

            # Date de création / âge
            raw_created = meta.get("created_at")
            dt_creation = _parse_iso(raw_created) if isinstance(raw_created, str) else (raw_created if isinstance(raw_created, datetime) else None)
            age_jours = (maintenant.date() - dt_creation.date()).days if dt_creation else None
            dt_creation_lisible = _formater_date_lisible(dt_creation)

            # Fréquence
            valeur_freq_meta = meta.get("metadata_dcat_accrualperiodicity_value")
            freq_info = _periode_et_seuils(valeur_freq_meta)
            periode_td: timedelta          = freq_info["periode_td"] or timedelta(0)
            seuil_attention_td: timedelta  = freq_info["seuil_attention_td"] or timedelta(0)
            # NB: tu as aussi freq_info["seuil_critique_td"] dispo

            # === Projection des ressources standards ===
            res_min: List[Dict[str, Any]] = []
            for r in ressources_src:
                if not isinstance(r, dict):
                    continue
                # Crée toutes les clés dont tu auras besoin en aval (avec valeurs par défaut)
                res_min.append({
                    # Principaux
                    "uid": r.get("uid"),
                    "uid_metadata": r.get("uid_metadata"),
                    "title": r.get("title"),
                    "display_name": r.get("display_name"),   # ajouté
                    "type": r.get("type"),                   # ajouté
                    "updated_at": r.get("updated_at", r.get("update_at")),
                    "origin_type": r.get("origin_type"),
                    "enabled": r.get("enabled", True),

                    # Datasource
                    "datasource_file_uid": r.get("datasource_file_uid"),
                    "datasource_type": r.get("datasource_type"),

                    # Params (au cas où)
                    "params_doublequote": r.get("params_doublequote"),
                    "params_encoding": r.get("params_encoding"),
                    "params_first_row_no": r.get("params_first_row_no"),
                    "params_headers_first_row": r.get("params_headers_first_row"),
                    "params_separator": r.get("params_separator"),

                    # Origin / extraction infos
                    "origin_label": r.get("origin_label"),
                    "extraction_infos_label": r.get("extraction_infos_label"),
                    "extraction_infos_type": r.get("extraction_infos_type"),
                })

            # === Projection/flag PDA ===
            flag_has_pda = bool(pda.get("has_sources_externes_pda_opendata_monitoring_bool"))
            pda_last_modified = pda.get("lastmodified", pda.get("LastModified"))
            pda_dt = _parse_iso(pda_last_modified) if pda_last_modified else None

            # === Analyse des ressources (actives) ===
            ressources_actives = res_min
            dates_upd: List[datetime] = []
            nb_ress_non_a_jour = 0
            by_type: Dict[str, int] = {}

            for r in ressources_actives:
                ori = (r.get("origin_type") or "").strip().lower()
                by_type[ori] = by_type.get(ori, 0) + 1

                upd = _parse_iso(r.get("updated_at"))
                if upd is not None:
                    dates_upd.append(upd)
                    if periode_td > timedelta(0) and (maintenant - upd) > seuil_attention_td:
                        nb_ress_non_a_jour += 1
                else:
                    nb_ress_non_a_jour += 1

                # Détail ressource (items_res) — valeurs lisibles
                res_derniere_maj = upd
                res_delta = (maintenant - res_derniere_maj) if res_derniere_maj else None
                res_est_a_jour = (res_delta is not None) and (res_delta <= seuil_attention_td) if periode_td > timedelta(0) else True
                res_prochaine = (res_derniere_maj + periode_td) if res_derniere_maj and periode_td > timedelta(0) else None

                items_res.append({
                    "id_jdd_odre": id_jdd,
                    "nom_jdd_odre": nom_jdd,
                    "res_uid": r.get("uid"),
                    "res_uid_metadata": r.get("uid_metadata"),
                    "res_title": r.get("title"),
                    "res_display_name": r.get("display_name"),
                    "res_type": r.get("type"),
                    "res_origin_type": r.get("origin_type"),
                    "res_updated_at": _formater_date_lisible(res_derniere_maj),
                    "res_statut": "à jour" if res_est_a_jour else "pas à jour",
                    "res_a_jour_depuis": _delta_en_j_h_m(res_delta if res_est_a_jour else None),
                    "res_pas_a_jour_depuis": _delta_en_j_h_m(res_delta if not res_est_a_jour else None),
                    "res_prochaine_mise_a_jour": _formater_date_lisible(res_prochaine),

                    # Datasource / params (si utiles pour l’UI)
                    "res_datasource_file_uid": r.get("datasource_file_uid"),
                    "res_datasource_type": r.get("datasource_type"),
                    "res_params_doublequote": r.get("params_doublequote"),
                    "res_params_encoding": r.get("params_encoding"),
                    "res_params_first_row_no": r.get("params_first_row_no"),
                    "res_params_headers_first_row": r.get("params_headers_first_row"),
                    "res_params_separator": r.get("params_separator"),
                    "res_origin_label": r.get("origin_label"),
                    "res_extraction_infos_label": r.get("extraction_infos_label"),
                    "res_extraction_infos_type": r.get("extraction_infos_type"),
                })

            # === Statut JDD (2 scénarios) ===
            if ressources_actives:
                derniere_maj = max(dates_upd) if dates_upd else None
            elif flag_has_pda and pda_dt:
                derniere_maj = pda_dt
            else:
                derniere_maj = None

            if derniere_maj:
                delta = maintenant - derniere_maj
                est_a_jour = (periode_td == timedelta(0)) or (delta <= seuil_attention_td)
                prochaine = derniere_maj + periode_td if periode_td > timedelta(0) else None
            else:
                delta = None
                est_a_jour = False
                prochaine = None

            # Dérivés lisibles + tri
            derniere_maj_lisible = _formater_date_lisible(derniere_maj)
            prochaine_maj_lisible = _formater_date_lisible(prochaine)
            a_jour_depuis = _delta_en_j_h_m(delta if est_a_jour else None)
            pas_a_jour_depuis = _delta_en_j_h_m(delta if not est_a_jour else None)
            depuis_min = int(delta.total_seconds() // 60) if delta else 0

            # === Synthèse JDD ===
            items_jdd.append({
                "id_jdd_odre": id_jdd,
                "nom_jdd_odre": nom_jdd,

                # Métas essentielles
                "uid": meta.get("uid"),
                "created_at": dt_creation_lisible,
                "metadata_default_title_value": meta.get("metadata_default_title_value"),
                "metadata_default_description_value": meta.get("metadata_default_description_value"),
                "metadata_default_publisher_value": meta.get("metadata_default_publisher_value"),
                "metadata_dcat_accrualperiodicity_value": freq_info["clef_frequence"],
                "is_restricted": meta.get("is_restricted"),

                # PDA
                "pda_dispo": "Oui" if flag_has_pda else "Non",
                "pda_last_modified": _formater_date_lisible(pda_dt),

                # Ressources agrégées
                "ressources_total": len(ressources_actives),
                "ressources_non_a_jour": nb_ress_non_a_jour,
                "ressources_par_type": by_type,

                # Seuils & période (exposés pour UI)
                "periode_jours": int((periode_td.total_seconds() // 86400) if isinstance(periode_td, timedelta) else 0),
                "facteur_attention": freq_info["facteur_attention"],
                "facteur_critique": freq_info["facteur_critique"],

                # Analyse globale JDD
                "statut": "à jour" if est_a_jour else "pas à jour",
                "derniere_mise_a_jour": derniere_maj_lisible,
                "prochaine_mise_a_jour": prochaine_maj_lisible,
                "a_jour_depuis": a_jour_depuis,
                "pas_a_jour_depuis": pas_a_jour_depuis,
                "depuis_min": depuis_min,  # pratique pour trier ton TOP
                "age_jdd_jours": age_jours,
            })

        # DataFrames de sortie
        df_jdd: pd.DataFrame = self._vers_dataframe(items=items_jdd)
        df_res: pd.DataFrame = pd.DataFrame(items_res) if items_res else pd.DataFrame()

        return {"items": items_jdd, "df": df_jdd, "df_ressources": df_res}




    # ----------------- MÉTHODES PRIVÉES (helpers) -----------------

    def _periode_et_tolerance_depuis_config(
        self,
        clef_frequence: str,
    ) -> Tuple[timedelta, float]:
        """
        Détermine (période, tolérance) à partir des Configurations.
        - Si TYPE_FREQUENCE[clé] est None → période = timedelta(0), tolérance = 0
        - Si clé inconnue → période = timedelta(0), tolérance = 0
        """

        tf = getattr(Configurations, "TYPE_FREQUENCE", {})
        rf = getattr(Configurations, "REGLES_FREQUENCES", {})

        # 1) Si absence de clé → période nulle, tolérance nulle
        if clef_frequence not in tf:
            return timedelta(0), 0.0

        # 2) Période depuis TYPE_FREQUENCE
        periode = tf.get(clef_frequence)

        # Cas des périodes "non définies" (None dans le config)
        if periode is None:
            return timedelta(0), 0.0

        # 3) Tolérance depuis REGLES_FREQUENCES
        regle = rf.get(clef_frequence, {"attention": 1.0})
        # attention = facteur du type 1.0, 1.5, etc.
        facteur_attention = regle.get("attention", 1.0)

        # → tolérance réelle (ex : attention=1.5 → tolérance=0.5)
        tolerance = max(0.0, facteur_attention - 1.0)

        return periode, tolerance

    def _vers_dataframe_v1(self, items: List[Dict[str, Any]]) -> pd.DataFrame:
        """
        Produit un DataFrame plat (une ligne par JDD) en respectant EXACTEMENT
        la projection des métadonnées réalisée dans `analyser_liste()`.

        - Inclut tous les champs projetés depuis `meta` (noms inchangés)
        - Inclut les champs d'analyse (fréquence, statut, dates, deltas, ressources)
        - Aucune KeyError (utilisation de .get et valeurs None par défaut)
        """
        
        lignes: List[Dict[str, Any]] = []

        for it in items:
            aj = it.get("a_jour_depuis", {}) or {}
            paj = it.get("pas_a_jour_depuis", {}) or {}

            lignes.append({
                # Identifiants JDD
                "id_jdd_odre": it.get("id_jdd_odre"),
                "nom_jdd_odre": it.get("nom_jdd_odre"),

                # Métadonnées (projection inchangée)
                "uid": it.get("uid"),
                "created_at": it.get("created_at"),
                "is_restricted": it.get("is_restricted"),

                "metadata_default_title_value": it.get("metadata_default_title_value"),
                "metadata_dcat_accrualperiodicity_value": it.get("metadata_dcat_accrualperiodicity_value"),
                "metadata_default_description_value": it.get("metadata_default_description_value"),
                "metadata_default_publisher_value": it.get("metadata_default_publisher_value"),

                "metadata_dcat_accrualperiodicity_value": it.get("metadata_dcat_accrualperiodicity_value"),
                "metadata_dcat_contact_name_value": it.get("metadata_dcat_contact_name_value"),
                "metadata_dcat_contact_email_value": it.get("metadata_dcat_contact_email_value"),

                "metadata_admin_source_de_la_donnee_value": it.get("metadata_admin_source_de_la_donnee_value"),
                "metadata_admin_gestionnaire_technique_de_la_donnee_value": it.get("metadata_admin_gestionnaire_technique_de_la_donnee_value"),
                "metadata_admin_gestionnaire_metier_de_la_donnee_value": it.get("metadata_admin_gestionnaire_metier_de_la_donnee_value"),
                "metadata_admin_direction_metier_concernee_value": it.get("metadata_admin_direction_metier_concernee_value"),
                "metadata_admin_type_de_source_de_donnees_value": it.get("metadata_admin_type_de_source_de_donnees_value"),
                "metadata_admin_sla_value": it.get("metadata_admin_sla_value"),
                "metadata_admin_enjeux_value": it.get("metadata_admin_enjeux_value"),

                # Ressources

                # Ressource pda


                # Analyse
                "clef_frequence": it.get("clef_frequence"),
                "periode_jours": it.get("periode_jours"),
                "tolerance_ratio": it.get("tolerance_ratio"),
                "statut": it.get("statut"),
                "derniere_mise_a_jour": it.get("derniere_mise_a_jour"),
                "prochaine_mise_a_jour": it.get("prochaine_mise_a_jour"),

                # Deltas (formatés)
                "a_jour_depuis_j": aj.get("jours"),
                "a_jour_depuis_h": aj.get("heures"),
                "a_jour_depuis_m": aj.get("minutes"),
                "pas_a_jour_depuis_j": paj.get("jours"),
                "pas_a_jour_depuis_h": paj.get("heures"),
                "pas_a_jour_depuis_m": paj.get("minutes"),

                # Age & Ressources
                "age_jdd_jours": it.get("age_jdd_jours"),
                "ressources_total": it.get("ressources_total"),
                "ressources_non_a_jour": it.get("ressources_non_a_jour"),
            })
        
        df = pd.DataFrame(lignes)


        df["metadata_dcat_accrualperiodicity_value"] = df["metadata_dcat_accrualperiodicity_value"].apply(
            lambda x: Configurations.TYPE_FREQUENCE_EN_FR.get(
                str(x).strip().lower() if x is None else "-- Aucun(e) --",
            )
        )

        return pd.DataFrame(lignes)



    def _vers_dataframe(self, items: List[Dict[str, Any]]) -> pd.DataFrame:
        """
        Produit un DataFrame plat (une ligne par JDD) en respectant EXACTEMENT
        la projection réalisée dans `analyser_liste()`.

        - Inclus les champs méta projetés (noms inchangés)
        - Inclus les champs d'analyse (fréquence, statut, dates, deltas, ressources)
        - Pas de KeyError (get + valeurs None par défaut)
        - Normalise la fréquence pour coller à Configurations.TYPE_FREQUENCE
        - (Optionnel) ajoute un libellé lisible 'frequence_libelle' si TYPE_FREQUENCE_EN_FR est dispo
        """
        import pandas as pd

        lignes: List[Dict[str, Any]] = []

        for it in items:
            aj = it.get("a_jour_depuis") or {}
            paj = it.get("pas_a_jour_depuis") or {}

            lignes.append({
                # Identifiants JDD
                "id_jdd_odre": it.get("id_jdd_odre"),
                "nom_jdd_odre": it.get("nom_jdd_odre"),

                # Métadonnées essentielles
                "uid": it.get("uid"),
                "created_at": it.get("created_at"),
                "is_restricted": it.get("is_restricted"),

                "metadata_default_title_value": it.get("metadata_default_title_value"),
                "metadata_default_description_value": it.get("metadata_default_description_value"),
                "metadata_default_publisher_value": it.get("metadata_default_publisher_value"),
                "metadata_dcat_accrualperiodicity_value": it.get("metadata_dcat_accrualperiodicity_value"),
                "metadata_dcat_contact_name_value": it.get("metadata_dcat_contact_name_value"),
                "metadata_dcat_contact_email_value": it.get("metadata_dcat_contact_email_value"),

                "metadata_admin_source_de_la_donnee_value": it.get("metadata_admin_source_de_la_donnee_value"),
                "metadata_admin_gestionnaire_technique_de_la_donnee_value": it.get("metadata_admin_gestionnaire_technique_de_la_donnee_value"),
                "metadata_admin_gestionnaire_metier_de_la_donnee_value": it.get("metadata_admin_gestionnaire_metier_de_la_donnee_value"),
                "metadata_admin_direction_metier_concernee_value": it.get("metadata_admin_direction_metier_concernee_value"),
                "metadata_admin_type_de_source_de_donnees_value": it.get("metadata_admin_type_de_source_de_donnees_value"),
                "metadata_admin_sla_value": it.get("metadata_admin_sla_value"),
                "metadata_admin_enjeux_value": it.get("metadata_admin_enjeux_value"),

                # PDA (si présents dans items)
                "pda_dispo": it.get("pda_dispo"),
                "pda_last_modified": it.get("pda_last_modified"),

                # Agrégats ressources (issus d'analyser_liste)
                "ressources_total": it.get("ressources_total"),
                "ressources_non_a_jour": it.get("ressources_non_a_jour"),
                "ressources_par_type": it.get("ressources_par_type"),  # dict

                # Analyse / fréquence / seuils
                "clef_frequence": it.get("clef_frequence"),
                "periode_jours": it.get("periode_jours"),
                "tolerance_ratio": it.get("tolerance_ratio", it.get("facteur_attention", None)),  # compat
                "facteur_attention": it.get("facteur_attention"),
                "facteur_critique": it.get("facteur_critique"),

                "statut": it.get("statut"),
                "derniere_mise_a_jour": it.get("derniere_mise_a_jour"),
                "prochaine_mise_a_jour": it.get("prochaine_mise_a_jour"),

                # Deltas (formatés)
                "a_jour_depuis_j": aj.get("jours"),
                "a_jour_depuis_h": aj.get("heures"),
                "a_jour_depuis_m": aj.get("minutes"),
                "pas_a_jour_depuis_j": paj.get("jours"),
                "pas_a_jour_depuis_h": paj.get("heures"),
                "pas_a_jour_depuis_m": paj.get("minutes"),

                # Pour tri & KPI
                "depuis_min": it.get("depuis_min"),
                "age_jdd_jours": it.get("age_jdd_jours"),
            })

        df = pd.DataFrame(lignes)

        # --- Normalisation de la clé de fréquence pour correspondre à TYPE_FREQUENCE ---
        try:
            tf = getattr(Configurations, "TYPE_FREQUENCE", {})
            # map des clés insensibles à la casse -> clé d'origine
            keys_lower_map = { ("" if k is None else str(k)).lower(): k for k in tf.keys() }

            def _norm_freq_key(x):
                if x is None:
                    return None
                s = str(x).strip()
                # si la clé existe telle quelle
                if s in tf:
                    return s
                # sinon, tente une correspondance insensible à la casse
                return keys_lower_map.get(s.lower(), s)

            if "metadata_dcat_accrualperiodicity_value" in df.columns:
                df["metadata_dcat_accrualperiodicity_value"] = df["metadata_dcat_accrualperiodicity_value"].apply(_norm_freq_key)
        except Exception:
            # en cas de souci de config, on laisse tel quel
            pass

        # --- (Optionnel) Ajout d’un libellé lisible si TYPE_FREQUENCE_EN_FR est dispo ---
        try:
            tfenfr = getattr(Configurations, "TYPE_FREQUENCE_EN_FR", None)
            if tfenfr and "metadata_dcat_accrualperiodicity_value" in df.columns:
                lower_to_label = { ("" if k is None else str(k)).lower(): v for k, v in tfenfr.items() }
                df["frequence_libelle"] = df["metadata_dcat_accrualperiodicity_value"].apply(
                    lambda k: lower_to_label.get(str(k).lower(), k)
                )
        except Exception:
            pass

        # --- Types utiles (numériques) ---
        for c in ("periode_jours", "tolerance_ratio", "facteur_attention", "facteur_critique",
                "depuis_min", "ressources_total", "ressources_non_a_jour", "age_jdd_jours"):
            if c in df.columns:
                df[c] = pd.to_numeric(df[c], errors="ignore")

        return df






# =============================================================================
#   Orchestration 8 : Service de traitement des données pour la page 5
# =============================================================================




# =============================================================================
#   Orchestration 9 : Service de traitement des données pour la page 6
# =============================================================================



#--------- Classes d'orchestrations --------------

# ======= Alimenter l'application automatique depuis les sources externes | Page de connexion      ======
# ======= Alimenter l'application automatique depuis le cache de l'application | Page de connexion ======


@dataclass
class orchestration_service_alimenter_cache_app_en_data:
    """
    Orchestration du service d'alimentation de l'application en data:
      - mesurer la fraîcheur du cache de données,
      - alimenter automatiquement (cron),
      - alimenter manuellement (déclencheur utilisateur).
    """
    def __init__(self):
        pass

    def fraicheur_du_cache_de_donnees(self) -> Tuple[Tuple[int, int, int, int], Optional[datetime]]:
        """
        Retourne ((jours, heures, minutes, secondes), last_refresh_dt).
        Si le cache est absent/invalide: ((0, 0, 0, 0), None).
        """
        now = _temps_actuel()
        meta = _lire_le_cache_data(Path(Configurations.CACHE_SOURCES))
        if not meta or "last_refresh_iso" not in meta:
            return (0, 0, 0, 0), None

        try:
            last = datetime.fromisoformat(meta["last_refresh_iso"])
            if last.tzinfo is None:
                last = last.replace(tzinfo=Configurations.TIME_ZONE)
            delta = now - last
            total_seconds = int(delta.total_seconds())
            return _age_cache_en_j_h_m_s(total_seconds), last
        except Exception:
            return (0, 0, 0, 0), None

    def alimenter_automatiquement(self) -> None:
        """
        Alimenter l'application selon la planification configurée.
        Déclenche uniquement si:
          - AUTO_REFRESH_CRON_ENABLED=True (par défaut)
          - Jour autorisé (ex: mon-fri)
          - Heure/minute correspondent exactement (ex: 09:30)
        """
        now = _temps_actuel()
        if not _analyse_declencheur_auto(now):
            st.info(
                f"Rafraîchissement auto non déclenché: "
                f"jour/heure non conformes (config {Configurations.AUTO_REFRESH_CRON_WEEKDAYS} "
                f"{Configurations.AUTO_REFRESH_CRON_HOUR:02d}:{Configurations.AUTO_REFRESH_CRON_MINUTE:02d})."
            )
            return

        try:
            # On alimente; la fonction sous-jacente gère les sorties (parquet, etc.)
            _, _, _, _ = alimenter_app_en_data(connecteurs=Configurations.CONNECTEURS)
            _ecrire_dans_le_cache_data(Path(Configurations.CACHE_SOURCES), now, mode="auto")
            st.success("Alimentation automatique effectuée et cache mis à jour.")
        except Exception as exc:
            st.error(f"Échec de l'alimentation automatique: {exc}")

    def alimenter_manuellement(self, declencheur: Optional[str] = "NON") -> str:
        """
        Alimenter l'application de supervision sous l'action de l'utilisateur.
        - Si declencheur == 'OUI': on alimente et on met à jour le cache.
        - Sinon: on ne fait rien.

        :param declencheur: 'OUI' pour déclencher; 'NON' par défaut.
        :return: message de statut en français.
        """
        if (declencheur or "NON").upper() != "OUI":
            return "Application non alimentée manuellement (par défaut)."

        now = _temps_actuel()
        try:
            _, _, _, _ = alimenter_app_en_data(connecteurs=Configurations.CONNECTEURS)
            _ecrire_dans_le_cache_data(Path(Configurations.CACHE_SOURCES), now, mode="manuel")
            return "Application alimentée manuellement par l'utilisateur."
        except Exception as exc:
            return f"Échec de l'alimentation manuelle: {exc}"


@dataclass
class orchestrer_alimentation_de_l_app:
    """
        Orchestration de l'alimentation de l'application:
            - Se connecter aux sources externes et récupérer :
                - catalogue des métadata pour les jeux de données
                - ressources assoicées au catalogue
                - ressources liées au blob opendata de la pda

            - Construire une liste de jdd à l'aide de la modélisation métier:
                - le modèle reste fidèle au métier

            - sauvegarder cette liste de jeux de données en local dans l'application
                - Pour une lecture rapide dans l'application 
    """
    def __init__(self, port_connexion: PortAbstraitRecupererJdd0dre):
        self.port_de_connexion = port_connexion
        self.connecteur = Configurations.CONNECTEURS

    def alimenter(self) -> None:
        """
            Orchestre une alimentation de l'application en jeux de données

        """
        try:
            # === Implémentation d'une connexion vers les sources externes ====
            return self.port_de_connexion.brancher_le_port()
        except Exception as e:
            print(f"[Code sénario utilisation | Service d'orchestration ] - mapping.py => classe du mapping\n")
            print(f"Classe : orchestrer alimentation de l'application\n")
            print(f"=== Fonction: alimenter | erreur: {e} \n")
            return None
    

# ======= Alimenter l'application automatique depuis le cache de l'application | Page de connexion ======
@dataclass
class orchestration_lecture_jdds_dans_cache_app:
    """
    Orchestration du service d'alimentation de l'application en data:
      - Alimenter l'application par lecture rapide de la sauvegarde de la liste de jdds,

    """
    def __init__(self): pass
    
    def alimenter_app_via_cache(self) -> None:
        """
            L'alimente l'application en liste de jeux de données à partir du cache local

        """
        convertir = ConvertirSourcesenJddOdre()
        convertir.sauvegarder_une_liste_jdds()
        return None

    def lire(self) -> List[Dict]:
        """
            Lecture d'une liste de jeux de données 

        """
        convertir = ConvertirSourcesenJddOdre()
        liste_des_jdds = convertir.lire_une_liste_jdds_du_cache_de_l_app()
        return liste_des_jdds


# --- Alimenter l'application | Par utilisateur, automatique (ex heure fixe lundi-vendredi)

# --- Visualiser données dans  l'application | 
@dataclass
class orchestration_service_voir_données_d_alimentation:
    def __init__(self):pass
    def voir(self
    ) -> Tuple[List[JddOdre], 
               Dict[str, pq.ParquetFile], 
               Dict[str, pd.DataFrame], 
               Dict[str, Any]
    ]:
        """
        Docstring for voir
        
        :param self: Description
        :return: Description
        :rtype: Tuple[List[JddOdre], Dict[str, ParquetFile], Dict[str, DataFrame], Dict[str, Any]]

        """
        liste_des_jdds_odre, \
        liste_des_jdds_format_tech_parquet, \
        liste_des_jdds_dataframe, json_consolide_dict = alimenter_app_en_data(connecteurs=Configurations.CONNECTEURS)
        
        return liste_des_jdds_odre, \
        liste_des_jdds_format_tech_parquet, \
        liste_des_jdds_dataframe, json_consolide_dict

    # Voir à partir du cache
    def voir_depuis_cache_v0(self) -> pd.DataFrame:
        """
        Docstring for voir
            Faire une récupération des datas qui alimentent l'app depuis un cache (local)
        :param self: Description
        :return: les jeux de données sous forme de jdd odre
        :rtype: dataframe
        
        """
        try:
            chemin_parquet = Path(Configurations.SORTIE_PARQUET_JDD_PATH)
            if not chemin_parquet.exists():
                return pd.DataFrame()
            data_issu_du_cache_local = pd.read_parquet(chemin_parquet, engine="pyarrow")
            return data_issu_du_cache_local
        except Exception:
            return pd.DataFrame()

    def voir_depuis_cache_v1(self) :
        """
        Docstring for voir
            Faire une récupération des datas qui alimentent l'app depuis un cache (local)
        :param self: Description
        :return: les jeux de données sous forme de jdd odre
        :rtype: dataframe
        
        """
        try:
            chemin_parquet = Path(Configurations.SORTIE_PARQUET_JDD_PATH)
            if not chemin_parquet.exists():
                return pd.DataFrame()
            #liste_des_jdds, data_issu_du_cache_local = lire_parquet_et_reconstituer(chemin_parquet)
            #data_issu_du_cache_local = lire_json_en_dataframe(chemin_parquet)
            data_issu_du_cache_local = lire_parquet_direct(chemin_parquet)
            
            
            return data_issu_du_cache_local
        except Exception:
            return  []

    def voir_depuis_cache_v2(self) -> pd.DataFrame:
        """
        Récupère les données depuis le cache local (parquet) et
        désérialise les colonnes JSON (qu'elles soient stockées en string
        ou en types imbriqués parquet).
        """
        try:
            chemin_parquet = Path(Configurations.SORTIE_PARQUET_JDD_PATH)
            if not chemin_parquet.exists():
                return pd.DataFrame()

            # Astuces utiles :
            # - engine="pyarrow" permet de garder les types imbriqués si présents
            # - use_nullable_dtypes=True harmonise les bool/int manquants
            df = pd.read_parquet(
                chemin_parquet,
                engine="pyarrow"
            )

            # --- 1) Désérialiser les colonnes JSON si stockées en string ---
            # Détecte les colonnes candidates (par nom ou heuristique sur le contenu)
            candidates_json = [
                col for col in df.columns
                if "json" in col.lower()                      # règle métier : colonnes avec 'json' dans le nom
                or df[col].dtype == "object"                  # potentiellement string/objets
            ]

            def try_parse_json(x):
                # Tente de convertir une chaîne JSON en dict/list
                if isinstance(x, str):
                    s = x.strip()
                    if (s.startswith("{") and s.endswith("}")) or (s.startswith("[") and s.endswith("]")):
                        try:
                            return json.loads(s)
                        except Exception:
                            return x  # laisse tel quel si non parseable
                return x  # déjà list/dict ou autre type

            for col in candidates_json:
                # Si la colonne est string, essaie de parser ligne à ligne
                if df[col].dtype == "object":
                    # Si c'est déjà list/dict (cas B), on ne touche pas
                    sample = df[col].dropna().head(1)
                    if not sample.empty and isinstance(sample.iloc[0], (dict, list)):
                        # Rien à faire : déjà "désérialisé"
                        pass
                    else:
                        # Tente de charger JSON depuis string
                        df[col] = df[col].map(try_parse_json)

            # --- 2) Normaliser une colonne JSON imbriquée (exemples) ---
            # Exemple: si 'jsonressources_jsonressources_count' est un dict avec des clés utiles
            col_struct = "jsonressources_jsonressources_count"
            if col_struct in df.columns:
                # Si la colonne est un dict par ligne, on peut l'ouvrir en colonnes
                mask_dict = df[col_struct].apply(lambda x: isinstance(x, dict))
                if mask_dict.any():
                    expanded = pd.json_normalize(df.loc[mask_dict, col_struct])
                    # Suffixe les colonnes pour éviter collisions
                    expanded = expanded.add_prefix(f"{col_struct}__")
                    # Réindex pour pouvoir concaténer proprement
                    expanded.index = df.index[mask_dict]
                    df = pd.concat([df, expanded], axis=1)

            # --- 3) Convertir les booléens/entiers propres ---
            # Ta colonne booléenne
            if "has_sources_externes_pda_opendata_monitoring_bool" in df.columns:
                # Convertit en booléen nullable pandas (gère NaN)
                df["has_sources_externes_pda_opendata_monitoring_bool"] = (
                    df["has_sources_externes_pda_opendata_monitoring_bool"]
                    .map(lambda x: bool(x) if pd.notna(x) else pd.NA)
                    .astype("boolean")
                )

            # Exemple de conversion numérique si 'ressources_count' doit être int
            if "ressources_count" in df.columns:
                df["ressources_count"] = pd.to_numeric(df["ressources_count"], errors="coerce").astype("Int64")

            return df

        except Exception:
            # En prod, log l'erreur; ici on renvoie DF vide
            return pd.DataFrame()

    def voir_depuis_cache_bon(self) -> List[Dict[str, Any]]:
        """
        Récupère les données depuis le cache local (Parquet).
        Retourne une liste de dicts avec colonnes JSON désérialisées.
        """
        try:
            chemin_parquet = Path(getattr(Configurations, "SORTIE_PARQUET_JDD_PATH"))
            if not chemin_parquet.exists():
                return []

            # Lecture Parquet avec PyArrow
            pf = pq.ParquetFile(str(chemin_parquet))
            table = pf.read()  # pyarrow.Table
            records = table.to_pylist()  # Liste de dicts natifs Python

            # Colonnes JSON à désérialiser (depuis ta config)
            colonnes_json = list(getattr(Configurations, "LISTE_COLS_JSON_RESSOURCES", ["ressources_json"])) \
                        + list(getattr(Configurations, "LISTE_COLS_JSON_PDA", ["matched_blobs_json"]))

            # Désérialisation en place
            for rec in records:
                for col in colonnes_json:
                    val = rec.get(col)
                    if isinstance(val, str):
                        s = val.strip()
                        if (s.startswith("{") and s.endswith("}")) or (s.startswith("[") and s.endswith("]")):
                            try:
                                rec[col] = json.loads(s)
                            except Exception:
                                pass  # laisse la valeur telle quelle si parsing échoue

            return records  # Liste de dicts

        except Exception as e:
            print(f"[voir_depuis_cache] Erreur: {e}")
            return []
 
    def voir_depuis_cache_v3(self) -> pd.DataFrame:
        """
        Lecture Parquet (PyArrow) -> records -> filtres -> expansion des ressources -> DataFrame.
        Règles de filtrage:
          - has_sources_externes_pda_opendata_monitoring == False (ou "False")
          - ressources_count > 0
        Colonnes JSON string désérialisées: ressources_json, matched_blobs_json (adaptable via Configurations).
        """
        try:
            chemin_parquet = Path(getattr(Configurations, "SORTIE_PARQUET_JDD_PATH"))
            if not chemin_parquet.exists():
                return pd.DataFrame()

            # --- Lecture Parquet en liste de dicts ---
            pf = pq.ParquetFile(str(chemin_parquet))
            table = pf.read()                       # pyarrow.Table
            records: List[Dict[str, Any]] = table.to_pylist()

            # --- Colonnes JSON à désérialiser (depuis ta config) ---
            cols_json_ress = list(getattr(Configurations, "LISTE_COLS_JSON_RESSOURCES", ["ressources_json"]))
            cols_json_pda  = list(getattr(Configurations, "LISTE_COLS_JSON_PDA", ["matched_blobs_json"]))
            colonnes_json = set(cols_json_ress + cols_json_pda)

            def parse_json(val: Any) -> Any:
                if isinstance(val, str):
                    s = val.strip()
                    if (s.startswith("{") and s.endswith("}")) or (s.startswith("[") and s.endswith("]")):
                        try:
                            return json.loads(s)
                        except Exception:
                            return val
                return val

            def normalize_bool(v: Any) -> Optional[bool]:
                if isinstance(v, bool):
                    return v
                if v is None:
                    return None
                if isinstance(v, (int, float)):
                    # 0 -> False, non-0 -> True
                    return bool(int(v))
                if isinstance(v, str):
                    s = v.strip().lower()
                    if s in ("true", "1", "yes", "y", "t"):
                        return True
                    if s in ("false", "0", "no", "n", "f"):
                        return False
                return None  # inconnu

            def to_int(v: Any) -> int:
                try:
                    if v is None:
                        return 0
                    if isinstance(v, (int, float)):
                        return int(v)
                    if isinstance(v, str):
                        s = v.strip()
                        return int(s) if s else 0
                    return 0
                except Exception:
                    return 0

            rows_out: List[Dict[str, Any]] = []

            for i, rec in enumerate(records):
                try:
                    # Désérialiser colonnes JSON string si besoin
                    for col in colonnes_json:
                        if col in rec:
                            rec[col] = parse_json(rec.get(col))

                    # Normaliser booléen "has_sources..."
                    has_bool = normalize_bool(rec.get("has_sources_externes_pda_opendata_monitoring_bool"))
                    if has_bool is None:
                        has_bool = normalize_bool(rec.get("has_sources_externes_pda_opendata_monitoring"))

                    # Compter ressources
                    ressources_count = to_int(rec.get("ressources_count"))

                    # --- Filtre: has_sources == False et ressources_count > 0 ---
                    #  Change "is False" en "is True" si tu veux l'inverse
                    if (has_bool is False) and (ressources_count > 0):
                        ressources_list = rec.get("ressources_json")

                        # Métas utiles au niveau dataset
                        dataset_id = rec.get("dataset_id") or rec.get("uid") or rec.get("uid_meta") or ""
                        uid_metadata = rec.get("uid_metadata") or rec.get("uid_meta") or ""
                        titre_dataset = rec.get("title") or rec.get("dataset_title") or rec.get("nom") or ""

                        # Infos blob (si dict)
                        blobs = rec.get("matched_blobs_json")
                        blob_fields = {}
                        if isinstance(blobs, dict):
                            for k in ["name", "size", "lastmodified", "boolisdeleted", "contenttype",
                                      "storageaccountname", "storagecontainername", "FullName"]:
                                if k in blobs:
                                    blob_fields[f"blob_{k}"] = blobs.get(k)

                        if isinstance(ressources_list, list) and len(ressources_list) > 0:
                            # Une ligne par ressource
                            for res in ressources_list:
                                if not isinstance(res, dict):
                                    continue

                                row = {
                                    # --- clés dataset/meta ---
                                    "dataset_id": dataset_id,
                                    "uid_metadata": uid_metadata,
                                    "title": titre_dataset,
                                    "has_sources_externes_pda_opendata_monitoring": rec.get("has_sources_externes_pda_opendata_monitoring"),
                                    "has_sources_externes_pda_opendata_monitoring_bool": has_bool,
                                    "ressources_count": ressources_count,

                                    # --- clés ressource ---
                                    "uid_ressource": res.get("uid_ressource") or res.get("id") or res.get("uid") or "",
                                    "updated_at_ressource": res.get("updated_at_ressource") or res.get("last_modified") or res.get("updated_at") or "",
                                    "display_name": res.get("display_name") or res.get("name") or "",

                                    # --- exemples meta supplémentaires (si présents) ---
                                    "uid_metadata_source": rec.get("uid_metadata") or "",
                                }
                                # fusionner champs blobs
                                row.update(blob_fields)

                                rows_out.append(row)
                        else:
                            # Pas de liste de ressources: on crée une ligne "dataset-only"
                            row = {
                                "dataset_id": dataset_id,
                                "uid_metadata": uid_metadata,
                                "title": titre_dataset,
                                "has_sources_externes_pda_opendata_monitoring": rec.get("has_sources_externes_pda_opendata_monitoring"),
                                "has_sources_externes_pda_opendata_monitoring_bool": has_bool,
                                "ressources_count": ressources_count,
                                "uid_ressource": "",
                                "updated_at_ressource": "",
                                "display_name": "",
                            }
                            row.update(blob_fields)
                            rows_out.append(row)

                except Exception:
                    # On ignore la ligne en erreur et continue
                    continue

            df = pd.DataFrame(rows_out)
            return df

        except Exception:
            # Lecture ou conversion en erreur: DF vide
            return pd.DataFrame()


    def voir_depuis_cache_v4(self) -> List[Dict[str, Any]]:
        """
        Récupère les données depuis le cache local (Parquet).
        Retourne une liste de dicts avec colonnes JSON désérialisées.
        """
        try:
            chemin_parquet = Path(getattr(Configurations, "SORTIE_PARQUET_JDD_PATH"))
            if not chemin_parquet.exists():
                return []

            # Lecture Parquet avec PyArrow
            pf = pq.ParquetFile(str(chemin_parquet))
            table = pf.read()  # pyarrow.Table
            records = table.to_pylist()  # Liste de dicts natifs Python

            # Colonnes JSON à désérialiser (depuis ta config)
            colonnes_json = list(getattr(Configurations, "LISTE_COLS_JSON_RESSOURCES", ["ressources_json"])) \
                        + list(getattr(Configurations, "LISTE_COLS_JSON_PDA", ["matched_blobs_json"]))

            # Désérialisation en place
            for rec in records:
                for col in colonnes_json:
                    val = rec.get(col)
                    if isinstance(val, str):
                        s = val.strip()
                        if (s.startswith("{") and s.endswith("}")) or (s.startswith("[") and s.endswith("]")):
                            try:
                                rec[col] = json.loads(s)
                            except Exception:
                                pass  # laisse la valeur telle quelle si parsing échoue

            return records  # Liste de dicts

        except Exception as e:
            print(f"[voir_depuis_cache] Erreur: {e}")
            return []



    def voir_depuis_cache(self) -> List[Dict[str, Any]]:
        """
        Récupère les données depuis le cache local (Parquet).
        Retourne une liste de dicts avec colonnes JSON désérialisées.
        """
        try:
            chemin_parquet = Path(getattr(Configurations, "SORTIE_PARQUET_JDD_PATH"))
            if not chemin_parquet.exists():
                return []

            # Lecture Parquet avec PyArrow
            pf = pq.ParquetFile(str(chemin_parquet))
            table = pf.read()  # pyarrow.Table
            records = table.to_pylist()  # Liste de dicts natifs Python

            # Colonnes JSON à désérialiser (depuis ta config)
            colonnes_json = list(getattr(Configurations, "LISTE_COLS_JSON_RESSOURCES", ["ressources_json"])) \
                        + list(getattr(Configurations, "LISTE_COLS_JSON_PDA", ["matched_blobs_json"]))

            # Désérialisation en place
            for rec in records:
                for col in colonnes_json:
                    val = rec.get(col)
                    if isinstance(val, str):
                        s = val.strip()
                        if (s.startswith("{") and s.endswith("}")) or (s.startswith("[") and s.endswith("]")):
                            try:
                                rec[col] = json.loads(s)
                            except Exception:
                                pass  # laisse la valeur telle quelle si parsing échoue

            return records  # Liste de dicts

        except Exception as e:
            print(f"[voir_depuis_cache] Erreur: {e}")
            return []


    def _3_jdds_extraits_imparfait(liste_dicts_jdds: Optional[List[Dict[str, Any]]]) -> pd.DataFrame:
        """
            Pour démonstration: retour trois jdds dans un dataframe
        """
        
        # --- Donnés / Sessionn ---
        try:
            df_trois_jdds_imparfaits = pd.DataFrame()

            service = orchestration_service_voir_données_d_alimentation()
            cles_sessions = ["liste_des_jdds_odre", "listes_des_jdds_format_tech_parquet", "liste_des_jdds_dataframe", "json_consolide_dict"]
            cles_sessions_filtres = ["selecteur_producteur", "selecteur_frequence", "selecteur_publique", "selecteur_restreint"]
            
            if not all(k in st.session_state for k in cles_sessions) or not all(k in st.session_state for k in cles_sessions_filtres):
                #liste_des_jdds_odre, liste_des_jdds_format_tech_parquet, liste_des_jdds_dataframe, json_consolide_dict = service.voir()
                
                liste_des_jdds_odre = service.voir_depuis_cache()
            
            if isinstance(liste_des_jdds_odre, (list, tuple)):
                # Filtrer la liste avant affichage
                filtre_liste = [
                    rec for rec in liste_des_jdds_odre
                    if isinstance(rec, dict)
                    and str(rec.get("has_sources_externes_pda_opendata_monitoring_bool", "")).lower() == "true"
                    and int(rec.get("ressources_count", 0)) > 0
                ]

                # récupère les  3 jdds
                for i, item in enumerate(filtre_liste[:3]):
                    cols_meta = [col for col in item.keys() if col in Configurations.LISTE_CHAMPS_META]
                    cols_res = [col for col in item["ressources_json"].keys()]
                    st.json(item)

            return 
        except Exception as e: 
            return pd.DataFrame()

    def manip(self) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
            Construire un jdd à partir des sources

        """
        sources_metadata, sources_ressources, sources_pda = alimenter_app_en_data_test(connecteurs= Configurations.CONNECTEURS)

        return (sources_metadata, sources_ressources, sources_pda)
    
    def lecture_sources(self) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
            Lecture des trois sources sauvegardées en locale au format json
        """
        sources_externe_metadata = pd.read_json(Configurations.SORTIE_JSON_SOURCE_EXTERNE_METADTA, orient="records")
        sources_externe_ressources = pd.read_json(Configurations.SORTIE_JSON_SOURCE_EXTERNE_RESSOURCES, orient="records")
        sources_externe_pda = pd.read_json(Configurations.SORTIE_JSON_SOURCE_EXTERNE_PDA, orient="records")
        return (sources_externe_metadata, sources_externe_ressources, sources_externe_pda)
    
    def modeliser_jdds(self) -> pd.DataFrame:
        """
            Prend les trois dataFrame retournées par la fonction lecture_source
            et construit un df final qui modélise les jdd odré
        """
        sources_externe_metadata, sources_externe_ressources, sources_externe_pda = self.lecture_sources()
        df_final = construire_df(df1=sources_externe_metadata,
                                 df2=sources_externe_ressources,
                                 df3=sources_externe_pda
        )
        return df_final


# --- Use case: Actualisation des données pour la page 5 -----------------------
@dataclass
class orchestration_service_actualisation_des_donnees:
    """
    Cas d'usage “Actualisation des données” :
    - construit les entités JddOdre depuis le DF consolidé,
    - appelle le service de domaine d'actualisation,
    - enrichit le DF pour l'UI,
    - retourne (df_enrichi, analyses, indicateurs_globaux_dict).
    """
    def __init__(self): pass

    def _construire_entites_depuis_df_0(self, df_consolide: pd.DataFrame) -> List[JddOdre]:
        if df_consolide is None or df_consolide.empty:
            return []
        jdds: List[JddOdre] = []
        metadonnees = {}
        ressources = {}
        pda_opendata = {}
        liste_metadta = Configurations.LISTE_CHAMPS_META
        liste_ressource = Configurations.LISTE_CHAMPS_RESSOURCES
        liste_blob = Configurations.LISTE_CHAMPS_BLOB_MONITORING

        for idx, lig in df_consolide.iterrows():
            uid = lig.get("uid")
            dataset_id = lig.get("dataset_id")
            # métadonnées complet avec usage des champs repertoriés dans la configuration
            for champ in liste_metadta:
                if champ in df_consolide.columns:
                    metadonnees[str(champ)] = lig.get(str(champ))

            # ressources complet avec usage des champs répertoriés dans la configuration
            for champ in liste_ressource:
                if champ in df_consolide.columns:
                    ressources[champ] = lig.get(champ)
            # Blob monitoring complet avec usage des champs répertoriés dans la configuration
            for champ in liste_blob:
                if champ in df_consolide.columns:
                    pda_opendata[champ] = lig.get(champ)
            # Ajout du jdd constitué        
            jdds.append(JddOdre(
                id_jdd_odre=int(idx) if isinstance(idx, int) else None,
                nom_jdd_odre=str(dataset_id) if dataset_id is not None else str(uid),
                metadonnees=metadonnees,
                ressources=ressources,
                pda_opendata=pda_opendata,
            ))
        return jdds


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


    def evaluer(self, df_consolide: pd.DataFrame,
                frequence_par_defaut_jours: int = 30,
                tolerance_ratio: float = 0.10
                ) -> Tuple[pd.DataFrame, List[AnalyseActualisationJdd], Dict[str, Any]]:
        """
        Évalue l'actualisation sur le DF consolidé : retourne (df_enrichi, analyses, indicateurs_globaux_dict).
        """
        # 1) Entités
        jdds = self._construire_entites_depuis_df(df_consolide)
        # 2) Appel domaine
        svc = ServiceActualisationDomaine()
        now = _temps_actuel()  # timezone de l'app
        periode_defaut = timedelta(days=frequence_par_defaut_jours) if frequence_par_defaut_jours > 0 else None
        analyses = svc.analyser_liste_jdd(
            jdds=jdds,
            maintenant=now,
            frequence_par_defaut=periode_defaut,
            tolerance_ratio=tolerance_ratio
        )
        # 3) Colonnes UI
        lignes_ui: List[Dict[str, Any]] = []
        for a in analyses:
            lignes_ui.append({
                "uid": a.uid,
                "dataset_id": a.dataset_id,
                "statut_actualisation": a.statut.value,
                "ressources_count": a.ressources_count,
                "ressources_non_a_jour_count": a.ressources_non_a_jour_count,
                "ressources_impacts_json": json.dumps([ri.__dict__ for ri in a.ressources_non_a_jour], ensure_ascii=False),
                "ressources_par_origin_type_json": json.dumps(a.repartition_par_origin_type, ensure_ascii=False),
                "date_anniversaire": a.date_anniversaire.isoformat() if a.date_anniversaire else "",
                "age_jdd_jours": a.age_jdd_jours,
            })
        df_enrichi = pd.DataFrame(lignes_ui)

        # Fusion (respect noms, pas de renommage)
        keys = [k for k in ["uid", "dataset_id"] if k in df_consolide.columns]
        if keys:
            df_out = df_consolide.merge(df_enrichi, on=keys, how="left")
        else:
            df_out = pd.concat([df_consolide.reset_index(drop=True), df_enrichi.reset_index(drop=True)], axis=1)

        # 4) Indicateurs globaux
        indics = calculer_indicateurs_globaux(analyses)
        indicateurs_globaux_dict = {
            "nb_jdd": indics.nb_jdd,
            "nb_a_jour": indics.nb_a_jour,
            "nb_pas_a_jour": indics.nb_pas_a_jour,
            "nb_ressources_total": indics.nb_ressources_total,
            "nb_ressources_non_a_jour": indics.nb_ressources_non_a_jour,
            "repartition_origin_type": dict(indics.repartition_origin_type),
        }
        return df_out, analyses, indicateurs_globaux_dict

    def voir_et_evaluer(self,
                        frequence_par_defaut_jours: int = 30,
                        tolerance_ratio: float = 0.10
                        ) -> Tuple[pd.DataFrame, List[AnalyseActualisationJdd], Dict[str, Any]]:
        """
        Récupère les données via le service 'voir' puis évalue l'actualisation.
        """
        service_visualiser = orchestration_service_voir_données_d_alimentation()
        _, _, liste_des_jdds_dataframe, _ = service_visualiser.voir()
        df_consolide = liste_des_jdds_dataframe.get("catalogue_ressources_blob", pd.DataFrame())
        return self.evaluer(df_consolide, frequence_par_defaut_jours, tolerance_ratio)








