import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[5]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.api.backend.repositories.contrat_repository import ContratRepository


@pytest.fixture
def sample_payload():
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


@pytest.fixture
def repo_with_table(tmp_path):
    db_path = tmp_path / "test_repository.sqlite"
    repo = ContratRepository(str(db_path))

    with repo._connect() as conn:
        conn.execute("""
            CREATE TABLE historique_contrats (
                id_client TEXT,
                id_vehicule TEXT,
                id_contrat TEXT,
                bonus REAL,
                type_contrat TEXT,
                duree_contrat INTEGER,
                anciennete_info INTEGER,
                freq_paiement TEXT,
                paiement TEXT,
                utilisation TEXT,
                code_postal TEXT,
                conducteur2 TEXT,
                age_conducteur1 INTEGER,
                age_conducteur2 INTEGER,
                sex_conducteur1 TEXT,
                sex_conducteur2 TEXT,
                anciennete_permis1 INTEGER,
                anciennete_permis2 INTEGER,
                anciennete_vehicule REAL,
                cylindre_vehicule INTEGER,
                din_vehicule INTEGER,
                essence_vehicule TEXT,
                marque_vehicule TEXT,
                modele_vehicule TEXT,
                debut_vente_vehicule INTEGER,
                fin_vente_vehicule INTEGER,
                vitesse_vehicule INTEGER,
                type_vehicule TEXT,
                prix_vehicule INTEGER,
                poids_vehicule INTEGER,
                nombre_sinistres INTEGER,
                montant_sinistre REAL
            )
            """)
        conn.commit()

    return repo


def test_table_exists_returns_true(repo_with_table):
    with repo_with_table._connect() as conn:
        assert repo_with_table._table_exists(conn) is True


def test_find_recent_returns_empty_list_when_table_missing(tmp_path):
    repo = ContratRepository(str(tmp_path / "missing_table.sqlite"))

    assert repo.find_recent() == []


def test_insert_and_find_by_id_contrat_roundtrip(repo_with_table, sample_payload):
    inserted = repo_with_table.insert(sample_payload)
    found = repo_with_table.find_by_id_contrat("C1")

    assert inserted["id_contrat"] == "C1"
    assert inserted["row_id"] >= 1
    assert found is not None
    assert found["id_client"] == sample_payload["id_client"]
    assert found["bonus"] == sample_payload["bonus"]


def test_find_recent_returns_rows_in_descending_order(repo_with_table, sample_payload):
    payload_1 = dict(sample_payload)
    payload_2 = dict(sample_payload)
    payload_2["id_contrat"] = "C2"
    payload_2["id_client"] = "CL2"

    repo_with_table.insert(payload_1)
    repo_with_table.insert(payload_2)

    rows = repo_with_table.find_recent(limit=2)

    assert len(rows) == 2
    assert rows[0]["id_contrat"] == "C2"
    assert rows[1]["id_contrat"] == "C1"


def test_insert_raises_when_table_missing(tmp_path, sample_payload):
    repo = ContratRepository(str(tmp_path / "missing_insert.sqlite"))

    with pytest.raises(RuntimeError) as exc_info:
        repo.insert(sample_payload)

    assert "Table historique_contrats introuvable" in str(exc_info.value)


def test_update_by_id_contrat_updates_existing_row(repo_with_table, sample_payload):
    repo_with_table.insert(sample_payload)
    updated_payload = dict(sample_payload)
    updated_payload["bonus"] = 0.9
    updated_payload["prix_vehicule"] = 30000

    updated = repo_with_table.update_by_id_contrat("C1", updated_payload)

    assert updated is not None
    assert updated["id_contrat"] == "C1"
    assert updated["bonus"] == 0.9
    assert updated["prix_vehicule"] == 30000


def test_update_by_id_contrat_returns_none_when_id_not_found(
    repo_with_table, sample_payload
):
    result = repo_with_table.update_by_id_contrat("UNKNOWN", sample_payload)

    assert result is None


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
