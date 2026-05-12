from __future__ import annotations

import logging
import os
import random

from iot_simulator.common import (
    IRRIGATION_EFFICIENCY,
    SOIL_WATER_RETENTION,
    SimulatorConfig,
    WeatherCache,
    build_client,
    clamp,
    gaussian_noise,
    publish_json,
    sleep_loop,
    utc_now_iso,
)


logger = logging.getLogger("iot_simulator.soil")


class SoilSensorSimulator:
    def __init__(self, config: SimulatorConfig, interval_seconds: float = 10.0) -> None:
        self.config = config
        self.interval_seconds = interval_seconds
        self.weather = WeatherCache(config)
        retention = SOIL_WATER_RETENTION.get(config.soil_type, 1.0)
        self.humidity = clamp(50.0 * retention + random.uniform(-5, 5), 18.0, 88.0)
        self.last_rain_mm = 0.0  # Track pluie précédente pour détecter changements

    def run(self) -> None:
        client = build_client("soil_sensor_1", self.config)
        topic = f"{self.config.topic_root}/soil"

        while True:
            forecast = self.weather.get()
            retention = SOIL_WATER_RETENTION.get(self.config.soil_type, 1.0)
            irrigation_efficiency = IRRIGATION_EFFICIENCY.get(self.config.irrigation, 0.65)

            # Évaporation : augmente avec la température
            # Plus il fait chaud, plus l'eau s'évapore rapidement
            evaporation = max(0.0, forecast.temperature - 14.0) * 0.015 / retention

            # Gain par pluie DU JOUR (plus réaliste que total 7j)
            # Si pluie > pluie précédente, c'est qu'il pleut maintenant → boost humidité
            rain_delta = forecast.precipitation_today - self.last_rain_mm
            if rain_delta > 0.5:  # Il pleut actuellement (>0.5mm nouveau)
                rain_gain = min(0.35, rain_delta * 0.15 * retention)  # Impact fort
            elif forecast.precipitation_today > 0.1:  # Pluie résiduelle
                rain_gain = min(0.18, forecast.precipitation_today * 0.06 * retention)
            else:
                rain_gain = 0.0
            self.last_rain_mm = forecast.precipitation_today

            # Gain par irrigation : compense si sol trop sec
            # Plus le sol est sec, plus l'irrigation apporte d'eau
            irrigation_gain = irrigation_efficiency * max(0.0, 55.0 - self.humidity) * 0.008

            # Drift total avec bruit gaussien pour variabilité naturelle
            drift = rain_gain + irrigation_gain - evaporation + gaussian_noise(0.12)

            self.humidity = clamp(self.humidity + drift, 12.0, 96.0)
            payload = {
                "sensor_id": "soil_sensor_1",
                "farm_id": self.config.farm_id,
                "humidity": round(self.humidity, 1),
                "soil_type": self.config.soil_type,
                "timestamp": utc_now_iso(),
            }
            publish_json(client, topic, payload)
            sleep_loop(self.interval_seconds)


def main() -> None:
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO").upper())
    interval = float(os.getenv("SOIL_SENSOR_INTERVAL_SECONDS", "10"))
    SoilSensorSimulator(SimulatorConfig.from_env(), interval_seconds=interval).run()


if __name__ == "__main__":
    main()
