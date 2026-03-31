import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

ROOT = Path(__file__).resolve().parents[5]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import src.api.backend.services.contrat_ml_service as contrat_ml_service


@pytest.fixture
def sample_data():
    return {"age": 30, "bonus": 0.5, "sinistres": 2}


def test_init_loads_model_when_file_exists(monkeypatch):
    fake_model = MagicMock()
    monkeypatch.setattr(contrat_ml_service.os.path, "exists", lambda _: True)
    monkeypatch.setattr(contrat_ml_service.joblib, "load", lambda _: fake_model)

    service = contrat_ml_service.MLService()

    assert service.model is fake_model
    assert service.model_path == "model.pkl"


def test_init_sets_model_none_when_loading_fails(monkeypatch):
    monkeypatch.setattr(contrat_ml_service.os.path, "exists", lambda _: True)

    def raise_error(_):
        raise RuntimeError("load error")

    monkeypatch.setattr(contrat_ml_service.joblib, "load", raise_error)

    service = contrat_ml_service.MLService()

    assert service.model is None


def test_init_uses_naive_mode_when_file_missing(monkeypatch):
    monkeypatch.setattr(contrat_ml_service.os.path, "exists", lambda _: False)

    service = contrat_ml_service.MLService()

    assert service.model is None


def test_formule_naive_returns_expected_value(monkeypatch, sample_data):
    monkeypatch.setattr(contrat_ml_service.os.path, "exists", lambda _: False)
    service = contrat_ml_service.MLService()

    result = service.formule_naive(sample_data)

    assert result == 3000.0


def test_predict_uses_loaded_model(monkeypatch, sample_data):
    fake_model = MagicMock()
    fake_model.predict.return_value = [1234.5]

    monkeypatch.setattr(contrat_ml_service.os.path, "exists", lambda _: True)
    monkeypatch.setattr(contrat_ml_service.joblib, "load", lambda _: fake_model)

    service = contrat_ml_service.MLService()
    result = service.predict(sample_data)

    assert result == 1234.5
    fake_model.predict.assert_called_once_with([[30, 0.5, 2]])


def test_predict_falls_back_to_naive_formula(monkeypatch, sample_data):
    monkeypatch.setattr(contrat_ml_service.os.path, "exists", lambda _: False)
    service = contrat_ml_service.MLService()

    result = service.predict(sample_data)

    assert result == 3000.0


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
