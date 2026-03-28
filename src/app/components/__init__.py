"""Composants réutilisables pour l'application."""

from __future__ import annotations

import logging

import streamlit as st

try:
    import streamlit_antd_components as sac
except ImportError as exc:
    raise RuntimeError(
        "Le paquet 'streamlit-antd-components' est requis."
    ) from exc

logger = logging.getLogger(__name__)


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
    try:
        sac.result(
            label=label,
            description=description or str(value),
            status="info",
        )
    except Exception:
        logger.exception("Echec du rendu info_box: %s", label)
        st.info(description or str(value))


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
    try:
        sac.result(
            label=title,
            description=description or "Opération réussie",
            status="success",
        )
    except Exception:
        logger.exception("Echec du rendu success_message: %s", title)
        st.success(description or "Opération réussie")


def error_message(title: str, description: str | None = None) -> None:
    """Affiche un message d'erreur.
    
    Args:
        title: Titre du message
        description: Description optionnelle
    """
    try:
        sac.result(
            label=title,
            description=description or "Une erreur est survenue",
            status="error",
        )
    except Exception:
        logger.exception("Echec du rendu error_message: %s", title)
        st.error(description or "Une erreur est survenue")


def warning_message(title: str, description: str | None = None) -> None:
    """Affiche un message d'avertissement.
    
    Args:
        title: Titre du message
        description: Description optionnelle
    """
    try:
        sac.result(
            label=title,
            description=description or "Avertissement",
            status="warning",
        )
    except Exception:
        logger.exception("Echec du rendu warning_message: %s", title)
        st.warning(description or "Avertissement")
