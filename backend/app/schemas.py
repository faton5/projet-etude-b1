from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


Recommendation = Literal["viable", "attendre", "non_viable"]
Season = Literal["printemps", "ete", "automne", "hiver"]
SoilType = Literal["argileux", "limoneux", "sableux", "calcaire", "humifere"]
IrrigationType = Literal["manuel", "goutte_a_goutte", "automatique", "aucun"]
IotTopic = Literal["farm/tomato/soil", "farm/tomato/irrigation", "farm/tomato/water_usage"]


class PredictionRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    location: str = Field(..., min_length=1, max_length=120, examples=["Rennes"])
    culture: Literal["tomate"] = Field(default="tomate")
    saison: Season
    type_sol: SoilType
    irrigation: IrrigationType
    humidite_sol: float = Field(..., ge=0, le=100)
    temp_actuelle: float = Field(..., ge=-30, le=60)
    temp_min_7j: float = Field(..., ge=-30, le=60)
    temp_moyenne_7j: float = Field(..., ge=-30, le=60)
    pluie_7j: bool
    risque_gel_7j: bool
    water_usage: float = Field(..., ge=0, le=1000)

    @field_validator("culture", "saison", "type_sol", "irrigation", mode="before")
    @classmethod
    def normalize_text(cls, value: str) -> str:
        if isinstance(value, str):
            return value.strip().lower().replace("-", "_")
        return value


class PredictionResult(BaseModel):
    recommandation: Recommendation
    score_confiance: float = Field(..., ge=0, le=1)
    explication: str
    facteurs_importants: list[str]


class PredictionResponse(PredictionResult):
    id: int
    created_at: datetime


class HistoryItem(PredictionResponse):
    request: PredictionRequest


class HealthResponse(BaseModel):
    api: Literal["ok"]
    mqtt: str
    model: str
    database: str
    websocket: Literal["ok"]
    demo_mode: bool = False


class ModelInfoResponse(BaseModel):
    name: str
    version: str
    type: str
    status: str
    classes: list[Recommendation]
    metrics: dict = Field(default_factory=dict)
    model_path: str | None = None
    dataset_name: str | None = None
    trained_at: datetime | None = None


class GardenProfile(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    location: str = Field(default="Rennes", min_length=1, max_length=120)
    type_sol: SoilType = Field(default="limoneux")
    irrigation: IrrigationType = Field(default="manuel")

    @field_validator("type_sol", "irrigation", mode="before")
    @classmethod
    def normalize_profile_text(cls, value: str) -> str:
        if isinstance(value, str):
            return value.strip().lower().replace("-", "_")
        return value


class WeatherResponse(BaseModel):
    location: str
    latitude: float
    longitude: float
    source: str
    status: str
    message: str
    temp_actuelle: float
    temp_min_7j: float
    temp_moyenne_7j: float
    pluie_7j: bool
    risque_gel_7j: bool
    precipitation_7j: float
    precipitation_probability_max: float


class SoilSensorPayload(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    sensor_id: str = Field(..., min_length=1, max_length=80)
    farm_id: str = Field(..., min_length=1, max_length=80)
    humidity: float = Field(..., ge=0, le=100)
    soil_type: SoilType | None = None
    timestamp: datetime


class IrrigationSensorPayload(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    sensor_id: str = Field(..., min_length=1, max_length=80)
    farm_id: str = Field(..., min_length=1, max_length=80)
    irrigation: IrrigationType
    active: bool
    flow_l_min: float = Field(..., ge=0, le=100)
    timestamp: datetime


class WaterUsageSensorPayload(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    sensor_id: str = Field(..., min_length=1, max_length=80)
    farm_id: str = Field(..., min_length=1, max_length=80)
    water_usage: float = Field(..., ge=0, le=1000)
    unit: str | None = None
    timestamp: datetime


class IotLiveResponse(BaseModel):
    soil_humidity: float | None = None
    water_usage: float | None = None
    irrigation: IrrigationType | None = None
    irrigation_active: bool | None = None
    mqtt_connected: bool
    mqtt_status: Literal["connected", "reconnecting", "disabled", "demo"] = "reconnecting"
    last_update: datetime | None = None
    farm_id: str | None = None
    soil_sensor_id: str | None = None
    irrigation_sensor_id: str | None = None
    water_sensor_id: str | None = None
    demo: bool = False


class IotPredictionRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    location: str = Field(default="Rennes", min_length=1, max_length=120)
    culture: Literal["tomate"] = Field(default="tomate")
    type_sol: SoilType = Field(default="limoneux")


class ModelVersion(BaseModel):
    version: str
    trained_at: datetime | None = None
    dataset_name: str | None = None
    accuracy: float | None = None
    f1_macro: float | None = None
    notes: str | None = None
