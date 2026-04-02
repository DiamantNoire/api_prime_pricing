import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

ROOT = Path(__file__).resolve().parents[5]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.api.backend.dto.contrat_dto import (
    ContratCreateDTO,
    ContratReadDTO,
    ContratResponseDTO,
    ContratUpdateDTO,
)


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


def test_contrat_create_dto_accepts_valid_payload(valid_payload):
    dto = ContratCreateDTO(**valid_payload)

    assert dto.id_contrat == "C1"
    assert dto.code_postal == "75001"
    assert dto.nombre_sinistres == 0


def test_contrat_update_dto_rejects_invalid_postal_code(valid_payload):
    invalid_payload = dict(valid_payload)
    invalid_payload["code_postal"] = "75A01"

    with pytest.raises(ValidationError) as exc_info:
        ContratUpdateDTO(**invalid_payload)

    assert "code_postal" in str(exc_info.value)


def test_contrat_create_dto_rejects_incoherent_permis1(valid_payload):
    invalid_payload = dict(valid_payload)
    invalid_payload["age_conducteur1"] = 20
    invalid_payload["anciennete_permis1"] = 10

    with pytest.raises(ValidationError) as exc_info:
        ContratCreateDTO(**invalid_payload)

    assert "anciennete_permis1 incohérente avec age_conducteur1" in str(exc_info.value)


def test_contrat_create_dto_rejects_incoherent_permis2(valid_payload):
    invalid_payload = dict(valid_payload)
    invalid_payload["conducteur2"] = "Yes"
    invalid_payload["age_conducteur2"] = 18
    invalid_payload["sex_conducteur2"] = "F"
    invalid_payload["anciennete_permis2"] = 5

    with pytest.raises(ValidationError) as exc_info:
        ContratCreateDTO(**invalid_payload)

    assert "anciennete_permis2 incohérente avec age_conducteur2" in str(exc_info.value)


def test_contrat_response_dto_accepts_index(valid_payload):
    dto = ContratResponseDTO(index=7, **valid_payload)

    assert dto.index == 7
    assert dto.id_client == "CL1"


def test_contrat_read_dto_is_tolerant_with_partial_data():
    dto = ContratReadDTO(id_contrat="C1", bonus=0.42)

    assert dto.id_contrat == "C1"
    assert dto.bonus == 0.42
    assert dto.id_client is None


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
