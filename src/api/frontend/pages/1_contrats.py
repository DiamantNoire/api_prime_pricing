import logging
import os

import streamlit as st
import requests
import pandas as pd

LOGGER = logging.getLogger(__name__)
API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")

st.title("Dashboard Contrats")

# --- Choix du mode ---
mode = st.radio(
    "Choisir l'affichage",
    ["Tous les contrats", "Par numéro de contrat", "Par type de contrat"]
)

# --- Tous les contrats ---
if mode == "Tous les contrats":
    try:
        LOGGER.info("Request GET %s/contrats", API_URL)
        response = requests.get(f"{API_URL}/contrats", timeout=30)
        response.raise_for_status()
        data = response.json()
        df = pd.DataFrame(data)
        st.dataframe(df)
    except Exception as exc:
        LOGGER.exception("Erreur appel API /contrats")
        st.error(f"Erreur API: {exc}")


# --- Par numéro ---
elif mode == "Par numéro de contrat":
    id_contrat = st.text_input("Entrer le numéro de contrat")

    if id_contrat:
        try:
            LOGGER.info("Request GET %s/contrats/%s", API_URL, id_contrat)
            response = requests.get(f"{API_URL}/contrats/{id_contrat}", timeout=30)
            response.raise_for_status()
            data = response.json()
            df = pd.DataFrame(data)
            st.dataframe(df)
        except Exception as exc:
            LOGGER.exception("Erreur appel API /contrats/{id}")
            st.error(f"Erreur API: {exc}")


# --- Par type ---
elif mode == "Par type de contrat":
    type_contrat = st.text_input("Entrer le type de contrat")

    if type_contrat:
        try:
            LOGGER.info("Request GET %s/contrats/type/%s", API_URL, type_contrat)
            response = requests.get(f"{API_URL}/contrats/type/{type_contrat}", timeout=30)
            response.raise_for_status()
            data = response.json()
            df = pd.DataFrame(data)
            st.dataframe(df)
        except Exception as exc:
            LOGGER.exception("Erreur appel API /contrats/type/{type}")
            st.error(f"Erreur API: {exc}")