"""Thème Ant Design pour Streamlit."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parents[2]
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from app import config

logger = logging.getLogger(__name__)

# ==============================================================================
# TOKENS ANT DESIGN
# ==============================================================================

ANT_TOKENS = {
    "colorPrimary": config.THEME["primary_color"],
    "colorSuccess": config.THEME["success_color"],
    "colorWarning": config.THEME["warning_color"],
    "colorError": config.THEME["danger_color"],
    "colorInfo": config.THEME["info_color"],
    "borderRadius": 6,
    "fontFamily": "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
}

# ==============================================================================
# COMPONENT STYLES
# ==============================================================================

COMPONENT_STYLES = {
    "button": {
        "height": "32px",
        "padding": "0 16px",
        "border_radius": "4px",
        "font_size": "14px",
    },
    "input": {
        "height": "32px",
        "padding": "0 12px",
        "border_radius": "4px",
        "border_color": config.THEME["border_color"],
    },
    "card": {
        "border_radius": "8px",
        "border": f"1px solid {config.THEME['border_color']}",
        "padding": "16px",
        "background": "#FFFFFF",
    },
}


def get_color(status: str) -> str:
    """Récupère la couleur selon le statut.
    
    Args:
        status: success | warning | danger | info | primary
        
    Returns:
        Valeur hex de la couleur
    """
    try:
        color_map = {
            "success": config.THEME["success_color"],
            "warning": config.THEME["warning_color"],
            "danger": config.THEME["danger_color"],
            "info": config.THEME["info_color"],
            "primary": config.THEME["primary_color"],
        }
        return color_map.get(status, config.THEME["primary_color"])
    except Exception:
        logger.exception("Echec resolution couleur pour status=%s", status)
        return "#1F77B4"
