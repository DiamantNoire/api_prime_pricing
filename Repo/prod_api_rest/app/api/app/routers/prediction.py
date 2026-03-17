from fastapi import APIRouter, HTTPException

from app.schemas import (
    BatchPredictionRequest,
    BatchPredictionResponse,
    PredictionRequest,
    PredictionResponse,
)
from app.services.predictor_service import predictor_service

router = APIRouter(tags=["prediction"])


@router.get("/health")
def health() -> dict:
    return {"status": "ok"}


@router.get("/ready")
def ready() -> dict:
    return {"ready": predictor_service.is_ready()}


@router.post("/predict", response_model=PredictionResponse)
def predict(payload: PredictionRequest) -> PredictionResponse:
    try:
        result = predictor_service.predict(payload.features)
        return PredictionResponse(**result.__dict__)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/predict/batch", response_model=BatchPredictionResponse)
def predict_batch(payload: BatchPredictionRequest) -> BatchPredictionResponse:
    try:
        results = predictor_service.predict_batch(item.features for item in payload.items)
        return BatchPredictionResponse(
            predictions=[PredictionResponse(**result.__dict__) for result in results]
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
