"""Configuration centralisée pour l'application Streamlit."""

import os

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

APP_NAME = "Prime Pricing - User Application"
APP_ICON = "📊"
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
