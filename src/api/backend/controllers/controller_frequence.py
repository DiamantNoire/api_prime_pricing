# --*- coding: utf-8 -*-
# =============================================
#------ IMPORTATIONS DES LIBRAIRIES ----------#
# =============================================
import json
import os
import pandas as pd
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from src.api.frontend.configs import SCHEMA_TEST_CONTRATS
from src.models.fonctions_utiles import Model_Prediction_Frequence

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


def _build_frequence_model() -> Model_Prediction_Frequence:
    """Instantiate predictor from JSON metadata and trained pickle artifact."""
    model = Model_Prediction_Frequence()
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
    json_path = os.path.join(project_root, "output_models", "modeles", "model_frequence.json")
    pickle_path = os.path.join(project_root, "output_models", "modeles", "model_frequence.pickle")

    if not os.path.exists(json_path):
        raise HTTPException(status_code=500, detail=f"Model JSON introuvable: {json_path}")

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            meta = json.load(f)
        model.selected_features_ = meta.get("selected_features_", []) or []
        model.fill_values_ = meta.get("fill_values_", {}) or {}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Erreur lecture model_frequence.json: {exc}")

    loaded = model.load_model(pickle_path)
    if loaded is None:
        raise HTTPException(
            status_code=500,
            detail=(
                "Impossible de charger model_frequence.pickle. "
                "Le JSON est bien lu, mais le pipeline entraîné n'est pas disponible."
            ),
        )

    return model

@router.post("/predict_frequence", response_model=FrequenceOutput)
def prediction(input_data: FrequenceInput):
    df = pd.DataFrame([input_data.model_dump(exclude_none=True)])
    model = _build_frequence_model()
    y_pred = model.predict(df)
    return FrequenceOutput(prediction=float(y_pred[0]))