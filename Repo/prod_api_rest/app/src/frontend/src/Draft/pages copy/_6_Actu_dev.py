# --- Application de supervision des jeux de données ODRE 
# chemin: /pages/_4_Actualisation_des_donnees.py
# ==== coding: utf-8 ====


# Importation des librairies
import pandas as pd
import streamlit as st
from datetime import datetime
import streamlit_antd_components as sac
from st_aggrid import AgGrid, GridOptionsBuilder


# Importation des modules
from srcs.configs import Configurations
from srcs.codes_pour_interface_ui.page_standard import (
    Page_standard
)
from srcs.codes_pour_senario_utilisation_app.services_d_orchestration import (
    orchestration_service_alimenter_cache_app_en_data
)
from srcs.codes_pour_interface_ui.composants_pour_pages import(
    composant_actualisation
)




def _ajouter_contenu():
    """Injecte le contenu dans les conteneurs posés par la disposition."""
    layout = st.session_state.get("layout_page_4")
    if not layout:
        st.warning("Disposition non initialisée.")
        return

    col_gauche = layout["col_gauche"]
    col_droite = layout["col_droite"]
    col_bas = layout["col_bas"]

    # --- Colonne droite : composant d'actualisation ---
    with col_droite:
        composant_actualisation(col_droite)

    # --- Bas de page (déjà géré par Page_standard._bas_de_page) ---


def _ajouter_contenu():
    """Injecte le contenu dans les conteneurs posés par la disposition."""
    layout = st.session_state.get("dispositon_page_actualisation_des_données")
    if not layout:
        st.warning("Disposition non initialisée.")
        return

    col_gauche = layout["col_gauche"]
    col_droite = layout["col_droite"]
    col_bas = layout["col_bas"]

    # --- Données / session ---
    try:
        service = orchestration_service_alimenter_cache_app_en_data()

        st.write(f"Dev")
        # === Pour filtre et affichage ===

        # Indicateurs globaux

        # === Options pour filtres ===

        # === Mise en session ===

        # Initialisation des sélecteurs (état des filtres UI)
 
    except Exception as e:
        st.error(f"[Page _6_Actu_dev] : {e}")
        return

    # --- Colonne gauche ---
    # rien à faire pour le moment 



    # --- Colonne droite ---
    with col_droite:
    # rien à faire pour le momment 
        composant_actualisation(col_droite)


    # --- Bas de page (ICI)---



# === Construction de la page ===
try:
    titre_page = Configurations.TITRE_PAGE_4
    utilisateur = Configurations.UTILISATEUR_0
    chemin_css = Configurations.PATH_CSS
    page = Page_standard(titre_page, utilisateur, chemin_css)
    page._mise_en_page()
    page._disposition_page_actualisations_des_donnees(ratios=(3,7))
    page._css()
    page._barre_laterale()
    _ajouter_contenu()
    page._bas_de_page()
except Exception as e:
    st.error(f"Erreur lors du chargement de la page: {e}")
