"""Configuration centralisée pour l'application Streamlit."""

import os
from typing import Optional

# ==============================================================================
# THEME & COULEURS
# ==============================================================================

THEME = {
    "primary_color": "#1F77B4",
    "secondary_color": "#FF7F0E",
    "success_color": "#2CA02C",
    "warning_color": "#FF9800",
    "danger_color": "#D62728",
    "info_color": "#17A2B8",
    "background_color": "#F5F5F5",
    "text_color": "#333333",
    "border_color": "#DCDCDC",
}

# ==============================================================================
# ANT DESIGN CONFIG
# ==============================================================================

ANT_DESIGN_CONFIG = {
    "layout": {
        "colorBgContainer": "#FFFFFF",
        "colorPrimaryBg": "#E6F7FF",
        "borderRadius": 6,
    },
    "button": {
        "colorPrimary": THEME["primary_color"],
        "controlHeight": 32,
    },
    "form": {
        "labelColor": THEME["text_color"],
        "controlHeight": 32,
    },
}

# ==============================================================================
# APPLICATION METADATA
# ==============================================================================

APP_NAME = "Prime Estimator"
APP_ICON = "🛡️"
APP_LAYOUT = "wide"
APP_INITIAL_SIDEBAR_STATE = "expanded"

# ==============================================================================
# PAGES CONFIG
# ==============================================================================

PAGES = {
    "dashboard": {"icon": "house", "name": "Tableau de bord"},
    "contrat": {"icon": "file-earmark-text", "name": "Compose Contrat"},
    "inference": {"icon": "graph-up", "name": "Compose Inference"},
}

# ==============================================================================
# API ENDPOINTS
# ==============================================================================

# URL de base : utilise la variable d'env en prod, localhost sinon
API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")
API_TIMEOUT = 10

ENDPOINTS = {
    "predict_frequence": f"{API_BASE_URL}/predict_frequence",
    "predict_severite": f"{API_BASE_URL}/predict_severite",
    "health_frequence": f"{API_BASE_URL}/predictio_frequence/health",
    "health_severite": f"{API_BASE_URL}/predictio_severite/health",
    "contrats": f"{API_BASE_URL}/contrats",
}

# ==============================================================================
# SCHÉMA DES DONNÉES CONTRAT (pour formulaires et validation)
# ==============================================================================

# Valeurs possibles pour les champs catégoriques (extraites du jeu d'entraînement)
FIELD_OPTIONS: dict = {
    # --- Champs saisis manuellement par l'assureur ---
    "essence_vehicule": ["Gasoline", "Diesel", "Hybrid"],
    "type_vehicule": ["Tourism", "Commercial"],
    "sex_conducteur1": ["M", "F"],
    # --- Champs également saisis manuellement ---
    "type_contrat": ["Maxi", "Median1", "Median2", "Mini"],
    "utilisation": ["WorkPrivate", "AllTrips", "Professional", "Retired"],
    # --- Champs générés aléatoirement (mais listés pour validation) ---
    "freq_paiement": ["Monthly", "Quarterly", "Biannual", "Yearly"],
    "paiement": ["No", "Yes"],
    "conducteur2": ["No", "Yes"],
    "sex_conducteur2": ["M", "F"],
    "marque_vehicule": [
        "PEUGEOT",
        "RENAULT",
        "CITROEN",
        "VOLKSWAGEN",
        "BMW",
        "MERCEDES BENZ",
        "AUDI",
        "FORD",
        "TOYOTA",
        "HONDA",
        "NISSAN",
        "OPEL",
        "FIAT",
        "SEAT",
        "SKODA",
        "HYUNDAI",
        "KIA",
        "MAZDA",
        "MITSUBISHI",
        "VOLVO",
        "LAND ROVER",
        "JEEP",
        "DACIA",
        "ALFA ROMEO",
        "PORSCHE",
        "JAGUAR",
        "LEXUS",
        "SUBARU",
        "SUZUKI",
        "DAEWOO",
        "CHEVROLET",
        "CHRYSLER",
        "SAAB",
        "LANCIA",
        "SMART",
        "MINI",
        "SSANGYONG",
        "DAIHATSU",
        "ISUZU",
        "ROVER",
        "MG",
        "LOTUS",
        "BENTLEY",
        "CADILLAC",
        "DODGE",
        "HUMMER",
        "INFINITI",
        "LADA VAZ",
        "MORGAN",
        "PONTIAC",
        "PININFARINA",
    ],
}

# Plages numériques pour la génération aléatoire des champs automatiques
FIELD_RANGES: dict = {
    "bonus": (0.5, 1.0, 0.05),  # (min, max, step)
    "duree_contrat": (1, 36),  # (min, max) en mois
    "anciennete_info": (0, 20),
    "age_conducteur2": (18, 85),
    "anciennete_permis2": (0, 60),
    "anciennete_vehicule": (0.0, 30.0),
    "din_vehicule": (50, 300),
    "debut_vente_vehicule": (1, 20),  # années depuis mise en vente
    "fin_vente_vehicule": (0, 15),
    "vitesse_vehicule": (120, 280),
    "poids_vehicule": (800, 2500),
}

SCHEMA_TEST_CONTRATS: dict = {
    "index": Optional[int],
    "bonus": Optional[float],
    "type_contrat": Optional[str],
    "duree_contrat": Optional[int],
    "anciennete_info": Optional[int],
    "freq_paiement": Optional[str],
    "paiement": Optional[str],
    "utilisation": Optional[str],
    "code_postal": Optional[str],
    "conducteur2": Optional[str],
    "age_conducteur1": Optional[int],
    "age_conducteur2": Optional[int],
    "sex_conducteur1": Optional[str],
    "sex_conducteur2": Optional[str],
    "anciennete_permis1": Optional[int],
    "anciennete_permis2": Optional[int],
    "anciennete_vehicule": Optional[float],
    "cylindre_vehicule": Optional[int],
    "din_vehicule": Optional[int],
    "essence_vehicule": Optional[str],
    "marque_vehicule": Optional[str],
    "modele_vehicule": Optional[str],
    "debut_vente_vehicule": Optional[int],
    "fin_vente_vehicule": Optional[int],
    "vitesse_vehicule": Optional[int],
    "type_vehicule": Optional[str],
    "prix_vehicule": Optional[int],
    "poids_vehicule": Optional[int],
}

# ==============================================================================
# DATABASE
# ==============================================================================

DATABASE_URL = "sqlite:///db/app.db"
DATABASE_ECHO = False

# ==============================================================================
# LOGGING
# ==============================================================================

LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# ==============================================================================
# FEATURE FLAGS
# ==============================================================================

FEATURES = {
    "enable_export": True,
    "enable_batch_prediction": True,
    "enable_model_comparison": False,
}
