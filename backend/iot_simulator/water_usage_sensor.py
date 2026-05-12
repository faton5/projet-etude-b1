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


logger = logging.getLogger("iot_simulator.water_usage")


class WaterUsageSensorSimulator:
    def __init__(self, config: SimulatorConfig, interval_seconds: float = 12.0) -> None:
        self.config = config
        self.interval_seconds = interval_seconds
        self.weather = WeatherCache(config)
        self.estimated_humidity = random.uniform(38.0, 62.0)

    def run(self) -> None:
        client = build_client("water_sensor_1", self.config)
        topic = f"{self.config.topic_root}/water_usage"

        while True:
            forecast = self.weather.get()
            retention = SOIL_WATER_RETENTION.get(self.config.soil_type, 1.0)
            irrigation_efficiency = IRRIGATION_EFFICIENCY.get(self.config.irrigation, 0.65)

            dry_pressure = max(0.0, 52.0 - self.estimated_humidity) / 8.0
            heat_pressure = max(0.0, forecast.temperature - 18.0) * 0.22
            soil_pressure = max(0.0, 1.1 - retention) * 3.0
            rain_offset = min(1.2, forecast.precipitation_7d * 0.04)
            usage = (dry_pressure + heat_pressure + soil_pressure - rain_offset) * irrigation_efficiency
            usage = clamp(usage + gaussian_noise(0.2), 0.0, 24.0)

            self.estimated_humidity = clamp(
                self.estimated_humidity + min(1.0, usage * 0.05) + rain_offset * 0.08 - heat_pressure * 0.03,
                18.0,
                90.0,
            )

            payload = {
                "sensor_id": "water_sensor_1",
                "farm_id": self.config.farm_id,
                "water_usage": round(usage, 1),
                "unit": "liters_per_day_estimate",
                "timestamp": utc_now_iso(),
            }
            publish_json(client, topic, payload)
            sleep_loop(self.interval_seconds)


def main() -> None:
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO").upper())
    interval = float(os.getenv("WATER_SENSOR_INTERVAL_SECONDS", "12"))
    WaterUsageSensorSimulator(SimulatorConfig.from_env(), interval_seconds=interval).run()


if __name__ == "__main__":
    main()
