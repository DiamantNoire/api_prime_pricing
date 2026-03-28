"""Composants réutilisables pour l'application."""

from __future__ import annotations

import streamlit as st

try:
    import streamlit_antd_components as sac
except ImportError as exc:
    raise RuntimeError(
        "Le paquet 'streamlit-antd-components' est requis."
    ) from exc


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


def info_box(
    label: str,
    value: str | int | float,
    description: str | None = None,
    icon: str = "info",
) -> None:
    """Affiche une boîte d'information.
    
    Args:
        label: Libellé de l'info
        value: Valeur à afficher
        description: Description optionnelle
        icon: Icône SAC
    """
    sac.result(
        label=label,
        description=description or str(value),
        status="info",
    )


def section_divider(title: str, icon: str | None = None) -> None:
    """Affiche un séparateur de section.
    
    Args:
        title: Titre de la section
        icon: Icône optionnelle
    """
    sac.divider(label=title, icon=icon, align="center")


def loading_spinner(text: str = "Chargement...") -> None:
    """Affiche un spinner de chargement.
    
    Args:
        text: Texte à afficher
    """
    with st.spinner(text):
        st.empty()


def success_message(title: str, description: str | None = None) -> None:
    """Affiche un message de succès.
    
    Args:
        title: Titre du message
        description: Description optionnelle
    """
    sac.result(
        label=title,
        description=description or "Opération réussie",
        status="success",
    )


def error_message(title: str, description: str | None = None) -> None:
    """Affiche un message d'erreur.
    
    Args:
        title: Titre du message
        description: Description optionnelle
    """
    sac.result(
        label=title,
        description=description or "Une erreur est survenue",
        status="error",
    )


def warning_message(title: str, description: str | None = None) -> None:
    """Affiche un message d'avertissement.
    
    Args:
        title: Titre du message
        description: Description optionnelle
    """
    sac.result(
        label=title,
        description=description or "Avertissement",
        status="warning",
    )
