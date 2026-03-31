import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import src.api.backend.model_runtime as model_runtime


def make_fake_path(exists: bool, path_value: str):
    fake_path = MagicMock()
    fake_path.exists.return_value = exists
    fake_path.__str__.return_value = path_value
    return fake_path


def test_load_frequence_model_success(monkeypatch):
    mock_model = MagicMock()
    mock_path = make_fake_path(True, "/tmp/model_frequence.json")
    mock_model.load_model.return_value = {"xgb_model_json": "ok"}

    monkeypatch.setattr(model_runtime, "Model_Prediction_Frequence", lambda: mock_model)
    monkeypatch.setattr(model_runtime, "MODEL_FREQUENCE_PATH", mock_path)

    model, error = model_runtime.load_frequence_model()

    assert model is mock_model
    assert error is None
    mock_model.load_model.assert_called_once_with(str(mock_path))


def test_load_frequence_model_missing_file(monkeypatch):
    mock_model = MagicMock()
    mock_path = make_fake_path(False, "/tmp/model_frequence.json")

    monkeypatch.setattr(model_runtime, "Model_Prediction_Frequence", lambda: mock_model)
    monkeypatch.setattr(model_runtime, "MODEL_FREQUENCE_PATH", mock_path)

    model, error = model_runtime.load_frequence_model()

    assert model is None
    assert "Model JSON introuvable" in error


def test_load_frequence_model_invalid_artifact(monkeypatch):
    mock_model = MagicMock()
    mock_path = make_fake_path(True, "/tmp/model_frequence.json")
    mock_model.load_model.return_value = {}

    monkeypatch.setattr(model_runtime, "Model_Prediction_Frequence", lambda: mock_model)
    monkeypatch.setattr(model_runtime, "MODEL_FREQUENCE_PATH", mock_path)

    model, error = model_runtime.load_frequence_model()

    assert model is None
    assert "artefact complet" in error


def test_load_frequence_model_returns_error_on_exception(monkeypatch):
    mock_model = MagicMock()
    mock_path = make_fake_path(True, "/tmp/model_frequence.json")
    mock_model.load_model.side_effect = RuntimeError("boom")

    monkeypatch.setattr(model_runtime, "Model_Prediction_Frequence", lambda: mock_model)
    monkeypatch.setattr(model_runtime, "MODEL_FREQUENCE_PATH", mock_path)

    model, error = model_runtime.load_frequence_model()

    assert model is None
    assert error == "Erreur chargement artefact frequence JSON: boom"


def test_load_severite_model_success(monkeypatch):
    mock_model = MagicMock()
    mock_path = make_fake_path(True, "/tmp/model_severite.json")
    mock_model.load_model.return_value = {"xgb_model_json": "ok"}

    monkeypatch.setattr(model_runtime, "Model_Prediction_Severite", lambda: mock_model)
    monkeypatch.setattr(model_runtime, "MODEL_SEVERITE_PATH", mock_path)

    model, error = model_runtime.load_severite_model()

    assert model is mock_model
    assert error is None
    mock_model.load_model.assert_called_once_with(str(mock_path))


def test_load_severite_model_missing_file(monkeypatch):
    mock_model = MagicMock()
    mock_path = make_fake_path(False, "/tmp/model_severite.json")

    monkeypatch.setattr(model_runtime, "Model_Prediction_Severite", lambda: mock_model)
    monkeypatch.setattr(model_runtime, "MODEL_SEVERITE_PATH", mock_path)

    model, error = model_runtime.load_severite_model()

    assert model is None
    assert "Model JSON introuvable" in error


def test_load_severite_model_invalid_artifact(monkeypatch):
    mock_model = MagicMock()
    mock_path = make_fake_path(True, "/tmp/model_severite.json")
    mock_model.load_model.return_value = {}

    monkeypatch.setattr(model_runtime, "Model_Prediction_Severite", lambda: mock_model)
    monkeypatch.setattr(model_runtime, "MODEL_SEVERITE_PATH", mock_path)

    model, error = model_runtime.load_severite_model()

    assert model is None
    assert "artefact complet" in error


def test_load_severite_model_returns_error_on_exception(monkeypatch):
    mock_model = MagicMock()
    mock_path = make_fake_path(True, "/tmp/model_severite.json")
    mock_model.load_model.side_effect = RuntimeError("boom")

    monkeypatch.setattr(model_runtime, "Model_Prediction_Severite", lambda: mock_model)
    monkeypatch.setattr(model_runtime, "MODEL_SEVERITE_PATH", mock_path)

    model, error = model_runtime.load_severite_model()

    assert model is None
    assert error == "Erreur chargement artefact severite JSON: boom"


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
