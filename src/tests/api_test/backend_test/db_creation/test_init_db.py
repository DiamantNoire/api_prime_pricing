import runpy
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

ROOT = Path(__file__).resolve().parents[5]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import src.api.backend.db_creation.init_db as init_db_module
import src.models.fonctions_utiles as fonctions_utiles


def test_init_db_calls_create_database(monkeypatch):
    mock_db = MagicMock()
    monkeypatch.setattr(init_db_module, "Data_Base_Creator", lambda: mock_db)

    init_db_module.init_db()

    mock_db.create_database.assert_called_once_with()


def test_fill_historique_calls_create_table(monkeypatch):
    mock_db = MagicMock()
    monkeypatch.setattr(init_db_module, "Data_Base_Creator", lambda: mock_db)

    init_db_module.fill_historique()

    mock_db.create_table_historique_contrats.assert_called_once_with("asset/train.csv")


def test_fill_predictions_calls_create_table_predictions(monkeypatch):
    mock_db = MagicMock()
    monkeypatch.setattr(init_db_module, "Data_Base_Creator", lambda: mock_db)

    init_db_module.fill_predictions()

    mock_db.create_table_predictions.assert_called_once_with(
        "output_models/predictions/test_predictions_frequence.csv",
        "output_models/predictions/test_predictions_severite.csv",
        "output_models/predictions/test_prime.csv",
    )


def test_run_api_calls_uvicorn_run(monkeypatch):
    fake_run = MagicMock()
    fake_uvicorn = SimpleNamespace(run=fake_run)
    monkeypatch.setitem(sys.modules, "uvicorn", fake_uvicorn)

    init_db_module.run_api()

    fake_run.assert_called_once_with(
        "src.api.backend.server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )


def test_main_prints_usage_for_invalid_action(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["main.py", "invalid_action"])

    runpy.run_module("src.api.backend.db_creation.init_db", run_name="__main__")

    captured = capsys.readouterr()
    assert "Usage: python main.py" in captured.out


def test_main_executes_selected_action(monkeypatch):
    mock_db = MagicMock()
    monkeypatch.setattr(fonctions_utiles, "Data_Base_Creator", lambda: mock_db)
    monkeypatch.setattr(sys, "argv", ["main.py", "fill_historique"])

    runpy.run_module("src.api.backend.db_creation.init_db", run_name="__main__")

    mock_db.create_table_historique_contrats.assert_called_once_with("asset/train.csv")


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
