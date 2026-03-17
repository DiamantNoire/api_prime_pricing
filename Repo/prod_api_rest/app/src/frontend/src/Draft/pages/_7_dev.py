# --- Application de supervision des jeux de données ODRE
# chemin: /page/_7_actu_data_dev.py
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
from srcs.codes_pour_metier_admin_jdd_odre_app.modelisation_jdd_odre import (
    JddOdre
)
from srcs.codes_pour_interface_ui.page_standard import (
    Page_standard
)
from srcs.codes_pour_senario_utilisation_app.services_d_orchestration import(
    ServiceJeuxDonneesOpendata,
    ServiceActualisationJdds
)

from srcs.codes_pour_senario_utilisation_app.outils_pour_les_services import(
    exiger_auth
)


def _ajouter_contenu():
    try:
        exiger_auth(roles_requis=["Product_owner", "Tech_lead", "Data_analyst", "Alternant", "Alternante"])
        st.write("✅ Connecté !")

        disposition = st.session_state.get("disposition")
        if not disposition:
            st.warning("Disposition non initialisée")
            return
        colonne_de_gauche = disposition["col_gauche"]
        colonne_de_droite = disposition["col_droite"]
        colonne_de_details = disposition["col_details"]

        service_de_recuperation_jdds = ServiceJeuxDonneesOpendata()
        service_d_analyse_actualisation = ServiceActualisationJdds()

        liste_jdds: List[JddOdre]
        analyse_listes_jdds: Dict[str, Any] = {}
        liste_jdds, _ = service_de_recuperation_jdds.lire_la_liste()
        analyse_listes_jdds = service_d_analyse_actualisation.analyser_liste(jdds=liste_jdds)

        par_items: Dict[str, Any] = {}
        par_df : pd.DataFrame = pd.DataFrame()

        par_items: Dict[str, Any] = analyse_listes_jdds["items"]
        par_df = analyse_listes_jdds["df"]

        st.write(f"JDDs analysés sous forme de dict : **{len(par_items)}**")

        # Affichage Pydantic v2
        st.json(par_df.to_dict(orient="records"))



    except Exception as e:
        st.error(f"Echec dans _ajouter_contenu: {e}")



def main() -> None:

    try:
        titre_page = "_7_dev"
        utilisateur = Configurations.UTILISATEUR_ALTERNANT
        chemin_css = Configurations.PATH_CSS

        page = Page_standard(titre_page, utilisateur, chemin_css)
        page._mise_en_page()
        page._css()
        page._barre_laterale()

        disposition = page._disposition(nom_de_page=Configurations.TITRE_PAGE_3)
        st.session_state["disposition"] = disposition or st.session_state.get("disposition", {})
        
        _ajouter_contenu()
        page._bas_de_page()

    except Exception as e:
        st.error(f"Erreur lors du chargement de la page: {e}")

if __name__ == "__main__":
    main()
    