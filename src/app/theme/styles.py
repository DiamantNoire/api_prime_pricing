"""Styles des composants UI."""

from __future__ import annotations

import sys
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parents[2]
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from app import config

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
