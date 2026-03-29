"""Page Compose Inference."""

from __future__ import annotations

import logging
import random
import sys
from pathlib import Path

import requests
import streamlit as st

try:
    import streamlit_antd_components as sac
except ImportError as exc:
    raise RuntimeError(
        "Le paquet 'streamlit-antd-components' est requis."
    ) from exc

SRC_DIR = Path(__file__).resolve().parents[2]
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from app.components import header, section_divider
from app.config import API_TIMEOUT, ENDPOINTS, FEATURES, FIELD_OPTIONS, FIELD_RANGES

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _random_code_postal() -> str:
    return f"{random.randint(1, 95):05d}"


def _generate_auto_fields() -> dict:
    """Génère aléatoirement tous les champs non-saisis par l'assureur."""
    r = FIELD_RANGES
    opts = FIELD_OPTIONS
    conducteur2 = random.choice(opts["conducteur2"])
    return {
        "auto_bonus": round(random.choice([i / 100 for i in range(50, 105, 5)]), 2),
        "auto_type_contrat": random.choice(opts["type_contrat"]),
        "auto_duree_contrat": random.randint(*r["duree_contrat"]),
        "auto_anciennete_info": random.randint(*r["anciennete_info"]),
        "auto_freq_paiement": random.choice(opts["freq_paiement"]),
        "auto_paiement": random.choice(opts["paiement"]),
        "auto_utilisation": random.choice(opts["utilisation"]),
        "auto_code_postal": _random_code_postal(),
        "auto_conducteur2": conducteur2,
        "auto_age_conducteur2": random.randint(*r["age_conducteur2"]) if conducteur2 == "Yes" else 0,
        "auto_sex_conducteur2": random.choice(opts["sex_conducteur2"]) if conducteur2 == "Yes" else "",
        "auto_anciennete_permis2": random.randint(*r["anciennete_permis2"]) if conducteur2 == "Yes" else 0,
        "auto_anciennete_vehicule": round(random.uniform(*r["anciennete_vehicule"]), 1),
        "auto_din_vehicule": random.randint(*r["din_vehicule"]),
        "auto_marque_vehicule": random.choice(opts["marque_vehicule"]),
        "auto_modele_vehicule": "",
        "auto_debut_vente_vehicule": random.randint(*r["debut_vente_vehicule"]),
        "auto_fin_vente_vehicule": random.randint(*r["fin_vente_vehicule"]),
        "auto_vitesse_vehicule": random.randint(*r["vitesse_vehicule"]),
        "auto_poids_vehicule": random.randint(*r["poids_vehicule"]),
    }


def _build_payload(manual: dict, auto: dict) -> dict:
    """Assemble le payload API à partir des champs manuels et auto-générés."""
    return {
        "bonus": auto.get("auto_bonus", 0.5),
        "type_contrat": auto.get("auto_type_contrat", "Maxi"),
        "duree_contrat": auto.get("auto_duree_contrat", 12),
        "anciennete_info": auto.get("auto_anciennete_info", 1),
        "freq_paiement": auto.get("auto_freq_paiement", "Yearly"),
        "paiement": auto.get("auto_paiement", "No"),
        "utilisation": auto.get("auto_utilisation", "WorkPrivate"),
        "code_postal": auto.get("auto_code_postal", "75001"),
        "conducteur2": auto.get("auto_conducteur2", "No"),
        "age_conducteur1": manual["age_conducteur1"],
        "age_conducteur2": auto.get("auto_age_conducteur2", 0),
        "sex_conducteur1": manual["sex_conducteur1"],
        "sex_conducteur2": auto.get("auto_sex_conducteur2", ""),
        "anciennete_permis1": manual["anciennete_permis1"],
        "anciennete_permis2": auto.get("auto_anciennete_permis2", 0),
        "anciennete_vehicule": auto.get("auto_anciennete_vehicule", 5.0),
        "cylindre_vehicule": manual["cylindre_vehicule"],
        "din_vehicule": auto.get("auto_din_vehicule", 100),
        "essence_vehicule": manual["essence_vehicule"],
        "marque_vehicule": auto.get("auto_marque_vehicule", "PEUGEOT"),
        "modele_vehicule": auto.get("auto_modele_vehicule", ""),
        "debut_vente_vehicule": auto.get("auto_debut_vente_vehicule", 5),
        "fin_vente_vehicule": auto.get("auto_fin_vente_vehicule", 2),
        "vitesse_vehicule": auto.get("auto_vitesse_vehicule", 180),
        "type_vehicule": manual["type_vehicule"],
        "prix_vehicule": manual["prix_vehicule"],
        "poids_vehicule": auto.get("auto_poids_vehicule", 1200),
    }


# ---------------------------------------------------------------------------
# Render
# ---------------------------------------------------------------------------

def render() -> None:
    """Affiche la page compose inference."""
    try:
        header("Compose Inference", "Prédiction de fréquence et sévérité")

        # ── Options ────────────────────────────────────────────────────────
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

        # ── Saisie manuelle ────────────────────────────────────────────────
        section_divider("Données conducteur & véhicule", icon="person-fill")
        st.caption("Informations à renseigner lors de l'entretien client.")

        c1, c2, c3 = st.columns(3)
        with c1:
            age_cond1 = st.number_input(
                "Âge conducteur 1", min_value=18, max_value=100, value=35, key="age_conducteur1"
            )
            anc_permis1 = st.number_input(
                "Ancienneté permis (ans)", min_value=0, max_value=70, value=10, key="anciennete_permis1"
            )
            sex_cond1 = st.selectbox(
                "Sexe conducteur 1", options=FIELD_OPTIONS["sex_conducteur1"], key="sex_conducteur1"
            )
        with c2:
            essence = st.selectbox(
                "Carburant", options=FIELD_OPTIONS["essence_vehicule"], key="essence_vehicule"
            )
            type_veh = st.selectbox(
                "Type véhicule", options=FIELD_OPTIONS["type_vehicule"], key="type_vehicule"
            )
        with c3:
            cylindre = st.number_input(
                "Cylindrée (cc)", min_value=500, max_value=8000, value=1600, step=100, key="cylindre_vehicule"
            )
            prix_veh = st.number_input(
                "Prix véhicule (€)", min_value=0, max_value=500_000, value=20_000, step=500, key="prix_vehicule"
            )

        st.divider()

        # ── Remplissage automatique ────────────────────────────────────────
        section_divider("Données complémentaires (auto-générées)", icon="lightning-fill")
        st.caption("Ces champs sont générés aléatoirement à partir des distributions du jeu d'entraînement.")

        col_btn, _ = st.columns([1, 3])
        with col_btn:
            if st.button("🔄 Remplissage auto", use_container_width=True, type="primary"):
                for k, v in _generate_auto_fields().items():
                    st.session_state[k] = v
                st.toast("Champs complémentaires générés !", icon="✅")

        # Initialisation au premier chargement
        if "auto_bonus" not in st.session_state:
            for k, v in _generate_auto_fields().items():
                st.session_state[k] = v

        auto = {k: st.session_state[k] for k in st.session_state if k.startswith("auto_")}

        with st.expander("Voir les champs générés", expanded=False):
            ac1, ac2, ac3, ac4 = st.columns(4)
            with ac1:
                st.metric("Bonus", auto.get("auto_bonus", "–"))
                st.metric("Type contrat", auto.get("auto_type_contrat", "–"))
                st.metric("Durée contrat", f"{auto.get('auto_duree_contrat', '–')} mois")
                st.metric("Utilisation", auto.get("auto_utilisation", "–"))
            with ac2:
                st.metric("Fréq. paiement", auto.get("auto_freq_paiement", "–"))
                st.metric("Paiement CB", auto.get("auto_paiement", "–"))
                st.metric("Code postal", auto.get("auto_code_postal", "–"))
                st.metric("Ancienneté info", auto.get("auto_anciennete_info", "–"))
            with ac3:
                st.metric("2ème conducteur", auto.get("auto_conducteur2", "–"))
                st.metric("Âge cond. 2", auto.get("auto_age_conducteur2", "–"))
                st.metric("Anc. permis 2", auto.get("auto_anciennete_permis2", "–"))
                st.metric("Marque", auto.get("auto_marque_vehicule", "–"))
            with ac4:
                st.metric("Anc. véhicule", f"{auto.get('auto_anciennete_vehicule', '–')} ans")
                st.metric("DIN (ch)", auto.get("auto_din_vehicule", "–"))
                st.metric("Vitesse max", f"{auto.get('auto_vitesse_vehicule', '–')} km/h")
                st.metric("Poids", f"{auto.get('auto_poids_vehicule', '–')} kg")

        st.divider()

        # ── Lancer la prédiction ───────────────────────────────────────────
        section_divider("Résultats", icon="check-circle")

        if st.button("⚡ Lancer la prédiction", type="primary"):
            manual = {
                "age_conducteur1": int(age_cond1),
                "anciennete_permis1": int(anc_permis1),
                "sex_conducteur1": sex_cond1,
                "essence_vehicule": essence,
                "type_vehicule": type_veh,
                "cylindre_vehicule": int(cylindre),
                "prix_vehicule": int(prix_veh),
            }
            payload = _build_payload(manual, auto)
            results: dict = {}
            error_occurred = False

            try:
                with st.spinner("Appel API en cours..."):
                    if pred_type in ("Fréquence", "Combinée"):
                        resp = requests.post(
                            ENDPOINTS["predict_frequence"], json=payload, timeout=API_TIMEOUT
                        )
                        resp.raise_for_status()
                        results["frequence"] = resp.json()
                    if pred_type in ("Sévérité", "Combinée"):
                        resp = requests.post(
                            ENDPOINTS["predict_severite"], json=payload, timeout=API_TIMEOUT
                        )
                        resp.raise_for_status()
                        results["severite"] = resp.json()
            except requests.exceptions.ConnectionError:
                st.error("❌ Impossible de joindre l'API. Vérifie que le serveur est démarré.")
                logger.exception("Connexion API échouée")
                error_occurred = True
            except requests.exceptions.HTTPError as exc:
                st.error(f"❌ Erreur API : {exc.response.status_code} — {exc.response.text}")
                logger.exception("Erreur HTTP API")
                error_occurred = True
            except Exception:
                st.error("❌ Erreur inattendue lors de la prédiction.")
                logger.exception("Erreur prediction")
                error_occurred = True

            if not error_occurred and results:
                rc1, rc2 = st.columns(2)
                freq_val_num: float | None = None
                sev_val_num: float | None = None

                if "frequence" in results:
                    with rc1:
                        val = results["frequence"]
                        freq_val_num = val.get("prediction", val.get("frequence"))
                        st.success("✅ Fréquence prédite")
                        st.metric(
                            "Fréquence sinistres",
                            f"{freq_val_num:.4f}" if isinstance(freq_val_num, float) else str(freq_val_num),
                        )

                if "severite" in results:
                    with rc2:
                        val = results["severite"]
                        sev_val_num = val.get("prediction", val.get("severite"))
                        st.success("✅ Sévérité prédite")
                        st.metric(
                            "Sévérité (€)",
                            f"{sev_val_num:.2f}" if isinstance(sev_val_num, float) else str(sev_val_num),
                        )

                if isinstance(freq_val_num, (int, float)) and isinstance(sev_val_num, (int, float)):
                    prime = freq_val_num * sev_val_num
                    st.divider()
                    st.metric("💰 Prime estimée (€)", f"{prime:.2f}")

                logger.info("Prediction reussie: type=%s mode=%s", pred_type, mode)

        col1, col2 = st.columns(2)
        with col1:
            st.caption(f"API Endpoint F: {ENDPOINTS['predict_frequence'].rsplit('/', 1)[0]}/docs")
        with col2:
            st.caption(f"API Endpoint S: {ENDPOINTS['predict_severite'].rsplit('/', 1)[0]}/docs")

    except Exception:
        logger.exception("Echec du rendu de la page inference")
        st.error("Une erreur est survenue lors du chargement de la page inference.")
