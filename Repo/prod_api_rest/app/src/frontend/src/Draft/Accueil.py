# ---------------------------------------------------------
# Point d'entrée dans l'application : Accueil
# ---------------------------------------------------------

# - Importation de librairies
import sys
import streamlit as st
from pathlib import Path

# - Importation de modules
from srcs.configs import Configurations
from srcs.codes_pour_interface_ui.page_standard import Page_standard


# Ajoute le dossier racine
sys.path.append(str(Path(__file__).resolve().parent.parent))  

# Méthode pour ajouter du contenur spécifique à la page d'accueil
def _ajouter_contenu():
    st.title("Bienvenue sur le tableau de bord ODRE")
    st.markdown(
        """
        Cette application permet de visualiser et d'analyser les jeux de données ODRE.
        
        Utilisez la barre latérale pour naviguer entre les différentes sections.
        """
    )
    # Badges cache (parquet) pour transparence utilisateur
    try:
        if getattr(Configurations, "FORCE_READ_PARQUET_ALWAYS", False):
            st.markdown(
                "<div class='flex-row'><div class='flex-block'>Mode test: lecture cache parquet forcée</div></div>",
                unsafe_allow_html=True
            )
        elif getattr(Configurations, "ENABLE_CACHE_JDD", True):
            ttl = getattr(Configurations, "CACHE_TTL_MINUTES_JDD", 60)
            st.markdown(
                f"<div class='flex-row'><div class='flex-block'>Cache TTL actif: {ttl} min</div></div>",
                unsafe_allow_html=True
            )
    except Exception:
        pass

# Connection à Snowflake
def connexion_sur_app():
        """Etablit la connexion à Snowflake"""
        pass

# Point de lancment
def run() -> None:
        try:
            # Paramètres
            titre_page = Configurations.TITRE_PAGE_0
            utilisateur = Configurations.UTILISATEUR_ALTERNANT
            chemin_css = Configurations.PATH_CSS

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