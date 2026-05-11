from __future__ import annotations

import math
from datetime import UTC, datetime

from app.schemas import IotLiveResponse, WeatherResponse


def demo_iot_snapshot(mqtt_connected: bool = False) -> IotLiveResponse:
    now = datetime.now(UTC)
    wave = math.sin(now.timestamp() / 45)
    humidity = round(48 + wave * 7, 1)
    water_usage = round(9 + max(0, -wave) * 5, 1)
    return IotLiveResponse(
        soil_humidity=humidity,
        water_usage=water_usage,
        irrigation="goutte_a_goutte",
        irrigation_active=water_usage > 10,
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
    now = datetime.now(UTC)
    wave = math.sin(now.timestamp() / 3600)
    temp_current = round(17 + wave * 4, 1)
    temp_mean = round(15 + wave * 3, 1)
    temp_min = round(temp_mean - 5, 1)
    return WeatherResponse(
        location=location,
        latitude=latitude,
        longitude=longitude,
        source="demo_fallback",
        status="fallback",
        message="Meteo de demonstration utilisee car Open-Meteo est indisponible.",
        temp_actuelle=temp_current,
        temp_min_7j=temp_min,
        temp_moyenne_7j=temp_mean,
        pluie_7j=True,
        risque_gel_7j=temp_min <= 0,
        precipitation_7j=3.2,
        precipitation_probability_max=55,
    )
