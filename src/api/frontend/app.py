import logging
import streamlit as st

LOGGER = logging.getLogger(__name__)
logging.basicConfig(level="INFO")

st.title("Dashboard Assurance")
LOGGER.info("Streamlit app loaded")

st.write("Bienvenue dans l'application.")
st.write("Utilisez le menu à gauche pour naviguer.")
