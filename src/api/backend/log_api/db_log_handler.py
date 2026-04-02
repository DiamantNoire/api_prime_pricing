import logging
import sqlite3
import os
from datetime import datetime


class DBLogHandler(logging.Handler):
    """
    Handler de log Python pour écrire les logs dans la table log_api (SQLite).
    """

    def __init__(self, db_path=None):
        super().__init__()
        self.db_path = db_path or os.getenv(
            "API_LOG_DB_PATH", "db/prime_pricing.sqlite"
        )

    def emit(self, record):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            timestamp = datetime.fromtimestamp(record.created).isoformat()
            level = record.levelname
            logger_name = record.name
            message = self.format(record)
            exception = (
                self.formatException(record.exc_info) if record.exc_info else None
            )
            cursor.execute(
                """
                INSERT INTO log_api (timestamp, level, logger_name, message, exception)
                VALUES (?, ?, ?, ?, ?)
                """,
                (timestamp, level, logger_name, message, exception),
            )
            conn.commit()
            conn.close()
        except Exception:
            # fallback: log to stderr if DB logging fails
            logging.Handler.handleError(self, record)
