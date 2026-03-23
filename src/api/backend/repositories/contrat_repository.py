import csv
from pathlib import Path


class ContratRepository:

    def __init__(self):
        base_dir = Path(__file__).resolve().parents[4]
        self.file_path = base_dir / "asset" / "train.csv"

    def find_all(self):
        with self.file_path.open(mode="r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            return list(reader)

    def find_by_contrat(self, id_contrat: str):
        data = self.find_all()
        return [row for row in data if row["id_contrat"] == id_contrat]

    def find_by_type(self, type_contrat: str):
        data = self.find_all()
        return [row for row in data if row["type_contrat"] == type_contrat]