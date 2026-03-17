from typing import Any, Dict, List

from pydantic import BaseModel, Field


class PredictionRequest(BaseModel):
    features: Dict[str, Any] = Field(
        ..., description="Champs d'entree pour un contrat a predire"
    )


class BatchPredictionRequest(BaseModel):
    items: List[PredictionRequest] = Field(
        ..., description="Liste d'observations a predire"
    )


class PredictionResponse(BaseModel):
    frequence_probabilite: float
    severite_prediction: float
    prime_prediction: float


class BatchPredictionResponse(BaseModel):
    predictions: List[PredictionResponse]
