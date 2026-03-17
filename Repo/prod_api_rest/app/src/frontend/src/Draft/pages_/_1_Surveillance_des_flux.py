# interface/pages/1_Surveillance_des_flux.py

# Importation de librairies
import streamlit as st

# Importation de modules
from srcs.configs import Configurations
from srcs.codes_pour_interface_ui.page_standard import Page_standard
from srcs.codes_pour_senario_utilisation_app.services_d_orchestration import(
    ServiceJeuxDonneesOpendata
)
from srcs.codes_pour_senario_utilisation_app.outils_pour_les_services import (
    exiger_auth
)


def _ajouter_contenu():
    try:
        st.set_page_config(page_title="Surveillance des flux", page_icon="📡")
        exiger_auth(roles_requis=["Product_owner", "Tech_lead", "Data_analyst", "Alternant", "Alternante"])  # Pour le moment on met tout

        st.write("✅ Connecté !")

        # --- Les services | orchestre les cas d'utilisation de l'application ---
        service_des_jdds = ServiceJeuxDonneesOpendata()

        # --- Appel des service ----
        lecture_des_jdds_opendata, infos_de_lecture = service_des_jdds.lire_la_liste()

        # --- Mise dans le cache de l'application ---
        if "jdds" not in st.session_state or "jdds_infos" not in st.session_state:
            jdds = st.session_state["jdds"]
            infos = st.session_state.get("jdds_infos", [])
        else:
            # Fallback si l’utilisateur arrive directement sur cette page
            jdds, infos = lecture_des_jdds_opendata, infos_de_lecture
            st.session_state["jdds"] = jdds
            st.session_state["jdds_infos"] = infos

        st.write(f"JDDs chargés: {len(jdds)}")
        if infos:
            st.warning("\n".join(infos))

        # Affichage Pydantic v2
        st.json([j.model_dump() for j in jdds][:3])

    except Exception as e:
        st.error(f"Echec de création de table: {e}")
        
try:
    titre_page = Configurations.TITRE_PAGE_1
    utilisateur = Configurations.UTILISATEUR_ALTERNANT
    chemin_css = Configurations.PATH_CSS

    page = Page_standard(titre_page, utilisateur, chemin_css)
    page._css()
    page._barre_laterale()
    _ajouter_contenu()
    page._bas_de_page_v2()
except Exception as e:
    st.error(f"Erreur lors du chargement de la page: {e}")


