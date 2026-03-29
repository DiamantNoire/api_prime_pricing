"""Module de surveillance de l'état de santé de l'API et de la base de données."""

from __future__ import annotations

import logging
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import requests

logger = logging.getLogger(__name__)


@dataclass
class HealthStatus:
    """Représente l'état de santé d'un service."""

    name: str
    status: str  # "ok", "error", "unreachable", "rate_limited"
    description: str
    details: Optional[dict] = None

    def is_healthy(self) -> bool:
        """Retourne True si le service est sain."""
        return self.status == "ok"

    def to_dict(self) -> dict:
        """Convertit le statut en dictionnaire."""
        return {
            "name": self.name,
            "status": self.status,
            "description": self.description,
            "details": self.details or {},
        }


class HealthMonitor:
    """Monitore l'état de santé de l'API et de la base de données."""

    def __init__(
        self,
        api_base_url: str = "http://127.0.0.1:8000",
        db_path: str = "db/prime_pricing.sqlite",
        timeout: int = 5,
    ):
        """
        Initialise le moniteur de santé.

        Args:
            api_base_url: URL de base de l'API
            db_path: Chemin vers la base de données SQLite
            timeout: Délai d'expiration pour les appels HTTP en secondes
        """
        self.api_base_url = api_base_url
        self.db_path = Path(db_path)
        self.timeout = timeout
        logger.info(
            f"HealthMonitor initialisé: API={api_base_url}, DB={db_path}, "
            f"timeout={timeout}s"
        )

    def check_main_api_health(self) -> HealthStatus:
        """Vérifie l'état de santé de l'API principale."""
        try:
            response = requests.get(
                f"{self.api_base_url}/health",
                timeout=self.timeout,
            )
            response.raise_for_status()

            logger.debug("✓ API principale est saine")
            return HealthStatus(
                name="API Principale",
                status="ok",
                description="L'API est en ligne et répond normalement",
                details=response.json(),
            )

        except requests.exceptions.ConnectionError as exc:
            logger.warning(f"✗ Connexion impossible à l'API: {exc}")
            return HealthStatus(
                name="API Principale",
                status="unreachable",
                description="Impossible de se connecter à l'API. Vérifiez que le serveur est lancé.",
                details={"error": str(exc)},
            )

        except requests.exceptions.Timeout:
            logger.warning(f"✗ Timeout lors de l'appel à l'API ({self.timeout}s)")
            return HealthStatus(
                name="API Principale",
                status="unreachable",
                description=f"L'API n'a pas répondu dans le délai imparti ({self.timeout}s)",
                details={"error": "Timeout"},
            )

        except requests.exceptions.HTTPError as exc:
            status_code = exc.response.status_code if exc.response is not None else None
            if status_code == 429:
                retry_after = exc.response.headers.get("Retry-After") if exc.response is not None else None
                logger.warning("✗ API principale limitée (HTTP 429), retry_after=%s", retry_after)
                return HealthStatus(
                    name="API Principale",
                    status="rate_limited",
                    description="Limite de requêtes atteinte sur l'API (HTTP 429)",
                    details={
                        "error": str(exc),
                        "status_code": status_code,
                        "retry_after": retry_after,
                    },
                )

            logger.warning(f"✗ L'API a retourné une erreur HTTP: {exc}")
            return HealthStatus(
                name="API Principale",
                status="error",
                description=f"L'API a retourné une erreur HTTP {status_code}",
                details={"error": str(exc), "status_code": status_code},
            )

        except Exception as exc:
            logger.exception(f"✗ Erreur inattendue lors du check API: {exc}")
            return HealthStatus(
                name="API Principale",
                status="error",
                description="Une erreur inattendue s'est produite",
                details={"error": str(exc)},
            )

    def _check_prediction_endpoint_health(self, endpoint_path: str, endpoint_name: str) -> HealthStatus:
        """Vérifie l'état d'un endpoint de santé lié aux prédictions."""
        try:
            url = f"{self.api_base_url}{endpoint_path}"
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()

            data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
            api_status = data.get("status")

            if api_status == "ok":
                return HealthStatus(
                    name=endpoint_name,
                    status="ok",
                    description="Endpoint santé opérationnel",
                    details={
                        "endpoint": endpoint_path,
                        "http_status": response.status_code,
                        "api_status": api_status,
                    },
                )

            return HealthStatus(
                name=endpoint_name,
                status="error",
                description="Endpoint santé répond mais signale une erreur applicative",
                details={
                    "endpoint": endpoint_path,
                    "http_status": response.status_code,
                    "api_status": api_status,
                    "detail": data.get("detail"),
                },
            )

        except requests.exceptions.ConnectionError as exc:
            logger.warning("✗ Endpoint %s injoignable: %s", endpoint_path, exc)
            return HealthStatus(
                name=endpoint_name,
                status="unreachable",
                description="Endpoint injoignable (API indisponible)",
                details={"endpoint": endpoint_path, "error": str(exc)},
            )

        except requests.exceptions.Timeout:
            logger.warning("✗ Timeout endpoint %s", endpoint_path)
            return HealthStatus(
                name=endpoint_name,
                status="unreachable",
                description="Endpoint non répondu dans le délai imparti",
                details={"endpoint": endpoint_path, "error": "Timeout"},
            )

        except requests.exceptions.HTTPError as exc:
            status_code = exc.response.status_code if exc.response is not None else None
            if status_code == 429:
                retry_after = exc.response.headers.get("Retry-After") if exc.response is not None else None
                return HealthStatus(
                    name=endpoint_name,
                    status="rate_limited",
                    description="Limite de requêtes atteinte (HTTP 429)",
                    details={
                        "endpoint": endpoint_path,
                        "status_code": status_code,
                        "retry_after": retry_after,
                        "error": str(exc),
                    },
                )

            return HealthStatus(
                name=endpoint_name,
                status="error",
                description=f"Endpoint en erreur HTTP {status_code}",
                details={
                    "endpoint": endpoint_path,
                    "status_code": status_code,
                    "error": str(exc),
                },
            )

        except Exception as exc:
            logger.exception("✗ Erreur endpoint %s: %s", endpoint_path, exc)
            return HealthStatus(
                name=endpoint_name,
                status="error",
                description="Erreur inattendue pendant le contrôle d'endpoint",
                details={"endpoint": endpoint_path, "error": str(exc)},
            )

    def check_frequence_model_health(self) -> HealthStatus:
        """Compatibilité: vérifie l'endpoint santé de prédiction fréquence."""
        return self._check_prediction_endpoint_health(
            endpoint_path="/predictio_frequence/health",
            endpoint_name="Endpoint Prédiction Fréquence",
        )

    def check_severite_model_health(self) -> HealthStatus:
        """Compatibilité: vérifie l'endpoint santé de prédiction sévérité."""
        return self._check_prediction_endpoint_health(
            endpoint_path="/predictio_severite/health",
            endpoint_name="Endpoint Prédiction Sévérité",
        )

    def check_database_health(self) -> HealthStatus:
        """Vérifie l'état de santé de la base de données SQLite."""
        try:
            # Vérifier l'existence du fichier
            if not self.db_path.exists():
                logger.warning(f"✗ Fichier de base de données non trouvé: {self.db_path}")
                return HealthStatus(
                    name="Base de données",
                    status="error",
                    description=f"Le fichier de base de données n'existe pas: {self.db_path}",
                    details={
                        "db_path": str(self.db_path),
                        "exists": False,
                    },
                )

            # Vérifier la connectivité et lister les tables
            with sqlite3.connect(str(self.db_path), timeout=self.timeout) as conn:
                cursor = conn.cursor()

                # Récupérer les tables
                cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type='table';"
                )
                tables = [row[0] for row in cursor.fetchall()]

                # Récupérer les statistiques
                db_stats = {}
                for table_name in tables:
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
                    count = cursor.fetchone()[0]
                    db_stats[table_name] = count

                logger.debug(f"✓ Base de données opérationnelle. Tables: {tables}")

                return HealthStatus(
                    name="Base de données",
                    status="ok",
                    description=f"Base de données opérationnelle ({len(tables)} tables)",
                    details={
                        "db_path": str(self.db_path),
                        "exists": True,
                        "tables": tables,
                        "table_stats": db_stats,
                    },
                )

        except sqlite3.DatabaseError as exc:
            logger.warning(f"✗ Erreur base de données (fichier corrompu?): {exc}")
            return HealthStatus(
                name="Base de données",
                status="error",
                description="Erreur d'accès à la base de données (fichier peut être corrompu)",
                details={
                    "db_path": str(self.db_path),
                    "error": str(exc),
                },
            )

        except sqlite3.OperationalError as exc:
            logger.warning(f"✗ Erreur opérationnelle base de données: {exc}")
            return HealthStatus(
                name="Base de données",
                status="error",
                description="Erreur d'accès à la base de données",
                details={
                    "db_path": str(self.db_path),
                    "error": str(exc),
                },
            )

        except Exception as exc:
            logger.exception(f"✗ Erreur inattendue lors du check DB: {exc}")
            return HealthStatus(
                name="Base de données",
                status="error",
                description="Erreur inattendue lors de la vérification",
                details={
                    "db_path": str(self.db_path),
                    "error": str(exc),
                },
            )

    def check_all_health(self) -> dict:
        """Vérifie l'état de santé de tous les services."""
        logger.info("Vérification complète de l'état de santé...")

        main_api_status = self.check_main_api_health()
        statuses = {
            "main_api": main_api_status,
            "frequence_model": None,
            "severite_model": None,
            "database": self.check_database_health(),
        }

        # Limite les appels HTTP en cascade quand l'API principale est déjà en échec.
        if main_api_status.status == "rate_limited":
            details = main_api_status.details or {}
            statuses["frequence_model"] = HealthStatus(
                name="Endpoint Prédiction Fréquence",
                status="rate_limited",
                description="Vérification ignorée: API principale limitée (HTTP 429)",
                details={
                    "status_code": 429,
                    "retry_after": details.get("retry_after"),
                    "reason": "short_circuit_from_main_api",
                },
            )
            statuses["severite_model"] = HealthStatus(
                name="Endpoint Prédiction Sévérité",
                status="rate_limited",
                description="Vérification ignorée: API principale limitée (HTTP 429)",
                details={
                    "status_code": 429,
                    "retry_after": details.get("retry_after"),
                    "reason": "short_circuit_from_main_api",
                },
            )
        elif main_api_status.status == "unreachable":
            statuses["frequence_model"] = HealthStatus(
                name="Endpoint Prédiction Fréquence",
                status="unreachable",
                description="Vérification ignorée: API principale injoignable",
                details={"reason": "short_circuit_from_main_api"},
            )
            statuses["severite_model"] = HealthStatus(
                name="Endpoint Prédiction Sévérité",
                status="unreachable",
                description="Vérification ignorée: API principale injoignable",
                details={"reason": "short_circuit_from_main_api"},
            )
        else:
            statuses["frequence_model"] = self.check_frequence_model_health()
            statuses["severite_model"] = self.check_severite_model_health()

        # Résumé
        healthy_count = sum(1 for s in statuses.values() if s.is_healthy())
        total_count = len(statuses)

        logger.info(
            f"Résumé santé: {healthy_count}/{total_count} services sains"
        )

        return statuses
