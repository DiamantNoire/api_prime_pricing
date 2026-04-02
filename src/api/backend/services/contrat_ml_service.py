import joblib
import os

class MLService:
    """
    Service de prédiction de prime d'assurance via un modèle ML ou une formule naïve fallback.
    """

    def __init__(self):
        """
        Initialise le service ML. Tente de charger un modèle joblib si présent, sinon utilise la formule naïve.
        """
        self.model = None
        self.model_path = "model.pkl"

        # Vérifie si le modèle existe avant de le charger
        if os.path.exists(self.model_path):
            try:
                self.model = joblib.load(self.model_path)
                print("Modèle chargé avec succès.")
            except Exception as e:
                print(f"Erreur lors du chargement du modèle : {e}")
                self.model = None
        else:
            print(f" Utilisation du modèle naif")

    def formule_naive(self, data: dict) -> float:
        """
        Calcule la prime d'assurance selon une formule naïve :
        prime = age * bonus * (1 + sinistres)

        Args:
            data (dict): Dictionnaire contenant les clés 'age', 'bonus', 'sinistres'.

        Returns:
            float: Prime calculée selon la formule naïve.
        """
        base_price = 100
        age_factor = data["age"] / 100
        bonus_factor = data["bonus"] * 100
        sinistres_factor = 1 + data["sinistres"] * 0.5

        return base_price * age_factor * bonus_factor * sinistres_factor

    def predict(self, data: dict) -> float:
        """
        Prédit la prime d'assurance à partir des données fournies.
        Utilise le modèle ML si chargé, sinon la formule naïve.

        Args:
            data (dict): Dictionnaire contenant les clés 'age', 'bonus', 'sinistres'.

        Returns:
            float: Prime prédite.
        """
        # Si le modèle est chargé
        if self.model is not None:
            features = [
                data["age"],
                data["bonus"],
                data["sinistres"]
            ]
            prediction = self.model.predict([features])
            return float(prediction[0])
        # Sinon, utilise la formule naïve
        else:
            return self.formule_naive(data)