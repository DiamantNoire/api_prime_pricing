#--*- coding: utf-8 -*-

# ===============================================================
# 1- IMPORTATIONS DES LIBRAIRIES - MODULES
# 2- LANCEMENT DES SERVICES
# ===============================================================

from src.api.backend.services.contrat_service import ContratService
from src.api.backend.services.contrat_ml_service import MLService
import logging


def main():
    # Initialisation du logger
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("main")

    # Initialisation des services
    contrat_service = ContratService()
    ml_service = MLService()
    logger.info("Service Contrat initialisé : %s", contrat_service)
    logger.info("Service ML initialisé : %s", ml_service)

if __name__ == "__main__":
    main()
