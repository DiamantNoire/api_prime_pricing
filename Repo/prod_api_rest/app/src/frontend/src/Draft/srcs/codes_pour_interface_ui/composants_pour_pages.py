# --- Application de supervision des jeux de données ODRE 
# chemin: srcs/codes_pour_interface_ui/composants_pour_pages.py
# ==== coding: utf-8 ====

# === Importation de librairies ===
from __future__ import annotations
import html
import math

import streamlit as st
import pandas as pd

from typing import Dict, Any, List, Optional
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Optional, Tuple
import streamlit_antd_components as sac
from st_aggrid import AgGrid, GridOptionsBuilder

from datetime import datetime, time
from zoneinfo import ZoneInfo
from typing import Dict, Any, List, Optional
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode


# === Importation de modules ===
from srcs.configs import Configurations
from srcs.codes_pour_metier_admin_jdd_odre_app.modelisation_jdd_odre import JddOdre



# ------------- Composants pour la page standard --------------------------




# ------------- Composants pour la page Actualisation des données --------------------------

def produire_indicateur_restriction(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Docstring for produire_indicateurs
    
    :param df: Description
    :type df: pd.DataFrame
    :return: Description
    :rtype: Dict[str, Any]
    """
    nb_jdd = len(df)
    nb_restreint_oui = int((df["is_restricted"] == True).sum())
    nb_restreint_non = int((df["is_restricted"] == False).sum())

    return {
        "nb_jdd": nb_jdd,
        "nb_restreint_oui": nb_restreint_oui,
        "nb_restreint_non": nb_restreint_non,
    }

def appliquer_filtres(df: pd.DataFrame) -> pd.DataFrame:
    """Applique les filtres UI (producteur, fréquence, visibilité) présents dans la session."""
    if df is None or df.empty:
        return pd.DataFrame()

    out = df.copy()

    # Filtre Producteur
    selecteur_producteur = st.session_state.get("selecteur_producteur", [])
    if selecteur_producteur and "metadata_default_publisher_value" in out.columns:
        def _match_any_pub(pub_val) -> bool:
            if pd.isna(pub_val):
                return False
            txt = str(pub_val)
            return any(prod.strip() in txt for prod in selecteur_producteur)
        out = out[out["metadata_default_publisher_value"].apply(_match_any_pub)]

    # Filtre Fréquence
    selecteur_frequence = st.session_state.get("selecteur_frequence", [])
    if selecteur_frequence and "clef_frequence" in out.columns:
        out = out[out["clef_frequence"].astype(str).isin([f.strip() for f in selecteur_frequence])]

    # Filtre Visibilité
    selecteur_visibilite = st.session_state.get("selecteur_visibilite", "Tous")
    if selecteur_visibilite in ("Public", "Restreint") and "visibilite" in out.columns:
        out = out[out["visibilite"] == selecteur_visibilite]

    return out

def appliquer_filtres_df(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # Producteur
    sel_prod = st.session_state.get("selecteur_producteur", [])
    if sel_prod:
        df = df[df["metadata_default_publisher_value"].astype(str).isin(sel_prod)]

    # Fréquence
    sel_freq = st.session_state.get("selecteur_frequence", [])
    if sel_freq:
        df = df[df["clef_frequence"].astype(str).isin(sel_freq)]


    # Visibilité restreinte (indépendante)
    choix_res = st.session_state.get("selecteur_visibilite_restreinte", "Tous")
    if choix_res == "Restreint":
        df = df[df["is_restricted"].astype(str).str.strip().str.lower() == "true"]
    elif choix_res == "Public":
        df = df[df["is_restricted"].astype(str).str.strip().str.lower() == "false"]

    return df


# ---------- Blocs UI ---------- #

# --- Colonne gauche --- #

# --- Fonction utilse --- #
def valeurs_uniques_df(df: pd.DataFrame) -> List[Any]:
    uniques = set()
    for col in df.columns:
        uniques.update(df[col].dropna().unique().tolist())
    return sorted(map(str, uniques))

def produire_filtres(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Génère des options de filtres triées, nettoyées et UNIQUES par colonne.
    Ajout : éclate les producteurs séparés par virgule.
    """

    PLACEHOLDER = "— Aucun(e) —"

    def _serie(df: pd.DataFrame, col: str) -> pd.Series:
        return df[col] if col in df.columns else pd.Series(dtype="object")

    def _dedupe(values: List[str]) -> List[str]:
        """Déduplication insensible à la casse, conserve la première occurrence."""
        seen = set()
        uniques = []
        for v in values:
            key = v.lower()
            if key not in seen:
                seen.add(key)
                uniques.append(v)
        return uniques

    def _nettoyer(vals: pd.Series) -> List[str]:
        """Nettoie, remplace NaN, strip, dedupe, tri."""
        if vals.empty:
            return []
        
        PLACEHOLDER_accrualperiodicity_value = "-- Aucune --"
        vals = vals.astype(str).map(lambda x: x.strip())
        vals = vals.replace(
            {"": PLACEHOLDER_accrualperiodicity_value, 
             "nan": PLACEHOLDER_accrualperiodicity_value, 
             "None": PLACEHOLDER_accrualperiodicity_value, 
             "NONE": PLACEHOLDER_accrualperiodicity_value
            }
        )

        uniques = _dedupe(vals.tolist())
        uniques = sorted(uniques, key=lambda x: x.lower())

        if PLACEHOLDER in uniques:
            uniques = [PLACEHOLDER] + [v for v in uniques if v != PLACEHOLDER]

        return uniques

    # Spécifique aux producteurs : éclatement par virgule
    def _nettoyer_producteurs(vals: pd.Series) -> List[str]:
        if vals.empty:
            return []
        liste = []
        for raw in vals.astype(str):
            if raw in ("", "nan", "None"):
                liste.append(PLACEHOLDER)
                continue
            morceaux = [p.strip() for p in raw.split(",")]
            liste.extend(morceaux)

        # Déduplication + tri
        liste = _dedupe(liste)
        liste = sorted(liste, key=lambda x: x.lower())

        if PLACEHOLDER in liste:
            liste = [PLACEHOLDER] + [v for v in liste if v != PLACEHOLDER]

        return liste

    def _opt_restriction() -> List[str]:
        s = _serie(df, "is_restricted")
        opts_res = []
        for val in s:
            opts_res.append("Restreint" if bool(val) else "Public")

        return list(dict.fromkeys(opts_res))

    # --- Retour final ---
    return {
        "is_restricted": _opt_restriction(),
        "metadata_default_title_value": _nettoyer(_serie(df, "metadata_default_title_value")),
        "metadata_dcat_accrualperiodicity_value": _nettoyer(_serie(df, "metadata_dcat_accrualperiodicity_value")),
        "metadata_default_publisher_value": _nettoyer_producteurs(_serie(df, "metadata_default_publisher_value")),
    }

# ===> Bloc valide
def bloc_indicateurs_et_filtres(df_analyse: pd.DataFrame) -> None:
    """
    """
    try:
        df = df_analyse.copy()
        filtres_options = produire_filtres(df)

        sac.divider(label='🧭 Filtres', icon='filter', align='center', color='blue', key="Filtre")

        # -- Préparation des options -- #
        producteurs_options = filtres_options.get("metadata_default_publisher_value", [])
        VALEUR_PRODUCTEUR_PAR_DEFAUT = "NaTran"
        producteur_par_default = VALEUR_PRODUCTEUR_PAR_DEFAUT if VALEUR_PRODUCTEUR_PAR_DEFAUT in producteurs_options else None

        frequences_options = filtres_options.get("metadata_dcat_accrualperiodicity_value", [])
        VALEUR_FREQUENCE_PAR_DEFAUT = "Annuelle"
        frequence_par_default = VALEUR_FREQUENCE_PAR_DEFAUT if VALEUR_FREQUENCE_PAR_DEFAUT in frequences_options else None

        # Visibilités
        restrictions_options = filtres_options.get("is_restricted", [])
        VALEUR_RESTRICTION_PAR_DEFAUT = "Public"
        restriction_par_default = VALEUR_RESTRICTION_PAR_DEFAUT if VALEUR_RESTRICTION_PAR_DEFAUT in restrictions_options else None


        # -- Initialisation des valeurs en session (1ère exécution uniquement) -- #
        if "selecteur_producteur" not in st.session_state:
            st.session_state["selecteur_producteur"] = [producteur_par_default] if producteur_par_default else []

        if "selecteur_frequence" not in st.session_state:
            st.session_state["selecteur_frequence"] = [frequence_par_default] if frequence_par_default else []

        if "selecteur_visibilite_restreinte" not in st.session_state:
            st.session_state["selecteur_visibilite_restreinte"] = restriction_par_default


        # -- on s'assure que la sélection est incluse dans les options -- #
        st.session_state["selecteur_producteur"] = [
            v for v in st.session_state["selecteur_producteur"] if v in producteurs_options
        ]
        st.session_state["selecteur_frequence"] = [
            v for v in st.session_state["selecteur_frequence"] if v in frequences_options
        ]
        if st.session_state["selecteur_visibilite_restreinte"] not in restrictions_options:
            st.session_state["selecteur_visibilite_restreinte"] = None

        # -- Application des filtres  -- #
        df_filtre = appliquer_filtres_df(df)
                
        st.session_state["df_filtre_debug"] = df_filtre.copy()  

        # KPI dynamiques
        indicateurs_filtres = produire_indicateur_restriction(df_filtre)
        total_jdd = indicateurs_filtres.get("nb_jdd", len(df_filtre))
        nb_restreint_oui = indicateurs_filtres.get("nb_restreint_oui", 0)
        nb_restreint_non = indicateurs_filtres.get("nb_restreint_non", 0)

        # Rendu KPI
        st.markdown(
            f"""
            <table class="kpi-modern-premium" style="width:100%; border-collapse:collapse;">
            <tbody>
                <tr class="row-total">
                <td colspan="4" style="text-align:center;">
                    <span class="kpi-total">📊 JDD(s) total :</span>
                    <span class="kpi-total">{len(df)}</span>
                </td>
                </tr>
                <tr>
                <td class="kpi-restreint">🛡️ Restreint</td>
                <td class="val-restreint">{nb_restreint_oui}</td>
                <td class="kpi-nonrestreint">✅ Public</td>
                <td class="val-nonrestreint">{nb_restreint_non}</td>
                </tr>
                <tr>
                <td class="kpi-restreint">🧭 Filtrage</td>
                <td class="val-filtrage">{total_jdd} lignes</td>
                <td class="kpi-nonrestreint">Sur</td>
                <td class="val-lignes_init">{len(df)} initiales</td>
                </tr>
            </tbody>
            </table>
            """,
            unsafe_allow_html=True
        )

        # -- Disposition des éléments -- #
        ligne_1_col0, ligne_1_col1 = st.columns(2)
        with ligne_1_col0:
            # Filtre pour les producteurs
            st.multiselect(
                label="Par producteurs",
                options=producteurs_options,
                accept_new_options=True,
                placeholder="Choisir un producteur Ex: NaTran",
                key="selecteur_producteur",
            )

        with ligne_1_col1:
            # Filtre pour la fréquence de mise à jour
            st.multiselect(
                label="Par fréquence",
                options=frequences_options,
                accept_new_options=False,
                placeholder="Choisir une ou plusieurs fréquences",
                key="selecteur_frequence",
            )

        ligne_2_col0, ligne_2_col1 = st.columns(2)
        with ligne_2_col0:
            # Filtre pour restriction
            st.selectbox(
                "Visibilité restreinte",
                placeholder="Choisir une restriction",
                options=restrictions_options,
                key="selecteur_visibilite_restreinte",
            )

        with ligne_2_col1:
            # Bouton de réinitialisation de tous les filtres
            def _reset_all():
                st.session_state["selecteur_producteur"] = []
                st.session_state["selecteur_frequence"] = []
                st.session_state["selecteur_visibilite_restreinte"] = None
                # Optionnel : forcer le rerun immédiat (souvent pas nécessaire)
                # st.rerun()

            st.button(
                label="↺ Réinitialiser tous les filtres",
                on_click=_reset_all,
            )
    except Exception as e:
        st.error(f"Erreur: {e}")

# ===> Bloc de dev testé à supprimer
def bloc_indicateurs_et_filtres_0(df_des_analyses: pd.DataFrame) -> None:
    """Affiche les indicateurs compacts et les filtres (Producteur + Fréquence + Visibilité)."""
    sac.divider(label='📈 Indicateurs', icon='line_chart', align='center', color='green', key="Indicateurs")

    df = df_des_analyses.copy()

    def _to_bool(x):
        """Convertit robustement x en booléen (True/False), None -> None."""
        if isinstance(x, bool):
            return x
        if x is None:
            return None
        s = str(x).strip().lower()
        if s in {"true", "1", "oui", "yes"}:
            return True
        if s in {"false", "0", "non", "no"}:
            return False
        return None  # inconnu

    def _derive_visibilite_from_row(row) -> str:
        """
        Déduit 'Public'/'Restreint' à partir:
        - visibilite existante si présente,
        - colonnes is_published / is_restricted,
        - ou dict metadonnes['is_published'] / ['is_restricted'].
        """
        # 1) Si 'visibilite' existe déjà, normaliser éventuelles variantes
        if "visibilite" in row and pd.notna(row["visibilite"]):
            s = str(row["visibilite"]).strip().lower()
            if s in {"public"}:
                return "Public"
            if s in {"restreint"}:
                return "Restreint"
            # sinon tenter de re-dériver via published/restricted

        # 2) Colonnes dédiées au niveau top (si présentes)
        is_pub = _to_bool(row.get("is_published")) if "is_published" in row else None
        is_res = _to_bool(row.get("is_restricted")) if "is_restricted" in row else None
        if is_pub is not None or is_res is not None:
            # règles: restricted True => Restreint ; else published True => Public ; sinon Restreint
            if is_res is True:
                return "Restreint"
            if is_pub is True:
                return "Public"
            return "Restreint"

        # 3) Dans le dict 'metadonnes' (si colonne présente)
        meta = row.get("metadonnes")
        if isinstance(meta, dict):
            is_pub = _to_bool(meta.get("is_published"))
            is_res = _to_bool(meta.get("is_restricted"))
            if is_res is True:
                return "Restreint"
            if is_pub is True:
                return "Public"
            return "Restreint"

        # 4) Fallback
        return "Restreint"

    if not df.empty:
        if "visibilite" in df.columns:
            df["visibilite"] = df.apply(_derive_visibilite_from_row, axis=1)
        else:
            df["visibilite"] = "Restreint"

        if "producteur" in df.columns:
            df["producteur"] = df["producteur"].apply(lambda v: "" if v is None else str(v).strip())
        else:
            df["producteur"] = ""

        if "frequence" in df.columns:
            df["frequence"] = df["frequence"].apply(lambda v: "" if v is None else str(v).strip())

    # --- KPI ---
    total_all = len(df)
    n_public = int((df["visibilite"] == "Public").sum()) if "visibilite" in df.columns else 0
    n_restreint = int((df["visibilite"] == "Restreint").sum()) if "visibilite" in df.columns else 0

    total_all = len(df_des_analyses)
    n_public = int((df_des_analyses["visibilite"] == "Public").sum()) if "visibilite" in df_des_analyses.columns else 0
    n_restreint = int((df_des_analyses["visibilite"] == "Restreint").sum()) if "visibilite" in df_des_analyses.columns else 0


    # --- Rangée 2 : deux colonnes (Public / Restreint) via classes CSS ---
    st.markdown(
        f"""
        <div class="kpi kpi-row">
          <div><span class="kpi__value">📊 {total_all}</span>JDD</div>
          <div><span class="badge badge--public">Public: {n_public}</span></div>
          <div><span class="badge badge--restreint">Restreint: {n_restreint}</span></div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # --------- Filtres ----------
    sac.divider(label='🧭 Filtres', icon='filter', align='center', color='blue', key="Filtre")

    # 1) Producteurs (multiselect)
    if "producteur" in df_des_analyses.columns:
        producteurs_options = sorted(set(df["producteur"].dropna().astype(str).str.strip().tolist()))
    else:
        producteurs_options = []

    st.multiselect(
        "Par producteurs",
        options=producteurs_options,
        accept_new_options=True,
        placeholder="Choisir un producteur. Ex: NATRAN",
        key="selecteur_producteur",
    )

    # 2) Fréquence (multiselect)
    if "frequence" in df_des_analyses.columns:
        freqs_options = sorted(set(df["frequence"].dropna().astype(str).str.strip().tolist()))
    else:
        freqs_options = []
    st.multiselect(
        "Par fréquence",
        options=freqs_options,
        accept_new_options=False,
        placeholder="Choisir une ou plusieurs fréquences",
        key="selecteur_frequence",
    )

    # 3) Visibilité (selectbox, pas de radio)
    # Valeurs possibles: Tous / Public / Restreint
    vis_options = ["Tous", "Public", "Restreint"]
    vis_default = st.session_state.get("selecteur_visibilite", "Tous")
    st.selectbox(
        "Par visibilité",
        options=vis_options,
        index=vis_options.index(vis_default) if vis_default in vis_options else 0,
        key="selecteur_visibilite",
        help="Filtre sur is_published projeté (Public ou Restreint).",
    )

    # Bouton unique: Réinitialiser tous les filtres
    def _reset_all():
        st.session_state["selecteur_producteur"] = []
        st.session_state["selecteur_frequence"] = []
        st.session_state["selecteur_visibilite"] = "Tous"

    st.button("↺ Réinitialiser tous les filtres", on_click=_reset_all)

def bloc_indicateurs_et_filtres_1(jdds_session: Any,
                                df_session: Any,
                                indicateurs_sessions: Any,
                                filtres_options_sessions: Any
    ) -> None:
    """Affiche les indicateurs compacts et les filtres (Producteur + Fréquence + Visibilité)."""
    sac.divider(label='📈 Indicateurs', icon='line_chart', align='center', color='green', key="Indicateurs")

    df = df_session.copy()

    # --- KPI ---
    total_jdd = indicateurs_sessions["nb_jdd"]
    nb_public_oui = indicateurs_sessions["nb_public_oui"]
    nb_public_non = indicateurs_sessions["nb_public_non"]
    nb_restreint_oui = indicateurs_sessions["nb_restreint_oui"]
    nb_restreint_non = indicateurs_sessions["nb_restreint_non"]


    # --- Rangée 2 : deux colonnes (Public / Restreint) via classes CSS ---
    st.markdown(
        f"""
        <div class="kpi kpi-center">
          <div><span class="kpi__value">📊 {total_jdd}</span>JDD</div>
        </div>
        <div class="kpi kpi-center">
          <div><span class="badge badge--public">Public: {nb_public_oui}</span></div>
          <div><span class="badge badge--restreint">Non public: {nb_public_non}</span></div>
        </div>
        <div class="kpi kpi-center">
          <div><span class="badge badge--public">Restreint: {nb_restreint_oui}</span></div>
          <div><span class="badge badge--restreint">Non restreint: {nb_restreint_non}</span></div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # --------- Filtres ----------
    sac.divider(label='🧭 Filtres', icon='filter', align='center', color='blue', key="Filtre")

    # 1) Producteurs (multiselect)
    if "producteur" in df.columns:
        producteurs_options = filtres_options_sessions["producteur"]
    else:
        producteurs_options = []

    st.multiselect(
        "Par producteurs",
        options=producteurs_options,
        accept_new_options=True,
        placeholder="Choisir un producteur. Ex: NATRAN",
        key="selecteur_producteur",
    )

    # 2) Fréquence (multiselect)
    if "frequence" in df.columns:
        freqs_options = filtres_options_sessions["frequence"]
    else:
        freqs_options = []
    st.multiselect(
        "Par fréquence",
        options=freqs_options,
        accept_new_options=False,
        placeholder="Choisir une ou plusieurs fréquences",
        key="selecteur_frequence",
    )

    # 3) Visibilité (selectbox, pas de radio)
    # Valeurs possibles: Tous / Public / Restreint
    vis_options = ["Tous", "Public", "Restreint"]
    vis_default = st.session_state.get("selecteur_visibilite", "Tous")
    st.selectbox(
        "Par visibilité",
        options=vis_options,
        index=vis_options.index(vis_default) if vis_default in vis_options else 0,
        key="selecteur_visibilite",
        help="Filtre sur is_published projeté (Public ou Restreint).",
    )

    # Bouton unique: Réinitialiser tous les filtres
    def _reset_all():
        st.session_state["selecteur_producteur"] = []
        st.session_state["selecteur_frequence"] = []
        st.session_state["selecteur_visibilite"] = "Tous"

    st.button("↺ Réinitialiser tous les filtres", on_click=_reset_all)

def bloc_indicateurs_et_filtres_v0(
    jdds_session: Any,
    df_session: pd.DataFrame,
    indicateurs_sessions: Dict[str, Any] | None,
    filtres_options_sessions: Dict[str, Any] | None
) -> None:
    """Affiche les indicateurs (dynamiques) et les filtres (Producteur, Fréquence, Visibilité)."""

    # --- Préparation DF ---
    df = df_session.copy()
    df = garantir_colonnes_de_base(df)
    df = normaliser_colonnes_visibilite(df)

    # --------- Filtres (widgets) ----------
    sac.divider(label='🧭 Filtres', icon='filter', align='center', color='blue', key="Filtre")

    # Options de filtres : priorité aux options injectées, sinon on les produit depuis df
    filtres_options = filtres_options_sessions or produire_filtres(df)

    # 1) Producteurs
    producteurs_options = filtres_options.get("producteur", [])
    st.multiselect(
        "Par producteurs",
        options=producteurs_options,
        accept_new_options=True,
        placeholder="Choisir un producteur. Ex: NATRAN",
        key="selecteur_producteur",
    )

    # 2) Fréquence
    freqs_options = filtres_options.get("frequence", [])
    st.multiselect(
        "Par fréquence",
        options=freqs_options,
        accept_new_options=False,
        placeholder="Choisir une ou plusieurs fréquences",
        key="selecteur_frequence",
    )

    # 3) Visibilités (séparées)

    # Sécurité colonnes (si helpers garantissent, ceci est redondant mais sûr)
    has_pub = "visibilite_publique" in df.columns
    has_res = "visibilite_restreinte" in df.columns

    opts_pub = ["Tous"]
    if has_pub and (df["visibilite_publique"] == "true").any():  opts_pub.append("Public")
    if has_pub and (df["visibilite_publique"] == "false").any(): opts_pub.append("Non public")

    opts_res = ["Tous"]
    if has_res and (df["visibilite_restreinte"] == "true").any():  opts_res.append("Restreint")
    if has_res and (df["visibilite_restreinte"] == "false").any(): opts_res.append("Non restreint")

    # Valeurs par défaut (sécurisées)
    default_pub = st.session_state.get("selecteur_visibilite_publique", "Tous")
    default_res = st.session_state.get("selecteur_visibilite_restreinte", "Tous")
    if default_pub not in opts_pub:
        default_pub = "Tous"; st.session_state["selecteur_visibilite_publique"] = "Tous"
    if default_res not in opts_res:
        default_res = "Tous"; st.session_state["selecteur_visibilite_restreinte"] = "Tous"

    col_pub, col_res = st.columns(2)
    with col_pub:
        st.selectbox(
            "Visibilité publique",
            options=opts_pub,
            index=opts_pub.index(default_pub),
            key="selecteur_visibilite_publique",
            help="Publication (is_published) : Public / Non public."
        )
    with col_res:
        st.selectbox(
            "Visibilité restreinte",
            options=opts_res,
            index=opts_res.index(default_res),
            key="selecteur_visibilite_restreinte",
            help="Accès restreint : Restreint / Non restreint."
        )

    # Bouton de reset — corriger les clés ciblées
    def _reset_all():
        st.session_state["selecteur_producteur"] = []
        st.session_state["selecteur_frequence"] = []
        st.session_state["selecteur_visibilite_publique"] = "Tous"
        st.session_state["selecteur_visibilite_restreinte"] = "Tous"
        # st.experimental_rerun()  # à activer si tu veux un refresh immédiat

    st.button("↺ Réinitialiser tous les filtres", on_click=_reset_all, width="content")

    # --------- Application des filtres + recalcul indicateurs ----------
    df_filtre = appliquer_filtres_df(df)
    st.session_state["df_filtre_debug"] = df_filtre  # utile ailleurs

    # Toujours recalculer APRES filtre
    indicateurs_filtres = produire_indicateurs(df_filtre)

    # --- KPI dynamiques ---
    total_jdd        = indicateurs_filtres.get("nb_jdd", len(df_filtre))
    nb_public_oui    = indicateurs_filtres.get("nb_public_oui", 0)
    nb_public_non    = indicateurs_filtres.get("nb_public_non", 0)
    nb_restreint_oui = indicateurs_filtres.get("nb_restreint_oui", 0)
    nb_restreint_non = indicateurs_filtres.get("nb_restreint_non", 0)

    # --- Rendu tableau moderne (sans pourcentages) ---
    st.markdown(
        f"""
        <table class="kpi-modern" style="width:100%; border-collapse:collapse;">
          <tbody>
            <tr class="row-total">
              <td colspan="4" style="text-align:center;">
                <span class="kpi-total">📊 JDD(s) total :</span>
                <span class="kpi-value kpi-total">{total_jdd}</span>
              </td>
            </tr>
            <tr>
              <td class="kpi-public">🔓 Public</td>
              <td class="kpi-value val-public">{nb_public_oui}</td>
              <td class="kpi-nonpublic">🚫 Non public</td>
              <td class="kpi-value val-nonpublic">{nb_public_non}</td>
            </tr>
            <tr>
              <td class="kpi-restreint">🛡️ Restreint</td>
              <td class="kpi-value val-restreint">{nb_restreint_oui}</td>
              <td class="kpi-nonrestreint">✅ Non restreint</td>
              <td class="kpi-value val-nonrestreint">{nb_restreint_non}</td>
            </tr>
            <tr class="row-info">
              <td colspan="4" style="text-align:center; color: var(--color-12); font-weight:500;">
                Filtrage: {len(df_filtre)} lignes sur {len(df)} initiales
              </td>
            </tr>
          </tbody>
        </table>
        """,
        unsafe_allow_html=True
    )




# --- Colonne droite ---
# --- Fonction utlise ---# 
def produire_indicateurs(
    df: pd.DataFrame,
    producteur_cible: str | None = None
) -> Dict[str, Any]:
    """
    Calcule différents indicateurs globaux + pour un producteur spécifique.

    Paramètres
    ----------
    df : DataFrame d'analyse (déjà filtré)
    producteur_cible : producteur pour lequel on veut un taux spécifique (ex : 'NaTran')

    Retour
    ------
    dict avec :
        - nb_jdd
        - nb_restreint_oui / non
        - nb_en_retard / nb_a_jour
        - nb_producteurs
        - repartition_statut globale
        - stats_producteur (si producteur_cible fourni)
    """

    # -- Indicateurs globaux --
    nb_jdd = len(df)

    nb_restreint_oui = int((df["is_restricted"] == "Restreint").sum())
    nb_restreint_non = int((df["is_restricted"] == "Non restreint").sum())

    nb_en_retard = int((df["statut"] == "pas à jour").sum())
    nb_a_jour = int((df["statut"] == "à jour").sum())

    nb_producteurs = df["metadata_default_publisher_value"].nunique()

    repartition_statut = df["statut"].value_counts(dropna=False).to_dict()

    resultat = {
        "nb_jdd": nb_jdd,
        "nb_restreint_oui": nb_restreint_oui,
        "nb_restreint_non": nb_restreint_non,
        "nb_en_retard": nb_en_retard,
        "nb_a_jour": nb_a_jour,
        "nb_producteurs": nb_producteurs,
        "repartition_statut": repartition_statut,
    }

    # -----------------------------------------------------------------
    # 🔥 Indicateurs spécifiques à un producteur (ex: NaTran)
    # -----------------------------------------------------------------
    if producteur_cible:
        df_prod = df[df["metadata_default_publisher_value"] == producteur_cible]

        nb_prod_total = len(df_prod)
        nb_prod_ajour = int((df_prod["statut"] == "à jour").sum())
        nb_prod_pasajour = int((df_prod["statut"] == "pas à jour").sum())

        taux_ajour = (
            round((nb_prod_ajour / nb_prod_total) * 100, 2)
            if nb_prod_total > 0
            else 0.0
        )

        resultat["stats_producteur"] = {
            "producteur": producteur_cible,
            "total_jdd": nb_prod_total,
            "nb_a_jour": nb_prod_ajour,
            "nb_pas_a_jour": nb_prod_pasajour,
            "taux_a_jour_pct": taux_ajour,
        }

    return resultat

def construire_df_top_critiques(
    df_analyse: pd.DataFrame,
    top_n: int = 10
) -> pd.DataFrame:
    """
    Construit le TOP des JDD 'CRITIQUE' à partir d'un df d'analyse.

    - Filtre statut == 'CRITIQUE' (casse-insensible)
    - Calcule 'ecart_min' (minutes) et 'ecart_fmt' (label lisible)
    - Trie par écart décroissant
    - Retourne un DataFrame avec les colonnes utiles :
        ['jdd', 'producteur', 'statut', 'frequence', 'ecart_min', 'ecart_fmt', 'prochaine_echeance']

    Args:
        df_analyse: DataFrame source (une ligne par JDD)
        top_n: nombre max de lignes à retourner (None -> tout)

    Returns:
        pd.DataFrame trié par écart décroissant.
    """
    if df_analyse is None or df_analyse.empty:
        return pd.DataFrame(columns=["id_jdd_odre",
                                    "nom_jdd_odre"
                                    "uid"
                                    "created_at"
                                    "is_restricted"
                                    "metadata_default_title_value"
                                    "metadata_dcat_accrualperiodicity_value"
                                    "metadata_default_description_value"
                                    "metadata_default_publisher_value"
                                    "metadata_dcat_contact_name_value"
                                    "metadata_dcat_contact_email_value"
                                    "metadata_admin_source_de_la_donnee_value"
                                    "metadata_admin_gestionnaire_technique_de_la_donnee_value"
                                    "metadata_admin_gestionnaire_metier_de_la_donnee_value"
                                    "metadata_admin_direction_metier_concernee_value"
                                    "metadata_admin_type_de_source_de_donnees_value"
                                    "metadata_admin_sla_value"
                                    "metadata_admin_enjeux_value"
                                    "clef_frequence"
                                    "periode_jours"
                                    "tolerance_ratio"
                                    "statut"
                                    "derniere_mise_a_jour"
                                    "prochaine_mise_a_jour"
                                    "a_jour_depuis_j"
                                    "a_jour_depuis_h"
                                    "a_jour_depuis_m"
                                    "pas_a_jour_depuis_j"
                                    "pas_a_jour_depuis_h"
                                    "pas_a_jour_depuis_m"
                                    "age_jdd_jours"
                                    "ressources_total"
                                    "ressources_non_a_jour"
            ]
        )


    # Helper fallback si tes fonctions n'existent pas dans le scope
    def _minutes_from_any_safe(row: Dict[str, Any]) -> Optional[int]:
        # Si tu as déjà _minutes_from_any(rec), on l’utilise.
        try:
            return _minutes_from_any(row)  # type: ignore[name-defined]
        except NameError:
            pass

        # Fallback générique :
        # - 'ecart_min' déjà présent -> minutes
        # - 'ecart_minutes' -> minutes
        # - 'ecart' -> secondes -> converti en minutes
        for key in ("ecart_min", "ecart_minutes"):
            if key in row and pd.notna(row[key]):
                try:
                    return int(row[key])
                except Exception:
                    pass

        if "ecart" in row and pd.notna(row["ecart"]):
            try:
                # si 'ecart' est en secondes
                return int(round(float(row["ecart"]) / 60.0))
            except Exception:
                pass

        return None  # inconnu

    def _format_ecart_safe(ecart_m: Optional[int], freq_label: Optional[str]) -> str:
        # Si tu as déjà _format_ecart, on l’utilise.
        try:
            return _format_ecart(ecart_m, freq_label)  # type: ignore[name-defined]
        except NameError:
            pass
        if ecart_m is None:
            return "—"
        # Fallback simple lisible : "12 h 30 min" (sans multiplicateur)
        h, m = divmod(max(0, int(ecart_m)), 60)
        if h > 0:
            return f"{h} h {m} min"
        return f"{m} min"

    # Normalisation du statut
    statut_series = df_analyse.get("statut")
    if statut_series is None:
        return pd.DataFrame(columns=[
            "jdd", "producteur", "statut", "frequence", "ecart_min", "ecart_fmt", "prochaine_echeance"
        ])

    masque_critique = statut_series.astype(str).str.upper().eq("CRITIQUE")
    df_crit = df_analyse.loc[masque_critique].copy()

    if df_crit.empty:
        return pd.DataFrame(columns=[
            "jdd", "producteur", "statut", "frequence", "ecart_min", "ecart_fmt", "prochaine_echeance"
        ])

    rows: List[Dict[str, Any]] = []
    for _, rec in df_crit.iterrows():
        # Series -> dict pour compat helper/fallbacks
        d = rec.to_dict()

        freq_label = d.get("frequence") or d.get("frequency")
        ecart_m = _minutes_from_any_safe(d)

        rows.append({
            "jdd": d.get("jdd", ""),
            "producteur": d.get("producteur", d.get("metadata_default_publisher_value", "")),
            "statut": d.get("statut", ""),
            "frequence": (freq_label or ""),
            "ecart_min": (ecart_m if ecart_m is not None else -1),  # utile pour tri
            "ecart_fmt": _format_ecart_safe(ecart_m, freq_label),
            "prochaine_echeance": d.get("prochaine_echeance", d.get("prochaine_mise_a_jour", "")),
        })

    if not rows:
        return pd.DataFrame(columns=[
            "jdd", "producteur", "statut", "frequence", "ecart_min", "ecart_fmt", "prochaine_echeance"
        ])

    df_top = pd.DataFrame(rows)
    # Tri décroissant par écart
    df_top.sort_values(by="ecart_min", ascending=False, inplace=True, kind="mergesort")
    df_top.reset_index(drop=True, inplace=True)

    # Limitation TOP N si demandé
    if isinstance(top_n, int) and top_n > 0:
        df_top = df_top.head(top_n)

    # Colonnes finales (sécurise l’ordre)
    colonnes = [c for c in [
        "jdd", "producteur", "statut", "frequence", "ecart_min", "ecart_fmt", "prochaine_echeance"
    ] if c in df_top.columns]
    return df_top[colonnes]

def top_classement(df_analyse: pd.DataFrame,
                   top_n: Optional[int] = 10,
                   statut_cible: str = "pas à jour",
                   colonnes_tri_prioritaires: Optional[List[str]] = None
    ) -> pd.DataFrame:
    """
    Filtre d'abord sur le 'statut' puis renvoie un TOP N.
    - 'statut_cible' est comparé de façon robuste (minuscule + trim).
    - Si des colonnes de tri existent (par ex. 'depuis_min', 'ecart_min', 'age_jdd_jours'),
      on trie en décroissant; sinon on conserve l'ordre d'origine (tri stable).
    - Retourne les colonnes d'origine de df_analyse (aucune structure imposée).

    Args:
        df_analyse: DataFrame source avec au moins la colonne 'statut'.
        top_n: nombre max de lignes à retourner (None -> tout).
        statut_cible: valeur de statut à filtrer (ex. "pas à jour", "à jour", "CRITIQUE"...).
        colonnes_tri_prioritaires: liste de colonnes à essayer pour trier en priorité
            (par défaut: ['depuis_min','ecart_min','ecart_minutes','ecart','age_jdd_jours']).

    Returns:
        pd.DataFrame filtré et éventuellement trié (TOP N).
    """
    # Garde une sortie cohérente si input invalide
    if df_analyse is None or df_analyse.empty or "statut" not in df_analyse.columns:
        return pd.DataFrame(columns=df_analyse.columns if df_analyse is not None else [])

    # 1) Filtre statut (robuste)
    s = df_analyse["statut"].astype(str).str.strip().str.lower()
    cible = (statut_cible or "").strip().lower()
    df_filtre = df_analyse.loc[s.eq(cible)].copy()

    if df_filtre.empty:
        # Rien à renvoyer pour ce statut
        return df_filtre

    # 2) Tri utile si possible
    if colonnes_tri_prioritaires is None:
        colonnes_tri_prioritaires = ["depuis_min", "ecart_min", "ecart_minutes", "ecart", "age_jdd_jours"]

    # On cherche la première colonne de tri existante
    col_tri = next((c for c in colonnes_tri_prioritaires if c in df_filtre.columns), None)

    if col_tri is not None:
        # Si 'ecart' est en secondes, ou si c'est textuel, on essaie de convertir en numérique
        # pour un tri correct (les valeurs non convertibles vont à la fin)
        df_filtre[col_tri] = pd.to_numeric(df_filtre[col_tri], errors="coerce")
        # Tri décroissant: les plus "en retard" / plus grands écarts en premier
        df_filtre.sort_values(by=col_tri, ascending=False, inplace=True, kind="mergesort")
    # Sinon, on garde l'ordre d'origine (pas de tri)

    # 3) Top N
    if isinstance(top_n, int) and top_n > 0:
        df_filtre = df_filtre.head(top_n)

    df_filtre.reset_index(drop=True, inplace=True)
    return df_filtre

def map_restriction(val: Any) -> str:
    if pd.isna(val):
        return "—"
    try:
        return "Restreint" if bool(val) else "Public"
    except Exception:
        return "—"

def _to_int_or_zero(x: Any) -> int:
    """Convertit en int, retourne 0 si NaN/None/'' ou conversion impossible."""
    try:
        if x is None:
            return 0
        # pandas NaN
        if isinstance(x, float) and math.isnan(x):
            return 0
        # pd.NA / pd.NaT
        if pd.isna(x):
            return 0
        return int(x)
    except Exception:
        return 0

def fmt_depuis(row: pd.Series) -> str:
    """
    Construit une chaîne lisible à partir des colonnes *_depuis_{j,h,m}.
    - Si 'pas_a_jour_depuis_*' ont au moins une valeur > 0 -> 'Depuis : X j Y h Z min'
    - Sinon si 'a_jour_depuis_*' > 0 -> 'À jour depuis : ...' (ou 'À jour' si tu préfères)
    - Sinon -> '—'
    """
    # Pas à jour
    j_p = _to_int_or_zero(row.get("pas_a_jour_depuis_j"))
    h_p = _to_int_or_zero(row.get("pas_a_jour_depuis_h"))
    m_p = _to_int_or_zero(row.get("pas_a_jour_depuis_m"))

    if (j_p + h_p + m_p) > 0:
        parts = []
        if j_p > 0: parts.append(f"{j_p} j")
        if h_p > 0: parts.append(f"{h_p} h")
        if m_p > 0: parts.append(f"{m_p} min")
        return parts

    # À jour
    j_a = _to_int_or_zero(row.get("a_jour_depuis_j"))
    h_a = _to_int_or_zero(row.get("a_jour_depuis_h"))
    m_a = _to_int_or_zero(row.get("a_jour_depuis_m"))

    if (j_a + h_a + m_a) > 0:
        parts = []
        if j_a > 0: parts.append(f"{j_a} j")
        if h_a > 0: parts.append(f"{h_a} h")
        if m_a > 0: parts.append(f"{m_a} min")
        # Si tu préfères un libellé simple, retourne juste "À jour"
        return parts

    return "—"

# ===> Bloc valide
def bloc_des_alertes(df: pd.DataFrame) -> None:
    """
    Affiche :
      - Les KPI globaux du statut des JDD
      - Les pourcentages "à jour", "en retard" et "critiques"
      - Le TOP 3 des JDD les plus en retard (facultatif)
    """

    # --------- 1) Calcul des indicateurs ---------
    try:
        indicateurs = produire_indicateurs(df=df, producteur_cible="NaTran")
    except Exception as e:
        st.error(f"Erreur indicateurs : {e}")
        return

    nb_a_jour   = indicateurs.get("nb_a_jour", 0)
    nb_en_retard = indicateurs.get("nb_en_retard", 0)
    nb_jdd      = indicateurs.get("nb_jdd", 1)

    # Pourcentages globaux (avec fallback sécurisés)
    pct_ok  = round((nb_a_jour / nb_jdd) * 100, 1) if nb_jdd > 0 else 0
    pct_ret = round((nb_en_retard / nb_jdd) * 100, 1) if nb_jdd > 0 else 0
    pct_cri = indicateurs.get("pourcentage_critiques", 0)  # si tu le calcules plus tard

    # --------- 2) En-tête stylisée ---------
    sac.divider(
        label='🔔 Statut global des jeux de données',
        icon='warning',
        align='center',
        color='red',
        key="Alertes_statut_global"
    )

    # --------- 3) Bloc KPI HTML premium ---------
    st.markdown(f"""
        <div class="kpi-panel">
            <div class="kpi-card kpi-ok">
                <div class="kpi-icon">✅</div>
                <div class="kpi-info">
                    <div class="kpi-number"> À jour: {pct_ok}%</div>
                </div>
            </div>
            <div class="kpi-card kpi-retard">
                <div class="kpi-icon">⏳</div>
                <div class="kpi-info">
                    <div class="kpi-number">Retard: {pct_ret}%</div>
                </div>
            </div>
            <div class="kpi-card kpi-critique">
                <div class="kpi-icon">🚨</div>
                <div class="kpi-info">
                    <div class="kpi-number">Critiques: {pct_cri}%</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    sac.divider(label='🚩 Top en retard (CRITIQUES)', icon='filter', align='center', color='red', key="Top_en_retard")

    # --- Construction du TOP CRITIQUE à partir du df_analyse (ex: df_filtre) ---
    df_top_aff = top_classement(df_analyse=df, top_n=11, statut_cible="pas à jour")

    # === Colonnes calculées ===
    df_top_aff["depuis_fmt"] = df_top_aff.apply(fmt_depuis, axis=1)
    df_top_aff["Restriction"] = df_top_aff["is_restricted"].apply(map_restriction) if "is_restricted" in df_top_aff.columns else "—"

    # 1) Normaliser 'depuis_fmt' en texte (si c’est une liste)
    if "depuis_fmt" in df_top_aff.columns:
        df_top_aff["depuis_fmt"] = df_top_aff["depuis_fmt"].apply(
            lambda v: " ".join(v) if isinstance(v, list) and v else (str(v) if v is not None else "—")
        )
    colonnes_a_afficher = {"nom_jdd_odre": "Jeu de donnée",
                            "Restriction": "Restriction",
                            "statut": "Statut",
                            "depuis_fmt": "Depuis",
                            "derniere_mise_a_jour": "Dernière mise à jour",
                            "metadata_dcat_accrualperiodicity_value": "Fréquence",
                            #"ressources_total": "Nombre de ressources" 
    }
    cols_existantes = [c for c in colonnes_a_afficher.keys() if c in df_top_aff.columns]

    df_affichage = df_top_aff[cols_existantes].copy()
    
    rename_map = {old: colonnes_a_afficher[old] for old in cols_existantes}
    df_affichage.rename(columns=rename_map, inplace=True)

    # (optionnel) nettoyer les colonnes techniques AgGrid si elles trainent
    df_affichage = df_affichage.drop(columns=[c for c in df_affichage.columns if str(c).startswith("::")], errors="ignore")

    # Stockage du df_affichage dans les états de sessions pour une utlisation ultérieur
    st.session_state.setdefault("df_affichage", pd.DataFrame())
    st.session_state["df_affichage"] = df_affichage

    if df_affichage.empty:
        st.info("Aucun JDD CRITIQUE pour le moment.")
    else:
        for idx, row in df_affichage.head(5).iterrows():
            with st.container():
                st.markdown('<div class="detail-row">', unsafe_allow_html=True)

                c1,c2,c3,c4,c5,c6,c7 = st.columns([1,3,2,2,3,4,3], gap="small")
                with c1:
                    if st.button("🔎", key=f"detail_{idx}"):
                    # Récupérer l'id en utilisant df d'origine (même index)
                                        selected_id = None
                                        if "id_jdd_odre" in df_top_aff.columns:
                                            try:
                                                selected_id = int(df_top_aff.loc[idx, "id_jdd_odre"])
                                            except Exception:
                                                pass

                                        # Sauvegarder la sélection
                                        st.session_state["detail_selected_id"] = selected_id
                                        # on peut aussi mettre la clé fonctionnelle (nom) pour fallback
                                        st.session_state["detail_selected_nom"] = row.get("Jeu de donnée", None)

                                        # (Optionnel) poser une copie de la ligne affichée
                                        st.session_state["detail_selected_row_min"] = row.to_dict()
                                        st.rerun()

                with c2:
                    st.markdown(f"<div class='jdd'>{row.get('Jeu de donnée','—')}</div>", unsafe_allow_html=True)

                with c3:
                    # Restriction badge
                    restr = str(row.get("Restriction","—"))
                    badge_cls = "badge-restrict" if restr.lower() in {"restreint","oui"} else "badge-info"
                    st.markdown(f"<div class='restriction'><span class='badge {badge_cls}'>{restr}</span></div>", unsafe_allow_html=True)

                with c4:
                    stat = str(row.get("Statut","—")).strip().lower()
                    if stat == "pas à jour":
                        st.markdown("<div class='statut'><span class='badge badge-critique'><span class='ico'>⏳</span>Pas à jour</span></div>", unsafe_allow_html=True)
                    else:
                        st.markdown("<div class='statut'><span class='badge badge-ok'>✅ À jour</span></div>", unsafe_allow_html=True)

                with c5:
                            # Variante 1 : label + valeur (en deux spans)
                            depuis_txt = row.get("Depuis", "—")
                            st.markdown(
                                f"""
                                <div class="depuis">
                                <span class="fld lbl"><span class="ico">⏳</span>Depuis :</span>
                                <span class="fld val">{html.escape(str(depuis_txt))}</span>
                                </div>
                                """,
                                unsafe_allow_html=True
                            )

                with c6:
                    maj_txt = row.get("Dernière mise à jour", "—")
                    st.markdown(
                        f"""
                        <div class="maj">
                        <span class="fld lbl"><span class="ico">🗓️</span>Dernière maj :</span>
                        <span class="fld val">{html.escape(str(maj_txt))}</span>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                with c7:
                    freq_txt = row.get("Fréquence", "—")
                    st.markdown(
                        f"""
                        <div class="freq">
                        <span class="fld lbl"><span class="ico">📈</span>Fréquence :</span>
                        <span class="fld val">{html.escape(str(freq_txt))}</span>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                st.markdown("</div>", unsafe_allow_html=True)





# ===> Bloc de dev testé à supprimer
def bloc_statut_global_et_top_0(indicateurs: Dict[str, Any],
                              statut_global: str,
                              top_en_retard: List[Dict[str, Any]]) -> None:
    """
    Affiche le panneau de Statut global + indicateurs + TOP en retard.
    - Formatage 'écart' basé sur la fréquence (TYPE_FREQUENCE)
    - Tri: CRITIQUE puis EN_RETARD, puis reste; à l'intérieur tri par écart décroissant
    """
    sac.divider(label='🔔 Alertes statut global', icon='warning', align='center', color='red', key="Alertes_statut_global")

    # --- Panneau Statut global ---

    # KPIs (pourcentages)
    pct_ok  = int(indicateurs.get("pourcentage_a_jour", 0) or 0)
    pct_ret = int(indicateurs.get("pourcentage_en_retard", 0) or 0)
    pct_cri = int(indicateurs.get("pourcentage_critiques", 0) or 0)

    # --- Rangée 1 :  Panneau Statut global ------
    # --- Rangée 2 : deux colonnes (Public / Restreint) via classes CSS ---
    st.markdown(
        f"""
        <div class="kpi kpi-row">
          <span class='kpi__value'>Statut global { _statut_global_badge(statut_global) }</span>
          <span class="badge badge--public">✅ À jour: {pct_ok}%</span>
          <span class="kpi-pill kpi-pill--ret">⏳ En retard: {pct_ret}%</span>
          <span class="kpi-pill kpi-pill--cri">🚨 Critiques: {pct_cri}%</span>
        </div>
        """,
        unsafe_allow_html=True
    )

    sac.divider(label='🚩 Top en retard', icon='filter', align='center', color='red', key="Top_en_retard")


    # --- Préparation du TOP (CRITIQUE seulement) ---
    rows: List[Dict[str, Any]] = []

    for rec in (top_en_retard or []):
        # Ne conserver que les statuts CRITIQUE
        statut_val = (rec.get("statut", "") or "").upper()
        if statut_val != "CRITIQUE":
            continue

        ecart_m = _minutes_from_any(rec)  # gère ecart_min / ecart_minutes / ecart (s -> min)
        freq_label = rec.get("frequence") or rec.get("frequency")

        rows.append({
            "jdd": rec.get("jdd", ""),
            "publisher": rec.get("publisher", ""),  # peut être vide si non fourni
            "statut": rec.get("statut", ""),
            "frequence": freq_label or "",
            "ecart_fmt": _format_ecart(ecart_m, freq_label),       # ex: "12 h 30 min • 8.3×"
            "ecart_min": ecart_m if ecart_m is not None else -1,   # pour tri
            "prochaine_echeance": rec.get("prochaine_echeance", ""),  # peut être vide
        })
    df_top = pd.DataFrame(rows)
    df_grid = df_top.copy()
    try:
        gb = GridOptionsBuilder.from_dataframe(df_grid)
        gb.configure_selection('single', use_checkbox=True)
        grid_response = AgGrid(
            df_grid,
            gridOptions=gb.build(),
            update_on=["selection_changed"],
            height=240,
            allow_unsafe_jscode=True,
            key="grid_alertes_actualisation"
        )
        selected_rows = grid_response.get("selected_rows", [])
        if isinstance(selected_rows, pd.DataFrame):
            selected_rows = selected_rows.to_dict(orient="records")
        return selected_rows[0] if (isinstance(selected_rows, list) and len(selected_rows) > 0) else None
        
    except Exception as e:
        st.write(f"Erreur AgGrid: {e}")
        return None

def bloc_statut_global_et_top_1(indicateurs: Dict[str, Any],
                              statut_global: str,
                              top_en_retard: List[Dict[str, Any]]) -> None:
    """
    Affiche le panneau de Statut global + indicateurs + TOP en retard.
    - Formatage 'écart' basé sur la fréquence (TYPE_FREQUENCE)
    - Filtre: CRITIQUE uniquement
    - Tri: par écart décroissant
    """
    sac.divider(label='🔔 Alertes statut global', icon='warning', align='center', color='red', key="Alertes_statut_global")

    # --- KPIs (pourcentages) ---
    pct_ok  = int(indicateurs.get("pourcentage_a_jour", 0) or 0)
    pct_ret = int(indicateurs.get("pourcentage_en_retard", 0) or 0)
    pct_cri = int(indicateurs.get("pourcentage_critiques", 0) or 0)

    # --- Panneau Statut global & KPIs (classes CSS, pas de style inline) ---
    st.markdown(
        f"""
        <div class="kpi kpi-row">
          <span class='kpi__value'>Statut global {_statut_global_badge(statut_global)}</span>
          <span class="badge badge--public">✅ À jour: {pct_ok}%</span>
          <span class="kpi-pill kpi-pill--ret">⏳ En retard: {pct_ret}%</span>
          <span class="kpi-pill kpi-pill--cri">🚨 Critiques: {pct_cri}%</span>
        </div>
        """,
        unsafe_allow_html=True
    )

    sac.divider(label='🚩 Top en retard (CRITIQUES)', icon='filter', align='center', color='red', key="Top_en_retard")

    # --- Préparation du TOP (CRITIQUE uniquement) ---
    rows: List[Dict[str, Any]] = []
    for rec in (top_en_retard or []):
        statut_val = (rec.get("statut", "") or "").upper()
        if statut_val != "CRITIQUE":
            continue

        ecart_m = _minutes_from_any(rec)  # gère ecart_min / ecart_minutes / ecart (s->min)
        freq_label = rec.get("frequence") or rec.get("frequency")

        rows.append({
            "jdd": rec.get("jdd", ""),
            "publisher": rec.get("publisher", ""),  # peut être vide
            "statut": rec.get("statut", ""),
            "frequence": (freq_label or ""),
            "ecart_min": (ecart_m if ecart_m is not None else -1),  # pour tri
            "ecart_fmt": _format_ecart(ecart_m, freq_label),        # "12 h 30 min • 8.3×"
            "prochaine_echeance": rec.get("prochaine_echeance", ""),  # peut être vide
        })

    if not rows:
        st.info("Aucun JDD CRITIQUE pour le moment.")
        # Légende
        st.markdown(
            "<div class='legend'>Légende: Écart en minutes/heures/jours, "
            "et ratio à la fréquence (×freq) quand elle est connue.</div>",
            unsafe_allow_html=True
        )
        return  # respecte la signature -> None (pas de sélection retournée)

    # Tri: par écart décroissant
    rows = sorted(rows, key=lambda r: -(r["ecart_min"] or 0))

    # DataFrame pour affichage
    df_top = pd.DataFrame(rows)

    # Colonnes demandées + intersection robuste
    colonnes_demandees = ["jdd", "publisher", "statut", "frequence", "ecart_min", "ecart_fmt", "prochaine_echeance"]
    colonnes_existantes = [c for c in colonnes_demandees if c in df_top.columns]
    df_aff = df_top[colonnes_existantes] if colonnes_existantes else df_top

    # Affichage AgGrid (sans extraction de sélection ici)
    try:
        gb = GridOptionsBuilder.from_dataframe(df_aff)
        # Tri par défaut côté grid: ecart_min desc
        if "ecart_min" in df_aff.columns:
            gb.configure_column("ecart_min", sort="desc")
        gb.configure_selection('none', use_checkbox=False)

        AgGrid(
            df_aff,
            gridOptions=gb.build(),
            update_on=["sort_changed"],  # pas de sélection dans ce composant
            height=280,
            allow_unsafe_jscode=True,
            key="grid_top_critiques"
        )
    except Exception as e:
        st.write(f"Erreur AgGrid: {e}")
        # Fallback Streamlit
        st.dataframe(df_aff, width='stretch', height=300)

    # Légende
    st.markdown(
        "<div class='legend'>Légende: Écart en minutes/heures/jours, "
        "et ratio à la fréquence (×freq) quand elle est connue.</div>",
        unsafe_allow_html=True
    )

def bloc_statut_global_et_top_2(indicateurs: Dict[str, Any],
                              statut_global: str,
                              top_en_retard: List[Dict[str, Any]]) -> None:
    """
    Affiche le panneau de Statut global + indicateurs + TOP en retard (CRITIQUE).
    Ce composant projette également 'visibilite' dans df_des_analyses et le
    réécrit dans la session pour homogénéiser l'état UI.
    """
    # -------- Projection 'visibilite' & stockage session (sans changer le nommage) --------
    try:
        df_session = st.session_state.get("df_des_analyses", pd.DataFrame()).copy()
        jdds_odre  = st.session_state.get("jdds_odre", [])
        if not df_session.empty and isinstance(jdds_odre, list):
            df_session = projeter_visibilite(df_session, jdds_odre)  # ajoute la colonne 'visibilite'
            st.session_state["df_des_analyses"] = df_session
    except Exception as e:
        st.warning(f"Projection 'visibilite' non appliquée: {e}")

    # -------- En-tête / KPIs --------
    sac.divider(label='🔔 Alertes statut global', icon='warning', align='center', color='red', key="Alertes_statut_global")

    pct_ok  = int(indicateurs.get("pourcentage_a_jour", 0) or 0)
    pct_ret = int(indicateurs.get("pourcentage_en_retard", 0) or 0)
    pct_cri = int(indicateurs.get("pourcentage_critiques", 0) or 0)

    st.markdown(
        f"""
        <div class="kpi kpi-row">
          <span class='kpi__value'>Statut global {_statut_global_badge(statut_global)}</span>
          <span class="badge badge--public">✅ À jour: {pct_ok}%</span>
          <span class="kpi-pill kpi-pill--ret">⏳ En retard: {pct_ret}%</span>
          <span class="kpi-pill kpi-pill--cri">🚨 Critiques: {pct_cri}%</span>
        </div>
        """,
        unsafe_allow_html=True
    )

    sac.divider(label='🚩 Top en retard (CRITIQUES)', icon='filter', align='center', color='red', key="Top_en_retard")

    # -------- Préparation TOP CRITIQUE uniquement --------
    rows: List[Dict[str, Any]] = []
    for rec in (top_en_retard or []):
        if (rec.get("statut", "") or "").upper() != "CRITIQUE":
            continue

        ecart_m    = _minutes_from_any(rec)  # gère ecart_min / ecart_minutes / ecart(s->min)
        freq_label = rec.get("frequence") or rec.get("frequency")

        rows.append({
            "jdd": rec.get("jdd", ""),
            "publisher": rec.get("publisher", ""),
            "statut": rec.get("statut", ""),
            "frequence": freq_label or "",
            "ecart_min": ecart_m if ecart_m is not None else -1,
            "ecart_fmt": _format_ecart(ecart_m, freq_label),
            "prochaine_echeance": rec.get("prochaine_echeance", ""),
        })

    if not rows:
        st.info("Aucun JDD CRITIQUE pour le moment.")
        st.markdown(
            "<div class='legend'>Légende: Écart en minutes/heures/jours, "
            "et ratio à la fréquence (×freq) quand elle est connue.</div>",
            unsafe_allow_html=True
        )
        return

    # Tri: par écart décroissant
    rows   = sorted(rows, key=lambda r: -(r["ecart_min"] or 0))
    df_top = pd.DataFrame(rows)

    # Colonnes à afficher (intersection robuste)
    colonnes_demandees  = ["jdd", "publisher", "statut", "frequence", "ecart_min", "ecart_fmt", "prochaine_echeance"]
    colonnes_existantes = [c for c in colonnes_demandees if c in df_top.columns]
    df_aff = df_top[colonnes_existantes] if colonnes_existantes else df_top

    # Affichage (AgGrid si souhaité, sinon dataframe)
    try:
        gb = GridOptionsBuilder.from_dataframe(df_aff)
        if "ecart_min" in df_aff.columns:
            gb.configure_column("ecart_min", sort="desc")
        gb.configure_selection('none', use_checkbox=False)

        AgGrid(
            df_aff,
            gridOptions=gb.build(),
            update_on=["sort_changed"],
            height=280,
            allow_unsafe_jscode=True,
            key="grid_top_critiques"
        )
    except Exception as e:
        st.write(f"Erreur AgGrid: {e}")
        st.dataframe(df_aff, width='stretch', height=300)

    st.markdown(
        "<div class='legend'>Légende: Écart en minutes/heures/jours, "
        "et ratio à la fréquence (freq) quand elle est connue.</div>",
        unsafe_allow_html=True
    )

def bloc_statut_global_et_top_3(df:pd.DataFrame) -> None:
    """
    Affiche le panneau de Statut global + indicateurs + TOP en retard (CRITIQUE).
    - Peut projeter 'visibilite' dans df_des_analyses (si fourni) ou dans le DF de session.
    - N'émet aucun retour (-> None), conforme au nommage existant.
    """
    # --------- 1) Préparation des données (projection 'visibilite') ---------

    try:
        indicateurs = produire_indicateurs(df=df,
                                           producteur_cible="NaTran")

    except Exception as e:
        st.warning(f"Projection 'visibilite' non appliquée: {e}")

    # --------- 2) En-tête / KPIs ---------
    sac.divider(label='🔔 Alertes statut global', icon='warning', align='center', color='red', key="Alertes_statut_global")

    pct_ok  = int(indicateurs.get("pourcentage_a_jour", 0) or 0)
    pct_ret = int(indicateurs.get("pourcentage_en_retard", 0) or 0)
    pct_cri = int(indicateurs.get("pourcentage_critiques", 0) or 0)

    # Rendu CSS (classes venant de custom.css)
    st.markdown(
        f"""
        <div class="kpi kpi-center">
          <span class="badge badge--public">✅ À jour: {pct_ok}%</span>
          <span class="kpi-pill kpi-pill--ret">⏳ En retard: {pct_ret}%</span>
          <span class="kpi-pill kpi-pill--cri">🚨 Critiques: {pct_cri}%</span>
        </div>
        <div class="kpi-container">
            <div class="kpi-box kpi-ok">
                <span class="kpi-value">{pct_ok}%</span>
                <span class="kpi-label">À jour</span>
            </div>

            <div class="kpi-box kpi-retard">
                <span class="kpi-value">{pct_ret}%</span>
                <span class="kpi-label">En retard</span>
            </div>

            <div class="kpi-box kpi-critique">
                <span class="kpi-value">{pct_cri}%</span>
                <span class="kpi-label">Critiques</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    sac.divider(label='🚩 Top en retard (CRITIQUES)', icon='filter', align='center', color='red', key="Top_en_retard")

def bloc_statut_global_et_top(indicateurs: Dict[str, Any],
                              statut_global: str,
                              top_en_retard: List[Dict[str, Any]],
                              df_des_analyses: Optional[pd.DataFrame] = None,
                              jdds_odre: Optional[List[JddOdre]] = None) -> None:
    """
    Affiche le panneau de Statut global + indicateurs + TOP en retard (CRITIQUE).
    - Peut projeter 'visibilite' dans df_des_analyses (si fourni) ou dans le DF de session.
    - N'émet aucun retour (-> None), conforme au nommage existant.
    """
    # --------- 1) Préparation des données (projection 'visibilite') ---------
    try:
        # Source des données prioritaires
        df_session = (df_des_analyses.copy()
                      if isinstance(df_des_analyses, pd.DataFrame)
                      else st.session_state.get("df_des_analyses", pd.DataFrame()).copy())

        jdds_list = (jdds_odre
                     if isinstance(jdds_odre, list)
                     else st.session_state.get("jdds_odre", []))

        # Projection 'visibilite' seulement si on a bien une colonne 'id'
        if not df_session.empty and "id" in df_session.columns and isinstance(jdds_list, list):
            df_session = projeter_visibilite(df_session, jdds_list)
            # On réécrit pour homogénéiser l'état UI
            st.session_state["df_des_analyses"] = df_session
    except Exception as e:
        st.warning(f"Projection 'visibilite' non appliquée: {e}")

    # --------- 2) En-tête / KPIs ---------
    sac.divider(label='🔔 Alertes statut global', icon='warning', align='center', color='red', key="Alertes_statut_global")

    pct_ok  = int(indicateurs.get("pourcentage_a_jour", 0) or 0)
    pct_ret = int(indicateurs.get("pourcentage_en_retard", 0) or 0)
    pct_cri = int(indicateurs.get("pourcentage_critiques", 0) or 0)

    # Rendu CSS (classes venant de custom.css)
    st.markdown(
        f"""
        <div class="kpi kpi-row">
          <span class='kpi__value'>Statut global {_statut_global_badge(statut_global)}</span>
          <span class="badge badge--public">✅ À jour: {pct_ok}%</span>
          <span class="kpi-pill kpi-pill--ret">⏳ En retard: {pct_ret}%</span>
          <span class="kpi-pill kpi-pill--cri">🚨 Critiques: {pct_cri}%</span>
        </div>
        """,
        unsafe_allow_html=True
    )

    sac.divider(label='🚩 Top en retard (CRITIQUES)', icon='filter', align='center', color='red', key="Top_en_retard")

    # --------- 3) Construction du TOP CRITIQUE ---------
    rows: List[Dict[str, Any]] = []
    for rec in (top_en_retard or []):
        if (rec.get("statut", "") or "").upper() != "CRITIQUE":
            continue

        ecart_m    = _minutes_from_any(rec)  # gère ecart_min / ecart_minutes / ecart (s->min)
        freq_label = rec.get("frequence") or rec.get("frequency")
        rows.append({
            "jdd": rec.get("jdd", ""),
            "producteur": rec.get("producteur", ""),
            "statut": rec.get("statut", ""),
            "frequence": (freq_label or ""),
            "ecart_min": (ecart_m if ecart_m is not None else -1),  # pour tri
            "ecart_fmt": _format_ecart(ecart_m, freq_label),        # "12 h 30 min • 8.3×"
            "prochaine_echeance": rec.get("prochaine_echeance", ""),
        })

    if not rows:
        st.info("Aucun JDD CRITIQUE pour le moment.")
        return

    # Tri: par écart décroissant
    rows   = sorted(rows, key=lambda r: -(r["ecart_min"] or 0))
    df_top = pd.DataFrame(rows)

    # Colonnes à afficher (intersection robuste)
    colonnes_demandees  = ["jdd", "producteur", "statut", "frequence", "ecart_fmt"]
    colonnes_existantes = [c for c in colonnes_demandees if c in df_top.columns]
    df_aff = df_top[colonnes_existantes] if colonnes_existantes else df_top

    # --------- 4) Affichage TOP (AgGrid si possible, sinon fallback Streamlit) ---------
    try:
        gb = GridOptionsBuilder.from_dataframe(df_aff)
        if "ecart_min" in df_aff.columns:
            gb.configure_column("ecart_min", sort="desc")
        gb.configure_selection('none', use_checkbox=False)

        AgGrid(
            df_aff,
            gridOptions=gb.build(),
            update_on=["sort_changed"],
            height=280,
            allow_unsafe_jscode=True,
            key="grid_top_critiques"
        )
    except Exception as e:
        st.write(f"Erreur AgGrid: {e}")
        st.dataframe(df_aff, width='stretch', height=300)




# --- Bas de page (conteneur détails)---

import html
import pandas as pd
import streamlit as st
import streamlit_antd_components as sac
from typing import List, Dict, Any, Optional

def _fmt_delta_dict(d: Optional[Dict[str, Any]]) -> str:
    """Transforme {'jours':j,'heures':h,'minutes':m} -> 'x j y h z min' (ou '—')."""
    if not isinstance(d, dict):
        return "—"
    j = d.get("jours") or 0
    h = d.get("heures") or 0
    m = d.get("minutes") or 0
    parts = []
    if j: parts.append(f"{int(j)} j")
    if h: parts.append(f"{int(h)} h")
    if m: parts.append(f"{int(m)} min")
    return " ".join(parts) if parts else "—"

def bloc_details(df: pd.DataFrame, liste_desjdds: List["JddOdre"] | None = None) -> None:
    sac.divider(
        label='🔎 Détails sur les alertes',
        icon='warning',
        align='center',
        color='green',
        key="Details_sur_les_alertes"
    )

    # 0) Sélection posée par le bloc alertes (loupe)
    selected_id   = st.session_state.get("detail_selected_id", None)
    selected_nom  = st.session_state.get("detail_selected_nom", None)

    if not selected_id and not selected_nom:
        sac.result(
            title="Aucun jeu de données sélectionné",
            subtitle="Cliquez sur le bouton 🔎 d'une ligne du bloc de droite pour afficher ici les détails (ressources, dernières mises à jour, fréquence…).",
            status="empty",
            key="result_details_empty"
        )
        sac.divider(label='Fin des détails', icon='warning', align='center', color='green', key="Fin_details_sur_les_alertes")
        return

    # 1) Retrouver la ligne JDD dans df
    row_full = None
    if selected_id is not None and "id_jdd_odre" in df.columns:
        try:
            row_full = df.loc[df["id_jdd_odre"] == selected_id].iloc[0].to_dict()
        except Exception:
            row_full = None
    if row_full is None and selected_nom is not None and "nom_jdd_odre" in df.columns:
        try:
            row_full = df.loc[df["nom_jdd_odre"] == selected_nom].iloc[0].to_dict()
        except Exception:
            row_full = None

    if row_full is None:
        sac.result(
            title="Détails introuvables",
            subtitle="Impossible de retrouver ce jeu de données dans la source. Essayez de rafraîchir ou de re-sélectionner.",
            status="warning",
            key="result_details_not_found"
        )
        sac.divider(label='Fin des détails', icon='warning', align='center', color='green', key="Fin_details_sur_les_alertes")
        return

    # 2) Données JDD (sécurisées)
    nom          = html.escape(str(row_full.get("nom_jdd_odre", "—")))
    statut       = str(row_full.get("statut", "—")).strip().lower()
    restr        = row_full.get("is_restricted", None)
    restriction  = "Restreint" if bool(restr) else "Public"
    freq_key     = str(row_full.get("metadata_dcat_accrualperiodicity_value", "—"))
    periode_j    = row_full.get("periode_jours", "—")
    der_maj      = html.escape(str(row_full.get("derniere_mise_a_jour", "—")))
    proch_maj    = html.escape(str(row_full.get("prochaine_mise_a_jour", "—")))
    created_at   = html.escape(str(row_full.get("created_at", "—")))
    producteur   = html.escape(str(row_full.get("metadata_default_publisher_value", "—")))
    nb_total     = int(row_full.get("ressources_total", 0) or 0)
    nb_non_ok    = int(row_full.get("ressources_non_a_jour", 0) or 0)
    by_type      = row_full.get("ressources_par_type", {}) or {}
    by_type_str  = " • ".join([f"{html.escape(str(k))}: {int(v)}" for k, v in by_type.items()]) if by_type else "—"
    pda_dispo    = str(row_full.get("pda_dispo", "Non"))
    pda_last     = html.escape(str(row_full.get("pda_last_modified", "—")))

    # 3) Ressources détaillées du JDD sélectionné (optionnelles)
    df_ress_all: pd.DataFrame = st.session_state.get("df_ressources", pd.DataFrame())
    if isinstance(df_ress_all, pd.DataFrame) and not df_ress_all.empty and selected_id is not None:
        df_res_sel = df_ress_all.loc[df_ress_all["id_jdd_odre"] == selected_id].copy()
    else:
        df_res_sel = pd.DataFrame()

    # Filtrer uniquement les ressources qui ont généré l'alerte : statut "pas à jour"
    if not df_res_sel.empty and "res_statut" in df_res_sel.columns:
        mask_alert = df_res_sel["res_statut"].astype(str).str.strip().str.lower().eq("pas à jour")
        df_res_alert = df_res_sel.loc[mask_alert].copy()
    else:
        df_res_alert = pd.DataFrame()

    # 4) Construit le tableau KPI premium (HTML) en plusieurs sections
    #    NB: on utilise des <tr>/<td> pour conserver ton gabarit.
    rows_html = []

    # Ligne titre : nom du JDD
    rows_html.append(f"""
        <tr class="row-total">
          <td colspan="4" style="text-align:center;">
            <span class="kpi-total">📊 JDD :</span>
            <span class="kpi-total">{nom}</span>
          </td>
        </tr>
    """)

    # --- Série 1 : KPI Ressources (peu de lignes, comme demandé) ---
    rows_html.append(f"""
        <tr class="section"><td colspan="4" style="text-align:left; font-weight:700;">🔧 Ressources (KPI)</td></tr>
        <tr>
          <td class="kpi-restreint">Total (standard)</td>
          <td class="val-restreint">{nb_total}</td>
          <td class="kpi-nonrestreint">Non à jour</td>
          <td class="val-nonrestreint">{nb_non_ok}</td>
        </tr>
        <tr>
          <td class="kpi-restreint">Par type</td>
          <td class="val-restreint">{by_type_str}</td>
          <td class="kpi-nonrestreint">PDA</td>
          <td class="val-nonrestreint">{html.escape(pda_dispo)} {f"(dernière : {pda_last})" if pda_dispo=='Oui' else ""}</td>
        </tr>
    """)

    # --- Série 1 bis : par ressource en ALERTE uniquement (analyse fine) ---
    # Une ressource = quelques lignes (pas trop verbeux, mais tout le nécessaire)
    if not df_res_alert.empty:
        rows_html.append(f"""
            <tr class="section"><td colspan="4" style="text-align:left; font-weight:700;">🚨 Ressources en alerte (analyse fine)</td></tr>
        """)
        for _, r in df_res_alert.iterrows():
            res_title   = html.escape(str(r.get("res_title", "—")))
            res_type    = html.escape(str(r.get("res_origin_type", r.get("res_type", "—"))))
            res_statut  = str(r.get("res_statut", "—")).strip().lower()
            res_maj     = html.escape(str(r.get("res_updated_at", "—")))
            res_next    = html.escape(str(r.get("res_prochaine_mise_a_jour", "—")))
            res_d_ok    = _fmt_delta_dict(r.get("res_a_jour_depuis"))
            res_d_nok   = _fmt_delta_dict(r.get("res_pas_a_jour_depuis"))

            # Ligne 1 : Titre + Type + Statut
            rows_html.append(f"""
                <tr>
                  <td class="kpi-restreint">Titre</td>
                  <td class="val-restreint">{res_title}</td>
                  <td class="kpi-nonrestreint">Type</td>
                  <td class="val-nonrestreint">{res_type}</td>
                </tr>
                <tr>
                  <td class="kpi-restreint">Statut</td>
                  <td class="val-restreint">{'⏳ Pas à jour' if res_statut=='pas à jour' else '✅ À jour'}</td>
                  <td class="kpi-nonrestreint">Dernière maj</td>
                  <td class="val-nonrestreint">{res_maj}</td>
                </tr>
                <tr>
                  <td class="kpi-restreint">Prochaine maj</td>
                  <td class="val-restreint">{res_next}</td>
                  <td class="kpi-nonrestreint">Retard</td>
                  <td class="val-nonrestreint">{res_d_nok}</td>
                </tr>
            """)

    # --- Série 2 : Métadonnées ---
    rows_html.append(f"""
        <tr class="section"><td colspan="4" style="text-align:left; font-weight:700;">📄 Métadonnées</td></tr>
        <tr>
          <td class="kpi-restreint">Producteur</td>
          <td class="val-restreint">{producteur}</td>
          <td class="kpi-nonrestreint">Restriction</td>
          <td class="val-nonrestreint">{restriction}</td>
        </tr>
        <tr>
          <td class="kpi-restreint">Fréquence (clé)</td>
          <td class="val-restreint">{html.escape(freq_key)}</td>
          <td class="kpi-nonrestreint">Période (jours)</td>
          <td class="val-nonrestreint">{periode_j}</td>
        </tr>
        <tr>
          <td class="kpi-restreint">Statut</td>
          <td class="val-restreint">{'⏳ Pas à jour' if statut=='pas à jour' else '✅ À jour'}</td>
          <td class="kpi-nonrestreint">Dernière maj</td>
          <td class="val-nonrestreint">{der_maj}</td>
        </tr>
        <tr>
          <td class="kpi-restreint">Prochaine maj</td>
          <td class="val-restreint">{proch_maj}</td>
          <td class="kpi-nonrestreint">Créé le</td>
          <td class="val-nonrestreint">{created_at}</td>
        </tr>
    """)

    # 5) Rendu du tableau KPI premium
    st.markdown(
        f"""
        <table class="kpi-modern-premium" style="width:100%; border-collapse:collapse;">
          <tbody>
            {''.join(rows_html)}
          </tbody>
        </table>
        """,
        unsafe_allow_html=True
    )

    # 6) Bouton pour effacer la sélection (optionnel)
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🗑️ Effacer la sélection"):
            for k in ("detail_selected_id", "detail_selected_nom", "detail_selected_row_min"):
                st.session_state.pop(k, None)
            st.rerun()

    sac.divider(
        label='Fin des détails',
        icon='warning',
        align='center',
        color='green',
        key="Fin_details_sur_les_alertes"
    )


def bloc_details_v0(df: pd.DataFrame, liste_desjdds: List[JddOdre]) -> None:
    sac.divider(
        label='🔎 Détails sur les alertes',
        icon='warning',
        align='center',
        color='green',
        key="Details_sur_les_alertes"
    )
    
    selected_id = st.session_state.get("detail_selected_id", None)
    selected_nom = st.session_state.get("detail_selected_nom", None)

    if not selected_id and not selected_nom:
        # ——— État vide si aucune sélection ———
        sac.result(
            title="Aucun jeu de données sélectionné",
            subtitle="Cliquez sur le bouton 🔎 d'une ligne du bloc de droite pour afficher ici les détails (ressources, dernières mises à jour, fréquence…).",
            status="empty",  
            key="result_details_empty"
        )

    # ——— Retrouver la ligne complète dans df ———
    row_full = None
    if selected_id is not None and "id_jdd_odre" in df.columns:
        try:
            row_full = df.loc[df["id_jdd_odre"] == selected_id].iloc[0].to_dict()
        except Exception:
            row_full = None

    if row_full is None and selected_nom is not None and "nom_jdd_odre" in df.columns:
        try:
            row_full = df.loc[df["nom_jdd_odre"] == selected_nom].iloc[0].to_dict()
        except Exception:
            row_full = None

    if row_full is None:
        sac.result(
            title="Détails introuvables",
            subtitle="Impossible de retrouver ce jeu de données dans la source. Essayez de rafraîchir ou de re-sélectionner.",
            status="warning",
            key="result_details_not_found"
        )


    sac.divider(
        label='Fin des détails',
        icon='warning',
        align='center',
        color='green',
        key="Fin_details_sur_les_alertes"
    )


    sac.divider(
        label='DEBUG-DEV',
        icon='warning',
        align='center',
        color='green',
        key="Debug_dev"
    )
    with st.expander(label="🔎  Debug dev"):
        st.subheader("🔎  Debug dev")

        # Récupérer le DF affichage calculé dans le bloc précédent
        df_affichage_recupere = st.session_state.get("df_affichage", pd.DataFrame())
        df_affichage = df_affichage_recupere.copy()

        # Débub à supprimer:
        #st.json(df_affichage.to_dict(orient="records"))

        if df_affichage.empty:
            sac.result(label='AUCUNS DETAILS', description='Cliquer sur un jeu de donnée pour voir ses détails', status='empty')
            return
        else:
            # Stockage du df_affichage dans les états de sessions pour une utlisation ultérieur
            st.session_state.setdefault("df_affichage", pd.DataFrame())
            st.session_state["df_affichage"] = df_affichage
            gb = GridOptionsBuilder.from_dataframe(df_affichage)
            gb.configure_default_column(resizable=True, sortable=True, filter=True)
            
            # Un peu d’esthétique
            if "statut" in df_affichage.columns:
                gb.configure_column(
                    "statut",
                    cellStyle={
                        "textTransform": "capitalize",
                        "fontWeight": "600"
                    }
                )
            # Hauteur auto (max 380px)
            height = min(380, 56 + 32 * len(df_affichage))

            AgGrid(
                df_affichage,
                gridOptions=gb.build(),
                update_on=["sort_changed"],
                height=height,
                allow_unsafe_jscode=True,
                key="grid_top_pas_a_jou",
                fit_columns_on_grid_load=True
            )






# ===> Bloc de dev testé à supprimer
def visuel_sur_jdds_traites(df_prepared_key: str = "df_prepared",
                            df_filtre_debug_key: str = "df_filtre_debug"
) -> None:
    """
    Affiche un aperçu du DataFrame (filtré si disponible), en utilisant les clés session fournies.
    """
    st.subheader("🔎 Aperçu du DataFrame filtré")
    df_viz = obtenir_df_filtre(df_prepared_key, df_filtre_debug_key)

    if df_viz.empty:
        st.info("Aucun résultat à afficher (DF filtré vide).")
        return

    colonnes_prioritaires = [
        "id", "nom", "producteur", "frequence", "statut",
        "visibilite_publique", "visibilite_restreinte",
        "prochaine_echeance", "confiance"
    ]
    cols = [c for c in colonnes_prioritaires if c in df_viz.columns]
    st.dataframe(df_viz[cols] if cols else df_viz, use_container_width=True)
    st.caption(f"Affichage de {len(df_viz)} ligne(s).")


def voir_toutes_les_colonnes_des_jjds(listes_cols: List[str]) -> None:
    """
    Affiche la liste des colonnes dans Streamlit
    """
    st.subheader("Toutes les colonnes détectées")
    
    if not listes_cols:
        st.warning("Aucune colonne trouvée.")
        return

    # Affichage simple
    st.write(f"Nombre total de colonnes : {len(listes_cols)}")
    
    # Affichage sous forme de liste
    st.write(listes_cols)

    # Optionnel : affichage plus lisible avec st.json
    st.json({"colonnes": listes_cols})

    # Ou sous forme de tableau
    st.table({"Colonnes": listes_cols})

def grille_alertes(df_application_filtre: pd.DataFrame) -> Optional[Dict[str, Any]]:
    """Affiche la grille des alertes; retourne la ligne sélectionnée (dict) si existante."""
    #sac.divider(label='🔔 Alertes', icon='warning', align='center', color='red', key="Alertes")
    sac.divider(label=' Analyse détaillée par JDD', icon='search', align='center', color='purple', key="Details_alerte")


    if df_application_filtre is None or df_application_filtre.empty:
        st.info("Aucune donnée à afficher.")
        return None

    colonnes_a_afficher = [
        'nom', 'producteur', 'visibilite',
        'statut', 'frequence', 'prochaine_echeance'
    ]
    colonnes_existantes = [c for c in colonnes_a_afficher if c in df_application_filtre.columns]

    df_grid = df_application_filtre.copy()
    # Formatage 'prochaine_echeance'
    if "prochaine_echeance" in df_grid.columns:
        df_grid["prochaine_echeance"] = _fmt_dt_series_local(df_grid["prochaine_echeance"], Configurations.TIME_ZONE)

    if colonnes_existantes:
        df_grid = df_grid[colonnes_existantes]

    try:
        gb = GridOptionsBuilder.from_dataframe(df_grid)
        gb.configure_selection('single', use_checkbox=True)
        grid_response = AgGrid(
            df_grid,
            gridOptions=gb.build(),
            update_on=["selection_changed"],
            height=240,
            allow_unsafe_jscode=True,
            key="grid_alertes_actualisation"
        )
        selected_rows = grid_response.get("selected_rows", [])
        if isinstance(selected_rows, pd.DataFrame):
            selected_rows = selected_rows.to_dict(orient="records")
        return selected_rows[0] if (isinstance(selected_rows, list) and len(selected_rows) > 0) else None
    except Exception as e:
        st.write(f"Erreur AgGrid: {e}")
        return None

def details_jdd(selected_row_full: Optional[Dict[str, Any]], jdds_odre: List[JddOdre]) -> None:
    """Affiche les détails enrichis du JDD sélectionné (métadonnées via objets métier)."""
    #sac.divider(label=' Analyse détaillée par JDD', icon='search', align='center', color='purple', key="Details_analyses")

    if not selected_row_full:
        st.caption("Sélectionnez un JDD dans la grille pour afficher les détails.")
        return

    # Recherche de l'objet métier correspondant
    description = ""
    uid = ""
    title = selected_row_full.get("nom", "")
    created_at = ""
    updated_at = ""
    modified = ""
    sla = ""
    tags = ""
    theme = ""
    enjeux = ""
    maille_geographique = ""
    pas_temporel = selected_row_full.get("frequence", "")
    profondeur_dhistorique = ""
    reseaux = ""
    energie = ""
    publisher = selected_row_full.get("producteur", "")
    id_sel = selected_row_full.get("id")
    nom_sel = selected_row_full.get("nom")

    try:
        jdd_trouve = None
        for j in (jdds_odre or []):
            if (id_sel is not None and j.id_jdd_odre == id_sel) or (nom_sel and j.nom_jdd_odre == nom_sel):
                jdd_trouve = j
                break
        if jdd_trouve:
            meta = jdd_trouve.metadonnees or {}
            description = meta.get("description", "")
            uid = meta.get("uid", "")
            title = meta.get("title", "") or title
            created_at = meta.get("created_at", "")
            updated_at = meta.get("updated_at", "") or meta.get("metadata_default_modified_value", "")
            modified = meta.get("metadata_default_modified_value", "")
            sla = meta.get("sla", "")
            tags = meta.get("tags", "")
            theme = meta.get("theme", "")
            enjeux = meta.get("enjeux", "")
            maille_geographique = meta.get("maille_geographique", "")
            profondeur_dhistorique = meta.get("profondeur_dhistorique", "")
            reseaux = meta.get("reseaux", "")
            energie = meta.get("energie", "")
            publisher = publisher or meta.get("publisher", "") or meta.get("metadata_default_publisher_value", "")
            pas_temporel = meta.get("metadata_custom_pas_temporel_value", "") or pas_temporel
    except Exception:
        pass

    with st.expander("🆔 Identifiants & Métadonnées", expanded=False):
        st.write(f"**UID**: {uid}")
        st.write(f"**Title**: {title}")
        st.write(f"**Created At**: {created_at}")
        st.write(f"**Updated At**: {updated_at}")
        st.write(f"**Modified**: {modified}")
        st.write(f"**SLA**: {sla}")

    with st.expander("💽 Informations sur le contenu", expanded=False):
        with st.container():
            sac.alert(
                f"**Description**",
                description=description or "Aucune description disponible.",
                variant="quote-light",
                banner=sac.Banner(play=False, direction='left', speed=30, pauseOnHover=True),
                key="description_alert"
            )
        st.write(f"**Tags**: {tags}")
        st.write(f"**Thème**: {theme}")
        st.write(f"**Enjeux**: {enjeux}")

    with st.expander("🌍 Dimensions & Couverture", expanded=False):
        st.write(f"**Maille Géographique**: {maille_geographique}")
        st.write(f"**Pas Temporel**: {pas_temporel}")
        st.write(f"**Profondeur Historique**: {profondeur_dhistorique}")
        st.write(f"**Réseaux**: {reseaux}")
        st.write(f"**Énergie**: {energie}")

    with st.expander("👥 Responsables & Organisation", expanded=False):
        st.write(f"**Publisher**: {publisher}")
        st.write(f"**Gestionnaire Technique**: {selected_row_full.get('gestionnaire_technique_de_la_donnee', '')}")
        st.write(f"**Gestionnaire Métier**: {selected_row_full.get('gestionnaire_metier_de_la_donnee', '')}")
        st.write(f"**Direction Métier Concernée**: {selected_row_full.get('direction_metier_concernee', '')}")

# --- Panneau debug (optionnel) ---
def panneau_debug(df_des_analyses: pd.DataFrame,
                  jdds_odre: List[JddOdre],
                  indicateurs: Dict[str, Any],
                  statut_global: str,
                  top_en_retard: List[Dict[str, Any]]) -> None:
    """Affiche un panneau debug complet (développement)."""
    
    with st.expander("🧰 Panneau debug — Actualisation des données", expanded=False):
        selecteur_producteur = st.session_state.get("selecteur_producteur", [])
        filtre_visibilite = st.session_state.get("filtre_visibilite", "Tous")

        # Boutons
        col_btn_a, col_btn_b, col_btn_c = st.columns([1, 1, 1])
        with col_btn_a:
            if st.button("🔄 Recharger données (service)", key="btn_reload_data"):
                st.experimental_rerun()
        with col_btn_b:
            if st.button("🧹 Réinitialiser filtres", key="btn_reset_filters"):
                st.session_state["selecteur_producteur"] = []
                st.session_state["filtre_visibilite"] = "Tous"
                st.success("Filtres réinitialisés.")
        with col_btn_c:
            if st.button("🗑️ Vider cache UI (analyses)", key="btn_clear_ui"):
                for k in ("df_des_analyses", "top_en_retard", "indicateurs", "statut_global"):
                    st.session_state.pop(k, None)
                st.success("Cache UI vidé (analyses/indicateurs/top/statut).")

        st.markdown("---")

        # Résumé
        st.subheader("📦 Résumé")
        col_r1, col_r2, col_r3, col_r4 = st.columns([1, 1, 1, 1])
        with col_r1:
            st.metric("JDD objets (liste)", len(jdds_odre) if isinstance(jdds_odre, list) else 0)
        with col_r2:
            st.metric("Analyses (lignes)", len(df_des_analyses))
        with col_r3:
            st.metric("Statut global", statut_global)
        with col_r4:
            st.metric("Filtre Producteur (n)", len(selecteur_producteur))

        st.caption(f"Colonnes DF Analyses: {list(df_des_analyses.columns)}")

        # Distributions
        st.subheader("👤 Distribution des producteurs")
        if "producteur" in df_des_analyses.columns and not df_des_analyses.empty:
            st.dataframe(df_des_analyses["producteur"].fillna("").astype(str).value_counts().head(15), width='stretch')
        else:
            st.info("Colonne 'producteur' absente.")

        st.subheader("⏱️ Distribution des fréquences")
        if "frequence" in df_des_analyses.columns and not df_des_analyses.empty:
            st.dataframe(df_des_analyses["frequence"].fillna("").astype(str).value_counts().head(15), width='stretch')
        else:
            st.info("Colonne 'frequence' absente.")

        st.subheader("🔒 Distribution de la visibilité")
        if "visibilite" in df_des_analyses.columns and not df_des_analyses.empty:
            st.dataframe(df_des_analyses["visibilite"].value_counts(), width='stretch')
        else:
            st.info("Colonne 'visibilite' absente.")

        st.subheader("🔎 Aperçu Analyses (5 premières lignes)")
        if not df_des_analyses.empty:
            cols = [c for c in ["id", "nom", "producteur", "visibilite", "statut", "ecart_min", "frequence", "prochaine_echeance", "confiance"] if c in df_des_analyses.columns]
            st.dataframe(df_des_analyses[cols].head(5), width='stretch')
        else:
            st.info("DF Analyses vide.")

        st.subheader("🚨 Top en retard (aperçu)")
        if isinstance(top_en_retard, list) and top_en_retard:
            try:
                df_top = pd.DataFrame(top_en_retard)
                cols_top = [c for c in ["jdd", "statut", "ecart_min", "frequence", "prochaine_echeance", "publisher"] if c in df_top.columns]
                st.dataframe(df_top[cols_top].head(10), width='stretch')
            except Exception as e:
                st.error(f"Erreur conversion top_en_retard en DataFrame: {e}")
                st.write(top_en_retard[:5])
        else:
            st.info("Top en retard vide.")

        st.subheader("📊 Indicateurs (brut)")
        st.json(indicateurs or {})



