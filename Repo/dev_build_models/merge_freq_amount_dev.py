#--*- coding: utf-8 -*-

# =============================================
#------ IMPORTATIONS DES LIBRAIRIES ----------#
# =============================================
import os
import pandas as pd
import numpy as np

# =============================================
#------ IMPORTATIONS DES MODULES -------------#
# =============================================
from utils_functions import (run_step)
import sys
CURRENT_DIR = os.path.dirname(__file__)
if CURRENT_DIR not in sys.path:
    sys.path.append(CURRENT_DIR)

if __name__ == "__main__":

    # =============================================
    #-------- CHARGEMENT DES DONNEES -------------#
    # =============================================
    DATA_DIR = os.path.dirname(__file__)
    FREQ_PRED_PATH = os.path.join(DATA_DIR, 'sorties/pour_kaggle/Freq/predictions_frequence_poisson.csv')
    AMOUNT_PRED_PATH = os.path.join(DATA_DIR, 'sorties/pour_kaggle/Amount/pred_amount.csv')

    # =======================================================
    #-------- DEFINITION DES CHEMINS DE SORTIE -------------#
    # =======================================================
    SUBMIT_KAGGLE_PATH = os.path.join(DATA_DIR, 'sorties/Final_pred_for_sublit/pred_prime.csv')


    # =======================================================
    #------ PIPELINE FINAL PRIME PREDICTION -----------------#
    # =======================================================
    freq_df = run_step('Chargement freq_pred.csv', pd.read_csv, FREQ_PRED_PATH)
    freq_df_copie = run_step('Copie Freq pour traitement', lambda df: df.copy(), freq_df)

    amount_df = run_step('Chargement amount_pred.csv', pd.read_csv, AMOUNT_PRED_PATH)
    amount_df_copie = run_step('Copie Amount pour traitement', lambda df: df.copy(), amount_df)
<<<<<<< HEAD

=======
    # Sauvegarde de la prédiction finale pour la soumission Kaggle
>>>>>>> d9632c7 (clean)
    submission_df = pd.DataFrame({
        'index': amount_df_copie['index'],
        'pred':  amount_df_copie['amount_pred']* freq_df['frequence_predite']
    })
    submission_df.to_csv(os.path.join(DATA_DIR, 'sorties/pour_kaggle/Final_pred_for_submit/prime_prediction.csv'), index=False)

