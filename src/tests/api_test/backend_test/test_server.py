import runpy
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi import APIRouter
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import src.api.backend.server as server_module


@pytest.fixture
def client():
    return TestClient(server_module.app)


def _make_router_module() -> ModuleType:
    module = ModuleType("fake_router_module")
    module.router = APIRouter()
    return module


def test_app_metadata():
    assert server_module.app.title == "API Prime Pricing"
    assert server_module.app.version == "1.0.0"


def test_read_root_endpoint(client):
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {"message": "API Prime Pricing is running"}


def test_health_endpoint(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_favicon_endpoint(client):
    response = client.get("/favicon.ico")

    assert response.status_code == 204
    assert response.text == ""


def test_expected_routes_are_registered():
    paths = {route.path for route in server_module.app.routes}

    assert "/" in paths
    assert "/health" in paths
    assert "/favicon.ico" in paths
    assert "/predictio_frequence/health" in paths
    assert "/predictio_severite/health" in paths
    assert "/contrats" in paths
    assert "/contrats/{id_contrat}" in paths


def test_main_calls_uvicorn_run(monkeypatch):
    fake_run = MagicMock()
    fake_uvicorn = SimpleNamespace(run=fake_run)

    monkeypatch.setitem(sys.modules, "uvicorn", fake_uvicorn)
    monkeypatch.setitem(
        sys.modules,
        "src.api.backend.controllers.controller_severite",
        _make_router_module(),
    )
    monkeypatch.setitem(
        sys.modules,
        "src.api.backend.controllers.controller_frequence",
        _make_router_module(),
    )

    fake_contrat_module = ModuleType("fake_contrat_module")
    fake_contrat_module.contrat_router = APIRouter()
    monkeypatch.setitem(
        sys.modules,
        "src.api.backend.controllers.contrat_controller",
        fake_contrat_module,
    )

    runpy.run_path(str(ROOT / "src/api/backend/server.py"), run_name="__main__")

    fake_run.assert_called_once_with(
        "src.api.backend.server:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
    )


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
