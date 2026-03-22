# --*- coding: utf-8 -*-
# =============================================
#------ IMPORTATIONS DES LIBRAIRIES ----------#
# =============================================
import pandas as pd
from typing import Optional
from fastapi import APIRouter
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

@router.post("/predict_frequence", response_model=FrequenceOutput)
def prediction(input_data: FrequenceInput):
    df = pd.DataFrame([input_data.model_dump()])
    y_pred = Model_Prediction_Frequence().predict(df)
    return FrequenceOutput(prediction=float(y_pred[0]))