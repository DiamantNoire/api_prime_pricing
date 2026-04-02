"""Composant spinner de chargement."""

from __future__ import annotations

import streamlit as st


def loading_spinner(text: str = "Chargement...") -> None:
    """Affiche un spinner de chargement.

    Args:
        text: Texte à afficher
    """
    with st.spinner(text):
        st.empty()
