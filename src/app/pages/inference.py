"""Page Compose Inference."""

from __future__ import annotations

import streamlit as st

try:
    import streamlit_antd_components as sac
except ImportError as exc:
    raise RuntimeError(
        "Le paquet 'streamlit-antd-components' est requis."
    ) from exc

from ..components import header, section_divider
from ..config import ENDPOINTS, FEATURES


def render() -> None:
    """Affiche la page compose inference."""
    header("Compose Inference", "Prédiction de fréquence et sévérité")
    
    section_divider("Options de prédiction", icon="crystal-ball")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Type de prédiction")
        pred_type = st.radio(
            "Sélectionne le type",
            options=["Fréquence", "Sévérité", "Combinée"],
            label_visibility="collapsed",
        )
    
    with col2:
        st.subheader("Mode")
        mode = st.radio(
            "Sélectionne le mode",
            options=["Unitaire", "Batch"] if FEATURES["enable_batch_prediction"] else ["Unitaire"],
            label_visibility="collapsed",
        )
    
    st.divider()
    
    section_divider("Saisie des données", icon="input-cursor-text")
    
    with st.form("inference_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.number_input("Age conducteur 1", value=35, min_value=18, max_value=100)
            st.number_input("Ancienneté permis", value=10, min_value=0, max_value=70)
            st.selectbox("Carburant", options=["Gasoline", "Diesel", "Hybrid", "Electric"])
        
        with col2:
            st.text_input("Type véhicule", placeholder="ex: SUV, Sedan")
            st.number_input("Cylindrée (cc)", value=1500, min_value=500)
            st.number_input("Prix véhicule (€)", value=25000, min_value=0)
        
        st.divider()
        
        col1, col2 = st.columns(2)
        with col1:
            if st.form_submit_button("Lancer prédiction", use_container_width=True):
                st.info("✨ Prédiction en cours...")
        with col2:
            st.form_submit_button("Réinitialiser", use_container_width=True)
    
    section_divider("Résultats", icon="check-circle")
    
    st.warning("⏳ Aucune prédiction effectuée.")
    
    col1, col2 = st.columns(2)
    with col1:
        st.caption(f"API Endpoint F: {ENDPOINTS['predict_frequence']}")
    with col2:
        st.caption(f"API Endpoint S: {ENDPOINTS['predict_severite']}")
