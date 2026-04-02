"""
Dashboard Streamlit pour la visualisation et la recherche de contrats d'assurance.

Permet d'afficher :
    - Tous les contrats
    - Un contrat par numéro
    - Les contrats filtrés par type

Les données sont récupérées via l'API FastAPI (contrats endpoints).
"""

import streamlit as st
import requests
import pandas as pd

API_URL = "http://127.0.0.1:8000"

st.title("Dashboard Contrats")

# --- Choix du mode ---
mode = st.radio(
    "Choisir l'affichage",
    ["Tous les contrats", "Par numéro de contrat", "Par type de contrat"],
)

# --- Tous les contrats ---
if mode == "Tous les contrats":
    response = requests.get(f"{API_URL}/contrats")
    data = response.json()
    df = pd.DataFrame(data)
    st.dataframe(df)


# --- Par numéro ---
elif mode == "Par numéro de contrat":
    id_contrat = st.text_input("Entrer le numéro de contrat")

    if id_contrat:
        response = requests.get(f"{API_URL}/contrats/{id_contrat}")
        data = response.json()
        df = pd.DataFrame(data)
        st.dataframe(df)


# --- Par type ---
elif mode == "Par type de contrat":
    type_contrat = st.text_input("Entrer le type de contrat")

    if type_contrat:
        response = requests.get(f"{API_URL}/contrats/type/{type_contrat}")
        data = response.json()
        df = pd.DataFrame(data)
        st.dataframe(df)
