import importlib.util
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pandas as pd
import requests
import streamlit as st

PAGE_PATH = Path(__file__).resolve().parents[4] / "api/frontend/pages/1_contrats.py"


def load_1_contrats_page(monkeypatch, mode_value, text_input_value="", response_json=None):
    """Charge le module 1_contrats avec les valeurs stub pour st et requests."""
    monkeypatch.setattr(st, "title", MagicMock())
    monkeypatch.setattr(st, "radio", MagicMock(return_value=mode_value))
    monkeypatch.setattr(st, "text_input", MagicMock(return_value=text_input_value))

    dataframe_mock = MagicMock()
    monkeypatch.setattr(st, "dataframe", dataframe_mock)

    response_mock = MagicMock()
    response_mock.json.return_value = response_json if response_json is not None else []
    requests_get_mock = MagicMock(return_value=response_mock)
    monkeypatch.setattr(requests, "get", requests_get_mock)

    module_name = f"test_1_contrats_{mode_value.replace(' ', '_').replace('/', '_')}"
    if module_name in sys.modules:
        sys.modules.pop(module_name)

    spec = importlib.util.spec_from_file_location(module_name, PAGE_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)

    return requests_get_mock, dataframe_mock, module


def test_tous_les_contrats_appelle_api_contrats(monkeypatch):
    data = [{"numero": "C-001", "type": "Standard"}]

    requests_get_mock, dataframe_mock, _ = load_1_contrats_page(
        monkeypatch,
        mode_value="Tous les contrats",
        response_json=data,
    )

    requests_get_mock.assert_called_once_with("http://127.0.0.1:8000/contrats")
    dataframe_mock.assert_called_once()
    df_arg = dataframe_mock.call_args[0][0]
    assert isinstance(df_arg, pd.DataFrame)
    assert df_arg.to_dict(orient="records") == data


def test_par_numero_contrat_appelle_api_numero(monkeypatch):
    data = [{"numero": "C-123", "type": "Premium"}]

    requests_get_mock, dataframe_mock, _ = load_1_contrats_page(
        monkeypatch,
        mode_value="Par numéro de contrat",
        text_input_value="C-123",
        response_json=data,
    )

    requests_get_mock.assert_called_once_with("http://127.0.0.1:8000/contrats/C-123")
    dataframe_mock.assert_called_once()
    assert dataframe_mock.call_args[0][0].to_dict(orient="records") == data


def test_par_type_contrat_appelle_api_type(monkeypatch):
    data = [{"numero": "C-456", "type": "Standard"}]

    requests_get_mock, dataframe_mock, _ = load_1_contrats_page(
        monkeypatch,
        mode_value="Par type de contrat",
        text_input_value="Standard",
        response_json=data,
    )

    requests_get_mock.assert_called_once_with("http://127.0.0.1:8000/contrats/type/Standard")
    dataframe_mock.assert_called_once()
    assert dataframe_mock.call_args[0][0].to_dict(orient="records") == data


def test_par_numero_contrat_pas_de_parametre_pas_dappel_api(monkeypatch):
    requests_get_mock, dataframe_mock, _ = load_1_contrats_page(
        monkeypatch,
        mode_value="Par numéro de contrat",
        text_input_value="",
    )

    requests_get_mock.assert_not_called()
    dataframe_mock.assert_not_called()
