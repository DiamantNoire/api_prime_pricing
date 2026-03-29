#--*- coding: utf-8 -*-

# ===============================================================
# 1- IMPORTATIONS DES LIBRAIRIES 
# 2- CONFIGURATION DE LA BARRE DE CHARGEMENT
# 3- FONCTION DE CREATION DE LA BASE DE DONNEES
# ===============================================================


# ===============================================================
# 1- IMPORTATIONS DES LIBRAIRIES | MODULES
# ===============================================================
import sys 
from src.models.fonctions_utiles import Data_Base_Creator

# ===============================================================
# 2- CHEMIN 
# ===============================================================


# ===============================================================
# 3- FONCTION DE CREATION DE LA BASE DE DONNEES
# ===============================================================
def init_db():
    db = Data_Base_Creator()
    db.create_database()

def fill_historique():
    db = Data_Base_Creator()
    db.create_table_historique_contrats("asset/train.csv")

def fill_predictions():
    db = Data_Base_Creator()
    db.create_table_predictions(
        "output_models/predictions/test_predictions_frequence.csv",
        "output_models/predictions/test_predictions_severite.csv",
        "output_models/predictions/test_prime.csv"
    )

def run_api():
    import uvicorn
    uvicorn.run("src.api.backend.server:app", host="0.0.0.0", port=8000, reload=True)

if __name__ == "__main__":
    actions = {
        "init_db": init_db,
        "fill_historique": fill_historique,
        "fill_predictions": fill_predictions,
        "run_api": run_api,
    }
    if len(sys.argv) < 2 or sys.argv[1] not in actions:
        print("Usage: python main.py [init_db|fill_historique|fill_predictions|run_api]")
    else:
        actions[sys.argv[1]]()
