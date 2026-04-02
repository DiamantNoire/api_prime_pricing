from __future__ import annotations

import logging
import sys
from pathlib import Path

import streamlit as st

SRC_DIR = Path(__file__).resolve().parents[1]
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from app import config
from app.layouts import footer, main_layout
from app.pages import contrat, dashboard, inference

logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL, logging.INFO), format=config.LOG_FORMAT
)
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

# Navigation Home dans une page unique
st.subheader("Home")
home_labels = [
    config.PAGES["dashboard"]["name"],
    config.PAGES["contrat"]["name"],
    config.PAGES["inference"]["name"],
]
current_to_label = {
    "dashboard": config.PAGES["dashboard"]["name"],
    "contrat": config.PAGES["contrat"]["name"],
    "inference": config.PAGES["inference"]["name"],
}
label_to_current = {
    config.PAGES["dashboard"]["name"]: "dashboard",
    config.PAGES["contrat"]["name"]: "contrat",
    config.PAGES["inference"]["name"]: "inference",
}

selected_home = st.radio(
    "Navigation",
    options=home_labels,
    horizontal=True,
    index=home_labels.index(
        current_to_label.get(st.session_state.current_page, home_labels[0])
    ),
)
st.session_state.current_page = label_to_current[selected_home]


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
    logger.exception(
        "Erreur lors du rendu de la page courante: %s", st.session_state.current_page
    )
    st.error("Une erreur est survenue lors du rendu de la page.")

# ==============================================================================
# FOOTER
# ==============================================================================

try:
    footer()
except Exception:
    logger.exception("Erreur lors du rendu du footer")
