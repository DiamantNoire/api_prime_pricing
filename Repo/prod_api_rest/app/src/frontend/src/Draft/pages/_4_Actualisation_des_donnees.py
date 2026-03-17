
# /pages/_4_Actualisation_des_donnees.py
# -*- coding: utf-8 -*-

# === Importation des librairies ===
import json
import pandas as pd
import streamlit as st
import streamlit_antd_components as sac

from pathlib import Path
from datetime import datetime
from st_aggrid import AgGrid, GridOptionsBuilder

from srcs.configs import Configurations
from srcs.codes_pour_interface_ui.page_standard import Page_standard

# Use case d'actualisation (ne relit pas les sources si on lui passe un DF)
from srcs.codes_pour_senario_utilisation_app.services_d_orchestration import (
    orchestration_service_actualisation_des_donnees,
)

# Composant d’actualisation (switch manuel + état planif)
from srcs.codes_pour_interface_ui.composants_pour_pages import (
    bloc_indicateurs_et_filtres,
    composant_actualisation,
)
from srcs.codes_pour_senario_utilisation_app.outils_pour_les_services import (
    exiger_auth
)
# Tes composants anciens (si tu veux les brancher)
from srcs.codes_pour_interface_ui.composants_pour_pages import (
    details_jdd,
    panneau_debug,
    grille_alertes,
    produire_filtres,
    produire_indicateurs,
    appliquer_filtres_df,
    visuel_sur_jdds_traites,
    garantir_colonnes_de_base,
    construire_filtres_options,
    bloc_statut_global_et_top_3,
    bloc_indicateurs_et_filtres,
    normaliser_colonnes_visibilite,
    voir_toutes_les_colonnes_des_jjds
)


def _ajouter_contenu(nom_de_page: str):
    # FIX: bonne clé de session et fallback sur _disposition uniquement si absente
    layout = st.session_state.get("disposition")  # (au lieu de "diposition")
    if not layout:
        try:
            global page  # instance Page_standard créée plus haut
            layout = page._disposition(nom_de_page=nom_de_page)
            st.session_state["disposition"] = layout  # mémoriser pour les reruns
        except Exception:
            st.warning("Disposition non initialisée.")
            return

    # FIX: ne pas appeler set_page_config ici (déjà fait dans app.py)
    # st.set_page_config(page_title="Surveillance des flux", page_icon="📡")

    # Garde d'accès rôles
    exiger_auth(roles_requis=["Product_owner", "Tech_lead", "Data_analyst", "Alternant", "Alternante"])

    st.write("✅ Connecté !")

    col_gauche = layout["col_gauche"]
    col_droite = layout["col_droite"]
    details_container = layout["details_container"]

    # --- Initialisations sûres ---
    df_consolide = pd.DataFrame()
    df_enrichi = pd.DataFrame()
    indicateurs = {}

    try:
        # Lecture depuis cache (Parquet)
        parquet_path = getattr(Configurations, "SORTIE_PARQUET_JDD_PATH", None)
        if not parquet_path:
            st.error("Chemin du Parquet consolidé non défini.")
            return

        p = Path(parquet_path)
        if not p.exists():
            st.error(f"Parquet consolidé introuvable: {p}")
            return

        with st.spinner(f"Lecture du cache consolidé… ({p})"):
            df_consolide = pd.read_parquet(p)

        if df_consolide.empty:
            st.warning("Cache consolidé vide.")
            return

        # Évaluation d’actualisation (use case) sans relecture des sources
        from srcs.codes_pour_senario_utilisation_app.services_d_orchestration import (
            orchestration_service_actualisation_des_donnees
        )
        usecase = orchestration_service_actualisation_des_donnees()
        df_enrichi, analyses, indicateurs = usecase.evaluer(
            df_consolide=df_consolide,
            frequence_par_defaut_jours=30,
            tolerance_ratio=0.10,
        )

        if df_enrichi.empty:
            st.warning("DF enrichi vide après évaluation.")
            return

        # Filet de sécurité colonnes (APRÈS affectation de df_enrichi)
        for c in ["ressources_impacts_json", "ressources_par_origin_type_json", "matched_blobs_json"]:
            if c not in df_enrichi.columns:
                df_enrichi[c] = "[]"
            else:
                df_enrichi[c] = df_enrichi[c].apply(
                    lambda v: "[]" if (v is None or (isinstance(v, list) and len(v) == 0)) else (v if isinstance(v, str) else json.dumps(v, ensure_ascii=False))
                )

        for c, default in [("visibilite_publique", "false"), ("visibilite_restreinte", "false")]:
            if c not in df_enrichi.columns:
                df_enrichi[c] = default
            else:
                df_enrichi[c] = df_enrichi[c].fillna(default).astype(str)

        # Mise en session
        st.session_state["df_des_analyses"] = df_enrichi
        st.session_state["indicateurs"] = indicateurs
        st.session_state.setdefault("selecteur_producteur", [])
        st.session_state.setdefault("selecteur_frequence", [])
        st.session_state.setdefault("selecteur_visibilite_publique", "Tous")
        st.session_state.setdefault("selecteur_visibilite_restreinte", "Tous")
        st.session_state["liste_toutes_les_colonnes_jdds"] = list(df_enrichi.columns)

    except Exception as e:
        import traceback, sys
        st.error(f"[Page _4_Actualisation_des_donnees] : {e}")
        st.code("".join(traceback.format_exception(*sys.exc_info())), language="python")
        return

    # --- Colonne gauche ---
    with col_gauche:
        st.subheader("Actualisation des données — Vue consolidée (cache)")
        df = st.session_state.get("df_des_analyses", pd.DataFrame())

        # Préparation DF (helpers)
        try:
            df_prepared = normaliser_colonnes_visibilite(garantir_colonnes_de_base(df))
        except Exception:
            df_prepared = df.copy()

        # Indicateurs + filtres
        try:
            indicateurs_calc = produire_indicateurs(df_prepared)
            filtres_options = produire_filtres(df_prepared)
            bloc_indicateurs_et_filtres(
                jdds_session=st.session_state.get("jdds_odre", []),
                df_session=df_prepared,
                indicateurs_sessions=indicateurs_calc,
                filtres_options_sessions=filtres_options
            )
        except Exception as e:
            st.warning(f"[Bloc filtres] Problème: {e}")
            st.session_state["df_filtre_debug"] = df_prepared
            indicateurs_calc = {}

        df_filtre = st.session_state.get("df_filtre_debug", df_prepared)

        # Grille
        colonnes_vue = [
            "uid", "dataset_id", "title",
            "statut_actualisation",
            "ressources_count", "ressources_non_a_jour_count",
            "date_anniversaire", "age_jdd_jours",
        ]
        colonnes_vue = [c for c in colonnes_vue if c in df_filtre.columns]

        if df_filtre.empty or not colonnes_vue:
            st.warning("Aucune donnée à afficher avec les filtres.")
            st.session_state["selection_ligne_jdd"] = None
        else:
            gb = GridOptionsBuilder.from_dataframe(df_filtre[colonnes_vue].head(1000))
            gb.configure_pagination(enabled=True, paginationAutoPageSize=False, paginationPageSize=25)
            gb.configure_default_column(resizable=True, filter=True)
            gb.configure_selection('single', use_checkbox=True)
            ag = AgGrid(df_filtre[colonnes_vue], gridOptions=gb.build(), height=380, theme='material')
            selection = ag.selected_rows or []
            st.session_state["selection_ligne_jdd"] = selection[0] if selection else None

    # --- Colonne droite ---
    with col_droite:
        st.subheader("Actions d'actualisation")
        composant_actualisation(col_droite)

        # Panneau “Statut global + Top 3” si disponible
        try:
            statut_global = st.session_state.get("statut_global", "INDETERMINE")
            top_en_retard = st.session_state.get("top_en_retard", [])
            bloc_statut_global_et_top_3(
                indicateurs=indicateurs_calc or indicateurs,
                statut_global=statut_global,
                top_en_retard=top_en_retard,
                df_des_analyses=df,
                jdds_odre=st.session_state.get("jdds_odre", []),
            )
        except Exception:
            pass

    # --- Détails bas ---
    with details_container:
        st.subheader("Détails des ressources non à jour (sélection)")
        ligne = st.session_state.get("selection_ligne_jdd")
        if ligne:
            try:
                impacts_list = json.loads(ligne.get("ressources_impacts_json", "[]"))
            except Exception:
                impacts_list = []
            nb_impacts = int(ligne.get("ressources_non_a_jour_count", 0) or 0)
            st.write(f"UID: {ligne.get('uid')} • Ressources non à jour: {nb_impacts}")
            st.json(impacts_list[:20] if impacts_list else [])
        else:
            st.caption("Sélectionne une ligne dans la grille pour voir les impacts.")


def main() -> None:
    # Construction de la page
    try:
        titre_page = Configurations.TITRE_PAGE_5 
        utilisateur = Configurations.UTILISATEUR_ALTERNANT
        chemin_css = Configurations.PATH_CSS

        global page
        page = Page_standard(titre_page, utilisateur, chemin_css)

        # ⚠️ Si app.py appelle déjà _mise_en_page(), commente la ligne suivante
        # Ici on laisse pour compat standalone, mais idéalement: uniquement dans app.py
        # page._mise_en_page()

        page._css()

        # FIX: Disposition — la méthode attend le NOM DE FICHIER exact
        layout = page._disposition(nom_de_page="_4_Actualisation_des_donnees.py")
        st.session_state["disposition"] = layout  # mémorise pour la suite

        # FIX: Barre latérale — passe le LIBELLÉ exact du menu
        page._barre_laterale(page_active="Actualisation des données")

        _ajouter_contenu(nom_de_page="_4_Actualisation_des_donnees.py")
        page._bas_de_page()
    except Exception as e:
        st.error(f"Erreur lors du chargement de la page: {e}")


if __name__ == "__main__":
    main()

