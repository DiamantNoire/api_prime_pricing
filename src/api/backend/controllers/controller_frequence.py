# --*- coding: utf-8 -*-
# =============================================
#------ IMPORTATIONS DES LIBRAIRIES ----------#
# =============================================
import logging
from typing import Optional

import pandas as pd
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from src.api.backend.model_runtime import MODEL_FREQUENCE_PATH
from src.api.frontend.configs import SCHEMA_TEST_CONTRATS
from src.models.fonctions_utiles import Model_Prediction_Frequence

LOGGER = logging.getLogger(__name__)

# =============================================
#------ CLASSES ----------#
# =============================================
class FrequenceInput(BaseModel):
    bonus:                  Optional[float] = None
    type_contrat:           Optional[str]   = None
    duree_contrat:          Optional[int]   = None
    anciennete_info:        Optional[int]   = None
    freq_paiement:          Optional[str]   = None
    paiement:               Optional[str]   = None
    utilisation:            Optional[str]   = None
    code_postal:            Optional[str]   = None
    conducteur2:            Optional[str]   = None
    age_conducteur1:        Optional[int]   = None
    age_conducteur2:        Optional[int]   = None
    sex_conducteur1:        Optional[str]   = None
    sex_conducteur2:        Optional[str]   = None
    anciennete_permis1:     Optional[int]   = None
    anciennete_permis2:     Optional[int]   = None
    anciennete_vehicule:    Optional[float] = None
    cylindre_vehicule:      Optional[int]   = None
    din_vehicule:           Optional[int]   = None
    essence_vehicule:       Optional[str]   = None
    marque_vehicule:        Optional[str]   = None
    modele_vehicule:        Optional[str]   = None
    debut_vente_vehicule:   Optional[int]   = None
    fin_vente_vehicule:     Optional[int]   = None
    vitesse_vehicule:       Optional[int]   = None
    type_vehicule:          Optional[str]   = None
    prix_vehicule:          Optional[int]   = None
    poids_vehicule:         Optional[int]   = None

    __schema__ = SCHEMA_TEST_CONTRATS

class FrequenceOutput(BaseModel):
    prediction: Optional[float] = None

# =============================================
#------ ROUTAGE ----------#
# =============================================

router = APIRouter()


@router.get("/predictio_frequence/health")
def health_predictio_frequence(request: Request):
    LOGGER.info("GET /predictio_frequence/health")
    model = getattr(request.app.state, "frequence_model", None)
    load_error = getattr(request.app.state, "frequence_model_load_error", None)

    return {
        "status": "ok" if model is not None else "error",
        "model_loaded": model is not None,
        "model_path": str(MODEL_FREQUENCE_PATH),
        "model_file_exists": MODEL_FREQUENCE_PATH.exists(),
        "detail": load_error,
    }

@router.post("/predict_frequence", response_model=FrequenceOutput)
def prediction(input_data: FrequenceInput, request: Request):
    LOGGER.info("POST /predict_frequence")
    model: Optional[Model_Prediction_Frequence] = getattr(request.app.state, "frequence_model", None)
    load_error = getattr(request.app.state, "frequence_model_load_error", None)

    if model is None:
        raise HTTPException(
            status_code=500,
            detail=(
                "Le modele de frequence n'est pas disponible. "
                f"Detail: {load_error or 'erreur inconnue'}"
            ),
        )

    df = pd.DataFrame([input_data.model_dump(exclude_none=True)])
    y_pred = model.predict(df)
    return FrequenceOutput(prediction=float(y_pred[0]))