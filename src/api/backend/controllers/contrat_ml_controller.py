import logging
from fastapi import APIRouter
from src.api.backend.services.contrat_ml_service import MLService

LOGGER = logging.getLogger(__name__)

ml_router = APIRouter()
ml_service = MLService()

@ml_router.post("/predict")
def predict(data: dict):
    LOGGER.info("POST /predict")
    prediction = ml_service.predict(data)
    return {"prediction": prediction}