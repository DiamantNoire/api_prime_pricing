#--*- coding: utf-8 -*-
# Script Amount Préprocessing (features investiguées transformées)

# =============================================
#------ IMPORTATIONS DES LIBRAIRIES ----------#
# =============================================
import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime
from sklearn.model_selection import train_test_split
from sklearn.inspection import permutation_importance

# =============================================
#------ IMPORTATIONS DES MODULES -------------#
# =============================================
CURRENT_DIR = os.path.dirname(__file__)
if CURRENT_DIR not in sys.path:
    sys.path.append(CURRENT_DIR)
from utils_functions import (run_step,
                             Feature_Engineer_Amount,
                             Model_Prediction_Amount,
                             Amount_Preprocessing)



if __name__ == "__main__":
    # =============================================
    #-------- CHARGEMENT DES DONNEES -------------#
    # =============================================
    DATA_DIR = os.path.dirname(__file__)
    TRAIN_PATH = os.path.join(DATA_DIR, 'input/train.csv')
    TEST_PATH = os.path.join(DATA_DIR, 'input/test.csv')
    df_train = run_step('Chargement train.csv', pd.read_csv, TRAIN_PATH)
    df_train_copie = run_step('Copie de df_train', lambda df: df.copy(), df_train)
    df_test = run_step('Chargement test.csv', pd.read_csv, TEST_PATH)
    df_test_copie = run_step('Copie de df_test', lambda df: df.copy(), df_test)

    # =======================================================
    #-------- DEFINITION DES CHEMINS DE SORTIE -------------#
    # =======================================================
    OUTPUT_ARTIFACT_PATH = os.path.join(DATA_DIR, 'sorties/pipeline/pipeline_amount_preproc.pickle')
    os.makedirs(os.path.dirname(OUTPUT_ARTIFACT_PATH), exist_ok=True)


    # =======================================================
    #--------------------- PIPELINE AMOUNT -----------------#
    # =======================================================
    # --- Train/Validation split ---
    X_train, X_valid, y_train, y_valid = run_step('Train/Validation split',
                                                  train_test_split,
                                                  df_train_copie.drop(columns=['montant_sinistre']),
                                                  df_train_copie['montant_sinistre'],
                                                  test_size=0.2,
                                                  random_state=42,
                                                  shuffle=True)
    # Booking métier pour preprocessing
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
             transform_remove_zero_target=True,
             threshold=0.9,
             preprocessing_map=preprocessing_map)
    run_step('fit du feature engineer Amount sur train',
             fe_amount.fit,
             X=X_train,
             y=y_train)
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
    model_amount = Model_Prediction_Amount()
    model_amount.fit(X_train_transfomed, y_train)
    y_test_pred = run_step('Prédiction du modèle Amount sur test',
                           model_amount.predict,
                           X_test_transfomed)
    metrics_amount_train = run_step('Évaluation du modèle de prédiction Amount sur train',
                                    model_amount.metrics,
                                    X=X_train_transfomed,
                                    y=y_train)
    metrics_amount_valid = run_step('Évaluation du modèle de prédiction Amount sur valid',
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
    selected_features = model_amount.get_selected_features()
    selected_features_keep = model_amount.get_selected_features_keep()
    selected_features_investigate = model_amount.get_selected_features_investigate()
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
    overfit_rmse_gap = metrics_amount_train.get("RMSE", 0.0) - metrics_amount_valid.get("RMSE", 0.0)
    overfit_rmse_ratio = (
        (metrics_amount_valid.get("RMSE", 0.0) + 1e-9)
        / (metrics_amount_train.get("RMSE", 0.0) + 1e-9)
    )
    overfit_flag_ratio_threshold_110 = overfit_rmse_ratio > 1.10
    # Trace des features à investiguer non sélectionnées et leur importance
    features_non_select = [f for f in selected_features_investigate if f not in selected_features_keep]
    importance_non_select = {}

    # Récupérer la contribution (drift) si présente dans le DataFrame
    contribution_non_select = {}
    for f in features_non_select:
        if f in contribution_drift_df['feature'].values:
            row = contribution_drift_df[contribution_drift_df['feature'] == f]
            contribution_non_select[f] = {
                'contribution_train': float(row['contribution_train'].values[0]),
                'contribution_valid': float(row['contribution_valid'].values[0]),
                'drift_abs': float(row['drift_abs'].values[0]),
                'drift_ratio_train_over_valid': float(row['drift_ratio_train_over_valid'].values[0])
            }
        else:
            contribution_non_select[f] = None

    # Critère de non-sélection (exemple : importance < seuil arbitraire ou non retenue par la sélection automatique)
    critere_non_selection = {}
    seuil_importance = 1e-3  # seuil arbitraire, à adapter selon le contexte
    for f in features_non_select:
        imp = importance_non_select.get(f)
        if imp is not None and abs(imp) < seuil_importance:
            critere_non_selection[f] = f"Importance permutation < {seuil_importance}"
        else:
            critere_non_selection[f] = "Non retenue par la sélection automatique du modèle (importance insuffisante ou redondance)"

    metadata_amount = {
        "target": "montant_sinistre",
        "objectif": "preprocessing",
        "feature_engineering_steps": {
            "booking_appleid": fe_amount.booking_applied,
            "preprocessing_map": fe_amount.preprocessing_map
        },        "created_at": datetime.now().isoformat(),
        "metrics_valid": metrics_amount_valid,
        "metrics_train": metrics_amount_train,
        "metrics_test": metrics_amount_test,
        "overfitting_amount": {
            "rmse_gap_train_minus_valid": overfit_rmse_gap,
            "rmse_ratio_valid_over_train": overfit_rmse_ratio,
            "flag_ratio_over_1_10": overfit_flag_ratio_threshold_110,
        },
        "selected_features": selected_features,
        "selected_features_keep": selected_features_keep,
        "selected_features_investigate": selected_features_investigate,
        "contribution_drift_top15": contribution_drift_df.head(15).to_dict(orient='records'),
        "prediction_test_sample_top10": [float(v) for v in y_test_pred[:10]],
        "random_state": 42,
        "feature_engineer": fe_amount,
        "resume_traitement_feature": (
            "Objectif du run : preprocessing (imputation, normalisation, encodage, puis sélection automatique des variables par permutation_importance).\n"
            f"Features à investiguer non sélectionnées : {features_non_select}.\n"
            f"Importance permutation_importance sur train : {importance_non_select}.\n"
            f"Contribution (drift) : {contribution_non_select}.\n"
            f"Critère de non-sélection : {critere_non_selection}.\n"
            "Elles sont écartées car leur contribution/importance est jugée insuffisante ou redondante par le modèle."
        )
    }
    run_step('Sauvegarde du pipeline Amount (preproc)',
             model_amount.save_model,
             model_amount.model_,
             OUTPUT_ARTIFACT_PATH,
             metadata=metadata_amount)
    print("\n[METADATA PIPELINE AMOUNT PREPROC]")
    print(metadata_amount)
