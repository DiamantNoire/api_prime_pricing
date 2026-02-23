#--*- coding: utf-8 -*-
# Script Amount Amélioration v1 (Sélection de modèles)

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

    OUTPUT_ARTIFACT_PATH = os.path.join(DATA_DIR, 'sorties/amelioration/pipeline_amount_amelioration_v1_modeles.pickle')
    os.makedirs(os.path.dirname(OUTPUT_ARTIFACT_PATH), exist_ok=True)
    # Ajout d'une interaction simple (exemple)
    def add_interaction(df):
        if 'age_conducteur1' in df.columns and 'bonus' in df.columns:
            df['age1_x_bonus'] = df['age_conducteur1'] * df['bonus']
        return df

    # Ajout de la feature d'interaction AVANT le split
    df_train = add_interaction(df_train)

    X_train, X_valid, y_train, y_valid = run_step('Train/Validation split',
                                                  train_test_split,
                                                  df_train.drop(columns=['montant_sinistre']),
                                                  df_train['montant_sinistre'],
                                                  test_size=0.2,
                                                  random_state=42,
                                                  shuffle=True)

    fe_amount = Feature_Engineer_Amount(amount_process=Amount_Preprocessing())
    # Ajout explicite de la colonne d'interaction à la liste des features à garder
    extra_features = ['age1_x_bonus']
    run_step('Construction du feature engineer Amount',
             fe_amount.build_feature_engineer,
             fit_process_nan_remover=True,
             transform_process_nan_remover=True,
             threshold=0.9,
             transform_remove_zero_target=True)
    # On s'assure que la colonne d'interaction n'est jamais supprimée
    fe_amount.columns_to_remove = [col for col in fe_amount.columns_to_remove if col not in extra_features]
    
    run_step('fit du feature engineer Amount', fe_amount.fit, X=X_train, y=y_train)
    X_train_transfomed = run_step('transform du feature engineer Amount sur train', fe_amount.transform, X=X_train, y=None)
    X_valid_transfomed = run_step('transform du feature engineer Amount sur valid', fe_amount.transform, X=X_valid, y=None)
    X_test_transfomed = run_step('transform du feature engineer Amount sur test', fe_amount.transform, X=df_test, y=None)

    # Sélection de modèles : on compare tous les modèles de MODELS_REGRESSION
    model_amount = Model_Prediction_Amount()
    model_amount.fit(X_train_transfomed, y_train)
    results = {}
    for model_name in model_amount.models_:
        metrics_train = model_amount.metrics(X_train_transfomed, y_train, model_name=model_name)
        metrics_valid = model_amount.metrics(X_valid_transfomed, y_valid, model_name=model_name)
        # Prédiction sur le test
        try:
            y_pred_test = model_amount.predict(X_test_transfomed, model_name=model_name)
            # Calcul des métriques sur test si possible
            if 'montant_sinistre' in df_test.columns:
                metrics_test = model_amount.metrics(X_test_transfomed, df_test['montant_sinistre'], model_name=model_name)
            else:
                metrics_test = None
        except Exception as e:
            y_pred_test = f"Erreur prédiction test: {e}"
            metrics_test = f"Erreur métrics test: {e}"
        results[model_name] = {
            'train': metrics_train,
            'valid': metrics_valid,
            'test_pred': y_pred_test if isinstance(y_pred_test, str) else y_pred_test[:10],  # top 10
            'metrics_test': metrics_test
        }
    # Sélection du meilleur modèle selon RMSE valid
    best_model = min(results, key=lambda m: results[m]['valid']['RMSE'])

    # Calcul des métriques du modèle principal (par défaut LinearRegression)
    main_model_name = list(model_amount.models_.keys())[0]
    metrics_amount_train = results[main_model_name]['train']
    metrics_amount_valid = results[main_model_name]['valid']

    # Bloc commun
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
        },
        # Bloc axe sélection modèles (résultats multi-modèles)
        "model_selection_result": {
            "objectif": "amelioration_v1_selection_modeles",
            "results": results,
            "best_model": best_model,
            "selected_features": model_amount.get_selected_features(),
            "selected_features_keep": model_amount.get_selected_features_keep(),
            "selected_features_investigate": model_amount.get_selected_features_investigate(),
            "contribution_drift_top15": model_amount.contribution_drift_df_.to_dict(orient='records')[:15] if hasattr(model_amount, 'contribution_drift_df_') else None,
            "feature_importance": [
                {"feature": f, "importance": imp}
                for f, imp in zip(
                    getattr(model_amount, 'selected_features_', []),
                    [None]*len(getattr(model_amount, 'selected_features_', []))
                )
            ],
            "model_rmse": {k: v['valid']['RMSE'] for k, v in results.items()},
            "selected_models": [best_model],
            "resume_traitement_modeles": (
                "Objectif du run : comparaison multi-modèles sur le même pipeline de features."
            )
        }
    }
    run_step('Sauvegarde du pipeline Amount (amelioration v1 modeles)',
             model_amount.save_model,
             model_amount.models_[best_model],
             OUTPUT_ARTIFACT_PATH,
             metadata=metadata_amount)
    print("\n[METADATA PIPELINE AMOUNT AMELIORATION V1 - MODELES]")
    print(metadata_amount)
