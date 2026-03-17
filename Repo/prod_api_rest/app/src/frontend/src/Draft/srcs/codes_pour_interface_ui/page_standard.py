# --- Application de supervision des jeux de données ODRE 
# chemin: srcs/codes_pour_interface_ui/page_standard.py
# ==== coding: utf-8 ====

# === Importation de librairies ===
from __future__ import annotations

import streamlit as st
import streamlit_antd_components as sac


from pathlib import Path
from typing import Dict, Tuple
from datetime import datetime, timedelta
from datetime import datetime as _dt

# Importation de module
from srcs.configs import Configurations
from srcs.codes_pour_senario_utilisation_app.services_d_orchestration import(
    orchestration_service_alimenter_cache_app_en_data
)
from srcs.codes_pour_senario_utilisation_app.outils_pour_les_services import(
    _age_cache_en_j_h_m_s, se_deconnecter
)

from srcs.codes_pour_senario_utilisation_app.outils_pour_les_services import(
    se_deconnecter
) 

from pathlib import Path
try:
    from streamlit.runtime.scriptrunner import add_script_run_ctx  # no-op si version différente
except Exception:
    pass

from srcs.codes_pour_senario_utilisation_app.outils_pour_les_services import (
    se_deconnecter, connecter_utilisateur, inscrire_utilisateur
)

from srcs.codes_pour_senario_utilisation_app.services_d_orchestration import (
    ServiceSourcesExternes,
    orchestration_service_alimenter_cache_app_en_data,
)
from srcs.codes_pour_sources_externes_app.entrees_sorties_app import(
    AdaptateurSourcesExternes
)


# --- Classe pour une page standard | Style Css, barre latérale, contenu (laissé vide pour chaque page), bas de page ===
class Page_standard:
    def __init__(self, titre_page:str,
                 utilisateur: str,
                 chemin_style:Path,
                 #fraicheur_data:datetime
    ): 
        self.titre_page = titre_page
        self.utilisateur = utilisateur
        self.chemin_style = chemin_style
        #self.fraicheur_data = fraicheur_data
    
        self.ROUTES: Dict[str, str] = {
                    "Connexion": "connexion",
                    "Surveillance des flux": "surveillance",
                    "Alertes & notifications": "alertes",
                    "Qualité de la donnée": "qualite",
                    "Actualisation des données": "actualisation",
                    "Gestion des référentiels": "referentiels",
                    "Dev 1": "dev1",
                    "Dev 2": "dev2",
                    "Dev 3": "dev3",
                    "Dev 4": "dev4",
        }


    # Chargement du style css:
    def _css(self) -> None:
        """Charge le CSS de l'application depuis un fichier."""
        try:
            with open(self.chemin_style, encoding="utf-8") as f:
                css = f.read()
            st.markdown(f"<style>{css}</style>", unsafe_allow_html=True, width="stretch")
            st.session_state["_css_loaded"] = True
        except Exception as e:
            st.warning(f"CSS non chargé: {e}")

    def _fraicheur_cache_et_alimentation(self) -> Tuple[str, str]:
        """
        Footer HTML :
        - Centre : planning
        - Droite : utilisateur + rôles + fraîcheur
        """
        # 1) Fraîcheur
        try:
            svc = orchestration_service_alimenter_cache_app_en_data()
            (age_j, age_h, age_m, age_s), last_dt = svc.fraicheur_du_cache_de_donnees()

            def _fmt_j_h_m_s(j: int, h: int, m: int, s: int) -> str:
                return f"{j} j {h} h {m} min {s} s"

            donnees_fraiches_html = (
                f"<br/>Données fraîches depuis : <strong>{_fmt_j_h_m_s(age_j, age_h, age_m, age_s)}</strong>"
                if last_dt is not None else ""
            )
        except Exception:
            donnees_fraiches_html = ""

        # 2) Planning
        try:
            auto_enabled = bool(getattr(Configurations, "AUTO_REFRESH_CRON_ENABLED", True))
            cron_hour = int(getattr(Configurations, "AUTO_REFRESH_CRON_HOUR", 9))
            cron_minute = int(getattr(Configurations, "AUTO_REFRESH_CRON_MINUTE", 30))
            cron_spec = str(getattr(Configurations, "AUTO_REFRESH_CRON_WEEKDAYS", "mon-fri")).lower()

            def _fmt_cron_spec(spec: str) -> str:
                mapping = {"mon": "Lun", "tue": "Mar", "wed": "Mer", "thu": "Jeu", "fri": "Ven", "sat": "Sam", "sun": "Dim"}
                spec = (spec or "").strip().lower()
                if "-" in spec and "," not in spec:
                    a, b = spec.split("-", 1)
                    return f"{mapping.get(a, a.capitalize())}-{mapping.get(b, b.capitalize())}"
                parts = [p.strip() for p in spec.split(",") if p.strip()]
                return ", ".join(mapping.get(p, p.capitalize()) for p in parts)

            planning_txt = (
                f"Alimentation automatique: {'activée' if auto_enabled else 'désactivée'} • "
                f"créneau prévu: {cron_hour:02d}:{cron_minute:02d} ({_fmt_cron_spec(cron_spec)})."
            )
        except Exception:
            planning_txt = "Planification: indisponible pour le moment."

        return planning_txt, donnees_fraiches_html
    
    def _login_dialog_body(self):
        """Corps du formulaire (login / signup) utilisé dans le dialog."""
        st.markdown("### Connexion")

        tab_login, tab_signup = st.tabs(["Se connecter", "S'inscrire"])

        # --- LOGIN ---
        with tab_login:
            with st.form("login_form", clear_on_submit=True):
                identifiant = st.text_input("Identifiant")
                mdp = st.text_input("Mot de passe", type="password")
                ok = st.form_submit_button("Se connecter", use_container_width=True)

            if ok:
                success, msg, roles = connecter_utilisateur(identifiant, mdp)
                if success:
                    st.toast(f"{msg} | Rôles: {roles}", icon="✅")
                    # Fermer le dialog et rediriger vers ta page favorite
                    st.session_state["__show_login_dialog__"] = False
                    #st.switch_page("pages/_1_Surveillance_des_flux.py")
                    st.rerun()
                else:
                    st.error(msg)
                    st.info("Si vous n'avez pas de compte, utilisez l'onglet 'S'inscrire'.")

        # --- SIGNUP ---
        with tab_signup:
            intitules = list(Configurations.MAPPING_INTITULE_VERS_ROLES.keys())
            with st.form("signup_form", clear_on_submit=True):
                identifiant2 = st.text_input("Identifiant (unique)")
                mdp2 = st.text_input("Mot de passe (≥ 8)", type="password")
                intitule = st.selectbox("Rôle", intitules)
                ok2 = st.form_submit_button("S'inscrire", use_container_width=True)

            if ok2:
                success, msg = inscrire_utilisateur(identifiant2, mdp2, intitule)
                if success:
                    st.toast(msg, icon="✅")
                    st.toast("Vous pouvez vous connecter maintenant.", icon="🔔")
                else:
                    st.error(msg)


    def _open_login_dialog(self):
        """Ouvre un dialog de connexion si supporté, sinon active le fallback dans la sidebar."""
        # On demande l'ouverture (flag commun auth)
        st.session_state["__show_login_dialog__"] = True

        try:
            # Streamlit >= 1.30 : modal centré
            @st.dialog("Authentification")
            def _dlg():
                # On rend le corps du dialogue
                self._login_dialog_body()
            _dlg()
        except AttributeError:
            # Si st.dialog n'existe pas (versions plus anciennes), on gardera le fallback dans la sidebar
            pass


    def _auth_cta_bottom_v0(self, login_page_path: str = "pages/_0_Connexion.py", 
                         key_suffix: str | None = None
        ):
        """
        Affiche un unique bouton en bas de la sidebar :
        - 'Se connecter' -> ouvre un dialog
        - 'Se déconnecter' -> purge + switch vers la page de connexion (ou page neutre)
        """
        suffix = key_suffix or Path(__file__).stem
        auth_btn_key = f"sb_auth_button__{suffix}"

        is_auth = bool(st.session_state.get("auth_ok", False))
        user = st.session_state.get("utilisateur") or "Invité"
        roles = st.session_state.get("roles") or []

        st.sidebar.markdown("---")
        if is_auth:
            roles_txt = ", ".join(roles) if roles else "—"
            st.sidebar.caption(f"Connecté : **{user}** • {roles_txt}")

            if st.sidebar.button("Se déconnecter", 
                                 use_container_width=True, 
                                 key=f"{auth_btn_key}_logout",
            ):
                se_deconnecter()
                st.toast("Déconnecté.", icon="✅")
                try:
                    st.query_params.clear()
                except Exception:
                    pass
                #st.switch_page(login_page_path)  # page de connexion existante
                st.rerun()
        else:
            if st.sidebar.button("Se connecter", use_container_width=True, type="primary", key=f"{auth_btn_key}_login"):
                # Ouvre le dialog (ou set un flag si version Streamlit < 1.30)
                self._open_login_dialog()


        if st.session_state.get("auth_ok", False) and st.session_state.get("__show_login_dialog__", False):
            st.session_state["__show_login_dialog__"] = False

        # Fallback: si pas de st.dialog dispo, on rend le formulaire inline
        if st.session_state.get("__show_login_dialog__", False):
            try:
                # Si st.dialog fonctionne, _open_login_dialog l'a déjà affiché.
                pass
            except Exception:
                # Rendu fallback dans la sidebar (ou dans la zone centrale)
                with st.sidebar.expander("Authentification", expanded=True):
                    self._login_dialog_body()

    def _auth_cta_bottom(self, login_page_path: str = "pages/_0_Connexion.py", 
                        key_suffix: str | None = None):
        """
        Affiche un unique bouton en bas de la sidebar :
        - 'Se connecter' -> ouvre un dialog
        - 'Se déconnecter' -> purge + switch vers la page de connexion (ou page neutre)
        """
        suffix = key_suffix or Path(__file__).stem
        auth_btn_key = f"sb_auth_button__{suffix}"

        is_auth = bool(st.session_state.get("auth_ok", False))
        user = st.session_state.get("utilisateur") or "Invité"
        roles = st.session_state.get("roles") or []

        # --- Couleurs paramétrables (runtime) ---
        # Tu peux les stocker dans session_state ailleurs si tu préfères
        st.session_state.setdefault("auth_btn_color_login",  "#214B4D")  # vert canard
        st.session_state.setdefault("auth_btn_color_logout", "#dc2626")  # rouge
        st.session_state.setdefault("auth_btn_text_color",   "#ffffff")  # texte

        st.sidebar.markdown("---")
        if is_auth:
            roles_txt = ", ".join(roles) if roles else "—"
            st.sidebar.caption(f"Connecté : **{user}** • {roles_txt}")

            # --- Wrapper ciblable par CSS : data-auth-key ---
            st.sidebar.markdown(
                f'<div data-auth-key="{auth_btn_key}_logout">', unsafe_allow_html=True
            )
            clicked = st.sidebar.button(
                "Se déconnecter",
                key=f"{auth_btn_key}_logout",
                type="primary",                 # on stylera la variante primary
                use_container_width=True,
            )
            st.sidebar.markdown('</div>', unsafe_allow_html=True)

            if clicked:
                se_deconnecter()
                st.toast("Déconnecté.", icon="✅")
                try:
                    st.query_params.clear()
                except Exception:
                    pass
                st.rerun()
        else:
            st.sidebar.markdown(
                f'<div data-auth-key="{auth_btn_key}_login">', unsafe_allow_html=True
            )
            if st.sidebar.button(
                "Se connecter",
                key=f"{auth_btn_key}_login",
                type="primary",                 # on stylera la variante primary
                use_container_width=True,
            ):
                self._open_login_dialog()
            st.sidebar.markdown('</div>', unsafe_allow_html=True)

        if st.session_state.get("auth_ok", False) and st.session_state.get("__show_login_dialog__", False):
            st.session_state["__show_login_dialog__"] = False

        # Fallback: si pas de st.dialog dispo, on rend le formulaire inline
        if st.session_state.get("__show_login_dialog__", False):
            try:
                pass
            except Exception:
                with st.sidebar.expander("Authentification", expanded=True):
                    self._login_dialog_body()


    def _alimentation_dialog_body(self):
        """Dialog 'Alimentation' : 2 boutons avec clés uniques et fermeture auto."""
        st.markdown("### Choisissez un mode d'alimentation.")

        route = st.session_state.get("route", "global")
        key_suffix = f"__{route}"
        k_auto   = f"btn_auto_feed{key_suffix}"
        k_manual = f"btn_manual_feed{key_suffix}"

        col1, col2 = st.columns(2)

        with col1:
            st.markdown('<div data-alim-action="auto">', unsafe_allow_html=True)
            if st.button("🛠️ Automatiquement", type="primary", use_container_width=True, key=k_auto):
                st.session_state["run_alimentation"] = "auto"
                st.session_state["__show_alim_dialog__"] = False
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        with col2:
            st.markdown('<div data-alim-action="manual">', unsafe_allow_html=True)
            if st.button("🛠️ Manuelle", type="secondary", use_container_width=True, key=k_manual):
                st.session_state["run_alimentation"] = "manuelle"
                st.session_state["__show_alim_dialog__"] = False
                st.rerun
            st.markdown('</div>', unsafe_allow_html=True)

    def _open_alimentation_dialog(self):
        """Ouvre le dialogue d'alimentation, fallback seulement si st.dialog indisponible."""
        st.session_state["__show_alim_dialog__"] = True

        try:
            @st.dialog("Alimentation de l'application")
            def _dlg():
                self._alimentation_dialog_body()
            _dlg()
        except Exception:
            # fallback sera affiché dans _alimentation_cta_bottom()
            pass

    def _alimentation_cta_bottom(self, key_suffix=None):

        roles = st.session_state.get("roles") or []
        autorises_lower = {r.lower() for r in Configurations.ROLES_AUTORISES}
        is_authorized = any(r.lower() in autorises_lower for r in roles)

        suffix = key_suffix or "global"
        alim_btn_key = f"sb_alim_button__{suffix}"

        st.sidebar.markdown("---")

        if is_authorized:
            st.sidebar.markdown(f'<div data-alim-key="{alim_btn_key}">', unsafe_allow_html=True)
            if st.sidebar.button("⚙️ Alimenter l'outil", key=alim_btn_key, type="secondary", use_container_width=True):
                self._open_alimentation_dialog()
            st.sidebar.markdown("</div>", unsafe_allow_html=True)

        # Fallback EXACT comme l'auth
        if st.session_state.get("__show_alim_dialog__", False):
            try:
                pass
            except Exception:
                with st.sidebar.expander("Alimentation de l'application", expanded=True):
                    self._alimentation_dialog_body()



    def _barre_laterale_v0(self, page_active: str | None = None) -> None:
        self._auth_cta_bottom(login_page_path="pages/_0_Connexion.py", key_suffix=page_active or "global")
        action_alimentation = st.session_state.get("run_alimentation")
        if action_alimentation == "auto":
            try:
                adaptateur = AdaptateurSourcesExternes()
                adaptateur.brancher_le_port()
                service_alim = orchestration_service_alimenter_cache_app_en_data()
                ok = service_alim.alimenter_automatiquement()
                st.toast("Alimentation automatique terminée ✅" if ok else "Échec alimentation automatique ❌",
                        icon="✅" if ok else "⚠️")
            except Exception as e:
                st.toast(f"Erreur auto : {e}", icon="⚠️")
            st.session_state["run_alimentation"] = None

        elif action_alimentation == "manuelle":
            try:
                adaptateur = AdaptateurSourcesExternes()
                adaptateur.brancher_le_port()
                service_alim = orchestration_service_alimenter_cache_app_en_data()
                ok = service_alim.alimenter_manuellement()
                st.toast("Alimentation automatique terminée ✅" if ok else "Échec alimentation manuelle ❌",
                        icon="✅" if ok else "⚠️")
            except Exception as e:
                st.toast(f"Erreur manuelle : {e}", icon="⚠️")
            st.session_state["run_alimentation"] = None

        #self._alimentation_cta_bottom(key_suffix=page_active or "global")

        st.markdown("""
        <style>
        /* Bouton automatique (vert) */
        [data-testid="stDialog"] [data-alim-action="auto"] button {
            background-color: #265B88 !important;
            border-color: #16a34a !important;
            color: white !important;
        }
        /* Bouton manuel (orange) */
        [data-testid="stDialog"] [data-alim-action="manual"] button {
            background-color: #543361 !important;
            border-color: #ea580c !important;
            color: white !important;
        }
        /* Effet hover */
        [data-testid="stDialog"] button:hover {
            filter: brightness(0.92);
        }
        </style>
        """, unsafe_allow_html=True)

        # (ton script JS existant)
        st.markdown(
            """
            <script>
                (function(){
                    function checkSidebar(){
                        const sidebar = document.querySelector('section[data-testid="stSidebar"]');
                        if (sidebar && sidebar.offsetWidth > 0){
                            document.body.classList.add('sidebar-open');
                        } else {
                            document.body.classList.remove('sidebar-open');
                        }
                    }
                    if (!window._sbIntervalSet) {
                        window._sbIntervalSet = true;
                        setInterval(checkSidebar, 800);
                    }
                    checkSidebar();
                })();
            </script>
            """,
            unsafe_allow_html=True
        )


    def _barre_laterale(self, page_active: str | None = None) -> None:
        # Auth CTA toujours en premier
        self._auth_cta_bottom(login_page_path="pages/_0_Connexion.py", key_suffix=page_active or "global")

        # --------------------------------
        # CTA alimentation (IMPORTANT : remettre !)
        # --------------------------------
        self._alimentation_cta_bottom(key_suffix=page_active or "global")


        # -------------------------------
        # Exécution post-dialog (après fermeture)
        # -------------------------------
        action_alimentation = st.session_state.get("run_alimentation")

        if action_alimentation == "auto":
            try:
                adaptateur = AdaptateurSourcesExternes()
                adaptateur.brancher_le_port()
                service_alim = orchestration_service_alimenter_cache_app_en_data()
                ok = service_alim.alimenter_automatiquement()

                st.toast("Alimentation automatique terminée ✅" if ok else "Échec alimentation automatique ❌",
                        icon="✅" if ok else "⚠️")

            except Exception as e:
                st.toast(f"Erreur auto : {e}", icon="⚠️")

            st.session_state["run_alimentation"] = None

        elif action_alimentation == "manuelle":
            try:
                adaptateur = AdaptateurSourcesExternes()
                adaptateur.brancher_le_port()
                service_alim = orchestration_service_alimenter_cache_app_en_data()
                ok = service_alim.alimenter_manuellement(declencheur="OUI")

                st.toast("Alimentation manuelle terminée ✅" if ok else "Échec alimentation manuelle ❌",
                        icon="✅" if ok else "⚠️")

            except Exception as e:
                st.toast(f"Erreur manuelle : {e}", icon="⚠️")

            st.session_state["run_alimentation"] = None


        # --------------------------------
        # CSS Dialog (avec vraies balises <style>)
        # --------------------------------
        st.markdown("""
        <style>
        /* Bouton automatique (vert) */
        [data-testid="stDialog"] [data-alim-action="auto"] button {
            background-color: #265B88 !important;
            border-color: #16a34a !important;
            color: white !important;
        }

        /* Bouton manuel (orange) */
        [data-testid="stDialog"] [data-alim-action="manual"] button {
            background-color: #543361 !important;
            border-color: #ea580c !important;
            color: white !important;
        }

        /* Effet hover */
        [data-testid="stDialog"] button:hover {
            filter: brightness(0.92);
        }
        </style>
        """, unsafe_allow_html=True)


        # --------------------------------
        # Script JS existant
        # --------------------------------
        st.markdown("""
        <script>
            (function(){
                function checkSidebar(){
                    const sidebar = document.querySelector('section[data-testid="stSidebar"]');
                    if (sidebar && sidebar.offsetWidth > 0){
                        document.body.classList.add('sidebar-open');
                    } else {
                        document.body.classList.remove('sidebar-open');
                    }
                }
                if (!window._sbIntervalSet) {
                    window._sbIntervalSet = true;
                    setInterval(checkSidebar, 800);
                }
                checkSidebar();
            })();
        </script>
        """, unsafe_allow_html=True)



    def _barre_laterale_v0(self, page_active: str | None = None) -> None:

        self._auth_cta_bottom(login_page_path="pages/_0_Connexion.py", key_suffix=page_active or "global")

        st.markdown(
            """
            <script>
                (function(){
                    function checkSidebar(){
                        const sidebar = document.querySelector('section[data-testid="stSidebar"]');
                        if (sidebar && sidebar.offsetWidth > 0){
                            document.body.classList.add('sidebar-open');
                        } else {
                            document.body.classList.remove('sidebar-open');
                        }
                    }
                    if (!window._sbIntervalSet) {
                        window._sbIntervalSet = true;
                        setInterval(checkSidebar, 800);
                    }
                    checkSidebar();
                })();
            </script>
            """,
            unsafe_allow_html=True
        )


    def _barre_laterale_v1(self, page_active: str | None = None) -> None:
        self._auth_cta_bottom(login_page_path="pages/_0_Connexion.py", key_suffix=page_active or "global")

        # Récupère les couleurs (runtime)
        c_login  = st.session_state.get("auth_btn_color_login",  "#16a34a")
        c_logout = st.session_state.get("auth_btn_color_logout", "#dc2626")
        c_text   = st.session_state.get("auth_btn_text_color",   "#ffffff")

        st.markdown(
            f"""
            <style>
            /* === Styles ciblés sidebar + clés spécifiques === */
            section[data-testid="stSidebar"] [data-auth-key$="_login"]  button[data-testid="baseButton-primary"] {{
                background-color: {c_login} !important;
                border-color: {c_login} !important;
                color: {c_text} !important;
            }}
            section[data-testid="stSidebar"] [data-auth-key$="_login"]  button[data-testid="baseButton-primary"]:hover {{
                filter: brightness(0.93);
            }}

            section[data-testid="stSidebar"] [data-auth-key$="_logout"] button[data-testid="baseButton-primary"] {{
                background-color: {c_logout} !important;
                border-color: {c_logout} !important;
                color: {c_text} !important;
            }}
            section[data-testid="stSidebar"] [data-auth-key$="_logout"] button[data-testid="baseButton-primary"]:hover {{
                filter: brightness(0.93);
            }}
            </style>
            """,
            unsafe_allow_html=True
        )

        st.markdown(
            """
            <script>
                (function(){
                    function checkSidebar(){
                        const sidebar = document.querySelector('section[data-testid="stSidebar"]');
                        if (sidebar && sidebar.offsetWidth > 0){
                            document.body.classList.add('sidebar-open');
                        } else {
                            document.body.classList.remove('sidebar-open');
                        }
                    }
                    if (!window._sbIntervalSet) {
                        window._sbIntervalSet = true;
                        setInterval(checkSidebar, 800);
                    }
                    checkSidebar();
                })();
            </script>
            """,
            unsafe_allow_html=True
        )






    # Mise en page
    def _mise_en_page(self) -> None:
        st.set_page_config(self.titre_page,
                           layout="wide",
                           initial_sidebar_state="expanded"
        )

    def _bouton_connexion(self):
        if not st.session_state.get("auth_ok"):
            if st.sidebar.button("Se Connecter"):
                st.switch_page("pages/_0_Connexion.py")

    def _bouton_deconnexion(self):
        if st.session_state.get("auth_ok"):
            if st.sidebar.button("Se déconnecter"):
                se_deconnecter()
                st.toast("Déconnecté.", icon="✅")
                st.switch_page("pages/_0_Connexion.py")

    def _bouton_connexion_deconnexion(self, statut: bool):
        if statut:
            self._bouton_deconnexion()
        else:
            self._bouton_connexion()

    def render_sidebar(self,
                    page_active_label: str | None = None,
                    show_login_logo: bool = True,
                    key_suffix: str | None = None):
        """
        - key_suffix permet de personnaliser la clé si besoin (ex. pour des tests, des sous-apps, etc.)
        """
        labels = list(self.ROUTES.keys())
        menu_items = [sac.MenuItem('Navigation entre les pages', disabled=True)]
        for label in labels:
            menu_items.append(sac.MenuItem(label))

        default_index = (labels.index(page_active_label) ) if (page_active_label in labels) else 1

        # 🔑 Clé unique = base + route (et éventuellement un suffixe passé par l'appelant)
        route = st.session_state.get("route", "root")
        menu_key = f"sb_nav_menu__{route}"
        if key_suffix:
            menu_key = f"{menu_key}__{key_suffix}"

        choice_label = sac.menu(
            items=menu_items,
            key=menu_key,
            index=default_index,
            open_all=True,
            return_index=False,
            size='middle',
        )

        if choice_label and choice_label in self.ROUTES:
            new_route = self.ROUTES[choice_label]
            if st.session_state.get("route") != new_route:
                st.session_state["route"] = new_route
                st.rerun()

        if show_login_logo:
            self._render_sidebar_bottom()

    def _render_sidebar_bottom(self):
        route = st.session_state.get("route", "root")
        auth_btn_key = f"sb_auth_button__{route}"

        is_auth = bool(st.session_state.get("auth_ok", False))
        if not is_auth:
            if st.sidebar.button("Se connecter", use_container_width=True, type="primary", key=auth_btn_key):
                st.session_state["route"] = "connexion"
                try: st.query_params.clear()
                except Exception: pass
                st.rerun()
        else:
            if st.sidebar.button("Se déconnecter", use_container_width=True, key=auth_btn_key):
                se_deconnecter()
                st.toast("Déconnecté.", icon="✅")
                try: st.query_params.clear()
                except Exception: pass
                st.session_state["route"] = "connexion"
                st.rerun()

    def _auth_cta_bottom_v0(self, login_page_path: str = "pages/_0_Connexion.py", 
                         key_suffix: str | None = None
        ):
        """
        Affiche un unique bouton en bas de la sidebar :
        - 'Se connecter' si l'utilisateur n'est pas connecté -> switch vers la page de connexion
        - 'Se déconnecter' si l'utilisateur est connecté -> se_deconnecter + retour connexion
        """
        # Clé unique pour éviter collisions si jamais sidebar rendue 2x
        suffix = key_suffix or Path(__file__).stem  # ou un label de la page courante
        auth_btn_key = f"sb_auth_button__{suffix}"

        is_auth = bool(st.session_state.get("auth_ok", False))
        user = st.session_state.get("utilisateur") or "Invité"
        roles = st.session_state.get("roles") or []

        st.sidebar.markdown("---")
        if is_auth:
            # (facultatif) afficher le résumé
            roles_txt = ", ".join(roles) if roles else "—"
            st.sidebar.caption(f"Connecté : **{user}** •  {roles_txt}")

            if st.sidebar.button("Se déconnecter", use_container_width=True, key=auth_btn_key):
                se_deconnecter()
                st.toast("Déconnecté.", icon="✅")
                try:
                    st.query_params.clear()
                except Exception:
                    pass
                st.switch_page(login_page_path)
        else:
            if st.sidebar.button("Se connecter", use_container_width=True, type="primary", key=auth_btn_key):
                try:
                    st.query_params.clear()
                except Exception:
                    pass
                st.switch_page(login_page_path)



    # Disposition pour la page 1 : (A venir) | Connexion 
    # Disposition pour la page 2 : (A venir) | Surveillance_des_flux
    # Disposition pour la page 3 : (A venir) |  Altertes_notifications
    # Disposition pour la page 4 : (A venir) |  Qualite_de_la_donnees
    # Disposition pour la page 5 : (A venir) |  Actualisation_des_donnees

    def _disposition(self, nom_de_page:str):
            """
                Crée la disposition (colonnes + séparateurs + conteneurs) pour la page 4.
                ratios: tuple pour le ratio des colonnes (gauche, droite), par défaut (2,3)
                
                Crée la disposition (colonnes + séparateurs + conteneurs) pour la page 4.
                Ne fait aucune opération métier (pas de service, pas de filtre).
                Retourne les conteneurs pour que la page injecte le contenu.
                
            """
            disposition = {}
            if nom_de_page == "Alertes et notification" :
                ratios: tuple[int, int] = (3, 7)
                # Barre de haut de page: 2 colonnes (gauche: Indicateurs/Filtres, droite: Alertes)
                col_gauche_indicateurs_filtres, col_droite_status_global_alerte = st.columns(list(ratios))

                # Conteneur Détails sous les colonnes
                details_alerte_par_jdd = st.container()

                disposition = {
                    "col_gauche": col_gauche_indicateurs_filtres,
                    "col_droite": col_droite_status_global_alerte,
                    "col_details": details_alerte_par_jdd,
                }
                # Retourne aussi pour usage direct
                st.session_state["disposition"] = disposition
                return st.session_state["disposition"]
            else:
                col_gauche, col_droite = st.columns([3, 7])
                col_details = st.container()
                disposition = {
                    "col_gauche": col_gauche,
                    "col_droite": col_droite,
                    "col_details": col_details,
                }
                # Retourne aussi pour usage direct
                st.session_state["disposition"] = disposition
                return st.session_state["disposition"]



    # Disposition pour la page 6 : (A venir) |  Gestion_des_referentiels
    # Disposition pour la page 7 : (A venir) |  Dev


    def _bas_de_page(self) -> None:
        """
        Footer HTML :
        - Centre : planning
        - Droite : utilisateur + rôles + fraîcheur
        """
        # 1) Fraîcheur
        try:
            svc = orchestration_service_alimenter_cache_app_en_data()
            (age_j, age_h, age_m, age_s), last_dt = svc.fraicheur_du_cache_de_donnees()

            def _fmt_j_h_m_s(j: int, h: int, m: int, s: int) -> str:
                return f"{j} j {h} h {m} min {s} s"

            donnees_fraiches_html = (
                f"<br/>Données fraîches depuis : <strong>{_fmt_j_h_m_s(age_j, age_h, age_m, age_s)}</strong>"
                if last_dt is not None else ""
            )
        except Exception:
            donnees_fraiches_html = ""

        # 2) Planning
        try:
            auto_enabled = bool(getattr(Configurations, "AUTO_REFRESH_CRON_ENABLED", True))
            cron_hour = int(getattr(Configurations, "AUTO_REFRESH_CRON_HOUR", 9))
            cron_minute = int(getattr(Configurations, "AUTO_REFRESH_CRON_MINUTE", 30))
            cron_spec = str(getattr(Configurations, "AUTO_REFRESH_CRON_WEEKDAYS", "mon-fri")).lower()

            def _fmt_cron_spec(spec: str) -> str:
                mapping = {"mon": "Lun", "tue": "Mar", "wed": "Mer", "thu": "Jeu", "fri": "Ven", "sat": "Sam", "sun": "Dim"}
                spec = (spec or "").strip().lower()
                if "-" in spec and "," not in spec:
                    a, b = spec.split("-", 1)
                    return f"{mapping.get(a, a.capitalize())}-{mapping.get(b, b.capitalize())}"
                parts = [p.strip() for p in spec.split(",") if p.strip()]
                return ", ".join(mapping.get(p, p.capitalize()) for p in parts)

            planning_txt = (
                f"Alimentation automatique: {'activée' if auto_enabled else 'désactivée'} • "
                f"créneau prévu: {cron_hour:02d}:{cron_minute:02d} ({_fmt_cron_spec(cron_spec)})."
            )
        except Exception:
            planning_txt = "Planification: indisponible pour le moment."

        # 3) Session utilisateur
        user = st.session_state.get("utilisateur") or "Invité"
        roles = st.session_state.get("roles") or []
        roles_txt = ", ".join(map(str, roles)) if roles else "—"
        auth_ok = bool(st.session_state.get("auth_ok", False))
        statut_chip = "✅" if auth_ok else "⚪️"

        # 4) Footer
        st.markdown(
            f"""
                <footer class="custom-footer">
                    <div class="footer-content">
                        <div class="footer-left"><strong>Outil de Supervision ODRE</strong></div>
                        <div class="footer-center">Page : 📊 <strong>{self.titre_page}</strong><br/><small>{planning_txt}</small></div>
                        <div class="footer-right">
                            {statut_chip} Connecté : <strong>{user}</strong> • Rôles : <strong>{roles_txt}</strong> | © {_dt.now().year}
                            {donnees_fraiches_html}
                        </div>
                    </div>
                </footer>
            """,
            unsafe_allow_html=True
        )



    # Bas de page (archive)
    def _bas_de_page_v2(self):
        """
        Footer HTML conservé :
        - Centre : inchangé (ton contenu existant)
        - Droite : ajoute "Données fraîches depuis : j h m s" uniquement si last_dt est connu
        - Droite : affiche l'utilisateur connecté + ses rôles si présents dans st.session_state
        """

        # --- 1) Données fraîcheur (ton code existant, conservé) ---
        try:
            svc = orchestration_service_alimenter_cache_app_en_data()
            (age_j, age_h, age_m, age_s), last_dt = svc.fraicheur_du_cache_de_donnees()

            def _fmt_j_h_m_s(j: int, h: int, m: int, s: int) -> str:
                return f"{j} j {h} h {m} min {s} s"

            donnees_fraiches_html = (
                f"<br/>Données fraîches depuis : <strong>{_fmt_j_h_m_s(age_j, age_h, age_m, age_s)}</strong>"
                if last_dt is not None else ""
            )
        except Exception:
            donnees_fraiches_html = ""

        # --- 2) Planning (ton code existant, conservé) ---
        try:
            from srcs.configs import Configurations
            auto_enabled = bool(getattr(Configurations, "AUTO_REFRESH_CRON_ENABLED", True))
            cron_hour = int(getattr(Configurations, "AUTO_REFRESH_CRON_HOUR", 9))
            cron_minute = int(getattr(Configurations, "AUTO_REFRESH_CRON_MINUTE", 30))
            cron_spec = str(getattr(Configurations, "AUTO_REFRESH_CRON_WEEKDAYS", "mon-fri")).lower()

            def _fmt_cron_spec(spec: str) -> str:
                mapping = {"mon": "Lun", "tue": "Mar", "wed": "Mer", "thu": "Jeu", "fri": "Ven", "sat": "Sam", "sun": "Dim"}
                spec = (spec or "").strip().lower()
                if "-" in spec and "," not in spec:
                    a, b = spec.split("-", 1)
                    return f"{mapping.get(a, a.capitalize())}-{mapping.get(b, b.capitalize())}"
                parts = [p.strip() for p in spec.split(",") if p.strip()]
                return ", ".join(mapping.get(p, p.capitalize()) for p in parts)

            planning_txt = (
                f"Alimentation automatique: {'activée' if auto_enabled else 'désactivée'} • "
                f"créneau prévu: {cron_hour:02d}:{cron_minute:02d} ({_fmt_cron_spec(cron_spec)})."
            )
        except Exception:
            planning_txt = "Planification: indisponible pour le moment."

        # --- 3) Infos utilisateur & rôles (NOUVEAU) ---
        user = st.session_state.get("utilisateur") or "Invité"
        roles = st.session_state.get("roles") or []
        # formatage pour éviter les affichages moches type [] ou quotes :
        roles_txt = ", ".join(map(str, roles)) if roles else "—"

        # --- 4) Footer HTML ---
        st.markdown(
            f"""
                <footer class="custom-footer">
                    <div class="footer-content">
                        <div class="footer-left"><strong>Outil de Supervision ODRE</strong></div>
                        <div class="footer-center">Page : 📊 <strong>{self.titre_page}</strong><br/><small>{planning_txt}</small></div>
                        <div class="footer-right">
                            Connecté en tant que <strong>{user}</strong> • Rôles : <strong>{roles_txt}</strong> | © {_dt.now().year}
                            {donnees_fraiches_html}
                        </div>
                    </div>
                </footer>
            """,
            unsafe_allow_html=True
        )

    def _bas_de_page_teste_v1(self):
        """
        Footer HTML conservé (centre = ligne de planning).
        """
        try:
            auto_enabled = bool(getattr(Configurations, "AUTO_REFRESH_CRON_ENABLED", True))
            cron_hour = int(getattr(Configurations, "AUTO_REFRESH_CRON_HOUR", 9))
            cron_minute = int(getattr(Configurations, "AUTO_REFRESH_CRON_MINUTE", 30))
            cron_spec = str(getattr(Configurations, "AUTO_REFRESH_CRON_WEEKDAYS", "mon-fri")).lower()

            def _fmt_cron_spec(spec: str) -> str:
                mapping = {"mon": "Lun", "tue": "Mar", "wed": "Mer", "thu": "Jeu", "fri": "Ven", "sat": "Sam", "sun": "Dim"}
                spec = (spec or "").strip().lower()
                if "-" in spec and "," not in spec:
                    a, b = spec.split("-", 1)
                    return f"{mapping.get(a, a.capitalize())}–{mapping.get(b, b.capitalize())}"
                parts = [p.strip() for p in spec.split(",") if p.strip()]
                return ", ".join(mapping.get(p, p.capitalize()) for p in parts)

            planning_txt = (
                f"Alimentation automatique: {'activée' if auto_enabled else 'désactivée'} • "
                f"créneau prévu: {cron_hour:02d}:{cron_minute:02d} ({_fmt_cron_spec(cron_spec)})."
            )

        except Exception:
            planning_txt = "Planification: indisponible pour le moment."

        st.markdown(
            f"""
                <footer class="custom-footer">
                    <div class="footer-content">
                        <div class="footer-left"><strong>Outil de Supervision ODRE</strong></div>
                        <div class="footer-center">Page : 📊 <strong>{self.titre_page}</strong><br/><small>{planning_txt}</small></div>
                        <div class="footer-right">Connecté en tant que <strong>{self.utilisateur} | © {_dt.now().year}</strong><br/>Données fraiches depuis :</div>
                    </div>
                </footer>
            """,
            unsafe_allow_html=True
        )

    def _bas_de_page_v3(self):
        """
        Pied de page standard :
        - Rappel du nom de la page et de l'utilisateur
        - Fraîcheur des données (cache + parquet consolidé)
        - Rappel du planning (09:30, Lun–Ven)
        """
        try:
            # 1) Infos de fraîcheur via le service d'orchestration (cache JSON)
            svc = orchestration_service_alimenter_cache_app_en_data()
            (age_j, age_h, age_m, age_s), last_dt = svc.fraicheur_du_cache_de_donnees()

            # Format lisible pour l’âge du cache
            def _fmt_age(j, h, m, s) -> str:
                # Exemples: "2 j 3 h", "3 h 12 min", "15 min 4 s"
                if j > 0:
                    return f"{j} j {h} h"
                if h > 0:
                    return f"{h} h {m} min"
                if m > 0:
                    return f"{m} min {s} s" if s > 0 else f"{m} min"
                return f"{s} s"

            # 2) Infos de fraîcheur du Parquet consolidé (optionnel, si présent)
            parquet_path = getattr(Configurations, "SORTIE_PARQUET_JDD_PATH", Path("srcs/data/JDD_ODRE.parquet"))
            parquet_age_txt = None
            parquet_mtime_txt = None
            try:
                p = Path(parquet_path)
                if p.exists():
                    mtime = datetime.fromtimestamp(p.stat().st_mtime, tz=Configurations.TIME_ZONE)
                    now = datetime.now(Configurations.TIME_ZONE)
                    delta = now - mtime
                    # Convertir en j/h/min/s
                    total_seconds = int(delta.total_seconds())
                    j2, h2, m2, s2 = _age_cache_en_j_h_m_s(total_seconds)
                    parquet_age_txt = _fmt_age(j2, h2, m2, s2)
                    parquet_mtime_txt = mtime.strftime("%d/%m/%Y %H:%M")
            except Exception:
                # On reste silencieux si le parquet n'est pas accessible
                pass

            # 3) Texte de planning (config)
            # Exemple: "Maj quotidienne prévue à 09:30 (Lun–Ven)"
            cron_hour = int(getattr(Configurations, "AUTO_REFRESH_CRON_HOUR", 9))
            cron_minute = int(getattr(Configurations, "AUTO_REFRESH_CRON_MINUTE", 30))
            cron_spec = str(getattr(Configurations, "AUTO_REFRESH_CRON_WEEKDAYS", "mon-fri")).lower()

            # Conversion simple "mon-fri" -> "Lun–Ven"
            def _fmt_cron_spec(spec: str) -> str:
                mapping = {
                    "mon": "Lun", "tue": "Mar", "wed": "Mer",
                    "thu": "Jeu", "fri": "Ven", "sat": "Sam", "sun": "Dim"
                }
                if "-" in spec and "," not in spec:
                    a, b = spec.split("-", 1)
                    return f"{mapping.get(a, a.capitalize())}-{mapping.get(b, b.capitalize())}"
                # Liste "mon,wed,fri" -> "Lun, Mer, Ven"
                parts = [p.strip() for p in spec.split(",")]
                return ", ".join(mapping.get(p, p.capitalize()) for p in parts if p)
            planning_txt = f"Maj quotidienne prévue à {cron_hour:02d}:{cron_minute:02d} ({_fmt_cron_spec(cron_spec)})"

            # 4) Construction du HTML de fraîcheur
            if last_dt is not None:
                last_txt = last_dt.strftime("%d/%m/%Y %H:%M")
                cache_html = f"Dernier rafraîchissement du cache: <strong>{last_txt}</strong> • âge: <strong>{_fmt_age(age_j, age_h, age_m, age_s)}</strong>"
            else:
                cache_html = "Cache des données: <strong>non initialisé</strong>"

            if parquet_mtime_txt and parquet_age_txt:
                parquet_html = f"Données consolidées (Parquet): <strong>{parquet_mtime_txt}</strong> • âge: <strong>{parquet_age_txt}</strong>"
            else:
                parquet_html = "Données consolidées (Parquet): <strong>indisponibles</strong>"

            freshness_html = f"{cache_html} • {parquet_html} • {planning_txt}"

        except Exception:
            freshness_html = "Données sources: <strong>indisponibles</strong>"
        st.markdown(
            f"""
                <footer class="custom-footer">
                    <div class="footer-content">
                        <div class="footer-left"><strong>Outil de Supervision ODRE</strong></div>
                        <div class="footer-center">Page : 📊 <strong>{self.titre_page}</strong><br/><small>{freshness_html}</small></div>
                        <div class="footer-right">Connecté en tant que <strong>{self.utilisateur} | © {_dt.now().year}</strong></div>
                    </div>
                </footer>
            """,
            unsafe_allow_html=True
        )

    def _bas_de_page_v2_archive(self):
        """
        Footer HTML conservé :
        - Centre : inchangé (ton contenu existant)
        - Droite : ajoute "Données fraîches depuis : j h m s" uniquement si last_dt est connu
        """

        try:
            svc = orchestration_service_alimenter_cache_app_en_data()
            (age_j, age_h, age_m, age_s), last_dt = svc.fraicheur_du_cache_de_donnees()

            # Format j h m s – affiche toutes les unités
            def _fmt_j_h_m_s(j: int, h: int, m: int, s: int) -> str:
                return f"{j} j {h} h {m} min {s} s"

            # Si last_dt est connu, on prépare la ligne HTML à ajouter à droite ; sinon, rien
            donnees_fraiches_html = (
                f"<br/>Données fraîches depuis : <strong>{_fmt_j_h_m_s(age_j, age_h, age_m, age_s)}</strong>"
                if last_dt is not None else ""
            )
        except Exception:
            donnees_fraiches_html = ""  # aucune info si erreur ou cache absent

        try:
            from srcs.configs import Configurations

            auto_enabled = bool(getattr(Configurations, "AUTO_REFRESH_CRON_ENABLED", True))
            cron_hour = int(getattr(Configurations, "AUTO_REFRESH_CRON_HOUR", 9))
            cron_minute = int(getattr(Configurations, "AUTO_REFRESH_CRON_MINUTE", 30))
            cron_spec = str(getattr(Configurations, "AUTO_REFRESH_CRON_WEEKDAYS", "mon-fri")).lower()

            def _fmt_cron_spec(spec: str) -> str:
                mapping = {"mon": "Lun", "tue": "Mar", "wed": "Mer", "thu": "Jeu", "fri": "Ven", "sat": "Sam", "sun": "Dim"}
                spec = (spec or "").strip().lower()
                if "-" in spec and "," not in spec:
                    a, b = spec.split("-", 1)
                    return f"{mapping.get(a, a.capitalize())}-{mapping.get(b, b.capitalize())}"
                parts = [p.strip() for p in spec.split(",") if p.strip()]
                return ", ".join(mapping.get(p, p.capitalize()) for p in parts)

            planning_txt = (
                f"Alimentation automatique: {'activée' if auto_enabled else 'désactivée'} • "
                f"créneau prévu: {cron_hour:02d}:{cron_minute:02d} ({_fmt_cron_spec(cron_spec)})."
            )
        except Exception:
            planning_txt = "Planification: indisponible pour le moment."

        # === Footer HTML : structure conservée, on ajoute juste la ligne à droite ===
        st.markdown(
            f"""
                <footer class="custom-footer">
                    <div class="footer-content">
                        <div class="footer-left"><strong>Outil de Supervision ODRE</strong></div>
                        <div class="footer-center">Page : 📊 <strong>{self.titre_page}</strong><br/><small>{planning_txt}</small></div>
                        <div class="footer-right">Connecté en tant que <strong>{self.utilisateur} | © {_dt.now().year}</strong>{donnees_fraiches_html}</div>
                    </div>
                </footer>
            """,
            unsafe_allow_html=True
        )

    def _bas_de_page_v0(self):
        """
            Rappel du nom de la page à l'utilisateur
            Rappel de la session de l'utilisateur
            Récupérer le nom de la page via son numéro 
            dans les variables d'environnement
        """    
        # Infos fraîcheur des données (parquet JDD)
        try:
            parquet_path = getattr(Configurations, "JDD_ODRE_PATH_PARQUET", "src/data/JDD_ODRE.parquet")
            p = Path(parquet_path)
            if p.exists():
                mtime = datetime.fromtimestamp(p.stat().st_mtime)
                now = datetime.now()
                delta = now - mtime
                def _fmt_delta(d: timedelta) -> str:
                    if d.days > 0:
                        hours = d.seconds // 3600
                        return f"{d.days} j {hours} h"
                    hours = d.seconds // 3600
                    minutes = (d.seconds % 3600) // 60
                    if hours > 0:
                        return f"{hours} h {minutes} min"
                    return f"{minutes} min"
                age_txt = _fmt_delta(delta)
                mtime_txt = mtime.strftime("%d/%m/%Y %H:%M")
                planning_txt = "Maj quotidienne prévue à 09:30 (Lun–Ven)"
                freshness_html = f"Données sources du <strong>{mtime_txt}</strong> • âge: <strong>{age_txt}</strong> • {planning_txt}"
            else:
                freshness_html = "Données sources: <strong>cache non initialisé</strong> • Maj quotidienne prévue à 09:30 (Lun–Ven)"

        except Exception:
            freshness_html = "Données sources: <strong>indisponibles</strong>"

        st.markdown(
            f"""
                <footer class="custom-footer">
                    <div class="footer-content">
                        <div class="footer-left"><strong>Outil de Supervision ODRE</strong></div>
                        <div class="footer-center">Page : 📊 <strong>{self.titre_page}</strong><br/><small>{freshness_html}</small></div>
                        <div class="footer-right">Connecté en tant que <strong>{self.utilisateur} | © {datetime.now().year}</strong></div>
                    </div>
                </footer>
            """,
            unsafe_allow_html=True
        )

