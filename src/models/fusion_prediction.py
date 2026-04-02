# --*- coding: utf-8 -*-

# =============================================
# ------ IMPORTATIONS DES LIBRAIRIES ----------#
# =============================================
import os
import sys
import json
import pickle
import logging
from datetime import datetime
from typing import Any
import pandas as pd
import numpy as np

CURRENT_DIR = os.path.dirname(__file__)
if CURRENT_DIR not in sys.path:
    sys.path.append(CURRENT_DIR)

from fonctions_utiles import Data_Base_Creator

LOGGER = logging.getLogger(__name__)


def run_step(step_name: str, func, *args, **kwargs):
    """
    Exécute une étape du pipeline avec logs simples.

    Args:
        step_name (str): Nom de l'étape à logger.
        func (callable): Fonction à exécuter.
        *args: Arguments positionnels pour la fonction.
        **kwargs: Arguments nommés pour la fonction.

    Returns:
        Any: Résultat de la fonction exécutée.
    """
    LOGGER.info("[STEP] %s ...", step_name)
    result = func(*args, **kwargs)
    LOGGER.info("[OK] %s", step_name)
    return result


def _to_json_serializable(value: Any) -> Any:
    """
    Convertit récursivement un objet Python en type sérialisable JSON.

    Args:
        value (Any): Objet Python à convertir.

    Returns:
        Any: Objet converti en type compatible JSON.
    """
    if value is None or isinstance(value, (str, int, float, bool)):
        return value

    if isinstance(value, np.generic):
        return value.item()

    if isinstance(value, np.ndarray):
        return value.tolist()

    if isinstance(value, dict):
        return {str(key): _to_json_serializable(val) for key, val in value.items()}

    if isinstance(value, (list, tuple, set)):
        return [_to_json_serializable(item) for item in value]

    if hasattr(value, "get_params"):
        return {
            "__class__": value.__class__.__name__,
            "params": _to_json_serializable(value.get_params(deep=False)),
        }

    return str(value)


def _dump_pickle_to_json(pickle_path: str, json_path: str) -> None:
    """
    Charge un modèle pickle et exporte ses informations importantes en JSON.

    Args:
        pickle_path (str): Chemin du fichier pickle à charger.
        json_path (str): Chemin du fichier JSON de sortie.

    Returns:
        None
    """
    with open(pickle_path, "rb") as file_handler:
        artifact = pickle.load(file_handler)

    payload = {
        "source_pickle": pickle_path,
        "exported_at": datetime.utcnow().isoformat() + "Z",
        "artifact_python_type": type(artifact).__name__,
    }

    if isinstance(artifact, dict):
        payload["keys"] = list(artifact.keys())
        payload["model_name_"] = _to_json_serializable(artifact.get("model_name_"))
        payload["best_params_"] = _to_json_serializable(artifact.get("best_params_"))
        payload["best_score_"] = _to_json_serializable(artifact.get("best_score_"))
        payload["selected_features_"] = _to_json_serializable(
            artifact.get("selected_features_")
        )
        payload["fill_values_"] = _to_json_serializable(artifact.get("fill_values_"))
        payload["history_"] = _to_json_serializable(artifact.get("history_"))
        payload["metadata"] = _to_json_serializable(artifact.get("metadata"))

        # On exporte aussi la config de pipeline pour audit/rejeu.
        if "pipeline_" in artifact:
            payload["pipeline_"] = _to_json_serializable(artifact.get("pipeline_"))
        if "best_estimator_" in artifact:
            payload["best_estimator_"] = _to_json_serializable(
                artifact.get("best_estimator_")
            )
    else:
        payload["content"] = _to_json_serializable(artifact)

    with open(json_path, "w", encoding="utf-8") as file_handler:
        json.dump(payload, file_handler, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))

    # =============================================
    # -------- CHARGEMENT DES DONNEES -------------#
    # =============================================
    DATA_DIR = os.path.dirname(__file__)
    PROJECT_ROOT = os.path.abspath(os.path.join(DATA_DIR, "..", ".."))

    FREQ_PRED_PATH = os.path.join(
        PROJECT_ROOT, "output_models", "predictions", "test_predictions_frequence.csv"
    )
    AMOUNT_PRED_PATH = os.path.join(
        PROJECT_ROOT, "output_models", "predictions", "test_predictions_severite.csv"
    )

    # --- Input ---
    MODEL_FREQUENCE_PATH = os.path.join(
        PROJECT_ROOT, "output_models", "modeles", "model_frequence.pickle"
    )
    MODEL_SEVERITE_PATH = os.path.join(
        PROJECT_ROOT, "output_models", "modeles", "model_severite.pickle"
    )
    os.makedirs(os.path.dirname(MODEL_FREQUENCE_PATH), exist_ok=True)
    os.makedirs(os.path.dirname(MODEL_SEVERITE_PATH), exist_ok=True)

    # --- Output ---
    SAVE_MODEL_FREQUENCE_PATH = os.path.join(
        PROJECT_ROOT, "output_models", "modeles", "model_frequence.json"
    )
    SAVE_MODEL_SEVERITE_PATH = os.path.join(
        PROJECT_ROOT, "output_models", "modeles", "model_severite.json"
    )
    os.makedirs(os.path.dirname(SAVE_MODEL_FREQUENCE_PATH), exist_ok=True)
    os.makedirs(os.path.dirname(SAVE_MODEL_SEVERITE_PATH), exist_ok=True)

    # =======================================================
    # -------- DEFINITION DES CHEMINS DE SORTIE -------------#
    # =======================================================
    PRIME_PREDICT_PATH = os.path.join(
        PROJECT_ROOT, "output_models", "predictions", "test_prime.csv"
    )

    # =======================================================
    # ------ PIPELINE FINAL PRIME PREDICTION -----------------#
    # =======================================================

    # =======================================================
    # ------ PIPELINE FINAL PRIME PREDICTION -----------------#
    # =======================================================
    freq_df = run_step("Chargement freq_pred.csv", pd.read_csv, FREQ_PRED_PATH)
    freq_df_copie = run_step(
        "Copie Freq pour traitement", lambda df: df.copy(), freq_df
    )

    amount_df = run_step("Chargement amount_pred.csv", pd.read_csv, AMOUNT_PRED_PATH)
    amount_df_copie = run_step(
        "Copie Amount pour traitement", lambda df: df.copy(), amount_df
    )
    # Sauvegarde de la prédiction finale
    submission_df = pd.DataFrame(
        {
            "index": amount_df_copie["index"],
            "pred": amount_df_copie["pred"] * freq_df["pred"],
        }
    )
    submission_df.to_csv(os.path.join(DATA_DIR, PRIME_PREDICT_PATH), index=False)

    # Export des modèles pickle vers JSON (version sérialisable pour inspection/API).
    run_step(
        "Dump model_frequence.pickle -> model_frequence.json",
        _dump_pickle_to_json,
        MODEL_FREQUENCE_PATH,
        SAVE_MODEL_FREQUENCE_PATH,
    )

    run_step(
        "Dump model_severite.pickle -> model_severite.json",
        _dump_pickle_to_json,
        MODEL_SEVERITE_PATH,
        SAVE_MODEL_SEVERITE_PATH,
    )

    # =======================================================
    # ------ BUILD DATABASE FOR PRIME PREDICTION-------------#
    # =======================================================
    TRAIN_CSV_PATH = os.path.join(PROJECT_ROOT, "asset", "train.csv")
    TEST_CSV_PATH = os.path.join(PROJECT_ROOT, "asset", "test.csv")
    PRED_FREQ_PATH = FREQ_PRED_PATH
    PRED_SEV_PATH = AMOUNT_PRED_PATH
    PRED_PRIME_PATH = PRIME_PREDICT_PATH
    DB_PATH = os.path.join(PROJECT_ROOT, "db", "prime_pricing.sqlite")

    db = Data_Base_Creator(db_path=DB_PATH)

    run_step("Initialisation base SQLite", db.create_database)

    run_step(
        "Création table historique_contrats (train.csv)",
        db.create_table_historique_contrats,
        TRAIN_CSV_PATH,
    )

    run_step(
        "Création table test_contrats (test.csv)",
        db.create_table_test_contrats,
        TEST_CSV_PATH,
    )

    run_step(
        "Création table predictions (freq + sev + prime)",
        db.create_table_predictions,
        PRED_FREQ_PATH,
        PRED_SEV_PATH,
        PRED_PRIME_PATH,
    )
