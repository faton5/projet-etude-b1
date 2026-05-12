from __future__ import annotations

from datetime import UTC, datetime

from app.schemas import IotLiveResponse, IrrigationType, SoilType, WeatherResponse


DEMO_SOIL_HUMIDITY: dict[SoilType, float] = {
    "argileux": 58.0,
    "limoneux": 52.0,
    "sableux": 44.0,
    "calcaire": 48.0,
    "humifere": 56.0,
}

DEMO_WATER_USAGE: dict[IrrigationType, float] = {
    "aucun": 0.0,
    "manuel": 4.0,
    "goutte_a_goutte": 2.5,
    "automatique": 3.5,
}


def demo_iot_snapshot(
    mqtt_connected: bool = False,
    soil_type: SoilType = "limoneux",
    irrigation: IrrigationType = "manuel",
) -> IotLiveResponse:
    now = datetime.now(UTC)
    return IotLiveResponse(
        soil_humidity=DEMO_SOIL_HUMIDITY[soil_type],
        water_usage=DEMO_WATER_USAGE[irrigation],
        irrigation=irrigation,
        irrigation_active=False,
        mqtt_connected=mqtt_connected,
        mqtt_status="demo" if not mqtt_connected else "connected",
        last_update=now,
        farm_id="farm_1",
        soil_sensor_id="soil_sensor_demo",
        irrigation_sensor_id="irrigation_sensor_demo",
        water_sensor_id="water_sensor_demo",
        demo=True,
    )


def fallback_weather(location: str, latitude: float, longitude: float) -> WeatherResponse:
    return WeatherResponse(
        location=location,
        latitude=latitude,
        longitude=longitude,
        source="demo_fallback",
        status="fallback",
        message="Meteo de demonstration utilisee car Open-Meteo est indisponible.",
        temp_actuelle=16.0,
        temp_min_7j=8.0,
        temp_moyenne_7j=14.0,
        pluie_7j=False,
        risque_gel_7j=False,
        precipitation_7j=0.0,
        precipitation_probability_max=0,
    )
