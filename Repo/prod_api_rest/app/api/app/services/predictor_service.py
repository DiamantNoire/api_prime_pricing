import importlib
import pickle
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List

import pandas as pd

from app.config import settings


@dataclass
class PredictionResult:
    frequence_probabilite: float
    severite_prediction: float
    prime_prediction: float


class PredictorService:
    def __init__(self) -> None:
        self.models_root = settings.models_root
        self.repo_root = settings.repo_root

        self._prepare_pickle_imports()

        from fonctions_utiles import Model_Prediction_Frequence, Model_Prediction_Severite

        self.model_frequence = Model_Prediction_Frequence()
        self.model_severite = Model_Prediction_Severite()

        self.feature_frequence = None
        self.feature_severite = None

    def _prepare_pickle_imports(self) -> None:
        # Les objets pickles references dans dev_build_models utilisent le module fonctions_utiles.
        dev_models_path = self.repo_root / "dev_build_models"
        if str(dev_models_path) not in sys.path:
            sys.path.insert(0, str(dev_models_path))
        importlib.import_module("fonctions_utiles")

    def _load_pickle(self, filepath: Path) -> Any:
        with filepath.open("rb") as file_handler:
            return pickle.load(file_handler)

    def load(self) -> None:
        model_dir = self.models_root / "modeles"
        fe_dir = self.models_root / "feature_engineering"

        model_frequence_path = model_dir / "model_frequence.pickle"
        model_severite_path = model_dir / "model_severite.pickle"
        fe_frequence_path = fe_dir / "features_frequence.pickle"
        fe_severite_path = fe_dir / "features_severite.pickle"

        required_files = [
            model_frequence_path,
            model_severite_path,
            fe_frequence_path,
            fe_severite_path,
        ]
        missing_files = [str(path) for path in required_files if not path.exists()]
        if missing_files:
            missing = "\n".join(missing_files)
            raise FileNotFoundError(f"Artefacts manquants:\n{missing}")

        self.model_frequence.load_model(str(model_frequence_path))
        self.model_severite.load_model(str(model_severite_path))

        self.feature_frequence = self._load_pickle(fe_frequence_path)
        self.feature_severite = self._load_pickle(fe_severite_path)

    def is_ready(self) -> bool:
        return self.feature_frequence is not None and self.feature_severite is not None

    def _predict_one(self, features: Dict[str, Any]) -> PredictionResult:
        input_df = pd.DataFrame([features])

        x_frequence = self.feature_frequence.transform(input_df)
        frequence_proba = self.model_frequence.predict_proba(x_frequence)
        if frequence_proba.shape[1] > 1:
            prob = float(frequence_proba[:, 1][0])
        else:
            prob = float(frequence_proba[:, 0][0])

        x_severite = self.feature_severite.transform(input_df)
        severite = float(self.model_severite.predict(x_severite)[0])
        severite = max(0.0, severite)

        prime = prob * severite

        return PredictionResult(
            frequence_probabilite=prob,
            severite_prediction=severite,
            prime_prediction=prime,
        )

    def predict(self, features: Dict[str, Any]) -> PredictionResult:
        if not self.is_ready():
            self.load()
        return self._predict_one(features)

    def predict_batch(self, batch_features: Iterable[Dict[str, Any]]) -> List[PredictionResult]:
        if not self.is_ready():
            self.load()
        return [self._predict_one(features) for features in batch_features]


predictor_service = PredictorService()
