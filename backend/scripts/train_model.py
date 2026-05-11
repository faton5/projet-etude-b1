from __future__ import annotations

import math
import random
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.dummy import DummyClassifier
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
)
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
from xgboost import XGBClassifier

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BACKEND_DIR))

from app.ml_model import CLASS_LABELS, FEATURE_COLUMNS, encode_payload
from app.schemas import PredictionRequest


SEASONS = ["printemps", "ete", "automne", "hiver"]
SOILS = ["argileux", "limoneux", "sableux", "calcaire", "humifere"]
IRRIGATIONS = ["manuel", "goutte_a_goutte", "automatique", "aucun"]
CLASS_INDEX = {label: index for index, label in enumerate(CLASS_LABELS)}


def build_training_payloads(sample_count: int = 8000) -> list[PredictionRequest]:
    rows = build_training_rows(sample_count=sample_count, seed=42)
    return [row["payload"] for row in rows]


def build_training_rows(sample_count: int = 8000, seed: int = 42) -> list[dict[str, Any]]:
    rng = random.Random(seed)
    rows: list[dict[str, Any]] = []

    for _ in range(sample_count):
        payload = _generate_payload(rng)
        score = viability_score(payload, rng=rng)
        label = _sample_label(score, rng)
        rows.append(
            {
                "payload": payload,
                "score_viabilite": round(score, 2),
                "target": CLASS_INDEX[label],
                "target_label": label,
            }
        )

    return rows


def target_for_payload(payload: PredictionRequest) -> int:
    """Most likely class for a payload, kept for diagnostics and manual checks."""
    return CLASS_INDEX[_most_likely_label(viability_score(payload, rng=None))]


def train(output_path: Path, sample_count: int = 8000) -> dict[str, object]:
    rows = build_training_rows(sample_count=sample_count)
    x = pd.DataFrame([encode_payload(row["payload"]) for row in rows], columns=FEATURE_COLUMNS)
    y = np.array([row["target"] for row in rows])

    x_train, x_test, y_train, y_test = train_test_split(
        x,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y,
    )

    model = _build_xgboost()
    model.fit(x_train, y_train)

    predictions = model.predict(x_test)
    report = classification_report(
        y_test,
        predictions,
        target_names=CLASS_LABELS,
        output_dict=True,
        zero_division=0,
    )
    metrics = {
        "accuracy": round(float(accuracy_score(y_test, predictions)), 3),
        "f1_macro": round(float(f1_score(y_test, predictions, average="macro")), 3),
        "samples": len(rows),
        "class_distribution": _class_distribution(y),
        "confusion_matrix": confusion_matrix(y_test, predictions).tolist(),
        "report": report,
        "baselines": _evaluate_baselines(x_train, x_test, y_train, y_test),
        "permutation_importance": _permutation_importance(model, x_test, y_test),
    }
    important_factors = _important_factors(model)

    bundle = {
        "name": "potager-tomate-xgboost",
        "version": "0.3.0",
        "type": "xgboost_classifier",
        "training_dataset": "synthetic_probabilistic_v1",
        "trained_at": datetime.now(UTC).isoformat(),
        "model": model,
        "feature_columns": FEATURE_COLUMNS,
        "class_labels": CLASS_LABELS,
        "important_factors": important_factors,
        "metrics": metrics,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(bundle, output_path)
    _print_report(model, metrics)
    return metrics


# ---------------------------------------------------------------------------
# Scoring: progressif, multi-variable, pas de seuils if/else brutaux
# ---------------------------------------------------------------------------


def viability_score(payload: PredictionRequest, rng: random.Random | None) -> float:
    score = 53.0

    score += _season_contribution(payload)
    score += _temperature_contribution(payload)
    score += _humidity_contribution(payload)
    score += _soil_contribution(payload)
    score += _irrigation_contribution(payload)
    score += _water_usage_contribution(payload)
    score += _rain_frost_contribution(payload)
    score += _interaction_effects(payload)

    if rng is not None:
        score += rng.gauss(0, 5.5)

    return max(0.0, min(100.0, score))


def _season_contribution(payload: PredictionRequest) -> float:
    base = {
        "printemps": 4.0,
        "ete": 2.5,
        "automne": -4.0,
        "hiver": -14.0,
    }[payload.saison]

    if payload.saison == "printemps" and payload.temp_moyenne_7j < 13:
        base -= 6.0
    elif payload.saison == "printemps" and payload.temp_moyenne_7j > 18:
        base += 3.0

    if payload.saison == "automne" and payload.temp_moyenne_7j > 16:
        base += 5.0
    elif payload.saison == "automne" and payload.temp_min_7j > 10:
        base += 3.0

    if payload.saison == "hiver" and payload.temp_moyenne_7j > 12:
        base += 8.0
    elif payload.saison == "hiver" and payload.temp_min_7j > 6:
        base += 4.0

    if payload.saison == "ete" and payload.temp_moyenne_7j > 30:
        base -= 6.0

    return base


def _temperature_contribution(payload: PredictionRequest) -> float:
    score = 0.0

    score += _smooth_range(payload.temp_min_7j, optimal_low=10, optimal_high=18, steepness=0.35)
    score += _smooth_range(payload.temp_moyenne_7j, optimal_low=15, optimal_high=25, steepness=0.4)
    score += _smooth_range(payload.temp_actuelle, optimal_low=14, optimal_high=32, steepness=0.25)

    if payload.temp_min_7j < 5:
        score -= (5 - payload.temp_min_7j) * 1.8
    if payload.temp_moyenne_7j > 28:
        score -= (payload.temp_moyenne_7j - 28) * 1.5

    return score


def _humidity_contribution(payload: PredictionRequest) -> float:
    return _smooth_range(payload.humidite_sol, optimal_low=40, optimal_high=72, steepness=0.32)


def _soil_contribution(payload: PredictionRequest) -> float:
    h = payload.humidite_sol

    if payload.type_sol == "limoneux":
        return 5.0 + _sigmoid_blend(h, center=55, width=15) * 2.5
    elif payload.type_sol == "humifere":
        return 4.5 + _sigmoid_blend(h, center=50, width=18) * 2.0
    elif payload.type_sol == "sableux":
        deficit = max(0, 50 - h)
        return -deficit * 0.30 - 2.0
    elif payload.type_sol == "argileux":
        excess = max(0, h - 60)
        return -excess * 0.30 - 1.5
    else:
        return -3.0


def _irrigation_contribution(payload: PredictionRequest) -> float:
    h = payload.humidite_sol
    deficit = max(0, 45 - h)
    excess = max(0, h - 75)

    if payload.irrigation == "goutte_a_goutte":
        return 5.0 + deficit * 0.18 - excess * 0.05
    elif payload.irrigation == "automatique":
        return 3.5 + deficit * 0.14 - excess * 0.08
    elif payload.irrigation == "manuel":
        return 1.5 + deficit * 0.06
    else:
        return -2.0 - deficit * 0.22


def _water_usage_contribution(payload: PredictionRequest) -> float:
    w = payload.water_usage
    h = payload.humidite_sol
    t = payload.temp_moyenne_7j

    ideal_water = 65.0
    if h < 40:
        ideal_water = 110.0
    elif h > 75:
        ideal_water = 25.0
    if t > 25:
        ideal_water += 30.0
    elif t < 12:
        ideal_water -= 20.0

    deviation = abs(w - ideal_water)
    score = -deviation * 0.07

    if h < 40 and w < 30:
        score -= 8.0
    if h > 80 and w > 120:
        score -= 7.0
    if 40 <= h <= 70 and 40 <= w <= 140:
        score += 4.0

    return max(-15.0, min(8.0, score))


def _rain_frost_contribution(payload: PredictionRequest) -> float:
    score = 0.0

    if payload.risque_gel_7j:
        severity = max(0, 8 - payload.temp_min_7j)
        score -= 10.0 + severity * 2.0

    if payload.pluie_7j:
        if payload.humidite_sol < 45:
            score += 4.0
        elif payload.humidite_sol > 80:
            score -= 4.0
        else:
            score += 1.0
    else:
        if payload.humidite_sol < 35:
            score -= 5.0

    return score


def _interaction_effects(payload: PredictionRequest) -> float:
    score = 0.0

    if payload.type_sol == "sableux" and payload.irrigation == "aucun" and payload.humidite_sol < 40:
        score -= 5.0
    if payload.type_sol == "argileux" and payload.humidite_sol > 80 and payload.pluie_7j:
        score -= 4.0

    if payload.type_sol == "limoneux" and payload.irrigation == "goutte_a_goutte":
        score += 3.0
    if payload.type_sol == "humifere" and 45 <= payload.humidite_sol <= 70:
        score += 2.0

    if payload.temp_moyenne_7j > 28 and payload.water_usage < 50:
        score -= 4.0
    if payload.temp_moyenne_7j > 28 and payload.water_usage > 80:
        score += 2.0

    if payload.saison == "printemps" and payload.irrigation == "goutte_a_goutte" and not payload.risque_gel_7j:
        score += 2.0

    return score


def _smooth_range(value: float, optimal_low: float, optimal_high: float, steepness: float) -> float:
    if optimal_low <= value <= optimal_high:
        center = (optimal_low + optimal_high) / 2
        dist_to_edge = min(value - optimal_low, optimal_high - value)
        range_half = (optimal_high - optimal_low) / 2
        return 5.0 * (dist_to_edge / range_half) ** 0.5
    elif value < optimal_low:
        return -(optimal_low - value) ** 1.3 * steepness
    else:
        return -(value - optimal_high) ** 1.3 * steepness


def _sigmoid_blend(value: float, center: float, width: float) -> float:
    x = (value - center) / width
    return 2.0 / (1 + math.exp(-x)) - 1.0


# ---------------------------------------------------------------------------
# Data generation
# ---------------------------------------------------------------------------


def _generate_payload(rng: random.Random) -> PredictionRequest:
    saison = rng.choices(SEASONS, weights=[0.34, 0.28, 0.22, 0.16])[0]
    scenario = rng.choices(
        [
            "normal",
            "temp_min_limite",
            "moyenne_limite",
            "sol_sec_limite",
            "sol_humide_limite",
            "trop_chaud",
            "printemps_froid",
            "ete_tres_chaud",
            "automne_doux",
            "hiver_doux",
            "sol_sableux_sec",
            "sol_argileux_humide",
        ],
        weights=[0.34, 0.08, 0.07, 0.07, 0.06, 0.06, 0.07, 0.06, 0.06, 0.05, 0.04, 0.04],
    )[0]

    temp_moyenne = _seasonal_temperature(saison, rng)
    humidite_sol = rng.uniform(30, 80)

    if scenario == "temp_min_limite":
        temp_moyenne = rng.uniform(13, 18)
        temp_min = rng.uniform(8, 11)
    elif scenario == "moyenne_limite":
        temp_moyenne = rng.uniform(13, 15)
        temp_min = rng.uniform(7, 12)
    elif scenario == "sol_sec_limite":
        humidite_sol = rng.uniform(28, 40)
        temp_min = temp_moyenne - rng.uniform(4, 8)
    elif scenario == "sol_humide_limite":
        humidite_sol = rng.uniform(78, 92)
        temp_min = temp_moyenne - rng.uniform(3, 7)
    elif scenario == "trop_chaud":
        temp_moyenne = rng.uniform(28, 33)
        temp_min = rng.uniform(18, 24)
    elif scenario == "printemps_froid":
        saison = "printemps"
        temp_moyenne = rng.uniform(9, 14)
        temp_min = rng.uniform(3, 9)
    elif scenario == "ete_tres_chaud":
        saison = "ete"
        temp_moyenne = rng.uniform(30, 36)
        temp_min = rng.uniform(19, 25)
    elif scenario == "automne_doux":
        saison = "automne"
        temp_moyenne = rng.uniform(15, 21)
        temp_min = rng.uniform(9, 15)
    elif scenario == "hiver_doux":
        saison = "hiver"
        temp_moyenne = rng.uniform(10, 15)
        temp_min = rng.uniform(5, 10)
    elif scenario == "sol_sableux_sec":
        humidite_sol = rng.uniform(22, 38)
        temp_min = temp_moyenne - rng.uniform(4, 8)
    elif scenario == "sol_argileux_humide":
        humidite_sol = rng.uniform(78, 95)
        temp_min = temp_moyenne - rng.uniform(3, 6)
    else:
        temp_min = temp_moyenne - rng.uniform(3, 9)

    temp_actuelle = temp_moyenne + rng.uniform(-4, 6)
    temp_actuelle += rng.gauss(0, 1.8)
    temp_min += rng.gauss(0, 1.5)
    temp_moyenne += rng.gauss(0, 1.5)
    humidite_sol += rng.gauss(0, 7.0)

    if scenario == "sol_sableux_sec":
        type_sol = "sableux"
    elif scenario == "sol_argileux_humide":
        type_sol = "argileux"
    else:
        type_sol = rng.choices(SOILS, weights=[0.20, 0.25, 0.20, 0.15, 0.20])[0]

    irrigation = rng.choices(IRRIGATIONS, weights=[0.35, 0.25, 0.22, 0.18])[0]
    pluie_mm = _rainfall_for_season(saison, rng)
    if humidite_sol < 35 and rng.random() < 0.4:
        pluie_mm = rng.uniform(0, 2)
    if humidite_sol > 82 and rng.random() < 0.5:
        pluie_mm += rng.uniform(8, 25)
    pluie_7j = pluie_mm > rng.uniform(2, 7)
    risque_gel_7j = _frost_risk(temp_min, rng)
    water_usage = _water_usage(irrigation, humidite_sol, temp_moyenne, pluie_mm, rng)

    return PredictionRequest(
        location=rng.choice(["Rennes", "Nantes", "Angers", "Vannes", "Tours", "Poitiers"]),
        culture="tomate",
        saison=saison,
        type_sol=type_sol,
        irrigation=irrigation,
        humidite_sol=round(max(0, min(100, humidite_sol)), 1),
        temp_actuelle=round(max(-30, min(60, temp_actuelle)), 1),
        temp_min_7j=round(max(-30, min(60, temp_min)), 1),
        temp_moyenne_7j=round(max(-30, min(60, temp_moyenne)), 1),
        pluie_7j=pluie_7j,
        risque_gel_7j=risque_gel_7j,
        water_usage=round(max(0, min(1000, water_usage)), 1),
    )


# ---------------------------------------------------------------------------
# Label sampling: probabiliste, pas de seuil fixe
# ---------------------------------------------------------------------------


def _sample_label(score: float, rng: random.Random) -> str:
    viable, attendre, non_viable = _label_probabilities(score)
    return rng.choices(CLASS_LABELS, weights=[viable, attendre, non_viable])[0]


def _most_likely_label(score: float) -> str:
    probabilities = _label_probabilities(score)
    return CLASS_LABELS[int(np.argmax(probabilities))]


def _label_probabilities(score: float) -> tuple[float, float, float]:
    temp = 11.0
    e_viable = math.exp((score - 60) / temp)
    e_attendre = math.exp(-(abs(score - 50) / temp) ** 1.4) * 2.2
    e_non_viable = math.exp((40 - score) / temp)

    total = e_viable + e_attendre + e_non_viable
    viable = e_viable / total
    attendre = e_attendre / total
    non_viable = e_non_viable / total

    viable = max(0.04, viable)
    attendre = max(0.06, attendre)
    non_viable = max(0.04, non_viable)

    total = viable + attendre + non_viable
    return viable / total, attendre / total, non_viable / total


# ---------------------------------------------------------------------------
# XGBoost configuration
# ---------------------------------------------------------------------------


def _build_xgboost() -> XGBClassifier:
    return XGBClassifier(
        objective="multi:softprob",
        num_class=len(CLASS_LABELS),
        n_estimators=200,
        max_depth=4,
        learning_rate=0.06,
        subsample=0.85,
        colsample_bytree=0.85,
        min_child_weight=3,
        reg_alpha=0.1,
        reg_lambda=1.5,
        eval_metric="mlogloss",
        random_state=42,
    )


# ---------------------------------------------------------------------------
# Helpers for data generation
# ---------------------------------------------------------------------------


def _seasonal_temperature(saison: str, rng: random.Random) -> float:
    if saison == "printemps":
        return rng.gauss(16.0, 4.5)
    if saison == "ete":
        return rng.gauss(24.5, 4.5)
    if saison == "automne":
        return rng.gauss(13.0, 4.5)
    return rng.gauss(6.5, 4.0)


def _rainfall_for_season(saison: str, rng: random.Random) -> float:
    base = {"printemps": 7.5, "ete": 4.5, "automne": 10.0, "hiver": 9.0}[saison]
    if rng.random() < 0.35:
        return 0.0
    return min(50.0, rng.expovariate(1 / base))


def _frost_risk(temp_min: float, rng: random.Random) -> bool:
    probability = 1 / (1 + math.exp((temp_min - 3.0) / 1.8))
    if rng.random() < 0.08:
        probability = 1 - probability
    return rng.random() < probability


def _water_usage(
    irrigation: str,
    humidite_sol: float,
    temp_moyenne: float,
    pluie_mm: float,
    rng: random.Random,
) -> float:
    base = {
        "aucun": rng.uniform(0, 18),
        "manuel": rng.uniform(30, 130),
        "goutte_a_goutte": rng.uniform(40, 120),
        "automatique": rng.uniform(50, 170),
    }[irrigation]
    if humidite_sol < 38:
        base += rng.uniform(15, 55)
    elif humidite_sol > 75:
        base -= rng.uniform(5, 30)
    if temp_moyenne > 26:
        base += rng.uniform(10, 45)
    elif temp_moyenne < 10:
        base -= rng.uniform(5, 25)
    if pluie_mm > 12:
        base -= rng.uniform(10, 40)
    base += rng.gauss(0, 12)
    return max(0, base)


# ---------------------------------------------------------------------------
# Evaluation baselines and metrics
# ---------------------------------------------------------------------------


def _evaluate_baselines(
    x_train: pd.DataFrame,
    x_test: pd.DataFrame,
    y_train: np.ndarray,
    y_test: np.ndarray,
) -> dict[str, dict[str, object]]:
    models = {
        "dummy_majority": DummyClassifier(strategy="most_frequent", random_state=42),
        "decision_tree_depth3": DecisionTreeClassifier(max_depth=3, random_state=42),
    }
    results: dict[str, dict[str, object]] = {}
    for name, model in models.items():
        model.fit(x_train, y_train)
        predictions = model.predict(x_test)
        results[name] = {
            "accuracy": round(float(accuracy_score(y_test, predictions)), 3),
            "f1_macro": round(float(f1_score(y_test, predictions, average="macro")), 3),
            "confusion_matrix": confusion_matrix(y_test, predictions).tolist(),
            "report": classification_report(
                y_test,
                predictions,
                target_names=CLASS_LABELS,
                output_dict=True,
                zero_division=0,
            ),
        }
    return results


def _permutation_importance(
    model: XGBClassifier,
    x_test: pd.DataFrame,
    y_test: np.ndarray,
) -> dict[str, dict[str, float]]:
    baseline = f1_score(y_test, model.predict(x_test), average="macro")
    rng = np.random.default_rng(42)
    result: dict[str, dict[str, float]] = {}
    for column in FEATURE_COLUMNS:
        drops = []
        for _ in range(10):
            shuffled = x_test.copy()
            shuffled[column] = rng.permutation(shuffled[column].to_numpy())
            score = f1_score(y_test, model.predict(shuffled), average="macro")
            drops.append(float(baseline - score))
        result[column] = {
            "mean_drop": round(float(np.mean(drops)), 4),
            "std": round(float(np.std(drops)), 4),
        }
    return result


def _important_factors(model: XGBClassifier) -> list[str]:
    importances = list(model.feature_importances_)
    ordered = sorted(
        zip(FEATURE_COLUMNS, importances, strict=True),
        key=lambda item: item[1],
        reverse=True,
    )
    return [feature for feature, _ in ordered[:4]]


def _class_distribution(y: np.ndarray) -> dict[str, int]:
    labels = [CLASS_LABELS[int(index)] for index in y]
    return pd.Series(labels).value_counts().to_dict()


def _print_report(model: XGBClassifier, metrics: dict[str, object]) -> None:
    print("\n" + "=" * 70)
    print("TRAINING REPORT — synthetic_probabilistic_v1")
    print("=" * 70)
    print(f"Samples: {metrics['samples']}")
    print("\nClass distribution:")
    for label, count in metrics["class_distribution"].items():
        pct = count / metrics["samples"] * 100
        print(f"  {label}: {count} ({pct:.1f}%)")
    print(f"\nXGBoost accuracy: {metrics['accuracy']}")
    print(f"XGBoost f1_macro: {metrics['f1_macro']}")
    print(f"\nConfusion matrix:")
    print(f"  {CLASS_LABELS}")
    for i, row in enumerate(metrics["confusion_matrix"]):
        print(f"  {CLASS_LABELS[i]:12s} {row}")
    print("\nClassification report:")
    print(pd.DataFrame(metrics["report"]).transpose().round(3).to_string())
    print("\nFeature importance (gain):")
    for feature, importance in sorted(
        zip(FEATURE_COLUMNS, model.feature_importances_, strict=True),
        key=lambda item: item[1],
        reverse=True,
    ):
        bar = "#" * int(importance * 80)
        print(f"  {feature:20s} {importance:.4f} {bar}")
    print("\nPermutation importance (f1_macro drop):")
    for feature, values in sorted(
        metrics["permutation_importance"].items(),
        key=lambda item: item[1]["mean_drop"],
        reverse=True,
    ):
        print(f"  {feature:20s} mean_drop={values['mean_drop']:.4f} ± {values['std']:.4f}")
    print("\nBaselines:")
    for name, baseline in metrics["baselines"].items():
        print(f"  {name}: accuracy={baseline['accuracy']}, f1_macro={baseline['f1_macro']}")
        print(f"    confusion_matrix: {baseline['confusion_matrix']}")

    xgb_f1 = metrics["f1_macro"]
    dummy_f1 = metrics["baselines"]["dummy_majority"]["f1_macro"]
    tree_f1 = metrics["baselines"]["decision_tree_depth3"]["f1_macro"]
    print(f"\nXGBoost vs DummyClassifier: +{xgb_f1 - dummy_f1:.3f} f1_macro")
    print(f"XGBoost vs DecisionTree(depth=3): +{xgb_f1 - tree_f1:.3f} f1_macro")

    if xgb_f1 <= dummy_f1:
        print("WARNING: XGBoost is NOT better than DummyClassifier!")
    if xgb_f1 - tree_f1 < 0.02:
        print("WARNING: DecisionTree(depth=3) is nearly as good as XGBoost!")
    print("=" * 70)


if __name__ == "__main__":
    target = Path(__file__).resolve().parent.parent / "models" / "xgboost_tomate.joblib"
    metrics = train(target)
    print(f"\nModel saved to {target}")
