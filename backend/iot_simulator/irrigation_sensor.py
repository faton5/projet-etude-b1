from __future__ import annotations

import logging
import os
import random

from iot_simulator.common import (
    IRRIGATION_EFFICIENCY,
    SimulatorConfig,
    WeatherCache,
    build_client,
    publish_json,
    sleep_loop,
    utc_now_iso,
)


logger = logging.getLogger("iot_simulator.irrigation")


class IrrigationSensorSimulator:
    def __init__(self, config: SimulatorConfig, interval_seconds: float = 15.0) -> None:
        self.config = config
        self.interval_seconds = interval_seconds
        self.weather = WeatherCache(config)

    def run(self) -> None:
        client = build_client("irrigation_sensor_1", self.config)
        topic = f"{self.config.topic_root}/irrigation"

        while True:
            forecast = self.weather.get()
            irrigation = self.config.irrigation
            efficiency = IRRIGATION_EFFICIENCY.get(irrigation, 0.65)
            dry_weather = forecast.precipitation_7d < 2.0
            warm_weather = forecast.temperature_mean_7d >= 18.0
            active_probability = 0.08 + (0.28 if dry_weather else 0.0) + (0.18 if warm_weather else 0.0)
            active = irrigation != "aucun" and random.random() < active_probability
            flow_l_min = 0.0
            if active:
                base_flow = {
                    "manuel": 5.5,
                    "goutte_a_goutte": 1.6,
                    "automatique": 3.2,
                    "aucun": 0.0,
                }.get(irrigation, 2.5)
                flow_l_min = max(0.0, random.gauss(base_flow * efficiency, 0.35))

            payload = {
                "sensor_id": "irrigation_sensor_1",
                "farm_id": self.config.farm_id,
                "irrigation": irrigation,
                "active": active,
                "flow_l_min": round(flow_l_min, 2),
                "timestamp": utc_now_iso(),
            }
            publish_json(client, topic, payload)
            sleep_loop(self.interval_seconds)


def main() -> None:
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO").upper())
    interval = float(os.getenv("IRRIGATION_SENSOR_INTERVAL_SECONDS", "15"))
    IrrigationSensorSimulator(SimulatorConfig.from_env(), interval_seconds=interval).run()


if __name__ == "__main__":
    main()
