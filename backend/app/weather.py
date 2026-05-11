from statistics import mean
from typing import Any

import httpx

from app.config import get_settings
from app.demo import fallback_weather
from app.schemas import WeatherResponse


DAILY_VARIABLES = (
    "temperature_2m_min",
    "temperature_2m_mean",
    "precipitation_sum",
    "precipitation_probability_max",
)
DEFAULT_FORECAST_DAYS = 7
RAIN_THRESHOLD_MM = 1.0
RAIN_PROBABILITY_THRESHOLD = 50
FROST_THRESHOLD_C = 0.0


class WeatherServiceError(RuntimeError):
    pass


def get_default_latitude() -> float:
    return get_settings().default_latitude


def get_default_longitude() -> float:
    return get_settings().default_longitude


def get_default_location() -> str:
    return get_settings().default_location


def get_open_meteo_base_url() -> str:
    return get_settings().open_meteo_base_url


def get_weather_forecast(
    location: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
) -> WeatherResponse:
    resolved_location = location or get_default_location()
    resolved_latitude = latitude if latitude is not None else get_default_latitude()
    resolved_longitude = longitude if longitude is not None else get_default_longitude()

    try:
        data = _fetch_open_meteo(resolved_latitude, resolved_longitude)
    except WeatherServiceError:
        if get_settings().demo_mode:
            return fallback_weather(resolved_location, resolved_latitude, resolved_longitude)
        raise
    daily = data.get("daily")
    if not isinstance(daily, dict):
        raise WeatherServiceError("Open-Meteo response does not contain daily forecasts")

    return _build_weather_response(
        location=resolved_location,
        latitude=resolved_latitude,
        longitude=resolved_longitude,
        current=data.get("current"),
        daily=daily,
    )


def _fetch_open_meteo(latitude: float, longitude: float) -> dict[str, Any]:
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": "temperature_2m",
        "daily": ",".join(DAILY_VARIABLES),
        "timezone": "auto",
        "forecast_days": DEFAULT_FORECAST_DAYS,
    }

    try:
        with httpx.Client(timeout=8.0) as client:
            response = client.get(get_open_meteo_base_url(), params=params)
            response.raise_for_status()
            return response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise WeatherServiceError("Open-Meteo forecast is unavailable") from exc


def _build_weather_response(
    location: str,
    latitude: float,
    longitude: float,
    current: Any,
    daily: dict[str, Any],
) -> WeatherResponse:
    min_temperatures = _read_number_list(daily, "temperature_2m_min")
    mean_temperatures = _read_number_list(daily, "temperature_2m_mean")
    precipitation = _read_number_list(daily, "precipitation_sum", required=False)
    precipitation_probabilities = _read_number_list(
        daily,
        "precipitation_probability_max",
        required=False,
    )

    if not min_temperatures or not mean_temperatures:
        raise WeatherServiceError("Open-Meteo response is missing temperature data")

    current_temperature = _read_current_temperature(current)
    total_rain = round(sum(precipitation), 1) if precipitation else 0.0
    max_rain_probability = max(precipitation_probabilities) if precipitation_probabilities else 0.0
    pluie_7j = total_rain >= RAIN_THRESHOLD_MM or max_rain_probability >= RAIN_PROBABILITY_THRESHOLD
    temp_min_7j = round(min(min_temperatures), 1)

    return WeatherResponse(
        location=location,
        latitude=latitude,
        longitude=longitude,
        source="open_meteo",
        status="ok",
        message="Meteo 7 jours recuperee depuis Open-Meteo.",
        temp_actuelle=current_temperature,
        temp_min_7j=temp_min_7j,
        temp_moyenne_7j=round(mean(mean_temperatures), 1),
        pluie_7j=pluie_7j,
        risque_gel_7j=temp_min_7j <= FROST_THRESHOLD_C,
        precipitation_7j=total_rain,
        precipitation_probability_max=max_rain_probability,
    )


def _read_number_list(
    daily: dict[str, Any],
    key: str,
    required: bool = True,
) -> list[float]:
    values = daily.get(key)
    if values is None:
        if required:
            raise WeatherServiceError(f"Open-Meteo response is missing {key}")
        return []
    if not isinstance(values, list):
        raise WeatherServiceError(f"Open-Meteo field {key} has an invalid format")

    result: list[float] = []
    for value in values[:DEFAULT_FORECAST_DAYS]:
        if value is None:
            continue
        result.append(float(value))
    return result


def _read_current_temperature(current: Any) -> float:
    if not isinstance(current, dict):
        raise WeatherServiceError("Open-Meteo response does not contain current weather")
    value = current.get("temperature_2m")
    if value is None:
        raise WeatherServiceError("Open-Meteo response is missing current temperature")
    return round(float(value), 1)
