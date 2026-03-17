# /pages/_4_Actualisation_des_donnees.py

# Importation des librairies
import pandas as pd
import streamlit as st
from datetime import datetime
import streamlit_antd_components as sac
from st_aggrid import AgGrid, GridOptionsBuilder


# Importation des modules
from src.config import Config
from src.interface_utilisateurs.page_standard import (
    Page_standard
)
from src.cas_d_usages_applicatifs.services import(
    CasActuatlisationsDonnees
)
from src.interface_utilisateurs._composants import _inser_tableau


def _ajouter_contenu():
    """Injecte le contenu dans les conteneurs posés par la disposition."""
    layout = st.session_state.get("layout_page_4")
    if not layout:
        st.warning("Disposition non initialisée.")
        return

    col_gauche = layout["col_gauche"]
    col_droite = layout["col_droite"]
    details_container = layout["details_container"]

    # Initialisation/chargement des données en session
    try:
        # --- 1) Service unique et clés requises ---
        service = CasActuatlisationsDonnees(chemin_parquet=Config.JDD_ODRE_PATH_PARQUET,
                                            seuils=Config.SEUILS_ALERTE,
                                            regles_frequences=Config.TYPE_FREQUENCE
        )
        JDDS_ODRE = service._charger_jdds_depuis_parquet()
        st.info(f"Taille JDDS ODRE: {len(JDDS_ODRE)}")


        # Dans ta page, après avoir chargé les JDD objets
        jdds = service._charger_jdds_depuis_parquet()

        # Comptage des labels de fréquence déclarés
        from collections import Counter
        labels = []
        for j in jdds:
            meta = j.metadonnees or {}
            labels.append(meta.get("metadata_custom_pas_temporel_value", "N/A"))
        st.write("Distribution des labels de fréquences:", Counter(labels))

        # Vérifie la proportion de labels reconnus dans TYPE_FREQUENCE
        connus = [lbl for lbl in labels if lbl in Config.TYPE_FREQUENCE and Config.TYPE_FREQUENCE.get(lbl) is not None]
        st.write("Fréquences reconnues (avec timedelta):", len(connus), "/", len(labels))


        # 3) Classement global
        classement = service.classement_global()
        st.json(classement)

        classement = service.classement_global()
        st.write(f"Classement:", classement)
        top_en_retard = classement.get("top_en_retard", [])
        les_indicateurs = classement.get("indicateurs", {})
        statut_global = classement.get("statut_global", "Aucun statut global")

        sac.divider(label='🧪 Test - Classement global', icon='experiment', align='center', color='purple', key='test_classement')
        col_a, col_b, col_c = st.columns([1,1,1])
        with col_a:
            st.metric("Statut global", statut_global)
        with col_b:
            st.metric("À jour (%)", les_indicateurs.get("pourcentage_a_jour", 0))
        with col_c:
            st.metric("En retard (%)", les_indicateurs.get("pourcentage_en_retard", 0))
        st.metric("Critiques (%)", les_indicateurs.get("pourcentage_critiques", 0))

        with st.expander("🔎 Détails classement (debug)"):
            st.json(les_indicateurs)
            st.write("Top en retard (aperçu):")
            st.write(top_en_retard[:5])


        resultats = service.analyser()
        df_des_analyses = pd.DataFrame(resultats)
        st.write(f"Analyse (5 lignes): ")
        st.dataframe(df_des_analyses.head(5), width="stretch")
    
    except Exception as e:
        st.error(f"Erreur de chargement des ressources à partir du cache: {e}")


# Construction de la page
try:
    titre_page = Config.TITRE_PAGE_4
    utilisateur = Config.UTILISATEUR_0
    chemin_css = Config.PATH_CSS
    page = Page_standard(titre_page, utilisateur, chemin_css)
    page._mise_en_page()
    page._disposition_page_actualisations_des_donnees()
    page._css()
    page._barre_laterale()
    _ajouter_contenu()
    page._bas_de_page()
except Exception as e:
    st.error(f"Erreur lors du chargement de la page: {e}")
