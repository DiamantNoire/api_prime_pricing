"""Page tableau de bord."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import streamlit as st

try:
    import streamlit_antd_components as sac
except ImportError as exc:
    raise RuntimeError("Le paquet 'streamlit-antd-components' est requis.") from exc

SRC_DIR = Path(__file__).resolve().parents[2]
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from app.components import header, section_divider
from app.config import API_BASE_URL
from app.services import HealthMonitor

logger = logging.getLogger(__name__)


@st.cache_data(ttl=600)
def get_health_status(
    api_base_url: str = API_BASE_URL, db_path: str = "db/prime_pricing.sqlite"
):
    """
    Récupère l'état de santé de tous les services.
    Les résultats sont cachés pendant 600 secondes.
    """
    monitor = HealthMonitor(api_base_url=api_base_url, db_path=db_path, timeout=5)
    return monitor.check_all_health()


def get_status_icon(status: str) -> str:
    """Retourne l'icône appropriée pour le statut."""
    status_icons = {
        "ok": "✅",
        "error": "⚠️",
        "unreachable": "🔴",
        "rate_limited": "⏳",
    }
    return status_icons.get(status, "❓")


def get_sac_status(status: str) -> str:
    """Convertit le statut en format attendu par sac.result."""
    status_map = {
        "ok": "success",
        "error": "warning",
        "unreachable": "error",
        "rate_limited": "warning",
    }
    return status_map.get(status, "warning")


def render_health_card(health_status, col):
    """Affiche une carte de statut de santé."""
    with col:
        icon = get_status_icon(health_status.status)
        sac_status = get_sac_status(health_status.status)

        sac.result(
            label=f"{icon} {health_status.name}",
            description=health_status.description,
            status=sac_status,
        )


def render_health_details(health_status):
    """Affiche les détails d'un statut de santé."""
    if health_status.details:
        with st.expander(f"📋 Détails - {health_status.name}"):
            for key, value in health_status.details.items():
                if isinstance(value, dict):
                    st.json(value)
                else:
                    st.write(f"**{key}:** {value}")


def render() -> None:
    """Affiche la page tableau de bord."""
    try:
        header("Tableau de bord", "Vue d'ensemble du système")

        section_divider("État du système", icon="speedometer")

        # Vérification uniquement sur action utilisateur
        col_btn_1, col_btn_2, _ = st.columns([1, 1, 2])
        with col_btn_1:
            run_check = st.button(
                "🩺 Vérifier la santé", type="primary", use_container_width=True
            )
        with col_btn_2:
            if st.button("🔄 Vider cache", use_container_width=True):
                st.cache_data.clear()
                st.session_state.pop("dashboard_health_statuses", None)
                st.rerun()

        st.markdown("---")

        # Affichage des statuts de santé
        try:
            if run_check:
                st.session_state["dashboard_health_statuses"] = get_health_status()

            health_statuses = st.session_state.get("dashboard_health_statuses")
            if not health_statuses:
                st.info(
                    "Cliquez sur 'Vérifier la santé' pour lancer le contrôle global."
                )
                return

            # Résumé général
            healthy_services = sum(
                1 for s in health_statuses.values() if s.is_healthy()
            )
            total_services = len(health_statuses)

            if healthy_services == total_services:
                st.success(
                    f"✅ Tous les services sont opérationnels ({healthy_services}/{total_services})"
                )
            elif healthy_services > 0:
                st.warning(
                    f"⚠️ {total_services - healthy_services} service(s) présentent des problèmes "
                    f"({healthy_services}/{total_services} sains)"
                )
            else:
                st.error(
                    f"🔴 Tous les services sont indisponibles (0/{total_services} sains)"
                )

            rate_limited_count = sum(
                1 for s in health_statuses.values() if s.status == "rate_limited"
            )
            if rate_limited_count:
                st.info(
                    f"⏳ {rate_limited_count} service(s) limité(s) par Render (HTTP 429). "
                    "Attendez un peu avant de rafraîchir."
                )

            st.markdown("---")

            # Affichage des cartes de santé
            st.subheader("🏥 État des services")

            # Rangée 1 : API principale + Base de données
            col1, col2 = st.columns(2)
            render_health_card(health_statuses["main_api"], col1)
            render_health_card(health_statuses["database"], col2)

            st.markdown("---")

            # Section des détails
            st.subheader("Détails des services")

            tab1, tab2 = st.tabs(
                [
                    "🌐 API Principale",
                    "💾 Base de données",
                ]
            )

            with tab1:
                render_health_details(health_statuses["main_api"])

            with tab2:
                render_health_details(health_statuses["database"])

        except Exception as exc:
            logger.exception("Erreur lors de la vérification de la santé")
            st.error(
                f"❌ Erreur lors de la vérification de l'état: {exc}\n\n"
                f"Vérifiez que l'API est en cours d'exécution et accessible."
            )

        st.divider()

        # Section d'informations
        with st.expander("ℹ️ À propos de ce tableau de bord"):
            st.markdown("""
            Ce tableau de bord affiche l'état de santé de l'application en temps réel.

            **Services surveillés:**
            - 🌐 **API Principale** - État général de l'API FastAPI
            - 💾 **Base de données** - État et statistiques de la base SQLite

            **Statuts possibles:**
            - ✅ **OK** - Le service est opérationnel
            - ⚠️ **Erreur** - Le service a rencontré un problème
            - 🔴 **Indisponible** - Le service ne peut pas être atteint
            - ⏳ **Rate limited** - Limite de requêtes atteinte (HTTP 429)

            **Notes:**
            - Le contrôle ne se lance que sur clic du bouton "Vérifier la santé"
            - Les résultats sont mis en cache pendant 600 secondes pour éviter de surcharger l'API
            - Utilisez le bouton "Vider cache" pour forcer une mise à jour immédiate
            - Les détails techniques sont disponibles dans les onglets ci-dessus
            """)

        st.info(
            "💡 Utilise le menu de navigation pour explorer les différentes sections."
        )

    except Exception:
        logger.exception("Echec du rendu complet de la page dashboard")
        st.error(
            "Une erreur critique est survenue lors du chargement du tableau de bord."
        )
