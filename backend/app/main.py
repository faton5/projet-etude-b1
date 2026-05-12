from contextlib import asynccontextmanager
import asyncio
import logging
from datetime import datetime
from typing import Annotated

from fastapi import FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import (
    check_database,
    get_prediction,
    init_db,
    list_predictions,
    save_prediction,
    upsert_model_version,
)
from app.garden_profile import garden_profile_store
from app.ml_model import get_model_metadata
from app.mqtt_consumer import iot_state, mqtt_consumer
from app.recommendation import predict_recommendation
from app.schemas import (
    HealthResponse,
    GardenProfile,
    HistoryItem,
    IotLiveResponse,
    IotPredictionRequest,
    ModelInfoResponse,
    PredictionRequest,
    PredictionResponse,
    WeatherResponse,
)
from app.weather import WeatherServiceError, get_weather_forecast


settings = get_settings()
logging.basicConfig(
    level=settings.log_level.upper(),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("potager.api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    _sync_model_version()
    mqtt_consumer.start()
    yield
    mqtt_consumer.stop()


app = FastAPI(
    title="Potager EHPAD Tomate API",
    description="API V0 pour predire la viabilite de plantation de tomates.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    metadata = get_model_metadata()
    snapshot = iot_state.snapshot()
    return HealthResponse(
        api="ok",
        mqtt=snapshot.mqtt_status,
        model="loaded" if metadata["status"] == "xgboost_loaded" else "fallback_rules",
        database="ok" if check_database() else "error",
        websocket="ok",
        demo_mode=settings.demo_mode,
    )


@app.get("/garden/profile", response_model=GardenProfile)
def garden_profile() -> GardenProfile:
    return garden_profile_store.get()


@app.put("/garden/profile", response_model=GardenProfile)
def update_garden_profile(profile: GardenProfile) -> GardenProfile:
    return garden_profile_store.update(profile)


@app.post("/predict", response_model=PredictionResponse, status_code=201)
def predict(payload: PredictionRequest) -> PredictionResponse:
    result = predict_recommendation(payload)
    return save_prediction(payload, result)


@app.post("/predict/iot", response_model=PredictionResponse, status_code=201)
def predict_with_iot(payload: IotPredictionRequest) -> PredictionResponse:
    snapshot = iot_state.snapshot()
    missing = []
    if snapshot.soil_humidity is None:
        missing.append("soil_humidity")
    if snapshot.water_usage is None:
        missing.append("water_usage")
    if snapshot.irrigation is None:
        missing.append("irrigation")
    if missing:
        raise HTTPException(
            status_code=409,
            detail=f"Donnees IoT manquantes: {', '.join(missing)}",
        )

    try:
        forecast = get_weather_forecast(location=payload.location)
    except WeatherServiceError as exc:
        raise HTTPException(
            status_code=503,
            detail="Meteo indisponible. Utilisez /predict en mode manuel.",
        ) from exc

    request = PredictionRequest(
        location=payload.location,
        culture=payload.culture,
        saison=_current_season(),
        type_sol=payload.type_sol,
        irrigation=snapshot.irrigation,
        humidite_sol=snapshot.soil_humidity,
        temp_actuelle=forecast.temp_actuelle,
        temp_min_7j=forecast.temp_min_7j,
        temp_moyenne_7j=forecast.temp_moyenne_7j,
        pluie_7j=forecast.pluie_7j,
        risque_gel_7j=forecast.risque_gel_7j,
        water_usage=snapshot.water_usage,
    )
    result = predict_recommendation(request)
    return save_prediction(request, result)


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
        dataset_name=metadata.get("dataset_name"),
        trained_at=metadata.get("trained_at"),
    )


@app.get("/weather", response_model=WeatherResponse)
def weather(
    location: Annotated[str, Query(min_length=1, max_length=120)] = "Rennes",
    latitude: Annotated[float | None, Query(ge=-90, le=90)] = None,
    longitude: Annotated[float | None, Query(ge=-180, le=180)] = None,
) -> WeatherResponse:
    try:
        return get_weather_forecast(
            location=location,
            latitude=latitude,
            longitude=longitude,
        )
    except WeatherServiceError as exc:
        raise HTTPException(
            status_code=503,
            detail="Meteo indisponible. Utilisez la saisie manuelle.",
        ) from exc


@app.get("/iot/live", response_model=IotLiveResponse)
def iot_live() -> IotLiveResponse:
    return iot_state.snapshot()


@app.websocket("/ws/iot")
async def iot_live_websocket(websocket: WebSocket) -> None:
    await websocket.accept()
    try:
        while True:
            await websocket.send_json(iot_state.snapshot().model_dump(mode="json"))
            await asyncio.sleep(2)
    except WebSocketDisconnect:
        return


def _current_season(now: datetime | None = None) -> str:
    month = (now or datetime.now()).month
    if month in {3, 4, 5}:
        return "printemps"
    if month in {6, 7, 8}:
        return "ete"
    if month in {9, 10, 11}:
        return "automne"
    return "hiver"


def _sync_model_version() -> None:
    metadata = get_model_metadata()
    metrics = metadata.get("metrics", {})
    try:
        upsert_model_version(
            version=metadata["version"],
            trained_at=metadata.get("trained_at"),
            dataset_name=metadata.get("dataset_name"),
            accuracy=metrics.get("accuracy"),
            f1_macro=metrics.get("f1_macro"),
            notes=metadata["status"],
        )
    except Exception as exc:
        logger.warning("Unable to sync model version metadata: %s", exc)
