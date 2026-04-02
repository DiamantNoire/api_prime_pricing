import logging
import os
from .db_log_handler import DBLogHandler

LOG_LEVEL = os.getenv("API_LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
LOG_FILE = os.getenv("API_LOG_FILE", None)
LOG_DB_PATH = os.getenv("API_LOG_DB_PATH", "db/prime_pricing.sqlite")

def get_logger(name: str) -> logging.Logger:
    """
    Retourne un logger configuré pour l'API backend.
    Les logs sont envoyés en console, fichier (optionnel) et base (log_api).
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(LOG_LEVEL)
        formatter = logging.Formatter(LOG_FORMAT)

        # Console
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)

        # Fichier (optionnel)
        if LOG_FILE:
            file_handler = logging.FileHandler(LOG_FILE)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

        # Base de données
        db_handler = DBLogHandler(db_path=LOG_DB_PATH)
        db_handler.setFormatter(formatter)
        logger.addHandler(db_handler)

    return logger
