"""Page Compose Contrat."""

from __future__ import annotations

import logging
import random
import sys
from pathlib import Path

import requests
import streamlit as st

SRC_DIR = Path(__file__).resolve().parents[2]
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from app.components import header, info_box, section_divider
from app.config import API_TIMEOUT, ENDPOINTS, FIELD_OPTIONS, FIELD_RANGES
from app.services import ContratGateway

logger = logging.getLogger(__name__)


MANUAL_STATE_KEYS = {
    "id_client": "contrat_id_client",
    "id_vehicule": "contrat_id_vehicule",
    "id_contrat": "contrat_id_contrat",
    "age_conducteur1": "contrat_age_conducteur1",
    "anciennete_permis1": "contrat_anciennete_permis1",
    "sex_conducteur1": "contrat_sex_conducteur1",
    "essence_vehicule": "contrat_essence_vehicule",
    "type_vehicule": "contrat_type_vehicule",
    "cylindre_vehicule": "contrat_cylindre_vehicule",
    "prix_vehicule": "contrat_prix_vehicule",
}

AUTO_STATE_KEYS = {
    "bonus": "contrat_auto_bonus",
    "type_contrat": "contrat_auto_type_contrat",
    "duree_contrat": "contrat_auto_duree_contrat",
    "anciennete_info": "contrat_auto_anciennete_info",
    "freq_paiement": "contrat_auto_freq_paiement",
    "paiement": "contrat_auto_paiement",
    "utilisation": "contrat_auto_utilisation",
    "code_postal": "contrat_auto_code_postal",
    "conducteur2": "contrat_auto_conducteur2",
    "age_conducteur2": "contrat_auto_age_conducteur2",
    "sex_conducteur2": "contrat_auto_sex_conducteur2",
    "anciennete_permis2": "contrat_auto_anciennete_permis2",
    "anciennete_vehicule": "contrat_auto_anciennete_vehicule",
    "din_vehicule": "contrat_auto_din_vehicule",
    "marque_vehicule": "contrat_auto_marque_vehicule",
    "modele_vehicule": "contrat_auto_modele_vehicule",
    "debut_vente_vehicule": "contrat_auto_debut_vente_vehicule",
    "fin_vente_vehicule": "contrat_auto_fin_vente_vehicule",
    "vitesse_vehicule": "contrat_auto_vitesse_vehicule",
    "poids_vehicule": "contrat_auto_poids_vehicule",
    "nombre_sinistres": "contrat_auto_nombre_sinistres",
    "montant_sinistre": "contrat_auto_montant_sinistre",
}


def _random_code_postal() -> str:
    return f"{random.randint(1, 95):05d}"


def _random_id(prefix: str) -> str:
    return f"{prefix}_{random.randint(10000, 99999)}"


def _generate_auto_contract_fields() -> dict:
    r = FIELD_RANGES
    opts = FIELD_OPTIONS
    conducteur2 = random.choice(opts["conducteur2"])
    return {
        "bonus": round(random.choice([i / 100 for i in range(50, 105, 5)]), 2),
        "type_contrat": random.choice(opts["type_contrat"]),
        "duree_contrat": random.randint(*r["duree_contrat"]),
        "anciennete_info": random.randint(*r["anciennete_info"]),
        "freq_paiement": random.choice(opts["freq_paiement"]),
        "paiement": random.choice(opts["paiement"]),
        "utilisation": random.choice(opts["utilisation"]),
        "code_postal": _random_code_postal(),
        "conducteur2": conducteur2,
        "age_conducteur2": random.randint(*r["age_conducteur2"]) if conducteur2 == "Yes" else 0,
        "sex_conducteur2": random.choice(opts["sex_conducteur2"]) if conducteur2 == "Yes" else "",
        "anciennete_permis2": random.randint(*r["anciennete_permis2"]) if conducteur2 == "Yes" else 0,
        "anciennete_vehicule": round(random.uniform(*r["anciennete_vehicule"]), 1),
        "din_vehicule": random.randint(*r["din_vehicule"]),
        "marque_vehicule": random.choice(opts["marque_vehicule"]),
        "modele_vehicule": "",
        "debut_vente_vehicule": random.randint(*r["debut_vente_vehicule"]),
        "fin_vente_vehicule": random.randint(*r["fin_vente_vehicule"]),
        "vitesse_vehicule": random.randint(*r["vitesse_vehicule"]),
        "poids_vehicule": random.randint(*r["poids_vehicule"]),
        "nombre_sinistres": random.randint(0, 4),
        "montant_sinistre": round(random.uniform(0, 20_000), 2),
    }


def _init_state() -> None:
    manual_defaults = {
        "id_client": _random_id("CLI"),
        "id_vehicule": _random_id("VEH"),
        "id_contrat": _random_id("CTR"),
        "age_conducteur1": 35,
        "anciennete_permis1": 10,
        "sex_conducteur1": FIELD_OPTIONS["sex_conducteur1"][0],
        "essence_vehicule": FIELD_OPTIONS["essence_vehicule"][0],
        "type_vehicule": FIELD_OPTIONS["type_vehicule"][0],
        "cylindre_vehicule": 1600,
        "prix_vehicule": 20_000,
    }
    auto_defaults = _generate_auto_contract_fields()

    for field_name, state_key in MANUAL_STATE_KEYS.items():
        if state_key not in st.session_state:
            st.session_state[state_key] = manual_defaults[field_name]

    for field_name, state_key in AUTO_STATE_KEYS.items():
        if state_key not in st.session_state:
            st.session_state[state_key] = auto_defaults[field_name]

    if "contrat_edit_original_id" not in st.session_state:
        st.session_state["contrat_edit_original_id"] = ""


def _collect_manual() -> dict:
    return {
        field_name: st.session_state[state_key]
        for field_name, state_key in MANUAL_STATE_KEYS.items()
    }


def _collect_auto() -> dict:
    return {
        field_name: st.session_state[state_key]
        for field_name, state_key in AUTO_STATE_KEYS.items()
    }


def _build_payload(manual: dict, auto: dict) -> dict:
    return {
        "id_client": manual["id_client"],
        "id_vehicule": manual["id_vehicule"],
        "id_contrat": manual["id_contrat"],
        "bonus": float(auto["bonus"]),
        "type_contrat": auto["type_contrat"],
        "duree_contrat": int(auto["duree_contrat"]),
        "anciennete_info": int(auto["anciennete_info"]),
        "freq_paiement": auto["freq_paiement"],
        "paiement": auto["paiement"],
        "utilisation": auto["utilisation"],
        "code_postal": str(auto["code_postal"]),
        "conducteur2": auto["conducteur2"],
        "age_conducteur1": int(manual["age_conducteur1"]),
        "age_conducteur2": int(auto["age_conducteur2"]),
        "sex_conducteur1": manual["sex_conducteur1"],
        "sex_conducteur2": auto["sex_conducteur2"],
        "anciennete_permis1": int(manual["anciennete_permis1"]),
        "anciennete_permis2": int(auto["anciennete_permis2"]),
        "anciennete_vehicule": float(auto["anciennete_vehicule"]),
        "cylindre_vehicule": int(manual["cylindre_vehicule"]),
        "din_vehicule": int(auto["din_vehicule"]),
        "essence_vehicule": manual["essence_vehicule"],
        "marque_vehicule": auto["marque_vehicule"],
        "modele_vehicule": auto["modele_vehicule"],
        "debut_vente_vehicule": int(auto["debut_vente_vehicule"]),
        "fin_vente_vehicule": int(auto["fin_vente_vehicule"]),
        "vitesse_vehicule": int(auto["vitesse_vehicule"]),
        "type_vehicule": manual["type_vehicule"],
        "prix_vehicule": int(manual["prix_vehicule"]),
        "poids_vehicule": int(auto["poids_vehicule"]),
        "nombre_sinistres": int(auto["nombre_sinistres"]),
        "montant_sinistre": float(auto["montant_sinistre"]),
    }


def _apply_loaded_contract(contract: dict) -> None:
    for field_name, state_key in MANUAL_STATE_KEYS.items():
        if field_name in contract:
            st.session_state[state_key] = contract[field_name]

    for field_name, state_key in AUTO_STATE_KEYS.items():
        if field_name in contract:
            st.session_state[state_key] = contract[field_name]

    st.session_state["contrat_edit_original_id"] = contract.get("id_contrat", "")


def render() -> None:
    """Affiche la page compose contrat."""
    try:
        _init_state()
        gateway = ContratGateway(ENDPOINTS["contrats"], timeout=API_TIMEOUT)

        header("Compose Contrat", "Création et édition de contrats d'assurance")

        section_divider("Mode d'édition", icon="sliders")
        mode = st.radio(
            "Choisir le mode",
            options=["Création", "Édition"],
            horizontal=True,
            label_visibility="collapsed",
        )

        if mode == "Édition":
            col_load_1, col_load_2 = st.columns([2, 1])
            with col_load_1:
                load_id = st.text_input("ID contrat à charger", placeholder="ex: CTR_12345")
            with col_load_2:
                if st.button("Charger", use_container_width=True):
                    if not load_id.strip():
                        st.warning("Saisis un id_contrat pour charger un contrat.")
                    else:
                        try:
                            contract = gateway.get_by_id(load_id.strip())
                            _apply_loaded_contract(contract)
                            st.success(f"Contrat '{load_id.strip()}' chargé.")
                        except requests.exceptions.HTTPError as exc:
                            if exc.response.status_code == 404:
                                st.error("Contrat introuvable.")
                            else:
                                st.error(f"Erreur API: {exc.response.status_code} - {exc.response.text}")
                        except Exception as exc:
                            logger.exception("Erreur chargement contrat")
                            st.error(f"Erreur de chargement: {exc}")

            st.caption("En mode édition, la mise à jour est appliquée sur l'identifiant chargé.")

        section_divider("Saisie manuelle", icon="pencil-square")

        c1, c2, c3 = st.columns(3)
        with c1:
            st.text_input("ID client", key=MANUAL_STATE_KEYS["id_client"])
            st.text_input("ID véhicule", key=MANUAL_STATE_KEYS["id_vehicule"])
            st.text_input("ID contrat", key=MANUAL_STATE_KEYS["id_contrat"])
        with c2:
            st.number_input(
                "Âge conducteur 1",
                min_value=18,
                max_value=100,
                key=MANUAL_STATE_KEYS["age_conducteur1"],
            )
            st.number_input(
                "Ancienneté permis 1",
                min_value=0,
                max_value=70,
                key=MANUAL_STATE_KEYS["anciennete_permis1"],
            )
            st.selectbox(
                "Sexe conducteur 1",
                options=FIELD_OPTIONS["sex_conducteur1"],
                key=MANUAL_STATE_KEYS["sex_conducteur1"],
            )
        with c3:
            st.selectbox(
                "Carburant",
                options=FIELD_OPTIONS["essence_vehicule"],
                key=MANUAL_STATE_KEYS["essence_vehicule"],
            )
            st.selectbox(
                "Type véhicule",
                options=FIELD_OPTIONS["type_vehicule"],
                key=MANUAL_STATE_KEYS["type_vehicule"],
            )
            st.number_input(
                "Cylindrée",
                min_value=500,
                max_value=8000,
                step=100,
                key=MANUAL_STATE_KEYS["cylindre_vehicule"],
            )
            st.number_input(
                "Prix véhicule",
                min_value=0,
                max_value=500_000,
                step=500,
                key=MANUAL_STATE_KEYS["prix_vehicule"],
            )

        section_divider("Compléments auto-générés", icon="lightning-fill")
        col_auto_1, col_auto_2 = st.columns([1, 3])
        with col_auto_1:
            if st.button("🔄 Remplissage auto", type="primary", use_container_width=True):
                for field_name, value in _generate_auto_contract_fields().items():
                    st.session_state[AUTO_STATE_KEYS[field_name]] = value
                st.toast("Champs auto mis à jour", icon="✅")

        auto_data = _collect_auto()
        with st.expander("Voir les champs auto", expanded=False):
            a1, a2, a3, a4 = st.columns(4)
            with a1:
                st.metric("Bonus", auto_data["bonus"])
                st.metric("Type contrat", auto_data["type_contrat"])
                st.metric("Durée", auto_data["duree_contrat"])
                st.metric("Ancienneté info", auto_data["anciennete_info"])
            with a2:
                st.metric("Paiement", auto_data["paiement"])
                st.metric("Freq paiement", auto_data["freq_paiement"])
                st.metric("Utilisation", auto_data["utilisation"])
                st.metric("Code postal", auto_data["code_postal"])
            with a3:
                st.metric("2e conducteur", auto_data["conducteur2"])
                st.metric("Âge cond.2", auto_data["age_conducteur2"])
                st.metric("Permis cond.2", auto_data["anciennete_permis2"])
                st.metric("Marque", auto_data["marque_vehicule"])
            with a4:
                st.metric("DIN", auto_data["din_vehicule"])
                st.metric("Vitesse", auto_data["vitesse_vehicule"])
                st.metric("Poids", auto_data["poids_vehicule"])
                st.metric("Sinistres", auto_data["nombre_sinistres"])

        st.divider()

        manual_data = _collect_manual()
        payload = _build_payload(manual_data, auto_data)

        col_action_1, col_action_2 = st.columns(2)
        with col_action_1:
            if st.button("Créer contrat", use_container_width=True, disabled=mode != "Création"):
                try:
                    created = gateway.create(payload)
                    st.success(f"Contrat créé: {created['id_contrat']}")
                except requests.exceptions.HTTPError as exc:
                    st.error(f"Erreur API: {exc.response.status_code} - {exc.response.text}")
                except Exception as exc:
                    logger.exception("Erreur création contrat")
                    st.error(f"Erreur création: {exc}")
        with col_action_2:
            if st.button("Mettre à jour", use_container_width=True, disabled=mode != "Édition"):
                original_id = st.session_state.get("contrat_edit_original_id") or payload["id_contrat"]
                payload_update = dict(payload)
                payload_update["id_contrat"] = original_id
                try:
                    updated = gateway.update(original_id, payload_update)
                    st.session_state["contrat_edit_original_id"] = updated["id_contrat"]
                    st.success(f"Contrat mis à jour: {updated['id_contrat']}")
                except requests.exceptions.HTTPError as exc:
                    st.error(f"Erreur API: {exc.response.status_code} - {exc.response.text}")
                except Exception as exc:
                    logger.exception("Erreur mise à jour contrat")
                    st.error(f"Erreur mise à jour: {exc}")

        section_divider("Contrats récents", icon="list-check")
        try:
            recent = gateway.list_recent(limit=10)
            if recent:
                st.dataframe(recent, use_container_width=True)
            else:
                st.info("📋 Aucun contrat en base pour le moment.")
        except Exception as exc:
            logger.exception("Erreur chargement contrats récents")
            st.error(f"Impossible de charger les contrats récents: {exc}")

        info_box("API Contrats", ENDPOINTS["contrats"], "Endpoint contrats")
        st.caption(f"API Endpoint: {ENDPOINTS['contrats']}")
    except Exception:
        logger.exception("Echec du rendu de la page contrat")
        st.error("Une erreur est survenue lors du chargement de la page contrat.")
