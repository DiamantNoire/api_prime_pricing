"""Sidebar de navigation."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import streamlit as st

SRC_DIR = Path(__file__).resolve().parents[2]
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from app.config import APP_ICON, APP_NAME

logger = logging.getLogger(__name__)


def sidebar_menu() -> str | None:
    """Affiche le menu de navigation dans la sidebar.
    
    Returns:
        La clé de la page sélectionnée ou None
    """
    try:
        with st.sidebar:
            st.caption("App")
            st.title(f"{APP_ICON} {APP_NAME}")
            st.divider()
            st.caption("v0.1.0 - Développement")

        return None
    except Exception:
        logger.exception("Echec du rendu de la sidebar")
        st.error("Erreur lors du rendu du menu de navigation.")
        return None
