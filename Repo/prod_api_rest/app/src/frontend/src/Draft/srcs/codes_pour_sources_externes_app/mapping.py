# --- Application de supervision des jeux de données ODRE
# chemin: srcs/codes_pour_sources_externes_app/mapping.py
# ==== coding: utf-8 ====

# === Importation des librairies ===
import pandas as pd
from typing import Dict, List, Any, Tuple, Set
from dataclasses import dataclass

# === Imporatation de modules ====
from srcs.configs import Configurations
from srcs.codes_pour_metier_admin_jdd_odre_app.modelisation_jdd_odre import JddOdre
from srcs.codes_pour_sources_externes_app.outils_pour_sources_externes import (
    save_jdds_jsonl,
    alimenter_app_en_data_test, 
    _construire_entites_depuis_df, 
    construire_df,
    load_jdds_jsonl_as_dicts
)


#--------- Classe de laison --------------
@dataclass
class ConvertirSourcesenJddOdre:
    """
        Liaison faite entre les trois sources (3 dataframes) et la modélisation des jeux de données
        Classe qui construit:
            un dataframe image d'une liste de jeux de dondnées
            sauvegarde la liste de jeux de données en local pour une lecture rapide (json line)
    """
    def __init__(self): pass
    
    def construire_une_liste_jdds(self) -> List[JddOdre]:
        """
            Fonction qui cré la liste de jeux de données odré

        """
        try:
            connecteur = Configurations.CONNECTEURS
            df_source_metadata, df_source_ressources, df_source_pda = alimenter_app_en_data_test(connecteurs=connecteur)
            df_sources_externes = construire_df(df1=df_source_metadata,
                                                df2=df_source_ressources,
                                                df3=df_source_pda
            )
            # === Sauvegarde de la liste des jeux de données en local pour lecture rapide ===
            # === (Une ligne = un objet JDD sérialisé en JSON.) ===
            liste_de_jdds_odre: List[JddOdre] = _construire_entites_depuis_df(df_consolide=df_sources_externes)
            
            return liste_de_jdds_odre
        except Exception as e:
            print(f"[Code pour entrées | Sortie ] - mapping.py => classe du mapping\n")
            print(f"=== Fonction: construire_une_liste_jdds | erreur: {e} \n")
            return []
    
    def sauvegarder_une_liste_jdds(self) -> str:
        """
            Fonction qui procède à la sauvegarde d'une liste de jjds en local 
            pour une lecture rapide dans l'application.

        """
        try:
            liste_jdds = self.construire_une_liste_jdds()
            save_jdds_jsonl(liste_jdds=liste_jdds,
                            path=Configurations.SAUVEGARDE_JDDS_EN_JSON_LINES
            )
            return "LISTE DE JDDS SAUVEGARDEE !"
        except Exception as e:
            print(f"[Code pour entrées | Sortie ] - mapping.py => classe du mapping\n")
            print(f"=== Fonction: construire_une_liste_jdds | erreur: {e} \n")
            return "LISTE DE JDDS NON SAUVEGARDEE ! "
    
    def lire_une_liste_jdds_du_cache_de_l_app(self) -> List[Dict]:
        """
            Fonction qui assure la lecture d'une liste de jeux de données
            Retourne une liste de dictionnaire (un dico = un jdd)
        """
        try:
            path = Configurations.SAUVEGARDE_JDDS_EN_JSON_LINES
            liste_de_dictionnaires = load_jdds_jsonl_as_dicts(path=path)
            return liste_de_dictionnaires
        except Exception as e:
            print(f"[Code pour entrées | Sortie ] - mapping.py => classe du mapping\n")
            print(f"=== Fonction: construire_une_liste_jdds | erreur: {e} \n")
            return []

