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


def _build_severite_model() -> Model_Prediction_Severite:
    """Instantiate predictor from JSON metadata and trained pickle artifact."""
    model = Model_Prediction_Severite()
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
    json_path = os.path.join(project_root, "output_models", "modeles", "model_severite.json")
    pickle_path = os.path.join(project_root, "output_models", "modeles", "model_severite.pickle")

    if not os.path.exists(json_path):
        raise HTTPException(status_code=500, detail=f"Model JSON introuvable: {json_path}")

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            meta = json.load(f)
        model.selected_features_ = meta.get("selected_features_", []) or []
        model.fill_values_ = meta.get("fill_values_", {}) or {}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Erreur lecture model_severite.json: {exc}")

    loaded = model.load_model(pickle_path)
    if loaded is None:
        raise HTTPException(
            status_code=500,
            detail=(
                "Impossible de charger model_severite.pickle. "
                "Le JSON est bien lu, mais le pipeline entraîné n'est pas disponible."
            ),
        )

    return model

@router.post("/predict_severite", response_model=SeveriteOutput)
def prediction(input_data: SeveriteInput):
    df = pd.DataFrame([input_data.model_dump(exclude_none=True)])
    model = _build_severite_model()
    y_pred = model.predict(df)
    return SeveriteOutput(prediction=float(y_pred[0]))