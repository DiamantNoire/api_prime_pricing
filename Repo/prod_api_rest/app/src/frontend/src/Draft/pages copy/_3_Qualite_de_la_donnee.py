# interface/pages/_3_Quakute_de_la_donnee.py

# Importation de librairies
import streamlit as st

# Importation de modules
from src.config import Config
from src.couche_ui.page_standard import Page_standard


def _ajouter_contenu():
    try:
        st.write("Le contenu de la page")

    except Exception as e:
        st.error(f"Erreur inattendue : {e}")


try:
    titre_page = Config.TITRE_PAGE_3
    utilisateur = Config.UTILISATEUR_0
    chemin_css = Config.PATH_CSS

    page = Page_standard(titre_page, utilisateur, chemin_css)
    page._css()
    page._barre_laterale()
    _ajouter_contenu()
    page._bas_de_page()
except Exception as e:
    st.error(f"Erreur lors du chargement de la page: {e}")