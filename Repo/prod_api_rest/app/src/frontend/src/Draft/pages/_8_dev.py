# --- Application de supervision des jeux de données ODRE
# chemin: /page/_8_dev.py
# ==== coding: utf-8 ====

# === Importation de librairies ===#
import bcrypt
import pandas as pd
import streamlit as st
from datetime import datetime
import streamlit_antd_components as sac
from typing import Dict, Optional, List, Any
from st_aggrid import AgGrid, GridOptionsBuilder


# === Importation de modules ===#
from srcs.configs import Configurations
from srcs.codes_pour_metier_admin_jdd_odre_app.modelisation_jdd_odre import JddOdre
from srcs.codes_pour_interface_ui.page_standard import Page_standard
from srcs.codes_pour_senario_utilisation_app.services_d_orchestration import(
    ServiceJeuxDonneesOpendata,
    ServiceActualisationJdds
)
from srcs.codes_pour_senario_utilisation_app.outils_pour_les_services import(
    exiger_auth
)

def _ajouter_contenu():
    try:
        exiger_auth(roles_requis=["Product_owner", "Tech_lead", "Data_analyst", "Alternant", "Alternante"])  # Pour le moment on met tout
        st.write("✅ Connecté !")

        # --- Les services | orchestre les cas d'utilisation de l'application ---
        service_des_jdds = ServiceJeuxDonneesOpendata()

        # Service
        service_des_jdds = ServiceJeuxDonneesOpendata()
        lecture_des_jdds_opendata: List[JddOdre] = []
        infos_de_lecture: List[str] = []
        lecture_des_jdds_opendata, infos_de_lecture = service_des_jdds.lire_la_liste()

        # --- Cache session sécurisé ---
        # Cas 1 : déjà en session -> on consomme
        if "jdds" in st.session_state and "jdds_infos" in st.session_state:
            jdds = st.session_state["jdds"]
            infos = st.session_state["jdds_infos"]
        else:
            # Cas 2 : première visite -> on alimente et on stocke
            jdds, infos = lecture_des_jdds_opendata, infos_de_lecture
            st.session_state["jdds"] = jdds
            st.session_state["jdds_infos"] = infos

            
    # ---- Paramètres UI (facultatif) ----
        with st.sidebar:
            freq_defaut = st.selectbox(
                "Fréquence par défaut (fallback)",
                options=["Mensuel", "Annuel", "Hebdomadaire", "Journalier", "Horaire", "Trimestriel"],
                index=0,
            )
            tol_pct = st.slider("Tolérance override (+%)", 0, 50, value=0, step=5)
            tol_ratio = tol_pct / 100.0 if tol_pct > 0 else None
            st.caption("Si laissé à 0%, on prend la règle 'attention' de la configuration.")

        # ---- Appel du service ----
        service = ServiceActualisationJdds()
        resultat = service.analyser_liste(
            jdds=jdds,
            frequence_defaut_clef=freq_defaut,
            tolerance_override=tol_ratio,  # None => prend REGLES_FREQUENCES[clé]['attention'] - 1.0
        )

        items = resultat["items"]
        df = resultat["df"]

        # ---- Indicateurs ----
        c1, c2, c3 = st.columns(3)
        c1.metric("JDD analysés", len(df))
        c2.metric("JDD à jour", int((df["statut"] == "à jour").sum()) if not df.empty else 0)
        c3.metric("JDD pas à jour", int((df["statut"] == "pas à jour").sum()) if not df.empty else 0)

        # ---- Tableau ----
        st.subheader("Vue par JDD")
        if df.empty:
            st.info("Pas de données à afficher.")
        else:
            st.dataframe(df, use_container_width=True)

        # ---- Détails bruts (debug) ----
        with st.expander("Détails bruts (items)"):
            st.json(items[:50])
        
        with st.expander("Teste le lecture des jdds"):
            st.json(jdds[:3])
        

    except Exception as e:
        st.error(f"Echec de création de table: {e}")
        


def main() -> None:

    try:
        titre_page = "_8_dev"
        utilisateur = Configurations.UTILISATEUR_ALTERNANT
        chemin_css = Configurations.PATH_CSS

        page = Page_standard(titre_page, utilisateur, chemin_css)
        page._css()
        page._barre_laterale()
        _ajouter_contenu()
        page._bas_de_page()
    except Exception as e:
        st.error(f"Erreur lors du chargement de la page: {e}")

if __name__ == "__main__":
    main()
    