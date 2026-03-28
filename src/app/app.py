from __future__ import annotations

import streamlit as st

try:
    import streamlit_antd_components as sac
except ImportError as exc:
    raise RuntimeError(
        "Le paquet 'streamlit-antd-components' est requis. "
        "Installe-le avec: uv add streamlit-antd-components"
    ) from exc


st.set_page_config(
    page_title="Prime Pricing - User Application",
    page_icon="📊",
    layout="wide",
)

st.title("User Application")
st.caption("Base UI Streamlit + Ant Design pour demarrer les compose.")

menu = sac.menu(
    [
        sac.MenuItem("Tableau de bord", icon="house"),
        sac.MenuItem("Compose Contrat", icon="file-earmark-text"),
        sac.MenuItem("Compose Inference", icon="graph-up"),
    ],
    open_all=True,
)

sac.divider(label="Espace de travail", icon="layout-three-columns")

if menu == "Tableau de bord":
    sac.result(
        label="Squelette pret",
        description="Le module src/app est initialise sur la branche dev_user_application.",
        status="success",
    )
elif menu == "Compose Contrat":
    st.subheader("Compose Contrat")
    st.info("Section reservee pour les composants de creation/edition de contrat.")
else:
    st.subheader("Compose Inference")
    st.info("Section reservee pour les composants de prediction et visualisation.")
