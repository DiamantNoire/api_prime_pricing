import csv


class ContratRepository:

    def __init__(self):
        # Chemin absolu vers ton fichier uploadé
        self.FILE_PATH = "api_prime_pricing/prod_api_rest/train.csv"

    def find_all(self):
        with open(self.FILE_PATH, mode="r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            return list(reader)

    def find_by_contrat(self, id_contrat: str):
        data = self.find_all()
        return [row for row in data if row["id_contrat"] == id_contrat]

    def find_by_type(self, type_contrat: str):
        data = self.find_all()
        return [row for row in data if row["type_contrat"] == type_contrat]