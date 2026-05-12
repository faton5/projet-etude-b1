from __future__ import annotations

import json
import logging
import os
import random
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import httpx
import paho.mqtt.client as mqtt


logger = logging.getLogger("iot_simulator")

SOIL_WATER_RETENTION = {
    "argileux": 1.25,
    "limoneux": 1.0,
    "sableux": 0.72,
    "calcaire": 0.82,
    "humifere": 1.18,
}

IRRIGATION_EFFICIENCY = {
    "aucun": 0.0,
    "manuel": 0.65,
    "goutte_a_goutte": 0.9,
    "automatique": 0.78,
}


@dataclass(frozen=True)
class SimulatorConfig:
    mqtt_host: str
    mqtt_port: int
    topic_root: str
    farm_id: str
    soil_type: str
    irrigation: str
    latitude: float
    longitude: float
    open_meteo_base_url: str

    @classmethod
    def from_env(cls) -> "SimulatorConfig":
        return cls(
            mqtt_host=os.getenv("MQTT_HOST", "localhost"),
            mqtt_port=int(os.getenv("MQTT_PORT", "1883")),
            topic_root=os.getenv("MQTT_TOPIC_ROOT", "farm/tomato").strip("/"),
            farm_id=os.getenv("FARM_ID", "farm_1"),
            soil_type=os.getenv("DEFAULT_SOIL_TYPE", "limoneux"),
            irrigation=os.getenv("DEFAULT_IRRIGATION", "goutte_a_goutte"),
            latitude=float(os.getenv("DEFAULT_LATITUDE", "48.1173")),
            longitude=float(os.getenv("DEFAULT_LONGITUDE", "-1.6778")),
            open_meteo_base_url=os.getenv(
                "OPEN_METEO_BASE_URL",
                "https://api.open-meteo.com/v1/forecast",
            ),
        )


@dataclass
class WeatherSnapshot:
    temperature: float
    temperature_mean_7d: float
    precipitation_7d: float
    precipitation_today: float  # Pluie du jour actuel (plus réaliste)


class WeatherCache:
    def __init__(self, config: SimulatorConfig, refresh_seconds: int = 900) -> None:
        self.config = config
        self.refresh_seconds = refresh_seconds
        self._snapshot: WeatherSnapshot | None = None
        self._last_refresh = 0.0

    def get(self) -> WeatherSnapshot:
        now = time.monotonic()
        if self._snapshot is None or now - self._last_refresh > self.refresh_seconds:
            self._snapshot = self._fetch()
            self._last_refresh = now
        return self._snapshot

    def _fetch(self) -> WeatherSnapshot:
        params = {
            "latitude": self.config.latitude,
            "longitude": self.config.longitude,
            "current": "temperature_2m",
            "daily": "temperature_2m_mean,precipitation_sum",
            "timezone": "auto",
            "forecast_days": 7,
        }

        try:
            with httpx.Client(timeout=8.0) as client:
                response = client.get(self.config.open_meteo_base_url, params=params)
                response.raise_for_status()
                data = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            logger.warning("Open-Meteo unavailable for simulator, using fallback: %s", exc)
            return WeatherSnapshot(
                temperature=random.uniform(12.0, 22.0),
                temperature_mean_7d=random.uniform(11.0, 20.0),
                precipitation_7d=random.uniform(0.0, 6.0),
                precipitation_today=random.uniform(0.0, 2.0),  # Pluie du jour fallback
            )

        daily = data.get("daily", {})
        mean_temperatures = [float(v) for v in daily.get("temperature_2m_mean", []) if v is not None]
        precipitation = [float(v) for v in daily.get("precipitation_sum", []) if v is not None]
        current = data.get("current", {})

        # Pluie du jour actuel (index 0) pour simulation réaliste
        precipitation_today = float(precipitation[0]) if precipitation else 0.0

        return WeatherSnapshot(
            temperature=round(float(current.get("temperature_2m", 16.0)), 1),
            temperature_mean_7d=round(sum(mean_temperatures) / max(len(mean_temperatures), 1), 1),
            precipitation_7d=round(sum(precipitation), 1),
            precipitation_today=round(precipitation_today, 1),
        )


def build_client(client_id: str, config: SimulatorConfig) -> mqtt.Client:
    client = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION2,
        client_id=client_id,
        reconnect_on_failure=True,
    )
    client.reconnect_delay_set(min_delay=1, max_delay=30)
    client.enable_logger(logger)
    client.connect_async(config.mqtt_host, config.mqtt_port, keepalive=30)
    client.loop_start()
    return client


def publish_json(client: mqtt.Client, topic: str, payload: dict[str, Any]) -> None:
    message = json.dumps(payload, separators=(",", ":"))
    result = client.publish(topic, message, qos=1, retain=False)
    if result.rc != mqtt.MQTT_ERR_SUCCESS:
        logger.warning("MQTT publish failed on %s with code %s", topic, result.rc)
    else:
        logger.info("MQTT publish %s %s", topic, message)


def utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def gaussian_noise(stddev: float) -> float:
    return random.gauss(0.0, stddev)


def sleep_loop(interval_seconds: float) -> None:
    time.sleep(interval_seconds + random.uniform(-0.1, 0.1) * interval_seconds)
