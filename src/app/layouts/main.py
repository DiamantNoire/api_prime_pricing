"""Layout principal de l'application."""

from __future__ import annotations

import logging

from .sidebar import sidebar_menu

logger = logging.getLogger(__name__)


def main_layout(page_key: str | None) -> str | None:
    """Configure le layout principal avec sidebar et contenu.

    Args:
        page_key: Clé de la page courante

    Returns:
        La page sélectionnée
    """
    selected_page = sidebar_menu()
    return selected_page or page_key
