# --*- coding: utf-8 -*-
# =============================================
# ------ IMPORTATIONS DES LIBRAIRIES ----------#
# =============================================
import os
import pandas as pd
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from src.api.frontend.configs import SCHEMA_TEST_CONTRATS
from src.models.fonctions_utiles import Model_Prediction_Frequence


# =============================================
# ------ CLASSES ----------#
# =============================================
class FrequenceInput(BaseModel):
    """
    Modèle d'entrée pour la prédiction de la fréquence d'un contrat d'assurance auto.

    Args:
        bonus (Optional[float]): Bonus-malus du contrat.
        type_contrat (Optional[str]): Type de contrat souscrit.
        duree_contrat (Optional[int]): Durée du contrat en mois.
        anciennete_info (Optional[int]): Ancienneté de l'information sur le contrat.
        freq_paiement (Optional[str]): Fréquence de paiement.
        paiement (Optional[str]): Statut du paiement.
        utilisation (Optional[str]): Type d'utilisation du véhicule.
        code_postal (Optional[str]): Code postal du souscripteur.
        conducteur2 (Optional[str]): Présence d'un second conducteur.
        age_conducteur1 (Optional[int]): Âge du conducteur principal.
        age_conducteur2 (Optional[int]): Âge du second conducteur.
        sex_conducteur1 (Optional[str]): Sexe du conducteur principal.
        sex_conducteur2 (Optional[str]): Sexe du second conducteur.
        anciennete_permis1 (Optional[int]): Ancienneté du permis du conducteur principal.
        anciennete_permis2 (Optional[int]): Ancienneté du permis du second conducteur.
        anciennete_vehicule (Optional[float]): Ancienneté du véhicule.
        cylindre_vehicule (Optional[int]): Cylindrée du véhicule.
        din_vehicule (Optional[int]): DIN du véhicule.
        essence_vehicule (Optional[str]): Type de carburant.
        marque_vehicule (Optional[str]): Marque du véhicule.
        modele_vehicule (Optional[str]): Modèle du véhicule.
        debut_vente_vehicule (Optional[int]): Année de début de commercialisation.
        fin_vente_vehicule (Optional[int]): Année de fin de commercialisation.
        vitesse_vehicule (Optional[int]): Vitesse maximale du véhicule.
        type_vehicule (Optional[str]): Type de véhicule.
        prix_vehicule (Optional[int]): Prix du véhicule.
        poids_vehicule (Optional[int]): Poids du véhicule.
    """

    bonus: Optional[float] = None
    type_contrat: Optional[str] = None
    duree_contrat: Optional[int] = None
    anciennete_info: Optional[int] = None
    freq_paiement: Optional[str] = None
    paiement: Optional[str] = None
    utilisation: Optional[str] = None
    code_postal: Optional[str] = None
    conducteur2: Optional[str] = None
    age_conducteur1: Optional[int] = None
    age_conducteur2: Optional[int] = None
    sex_conducteur1: Optional[str] = None
    sex_conducteur2: Optional[str] = None
    anciennete_permis1: Optional[int] = None
    anciennete_permis2: Optional[int] = None
    anciennete_vehicule: Optional[float] = None
    cylindre_vehicule: Optional[int] = None
    din_vehicule: Optional[int] = None
    essence_vehicule: Optional[str] = None
    marque_vehicule: Optional[str] = None
    modele_vehicule: Optional[str] = None
    debut_vente_vehicule: Optional[int] = None
    fin_vente_vehicule: Optional[int] = None
    vitesse_vehicule: Optional[int] = None
    type_vehicule: Optional[str] = None
    prix_vehicule: Optional[int] = None
    poids_vehicule: Optional[int] = None

    __schema__ = SCHEMA_TEST_CONTRATS


class FrequenceOutput(BaseModel):
    """
    Modèle de sortie pour la prédiction de la fréquence.

    Args:
        prediction (Optional[float]): Valeur prédite de la fréquence d'accident.

    Returns:
        dict: Un dictionnaire contenant la prédiction de la fréquence.
    """

    prediction: Optional[float] = None


# =============================================
# -------- CHARGEMENT DES DONNEES -------------#
# =============================================
DATA_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
)

# --- Input ---
MODEL_FREQUENCE_PATH = os.path.join(
    PROJECT_ROOT, "output_models", "modeles", "model_frequence.json"
)
os.makedirs(os.path.dirname(MODEL_FREQUENCE_PATH), exist_ok=True)

# =============================================
# ------ ROUTAGE ----------#
# =============================================

router = APIRouter()


def _build_frequence_model() -> Model_Prediction_Frequence:
    """Instantiate predictor from complete pre-trained JSON artifact."""
    model = Model_Prediction_Frequence()

    if not os.path.exists(MODEL_FREQUENCE_PATH):
        raise HTTPException(
            status_code=500, detail=f"Model JSON introuvable: {MODEL_FREQUENCE_PATH}"
        )

    try:
        loaded = model.load_model(MODEL_FREQUENCE_PATH)
        if not isinstance(loaded, dict) or not loaded.get("xgb_model_json"):
            raise HTTPException(
                status_code=500,
                detail=(
                    "Le JSON de fréquence chargé n'est pas un artefact complet. "
                    "Relancer l'entraînement pour générer 'xgb_model_json'."
                ),
            )
    except Exception as exc:
        raise HTTPException(
            status_code=500, detail=f"Erreur chargement artefact frequence JSON: {exc}"
        )

    return model


# Chargement unique du modèle entraîné au démarrage du module.
FREQUENCE_MODEL: Optional[Model_Prediction_Frequence] = None
FREQUENCE_MODEL_LOAD_ERROR: Optional[str] = None

try:
    FREQUENCE_MODEL = _build_frequence_model()
except HTTPException as exc:
    FREQUENCE_MODEL_LOAD_ERROR = str(exc.detail)
except Exception as exc:
    FREQUENCE_MODEL_LOAD_ERROR = str(exc)


@router.get("/predictio_frequence/health")
def health_predictio_frequence():
    return {
        "status": "ok" if FREQUENCE_MODEL is not None else "error",
        "model_loaded": FREQUENCE_MODEL is not None,
        "model_path": MODEL_FREQUENCE_PATH,
        "model_file_exists": os.path.exists(MODEL_FREQUENCE_PATH),
        "detail": FREQUENCE_MODEL_LOAD_ERROR,
    }


@router.post("/predict_frequence", response_model=FrequenceOutput)
def prediction(input_data: FrequenceInput):
    """
    Prédiction de la fréquence d'un contrat d'assurance auto.

    Paramètres
    ----------
    input_data : FrequenceInput
        Données d'entrée du contrat (voir modèle Pydantic).

    Retour
    ------
    FrequenceOutput
        Prédiction de la fréquence (float).
    """
    if FREQUENCE_MODEL is None:
        raise HTTPException(
            status_code=500,
            detail=(
                "Le modèle de fréquence n'est pas disponible. "
                f"Détail: {FREQUENCE_MODEL_LOAD_ERROR or 'erreur inconnue'}"
            ),
        )

    df = pd.DataFrame([input_data.model_dump(exclude_none=True)])
    y_pred = FREQUENCE_MODEL.predict(df)
    return FrequenceOutput(prediction=float(y_pred[0]))
