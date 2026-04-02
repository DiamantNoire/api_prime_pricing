import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

ROOT = Path(__file__).resolve().parents[5]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.api.backend.dto.contrat_dto import ContratCreateDTO, ContratUpdateDTO
from src.api.backend.services.contrat_service import ContratService


@pytest.fixture
def repository_mock():
    return MagicMock()


@pytest.fixture
def service(repository_mock):
    return ContratService(repository=repository_mock)


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
        "age_conducteur2": 22,
        "sex_conducteur1": "M",
        "sex_conducteur2": "F",
        "anciennete_permis1": 10,
        "anciennete_permis2": 2,
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


def test_normalize_payload_resets_second_driver_fields_when_no_second_driver(
    valid_payload,
):
    normalized = ContratService._normalize_payload(valid_payload)

    assert normalized["age_conducteur2"] == 0
    assert normalized["sex_conducteur2"] == ""
    assert normalized["anciennete_permis2"] == 0


def test_list_recent_delegates_to_repository(service, repository_mock):
    repository_mock.find_recent.return_value = [{"id_contrat": "C1"}]

    result = service.list_recent(limit=5)

    assert result == [{"id_contrat": "C1"}]
    repository_mock.find_recent.assert_called_once_with(limit=5)


def test_get_by_id_contrat_delegates_to_repository(service, repository_mock):
    repository_mock.find_by_id_contrat.return_value = {"id_contrat": "C1"}

    result = service.get_by_id_contrat("C1")

    assert result == {"id_contrat": "C1"}
    repository_mock.find_by_id_contrat.assert_called_once_with("C1")


def test_create_inserts_normalized_payload(service, repository_mock, valid_payload):
    dto = ContratCreateDTO(**valid_payload)
    repository_mock.find_by_id_contrat.return_value = None
    repository_mock.insert.return_value = {"id_contrat": "C1", "age_conducteur2": 0}

    result = service.create(dto)

    assert result["id_contrat"] == "C1"
    inserted_payload = repository_mock.insert.call_args.args[0]
    assert inserted_payload["age_conducteur2"] == 0
    assert inserted_payload["sex_conducteur2"] == ""
    assert inserted_payload["anciennete_permis2"] == 0


def test_create_raises_when_contract_already_exists(
    service, repository_mock, valid_payload
):
    dto = ContratCreateDTO(**valid_payload)
    repository_mock.find_by_id_contrat.return_value = {"id_contrat": "C1"}

    with pytest.raises(ValueError) as exc_info:
        service.create(dto)

    assert "existe déjà" in str(exc_info.value)
    repository_mock.insert.assert_not_called()


def test_update_raises_when_contract_not_found(service, repository_mock, valid_payload):
    dto = ContratUpdateDTO(**valid_payload)
    repository_mock.find_by_id_contrat.return_value = None

    with pytest.raises(LookupError) as exc_info:
        service.update("C1", dto)

    assert "introuvable" in str(exc_info.value)
    repository_mock.update_by_id_contrat.assert_not_called()


def test_update_returns_updated_contract(service, repository_mock, valid_payload):
    dto = ContratUpdateDTO(**valid_payload)
    repository_mock.find_by_id_contrat.return_value = {"id_contrat": "C1"}
    repository_mock.update_by_id_contrat.return_value = {
        "id_contrat": "C1",
        "bonus": 0.5,
    }

    result = service.update("C1", dto)

    assert result == {"id_contrat": "C1", "bonus": 0.5}
    repository_mock.update_by_id_contrat.assert_called_once()
    called_id, called_payload = repository_mock.update_by_id_contrat.call_args.args
    assert called_id == "C1"
    assert called_payload["id_contrat"] == "C1"
    assert called_payload["age_conducteur2"] == 0


def test_update_raises_when_repository_returns_none(
    service, repository_mock, valid_payload
):
    dto = ContratUpdateDTO(**valid_payload)
    repository_mock.find_by_id_contrat.return_value = {"id_contrat": "C1"}
    repository_mock.update_by_id_contrat.return_value = None

    with pytest.raises(LookupError) as exc_info:
        service.update("C1", dto)

    assert "introuvable après mise à jour" in str(exc_info.value)


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
