"""Tokens Ant Design pour la configuration du thème."""

from __future__ import annotations

import sys
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parents[2]
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from app import config

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
