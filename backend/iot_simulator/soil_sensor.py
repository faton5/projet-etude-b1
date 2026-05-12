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
        self.last_rain_mm = 0.0
        self.recent_rain_effect = 0.0
        self.manual_watering_ticks = 0

    def run(self) -> None:
        client = build_client("soil_sensor_1", self.config)
        topic = f"{self.config.topic_root}/soil"

        while True:
            forecast = self.weather.get()
            retention = SOIL_WATER_RETENTION.get(self.config.soil_type, 1.0)
            irrigation_efficiency = IRRIGATION_EFFICIENCY.get(self.config.irrigation, 0.65)

            # Evaporation: warm weather dries the soil faster.
            evaporation = max(0.0, forecast.temperature - 12.0) * 0.022 / retention

            # Rain has memory. A shower should keep the soil wetter for a while,
            # then the effect slowly fades instead of snapping back to 52%.
            rain_delta = forecast.precipitation_today - self.last_rain_mm
            if rain_delta > 0.2:
                self.recent_rain_effect = clamp(self.recent_rain_effect + rain_delta * 0.9, 0.0, 14.0)
            elif forecast.precipitation_today <= 0.1:
                self.recent_rain_effect *= 0.965
            else:
                self.recent_rain_effect *= 0.985

            rain_gain = min(0.28, self.recent_rain_effect * 0.018 * retention)
            self.last_rain_mm = forecast.precipitation_today

            # Manual watering is occasional. Drip/automatic watering can react
            # when the soil becomes dry, but no mode constantly pulls to 55%.
            irrigation_gain = 0.0
            if self.config.irrigation == "manuel":
                if self.manual_watering_ticks > 0:
                    irrigation_gain = random.uniform(0.45, 0.95) * irrigation_efficiency * retention
                    self.manual_watering_ticks -= 1
                elif self.humidity < 34.0 and forecast.precipitation_7d < 4.0 and random.random() < 0.12:
                    self.manual_watering_ticks = random.randint(6, 14)
            elif self.config.irrigation == "automatique" and self.humidity < 43.0:
                irrigation_gain = min(0.38, (48.0 - self.humidity) * 0.035) * irrigation_efficiency
            elif self.config.irrigation == "goutte_a_goutte" and self.humidity < 50.0:
                irrigation_gain = min(0.22, (52.0 - self.humidity) * 0.018) * irrigation_efficiency

            weekly_rain_cooldown = min(0.08, forecast.precipitation_7d * 0.003)
            drift = rain_gain + irrigation_gain + weekly_rain_cooldown - evaporation + gaussian_noise(0.18)

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
