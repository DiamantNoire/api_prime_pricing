#--*- coding: utf-8 -*-

# =============================================
#------ IMPORTATIONS DES LIBRAIRIES ----------#
# =============================================
import os
import pandas as pd
import numpy as np
from datetime import datetime
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.inspection import permutation_importance


# =============================================
#------ IMPORTATIONS DES MODULES -------------#
# =============================================
import sys
CURRENT_DIR = os.path.dirname(__file__)
if CURRENT_DIR not in sys.path:
    sys.path.append(CURRENT_DIR)

from utils_functions import (run_step,
                             Feature_Engineer_Freq,
                             Feature_Engineer_Amount,
                             Model_Prediction_Freq,
                             Model_Prediction_Amount,
                             Amount_Preprocessing)

if __name__ == "__main__":

    # =============================================
    #-------- CHARGEMENT DES DONNEES -------------#
    # =============================================
    DATA_DIR = os.path.dirname(__file__)
    TRAIN_PATH = os.path.join(DATA_DIR, 'input/train.csv')
    TEST_PATH = os.path.join(DATA_DIR, 'input/test.csv')
    PRIME_PRED_SANDBOX_PATH = os.path.join(DATA_DIR, 'input/prime_pred_sandbox.csv')
    POPULATION_PATH = os.path.join(DATA_DIR, 'input/POPULATION_MUNICIPALE_DEPARTEMENT_FRANCE.xlsx')

    df_train = run_step('Chargement train.csv', pd.read_csv, TRAIN_PATH)
    df_train_copie = run_step('Copie de df_train', lambda df: df.copy(), df_train)
    df_test = run_step('Chargement test.csv', pd.read_csv, TEST_PATH)
    df_test_copie = run_step('Copie de df_test', lambda df: df.copy(), df_test)
    df_prime_sandbox = run_step('Chargement prime_pred_sandbox.csv', pd.read_csv, PRIME_PRED_SANDBOX_PATH)
    df_prime_sandbox_copie = run_step('Copie de df_prime_sandbox', lambda df: df.copy(), df_prime_sandbox)
    df_population = run_step('Chargement POPULATION_MUNICIPALE_DEPARTEMENT_FRANCE.xlsx', pd.read_excel, POPULATION_PATH)
    df_population_copie = run_step('Copie de df_population', lambda df: df.copy(), df_population)

    # =======================================================
    #-------- DEFINITION DES CHEMINS DE SORTIE -------------#
    # =======================================================
    OUTPUT_FEATURE_ENGINEERING_AMOUNT_PATH = os.path.join(DATA_DIR, 'sorties/feature_engineering/features_amount.pickle')
    os.makedirs(os.path.dirname(OUTPUT_FEATURE_ENGINEERING_AMOUNT_PATH), exist_ok=True)

    OUTPUT_PAPELINE_AMOUNT_ARTIFACT_PATH = os.path.join(DATA_DIR, 'sorties/pipeline/pipeline_amount.pickle')
    os.makedirs(os.path.dirname(OUTPUT_PAPELINE_AMOUNT_ARTIFACT_PATH), exist_ok=True)


    # =======================================================
    #--------------------- PIPELINE AMOUNT -----------------#
    # =======================================================

    # --- Train/Validation split ---
    X_train_transfomed : pd.DataFrame = pd.DataFrame()  
    X_valid_transfomed : pd.DataFrame = pd.DataFrame()
    X_test_transfomed : pd.DataFrame = pd.DataFrame()

    X_train, X_valid, y_train, y_valid = run_step('Train/Validation split',
                                                  train_test_split,
                                                  df_train_copie.drop(columns=['montant_sinistre']),
                                                  df_train_copie['montant_sinistre'],
                                                  test_size=0.2,
                                                  random_state=42,
                                                  shuffle=True,)
    
    # --- Feature Engineering Amount  ---
    fe_amount = Feature_Engineer_Amount(amount_process=Amount_Preprocessing())
    run_step('Construction du feature engineer Amount', 
             fe_amount.build_feature_engineer, 
             fit_process_nan_remover=True, 
             transform_process_nan_remover=True, 
             threshold=0.9,
             transform_remove_zero_target=True,
             transform_preprocessing_null_target=True,
             transform_remove_null_target=True,
             preprocessing_map=None,
             categorical_features=['marque_vehicule', 'modele_vehicule'],
             alpha=20.0,
             min_count=5,
             per_col_min_count={'modele_vehicule': 20},
             per_col_top_k=None,
             noise_during_fit=True,
             noise_std=0.01,
             do_standardize=False,
             clip_pct=(0.01, 0.99))
    
    run_step('fit du feature engineer Amount sur train', 
             fe_amount.fit, 
             X=X_train,
             y=y_train)
    run_step('fit du feature engineer Amount sur valid', 
             fe_amount.fit, 
             X=X_valid,
             y=y_valid)
    
    X_train_transfomed = run_step('transform du feature engineer Amount sur train', 
                                  fe_amount.transform,
                                  X=X_train,
                                  y=None)
    X_valid_transfomed = run_step('transform du feature engineer Amount sur valid', 
                                  fe_amount.transform, 
                                  X=X_valid,
                                  y=None)
    X_test_transfomed = run_step('transform du feature engineer Amount sur test', 
                                 fe_amount.transform, 
                                 X=df_test_copie,
                                 y=None)
    
    # --- Modèle de prédiction Amount ---
    model_amount = Model_Prediction_Amount()
    metrics_amount = {}
    metrics_amount_train = {}
    metrics_amount_test = {}
    y_test_pred = pd.Series(dtype=float)

    model_amount.fit(X_train_transfomed, y_train)
    y_test_pred = run_step('Prédiction du modèle Amount sur test',
                           model_amount.predict,
                           X_test_transfomed)

    metrics_amount_train = run_step('Évaluation du modèle de prédiction Amount sur train',
                                    model_amount.metrics,
                                    X=X_train_transfomed,
                                    y=y_train)
    metrics_amount = run_step('Évaluation du modèle de prédiction Amount',
                              model_amount.metrics,
                              X=X_valid_transfomed,
                              y=y_valid)

    metrics_amount_test = {
        "count_predictions": int(len(y_test_pred)),
        "pred_mean": float(np.mean(y_test_pred)) if len(y_test_pred) > 0 else None,
        "pred_std": float(np.std(y_test_pred)) if len(y_test_pred) > 0 else None,
        "pred_min": float(np.min(y_test_pred)) if len(y_test_pred) > 0 else None,
        "pred_max": float(np.max(y_test_pred)) if len(y_test_pred) > 0 else None,
    }

    # --- Contrôle simple de contribution + drift (surapprentissage) ---
    selected_features = model_amount.get_selected_features()
    selected_features_keep = model_amount.get_selected_features_keep()
    selected_features_investigate = model_amount.get_selected_features_investigate()

    print("\n[FEATURES KEEP - AMOUNT]")
    print(selected_features_keep)
    print("\n[FEATURES INVESTIGATE - AMOUNT]")
    print(selected_features_investigate)

    perm_train = run_step('Permutation importance train (Amount)',
                          permutation_importance,
                          model_amount,
                          X_train_transfomed[selected_features],
                          y_train,
                          n_repeats=5,
                          random_state=42,
                          scoring='neg_mean_squared_error')

    perm_valid = run_step('Permutation importance valid (Amount)',
                          permutation_importance,
                          model_amount,
                          X_valid_transfomed[selected_features],
                          y_valid,
                          n_repeats=5,
                          random_state=42,
                          scoring='neg_mean_squared_error')

    contribution_drift_df = pd.DataFrame({
        'feature': selected_features,
        'contribution_train': perm_train.importances_mean,
        'contribution_valid': perm_valid.importances_mean,
    })
    contribution_drift_df['drift_abs'] = (
        contribution_drift_df['contribution_train'] - contribution_drift_df['contribution_valid']
    ).abs()
    contribution_drift_df['drift_ratio_train_over_valid'] = (
        contribution_drift_df['contribution_train'].abs() + 1e-9
    ) / (contribution_drift_df['contribution_valid'].abs() + 1e-9)
    contribution_drift_df = contribution_drift_df.sort_values('drift_abs', ascending=False)

    overfit_rmse_gap = metrics_amount_train.get("RMSE", 0.0) - metrics_amount.get("RMSE", 0.0)
    overfit_rmse_ratio = (
        (metrics_amount.get("RMSE", 0.0) + 1e-9)
        / (metrics_amount_train.get("RMSE", 0.0) + 1e-9)
    )
    overfit_flag_ratio_threshold_110 = overfit_rmse_ratio > 1.10

    print("\n[CONTRIBUTION DRIFT AMOUNT - TOP 15]")
    print(contribution_drift_df.head(15).to_string(index=False))
    
    # Sauvegardes robustes: FE , Modèle séparé + artefact pipeline unique
    run_step('Sauvegarde du feature engineer Amount',
             fe_amount.save_feature_engineer,
             fe_amount,
             OUTPUT_FEATURE_ENGINEERING_AMOUNT_PATH)
    run_step('Sauvegarde du modèle de prédiction Amount',
             model_amount.save_model,
             model_amount.model_,
             os.path.join(DATA_DIR, 'sorties/modeles/model_amount.pickle'))
    
    metadata_amount = {
        "target": "montant_sinistre",
        "created_at": datetime.now().isoformat(),
        "metrics_valid": {
            "RMSE": metrics_amount.get("RMSE"),
            "MSE": metrics_amount.get("MSE"),
        },
        "metrics_train": {
            "RMSE": metrics_amount_train.get("RMSE"),
            "MSE": metrics_amount_train.get("MSE"),
        },
        "metrics_test": metrics_amount_test,
        "overfitting_amount": {
            "rmse_gap_train_minus_valid": overfit_rmse_gap,
            "rmse_ratio_valid_over_train": overfit_rmse_ratio,
            "flag_ratio_over_1_10": overfit_flag_ratio_threshold_110,
        },
        "selected_features": selected_features,
        "selected_features_keep": selected_features_keep,
        "selected_features_investigate": selected_features_investigate,
        "columns_removed_due_to_nan": fe_amount.columns_to_remove,
        "contribution_drift_top15": contribution_drift_df.head(15).to_dict(orient='records'),
        "prediction_test_sample_top10": [float(v) for v in y_test_pred[:10]],
        "random_state": 42,
        "feature_engineer": fe_amount,
    }

    run_step('Sauvegarde du pipeline Amount (feature engineer + modèle)',
             model_amount.save_model,
             model_amount.model_,
             OUTPUT_PAPELINE_AMOUNT_ARTIFACT_PATH,
             metadata=metadata_amount)

    metadata_amount_loaded = run_step('Lecture des métadonnées de l\'artefact pipeline Amount',
                                      model_amount.read_artifact_metadata,
                                      OUTPUT_PAPELINE_AMOUNT_ARTIFACT_PATH)

    print("\n[METADATA PIPELINE AMOUNT]")
    print(metadata_amount_loaded)
    # Sauvegarde des prédictions de test pour la soumission finale
    amount_df = pd.DataFrame({
        'index': df_test_copie['index'],
        'amount_pred': y_test_pred 
    })
    amount_df.to_csv(os.path.join(DATA_DIR, 'sorties/pour_kaggle/Amount/pred_amount.csv'), index=False)
