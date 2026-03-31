from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional, Tuple

from src.models.fonctions_utiles import Model_Prediction_Frequence, Model_Prediction_Severite


LOGGER = logging.getLogger(__name__)
BASE_DIR = Path(__file__).resolve().parents[3]
OUTPUT_MODELS_DIR = BASE_DIR / "output_models"
MODELS_DIR = OUTPUT_MODELS_DIR / "modeles"
MODEL_FREQUENCE_PATH = MODELS_DIR / "model_frequence.json"
MODEL_SEVERITE_PATH = MODELS_DIR / "model_severite.json"


def load_frequence_model() -> Tuple[Optional[Model_Prediction_Frequence], Optional[str]]:
    """
    Charge le modèle de prédiction de fréquence depuis un artefact JSON.

    Returns:
        Tuple[Optional[Model_Prediction_Frequence], Optional[str]]: 
            - Instance du modèle chargée si succès, sinon None
            - Message d'erreur ou None si succès
    """
    model = Model_Prediction_Frequence()

    if not MODEL_FREQUENCE_PATH.exists():
        return None, f"Model JSON introuvable: {MODEL_FREQUENCE_PATH}"

    try:
        loaded = model.load_model(str(MODEL_FREQUENCE_PATH))
        if not isinstance(loaded, dict) or not loaded.get("xgb_model_json"):
            return (
                None,
                "Le JSON de frequence charge n'est pas un artefact complet. Relancer l'entrainement.",
            )
        LOGGER.info("Modele frequence charge depuis %s", MODEL_FREQUENCE_PATH)
        return model, None
    except Exception as exc:  # pragma: no cover - defensive runtime guard
        LOGGER.exception("Erreur chargement artefact frequence JSON")
        return None, f"Erreur chargement artefact frequence JSON: {exc}"


def load_severite_model() -> Tuple[Optional[Model_Prediction_Severite], Optional[str]]:
    """
    Charge le modèle de prédiction de sévérité depuis un artefact JSON.

    Returns:
        Tuple[Optional[Model_Prediction_Severite], Optional[str]]: 
            - Instance du modèle chargée si succès, sinon None
            - Message d'erreur ou None si succès
    """
    model = Model_Prediction_Severite()

    if not MODEL_SEVERITE_PATH.exists():
        return None, f"Model JSON introuvable: {MODEL_SEVERITE_PATH}"

    try:
        loaded = model.load_model(str(MODEL_SEVERITE_PATH))
        if not isinstance(loaded, dict) or not loaded.get("xgb_model_json"):
            return (
                None,
                "Le JSON de severite charge n'est pas un artefact complet. Relancer l'entrainement.",
            )
        LOGGER.info("Modele severite charge depuis %s", MODEL_SEVERITE_PATH)
        return model, None
    except Exception as exc:  # pragma: no cover - defensive runtime guard
        LOGGER.exception("Erreur chargement artefact severite JSON")
        return None, f"Erreur chargement artefact severite JSON: {exc}"
