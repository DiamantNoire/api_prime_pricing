# --- Application de supervision des jeux de données ODRE
# chemin: /page/_8_actu_data_dev_ressources_peu_visible.py
# ==== coding: utf-8 ====

# === Importation de librairies ===#
import pandas as pd
import streamlit as st
from datetime import datetime
import streamlit_antd_components as sac
from st_aggrid import AgGrid, GridOptionsBuilder


# === Importation de modules ===#
from srcs.configs import Configurations
from srcs.codes_pour_interface_ui.page_standard import Page_standard
from srcs.codes_pour_senario_utilisation_app.services_d_orchestration import(
    orchestration_service_voir_données_d_alimentation
)
from srcs.codes_pour_senario_utilisation_app.outils_pour_les_services import(
    records_en_dataframe_sur,
    applatir_jdds,
    aplatir_jdds_generique,
    exiger_auth
)




def _ajouter_contenu():
    """Injece le contenu dans le conteneurs posée par la disposition"""
    layout = st.session_state.get("layout_page_4")
    if not layout:
        st.warning(f"Dispositio non initialisée")

    col_gauche = layout["col_gauche"]
    col_droite = layout["col_droite"]
    details_container = layout["details_container"]

    # --- Donnés / Sessionn ---
    try:

        st.set_page_config(page_title="Surveillance des flux", page_icon="📡")
        exiger_auth(roles_requis=["Product_owner", "Tech_lead", "Data_analyst", "Alternant", "Alternante"])  # Pour le moment on met tout

        st.write("✅ Connecté !")


        service = orchestration_service_voir_données_d_alimentation()
        cles_sessions = ["liste_des_jdds_odre", "listes_des_jdds_format_tech_parquet", "liste_des_jdds_dataframe", "json_consolide_dict"]
        cles_sessions_filtres = ["selecteur_producteur", "selecteur_frequence", "selecteur_publique", "selecteur_restreint"]
        
        if not all(k in st.session_state for k in cles_sessions) or not all(k in st.session_state for k in cles_sessions_filtres):
            #liste_des_jdds_odre, liste_des_jdds_format_tech_parquet, liste_des_jdds_dataframe, json_consolide_dict = service.voir()
            
            liste_des_jdds_odre = service.voir_depuis_cache()
        

    # --- Affichage robuste ---
        if isinstance(liste_des_jdds_odre, pd.DataFrame):
            st.write(f"Nombre de JDD chargés : {len(liste_des_jdds_odre)}")
            cols = liste_des_jdds_odre.columns.tolist()   # CORRECTION: .tolist()
            st.write(f"Nombre total de colonnes : {len(cols)}")
            st.json({"colonnes": cols})

            if not liste_des_jdds_odre.empty:
                st.dataframe(liste_des_jdds_odre.head(50))
            else:
                st.info("Le DataFrame est vide. Vérifiez le cache (parquet/json) et la configuration.")

        elif isinstance(liste_des_jdds_odre, (list, tuple)):
            # Cas où voir_depuis_cache() retourne une liste de dicts (PyArrow)
            st.write(f"Nombre de JDD chargés : {len(liste_des_jdds_odre)}")
    
            # Filtrer la liste avant affichage
            filtre_liste = [
                rec for rec in liste_des_jdds_odre
                if isinstance(rec, dict)
                and str(rec.get("has_sources_externes_pda_opendata_monitoring_bool", "")).lower() == "true"
                and int(rec.get("ressources_count", 0)) > 0
            ]

            # Afficher 3 éléments complets en JSON brut
            st.write("✅ Extrait complet (3 lignes filtrées) :")
            for i, item in enumerate(filtre_liste[:3]):
                st.json(item)


            # Afficher un extrait JSON du premier élément
            if len(liste_des_jdds_odre) > 0 and isinstance(liste_des_jdds_odre[0], dict):
                st.json(liste_des_jdds_odre[0])
                # Option: convertir en DataFrame pour afficher les colonnes
                df_tmp = records_en_dataframe_sur(liste_des_jdds_odre)
                cols = df_tmp.columns.tolist()
                st.write(f"Nombre total de colonnes : {len(cols)}")
                st.json({"colonnes": cols})
                st.dataframe(df_tmp.head(50))
            else:
                st.info("Liste vide ou non composée de dictionnaires.")
            df_teste = pd.DataFrame(liste_des_jdds_odre)

            # Afficher infos
            st.write(f"Nombre de lignes : {len(df_teste)}")
            st.write(f"Nombre de colonnes : {len(df_teste.columns)}")
            st.json({"colonnes": df_teste.columns.tolist()})

        else:
            st.warning(f"Type inattendu pour 'liste_des_jdds_odre': {type(liste_des_jdds_odre)}")

    except Exception as e:
        st.error(f"[Page _7_actu_data_dev | service.avoir ] {e}")


# Construction de la page
try:
    titre_page = Configurations.TITRE_PAGE_4
    utilisateur = Configurations.UTILISATEUR_ALTERNANT
    chemin_css = Configurations.PATH_CSS
    page = Page_standard(titre_page, utilisateur, chemin_css)
    page._mise_en_page()
    page._disposition_page_actualisations_des_donnees()
    page._css()
    page._barre_laterale()
    _ajouter_contenu()
    page._bas_de_page_v2()
except Exception as e:
    st.error(f"Erreur lors du chargement de la page: {e}")


