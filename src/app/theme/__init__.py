"""Thème Ant Design pour Streamlit."""

from __future__ import annotations

from . import config

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
    color_map = {
        "success": config.THEME["success_color"],
        "warning": config.THEME["warning_color"],
        "danger": config.THEME["danger_color"],
        "info": config.THEME["info_color"],
        "primary": config.THEME["primary_color"],
    }
    return color_map.get(status, config.THEME["primary_color"])
