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
    orchestration_service_alimenter_cache_app_en_data,
    orchestration_service_voir_données_d_alimentation
)
from srcs.codes_pour_interface_ui.composants_pour_pages import(
    composant_actualisation
)
from srcs.codes_pour_senario_utilisation_app.outils_pour_les_services import (
    exiger_auth
)

def _ajouter_contenu():
# --- Données / session ---
    try:
        exiger_auth(roles_requis=["Product_owner", "Tech_lead", "Data_analyst", "Alternant", "Alternante"])  # Pour le moment on met tout

        st.write("✅ Connecté !")


        st.info("Initialisation des services…")
        # 1) Instanciation des services (log types)
        try:
            service_alimentation_en_data = orchestration_service_alimenter_cache_app_en_data()
            st.write("✅ service_alimentation_en_data initialisé:", type(service_alimentation_en_data).__name__)
        except Exception as e:
            st.exception(f"❌ Échec init service_alimentation_en_data: {e}")
            return

        try:
            service_visualiser_data = orchestration_service_voir_données_d_alimentation()
            st.write("✅ service_visualiser_data initialisé:", type(service_visualiser_data).__name__)
        except Exception as e:
            st.exception(f"❌ Échec init service_visualiser_data: {e}")
            return

        # 2) Appel à .voir() instrumenté
        with st.spinner("Chargement des données (service_visualiser_data.voir)…"):
            try:
                retour = service_visualiser_data.voir()
            except Exception as e:
                import traceback, sys
                st.error("❌ Exception levée dans service_visualiser_data.voir()")
                st.code("".join(traceback.format_exception(*sys.exc_info())), language="python")
                return

        # 3) Validation structure du retour
        if not isinstance(retour, (list, tuple)) or len(retour) != 4:
            st.error(f"❌ Retour inattendu de .voir(): type={type(retour)}, len={getattr(retour,'__len__',lambda: 'n/a')()}")
            st.write("Valeur brute:", retour)
            return

        (
            liste_des_jdds_odre,
            liste_des_jdds_format_tech_parquet,
            liste_des_jdds_dataframe,
            json_consolide_dict
        ) = retour

        st.success("✅ service_visualiser_data.voir() OK")
        st.write("Test")  # Ta ligne de test

        # 4) Logs rapides sur le contenu renvoyé
        st.caption(f"📦 jdds_odre: {len(liste_des_jdds_odre)} éléments")
        st.caption(f"🗂️ format_tech_parquet keys: {list(liste_des_jdds_format_tech_parquet.keys())[:5]} …")
        if isinstance(liste_des_jdds_dataframe, dict):
            st.caption(f"📊 dataframes keys: {list(liste_des_jdds_dataframe.keys())}")
        else:
            st.error(f"❌ liste_des_jdds_dataframe n'est pas un dict: {type(liste_des_jdds_dataframe)}")

        # 5) Contrôle DF consolidé + colonnes sensibles
        df_consolide = pd.DataFrame()
        if isinstance(liste_des_jdds_dataframe, dict):
            df_consolide = liste_des_jdds_dataframe.get("catalogue_ressources_blob", pd.DataFrame())
        st.write("DF consolidé shape:", df_consolide.shape)

        # colonnes sensibles
        for col in ["uid", "ressources_json", "matched_blobs_json",
                    "has_sources_externes_pda_opendata_monitoring"]:
            st.write(f"• Colonne '{col}' présente ? ", col in df_consolide.columns)

        # (Optionnel) affichage d’un échantillon
        if not df_consolide.empty:
            st.dataframe(df_consolide.head(5))

    except Exception as e:
        # 6) Exception de plus haut niveau (fallback)
        import traceback, sys
        st.error(f"[Page _6_Actu_dev] : {e}")
        st.code("".join(traceback.format_exception(*sys.exc_info())), language="python")
        return

def main() -> None:

    # === Construction de la page ===
    try:
        titre_page = "_6_dev"
        utilisateur = Configurations.UTILISATEUR_ALTERNANT
        chemin_css = Configurations.PATH_CSS
        page = Page_standard(titre_page, utilisateur, chemin_css)
        page._mise_en_page()
        page._disposition(nom_de_page=titre_page)
        page._css()
        page._barre_laterale()
        _ajouter_contenu()
        page._bas_de_page_v2()
    except Exception as e:
        st.error(f"Erreur lors du chargement de la page: {e}")

if __name__ == "__main__":
    main()