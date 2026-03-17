# ---------------------------------------------------------
# Point d'entrée dans l'application : Accueil
# ---------------------------------------------------------

# === Remarque ===
# Aucune logique de récupération des sources: à termes une lecture dans la PDA ou dans un blob
# Les sources sont dans un fichier Parquet /data
# 

# - Importation de librairies
import sys
import time
import requests
import random
import pandas as pd
import streamlit as st
from pathlib import Path

# - Importation de modules
from src.config import Config
from src.couche_ui.page_standard import Page_standard

from src.couche_infra.recuperateurs_des_data_ds_parquet import (
        Souscripteur
)
from src.couche_infra.services_techniques import (
        ServiceInfraDevDonneesSousParquet
)

# Ajoute le dossier racine
sys.path.append(str(Path(__file__).resolve().parent.parent))  

# Méthode pour ajouter du contenur spécifique à la page d'accueil
def _ajouter_contenu():
    try:
        st.write("Le contenu de la page")
        souscripteur_service_data_odre = Souscripteur()
        sources_data_odre = ServiceInfraDevDonneesSousParquet(souscripteur_service_data_odre)
        df = sources_data_odre.souscrire_au_service()

        st.warning(f"type du df : {type(df).__name__}")
        st.dataframe(df, width="stretch")  

    except Exception as e:
        st.error(f"Echec dans _ajouter_ctenu : {e}")

# Connection à Snowflake
def connexion_sur_app():
        """Etablit la connexion à Snowflake"""
        pass

# Point de lancment
def run() -> None:
        try:
            # Paramètres
            titre_page = Config.TITRE_PAGE_0
            utilisateur = Config.UTILISATEUR_0
            chemin_css = Config.PATH_CSS

            # Instanciation de la page d'acceuil 
            page = Page_standard(
                titre_page,
                utilisateur,
                chemin_css
            )

            # Création d'une page standard
            page._css()
            page._barre_laterale()
            _ajouter_contenu()
            page._bas_de_page()

        except Exception as e:
               # Pour la console
               print(f"Erreur de chargement de la page d'acceuil: {e}")

if __name__ == "__main__":
       run()