# --*- coding: utf-8 -*-
# =============================================
# Schémas des tables SQLite — colonnes : type Optional
# Utilisés comme base pour les modèles Pydantic des controllers.
# =============================================
from typing import Optional

# --- Table : historique_contrats (train.csv) ---
SCHEMA_HISTORIQUE_CONTRATS: dict = {
    "index":                  Optional[int],
    "id_client":              Optional[str],
    "id_vehicule":            Optional[str],
    "id_contrat":             Optional[str],
    "bonus":                  Optional[float],
    "type_contrat":           Optional[str],
    "duree_contrat":          Optional[int],
    "anciennete_info":        Optional[int],
    "freq_paiement":          Optional[str],
    "paiement":               Optional[str],
    "utilisation":            Optional[str],
    "code_postal":            Optional[str],
    "conducteur2":            Optional[str],
    "age_conducteur1":        Optional[int],
    "age_conducteur2":        Optional[int],
    "sex_conducteur1":        Optional[str],
    "sex_conducteur2":        Optional[str],
    "anciennete_permis1":     Optional[int],
    "anciennete_permis2":     Optional[int],
    "anciennete_vehicule":    Optional[float],
    "cylindre_vehicule":      Optional[int],
    "din_vehicule":           Optional[int],
    "essence_vehicule":       Optional[str],
    "marque_vehicule":        Optional[str],
    "modele_vehicule":        Optional[str],
    "debut_vente_vehicule":   Optional[int],
    "fin_vente_vehicule":     Optional[int],
    "vitesse_vehicule":       Optional[int],
    "type_vehicule":          Optional[str],
    "prix_vehicule":          Optional[int],
    "poids_vehicule":         Optional[int],
    "nombre_sinistres":       Optional[int],
    "montant_sinistre":       Optional[float],
}

# --- Table : test_contrats (test.csv) — features d'entrée pour la prédiction ---
SCHEMA_TEST_CONTRATS: dict = {
    "index":                  Optional[int],
    "bonus":                  Optional[float],
    "type_contrat":           Optional[str],
    "duree_contrat":          Optional[int],
    "anciennete_info":        Optional[int],
    "freq_paiement":          Optional[str],
    "paiement":               Optional[str],
    "utilisation":            Optional[str],
    "code_postal":            Optional[str],
    "conducteur2":            Optional[str],
    "age_conducteur1":        Optional[int],
    "age_conducteur2":        Optional[int],
    "sex_conducteur1":        Optional[str],
    "sex_conducteur2":        Optional[str],
    "anciennete_permis1":     Optional[int],
    "anciennete_permis2":     Optional[int],
    "anciennete_vehicule":    Optional[float],
    "cylindre_vehicule":      Optional[int],
    "din_vehicule":           Optional[int],
    "essence_vehicule":       Optional[str],
    "marque_vehicule":        Optional[str],
    "modele_vehicule":        Optional[str],
    "debut_vente_vehicule":   Optional[int],
    "fin_vente_vehicule":     Optional[int],
    "vitesse_vehicule":       Optional[int],
    "type_vehicule":          Optional[str],
    "prix_vehicule":          Optional[int],
    "poids_vehicule":         Optional[int],
}

# --- Table : predictions ---
SCHEMA_PREDICTIONS: dict = {
    "index":         Optional[int],
    "pred_freq":     Optional[float],
    "pred_severite": Optional[float],
    "pred_prime":    Optional[float],
}
