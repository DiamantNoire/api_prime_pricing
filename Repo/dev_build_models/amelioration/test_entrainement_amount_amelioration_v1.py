#--*- coding: utf-8 -*-
# Script Amount Amélioration v1 (Feature Engineering)

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime
from sklearn.model_selection import train_test_split
# Dossier parent pour import utils_functions
CURRENT_DIR = os.path.dirname(__file__)
PARENT_DIR = os.path.abspath(os.path.join(CURRENT_DIR, os.pardir))
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)
from utils_functions import (run_step, Feature_Engineer_Amount, Model_Prediction_Amount, Amount_Preprocessing)

if __name__ == "__main__":
    DATA_DIR = os.path.dirname(os.path.dirname(__file__))
    TRAIN_PATH = os.path.join(DATA_DIR, 'input/train.csv')
    TEST_PATH = os.path.join(DATA_DIR, 'input/test.csv')
    df_train = run_step('Chargement train.csv', pd.read_csv, TRAIN_PATH)
    df_test = run_step('Chargement test.csv', pd.read_csv, TEST_PATH)

    OUTPUT_ARTIFACT_PATH = os.path.join(DATA_DIR, 'sorties/amelioration/pipeline_amount_amelioration_v1.pickle')
    os.makedirs(os.path.dirname(OUTPUT_ARTIFACT_PATH), exist_ok=True)
    
    # Ajout d'une interaction simple (exemple)
    def add_interaction(df):
        if 'age_conducteur1' in df.columns and 'bonus' in df.columns:
            df['age1_x_bonus'] = df['age_conducteur1'] * df['bonus']
        return df

    # Ajout de la feature d'interaction AVANT le split
    df_train = add_interaction(df_train)
    
    # Split train/valid
    X_train, X_valid, y_train, y_valid = run_step('Train/Validation split',
                                                  train_test_split,
                                                  df_train.drop(columns=['montant_sinistre']),
                                                  df_train['montant_sinistre'],
                                                  test_size=0.2,
                                                  random_state=42,
                                                  shuffle=True)
    # Booking métier pour preprocessing + 1ère amélioration (exemple : interaction)
    preprocessing_map = {
        'bonus': 'winsorize',
        'prix_vehicule': 'log',
        'poids_vehicule': 'bin',
        'age_conducteur1': 'winsorize',
        'age_conducteur2': 'winsorize',
        'duree_contrat': 'bin',
    }

    fe_amount = Feature_Engineer_Amount(amount_process=Amount_Preprocessing())
    run_step('Construction du feature engineer Amount',
             fe_amount.build_feature_engineer,
             fit_process_nan_remover=True,
             transform_process_nan_remover=True,
             threshold=0.9,
             transform_remove_zero_target=True)
    run_step('fit du feature engineer Amount', fe_amount.fit, X=X_train, y=y_train)
    X_train_transfomed = run_step('transform du feature engineer Amount sur train', fe_amount.transform, X=X_train, y=None)
    X_valid_transfomed = run_step('transform du feature engineer Amount sur valid', fe_amount.transform, X=X_valid, y=None)
    X_test_transfomed = run_step('transform du feature engineer Amount sur test', fe_amount.transform, X=df_test, y=None)
    # Application de l'interaction
    X_train_transfomed = run_step('Ajout interaction sur train', add_interaction, X_train_transfomed)
    X_valid_transfomed = run_step('Ajout interaction sur valid', add_interaction, X_valid_transfomed)
    X_test_transfomed = run_step('Ajout interaction sur test', add_interaction, X_test_transfomed)

    model_amount = Model_Prediction_Amount()
    model_amount.fit(X_train_transfomed, y_train)
    y_test_pred = run_step('Prédiction du modèle Amount sur test', model_amount.predict, X_test_transfomed)
    metrics_amount_train = run_step('Évaluation du modèle Amount sur train', model_amount.metrics, X=X_train_transfomed, y=y_train)
    metrics_amount_valid = run_step('Évaluation du modèle Amount sur valid', model_amount.metrics, X=X_valid_transfomed, y=y_valid)
    
    # Traces et sauvegarde (structure harmonisée avec la version multi-modèles)
    metadata_amount = {
        "target": "montant_sinistre",
        "feature_engineering_steps": [
            "Suppression des NaN lors du fit",
            "Suppression des NaN lors du transform",
            "Seuil de sélection des features: 0.9",
            "Ajout interaction: age_conducteur1 x bonus"
        ],
        "created_at": datetime.now().isoformat(),
        "random_state": 42,
        "feature_engineer": fe_amount,
        # Bloc axe feature engineering (résultats pipeline unique)
        "feature_engineering_result": {
            "objectif": "amelioration_v1_feature_engineering",
            "metrics_train": metrics_amount_train,
            "metrics_valid": metrics_amount_valid,
            "selected_features": model_amount.get_selected_features(),
            "resume_traitement_feature": (
                "Objectif du run : ajout d'une interaction simple (age_conducteur1 x bonus) en plus du preprocessing."
            )
        }
    }
    run_step('Sauvegarde du pipeline Amount (amelioration v1)',
             model_amount.save_model,
             model_amount.model_,
             OUTPUT_ARTIFACT_PATH,
             metadata=metadata_amount)
    print("\n[METADATA PIPELINE AMOUNT AMELIORATION V1]")
    print(metadata_amount)
