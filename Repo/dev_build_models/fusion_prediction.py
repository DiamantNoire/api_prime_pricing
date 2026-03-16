#--*- coding: utf-8 -*-

# =============================================
#------ IMPORTATIONS DES LIBRAIRIES ----------#
# =============================================
import os
import sys
import pandas as pd
import numpy as np

# =============================================
#------ IMPORTATIONS DES MODULES -------------#
# =============================================
from fonctions_utiles import (run_step)

CURRENT_DIR = os.path.dirname(__file__)
if CURRENT_DIR not in sys.path:
    sys.path.append(CURRENT_DIR)

if __name__ == "__main__":
    # =============================================
    #-------- CHARGEMENT DES DONNEES -------------#
    # =============================================
    DATA_DIR = os.path.dirname(__file__)
    FREQ_PRED_PATH = os.path.join(DATA_DIR, 'sorties/predictions/test_predictions_frequence.csv')
    AMOUNT_PRED_PATH = os.path.join(DATA_DIR, 'sorties/predictions/test_predictions_severite.csv')

    # =======================================================
    #-------- DEFINITION DES CHEMINS DE SORTIE -------------#
    # =======================================================
    PRIME_PREDICT_PATH = os.path.join(DATA_DIR, 'sorties/predictions/test_prime.csv')


    # =======================================================
    #------ PIPELINE FINAL PRIME PREDICTION -----------------#
    # =======================================================
    freq_df = run_step('Chargement freq_pred.csv', pd.read_csv, FREQ_PRED_PATH)
    freq_df_copie = run_step('Copie Freq pour traitement', lambda df: df.copy(), freq_df)

    amount_df = run_step('Chargement amount_pred.csv', pd.read_csv, AMOUNT_PRED_PATH)
    amount_df_copie = run_step('Copie Amount pour traitement', lambda df: df.copy(), amount_df)
    # Sauvegarde de la prédiction finale 
    submission_df = pd.DataFrame({
        'index': amount_df_copie['index'],
        'pred':  amount_df_copie['pred']* freq_df['pred']
    })
    submission_df.to_csv(os.path.join(DATA_DIR, PRIME_PREDICT_PATH), index=False)

