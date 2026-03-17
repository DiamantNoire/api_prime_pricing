# --- Application de supervision des jeux de données ODRE
# chemin: /page/_7_actu_data_dev.py
# ==== coding: utf-8 ====

# === Importation de librairies ===#
import bcrypt
import pandas as pd
import streamlit as st
from datetime import datetime
import streamlit_antd_components as sac
from st_aggrid import AgGrid, GridOptionsBuilder


# === Importation de modules ===#
from srcs.configs import Configurations
from srcs.codes_pour_interface_ui.page_standard import Page_standard
from srcs.codes_pour_senario_utilisation_app.services_d_orchestration import(
    ServiceJeuxDonneesOpendata
)
from srcs.codes_pour_senario_utilisation_app.outils_pour_les_services import(
    inscrire_utilisateur, connecter_utilisateur, se_deconnecter
)





def _ajouter_contenu():
    try:
        st.title("Connexion à l'application")

        # --- Services d'orchestration ---
        service_des_jdds = ServiceJeuxDonneesOpendata()

        # --- Charger jdds une seule fois puis mettre en session ---
        if "jdds" not in st.session_state or "jdds_infos" not in st.session_state:
            lecture_des_jdds_opendata, infos_de_lecture = service_des_jdds.lire_la_liste()
            jdds = lecture_des_jdds_opendata or []
            infos = infos_de_lecture or []
            st.session_state["jdds"] = jdds
            st.session_state["jdds_infos"] = infos
        else:
            jdds = st.session_state["jdds"]
            infos = st.session_state.get("jdds_infos", [])

        # --- Authentification ---
        if not st.session_state.get("auth_ok", False):
            tab_login, tab_signup = st.tabs(["Se connecter", "S'inscrire"])

            # --- Login ---
            with tab_login:
                with st.form("login", clear_on_submit=True):
                    identifiant = st.text_input("Identifiant")
                    mdp = st.text_input("Mot de passe", type="password")
                    ok = st.form_submit_button("Se connecter")
                if ok:
                    success, msg, roles = connecter_utilisateur(identifiant, mdp)
                    if success:
                        # Notification éphémère, puis rafraîchit l’état connecté
                        st.toast(f"{msg} | Rôles: {roles}", icon="✅")
                        st.rerun()
                    else:
                        st.error(msg)
                        st.info("Si vous n'avez pas de compte, utilisez l'onglet 'S'inscrire'.")

            # --- Signup ---
            with tab_signup:
                intitules = list(Configurations.MAPPING_INTITULE_VERS_ROLES.keys())
                # Optionnel: clear_on_submit=True pour vider les champs auto après submit
                with st.form("signup", clear_on_submit=True):
                    identifiant2 = st.text_input("Identifiant (unique)")
                    mdp2 = st.text_input("Mot de passe (≥ 8)", type="password")
                    intitule = st.selectbox("Rôle", intitules)
                    ok2 = st.form_submit_button("S'inscrire")
                if ok2:
                    success, msg = inscrire_utilisateur(identifiant2, mdp2, intitule)
                    if success:
                        # Notifications éphémères (pas de bandeau persistant)
                        st.toast(msg, icon="✅")
                        st.toast("Vous pouvez vous connecter maintenant.", icon="🔔")
                        # Pas de rerun ici: on laisse l’utilisateur aller sur l’onglet Login
                    else:
                        st.error(msg)

        else:
            st.success(
                f"Connecté en tant que **{st.session_state['utilisateur']}** "
                f"| Rôles: {st.session_state.get('roles', [])}"
            )
            if st.button("Se déconnecter"):
                se_deconnecter()
                st.toast("Déconnecté.", icon="✅")
                st.rerun()

        # --- Aperçu des JDDs (toujours après initialisation de jdds/infos) ---
        st.write(f"JDDs chargés: {len(jdds)}")
        if infos:
            with st.expander("Informations / avertissements de lecture"):
                st.write("\n".join(infos))

        # Affichage Pydantic v2
        try:
            st.json([j.model_dump() for j in jdds][:3])
        except Exception:
            st.json([getattr(j, "__dict__", j) for j in jdds][:3])

    except Exception as e:
        st.error(f"Échec : {e}")




# Construction de la page
try:
    titre_page = Configurations.TITRE_PAGE_4
    utilisateur = Configurations.UTILISATEUR_ALTERNANT
    chemin_css = Configurations.PATH_CSS
    page = Page_standard(titre_page, utilisateur, chemin_css)
    page._mise_en_page()
    page._disposition_page_actualisations_des_donnees()
    page._css()
    page._barre_laterale()
    _ajouter_contenu()
    page._bas_de_page_v2()
except Exception as e:
    st.error(f"Erreur lors du chargement de la page: {e}")


