import importlib.util
import sys
from pathlib import Path
from unittest.mock import MagicMock

import requests
import streamlit as st

PAGE_PATH = Path(__file__).resolve().parents[4] / "api/frontend/pages/2_inference.py"


def load_2_inference_page(monkeypatch, age_value=18, bonus_value=0.0, sinistres_value=0, button_value=False, response_json=None):
    monkeypatch.setattr(st, "title", MagicMock())
    monkeypatch.setattr(st, "number_input", MagicMock(side_effect=[age_value, bonus_value, sinistres_value]))
    monkeypatch.setattr(st, "button", MagicMock(return_value=button_value))
    success_mock = MagicMock()
    monkeypatch.setattr(st, "success", success_mock)

    response_mock = MagicMock()
    response_mock.json.return_value = response_json if response_json is not None else {}
    requests_post_mock = MagicMock(return_value=response_mock)
    monkeypatch.setattr(requests, "post", requests_post_mock)

    module_name = f"test_2_inference_{age_value}_{bonus_value}_{sinistres_value}_{button_value}"
    if module_name in sys.modules:
        sys.modules.pop(module_name)

    spec = importlib.util.spec_from_file_location(module_name, PAGE_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)

    return requests_post_mock, success_mock, module


def test_prediction_clique_appelle_api_et_affiche_resultat(monkeypatch):
    test_data = {"prediction": 256.75}

    requests_post_mock, success_mock, _ = load_2_inference_page(
        monkeypatch,
        age_value=35,
        bonus_value=0.8,
        sinistres_value=2,
        button_value=True,
        response_json=test_data,
    )

    requests_post_mock.assert_called_once_with(
        "http://127.0.0.1:8000/predict",
        json={"age": 35, "bonus": 0.8, "sinistres": 2},
    )
    success_mock.assert_called_once_with("Prime estimée : 256.75 €")


def test_prediction_non_clique_pas_dappel_api(monkeypatch):
    requests_post_mock, success_mock, _ = load_2_inference_page(
        monkeypatch,
        age_value=45,
        bonus_value=0.5,
        sinistres_value=1,
        button_value=False,
    )

    requests_post_mock.assert_not_called()
    success_mock.assert_not_called()
