import streamlit as st
import requests

API_URL = "http://127.0.0.1:8000"

st.title("Prédiction de la prime")

age = st.number_input("Age conducteur", min_value=18, max_value=100)
bonus = st.number_input("Bonus", min_value=0.0, max_value=1.0)
sinistres = st.number_input("Nombre de sinistres", min_value=0)

if st.button("Prédire"):
    response = requests.post(
        f"{API_URL}/predict",
        json={
            "age": age,
            "bonus": bonus,
            "sinistres": sinistres
        }
    )

    result = response.json()
    st.success(f"Prime estimée : {result['prediction']} €")