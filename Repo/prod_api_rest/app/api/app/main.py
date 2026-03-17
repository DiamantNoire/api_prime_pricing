from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers.prediction import router as prediction_router
from app.services.predictor_service import predictor_service


@asynccontextmanager
async def lifespan(_: FastAPI):
    try:
        predictor_service.load()
    except Exception:
        # Le service reste demarrable meme si les artefacts ne sont pas disponibles.
        pass
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(prediction_router, prefix=settings.api_prefix)
