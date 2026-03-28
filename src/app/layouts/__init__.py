"""Layout principal de l'application."""

from __future__ import annotations

import streamlit as st

try:
    import streamlit_antd_components as sac
except ImportError as exc:
    raise RuntimeError(
        "Le paquet 'streamlit-antd-components' est requis."
    ) from exc

from ..config import APP_NAME, APP_ICON, PAGES


def sidebar_menu() -> str | None:
    """Affiche le menu de navigation dans la sidebar.
    
    Returns:
        La clé de la page sélectionnée ou None
    """
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
    st.divider()
    col1, col2, col3 = st.columns(3)
    with col1:
        st.caption("© 2026 Prime Pricing")
    with col2:
        st.caption("Version 0.1.0")
    with col3:
        st.caption("Dev Environment")
