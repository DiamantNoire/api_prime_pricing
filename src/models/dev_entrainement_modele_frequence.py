# --*- coding: utf-8 -*-

import os
import sys
import json
import logging
import pandas as pd
from sklearn.model_selection import train_test_split

LOGGER = logging.getLogger(__name__)

CURRENT_DIR = os.path.dirname(__file__)
if CURRENT_DIR not in sys.path:
    sys.path.append(CURRENT_DIR)

from fonctions_utiles import (
    run_step,
    run_internal_step,
    _generer_csv_pred_freqence,
    Frequence_Preprocessing,
    Frequence_Feature_Engineer,
    Model_Prediction_Frequence
)

# Les fonctions utilitaires importées sont documentées dans leur module d'origine.
# Ce script principal orchestre l'entraînement du modèle de fréquence, la sauvegarde des artefacts et l'export des prédictions.

# Aucun ajout de fonction locale à documenter ici, mais on ajoute une docstring de module.

"""
Script principal pour l'entraînement du modèle de prédiction de la fréquence.

Étapes principales :
    - Chargement et préparation des données d'entraînement et de test
    - Prétraitement et feature engineering
    - Entraînement, tuning et évaluation du modèle
    - Prédiction sur les jeux de données
    - Sauvegarde des artefacts (modèle, features, métriques, artefacts JSON)
    - Export des prédictions test au format CSV

Ce script ne définit pas de fonctions ou classes supplémentaires, mais orchestre l'ensemble du pipeline via les fonctions importées.
"""

if __name__ == "__main__":
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
    LOGGER.info("Demarrage entrainement modele frequence")

    # =============================================
    #-------- CHARGEMENT DES DONNEES -------------#
    # =============================================
    DATA_DIR = os.path.dirname(__file__)
    PROJECT_ROOT = os.path.abspath(os.path.join(DATA_DIR, '..', '..'))

    # --- Input ---
    TRAIN_PATH = os.path.join(PROJECT_ROOT, 'asset', 'train.csv')
    TEST_PATH = os.path.join(PROJECT_ROOT, 'asset', 'test.csv')

    # --- Output ---
    OUTPUT_FEATURE_ENGINEERING_FREQUENCE_PATH = os.path.join(DATA_DIR, 'output', 'feature_engineering', 'features_frequence.pickle')
    OUTPUT_MODEL_FREQUENCE_PATH = os.path.join(DATA_DIR, 'output', 'modeles', 'model_frequence.pickle')
    OUTPUT_METRICS_FREQUENCE_PATH = os.path.join(DATA_DIR, 'output', 'metrics', 'metrics_frequence.json')
    OUTPUT_TEST_PRED_FREQUENCE_PATH = os.path.join(DATA_DIR, 'output', 'predictions', 'test_predictions_frequence.csv')
    OUTPUT_COMPLETE_ARTIFACT_FREQUENCE_PATH = os.path.join(PROJECT_ROOT, 'output_models', 'modeles', 'model_frequence.json')
    OUTPUT_SYNTHETIC_ARTIFACT_FREQUENCE_PATH = os.path.join(DATA_DIR, 'output', 'artifacts', 'synthetic_artifact_frequence.json')

    os.makedirs(os.path.dirname(OUTPUT_FEATURE_ENGINEERING_FREQUENCE_PATH), exist_ok=True)
    os.makedirs(os.path.dirname(OUTPUT_MODEL_FREQUENCE_PATH), exist_ok=True)
    os.makedirs(os.path.dirname(OUTPUT_METRICS_FREQUENCE_PATH), exist_ok=True)
    os.makedirs(os.path.dirname(OUTPUT_TEST_PRED_FREQUENCE_PATH), exist_ok=True)
    os.makedirs(os.path.dirname(OUTPUT_COMPLETE_ARTIFACT_FREQUENCE_PATH), exist_ok=True)
    os.makedirs(os.path.dirname(OUTPUT_SYNTHETIC_ARTIFACT_FREQUENCE_PATH), exist_ok=True)

    df_train = run_step('Chargement train.csv', pd.read_csv, TRAIN_PATH)
    df_test = run_step('Chargement test.csv', pd.read_csv, TEST_PATH)


    df_train_freq = run_step('Copie de df_train', lambda df: df.copy(), df_train)
    df_test_freq = run_step('Copie de df_test', lambda df: df.copy(), df_test)

    # =======================================================
    #--------------------- PIPELINE SEVERITE ---------------#
    # =======================================================

    # =============================================
    #------------- PREPROCESSING -----------------#
    # =============================================
    target_col_freq = 'nombre_sinistres'
    pre_process = Frequence_Preprocessing(target_col=target_col_freq)

    df_train_freq = run_step(
        'Remove id columns train frequence',
        pre_process._transform_remove_id_columns,
        'frequence_train',
        df_train_freq
    )

    df_train_freq = run_step(
        'Remove zero second target',
        pre_process._transform_remove_null_second_target,
        df_train_freq
    )

    df_test_freq = run_step(
        'Remove id columns test frequence',
        pre_process._transform_remove_id_columns,
        'frequence_test',
        df_test_freq
    )

    # =============================================
    #------------- TRAIN / VALID SPLIT ------------#
    # =============================================
    X_train_freq, X_valid_freq, y_train_freq, y_valid_freq = run_step(
        'Train/Validation split pour fréquence',
        train_test_split,
        df_train_freq.drop(columns=[target_col_freq]),
        df_train_freq[target_col_freq],
        test_size=0.2,
        random_state=42,
        shuffle=True,
        stratify=df_train_freq[target_col_freq]
    )

    # --- Traitement sur les copies ---
    X_train_copie_freq = X_train_freq.copy()
    X_valid_copie_freq = X_valid_freq.copy()
    y_train_copie_freq = y_train_freq.copy()
    y_valid_copie_freq = y_valid_freq.copy()

    # =============================================
    #----------- FEATURE ENGINEERING --------------#
    # =============================================
    fe_frequence = Frequence_Feature_Engineer(
        frequence_process=pre_process
    ).build_feature_engineer(
        fit_process_nan_remover=True,
        transform_process_nan_remover=True,
        transform_remove_id_columns=False,
        threshold=0.9,
        preprocessing_map={},
        select_numeric_features_only=True,
        excluded_feature_columns=[]
    )

    X_train_copie_freq = run_step(
        'Feature engineering fit_transform train frequence',
        fe_frequence.fit_transform,
        X_train_copie_freq,
        y_train_copie_freq
    )

    X_valid_copie_freq = run_step(
        'Feature engineering transform valid frequence',
        fe_frequence.transform,
        X_valid_copie_freq
    )

    df_test_copie_freq = run_step(
        'Feature engineering transform test frequence',
        fe_frequence.transform,
        df_test_freq
    )


    # =============================================
    #------------------- MODELE -------------------#
    # =============================================
    model_frequence = Model_Prediction_Frequence()

    tuning_results = run_step(
        'Tune XGBRegressor',
        model_frequence.tune_XGBRegressor_hyperparameters,
        X_train_copie_freq,
        y_train_copie_freq
    )

    model_frequence = run_step(
        'Fit modele frequence',
        model_frequence.fit,
        X_train_copie_freq,
        y_train_copie_freq
    )

    y_pred_train_freq = run_step(
        'Predict train frequence',
        model_frequence.predict,
        X_train_copie_freq
    )

    y_pred_valid_freq = run_step(
        'Predict valid frequence',
        model_frequence.predict,
        X_valid_copie_freq
    )

    y_pred_test_freq = run_step(
        'Predict test frequence',
        model_frequence.predict,
        df_test_freq
    )
    metrics = run_step(
        'Metrics train frequence',
        model_frequence.metrics,
        y_train_copie_freq,
        y_pred_train_freq,
        y_valid_copie_freq,
        y_pred_valid_freq, 
    )

    metrics_all = {
        "train": metrics['train'],
        "valid": metrics['valid'],
        "tuning": {
            "best_params": tuning_results.get("best_params"),
            "best_score": tuning_results.get("best_score")
        }
    }

    stats_test_freq = run_step(
        'Stats predictions test frequence',
        model_frequence.test_prediction_stats,
        y_pred_test_freq,
        OUTPUT_METRICS_FREQUENCE_PATH
    )


    # --- Export prédictions test ---
    _generer_csv_pred_freqence(df=df_test,
                               y_pred=y_pred_test_freq,
                               path=OUTPUT_TEST_PRED_FREQUENCE_PATH)
    

    # --- SAUVEGARDES --- 
    run_step(
        'Save feature engineer frequence',
        fe_frequence.save_feature_engineer,
        fe_frequence,
        OUTPUT_FEATURE_ENGINEERING_FREQUENCE_PATH
    )

    run_step(
        'Save modele frequence',
        model_frequence.save_model,
        model_frequence,
        OUTPUT_MODEL_FREQUENCE_PATH,
        {"metrics": metrics_all}
    )

    run_step(
        'Save complete frequence artifact',
        model_frequence.save_complete_artifact,
        OUTPUT_COMPLETE_ARTIFACT_FREQUENCE_PATH,
        fe_frequence,
        {"metrics": metrics_all}
    )

    run_step(
        'Save synthetic frequence artifact',
        model_frequence.save_synthetic_artifact,
        OUTPUT_SYNTHETIC_ARTIFACT_FREQUENCE_PATH,
        {"metrics": metrics_all}
    )

    LOGGER.info("Fin entrainement modele frequence")