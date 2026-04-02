"""Composant séparateur de section."""

from __future__ import annotations

import logging

import streamlit as st

try:
    import streamlit_antd_components as sac
except ImportError as exc:
    raise RuntimeError("Le paquet 'streamlit-antd-components' est requis.") from exc

logger = logging.getLogger(__name__)


def section_divider(title: str, icon: str | None = None) -> None:
    """Affiche un séparateur de section.

    Args:
        title: Titre de la section
        icon: Icône optionnelle
    """
    try:
        sac.divider(label=title, icon=icon, align="center")
    except Exception:
        logger.exception("Echec du rendu section_divider: %s", title)
        st.subheader(title)
