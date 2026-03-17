# interface/pages/_5_Gestion_des_referentiels.py

# - Importation de librairies
import sys
import time
import requests
import random
import pandas as pd
import streamlit as st
from pathlib import Path

# - Importation de modules
from srcs.configs import Configurations
from srcs.codes_pour_interface_ui.page_standard import Page_standard
from srcs.codes_pour_senario_utilisation_app.services_d_orchestration import(
    ServiceJeuxDonneesOpendata
)
from srcs.codes_pour_senario_utilisation_app.outils_pour_les_services import(
    exiger_auth
)

def _ajouter_contenu():
    try:
        
        exiger_auth(roles_requis=["Product_owner", "Tech_lead", "Data_analyst", "Alternant", "Alternante"])  # Pour le moment on met tout

        st.write("✅ Connecté !")
        # Service
        service_des_jdds = ServiceJeuxDonneesOpendata()
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

        # Bouton de rafraîchissement -> relance la lecture et met à jour session
        if st.button("🔁 Rafraîchir les JDDs"):
            jdds, infos = service_des_jdds.lire_la_liste()
            st.session_state["jdds"] = jdds
            st.session_state["jdds_infos"] = infos
            st.toast("JDDs rafraîchis.", icon="🔁")

        st.write(f"JDDs chargés : **{len(jdds)}**")
        if infos:
            st.warning("\n".join(infos))

        # Affichage Pydantic v2
        st.json([j.model_dump() for j in jdds][:3])

    except Exception as e:
        st.error(f"Echec de création de table: {e}")



def main() -> None:

    try:
        titre_page = Configurations.TITRE_PAGE_6
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