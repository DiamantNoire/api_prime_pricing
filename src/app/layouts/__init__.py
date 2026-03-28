"""Layout principal de l'application."""

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

from app.config import APP_ICON, APP_NAME, PAGES

logger = logging.getLogger(__name__)


def sidebar_menu() -> str | None:
    """Affiche le menu de navigation dans la sidebar.
    
    Returns:
        La clé de la page sélectionnée ou None
    """
    try:
        with st.sidebar:
            st.title(f"{APP_ICON} {APP_NAME}")
            st.divider()

            menu_items = [
                sac.MenuItem(
                    label=page_config["name"],
                    icon=page_config["icon"],
                )
                for page_key, page_config in PAGES.items()
            ]

            selected = sac.menu(menu_items, open_all=False)

            st.divider()
            st.caption("v0.1.0 - Développement")

        return selected
    except Exception:
        logger.exception("Echec du rendu de la sidebar")
        st.error("Erreur lors du rendu du menu de navigation.")
        return None


def main_layout(page_key: str | None) -> str | None:
    """Configure le layout principal avec sidebar et contenu.
    
    Args:
        page_key: Clé de la page courante
        
    Returns:
        La page sélectionnée
    """
    selected_page = sidebar_menu()
    return selected_page or page_key


def footer() -> None:
    """Affiche un footer standardisé."""
    try:
        st.divider()
        col1, col2, col3 = st.columns(3)
        with col1:
            st.caption("© 2026 Prime Pricing")
        with col2:
            st.caption("Version 0.1.0")
        with col3:
            st.caption("Dev Environment")
    except Exception:
        logger.exception("Echec du rendu du footer")
