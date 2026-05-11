from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


Recommendation = Literal["viable", "attendre", "non_viable"]
Season = Literal["printemps", "ete", "automne", "hiver"]
SoilType = Literal["argileux", "limoneux", "sableux", "calcaire", "humifere"]
IrrigationType = Literal["manuel", "goutte_a_goutte", "automatique", "aucun"]


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
    status: Literal["ok"]
    service: str


class ModelInfoResponse(BaseModel):
    name: str
    version: str
    type: str
    status: str
    classes: list[Recommendation]
    metrics: dict = Field(default_factory=dict)
    model_path: str | None = None


class WeatherResponse(BaseModel):
    location: str
    source: str
    status: str
    message: str
