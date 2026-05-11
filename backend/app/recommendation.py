from app.schemas import PredictionRequest, PredictionResult
from app.ml_model import predict_with_model


def predict_recommendation(payload: PredictionRequest) -> PredictionResult:
    rule_result = predict_with_rules(payload)
    model_prediction = predict_with_model(payload)
    if model_prediction is None:
        return rule_result

    recommendation, confidence, factors = model_prediction
    return PredictionResult(
        recommandation=recommendation,
        score_confiance=confidence,
        explication=_model_explanation(recommendation, rule_result.explication),
        facteurs_importants=_deduplicate(rule_result.facteurs_importants + factors)[:4],
    )


def predict_with_rules(payload: PredictionRequest) -> PredictionResult:
    """Fallback V0 predictor used when the XGBoost artifact is missing."""
    reasons: list[str] = []
    factors: list[str] = []

    if payload.risque_gel_7j:
        return PredictionResult(
            recommandation="non_viable",
            score_confiance=0.95,
            explication=(
                "Un risque de gel est prevu dans les prochains jours. "
                "Il est deconseille de planter les tomates maintenant."
            ),
            facteurs_importants=["risque_gel_7j", "temp_min_7j"],
        )

    if payload.temp_min_7j < 5:
        return PredictionResult(
            recommandation="non_viable",
            score_confiance=0.9,
            explication=(
                "Les temperatures minimales prevues sont trop basses pour les tomates. "
                "La plantation presente un risque important."
            ),
            facteurs_importants=["temp_min_7j"],
        )

    if payload.saison in {"automne", "hiver"}:
        return PredictionResult(
            recommandation="non_viable",
            score_confiance=0.86,
            explication=(
                "La saison n'est pas adaptee a la plantation de tomates en exterieur. "
                "Il vaut mieux attendre une periode plus favorable."
            ),
            facteurs_importants=["saison"],
        )

    if payload.temp_min_7j < 10:
        reasons.append(
            "les temperatures minimales prevues restent encore basses pour les jeunes plants"
        )
        factors.append("temp_min_7j")

    if payload.temp_moyenne_7j < 14:
        reasons.append("la temperature moyenne prevue manque de douceur")
        factors.append("temp_moyenne_7j")

    if payload.temp_moyenne_7j > 28 or payload.temp_actuelle > 32:
        reasons.append("les temperatures sont elevees et peuvent stresser les plants")
        factors.extend(["temp_moyenne_7j", "temp_actuelle"])

    if payload.humidite_sol < 35 and not payload.pluie_7j:
        reasons.append("le sol est trop sec et aucune pluie n'est prevue")
        factors.extend(["humidite_sol", "pluie_7j"])

    if payload.humidite_sol > 85:
        reasons.append("le sol est tres humide, ce qui peut fragiliser les racines")
        factors.append("humidite_sol")

    if payload.type_sol == "sableux" and payload.humidite_sol < 45:
        reasons.append("le sol sableux retient peu l'eau")
        factors.extend(["type_sol", "humidite_sol"])

    if payload.irrigation == "aucun" and payload.humidite_sol < 45:
        reasons.append("aucune irrigation n'est indiquee alors que le sol manque d'eau")
        factors.extend(["irrigation", "humidite_sol"])

    unique_factors = _deduplicate(factors)
    if reasons:
        return PredictionResult(
            recommandation="attendre",
            score_confiance=_waiting_confidence(len(reasons)),
            explication="Il vaut mieux attendre car " + ", et ".join(reasons) + ".",
            facteurs_importants=unique_factors[:4],
        )

    confidence = 0.84
    if payload.saison == "printemps":
        confidence += 0.04
    if 15 <= payload.temp_moyenne_7j <= 24:
        confidence += 0.04
    if 45 <= payload.humidite_sol <= 75:
        confidence += 0.03

    return PredictionResult(
        recommandation="viable",
        score_confiance=round(min(confidence, 0.95), 2),
        explication=(
            "Les conditions sont favorables pour planter des tomates : pas de gel prevu, "
            "des temperatures adaptees et une humidite du sol correcte."
        ),
        facteurs_importants=["risque_gel_7j", "temp_min_7j", "temp_moyenne_7j", "humidite_sol"],
    )


def _waiting_confidence(reason_count: int) -> float:
    return round(min(0.72 + reason_count * 0.05, 0.9), 2)


def _deduplicate(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result


def _model_explanation(recommendation: str, rule_explanation: str) -> str:
    prefix = {
        "viable": "Le modele XGBoost classe les conditions comme favorables.",
        "attendre": "Le modele XGBoost conseille d'attendre avant de planter.",
        "non_viable": "Le modele XGBoost detecte un risque important pour la plantation.",
    }[recommendation]
    return f"{prefix} Repere metier : {rule_explanation}"
