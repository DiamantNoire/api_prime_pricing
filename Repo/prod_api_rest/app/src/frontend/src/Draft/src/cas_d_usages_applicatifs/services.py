# src/cas_d_usage_applicatifs/services.py
# ==== coding: utf-8 ====

# Importation de librairies
from __future__ import annotations

import pandas as pd
from pathlib import Path

from typing import List, Dict, Any

# Importation de modules
from src.config import Config
from src.domaine_fonctionnel.entites import JddOdre

from src.infrastructure_technique.correspondances import(
    lecture_des_donnees_sources
)
from src.infrastructure_technique.boite_a_outils_de_fonctions_auxiliaires import(
    lecture_du_parquet
) 
from src.cas_d_usages_applicatifs.outils_fonctions_auxiliaires import(
    normaliser_cle_chemin,
    lier_sources_jdds_modelises,
    extraire_cles_normalisees_depuis_objet
)
from src.domaine_fonctionnel.logiques import  (
    # ==== Fonctions dédiées à la page: Actualisation des données ====#
    calculer_age_jdd,
    evaluer_confirmite_frequence,
    projeter_prochaine_mise_a_jour,
    mise_a_dispo_cols_utiles_du_jdds,
    generer_indicatuer_actualisation,
    detecter_anomalie_actualisation_sur_1_jjd,
)


class CasActuatlisationsDonnees:
    def __init__(self, chemin_parquet, seuils, regles_frequences):
        self.chemin_parquet = chemin_parquet
        self.seuils = seuils
        self.regles_frequences = regles_frequences
    
    def _charger_jdds_depuis_parquet(self) -> List["JddOdre"]:
        p = Path(self.chemin_parquet or Config.JDD_ODRE_PATH_PARQUET)
        df = lecture_du_parquet(p)
        return lier_sources_jdds_modelises(df) if (df is not None and not df.empty) else []
    
    def analyser(self) -> List[Dict[str, Any]]: 
        """
        Docstring for analyser
            Analyse chaque JDD: pour le moment âge, statut, écart, fréquence, prochaine échange, confiance, anomalies.
        :param self: Description
        :return: Description
        :rtype: List[Dict[str, Any]]
        """
        try:
            jdds = self._charger_jdds_depuis_parquet()
            if not jdds:
                return []
            
            resultalts: List[Dict[str, Any]] = []
            for jdd in jdds:
                age_str, age_commentaire = calculer_age_jdd(jdd=jdd)
                statut, ecart_min, frequence = evaluer_confirmite_frequence(jdd=jdd,
                                                                            regle_frequence=self.regles_frequences
                )
                prochaine_echeance, mode_calcul, confiance = projeter_prochaine_mise_a_jour(jdd=jdd,
                                                                                            regle_frequence=self.regles_frequences
                )
                anomalies, has_d_anomalies = detecter_anomalie_actualisation_sur_1_jjd(jdd=jdd,
                                                                                       seuil_alerte=self.seuils,
                                                                                       regle_frequence=self.regles_frequences
                )
                indices, top_en_retard, statut_global = generer_indicatuer_actualisation(list_jdds=jdds,
                                                                                        seuils_alerte=self.seuils,
                                                                                        regles_frequecnce=self.regles_frequences
                )
                resultalts.append({
                    # === Pour identidier jdd, ressources, metadonnée et PDA si dipo ===
                    "id": jdd.id_jdd_odre,
                    "nom": jdd.nom_jdd_odre,
                    "metadonnes": jdd.metadonnees,
                    "ressources": jdd.ressources,
                    "PDA": jdd.PDA_opendata,

                    # === Pour des besoins en alterte
                    "age": age_str,
                    "age_commentaire": age_commentaire,
                    "statut": statut,
                    "ecart_min": ecart_min,
                    "frequence": frequence,
                    "prochaine_echeance": prochaine_echeance,
                    "mode_calcul": mode_calcul,
                    "confiance": confiance,
                    "anomalies": anomalies,
                    "has_d_anomalies": has_d_anomalies,

                    # === Pour des besoins de classement global ===
                    "indicateurs": indices,
                    "top_en_retard": top_en_retard,
                    "statut_global": statut_global,

                    # === Pour des besoins de filtres ====
                    "producteur": (jdd.metadonnees or {}).get("metadata_default_publisher_value", ""),
                    "visibilite_publique": (jdd.metadonnees or {}).get("is_published", ""),
                    "visibilite_restreinte": (jdd.metadonnees or {}).get("is_restricted", "")
                })
            return resultalts
        except Exception:
            return []

    def toute_les_colonnes(self, *, conserver_indices: bool = False) -> List[str]:
        """
        Agrège et normalise les clés des différentes sources sur l'ensemble des JDDs.
        """
        jdds = self._charger_jdds_depuis_parquet()
        if not jdds:
            return []

        seen = set(); colonnes: List[str] = []
        for jdd in jdds:
            # 1) Méta à plat
            for k in (jdd.metadonnees or {}).keys():
                nk = normaliser_cle_chemin(k, conserver_indices=False)
                if nk not in seen:
                    seen.add(nk); colonnes.append(nk)

            # 2) Ressources (JSON)
            if jdd.ressources is not None:
                for nk in extraire_cles_normalisees_depuis_objet(jdd.ressources, prefix="ressources",
                                                                 conserver_indices=conserver_indices
                    ):
                    if nk not in seen:
                        seen.add(nk); colonnes.append(nk)

            # 3) PDA / Blobs (JSON)
            if jdd.PDA_opendata is not None:
                for nk in extraire_cles_normalisees_depuis_objet(jdd.PDA_opendata, prefix="PDA",
                                                                 conserver_indices=conserver_indices
                    ):
                    if nk not in seen:
                        seen.add(nk); colonnes.append(nk)

        return colonnes

    def toute_les_colonnes_0(self) -> List[str]:
        """
        """
        jdds = self._charger_jdds_depuis_parquet()
        if not jdds:
            return []
        liste_retour = mise_a_dispo_cols_utiles_du_jdds(jdds)
        return liste_retour
