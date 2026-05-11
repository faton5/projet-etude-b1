from __future__ import annotations

import logging
import os
import threading
import time

from iot_simulator.common import SimulatorConfig
from iot_simulator.irrigation_sensor import IrrigationSensorSimulator
from iot_simulator.soil_sensor import SoilSensorSimulator
from iot_simulator.water_usage_sensor import WaterUsageSensorSimulator


def main() -> None:
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO").upper(),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    config = SimulatorConfig.from_env()
    simulators = [
        SoilSensorSimulator(
            config,
            interval_seconds=float(os.getenv("SOIL_SENSOR_INTERVAL_SECONDS", "10")),
        ),
        IrrigationSensorSimulator(
            config,
            interval_seconds=float(os.getenv("IRRIGATION_SENSOR_INTERVAL_SECONDS", "15")),
        ),
        WaterUsageSensorSimulator(
            config,
            interval_seconds=float(os.getenv("WATER_SENSOR_INTERVAL_SECONDS", "12")),
        ),
    ]

    for simulator in simulators:
        thread = threading.Thread(target=simulator.run, daemon=True)
        thread.start()

    while True:
        time.sleep(60)


if __name__ == "__main__":
    main()
