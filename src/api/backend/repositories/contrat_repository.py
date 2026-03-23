import csv
import logging
from pathlib import Path

LOGGER = logging.getLogger(__name__)


class ContratRepository:

    def __init__(self):
        base_dir = Path(__file__).resolve().parents[4]
        self.file_path = base_dir / "asset" / "train.csv"

    def find_all(self):
        LOGGER.info("Lecture des contrats depuis %s", self.file_path)
        with self.file_path.open(mode="r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            return list(reader)

    def find_by_contrat(self, id_contrat: str):
        data = self.find_all()
        LOGGER.info("Filtrage contrat par id=%s", id_contrat)
        return [row for row in data if row["id_contrat"] == id_contrat]

    def find_by_type(self, type_contrat: str):
        data = self.find_all()
        LOGGER.info("Filtrage contrats par type=%s", type_contrat)
        return [row for row in data if row["type_contrat"] == type_contrat]