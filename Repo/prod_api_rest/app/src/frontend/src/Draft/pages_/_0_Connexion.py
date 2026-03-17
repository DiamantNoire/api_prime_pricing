
# --- Application de supervision des jeux de données ODRE
# page: /page/_0_Connexion.py 
# -*- coding: utf-8 -*-

import streamlit as st
import pandas as pd

from srcs.configs import Configurations
from srcs.codes_pour_interface_ui.page_standard import Page_standard
from srcs.codes_pour_sources_externes_app.entrees_sorties_app import AdaptateurSourcesExternes
from srcs.codes_pour_senario_utilisation_app.services_d_orchestration import (
    ServiceSourcesExternes, ServiceDemarrage, ServiceJeuxDonneesOpendata
)
from srcs.codes_pour_senario_utilisation_app.outils_pour_les_services import (
    inscrire_utilisateur, connecter_utilisateur, se_deconnecter, exiger_auth
)

# --- Helpers optionnels ---
def _init_session_defaults():
    st.session_state.setdefault("auth_ok", False)
    st.session_state.setdefault("utilisateur", None)
    st.session_state.setdefault("roles", [])

def _bloc_authentication():
    """Affiche les onglets Login / Sign up si non connecté. Retourne True si utilisateur connecté après action."""
    if st.session_state.get("auth_ok", False):
        # Affichage minimal si déjà connecté
        st.success(
            f"Connecté en tant que **{st.session_state['utilisateur']}** "
            f"| Rôles: {st.session_state.get('roles', [])}"
        )
        return True

    tab_login, tab_signup = st.tabs(["Se connecter", "S'inscrire"])

    with tab_login:
        with st.form("login", clear_on_submit=True):
            identifiant = st.text_input("Identifiant")
            mdp = st.text_input("Mot de passe", type="password")
            ok = st.form_submit_button("Se connecter")

        if ok:
            success, msg, roles = connecter_utilisateur(identifiant, mdp)
            if success:
                st.toast(f"{msg} | Rôles: {roles}", icon="✅")
                st.switch_page("pages/_1_Surveillance_des_flux.py")  # à voir avec le metier
                return True
            else:
                st.error(msg)
                st.info("Si vous n'avez pas de compte, utilisez l'onglet 'S'inscrire'.")

    with tab_signup:
        intitules = list(Configurations.MAPPING_INTITULE_VERS_ROLES.keys())
        with st.form("signup", clear_on_submit=True):
            identifiant2 = st.text_input("Identifiant (unique)")
            mdp2 = st.text_input("Mot de passe (≥ 8)", type="password")
            intitule = st.selectbox("Rôle", intitules)
            ok2 = st.form_submit_button("S'inscrire")

        if ok2:
            success, msg = inscrire_utilisateur(identifiant2, mdp2, intitule)
            if success:
                st.toast(msg, icon="✅")
                st.toast("Vous pouvez vous connecter maintenant.", icon="🔔")
            else:
                st.error(msg)

    return False

def _logout_button():
    if st.session_state.get("auth_ok"):
        # Sidebar ou header selon ton design
        st.sidebar.markdown("---")
        if st.sidebar.button("Se déconnecter"):
            se_deconnecter()
            st.toast("Déconnecté.", icon="✅")
            st.switch_page("pages/_0_Connexion.py")

def _contenu_protege():
    """Tout le code métier de la page, exécuté uniquement après auth."""
    # --- Protection stricte (possible de vérifier les rôles ici) ---
    # exiger_auth()                   # sans rôles
    # exiger_auth(["ADMIN", "OPS"])   # avec rôles
    exiger_auth()

    # --- Services / Orchestrations ---
    service_des_jdds = ServiceJeuxDonneesOpendata()

    # Appel au service (réel)
    jdds, infos = service_des_jdds.lire_la_liste()

    # Stockage en session (safe)
    st.session_state["jdds"] = st.session_state.get("jdds", jdds)
    st.session_state["jdds_infos"] = st.session_state.get("jdds_infos", infos)

    # Bouton de rafraîchissement → relire le service, pas juste recycler les anciennes valeurs
    if st.button("🔁 Rafraîchir les JDDs"):
        # Si tu utilises st.cache_data dans le service, tu peux effacer ce cache interne,
        # mais évite un clear() global ici qui affecterait d'autres utilisateurs
        jdds, infos = service_des_jdds.lire_la_liste()
        st.session_state["jdds"] = jdds
        st.session_state["jdds_infos"] = infos
        st.toast("JDDs rafraîchis.", icon="🔁")

    # Les ports
    connectiques = AdaptateurSourcesExternes()
    # Les services
    services_d_acces_aux_sources_externes = ServiceSourcesExternes(connectiques)
    service_de_demarrage = ServiceDemarrage(
        chemins_fichiers_ds_app=Configurations.SERIES_CHEMINS_VERS_FICHIERS
    )

    # Appels aux services réservés aux connectés
    df1, df2, df3 = service_de_demarrage.lire_les_sources_depuis_app()

    # Exemple d’utilisation (optionnel)
    st.subheader("Aperçu des données")
    with st.expander("Métadata (1 ligne)"):
        st.dataframe(df1.head(1))
    with st.expander("Ressources (1 ligne)"):
        st.dataframe(df2.head(1))
    with st.expander("Blob opendata (1 ligne)"):
        st.dataframe(df3.head(1))

def main():
    try:
        # --- Mise en page standard ---
        titre_page = Configurations.TITRE_PAGE_0
        utilisateur = Configurations.UTILISATEUR_ALTERNANT
        chemin_css = Configurations.PATH_CSS

        page = Page_standard(titre_page, utilisateur, chemin_css)
        page._mise_en_page()
        page._css()
        page._barre_laterale(page_active=titre_page)

        page._disposition(nom_de_page=titre_page)

        # --- Init session ---
        _init_session_defaults()

        # --- Auth block (login/signup si non connecté) ---
        connected = _bloc_authentication()

        # --- Bouton de déconnexion (si connecté) ---
        _logout_button()

        # --- Si non connecté → on arrête ici. Aucun service n'est exécuté. ---
        if not connected and not st.session_state.get("auth_ok", False):
            st.info("Connectez-vous pour accéder aux services.")
            page._bas_de_page()
            return

        # --- À partir d'ici → contenu protégé uniquement ---
        _contenu_protege()

        page._bas_de_page()

    except Exception as e:
        st.error(f"Erreur lors du chargement de la page: {e}")

if __name__ == "__main__":
    main()
