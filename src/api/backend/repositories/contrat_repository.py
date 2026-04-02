from __future__ import annotations

import logging
import sqlite3
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class ContratRepository:
    """Accès DB sécurisé à la table historique_contrats."""

    TABLE_NAME = "historique_contrats"
    COLUMNS = [
        "id_client",
        "id_vehicule",
        "id_contrat",
        "bonus",
        "type_contrat",
        "duree_contrat",
        "anciennete_info",
        "freq_paiement",
        "paiement",
        "utilisation",
        "code_postal",
        "conducteur2",
        "age_conducteur1",
        "age_conducteur2",
        "sex_conducteur1",
        "sex_conducteur2",
        "anciennete_permis1",
        "anciennete_permis2",
        "anciennete_vehicule",
        "cylindre_vehicule",
        "din_vehicule",
        "essence_vehicule",
        "marque_vehicule",
        "modele_vehicule",
        "debut_vente_vehicule",
        "fin_vente_vehicule",
        "vitesse_vehicule",
        "type_vehicule",
        "prix_vehicule",
        "poids_vehicule",
        "nombre_sinistres",
        "montant_sinistre",
    ]

    def __init__(self, db_path: str = "db/prime_pricing.sqlite"):
        """
        Initialise le repository avec le chemin de la base SQLite.

        Args:
            db_path (str): Chemin du fichier SQLite (par défaut "db/prime_pricing.sqlite").
        """
        self.db_path = Path(db_path)

    def _connect(self) -> sqlite3.Connection:
        """
        Ouvre une connexion SQLite avec row_factory configuré.

        Returns:
            sqlite3.Connection: Connexion à la base de données.
        """
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _table_exists(self, conn: sqlite3.Connection) -> bool:
        """
        Vérifie si la table principale existe dans la base.

        Args:
            conn (sqlite3.Connection): Connexion SQLite ouverte.

        Returns:
            bool: True si la table existe, False sinon.
        """
        cur = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
            (self.TABLE_NAME,),
        )
        return cur.fetchone() is not None

    def _row_to_dict(self, row: sqlite3.Row) -> dict[str, Any]:
        """
        Convertit une ligne SQLite en dictionnaire Python.

        Args:
            row (sqlite3.Row): Ligne issue d'une requête.

        Returns:
            dict[str, Any]: Dictionnaire clé-valeur.
        """
        return {k: row[k] for k in row.keys()}

    def find_recent(self, limit: int = 20) -> list[dict[str, Any]]:
        """
        Récupère les derniers contrats insérés dans la table.

        Args:
            limit (int): Nombre maximum de lignes à retourner (défaut 20).

        Returns:
            list[dict[str, Any]]: Liste de contrats récents.
        """
        with self._connect() as conn:
            if not self._table_exists(conn):
                logger.warning("Table %s absente", self.TABLE_NAME)
                return []

            sql = (
                f"SELECT rowid as row_id, {', '.join(self.COLUMNS)} "
                f"FROM {self.TABLE_NAME} ORDER BY rowid DESC LIMIT ?"
            )
            rows = conn.execute(sql, (limit,)).fetchall()
            return [self._row_to_dict(row) for row in rows]

    def find_by_id_contrat(self, id_contrat: str) -> dict[str, Any] | None:
        """
        Recherche un contrat par son identifiant unique.

        Args:
            id_contrat (str): Identifiant du contrat recherché.

        Returns:
            dict[str, Any] | None: Contrat trouvé ou None si absent.
        """
        with self._connect() as conn:
            if not self._table_exists(conn):
                return None

            sql = (
                f"SELECT rowid as row_id, {', '.join(self.COLUMNS)} "
                f"FROM {self.TABLE_NAME} WHERE id_contrat = ? LIMIT 1"
            )
            row = conn.execute(sql, (id_contrat,)).fetchone()
            return self._row_to_dict(row) if row else None

    def insert(self, payload: dict[str, Any]) -> dict[str, Any]:
        """
        Insère un nouveau contrat dans la table.

        Args:
            payload (dict[str, Any]): Dictionnaire contenant toutes les colonnes requises.

        Returns:
            dict[str, Any]: Contrat inséré (avec row_id).
        """
        columns = ", ".join(self.COLUMNS)
        placeholders = ", ".join(["?" for _ in self.COLUMNS])
        values = tuple(payload[col] for col in self.COLUMNS)

        with self._connect() as conn:
            if not self._table_exists(conn):
                raise RuntimeError(f"Table {self.TABLE_NAME} introuvable")

            sql = f"INSERT INTO {self.TABLE_NAME} ({columns}) VALUES ({placeholders})"
            cur = conn.execute(sql, values)
            conn.commit()
            row_id = cur.lastrowid

            row = conn.execute(
                (
                    f"SELECT rowid as row_id, {', '.join(self.COLUMNS)} "
                    f"FROM {self.TABLE_NAME} WHERE rowid = ?"
                ),
                (row_id,),
            ).fetchone()
            return self._row_to_dict(row)

    def update_by_id_contrat(
        self, id_contrat: str, payload: dict[str, Any]
    ) -> dict[str, Any] | None:
        """
        Met à jour un contrat existant à partir de son id_contrat.

        Args:
            id_contrat (str): Identifiant du contrat à mettre à jour.
            payload (dict[str, Any]): Nouvelles valeurs pour les colonnes (sauf id_contrat).

        Returns:
            dict[str, Any] | None: Contrat mis à jour ou None si non trouvé.
        """
        assignments = ", ".join(
            [f"{col} = ?" for col in self.COLUMNS if col != "id_contrat"]
        )
        values = tuple(payload[col] for col in self.COLUMNS if col != "id_contrat") + (
            id_contrat,
        )

        with self._connect() as conn:
            if not self._table_exists(conn):
                raise RuntimeError(f"Table {self.TABLE_NAME} introuvable")

            sql = f"UPDATE {self.TABLE_NAME} SET {assignments} WHERE id_contrat = ?"
            cur = conn.execute(sql, values)
            conn.commit()

            if cur.rowcount == 0:
                return None

            return self.find_by_id_contrat(payload["id_contrat"])
