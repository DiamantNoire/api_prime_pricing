import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[5]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.api.backend.controllers.contrat_controller import contrat_router


@pytest.fixture
def valid_payload():
    return {
        "id_client": "CL1",
        "id_vehicule": "VH1",
        "id_contrat": "C1",
        "bonus": 0.5,
        "type_contrat": "Mini",
        "duree_contrat": 12,
        "anciennete_info": 3,
        "freq_paiement": "Monthly",
        "paiement": "Yes",
        "utilisation": "Professional",
        "code_postal": "75001",
        "conducteur2": "No",
        "age_conducteur1": 30,
        "age_conducteur2": 0,
        "sex_conducteur1": "M",
        "sex_conducteur2": "",
        "anciennete_permis1": 10,
        "anciennete_permis2": 0,
        "anciennete_vehicule": 2.0,
        "cylindre_vehicule": 1600,
        "din_vehicule": 120,
        "essence_vehicule": "Hybrid",
        "marque_vehicule": "TOYOTA",
        "modele_vehicule": "COROLLA",
        "debut_vente_vehicule": 10,
        "fin_vente_vehicule": 15,
        "vitesse_vehicule": 180,
        "type_vehicule": "Tourism",
        "prix_vehicule": 25000,
        "poids_vehicule": 1300,
        "nombre_sinistres": 0,
        "montant_sinistre": 0.0,
    }


@pytest.fixture
def client(monkeypatch):
    app = FastAPI()
    app.include_router(contrat_router)

    mock_service = MagicMock()

    monkeypatch.setattr(
        "src.api.backend.controllers.contrat_controller.contrat_service",
        mock_service,
    )

    return TestClient(app), mock_service


# ----------------------
# GET /contrats
# ----------------------
def test_get_recent_contrats_success(client):
    client, mock_service = client

    mock_service.list_recent.return_value = [
        {"id_contrat": "C1"},
        {"id_contrat": "C2"},
    ]

    response = client.get("/contrats")

    assert response.status_code == 200
    assert len(response.json()) == 2


def test_get_recent_contrats_error(client):
    client, mock_service = client

    mock_service.list_recent.side_effect = Exception("DB error")

    response = client.get("/contrats")

    assert response.status_code == 500
    assert "Erreur lecture contrats" in response.json()["detail"]


# ----------------------
# GET /contrats/{id}
# ----------------------
def test_get_contrat_success(client):
    client, mock_service = client

    mock_service.get_by_id_contrat.return_value = {"id_contrat": "C1"}

    response = client.get("/contrats/C1")

    assert response.status_code == 200
    assert response.json()["id_contrat"] == "C1"


def test_get_contrat_not_found(client):
    client, mock_service = client

    mock_service.get_by_id_contrat.return_value = None

    response = client.get("/contrats/C1")

    assert response.status_code == 404


def test_get_contrat_error(client):
    client, mock_service = client

    mock_service.get_by_id_contrat.side_effect = Exception("DB error")

    response = client.get("/contrats/C1")

    assert response.status_code == 500


# ----------------------
# POST /contrats
# ----------------------
def test_create_contrat_success(client, valid_payload):
    client, mock_service = client

    mock_service.create.return_value = valid_payload

    response = client.post("/contrats", json=valid_payload)

    assert response.status_code == 201
    assert response.json()["id_contrat"] == "C1"


def test_create_contrat_conflict(client, valid_payload):
    client, mock_service = client

    mock_service.create.side_effect = ValueError("Already exists")

    response = client.post("/contrats", json=valid_payload)

    assert response.status_code == 409


def test_create_contrat_error(client, valid_payload):
    client, mock_service = client

    mock_service.create.side_effect = Exception("DB error")

    response = client.post("/contrats", json=valid_payload)

    assert response.status_code == 500


# ----------------------
# PUT /contrats/{id}
# ----------------------
def test_update_contrat_success(client, valid_payload):
    client, mock_service = client

    mock_service.update.return_value = valid_payload

    response = client.put("/contrats/C1", json=valid_payload)

    assert response.status_code == 200
    assert response.json()["id_contrat"] == "C1"


def test_update_contrat_not_found(client, valid_payload):
    client, mock_service = client

    mock_service.update.side_effect = LookupError("Not found")

    response = client.put("/contrats/C1", json=valid_payload)

    assert response.status_code == 404


def test_update_contrat_conflict(client, valid_payload):
    client, mock_service = client

    mock_service.update.side_effect = ValueError("Conflict")

    response = client.put("/contrats/C1", json=valid_payload)

    assert response.status_code == 409


def test_update_contrat_error(client, valid_payload):
    client, mock_service = client

    mock_service.update.side_effect = Exception("DB error")

    response = client.put("/contrats/C1", json=valid_payload)

    assert response.status_code == 500


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))