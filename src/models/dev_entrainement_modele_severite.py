# --*- coding: utf-8 -*-

# =============================================
# ------ IMPORTATIONS DES LIBRAIRIES ----------#
# =============================================
import os
import sys
import logging
import pandas as pd
from sklearn.model_selection import train_test_split

LOGGER = logging.getLogger(__name__)


# =============================================
# ------ IMPORTATIONS DES MODULES -------------#
# =============================================

CURRENT_DIR = os.path.dirname(__file__)
if CURRENT_DIR not in sys.path:
    sys.path.append(CURRENT_DIR)

from fonctions_utiles import (
    run_step,
    _generer_csv_pred_severite,
    Severite_Preprocessing,
    Severite_Feature_Engineer,
    Model_Prediction_Severite,
)

# Les fonctions utilitaires importées sont documentées dans leur module d'origine.
# Ce script orchestre l'entraînement du modèle de sévérité,
# la sauvegarde des artefacts et l'export des prédictions.

# Aucun ajout de fonction locale à documenter ici, mais on ajoute une docstring de module.

"""
Script principal pour l'entraînement du modèle de prédiction de la sévérité.

Étapes principales :
    - Chargement et préparation des données d'entraînement et de test
    - Prétraitement et feature engineering
    - Entraînement, tuning et évaluation du modèle
    - Prédiction sur les jeux de données
    - Sauvegarde des artefacts (modèle, features, métriques, artefacts JSON)
    - Export des prédictions test au format CSV

Ce script ne définit pas de fonctions ou classes supplémentaires,
mais orchestre l'ensemble du pipeline via les fonctions importées.
"""

if __name__ == "__main__":
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
    LOGGER.info("Demarrage entrainement modele severite")

    # =============================================
    # -------- CHARGEMENT DES DONNEES -------------#
    # =============================================
    # --- Chemin ---
    DATA_DIR = os.path.dirname(__file__)
    PROJECT_ROOT = os.path.abspath(os.path.join(DATA_DIR, "..", ".."))

    # --- Input ---
    TRAIN_PATH = os.path.join(PROJECT_ROOT, "asset", "train.csv")
    TEST_PATH = os.path.join(PROJECT_ROOT, "asset", "test.csv")

    # --- Output ---
    OUTPUT_FEATURE_ENGINEERING_SEVERITE_PATH = os.path.join(
        DATA_DIR, "output/feature_engineering/features_severite.pickle"
    )
    OUTPUT_MODEL_SEVERITE_PATH = os.path.join(
        DATA_DIR, "output/modeles/model_severite.pickle"
    )
    OUTPUT_TEST_SEVERITE_PATH = os.path.join(
        DATA_DIR, "output/predictions/test_predictions_severite.csv"
    )
    OUTPUT_METRICS_SEVERITE_PATH = os.path.join(
        DATA_DIR, "output/metrics/metrics_severite.json"
    )
    OUTPUT_PIPELINE_SEVERITE_ARTIFACT_PATH = os.path.join(
        DATA_DIR, "output/pipeline/pipeline_severite.pickle"
    )
    OUTPUT_PIPELINE_SEVERITE_JSON_PATH = os.path.join(
        PROJECT_ROOT, "output_models", "modeles", "model_severite.json"
    )
    OUTPUT_COMPLETE_ARTIFACT_SEVERITE_PATH = OUTPUT_PIPELINE_SEVERITE_JSON_PATH
    OUTPUT_SYNTHETIC_ARTIFACT_SEVERITE_PATH = os.path.join(
        DATA_DIR, "output/artifacts/synthetic_artifact_severite.json"
    )

    os.makedirs(
        os.path.dirname(OUTPUT_FEATURE_ENGINEERING_SEVERITE_PATH), exist_ok=True
    )
    os.makedirs(os.path.dirname(OUTPUT_MODEL_SEVERITE_PATH), exist_ok=True)
    os.makedirs(os.path.dirname(OUTPUT_TEST_SEVERITE_PATH), exist_ok=True)
    os.makedirs(os.path.dirname(OUTPUT_METRICS_SEVERITE_PATH), exist_ok=True)
    os.makedirs(os.path.dirname(OUTPUT_PIPELINE_SEVERITE_ARTIFACT_PATH), exist_ok=True)
    os.makedirs(os.path.dirname(OUTPUT_PIPELINE_SEVERITE_JSON_PATH), exist_ok=True)
    os.makedirs(os.path.dirname(OUTPUT_COMPLETE_ARTIFACT_SEVERITE_PATH), exist_ok=True)
    os.makedirs(os.path.dirname(OUTPUT_SYNTHETIC_ARTIFACT_SEVERITE_PATH), exist_ok=True)

    # --- Chargement| copie avant traitement ---
    df_train = run_step("Chargement train.csv", pd.read_csv, TRAIN_PATH)
    df_test = run_step("Chargement test.csv", pd.read_csv, TEST_PATH)

    df_train_severite = run_step("Copie de df_train", lambda df: df.copy(), df_train)
    df_test_severite = run_step("Copie de df_test", lambda df: df.copy(), df_test)

    # =======================================================
    # --------------------- PIPELINE SEVERITE ---------------#
    # =======================================================

    # =============================================
    # ------------- PREPROCESSING -----------------#
    # =============================================
    target_col_severite = "montant_sinistre"
    pre_process = Severite_Preprocessing()

    df_train_severite = run_step(
        "Remove id columns train",
        pre_process._transform_remove_id_columns,
        "severite_train",
        df_train_severite,
    )

    df_train_severite = run_step(
        "Remove zero target train",
        pre_process._transform_remove_null_target,
        df_train_severite,
    )

    df_test_severite = run_step(
        "Remove id columns test",
        pre_process._transform_remove_id_columns,
        "severite_test",
        df_test_severite,
    )

    # =============================================
    # ----------- TRAIN / VALID SPLIT -------------#
    # =============================================
    X_train_severite, X_valid_severite, y_train_severite, y_valid_severite = run_step(
        "Train/Validation split",
        train_test_split,
        df_train_severite.drop(columns=[target_col_severite]),
        df_train_severite[target_col_severite],
        test_size=0.2,
        random_state=42,
        shuffle=True,
    )

    # --- Traitement sur les copies ---
    X_train_copie_severite = X_train_severite.copy()
    X_valid_copie_severite = X_valid_severite.copy()
    y_train_copie_severite = y_train_severite.copy()
    y_valid_copie_severite = y_valid_severite.copy()

    # =============================================
    # --------- FEATURE ENGINEERING ---------------#
    # =============================================
    fe_severite = Severite_Feature_Engineer(
        severite_process=pre_process
    ).build_feature_engineer(
        fit_process_nan_remover=True,
        transform_process_nan_remover=True,
        transform_remove_id_columns=False,
        transform_remove_zero_target=False,
        transform_preprocessing_null_target=False,
        threshold=0.9,
        preprocessing_map={},
        select_numeric_features_only=True,
        excluded_feature_columns=["nombre_sinistres"],
    )

    X_train_copie_severite = run_step(
        "Feature engineering fit_transform train severite",
        fe_severite.fit_transform,
        X_train_copie_severite,
        y_train_copie_severite,
    )

    X_valid_copie_severite = run_step(
        "Feature engineering transform valid severite",
        fe_severite.transform,
        X_valid_copie_severite,
    )

    df_test_severite = run_step(
        "Feature engineering transform test severite",
        fe_severite.transform,
        df_test_severite,
    )

    # =============================================
    # ----------------- MODELE --------------------#
    # =============================================
    model_severite = Model_Prediction_Severite()

    tuning_results = run_step(
        "Tune XGBRegressor",
        model_severite.tune_GBRegressor_hyperparameters,
        X_train_copie_severite,
        y_train_copie_severite,
    )

    model_severite = run_step(
        "Fit modele severite",
        model_severite.fit,
        X_train_copie_severite,
        y_train_copie_severite,
    )

    y_pred_train_severite = run_step(
        "Predict train severite", model_severite.predict, X_train_copie_severite
    )

    y_pred_valid_severite = run_step(
        "Predict valid severite", model_severite.predict, X_valid_copie_severite
    )

    y_pred_test_severite = run_step(
        "Predict test severite", model_severite.predict, df_test_severite
    )

    metrics = run_step(
        "Metrics severite",
        model_severite.metrics,
        y_train_copie_severite,
        y_pred_train_severite,
        y_valid_copie_severite,
        y_pred_valid_severite,
    )

    metrics_all = {
        "train": metrics["train"],
        "valid": metrics["valid"],
        "tuning": {
            "best_params": tuning_results.get("best_params"),
            "best_score": tuning_results.get("best_score"),
        },
    }

    stats_test_severite = run_step(
        "Stats predictions test severite",
        model_severite.test_prediction_stats,
        y_pred_test_severite,
        OUTPUT_METRICS_SEVERITE_PATH,
    )

    # Export prédictions test
    _generer_csv_pred_severite(
        df=df_test, y_pred=y_pred_test_severite, path=OUTPUT_TEST_SEVERITE_PATH
    )

    # --- SAUVEGARDES ---
    run_step(
        "Save feature engineer severite",
        fe_severite.save_feature_engineer,
        fe_severite,
        OUTPUT_FEATURE_ENGINEERING_SEVERITE_PATH,
    )

    run_step(
        "Save modele severite",
        model_severite.save_model,
        model_severite,
        OUTPUT_MODEL_SEVERITE_PATH,
        {"metrics": metrics_all},
    )

    run_step(
        "Save complete severite artifact",
        model_severite.save_complete_artifact,
        OUTPUT_COMPLETE_ARTIFACT_SEVERITE_PATH,
        fe_severite,
        {"metrics": metrics_all},
    )

    run_step(
        "Save synthetic severite artifact",
        model_severite.save_synthetic_artifact,
        OUTPUT_SYNTHETIC_ARTIFACT_SEVERITE_PATH,
        {"metrics": metrics_all},
    )

    LOGGER.info("Fin entrainement modele severite")
