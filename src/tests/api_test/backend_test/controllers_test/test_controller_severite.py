import sys
from pathlib import Path
from unittest.mock import MagicMock

import pandas as pd
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[5]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import src.api.backend.controllers.controller_severite as controller_severite


@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(controller_severite.router)
    return TestClient(app)


@pytest.fixture
def valid_payload():
    return {
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
        "debut_vente_vehicule": 2020,
        "fin_vente_vehicule": 2024,
        "vitesse_vehicule": 180,
        "type_vehicule": "Tourism",
        "prix_vehicule": 25000,
        "poids_vehicule": 1300,
    }


def test_build_severite_model_success(monkeypatch):
    mock_model = MagicMock()
    mock_model.load_model.return_value = {"xgb_model_json": "ok"}

    monkeypatch.setattr(
        controller_severite, "Model_Prediction_Severite", lambda: mock_model
    )
    monkeypatch.setattr(controller_severite.os.path, "exists", lambda _: True)

    result = controller_severite._build_severite_model()

    assert result is mock_model
    mock_model.load_model.assert_called_once_with(
        controller_severite.MODEL_SEVERITE_PATH
    )


def test_build_severite_model_missing_file(monkeypatch):
    mock_model = MagicMock()

    monkeypatch.setattr(
        controller_severite, "Model_Prediction_Severite", lambda: mock_model
    )
    monkeypatch.setattr(controller_severite.os.path, "exists", lambda _: False)

    with pytest.raises(controller_severite.HTTPException) as exc_info:
        controller_severite._build_severite_model()

    assert exc_info.value.status_code == 500
    assert "Model JSON introuvable" in exc_info.value.detail


def test_build_severite_model_invalid_artifact(monkeypatch):
    mock_model = MagicMock()
    mock_model.load_model.return_value = {}

    monkeypatch.setattr(
        controller_severite, "Model_Prediction_Severite", lambda: mock_model
    )
    monkeypatch.setattr(controller_severite.os.path, "exists", lambda _: True)

    with pytest.raises(controller_severite.HTTPException) as exc_info:
        controller_severite._build_severite_model()

    assert exc_info.value.status_code == 500
    assert "artefact complet" in exc_info.value.detail


def test_health_predictio_severite_ok(client, monkeypatch):
    monkeypatch.setattr(controller_severite, "SEVERITE_MODEL", MagicMock())
    monkeypatch.setattr(controller_severite, "SEVERITE_MODEL_LOAD_ERROR", None)
    monkeypatch.setattr(controller_severite.os.path, "exists", lambda _: True)

    response = client.get("/predictio_severite/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["model_loaded"] is True
    assert response.json()["model_file_exists"] is True


def test_health_predictio_severite_error(client, monkeypatch):
    monkeypatch.setattr(controller_severite, "SEVERITE_MODEL", None)
    monkeypatch.setattr(
        controller_severite, "SEVERITE_MODEL_LOAD_ERROR", "modèle absent"
    )
    monkeypatch.setattr(controller_severite.os.path, "exists", lambda _: False)

    response = client.get("/predictio_severite/health")

    assert response.status_code == 200
    assert response.json()["status"] == "error"
    assert response.json()["model_loaded"] is False
    assert response.json()["detail"] == "modèle absent"


def test_prediction_success(client, valid_payload, monkeypatch):
    mock_model = MagicMock()
    mock_model.predict.return_value = [1234.56]

    monkeypatch.setattr(controller_severite, "SEVERITE_MODEL", mock_model)
    monkeypatch.setattr(controller_severite, "SEVERITE_MODEL_LOAD_ERROR", None)

    response = client.post("/predict_severite", json=valid_payload)

    assert response.status_code == 200
    assert response.json() == {"prediction": 1234.56}

    sent_df = mock_model.predict.call_args.args[0]
    assert isinstance(sent_df, pd.DataFrame)
    assert sent_df.iloc[0].to_dict() == valid_payload


def test_prediction_model_unavailable(client, valid_payload, monkeypatch):
    monkeypatch.setattr(controller_severite, "SEVERITE_MODEL", None)
    monkeypatch.setattr(
        controller_severite, "SEVERITE_MODEL_LOAD_ERROR", "chargement impossible"
    )

    response = client.post("/predict_severite", json=valid_payload)

    assert response.status_code == 500
    assert "Le modèle de sévérité n'est pas disponible" in response.json()["detail"]
    assert "chargement impossible" in response.json()["detail"]


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
