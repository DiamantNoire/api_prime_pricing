import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[5]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.api.backend.controllers.contrat_ml_controller import ml_router


@pytest.fixture
def client(monkeypatch):
    app = FastAPI()
    app.include_router(ml_router)

    mock_service = MagicMock()
    monkeypatch.setattr(
        "src.api.backend.controllers.contrat_ml_controller.ml_service",
        mock_service,
    )

    return TestClient(app), mock_service


def test_predict_success(client):
    client, mock_service = client
    payload = {"age": 30, "bonus": 0.5, "sinistres": 1}

    mock_service.predict.return_value = 2250.0

    response = client.post("/predict", json=payload)

    assert response.status_code == 200
    assert response.json() == {"prediction": 2250.0}
    mock_service.predict.assert_called_once_with(payload)


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
