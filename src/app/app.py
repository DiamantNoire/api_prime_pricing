from __future__ import annotations

import streamlit as st

from . import config
from .layouts import main_layout, footer
from . import pages

try:
    import streamlit_antd_components as sac
except ImportError as exc:
    raise RuntimeError(
        "Le paquet 'streamlit-antd-components' est requis. "
        "Installe-le avec: uv add streamlit-antd-components"
    ) from exc


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

selected_page = main_layout(st.session_state.current_page)

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

if st.session_state.current_page == "dashboard":
    pages.dashboard.render()
elif st.session_state.current_page == "contrat":
    pages.contrat.render()
elif st.session_state.current_page == "inference":
    pages.inference.render()
else:
    pages.dashboard.render()

# ==============================================================================
# FOOTER
# ==============================================================================

footer()
