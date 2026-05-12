from __future__ import annotations

from datetime import UTC, datetime

from app.schemas import IotLiveResponse, WeatherResponse


def demo_iot_snapshot(mqtt_connected: bool = False) -> IotLiveResponse:
    now = datetime.now(UTC)
    return IotLiveResponse(
        soil_humidity=52.0,
        water_usage=0.0,
        irrigation="goutte_a_goutte",
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
