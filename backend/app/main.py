from contextlib import asynccontextmanager
import os
from typing import Annotated

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from app.database import get_prediction, init_db, list_predictions, save_prediction
from app.ml_model import get_model_metadata
from app.recommendation import predict_recommendation
from app.schemas import (
    HealthResponse,
    HistoryItem,
    ModelInfoResponse,
    PredictionRequest,
    PredictionResponse,
    WeatherResponse,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Potager EHPAD Tomate API",
    description="API V0 pour predire la viabilite de plantation de tomates.",
    version="0.1.0",
    lifespan=lifespan,
)

cors_origins = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins or ["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", service="potager-ehpad-backend")


@app.post("/predict", response_model=PredictionResponse, status_code=201)
def predict(payload: PredictionRequest) -> PredictionResponse:
    result = predict_recommendation(payload)
    return save_prediction(payload, result)


@app.get("/history", response_model=list[HistoryItem])
def history(
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
) -> list[HistoryItem]:
    return list_predictions(limit=limit)


@app.get("/history/{prediction_id}", response_model=HistoryItem)
def history_item(prediction_id: int) -> HistoryItem:
    prediction = get_prediction(prediction_id)
    if prediction is None:
        raise HTTPException(status_code=404, detail="Prediction not found")
    return prediction


@app.get("/model/info", response_model=ModelInfoResponse)
def model_info() -> ModelInfoResponse:
    metadata = get_model_metadata()
    return ModelInfoResponse(
        name=metadata["name"],
        version=metadata["version"],
        type=metadata["type"],
        status=metadata["status"],
        classes=["viable", "attendre", "non_viable"],
        metrics=metadata.get("metrics", {}),
        model_path=metadata.get("path"),
    )


@app.get("/weather", response_model=WeatherResponse)
def weather(
    location: Annotated[str, Query(min_length=1, max_length=120)] = "Rennes",
) -> WeatherResponse:
    return WeatherResponse(
        location=location,
        source="manual_v0",
        status="not_integrated",
        message="La V0 accepte les donnees meteo saisies manuellement dans le formulaire.",
    )
