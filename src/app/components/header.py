"""Composant header standardisé."""

from __future__ import annotations

import streamlit as st


def header(title: str, subtitle: str | None = None, icon: str | None = None) -> None:
    """Affiche un header standardisé.
    
    Args:
        title: Titre principal
        subtitle: Sous-titre optionnel
        icon: Emoji ou icône optionnelle
    """
    if icon:
        st.title(f"{icon} {title}")
    else:
        st.title(title)
    if subtitle:
        st.caption(subtitle)
