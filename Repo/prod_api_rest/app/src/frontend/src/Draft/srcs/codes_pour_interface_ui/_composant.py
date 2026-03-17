# --- Application de supervision des jeux de données ODRE 
# chemin: srcs/codes_pour_interface_ui/composants_pour_pages.py
# ==== coding: utf-8 ====

# === Importation de librairies ===
from __future__ import annotations

import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Optional, Tuple
import streamlit_antd_components as sac
from st_aggrid import AgGrid, GridOptionsBuilder

from datetime import datetime, time
from zoneinfo import ZoneInfo
from dataclasses import dataclass
from typing import Dict, Any, List, Optional
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode



# === Importation de modules ===
from srcs.configs import Configurations
from srcs.codes_pour_metier_admin_jdd_odre_app.modelisation_jdd_odre import JddOdre
from srcs.codes_pour_senario_utilisation_app.services_d_orchestration import (
    orchestration_service_alimenter_cache_app_en_data
)
from srcs.codes_pour_senario_utilisation_app.outils_pour_les_services import (
    _lire_le_cache_data,
    _analyse_declencheur_auto,
)




# ------------- Composants pour la page standard --------------------------
# Base de page: 
# Formatage FR de l’âge 
def _fmt_age(j: int, h: int, m: int, s: int) -> str:
    """
    Format compact de l'âge:
      - "2 j 3 h"
      - "3 h 12 min"
      - "15 min 4 s"
      - "8 s"
    """
    if j > 0:
        return f"{j} j {h} h"
    if h > 0:
        return f"{h} h {m} min"
    if m > 0:
        return f"{m} min {s} s" if s > 0 else f"{m} min"
    return f"{s} s"

def _fmt_cron_spec(spec: str) -> str:
    """
    Convertit 'mon-fri' en 'Lun–Ven', ou 'mon,wed,fri' en 'Lun, Mer, Ven'.
    """
    spec = (spec or "").strip().lower()
    mapping = {
        "mon": "Lun", "tue": "Mar", "wed": "Mer",
        "thu": "Jeu", "fri": "Ven", "sat": "Sam", "sun": "Dim"
    }
    if "-" in spec and "," not in spec:
        a, b = spec.split("-", 1)
        return f"{mapping.get(a, a.capitalize())}–{mapping.get(b, b.capitalize())}"
    parts = [p.strip() for p in spec.split(",") if p.strip()]
    return ", ".join(mapping.get(p, p.capitalize()) for p in parts)

def composant_actualisation(col_container: st.delta_generator.DeltaGenerator) -> None:
    """
    Rend un bloc UI permettant:
      - Déclenchement d'une alimentation manuelle,
      - Affichage du statut et de la planification automatique,
      - Affichage de la dernière alimentation et de l'âge du cache.
    """
    svc = orchestration_service_alimenter_cache_app_en_data()

    with col_container:
        st.subheader("Actualisation des données")

        # Lecture du cache (meta) pour afficher le dernier mode et la dernière date
        meta = _lire_le_cache_data(Path(Configurations.CACHE_SOURCES)) or {}
        (age_j, age_h, age_m, age_s), last_dt = svc.fraicheur_du_cache_de_donnees()
        last_mode = meta.get("mode", "inconnu")

        # Planification auto (depuis la config)
        auto_enabled = bool(getattr(Configurations, "AUTO_REFRESH_CRON_ENABLED", True))
        cron_hour = int(getattr(Configurations, "AUTO_REFRESH_CRON_HOUR", 9))
        cron_minute = int(getattr(Configurations, "AUTO_REFRESH_CRON_MINUTE", 30))
        cron_spec = str(getattr(Configurations, "AUTO_REFRESH_CRON_WEEKDAYS", "mon-fri")).lower()

        now = datetime.now(Configurations.TIME_ZONE)
        doit_declencher_maintenant = _analyse_declencheur_auto(now)

        # --- Bloc informations -------------------------------------------------
        st.info(
            f"Alimentation automatique: "
            f"{'activée' if auto_enabled else 'désactivée'} • "
            f"créneau prévu: {cron_hour:02d}:{cron_minute:02d} ({_fmt_cron_spec(cron_spec)})."
        )

        if last_dt:
            st.write(
                f"**Dernière alimentation**: {last_dt.strftime('%d/%m/%Y %H:%M')} "
                f"({last_mode}) • **Âge du cache**: {_fmt_age(age_j, age_h, age_m, age_s)}."
            )
        else:
            st.warning("Cache des données non initialisé (aucune alimentation enregistrée).")

        if auto_enabled:
            st.write(
                f"**État planification maintenant**: "
                f"{'✅ Déclenchement attendu à cette minute' if doit_declencher_maintenant else '⏱️ En dehors du créneau'}."
            )

        st.divider()

        # --- Actions utilisateur ----------------------------------------------
        col1, col2, col3 = st.columns([2, 2, 6])

        # Bouton alimentation manuelle
        with col1:
            if st.button("🔄 Alimenter manuellement", key="btn_alimenter_man"):
                msg = svc.alimenter_manuellement("OUI")
                st.success(msg)
                # Relecture rapide des infos
                (age_j, age_h, age_m, age_s), last_dt = svc.fraicheur_du_cache_de_donnees()
                st.caption(
                    f"Dernière alimentation: {last_dt.strftime('%d/%m/%Y %H:%M') if last_dt else 'inconnue'} • "
                    f"Âge: {_fmt_age(age_j, age_h, age_m, age_s)}."
                )

        # Bouton test de l’auto (il n’alimente que si l’on est dans le créneau)
        with col2:
            if st.button("⚙️ Tester auto maintenant", key="btn_tester_auto"):
                svc.alimenter_automatiquement()
                # Relecture rapide des infos
                (age_j, age_h, age_m, age_s), last_dt = svc.fraicheur_du_cache_de_donnees()
                st.caption(
                    f"Dernière alimentation: {last_dt.strftime('%d/%m/%Y %H:%M') if last_dt else 'inconnue'} • "
                    f"Âge: {_fmt_age(age_j, age_h, age_m, age_s)}."
                )

        with col3:
            st.caption("Astuce: le bouton **Tester auto** ne déclenchera que si vous êtes exactement sur le créneau planifié.")




# ------------- Composants pour la page Actualisation des données --------------------------


# utilitaire d’affectation sécurisé
def _safe_set_column(df: pd.DataFrame, col: str, value) -> pd.DataFrame:
    """
    Affecte une colonne en garantissant la longueur correcte.
    - Si value est un scalaire -> broadcast correct
    - Si value est list/Series/ndarray -> doit avoir len == len(df), sinon fallback neutre.
    """
    import numpy as np
    from pandas import Series

    if isinstance(value, (list, Series, np.ndarray)):
        if len(value) == len(df):
            df[col] = value
        else:
            # Fallback neutre (string vide pour colonnes texte/JSON)
            df[col] = Series([None] * len(df), index=df.index)
    else:
        # Scalaire
        df[col] = value
    return df

#  KPI globaux  
def composant_kpis_actualisation(indics: dict) -> None:
    st.metric("Jeux de données", indics.get("nb_jdd", 0))
    c1, c2, c3 = st.columns(3)
    c1.metric("À jour", indics.get("nb_a_jour", 0))
    c2.metric("Pas à jour", indics.get("nb_pas_a_jour", 0))
    c3.metric("Ressources non à jour", indics.get("nb_ressources_non_a_jour", 0))

# Filtre pour la colonne de gauche 
def produire_filtre_V0(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Génère des options de filtres triées et nettoyées à partir du DataFrame.
    Champs : producteur, visibilite, statut, frequence.
    Les valeurs sont converties en chaînes et les NaN sont remplacé par str "aucun(e)".
    """
    def _netoyage(col: str) -> list:
        return sorted(df[col].dropna().astype(str).unique().tolist())
    return {
        "producteur": _netoyage("producteur"),
        "frequence": _netoyage("clef_frequence"),
        "restriction": _netoyage("restriction")
    }
# Filtre par statut (segmented SAC), recherche texte, filtre âge
def composant_filtres_actualisation(df: pd.DataFrame) -> pd.DataFrame:
    st.subheader("Filtres")
    # Statut
    statut = sac.segmented(
        items=['tous', 'à jour', 'pas à jour'],
        value='tous',
        align='center',
        size='small',
        key='filtre_statut',
    )
    # Recherche simple sur title / uid
    col1, col2 = st.columns([2,1])
    with col1:
        q = st.text_input("Recherche (uid / title contient)", value="", key="filtre_recherche")
    with col2:
        max_age = st.number_input("Âge max JDD (jours)", min_value=0, value=9999, step=1, key="filtre_age")

    df_vue = df.copy()
    if statut == 'à jour':
        df_vue = df_vue[df_vue["statut_actualisation"] == "à jour"]
    elif statut == 'pas à jour':
        df_vue = df_vue[df_vue["statut_actualisation"] == "pas à jour"]

    if q:
        ql = q.lower()
        # on filtre sur title si présent, sinon uid
        if "title" in df_vue.columns:
            df_vue = df_vue[df_vue["title"].astype(str).str.lower().str.contains(ql)]
        else:
            df_vue = df_vue[df_vue["uid"].astype(str).str.lower().str.contains(ql)]

    if "age_jdd_jours" in df_vue.columns:
        df_vue = df_vue[(df_vue["age_jdd_jours"].fillna(0).astype(int) <= int(max_age))]

    return df_vue

# Grille AgGrid — renvoie la sélection
def composant_table_jdds(df_vue: pd.DataFrame, colonnes: list[str]) -> list[dict]:
    st.subheader("Jeux de données (vue)")
    if df_vue.empty:
        st.warning("Aucune donnée pour les filtres appliqués.")
        return []
    cols = [c for c in colonnes if c in df_vue.columns]
    gb = GridOptionsBuilder.from_dataframe(df_vue[cols].head(1000))
    gb.configure_pagination(enabled=True, paginationAutoPageSize=False, paginationPageSize=25)
    gb.configure_default_column(resizable=True, filter=True)
    gb.configure_selection('single', use_checkbox=True)
    grid_options = gb.build()
    ag = AgGrid(df_vue[cols], gridOptions=grid_options, height=380, theme='material', enable_enterprise_modules=False)
    return ag.selected_rows or []


# Détails des ressources non à jour d’une ligne sélectionnée

def composant_details_ressources_non_a_jour(ligne: dict | None) -> None:
    st.subheader("Détails des ressources non à jour")
    if not ligne:
        st.caption("Sélectionne une ligne dans la grille pour voir les détails.")
        return
    nb_impacts = int(ligne.get("ressources_non_a_jour_count", 0))
    st.write(f"UID: {ligne.get('uid')} • Ressources non à jour: {nb_impacts}")
    try:
        import json
        impacts_list = json.loads(ligne.get("ressources_impacts_json", "[]"))
    except Exception:
        impacts_list = []
    if impacts_list:
        st.json(impacts_list[:20])
    else:
        st.caption("Aucune ressource marquée non à jour sur cette sélection.")

# Répartition par type origin_type (bar chart rapide)

def composant_repartition_origin_type(indics: dict) -> None:
    st.subheader("Répartition des ressources par type (origin_type)")
    rep = indics.get("repartition_origin_type", {})
    if not rep:
        st.caption("Aucune répartition disponible.")
        return
    import pandas as pd
    s = pd.Series(rep).sort_values(ascending=False)
    st.bar_chart(s)





































# ==== Composants de la page d'Accueil: Inspiré de Amber Six ====
def composant_arriere_plan():
    """Composant de gestion image arrière-plan avec découpage en diagonale"""
    st.info("image_arriere_plancomposant")

def composant_premier_plan():
    """Composants de gestion du premier plan"""
    st.info("Gestion de premier plan")

def composant_carousel():
    """ Afficher un carousel"""
    st.info("Slide des pages")

def composant_ticket():
    """Bandeau défilant en bas de pages pour montrer un indicateur fonctionnel: Les producteurs"""
    st.info("Bandeau défilant en bas")

def composant_composite_accueil():
    """ Assemble les composants (haut, bas, gauche, droite)"""
    st.info("Rassemble les composants")


# ==== Composants de la page d'Actualisation des données  ====

# ------------ Fonctions utiles -------------

def _inser_tableau_0(df: pd.DataFrame, hauteur: int = 290):
    try:
        if df.empty:
            st.warning("Aucune donnée à afficher dans le tableau.")
            return None

        gd = GridOptionsBuilder.from_dataframe(df)
        gd.configure_selection('single', use_checkbox=True)
        gd.configure_pagination(enabled=True)  # Ajout pagination
        gd.configure_default_column(resizable=True, sortable=True, filter=True)

        grid_options = gd.build()

        grid_response = AgGrid(
            df,
            gridOptions=grid_options,
            update_mode=GridUpdateMode.SELECTION_CHANGED,
            height=hauteur,
            allow_unsafe_jscode=True,
            fit_columns_on_grid_load=True
        )

        return grid_response  # Retourne la réponse pour récupérer la sélection

    except Exception as e:
        st.error(f"Erreur de chargement des données dans le tableau: {e}")
        return None

def _inser_tableau(df: pd.DataFrame, hauteur: int = 290, page_size: int = 25):
    """
    Insère un tableau AgGrid :
    - Remplit la largeur disponible (flex + fit_columns_on_grid_load)
    - Pagination contrôlée
    - Sélection simple (avec checkbox)
    - Retourne la sélection sous forme de liste de dicts

    Paramètres:
    - df: DataFrame à afficher
    - hauteur: hauteur en pixels du composant (utiliser domLayout='autoHeight' pour adapter)
    - page_size: taille des pages pour la pagination
    """
    try:
        if df is None or df.empty:
            st.warning("Aucune donnée à afficher dans le tableau.")
            return []

        gd = GridOptionsBuilder.from_dataframe(df)

        # Sélection (simple) avec checkbox
        gd.configure_selection(selection_mode='single', use_checkbox=True)

        # Pagination
        gd.configure_pagination(enabled=True, paginationAutoPageSize=False, paginationPageSize=page_size)

        # Colonnes par défaut
        gd.configure_default_column(
            resizable=True,
            sortable=True,
            filter=True,
            min_column_width=120  # assure une largeur minimale lisible
        )

        grid_options = gd.build()

        # Remplissage horizontal via flex
        grid_options["defaultColDef"] = grid_options.get("defaultColDef", {})
        grid_options["defaultColDef"].update({
            "flex": 1,
            "minWidth": 120
        })

        # Layout normal (garde la height)
        grid_options["domLayout"] = "normal"  # passer à "autoHeight" si tu veux supprimer height & scroll interne

        grid_response = AgGrid(
            df,
            gridOptions=grid_options,
            update_mode=GridUpdateMode.SELECTION_CHANGED,
            height=hauteur,
            allow_unsafe_jscode=True,
            fit_columns_on_grid_load=True,
            theme="balham",  # "streamlit" ou "material" possible
        )

        selected_rows = grid_response.get("selected_rows", []) if grid_response else []
        if isinstance(selected_rows, pd.DataFrame):
            selected_rows = selected_rows.to_dict(orient="records")
        if isinstance(selected_rows, list) and len(selected_rows)>0:
            selected_rows = selected_rows[0]
        else:
            return None
        return selected_rows

    except Exception as e:
        st.error(f"Erreur de chargement des données dans le tableau: {e}")
        return []

def _descriptfis_des_pages():
        st.markdown("""
        <div class="card-container">
            <div class="card" style="font-family: var(--font-default); background-color: var(--color-2); color: var(--color-1);">
                <div class="card-title">📊 Surveillance des flux</div>
                <div class="card-description">Visualisez les flux de données en temps réel et détectez les anomalies.</div>
            </div>
            <div class="card" style="font-family: var(--font-default); background-color: var(--color-2); color: var(--color-1);">
                <div class="card-title">🚨 Alertes & notifications</div>
                <div class="card-description">Recevez des alertes automatiques en cas d'incident ou de seuil critique.</div>
            </div>
            <div class="card" style="font-family: var(--font-default); background-color: var(--color-2); color: var(--color-1);">
                <div class="card-title">📈 Qualité de la donnée</div>
                <div class="card-description">Analysez la qualité des données collectées et identifiez les erreurs.</div>
            </div>
            <div class="card-larged" style="font-family: var(--font-default); background-color: var(--color-2); color: var(--color-2);">
                <div class="card-title">🔄 Actualisation des données</div>
                <div class="card-description">Suivez les mises à jour des jeux de données et leur fréquence.</div>
            </div>
            <div class="card-larged" style="font-family: var(--font-default); background-color: var(--color-2); color: var(--color-1);">
                <div class="card-title">📁 Gestion des référentiels</div>
                <div class="card-description">Administrez les référentiels utilisés dans les flux et les traitements.</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Idée monter le chargement de données effective pour l'outil de surveillance
        st.markdown("<div style='margin-top: 40px;'></div>", unsafe_allow_html=True)
        chargement_container = st.empty()

        with chargement_container.container(horizontal_alignment="center"):
                # Spinner visible
                with st.spinner("⏳ Chargement des données en cours…"):
                    progress_bar = st.progress(0)
                    for i in range(100):
                        time.sleep(0.05)
                        progress_bar.progress(i + 1)
                    time.sleep(1)
                    #st.success("✅ Terminé !")
                    st.write("🟢 Chargement terminé !")
                # Pause pour laisser le message visible un instant
                time.sleep(1)
        # Nettoyage complet
        chargement_container.empty()
        # Invitation à utiliser le barre de naviation latérale pour accéder au pages
        st.info("ℹ️ Utilisez la barre de navigation à gauche pour accéder aux différentes pages de l'application.")

# ---------- Helpers ----------
def _to_bool_any(v) -> bool:
    """Normalise une valeur quelconque en booléen pour is_published."""
    if v is None:
        return False
    if isinstance(v, bool):
        return v
    try:
        if isinstance(v, (int, float)):
            return int(v) == 1
        s = str(v).strip().lower()
        if s in ("true", "1", "yes", "y", "published", "public", "ouvert"):
            return True
        if s in ("false", "0", "no", "n", "unpublished", "private", "restreint", "fermé"):
            return False
        return False
    except Exception:
        return False

def _fmt_dt_series_local(series: pd.Series, tz: ZoneInfo) -> pd.Series:
    """Formate une série ISO en horodatage lisible, localisé."""
    dt = pd.to_datetime(series, errors="coerce", utc=True)
    try:
        return dt.dt.tz_convert(tz).dt.strftime("%Y-%m-%d %H:%M")
    except Exception:
        return dt.dt.strftime("%Y-%m-%d %H:%M")

def afficher_compteurs_visibilite(n_public: int, n_restreint: int) -> None:
    """Affiche deux mini badges 'Public' / 'Restreint' (fallback HTML si sac.tag absent)."""
    try:
        if hasattr(sac, "tag"):
            sac.tag(text=f"Public: {n_public}", color="green", bordered=True)
            sac.tag(text=f"Restreint: {n_restreint}", color="orange", bordered=True)
            return
        if hasattr(sac, "chip"):
            sac.chip(text=f"Public: {n_public}", color="green", check=False)
            sac.chip(text=f"Restreint: {n_restreint}", color="orange", check=False)
            return
    except Exception:
        pass

    st.markdown(
        f"""
        <div class="badges">
            <span class="badge badge--public">Public: {n_public}</span>
            <span class="badge badge--restreint">Restreint: {n_restreint}</span>
        </div>
        """,
        unsafe_allow_html=True
    )

# ------------------ Helpers formatage écart ------------------
def _minutes_from_any(rec: Dict[str, Any]) -> Optional[int]:
    """
    Récupère l'écart en minutes à partir d'un enregistrement de top.
    Tolère 'ecart_min', 'ecart_minutes' ou 'ecart' (secondes -> converties en minutes).
    """
    if rec is None:
        return None
    if "ecart_min" in rec and rec["ecart_min"] is not None:
        try:
            return int(rec["ecart_min"])
        except Exception:
            pass
    if "ecart_minutes" in rec and rec["ecart_minutes"] is not None:
        try:
            return int(rec["ecart_minutes"])
        except Exception:
            pass
    # 'ecart' supposé en secondes
    if "ecart" in rec and rec["ecart"] is not None:
        try:
            return int(int(rec["ecart"]) // 60)
        except Exception:
            pass
    return None

def _format_ecart_0(ecart_min: Optional[int], freq_label: Optional[str]) -> str:
    """
    Formate l'écart en tenant compte de la fréquence:
    - affiche en min/h/j selon la taille
    - ajoute un ratio '×freq' si la fréquence est renseignée (TYPE_FREQUENCE)
    """
    if ecart_min is None:
        return ""
    m = max(0, int(ecart_min))

    # human-friendly
    if m < 60:
        human = f"{m} min"
    elif m < 1440:
        h = m // 60
        r = m % 60
        human = f"{h} h" + (f" {r} min" if r else "")
    else:
        d = m // 1440
        rest = m % 1440
        h = rest // 60
        human = f"{d} j" + (f" {h} h" if h else "")

    # ratio à la fréquence
    ratio_txt = ""
    if freq_label and freq_label in Configurations.TYPE_FREQUENCE and Configurations.TYPE_FREQUENCE.get(freq_label):
        freq_td = Configurations.TYPE_FREQUENCE[freq_label]
        freq_minutes = int(freq_td.total_seconds() // 60)
        if freq_minutes > 0:
            ratio = m / freq_minutes
            # 1 décimale si utile
            ratio_txt = f" • {ratio:.1f}×"

    return human + ratio_txt


def _format_ecart(ecart_min: Optional[int], freq_label: Optional[str]) -> str:
    """
    Formate l'écart en 'J h m s' en tenant compte de la fréquence:
    - affiche en j/h/min/s selon la taille (segments à 0 omis)
    - ajoute un ratio '• freq' si la fréquence est renseignée (TYPE_FREQUENCE)
    NOTE: ecart_min est en minutes (entier attendu), donc 's' sera le plus souvent 0.
    """
    if ecart_min is None:
        return ""

    # normalisation en minutes >= 0
    m_total = max(0, int(ecart_min))

    # conversion en secondes pour une décomposition J/H/M/S (les secondes seront 0 ici)
    total_seconds = m_total * 60

    # décomposition J/H/M/S
    d = total_seconds // 86400
    rest = total_seconds % 86400
    h = rest // 3600
    rest %= 3600
    m = rest // 60
    s = rest % 60  # restera 0 avec un input en minutes entières

    # construction de la chaîne human-friendly en 'J h m s'
    parts = []
    if d > 0:
        parts.append(f"{d} j")
    if h > 0:
        parts.append(f"{h} h")
    if m > 0:
        parts.append(f"{m} min")

    # Règles d'affichage pour les secondes :
    # - si total < 60 s (impossible ici car entrée en minutes), on afficherait "Xs".
    # - sinon, on affiche les secondes seulement si elles sont >0 et qu'il n'y a pas de jours (pour rester concis).
    if s > 0 and d == 0:
        parts.append(f"{s} s")

    # Cas particulier: si tout est 0
    human = " ".join(parts) if parts else "0 s"

    # ratio à la fréquence (Configurations.TYPE_FREQUENCE doit fournir une timedelta)
    ratio_txt = ""
    if freq_label and freq_label in Configurations.TYPE_FREQUENCE and Configurations.TYPE_FREQUENCE.get(freq_label):
        try:
            freq_td = Configurations.TYPE_FREQUENCE[freq_label]
            freq_minutes = int(freq_td.total_seconds() // 60)
            if freq_minutes > 0:
                ratio = m_total / freq_minutes
                ratio_txt = f" • {ratio:.1f}×"
        except Exception:
            # silencieux si la config n'est pas exploitable
            pass

    #return human + ratio_txt
    return human 

def _statut_css(statut: str) -> str:
    s = (statut or "").upper()
    if s in ("OK", "A_JOUR"):
        return "status--ok"
    if s in ("EN_RETARD", "WARNING", "A_SURVEILLER"):
        return "status--warn"
    if s in ("CRITIQUE", "KO"):
        return "status--ko"
    return "status--indet"

def _statut_global_badge(statut_global: str) -> str:
    css = _statut_css(statut_global)
    lib = statut_global or "INDETERMINE"
    return f"<span class='status-badge {css}'>{lib}</span>"

def construire_filtres_options(df: pd.DataFrame) -> Dict[str, List[str]]:
        """Construit les options de filtres (valeurs uniques triées)."""
        def uniques(col):
            return sorted(df[col].dropna().unique().tolist()) if col in df.columns else []

        return {
            "producteurs": uniques("producteur"),
            "visibilites": uniques("visibilite"),
            "statuts": uniques("statut"),
            "frequences": uniques("frequence"),
        }

def _render_value(v: Any) -> None:
    """Rendu typé (DataFrame, dict, list, scalar…)."""
    import pandas as pd
    if isinstance(v, pd.DataFrame):
        st.dataframe(v, use_container_width=True)
    elif isinstance(v, dict):
        with st.expander("Détails (dict)", expanded=False):
            # Rendu clé→valeur simple + possibilité de deep-render
            for kk, vv in v.items():
                st.markdown(f"- **{kk}** :")
                _render_value(vv)  # récursif si tu veux naviguer dans les sous-dicts
    elif isinstance(v, (list, tuple)):
        with st.expander(f"Liste ({len(v)})", expanded=False):
            for i, item in enumerate(v):
                st.markdown(f"- **[{i}]**")
                _render_value(item)
    else:
        # scalaires et autres objets
        st.write(v)

def longueur_anomalies_securisee(valeur: Any) -> int:
    """
    Retourne un nombre d'anomalies de façon robuste :
    - liste -> longueur de la liste
    - dict  -> nombre d'entrées (clés) dans le dictionnaire
    - autres (None, str, int, etc.) -> 0
    """
    if isinstance(valeur, list):
        return len(valeur)
    if isinstance(valeur, dict):
        return len(valeur)  # adapter si ton dict contient des listes par clé
    return 0

def normaliser_colonnes_visibilite(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalise les colonnes de visibilité en chaînes 'true'/'false' (lowercase),
    afin d'assurer des comparaisons fiables même si la source fournit des booléens ou des NaN.
    Colonnes ciblées : 'visibilite_publique', 'visibilite_restreinte'.
    """
    df = df.copy()
    for col in ["visibilite_publique", "visibilite_restreinte"]:
        if col in df.columns:
            df[col] = (
                df[col]
                .astype(str)        # convertit True/False/NaN en chaînes
                .str.strip()
                .str.lower()
                .replace({"none": "", "nan": ""})
            )
    return df

def garantir_colonnes_de_base_v0(df: pd.DataFrame) -> pd.DataFrame:
    """
    Garantit l'existence des colonnes de base attendues par les indicateurs et les filtres,
    en les créant le cas échéant avec des valeurs par défaut.
    Colonnes assurées : producteur, visibilite, statut, frequence,
                        visibilite_publique, visibilite_restreinte, anomalies.
    """
    df = df.copy()
    valeurs_par_defaut = {
        "producteur": "",
        "visibilite": "",
        "statut": "",
        "frequence": "",
        "visibilite_publique": "",
        "visibilite_restreinte": "",
        "anomalies": [],
    }
    for colonne, valeur_defaut in valeurs_par_defaut.items():
        if colonne not in df.columns:
            df[colonne] = valeur_defaut
    return df

def garantir_colonnes_de_base(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    colonnes_json = ["anomalies", "ressources_impacts_json", "matched_blobs_json", "ressources_par_origin_type_json"]
    colonnes_visibilite = ["visibilite", "visibilite_publique", "visibilite_restreinte"]
    colonnes_identite = ["uid", "dataset_id", "producteur", "frequence", "statut"]

    # JSON-like : chaînes "[]"
    for c in colonnes_json:
        if c not in df.columns:
            df = _safe_set_column(df, c, "[]")
        else:
            df[c] = df[c].apply(lambda v: "[]" if (v is None or (isinstance(v, list) and len(v) == 0)) else str(v))

    # Visibilités
    if "visibilite_publique" not in df.columns:
        df = _safe_set_column(df, "visibilite_publique", "false")
    else:
        df["visibilite_publique"] = df["visibilite_publique"].fillna("false").astype(str).str.lower()

    if "visibilite_restreinte" not in df.columns:
        df = _safe_set_column(df, "visibilite_restreinte", "false")
    else:
        df["visibilite_restreinte"] = df["visibilite_restreinte"].fillna("false").astype(str).str.lower()

    # Visibilite globale (si manquante)
    if "visibilite" not in df.columns:
        df = _safe_set_column(
            df, "visibilite",
            (df["visibilite_restreinte"] == "true").map(lambda b: "Restreint" if b else "Non restreint")
        )

    # Identité / texte
    for c in colonnes_identite:
        if c not in df.columns:
            df = _safe_set_column(df, c, "")
        else:
            df[c] = df[c].fillna("").astype(str)

    return df

def longueur_anomalies_securisee(valeur: Any) -> int:
    """
    Retourne un nombre d'anomalies de façon robuste :
    - liste -> longueur de la liste
    - dict  -> nombre d'entrées (clés) dans le dictionnaire
    - autres (None, str, int, etc.) -> 0
    """
    if isinstance(valeur, list):
        return len(valeur)
    if isinstance(valeur, dict):
        return len(valeur)  # adapter si ton dict contient des listes par clé
    return 0

def normaliser_colonnes_visibilite_v0(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalise les colonnes de visibilité en chaînes 'true'/'false' (lowercase),
    afin d'assurer des comparaisons fiables même si la source fournit des booléens ou des NaN.
    Colonnes ciblées : 'visibilite_publique', 'visibilite_restreinte'.
    """
    df = df.copy()
    for col in ["visibilite_publique", "visibilite_restreinte"]:
        if col in df.columns:
            df[col] = (
                df[col]
                .astype(str)        # convertit True/False/NaN en chaînes
                .str.strip()
                .str.lower()
                .replace({"none": "", "nan": ""})
            )
    return df


def normaliser_colonnes_visibilite(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    if "visibilite_publique" in df.columns:
        df["visibilite_publique"] = df["visibilite_publique"].fillna("false").astype(str).str.lower()
        df.loc[~df["visibilite_publique"].isin(["true", "false"]), "visibilite_publique"] = "false"
    else:
        df = _safe_set_column(df, "visibilite_publique", "false")

    if "visibilite_restreinte" in df.columns:
        df["visibilite_restreinte"] = df["visibilite_restreinte"].fillna("false").astype(str).str.lower()
        df.loc[~df["visibilite_restreinte"].isin(["true", "false"]), "visibilite_restreinte"] = "false"
    else:
        df = _safe_set_column(df, "visibilite_restreinte", "false")

    if "visibilite" not in df.columns:
        df = _safe_set_column(
            df, "visibilite",
            (df["visibilite_restreinte"] == "true").map(lambda b: "Restreint" if b else "Non restreint")
        )
    return df


def garantir_colonnes_de_base(df: pd.DataFrame) -> pd.DataFrame:
    """
    Garantit l'existence des colonnes de base attendues par les indicateurs et les filtres,
    en les créant le cas échéant avec des valeurs par défaut.
    Colonnes assurées : producteur, visibilite, statut, frequence,
                        visibilite_publique, visibilite_restreinte, anomalies.
    """
    df = df.copy()
    valeurs_par_defaut = {
        "producteur": "",
        "visibilite": "",
        "statut": "",
        "frequence": "",
        "visibilite_publique": "",
        "visibilite_restreinte": "",
        "anomalies": [],
    }
    for colonne, valeur_defaut in valeurs_par_defaut.items():
        if colonne not in df.columns:
            df[colonne] = valeur_defaut
    return df

def produire_indicateurs_v0(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Calcule un ensemble d'indicateurs à partir d'un DataFrame des JDD.
    - nb_jdd : nombre total de lignes
    - nb_public_oui / nb_public_non : comptages basés sur 'visibilite_publique'
    - nb_restreint_oui / nb_restreint_non : comptages basés sur 'visibilite_restreinte'
    - nb_en_retard : nombre de JDD avec statut 'EN_RETARD'
    - nb_anomalies_total : somme des anomalies (listes/dicts)
    - nb_producteurs : nombre de producteurs distincts
    - repartition_statut : distribution des statuts (value_counts)
    """
    # Préparations (sécurité)
    df = garantir_colonnes_de_base(df)
    df = normaliser_colonnes_visibilite(df)

    nb_jdd = len(df)
    nb_public_oui = int((df["visibilite_publique"] == "true").sum())
    nb_public_non = int((df["visibilite_publique"] == "false").sum())

    nb_restreint_oui = int((df["visibilite_restreinte"] == "true").sum())
    nb_restreint_non = int((df["visibilite_restreinte"] == "false").sum())

    nb_en_retard = int((df["statut"] == "EN_RETARD").sum())

    nb_anomalies_total = int(df["anomalies"].apply(longueur_anomalies_securisee).sum())

    nb_producteurs = df["producteur"].nunique()

    repartition_statut = df["statut"].value_counts(dropna=False).to_dict()

    return {
        "nb_jdd": nb_jdd,
        "nb_public_oui": nb_public_oui,
        "nb_public_non": nb_public_non,
        "nb_restreint_oui": nb_restreint_oui,
        "nb_restreint_non": nb_restreint_non,
        "nb_en_retard": nb_en_retard,
        "nb_anomalies_total": nb_anomalies_total,
        "nb_producteurs": nb_producteurs,
        "repartition_statut": repartition_statut,
    }



def produire_filtres_0(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Génère des options de filtres triées et nettoyées à partir du DataFrame.
    Champs : producteur, visibilite, statut, frequence.
    Les valeurs sont converties en chaînes et les NaN sont exclus.
    """
    df = garantir_colonnes_de_base(df)

    def _options(col: str) -> list:
        return sorted(df[col].dropna().astype(str).unique().tolist())

    return {
        "producteur": _options("producteur"),
        "visibilite": _options("visibilite"),
        "statut": _options("statut"),
        "frequence": _options("frequence"),
    }


def produire_indicateurs(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Docstring for produire_indicateurs
    
    :param df: Description
    :type df: pd.DataFrame
    :return: Description
    :rtype: Dict[str, Any]
    """
    df = normaliser_colonnes_visibilite(df)
    nb_jdd = len(df)
    nb_restreint_oui = int((df["visibilite_restreinte"] == "true").sum())
    nb_restreint_non = int((df["visibilite_restreinte"] == "false").sum())

    return {
        "nb_jdd": nb_jdd,
        "nb_restreint_oui": nb_restreint_oui,
        "nb_restreint_non": nb_restreint_non,
    }


def produire_filtres_v0(df: pd.DataFrame) -> Dict[str, Any]:
    df = garantir_colonnes_de_base(df)

    def _options(col: str) -> list:
        if col not in df.columns:
            return []
        return sorted(df[col].dropna().astype(str).unique().tolist())

    return {
        "producteur": _options("producteur"),
        "visibilite": _options("visibilite"),
        "statut": _options("statut"),
        "frequence": _options("frequence"),
    }


def produire_filtres_v2(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Génère des options de filtres triées, nettoyées et UNIQUES par colonne.
    Ajout : éclate les producteurs séparés par virgule.
    """

    PLACEHOLDER = "— Aucune —"

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

        vals = vals.astype(str).map(lambda x: x.strip())
        vals = vals.replace(
            {"": PLACEHOLDER, "nan": PLACEHOLDER, "None": PLACEHOLDER, "NONE": PLACEHOLDER}
        )

        uniques = _dedupe(vals.tolist())
        uniques = sorted(uniques, key=lambda x: x.lower())

        if PLACEHOLDER in uniques:
            uniques = [PLACEHOLDER] + [v for v in uniques if v != PLACEHOLDER]

        return uniques

    # 🔥 Spécifique aux producteurs : éclatement par virgule
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
        if s.empty:
            return []

        def _label(x: Any) -> str:
            if pd.isna(x): return PLACEHOLDER
            if isinstance(x, bool): return "Restreint" if x else "Public"
            xs = str(x).strip().lower()
            if xs in {"true", "1", "oui", "yes"}: return "Restreint"
            if xs in {"false", "0", "non", "no"}: return "Public"
            return PLACEHOLDER

        cleaned = s.map(_label)
        return _nettoyer(cleaned)

    # --- Retour final ---
    return {
        "is_restricted": _opt_restriction(),
        "metadata_default_title_value": _nettoyer(_serie(df, "metadata_default_title_value")),
        "metadata_dcat_accrualperiodicity_value": _nettoyer(_serie(df, "metadata_dcat_accrualperiodicity_value")),
        "metadata_default_publisher_value": _nettoyer_producteurs(_serie(df, "metadata_default_publisher_value")),
    }


def produire_filtres_v1(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Génère des options de filtres triées et nettoyées à partir du DataFrame.
    Champs gérés :
      - is_restricted                         -> "Public" / "Restreint" / "— Aucune —"
      - metadata_default_title_value          -> texte ou "— Aucune —"
      - metadata_dcat_accrualperiodicity_value-> texte ou "— Aucune —"
      - metadata_default_publisher_value      -> texte ou "— Aucune —"

    Règles :
      - Si la colonne manque, renvoie [] pour cette clé.
      - NaN/None/"": remplacés par "— Aucune —".
      - Tout est converti en str, .strip() appliqué.
      - Tri alphabétique, avec "— Aucune —" forcé en premier si présent.
    """

    PLACEHOLDER = "— Aucune —"

    def _serie_col(df: pd.DataFrame, col: str) -> pd.Series:
        """Retourne la série si existe, sinon une série vide."""
        return df[col] if (isinstance(df, pd.DataFrame) and col in df.columns) else pd.Series(dtype="object")

    def _options_generiques(col: str) -> List[str]:
        """Options génériques pour colonnes texte : nettoyage + tri + placeholder en tête."""
        s = _serie_col(df, col)
        if s.empty:
            return []
        # to string + strip
        s = s.astype(str).map(lambda x: x.strip())
        # Normalise les valeurs vides / 'nan' / 'None'
        s = s.replace({"": PLACEHOLDER, "nan": PLACEHOLDER, "None": PLACEHOLDER, "NONE": PLACEHOLDER})
        vals = sorted(s.dropna().unique().tolist(), key=lambda v: v.lower())
        # Place le placeholder en premier s'il existe
        if PLACEHOLDER in vals:
            vals = [PLACEHOLDER] + [v for v in vals if v != PLACEHOLDER]
        return vals

    def _options_restriction() -> List[str]:
        """Options spécifiques pour is_restricted (booléen/texte)."""
        s = _serie_col(df, "is_restricted")
        if s.empty:
            return []
        # Normalisation booléen/texte -> labels lisibles
        def _to_label(x: Any) -> str:
            if pd.isna(x):
                return PLACEHOLDER
            # bool direct
            if isinstance(x, bool):
                return "Restreint" if x else "Public"
            # numériques 0/1
            if isinstance(x, (int, float)) and not isinstance(x, bool):
                return "Restreint" if int(x) != 0 else "Public"
            # texte
            xs = str(x).strip().lower()
            if xs in {"true", "1", "oui", "yes", "y"}:
                return "Restreint"
            if xs in {"false", "0", "non", "no", "n"}:
                return "Public"
            if xs in {"", "nan", "none"}:
                return PLACEHOLDER
            # Valeur inattendue -> garder la valeur brute affichable
            return str(x).strip()

        vals = sorted(s.map(_to_label).dropna().unique().tolist(), key=lambda v: v.lower())
        if PLACEHOLDER in vals:
            vals = [PLACEHOLDER] + [v for v in vals if v != PLACEHOLDER]
        return vals

    return {
        # On nomme les clés de sortie de façon explicite et identique aux colonnes
        "is_restricted": _options_restriction(),
        "metadata_default_title_value": _options_generiques("metadata_default_title_value"),
        "metadata_dcat_accrualperiodicity_value": _options_generiques("metadata_dcat_accrualperiodicity_value"),
        "metadata_default_publisher_value": _options_generiques("metadata_default_publisher_value"),
    }



# ---------- Projections & filtres ----------
def projeter_visibilite(df_des_analyses: pd.DataFrame, jdds_odre: List[JddOdre]) -> pd.DataFrame:
    """Ajoute la colonne 'visibilite' à df_des_analyses via un mapping id -> Public/Restreint à partir des objets métier."""
    if df_des_analyses is None or df_des_analyses.empty or "id" not in df_des_analyses.columns:
        return df_des_analyses if isinstance(df_des_analyses, pd.DataFrame) else pd.DataFrame()

    map_visibilite: Dict[Any, str] = {}
    if isinstance(jdds_odre, list) and jdds_odre:
        for j in jdds_odre:
            meta = j.metadonnees or {}
            raw = meta.get("is_published", meta.get("metadata_default_is_published_value"))
            map_visibilite[j.id_jdd_odre] = "Public" if _to_bool_any(raw) else "Restreint"

    df = df_des_analyses.copy()
    df["visibilite"] = df["id"].map(map_visibilite)
    return df

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
    elif choix_res == "Non restreint":
        df = df[df["is_restricted"].astype(str).str.strip().str.lower() == "false"]

    return df

def obtenir_df_filtre(df_prepared_key: str = "df_prepared",
                      df_filtre_debug_key: str = "df_filtre_debug") -> pd.DataFrame:
    """
    Retourne le DataFrame filtré courant, en priorisant les valeurs dans st.session_state.

    Priorité :
      1) st.session_state[df_filtre_debug_key] si présent et non vide,
      2) st.session_state[df_prepared_key] si présent et non vide,
      3) DataFrame vide s'il n'y a rien.

    Paramètres:
      df_prepared_key: clé session pour le DF préparé (par défaut 'df_prepared').
      df_filtre_debug_key: clé session pour le DF filtré (par défaut 'df_filtre_debug').
    """
    df_filtre = st.session_state.get(df_filtre_debug_key)
    if isinstance(df_filtre, pd.DataFrame) and not df_filtre.empty:
        return df_filtre

    df_prepared = st.session_state.get(df_prepared_key)
    if isinstance(df_prepared, pd.DataFrame) and not df_prepared.empty:
        return df_prepared

    return pd.DataFrame()


# ---------- Blocs UI ----------
# --- Colonne gauche ---
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

    PLACEHOLDER = "— Aucune —"

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

        vals = vals.astype(str).map(lambda x: x.strip())
        vals = vals.replace(
            {"": PLACEHOLDER, "nan": PLACEHOLDER, "None": PLACEHOLDER, "NONE": PLACEHOLDER}
        )

        uniques = _dedupe(vals.tolist())
        uniques = sorted(uniques, key=lambda x: x.lower())

        if PLACEHOLDER in uniques:
            uniques = [PLACEHOLDER] + [v for v in uniques if v != PLACEHOLDER]

        return uniques

    # 🔥 Spécifique aux producteurs : éclatement par virgule
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
        if s.empty:
            return []

        def _label(x: Any) -> str:
            if pd.isna(x): return PLACEHOLDER
            if isinstance(x, bool): return "Restreint" if x else "Public"
            xs = str(x).strip().lower()
            if xs in {"true", "1", "oui", "yes"}: return "Restreint"
            if xs in {"false", "0", "non", "no"}: return "Public"
            return PLACEHOLDER

        cleaned = s.map(_label)
        return _nettoyer(cleaned)

    # --- Retour final ---
    return {
        "is_restricted": _opt_restriction(),
        "metadata_default_title_value": _nettoyer(_serie(df, "metadata_default_title_value")),
        "metadata_dcat_accrualperiodicity_value": _nettoyer(_serie(df, "metadata_dcat_accrualperiodicity_value")),
        "metadata_default_publisher_value": _nettoyer_producteurs(_serie(df, "metadata_default_publisher_value")),
    }



def bloc_indicateurs_et_filtres(df_analyse: pd.DataFrame) -> None:
    """
    """
    try:
        df = df_analyse.copy()
        filtres_options = produire_filtres(df)

        sac.divider(label='🧭 Filtres', icon='filter', align='center', color='blue', key="Filtre")

        # -- Préparation des options -- #
        producteurs_options = filtres_options.get("metadata_default_publisher_value", [])
        VALEUR_PRODUCTEUR_PAR_DEFAUT = "NATRAN"
        producteur_par_default = VALEUR_PRODUCTEUR_PAR_DEFAUT if VALEUR_PRODUCTEUR_PAR_DEFAUT in producteurs_options else None

        frequences_options = filtres_options.get("metadata_dcat_accrualperiodicity_value", [])
        VALEUR_FREQUENCE_PAR_DEFAUT = "Annuelle"
        frequence_par_default = VALEUR_FREQUENCE_PAR_DEFAUT if VALEUR_FREQUENCE_PAR_DEFAUT in frequences_options else None

        # Visibilités
        has_res = "is_restricted" in df.columns
        opts_res = ["Tous"]
        if has_res and (df["is_restricted"] == "true").any():
            opts_res.append("Restreint")
        if has_res and (df["is_restricted"] == "false").any():
            opts_res.append("Non restreint")

        # -- Initialisation des valeurs en session (1ère exécution uniquement) -- #
        if "selecteur_producteur" not in st.session_state:
            st.session_state["selecteur_producteur"] = [producteur_par_default] if producteur_par_default else []

        if "selecteur_frequence" not in st.session_state:
            st.session_state["selecteur_frequence"] = [frequence_par_default] if frequence_par_default else []

        if "selecteur_visibilite_restreinte" not in st.session_state:
            st.session_state["selecteur_visibilite_restreinte"] = "Tous"

        # -- Sanitation : on s'assure que la sélection est incluse dans les options -- #
        st.session_state["selecteur_producteur"] = [
            v for v in st.session_state["selecteur_producteur"] if v in producteurs_options
        ]
        st.session_state["selecteur_frequence"] = [
            v for v in st.session_state["selecteur_frequence"] if v in frequences_options
        ]
        if st.session_state["selecteur_visibilite_restreinte"] not in opts_res:
            st.session_state["selecteur_visibilite_restreinte"] = "Tous"


        # -- Application des filtres (ton helper) -- #
        df_filtre = appliquer_filtres_df(df)
        st.session_state["df_filtre_debug"] = df_filtre.copy()  # ✅ DataFrame

        # KPI dynamiques
        indicateurs_filtres = produire_indicateurs(df_filtre)
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
                    <span class="kpi-value kpi-total">{df}</span>
                </td>
                </tr>
                <tr>
                <td class="kpi-restreint">🛡️ Restreint</td>
                <td class="kpi-value val-restreint">{nb_restreint_oui}</td>
                <td class="kpi-nonrestreint">✅ Non restreint</td>
                <td class="kpi-value val-nonrestreint">{nb_restreint_non}</td>
                </tr>
                <tr>
                <td class="kpi-restreint">🧭 Filtrage</td>
                <td class="kpi-value val-restreint">{len(df_filtre)} lignes</td>
                <td class="kpi-nonrestreint">Sur</td>
                <td class="kpi-value val-nonrestreint">{len(df)} initiales</td>
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
                placeholder="Choisir un producteur Ex: NATRAN",
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
                options=opts_res,
                key="selecteur_visibilite_restreinte",
            )

        with ligne_2_col1:
            # Bouton de réinitialisation de tous les filtres
            def _reset_all():
                st.session_state["selecteur_producteur"] = []
                st.session_state["selecteur_frequence"] = []
                st.session_state["selecteur_visibilite_restreinte"] = "Tous"
                # Optionnel : forcer le rerun immédiat (souvent pas nécessaire)
                # st.rerun()

            st.button(
                label="↺ Réinitialiser tous les filtres",
                on_click=_reset_all,
            )
    except Exception as e:
        st.warning({e})




# --- Colonne droite ---
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

def bloc_statut_global_et_top_3(indicateurs: Dict[str, Any],
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
        <div class="kpi kpi-center">
          <span class='kpi__value'>Statut global {_statut_global_badge(statut_global)}</span>
          <span class="badge badge--public">✅ À jour: {pct_ok}%</span>
          <span class="kpi-pill kpi-pill--ret">⏳ En retard: {pct_ret}%</span>
          <span class="kpi-pill kpi-pill--cri">🚨 Critiques: {pct_cri}%</span>
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



