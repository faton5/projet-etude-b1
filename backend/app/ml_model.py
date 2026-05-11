import os
from functools import lru_cache
from pathlib import Path
from typing import Any

import joblib

from app.config import get_settings
from app.schemas import PredictionRequest


CLASS_LABELS = ["viable", "attendre", "non_viable"]
FEATURE_COLUMNS = [
    "saison_code",
    "type_sol_code",
    "irrigation_code",
    "humidite_sol",
    "temp_actuelle",
    "temp_min_7j",
    "temp_moyenne_7j",
    "pluie_7j",
    "risque_gel_7j",
    "water_usage",
    "confort_thermique",
    "stress_hydrique",
    "risque_secheresse",
    "score_saison_tomate",
]

SEASON_CODES = {"printemps": 0, "ete": 1, "automne": 2, "hiver": 3}
SOIL_CODES = {"argileux": 0, "limoneux": 1, "sableux": 2, "calcaire": 3, "humifere": 4}
IRRIGATION_CODES = {"manuel": 0, "goutte_a_goutte": 1, "automatique": 2, "aucun": 3}


def default_model_path() -> Path:
    return Path(__file__).resolve().parent.parent / "models" / "xgboost_tomate.joblib"


def get_model_path() -> Path:
    return get_settings().model_path or Path(os.getenv("MODEL_PATH", str(default_model_path())))


def encode_payload(payload: PredictionRequest) -> list[float]:
    temp_ideal_center = 20.0
    confort_thermique = max(0.0, 10.0 - abs(payload.temp_moyenne_7j - temp_ideal_center) * 0.5)
    if payload.temp_min_7j < 8:
        confort_thermique *= max(0.2, payload.temp_min_7j / 8.0)

    stress_hydrique = max(0.0, 50.0 - payload.humidite_sol) * (1.0 if not payload.pluie_7j else 0.3)
    if payload.irrigation == "aucun":
        stress_hydrique *= 1.5

    risque_secheresse = (
        max(0.0, 40.0 - payload.humidite_sol)
        + max(0.0, payload.temp_moyenne_7j - 25.0) * 2.5
        + (5.0 if not payload.pluie_7j and payload.humidite_sol < 40 else 0.0)
    )

    season_tomate_scores = {"printemps": 0.7, "ete": 0.9, "automne": 0.3, "hiver": 0.1}
    score_saison_tomate = season_tomate_scores[payload.saison]
    if payload.saison == "printemps" and payload.temp_moyenne_7j < 13:
        score_saison_tomate = 0.35
    elif payload.saison == "printemps" and payload.temp_moyenne_7j > 18:
        score_saison_tomate = 0.85
    elif payload.saison == "automne" and payload.temp_moyenne_7j > 16:
        score_saison_tomate = 0.5
    elif payload.saison == "hiver" and payload.temp_moyenne_7j > 12:
        score_saison_tomate = 0.25

    return [
        float(SEASON_CODES[payload.saison]),
        float(SOIL_CODES[payload.type_sol]),
        float(IRRIGATION_CODES[payload.irrigation]),
        payload.humidite_sol,
        payload.temp_actuelle,
        payload.temp_min_7j,
        payload.temp_moyenne_7j,
        float(payload.pluie_7j),
        float(payload.risque_gel_7j),
        payload.water_usage,
        confort_thermique,
        stress_hydrique,
        risque_secheresse,
        score_saison_tomate,
    ]


@lru_cache(maxsize=1)
def load_model_bundle() -> dict[str, Any] | None:
    model_path = get_model_path()
    if not model_path.exists():
        return None
    return joblib.load(model_path)


def clear_model_cache() -> None:
    load_model_bundle.cache_clear()


def get_model_metadata() -> dict[str, Any]:
    model_path = get_model_path()
    bundle = load_model_bundle()
    if bundle is None:
        return {
            "name": "potager-tomate-xgboost",
            "version": "0.1.0",
            "type": "xgboost_classifier",
            "status": "model_missing_fallback_rules",
            "path": str(model_path),
            "metrics": {},
        }

    return {
        "name": bundle.get("name", "potager-tomate-xgboost"),
        "version": bundle.get("version", "0.1.0"),
        "type": bundle.get("type", "xgboost_classifier"),
        "status": "xgboost_loaded",
        "path": str(model_path),
        "metrics": bundle.get("metrics", {}),
        "trained_at": bundle.get("trained_at"),
        "dataset_name": bundle.get("training_dataset"),
    }


def predict_with_model(payload: PredictionRequest) -> tuple[str, float, list[str]] | None:
    bundle = load_model_bundle()
    if bundle is None:
        return None

    model = bundle["model"]
    features = [encode_payload(payload)]
    prediction_index = int(model.predict(features)[0])
    probabilities = model.predict_proba(features)[0]
    confidence = round(float(max(probabilities)), 2)
    recommendation = CLASS_LABELS[prediction_index]
    important_factors = bundle.get("important_factors", FEATURE_COLUMNS[:4])
    return recommendation, confidence, important_factors[:4]
