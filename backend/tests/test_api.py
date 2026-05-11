from collections.abc import Iterator

import pytest
from pydantic import ValidationError

from app.database import init_db
from app.main import health, history, history_item, model_info, predict
from app.schemas import PredictionRequest


@pytest.fixture(autouse=True)
def isolated_db(tmp_path, monkeypatch) -> Iterator[None]:
    monkeypatch.setenv("POTAGER_DB_PATH", str(tmp_path / "test.db"))
    init_db()
    yield


def valid_payload(**overrides) -> PredictionRequest:
    payload = {
        "location": "Rennes",
        "culture": "tomate",
        "saison": "printemps",
        "type_sol": "limoneux",
        "irrigation": "manuel",
        "humidite_sol": 55,
        "temp_actuelle": 20,
        "temp_min_7j": 13,
        "temp_moyenne_7j": 18,
        "pluie_7j": True,
        "risque_gel_7j": False,
        "water_usage": 80,
    }
    payload.update(overrides)
    return PredictionRequest(**payload)


def test_health_returns_ok():
    assert health().model_dump() == {
        "status": "ok",
        "service": "potager-ehpad-backend",
    }


def test_prediction_returns_viable_for_good_conditions():
    body = predict(valid_payload())

    assert body.recommandation == "viable"
    assert body.score_confiance > 0.8
    assert body.id == 1


def test_prediction_returns_non_viable_when_frost_risk():
    body = predict(valid_payload(temp_min_7j=2, risque_gel_7j=True))

    assert body.recommandation == "non_viable"
    assert "risque_gel_7j" in body.facteurs_importants


def test_prediction_returns_attendre_when_soil_is_dry():
    body = predict(valid_payload(humidite_sol=25, pluie_7j=False))

    assert body.recommandation == "attendre"
    assert "humidite_sol" in body.facteurs_importants


def test_prediction_validates_payload():
    with pytest.raises(ValidationError):
        valid_payload(humidite_sol=130)


def test_history_persists_predictions():
    predict(valid_payload(location="Rennes"))
    predict(valid_payload(location="Nantes", temp_min_7j=7))

    rows = history()

    assert len(rows) == 2
    assert rows[0].request.location == "Nantes"
    assert rows[1].request.location == "Rennes"


def test_history_limit():
    predict(valid_payload(location="Rennes"))
    predict(valid_payload(location="Nantes"))

    assert len(history(limit=1)) == 1


def test_history_item_returns_prediction():
    created = predict(valid_payload(location="Rennes"))

    item = history_item(created.id)

    assert item.request.location == "Rennes"


def test_model_info_returns_baseline_status():
    info = model_info()

    assert info.classes == ["viable", "attendre", "non_viable"]
    assert info.status == "xgboost_loaded"
    assert info.metrics["accuracy"] >= 0.9
