from fastapi import APIRouter
from src.api.backend.services.contrat_ml_service import MLService

ml_router = APIRouter()
ml_service = MLService()

@ml_router.post("/predict")
def predict(data: dict):
    prediction = ml_service.predict(data)
    return {"prediction": prediction}