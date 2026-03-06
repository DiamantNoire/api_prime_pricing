#--*- coding: utf-8 -*-

# =============================================
#------ IMPORTATIONS DES LIBRAIRIES ----------#
# =============================================
import os
import pandas as pd
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
                             Model_Prediction_Freq,
                             Freq_Preprocessing)

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
    OUTPUT_FEATURE_ENGINEERING_FREQ_PATH = os.path.join(DATA_DIR, 'sorties/feature_engineering/features_freq.pickle')
    os.makedirs(os.path.dirname(OUTPUT_FEATURE_ENGINEERING_FREQ_PATH), exist_ok=True)
    OUTPUT_MODEL_PREDICTION_FREQ_PATH = os.path.join(DATA_DIR, 'sorties/model_prediction/model_prediction_freq.pickle')
    os.makedirs(os.path.dirname(OUTPUT_MODEL_PREDICTION_FREQ_PATH), exist_ok=True)
    OUTPUT_PAPELINE_FREQ_ARTIFACT_PATH = os.path.join(DATA_DIR, 'sorties/pipeline/pipeline_freq.pickle')
    os.makedirs(os.path.dirname(OUTPUT_PAPELINE_FREQ_ARTIFACT_PATH), exist_ok=True)


    # =======================================================
    #--------------------- PIPELINE FREQ -------------------#
    # =======================================================
    TARGET_FREQ = 'nombre_sinistres'

    # --- Train/Validation split ---
    X_train_transfomed : pd.DataFrame = pd.DataFrame()  
    X_valid_transfomed : pd.DataFrame = pd.DataFrame()
    X_test_transfomed : pd.DataFrame = pd.DataFrame()

    X_train, X_valid, y_train, y_valid = run_step('Train/Validation split',
                                                  train_test_split,
                                                  df_train_copie.drop(columns=[TARGET_FREQ, 'montant_sinistre'], errors='ignore'),
                                                  df_train_copie[TARGET_FREQ],
                                                  test_size=0.2,
                                                  random_state=42,
                                                  shuffle=True,)
    

    # --- Feature Engineering Freq  ---
    fe_freq = Feature_Engineer_Freq(freq_process=Freq_Preprocessing())
    run_step('Construction du feature engineer Freq', 
             fe_freq.build_feature_engineer, 
             fit_process_nan_remover=True, 
             transform_process_nan_remover=True, 
             transform_remove_zero_target=True,
             threshold=0.9,
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

    run_step('fit du feature engineer Freq', 
            fe_freq.fit, 
            X=X_train,
            y=y_train)
    
    X_train_transfomed = run_step('transform du feature engineer Freq sur train', 
                                  fe_freq.transform,
                                  X=X_train,
                                  y=None)
    X_valid_transfomed = run_step('transform du feature engineer Freq sur valid', 
                                  fe_freq.transform, 
                                  X=X_valid,
                                  y=None)
    X_test_transfomed = run_step('transform du feature engineer Freq sur test', 
                                 fe_freq.transform, 
                                 X=df_test_copie,
                                 y=None)

    # --- Modèle de prédiction Freq ---
    model_freq = Model_Prediction_Freq()
    metrics_freq = {}
    model_freq.fit(X_train_transfomed, y_train)
    # Prédiction sur le jeu de test
    y_test_pred_proba = run_step('Prédiction du modèle Freq sur test',
                                 model_freq.predict_proba,
                                 X_test_transfomed)

    # Affichage des métriques sur la prédiction du test
    if hasattr(y_test_pred_proba, 'shape') and y_test_pred_proba.shape[1] > 1:
        proba_1 = y_test_pred_proba[:, 1]
    else:
        proba_1 = y_test_pred_proba.ravel()
    print("\n[METRICS PREDICTION TEST FREQ]")
    print(f"mean_pred: {proba_1.mean():.4f}, min_pred: {proba_1.min():.4f}, max_pred: {proba_1.max():.4f}")
    print(f"Distribution: {pd.Series(proba_1).describe()}")


    # Évaluation sur train et valid
    metrics_freq_train = run_step('Évaluation du modèle de prédiction Freq sur train',
                                  model_freq.metrics,
                                  X=X_train_transfomed,
                                  y=y_train)
    metrics_freq = run_step('Évaluation du modèle de prédiction Freq',
                            model_freq.metrics,
                            X=X_valid_transfomed,
                            y=y_valid)

    # --- Contrôle simple de contribution + drift (surapprentissage) ---
    selected_features = model_freq.get_selected_features()
    selected_features_keep = model_freq.get_selected_features_keep()
    selected_features_investigate = model_freq.get_selected_features_investigate()

    print("\n[FEATURES KEEP - FREQ]")
    print(selected_features_keep)
    print("\n[FEATURES INVESTIGATE - FREQ]")
    print(selected_features_investigate)

    perm_train = run_step('Permutation importance train (Freq)',
                          permutation_importance,
                          model_freq,
                          X_train_transfomed[selected_features],
                          y_train,
                          n_repeats=5,
                          random_state=42,
                          scoring='neg_mean_squared_error')

    perm_valid = run_step('Permutation importance valid (Freq)',
                          permutation_importance,
                          model_freq,
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

    print("\n[CONTRIBUTION DRIFT FREQ - TOP 15]")
    print(contribution_drift_df.head(15).to_string(index=False))

    # Sauvegardes robustes: FE séparé + artefact pipeline unique
    run_step('Sauvegarde du feature engineer Freq',
             fe_freq.save_feature_engineer,
             fe_freq,
             OUTPUT_FEATURE_ENGINEERING_FREQ_PATH)

    metadata_freq = {
        "target": TARGET_FREQ,
        "created_at": datetime.now().isoformat(),
        "metrics_train": {
            "RMSE": metrics_freq_train.get("RMSE"),
        },
        "metrics_valid": {
            "RMSE": metrics_freq.get("RMSE"),
        },
        "metrics_pred_test": {
            "mean_pred": float(proba_1.mean()),
            "min_pred": float(proba_1.min()),
            "max_pred": float(proba_1.max()),
            "describe": pd.Series(proba_1).describe().to_dict()
        },
        "selected_features": selected_features,
        "selected_features_keep": selected_features_keep,
        "selected_features_investigate": selected_features_investigate,
        "columns_removed_due_to_nan": fe_freq.columns_to_remove,
        "contribution_drift_top15": contribution_drift_df.head(15).to_dict(orient='records'),
        "random_state": 42,
        "feature_engineer": fe_freq,
    }

    run_step('Sauvegarde du pipeline Freq (feature engineer + modèle)',
             model_freq.save_model,
             model_freq.model_,
             OUTPUT_PAPELINE_FREQ_ARTIFACT_PATH,
             metadata=metadata_freq)

    metadata_freq_loaded = run_step('Lecture des métadonnées de l\'artefact pipeline Freq',
                                    model_freq.read_artifact_metadata,
                                    OUTPUT_PAPELINE_FREQ_ARTIFACT_PATH)

    print("\n[METADATA PIPELINE FREQ]")
    print(metadata_freq_loaded)

    # Sauvegarde des prédictions de test pour la soumission finale
    # Sauvegarde la probabilité de la classe 1 (sans seuil)
    if hasattr(y_test_pred_proba, 'shape') and y_test_pred_proba.shape[1] > 1:
        proba_1 = y_test_pred_proba[:, 1]
    else:
        proba_1 = y_test_pred_proba.ravel()
    freq_df = pd.DataFrame({
        'index': df_test_copie['index'],
        'freq_pred': proba_1
    })
    freq_df.to_csv(os.path.join(DATA_DIR, 'sorties/pour_kaggle/Freq/pred_freq.csv'), index=False)
