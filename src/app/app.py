from __future__ import annotations

import logging
import sys
from pathlib import Path

import streamlit as st

# Permet d'executer l'app via `streamlit run src/app/app.py`
# en rendant le package `app` resolvable depuis /app/src.
SRC_DIR = Path(__file__).resolve().parents[1]
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from app import config
from app.layouts import footer, main_layout
from app.pages import contrat, dashboard, inference

logging.basicConfig(level=getattr(logging, config.LOG_LEVEL, logging.INFO), format=config.LOG_FORMAT)
logger = logging.getLogger(__name__)


# ==============================================================================
# PAGE CONFIG
# ==============================================================================

st.set_page_config(
    page_title=config.APP_NAME,
    page_icon=config.APP_ICON,
    layout=config.APP_LAYOUT,
    initial_sidebar_state=config.APP_INITIAL_SIDEBAR_STATE,
)

# ==============================================================================
# SESSION STATE INIT
# ==============================================================================

if "current_page" not in st.session_state:
    st.session_state.current_page = "dashboard"


# ==============================================================================
# LAYOUT & NAVIGATION
# ==============================================================================

try:
    selected_page = main_layout(st.session_state.current_page)
except Exception:
    logger.exception("Erreur lors de l'initialisation du layout principal")
    st.error("Impossible de charger le layout de l'application.")
    selected_page = st.session_state.current_page

# Map menu selection to page routing
page_mapping = {
    "Tableau de bord": "dashboard",
    "Compose Contrat": "contrat",
    "Compose Inference": "inference",
}

if selected_page and selected_page in page_mapping:
    st.session_state.current_page = page_mapping[selected_page]


# ==============================================================================
# PAGE RENDERING
# ==============================================================================

try:
    if st.session_state.current_page == "dashboard":
        dashboard.render()
    elif st.session_state.current_page == "contrat":
        contrat.render()
    elif st.session_state.current_page == "inference":
        inference.render()
    else:
        dashboard.render()
except Exception:
    logger.exception("Erreur lors du rendu de la page courante: %s", st.session_state.current_page)
    st.error("Une erreur est survenue lors du rendu de la page.")

# ==============================================================================
# FOOTER
# ==============================================================================

try:
    footer()
except Exception:
    logger.exception("Erreur lors du rendu du footer")
