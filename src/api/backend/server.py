# --*- coding: utf-8 -*-
# =============================================
#------ IMPORTATIONS DES LIBRAIRIES ----------#
# =============================================
import logging
import os
from contextlib import asynccontextmanager

import pandas as pd
from fastapi import FastAPI
from fastapi.responses import Response

from src.api.backend.controllers.controller_frequence import FrequenceInput
from src.api.backend.controllers.controller_severite import router as severite_router
from src.api.backend.controllers.controller_frequence import router as frequence_router
from src.api.backend.model_runtime import load_frequence_model, load_severite_model


logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
LOGGER = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    frequence_model, frequence_error = load_frequence_model()
    severite_model, severite_error = load_severite_model()

    app.state.frequence_model = frequence_model
    app.state.frequence_model_load_error = frequence_error
    app.state.severite_model = severite_model
    app.state.severite_model_load_error = severite_error

    if frequence_error:
        LOGGER.warning("Chargement frequence incomplet: %s", frequence_error)
    if severite_error:
        LOGGER.warning("Chargement severite incomplet: %s", severite_error)

    yield

# =============================================
#------ AJOUT DES ENDPOINTS ----------#
# =============================================
app = FastAPI(
    title="API Prime Pricing",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(severite_router)
app.include_router(frequence_router)

@app.get("/")
def read_root():
    return {"message": "API Prime Pricing is running"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/predict_price")
def predict_price(input_data: FrequenceInput):
    frequence_model = getattr(app.state, "frequence_model", None)
    severite_model = getattr(app.state, "severite_model", None)

    if frequence_model is None or severite_model is None:
        return {
            "status": "error",
            "detail": "Les modeles frequence et severite doivent etre charges pour calculer la prime.",
        }

    df = pd.DataFrame([input_data.model_dump(exclude_none=True)])
    frequence = float(frequence_model.predict(df)[0])
    severite = float(severite_model.predict(df)[0])
    return {
        "status": "ok",
        "frequence": frequence,
        "severite": severite,
        "prime": frequence * severite,
    }

@app.get("/favicon.ico")
def favicon():
    return Response(status_code=204)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.api.backend.server:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8000")),
        reload=os.getenv("APP_RELOAD", "false").lower() == "true",
    )
