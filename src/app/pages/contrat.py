"""Page Compose Contrat."""

from __future__ import annotations

import streamlit as st

try:
    import streamlit_antd_components as sac
except ImportError as exc:
    raise RuntimeError(
        "Le paquet 'streamlit-antd-components' est requis."
    ) from exc

from ..components import header, section_divider, info_box
from ..config import ENDPOINTS


def render() -> None:
    """Affiche la page compose contrat."""
    header("Compose Contrat", "Création et édition de contrats d'assurance")
    
    section_divider("Formulaire de contrat", icon="file-earmark-plus")
    
    with st.form("contrat_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.text_input("Type de contrat", placeholder="ex: Mini, Medium, Maxi")
            st.number_input("Durée contrat (mois)", value=12, min_value=1, max_value=24)
            st.text_input("Fréquence de paiement", placeholder="ex: Monthly, Yearly")
        
        with col2:
            st.text_input("Code postal", placeholder="ex: 75001")
            st.number_input("Ancienneté info", value=1, min_value=0)
            st.selectbox("Paiement", options=["Yes", "No"])
        
        st.divider()
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.form_submit_button("Créer contrat", use_container_width=True):
                st.success("Contrat créé avec succès")
        with col2:
            st.form_submit_button("Brouillon", use_container_width=True)
        with col3:
            st.form_submit_button("Réinitialiser", use_container_width=True)
    
    section_divider("Contrats récents", icon="list-check")
    
    st.info("📋 Aucun contrat créé pour le moment.")
    
    st.caption(f"API Endpoint: {ENDPOINTS['predict_frequence']}")
