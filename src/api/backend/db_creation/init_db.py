#--*- coding: utf-8 -*-

# ===============================================================
# 1- IMPORTATIONS DES LIBRAIRIES 
# 2- CONFIGURATION DE LA BARRE DE CHARGEMENT
# 3- FONCTION DE CREATION DE LA BASE DE DONNEES
# ===============================================================


# ===============================================================
# 1- IMPORTATIONS DES LIBRAIRIES | MODULES
# ===============================================================
import os
import sys
import logging
from pathlib import Path
from src.models.fonctions_utiles import Data_Base_Creator

LOGGER = logging.getLogger(__name__)
BASE_DIR = Path(__file__).resolve().parents[4]
ASSET_DIR = BASE_DIR / "asset"
OUTPUT_PREDICTIONS_DIR = BASE_DIR / "output_models" / "predictions"


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
    db.create_table_historique_contrats(str(ASSET_DIR / "train.csv"))

def fill_predictions():
    db = Data_Base_Creator()
    db.create_table_predictions(
        str(OUTPUT_PREDICTIONS_DIR / "test_predictions_frequence.csv"),
        str(OUTPUT_PREDICTIONS_DIR / "test_predictions_severite.csv"),
        str(OUTPUT_PREDICTIONS_DIR / "test_prime.csv"),
    )

def run_api():
    import uvicorn

    uvicorn.run(
        "src.api.backend.server:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8000")),
        reload=os.getenv("APP_RELOAD", "false").lower() == "true",
    )

if __name__ == "__main__":
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))

    actions = {
        "init_db": init_db,
        "fill_historique": fill_historique,
        "fill_predictions": fill_predictions,
        "run_api": run_api,
    }
    if len(sys.argv) < 2 or sys.argv[1] not in actions:
        LOGGER.warning("Usage: python main.py [init_db|fill_historique|fill_predictions|run_api]")
    else:
        LOGGER.info("Execution action init_db: %s", sys.argv[1])
        actions[sys.argv[1]]()
