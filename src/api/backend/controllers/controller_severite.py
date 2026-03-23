# --*- coding: utf-8 -*-
# =============================================
#------ IMPORTATIONS DES LIBRAIRIES ----------#
# =============================================
from typing import Optional

import pandas as pd
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from src.api.backend.model_runtime import MODEL_SEVERITE_PATH
from src.api.frontend.configs import SCHEMA_TEST_CONTRATS
from src.models.fonctions_utiles import Model_Prediction_Severite

# =============================================
#------ CLASSES ----------#
# =============================================
class SeveriteInput(BaseModel):
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

    # Schéma de référence (pour inspection/documentation)
    __schema__ = SCHEMA_TEST_CONTRATS

class SeveriteOutput(BaseModel):
    prediction: Optional[float] = None

# =============================================
#------ ROUTAGE ----------#
# =============================================
router = APIRouter()

@router.get("/predictio_severite/health")
def health_predictio_severite(request: Request):
    model = getattr(request.app.state, "severite_model", None)
    load_error = getattr(request.app.state, "severite_model_load_error", None)

    return {
        "status": "ok" if model is not None else "error",
        "model_loaded": model is not None,
        "model_path": str(MODEL_SEVERITE_PATH),
        "model_file_exists": MODEL_SEVERITE_PATH.exists(),
        "detail": load_error,
    }

@router.post("/predict_severite", response_model=SeveriteOutput)
def prediction(input_data: SeveriteInput, request: Request):
    model: Optional[Model_Prediction_Severite] = getattr(request.app.state, "severite_model", None)
    load_error = getattr(request.app.state, "severite_model_load_error", None)

    if model is None:
        raise HTTPException(
            status_code=500,
            detail=(
                "Le modele de severite n'est pas disponible. "
                f"Detail: {load_error or 'erreur inconnue'}"
            ),
        )

    df = pd.DataFrame([input_data.model_dump(exclude_none=True)])
    y_pred = model.predict(df)
    return SeveriteOutput(prediction=float(y_pred[0]))