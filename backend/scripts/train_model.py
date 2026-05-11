from __future__ import annotations

import random
import sys
from datetime import UTC, datetime
from pathlib import Path

import joblib
import pandas as pd
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BACKEND_DIR))

from app.ml_model import CLASS_LABELS, FEATURE_COLUMNS, encode_payload
from app.schemas import PredictionRequest


SEASONS = ["printemps", "ete", "automne", "hiver"]
SOILS = ["argileux", "limoneux", "sableux", "calcaire", "humifere"]
IRRIGATIONS = ["manuel", "goutte_a_goutte", "automatique", "aucun"]


def build_training_payloads(sample_count: int = 2500) -> list[PredictionRequest]:
    random.seed(42)
    payloads: list[PredictionRequest] = []

    for _ in range(sample_count):
        saison = random.choices(SEASONS, weights=[0.42, 0.32, 0.16, 0.10])[0]
        temp_moyenne = _seasonal_temperature(saison)
        temp_min = temp_moyenne - random.uniform(3, 10)
        risque_gel = temp_min <= random.uniform(0, 3)
        pluie = random.random() < 0.42

        payloads.append(
            PredictionRequest(
                location=random.choice(["Rennes", "Nantes", "Angers", "Vannes"]),
                culture="tomate",
                saison=saison,
                type_sol=random.choice(SOILS),
                irrigation=random.choice(IRRIGATIONS),
                humidite_sol=round(random.uniform(18, 92), 1),
                temp_actuelle=round(temp_moyenne + random.uniform(-4, 7), 1),
                temp_min_7j=round(temp_min, 1),
                temp_moyenne_7j=round(temp_moyenne, 1),
                pluie_7j=pluie,
                risque_gel_7j=risque_gel,
                water_usage=round(random.uniform(20, 180), 1),
            )
        )

    return payloads


def target_for_payload(payload: PredictionRequest) -> int:
    if (
        payload.risque_gel_7j
        or payload.temp_min_7j < 5
        or payload.saison in {"automne", "hiver"}
    ):
        return CLASS_LABELS.index("non_viable")

    waiting_conditions = [
        payload.temp_min_7j < 10,
        payload.temp_moyenne_7j < 14,
        payload.temp_moyenne_7j > 28,
        payload.temp_actuelle > 32,
        payload.humidite_sol < 35 and not payload.pluie_7j,
        payload.humidite_sol > 85,
        payload.type_sol == "sableux" and payload.humidite_sol < 45,
        payload.irrigation == "aucun" and payload.humidite_sol < 45,
    ]
    if any(waiting_conditions):
        return CLASS_LABELS.index("attendre")
    return CLASS_LABELS.index("viable")


def train(output_path: Path) -> dict[str, object]:
    payloads = build_training_payloads()
    x = pd.DataFrame([encode_payload(payload) for payload in payloads], columns=FEATURE_COLUMNS)
    y = [target_for_payload(payload) for payload in payloads]

    x_train, x_test, y_train, y_test = train_test_split(
        x,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y,
    )

    model = XGBClassifier(
        objective="multi:softprob",
        num_class=len(CLASS_LABELS),
        n_estimators=120,
        max_depth=3,
        learning_rate=0.08,
        subsample=0.9,
        colsample_bytree=0.9,
        eval_metric="mlogloss",
        random_state=42,
    )
    model.fit(x_train, y_train)

    predictions = model.predict(x_test)
    accuracy = round(float(accuracy_score(y_test, predictions)), 3)
    report = classification_report(
        y_test,
        predictions,
        target_names=CLASS_LABELS,
        output_dict=True,
        zero_division=0,
    )
    important_factors = _important_factors(model)

    bundle = {
        "name": "potager-tomate-xgboost",
        "version": "0.1.0",
        "type": "xgboost_classifier",
        "trained_at": datetime.now(UTC).isoformat(),
        "model": model,
        "feature_columns": FEATURE_COLUMNS,
        "class_labels": CLASS_LABELS,
        "important_factors": important_factors,
        "metrics": {
            "accuracy": accuracy,
            "samples": len(payloads),
            "report": report,
        },
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(bundle, output_path)
    return bundle["metrics"]


def _seasonal_temperature(saison: str) -> float:
    if saison == "printemps":
        return random.uniform(10, 23)
    if saison == "ete":
        return random.uniform(17, 32)
    if saison == "automne":
        return random.uniform(7, 18)
    return random.uniform(0, 12)


def _important_factors(model: XGBClassifier) -> list[str]:
    importances = list(model.feature_importances_)
    ordered = sorted(
        zip(FEATURE_COLUMNS, importances, strict=True),
        key=lambda item: item[1],
        reverse=True,
    )
    return [feature for feature, _ in ordered[:4]]


if __name__ == "__main__":
    target = Path(__file__).resolve().parent.parent / "models" / "xgboost_tomate.joblib"
    metrics = train(target)
    print(f"Model saved to {target}")
    print(f"Accuracy: {metrics['accuracy']}")
