
# interface/pages/1_Surveillance_des_flux.py
# -*- coding: utf-8 -*-

import streamlit as st

from srcs.configs import Configurations
from srcs.codes_pour_interface_ui.page_standard import Page_standard
from srcs.codes_pour_senario_utilisation_app.services_d_orchestration import (
    ServiceJeuxDonneesOpendata,
    ServiceSourcesExternes,
    orchestration_service_alimenter_cache_app_en_data,
    orchestrer_alimentation_de_l_app
)
from srcs.codes_pour_sources_externes_app.entrees_sorties_app import(
    AdaptateurSourcesExternes
)
from srcs.codes_pour_senario_utilisation_app.outils_pour_les_services import exiger_auth
from srcs.codes_pour_metier_admin_jdd_odre_app.ports_abstraits_connexions_aux_sources_externes import(
    PortAbstraitRecupererJdd0dre
)

def _ajouter_contenu():
    try:
        # ❌ Ne pas appeler st.set_page_config ici (déjà fait dans app.py)
        # st.set_page_config(page_title="Surveillance des flux", page_icon="📡")

        # Guard d'accès par rôles
        exiger_auth(roles_requis=["Product_owner", "Tech_lead", "Data_analyst", "Alternant", "Alternante"])


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
        titre_page = Configurations.TITRE_PAGE_2
        utilisateur = Configurations.UTILISATEUR_ALTERNANT
        chemin_css = Configurations.PATH_CSS

        page = Page_standard(titre_page, utilisateur, chemin_css)
        page._css()
        page._barre_laterale(page_active=titre_page)
        _ajouter_contenu()
        page._bas_de_page()
    except Exception as e:
        st.error(f"Erreur lors du chargement de la page: {e}")


if __name__ == "__main__":
    main()
