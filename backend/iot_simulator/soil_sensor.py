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

    def run(self) -> None:
        client = build_client("soil_sensor_1", self.config)
        topic = f"{self.config.topic_root}/soil"

        while True:
            forecast = self.weather.get()
            retention = SOIL_WATER_RETENTION.get(self.config.soil_type, 1.0)
            irrigation_efficiency = IRRIGATION_EFFICIENCY.get(self.config.irrigation, 0.65)

            evaporation = max(0.0, forecast.temperature - 14.0) * 0.015 / retention
            rain_gain = min(0.18, forecast.precipitation_7d * 0.002 * retention)
            irrigation_gain = irrigation_efficiency * max(0.0, 55.0 - self.humidity) * 0.008
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
