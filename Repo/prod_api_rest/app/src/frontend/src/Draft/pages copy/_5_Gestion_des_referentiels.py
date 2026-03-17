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
from src.config import Config
from src.couche_ui.page_standard import Page_standard
from src.couche_infra.lanceur_requetes import *

from src.couche_infra.services_techniques import (
    ServicePortApiMetada, 
    ServicePortApiRessources, 
    ServicePortExcelLocal

)

from src.couche_infra.utlisation_connecteurs import (
    ConnecteurApi, 
    ConnecteurApiRessources, 
    ConnecteurExcelLocal
)

# Ajoute le dossier racine
sys.path.append(str(Path(__file__).resolve().parent.parent))  

# Méthode pour ajouter du contenur spécifique à la page d'accueil
def _ajouter_contenu():
    try:
        # Mise en place des ports de connexion
        connecteur_api = ConnecteurApi()
        connecteur_api_ressources = ConnecteurApiRessources()
        connecteur_excel = ConnecteurExcelLocal()

        # Mise en place des services de souscriptions aux contrat d'interface pour ces ports
        service_api = ServicePortApiMetada(connecteur_api)
        service_api_ressource = ServicePortApiRessources(connecteur_api_ressources)
        service_excel = ServicePortExcelLocal(connecteur_excel)

        # Récupération des retour des contracts de souscription
        Metas = service_api.charger_metadata()
        Ressources = service_api_ressource.charger_ressources()
        blob_monitor = service_excel.charger_blob()

        # Constructions DTO
        t0 = time.perf_counter()
        metada_dto = service_api.construire_dto()
        t1 = time.perf_counter()
        ressources_dto = service_api_ressource.construire_dto()
        t2 = time.perf_counter()
        blob_dto = service_excel.construire_dto()
        t3 = time.perf_counter()

        st.caption(
              f"Perf: metadat= {t1-t0:.3f}s | "
              f"Ressources= {t2-t1:.3f}s | "
              f"Blob= {t3-t2:.3f}s"
        )

        # Teste
        st.info(
            f"Taille: Metada {len(Metas)} | "
            f"Ressources (UIDs) {len(Ressources)} | "
            f"Blob {len(blob_monitor)}"
        )

        st.info(
            f"Taille: Metada DOT {len(metada_dto)} | "
            f"Ressources (UIDs) DOT {len(ressources_dto.ressources_par_uid)} | "
            f"Blob DOT {len(blob_dto)}"
        )


        # sélection aléatoire d'un UID pour aperçu
        uid_list = list(ressources_dto.ressources_par_uid.keys())
        sample_uid = st.selectbox("Choisir un uid", uid_list, index=0)
        st.write(f"UID sélectionnée: **{sample_uid}**")
        
                # --- Aperçu Metadata ---
        with st.expander("Aperçu Métadata"):
            df_meta_filtered = Metas[Metas["uid"] == sample_uid]
            st.dataframe(df_meta_filtered)


        with st.expander("Aperçu Ressources (échantillon)"):
                        st.dataframe(ressources_dto.ressources_par_uid[sample_uid])


        # --- Aperçu Blobmonitoring ---
        with st.expander("Aperçu Blobmonitoring"):
            df_res = Ressources.get(sample_uid, pd.DataFrame())
            if "FullName" in blob_monitor.columns:
                if not df_res.empty and "title" in df_res.columns:
                    # Corrélation par inclusion : FullName contient le titre
                    matched_blob = blob_monitor[
                        blob_monitor["FullName"].apply(
                            lambda full_name: any(str(title) in full_name for title in df_res["title"].dropna())
                        )
                    ]
                    if not matched_blob.empty:
                        st.dataframe(matched_blob)
                    else:
                        st.warning("Aucun blob corrélé à cet UID (par inclusion).")
                else:
                    st.warning("Impossible de corréler : colonne 'title' absente dans ressources.")
            else:
                st.warning("Colonne FullName absente dans blob_monitor.")

        #object_cols = blob_monitor.columns.tolist()
        #st.write(object_cols)
        # Sélecteur pour explorer une colonne object
        #if object_cols:
        #    selected_col = st.selectbox("Choisir une colonne à analyser", object_cols)
        #    st.write("Exemple de valeur :", blob_monitor[selected_col].dropna().iloc[0])

    except Exception as e:
        st.exception(e) #Pour Dev
        st.error(f"Erreur: {e}")


try:
    titre_page = Config.TITRE_PAGE_5
    utilisateur = Config.UTILISATEUR_0
    chemin_css = Config.PATH_CSS

    page = Page_standard(titre_page, utilisateur, chemin_css)
    page._css()
    page._barre_laterale()
    _ajouter_contenu()
    page._bas_de_page()
except Exception as e:
    st.error(f"Erreur lors du chargement de la page: {e}")