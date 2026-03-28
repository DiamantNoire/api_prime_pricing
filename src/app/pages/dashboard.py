"""Page tableau de bord."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import streamlit as st

try:
    import streamlit_antd_components as sac
except ImportError as exc:
    raise RuntimeError(
        "Le paquet 'streamlit-antd-components' est requis."
    ) from exc

SRC_DIR = Path(__file__).resolve().parents[2]
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from app.components import header, section_divider, success_message
from app.config import FEATURES

logger = logging.getLogger(__name__)


def render() -> None:
    """Affiche la page tableau de bord."""
    try:
        header("Tableau de bord", "Vue d'ensemble du système")

        section_divider("État du système", icon="speedometer")

        col1, col2, col3 = st.columns(3)
        with col1:
            sac.result(
                label="API Frequence",
                description="Status: operational",
                status="success",
            )
        with col2:
            sac.result(
                label="API Severite",
                description="Status: operational",
                status="success",
            )
        with col3:
            sac.result(
                label="Base de données",
                description="Status: connected",
                status="success",
            )

        section_divider("Module app", icon="rocket")
        success_message(
            "Structure initialisée",
            "Le module src/app est prêt pour développement avec Streamlit + Ant Design.",
        )

        section_divider("Fonctionnalités activées", icon="check2-circle")

        cols = st.columns(len(FEATURES))
        for idx, (feature_key, is_enabled) in enumerate(FEATURES.items()):
            with cols[idx]:
                status = "success" if is_enabled else "warning"
                label = feature_key.replace("enable_", "").replace("_", " ").title()
                sac.result(
                    label=label,
                    description="Activée" if is_enabled else "Désactivée",
                    status=status,
                )

        st.divider()
        st.info("💡 Utilise le menu de navigation pour explorer les différentes sections.")
    except Exception:
        logger.exception("Echec du rendu de la page dashboard")
        st.error("Une erreur est survenue lors du chargement du tableau de bord.")
