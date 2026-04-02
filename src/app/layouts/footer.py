"""Footer de l'application."""

from __future__ import annotations

import logging

import streamlit as st

logger = logging.getLogger(__name__)


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
