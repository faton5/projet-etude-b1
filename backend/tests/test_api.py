from collections.abc import Iterator

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.database import init_db
from app.garden_profile import garden_profile_store
from app.main import garden_profile, health, history, history_item, iot_live, model_info, predict, predict_with_iot, update_garden_profile, weather
from app.mqtt_consumer import iot_state
from app.schemas import GardenProfile, IotPredictionRequest, PredictionRequest, WeatherResponse
from app.weather import WeatherServiceError, get_weather_forecast


@pytest.fixture(autouse=True)
def isolated_db(tmp_path, monkeypatch) -> Iterator[None]:
    monkeypatch.setenv("POTAGER_DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("DEMO_MODE", "false")
    init_db()
    iot_state.clear()
    garden_profile_store.update(GardenProfile())
    yield
    iot_state.clear()
    garden_profile_store.update(GardenProfile())


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
    body = health().model_dump()

    assert body["api"] == "ok"
    assert body["database"] == "ok"
    assert body["model"] in ("loaded", "fallback_rules")
    assert body["websocket"] == "ok"


def test_garden_profile_can_be_updated():
    updated = update_garden_profile(
        GardenProfile(location="Nantes", type_sol="sableux", irrigation="goutte_a_goutte")
    )

    assert updated.location == "Nantes"
    assert updated.type_sol == "sableux"
    assert updated.irrigation == "goutte_a_goutte"
    assert garden_profile().location == "Nantes"


def test_prediction_returns_viable_for_good_conditions():
    body = predict(valid_payload())

    assert body.recommandation == "viable"
    assert body.score_confiance > 0.7
    assert body.id == 1


def test_prediction_returns_non_viable_when_frost_risk():
    body = predict(valid_payload(
        temp_min_7j=-2,
        temp_moyenne_7j=5,
        temp_actuelle=4,
        risque_gel_7j=True,
        saison="hiver",
    ))

    assert body.recommandation == "non_viable"
    assert "risque_gel_7j" in body.facteurs_importants


def test_prediction_returns_attendre_when_soil_is_dry():
    body = predict(valid_payload(
        humidite_sol=20,
        pluie_7j=False,
        irrigation="aucun",
        water_usage=10,
    ))

    assert body.recommandation in ("attendre", "non_viable")
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
    assert info.metrics["accuracy"] >= 0.6
    assert info.metrics["f1_macro"] >= 0.6
    assert info.metrics["baselines"]["dummy_majority"]["accuracy"] < info.metrics["accuracy"]


def test_weather_forecast_maps_open_meteo_to_prediction_fields(monkeypatch):
    def fake_fetch(latitude: float, longitude: float):
        assert latitude == 48.1173
        assert longitude == -1.6778
        return {
            "current": {
                "temperature_2m": 10.8,
            },
            "daily": {
                "temperature_2m_min": [4.2, 2.1, -0.4, 6.0, 7.2, 8.0, 9.1],
                "temperature_2m_mean": [12.0, 13.0, 11.0, 15.0, 16.0, 17.0, 18.0],
                "precipitation_sum": [0, 0, 0.2, 0, 1.4, 0, 0],
                "precipitation_probability_max": [10, 20, 30, 25, 55, 10, 5],
            }
        }

    monkeypatch.setattr("app.weather._fetch_open_meteo", fake_fetch)

    forecast = get_weather_forecast(location="Rennes")

    assert forecast.status == "ok"
    assert forecast.source == "open_meteo"
    assert forecast.temp_actuelle == 10.8
    assert forecast.temp_min_7j == -0.4
    assert forecast.temp_moyenne_7j == 14.6
    assert forecast.pluie_7j is True
    assert forecast.risque_gel_7j is True
    assert forecast.precipitation_7j == 1.6
    assert forecast.precipitation_probability_max == 55


def test_weather_forecast_geocodes_custom_location(monkeypatch):
    def fake_geocoding(location: str):
        assert location == "Nantes"
        return "Nantes, Pays de la Loire, France", 47.2184, -1.5536

    def fake_fetch(latitude: float, longitude: float):
        assert latitude == 47.2184
        assert longitude == -1.5536
        return {
            "current": {
                "temperature_2m": 18.2,
            },
            "daily": {
                "temperature_2m_min": [9.0, 10.0, 8.5, 11.0, 12.0, 12.5, 13.0],
                "temperature_2m_mean": [15.0, 16.0, 15.5, 17.0, 18.0, 18.5, 19.0],
                "precipitation_sum": [0, 0, 0, 0, 0, 0, 0],
                "precipitation_probability_max": [10, 15, 15, 20, 20, 10, 5],
            }
        }

    monkeypatch.setattr("app.weather._fetch_open_meteo_geocoding", fake_geocoding)
    monkeypatch.setattr("app.weather._fetch_open_meteo", fake_fetch)

    forecast = get_weather_forecast(location="Nantes")

    assert forecast.location == "Nantes, Pays de la Loire, France"
    assert forecast.latitude == 47.2184
    assert forecast.longitude == -1.5536
    assert forecast.temp_actuelle == 18.2
    assert forecast.pluie_7j is False


def test_weather_route_returns_503_when_forecast_is_unavailable(monkeypatch):
    def fail_forecast(**_kwargs):
        raise WeatherServiceError("unavailable")

    monkeypatch.setattr("app.main.get_weather_forecast", fail_forecast)

    with pytest.raises(HTTPException) as exc:
        weather()

    assert exc.value.status_code == 503


def test_iot_live_returns_latest_mqtt_values():
    timestamp = "2026-05-11T18:00:00Z"
    iot_state.update(
        "farm/tomato/soil",
        {
            "sensor_id": "soil_sensor_1",
            "farm_id": "farm_1",
            "humidity": 43.2,
            "timestamp": timestamp,
        },
    )
    iot_state.update(
        "farm/tomato/irrigation",
        {
            "sensor_id": "irrigation_sensor_1",
            "farm_id": "farm_1",
            "irrigation": "goutte_a_goutte",
            "active": True,
            "flow_l_min": 1.8,
            "timestamp": timestamp,
        },
    )
    iot_state.update(
        "farm/tomato/water_usage",
        {
            "sensor_id": "water_sensor_1",
            "farm_id": "farm_1",
            "water_usage": 12.4,
            "timestamp": timestamp,
        },
    )

    live = iot_live()

    assert live.soil_humidity == 43.2
    assert live.water_usage == 12.4
    assert live.irrigation == "goutte_a_goutte"
    assert live.farm_id == "farm_1"


def test_iot_live_uses_profile_irrigation_in_demo_mode(monkeypatch):
    monkeypatch.setenv("DEMO_MODE", "true")
    update_garden_profile(GardenProfile(location="Nantes", type_sol="sableux", irrigation="aucun"))
    timestamp = "2026-05-11T18:00:00Z"
    iot_state.update(
        "farm/tomato/irrigation",
        {
            "sensor_id": "irrigation_sensor_1",
            "farm_id": "farm_1",
            "irrigation": "goutte_a_goutte",
            "active": True,
            "flow_l_min": 1.8,
            "timestamp": timestamp,
        },
    )

    live = iot_live()

    assert live.irrigation == "aucun"
    assert live.irrigation_active is False


def test_predict_with_iot_combines_weather_and_mqtt(monkeypatch):
    timestamp = "2026-05-11T18:00:00Z"
    iot_state.update(
        "farm/tomato/soil",
        {
            "sensor_id": "soil_sensor_1",
            "farm_id": "farm_1",
            "humidity": 55,
            "timestamp": timestamp,
        },
    )
    iot_state.update(
        "farm/tomato/irrigation",
        {
            "sensor_id": "irrigation_sensor_1",
            "farm_id": "farm_1",
            "irrigation": "goutte_a_goutte",
            "active": False,
            "flow_l_min": 0,
            "timestamp": timestamp,
        },
    )
    iot_state.update(
        "farm/tomato/water_usage",
        {
            "sensor_id": "water_sensor_1",
            "farm_id": "farm_1",
            "water_usage": 7.5,
            "timestamp": timestamp,
        },
    )

    def fake_forecast(**_kwargs):
        return WeatherResponse(
            location="Rennes",
            latitude=48.1173,
            longitude=-1.6778,
            source="open_meteo",
            status="ok",
            message="ok",
            temp_actuelle=20,
            temp_min_7j=12,
            temp_moyenne_7j=18,
            pluie_7j=True,
            risque_gel_7j=False,
            precipitation_7j=2,
            precipitation_probability_max=60,
        )

    monkeypatch.setattr("app.main.get_weather_forecast", fake_forecast)

    result = predict_with_iot(IotPredictionRequest(location="Rennes", type_sol="limoneux"))

    assert result.id == 1
    assert result.recommandation in ("viable", "attendre", "non_viable")


def test_predict_with_iot_requires_sensor_data():
    with pytest.raises(HTTPException) as exc:
        predict_with_iot(IotPredictionRequest(location="Rennes"))

    assert exc.value.status_code == 409
