
import joblib
import os
from src.api.backend.log_api.logger import get_logger


logger = get_logger(__name__)

class MLService:

    def __init__(self):
        self.model = None
        self.model_path = "model.pkl"

        # verifie si le modèle existe avant de le charger
        if os.path.exists(self.model_path):
            try:
                self.model = joblib.load(self.model_path)
                print("Modèle chargé avec succès.")
            except Exception as e:
                print(f"Erreur lors du chargement du modèle : {e}")
                self.model = None
        else:
            print(f" Utilisation du modèle naif")

    def formule_naive(self, data: dict):
        try:
            base_price = 100
            age_factor = data["age"] / 100
            bonus_factor = data["bonus"]*100
            sinistres_factor = 1 + data["sinistres"] * 0.5
            return base_price * age_factor * bonus_factor * sinistres_factor
        except Exception as e:
            logger.exception("Erreur dans formule_naive")
            raise

    def predict(self, data: dict):
        try:
            if self.model is not None:
                features = [
                    data["age"],
                    data["bonus"],
                    data["sinistres"]
                ]
                prediction = self.model.predict([features])
                return float(prediction[0])
            else:
                return self.formule_naive(data)
        except Exception as e:
            logger.exception("Erreur dans predict")
            raise