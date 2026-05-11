from __future__ import annotations

import json
import logging
import threading
from typing import Any

import paho.mqtt.client as mqtt
from pydantic import ValidationError

from app.config import get_settings
from app.database import save_iot_reading
from app.demo import demo_iot_snapshot
from app.schemas import (
    IotLiveResponse,
    IrrigationSensorPayload,
    SoilSensorPayload,
    WaterUsageSensorPayload,
)


logger = logging.getLogger("potager.mqtt")


class IotStateStore:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._soil: SoilSensorPayload | None = None
        self._irrigation: IrrigationSensorPayload | None = None
        self._water_usage: WaterUsageSensorPayload | None = None
        self._mqtt_connected = False
        self._mqtt_status = "reconnecting"

    def set_connected(self, value: bool) -> None:
        with self._lock:
            self._mqtt_connected = value
            self._mqtt_status = "connected" if value else "reconnecting"

    def set_status(self, value: str) -> None:
        with self._lock:
            self._mqtt_status = value

    def clear(self) -> None:
        with self._lock:
            self._soil = None
            self._irrigation = None
            self._water_usage = None
            self._mqtt_connected = False
            self._mqtt_status = "reconnecting"

    def update(self, topic: str, payload: dict[str, Any]) -> None:
        parsed = self._parse_payload(topic, payload)
        save_iot_reading(
            topic=topic,
            sensor_id=parsed.sensor_id,
            farm_id=parsed.farm_id,
            observed_at=parsed.timestamp,
            payload=payload,
        )
        with self._lock:
            if isinstance(parsed, SoilSensorPayload):
                self._soil = parsed
            elif isinstance(parsed, IrrigationSensorPayload):
                self._irrigation = parsed
            elif isinstance(parsed, WaterUsageSensorPayload):
                self._water_usage = parsed

    def snapshot(self) -> IotLiveResponse:
        with self._lock:
            updates = [
                item.timestamp
                for item in (self._soil, self._irrigation, self._water_usage)
                if item is not None
            ]
            farm_id = (
                self._soil.farm_id
                if self._soil is not None
                else self._irrigation.farm_id
                if self._irrigation is not None
                else self._water_usage.farm_id
                if self._water_usage is not None
                else None
            )
            response = IotLiveResponse(
                soil_humidity=self._soil.humidity if self._soil else None,
                water_usage=self._water_usage.water_usage if self._water_usage else None,
                irrigation=self._irrigation.irrigation if self._irrigation else None,
                irrigation_active=self._irrigation.active if self._irrigation else None,
                mqtt_connected=self._mqtt_connected,
                mqtt_status=self._mqtt_status,
                last_update=max(updates) if updates else None,
                farm_id=farm_id,
                soil_sensor_id=self._soil.sensor_id if self._soil else None,
                irrigation_sensor_id=self._irrigation.sensor_id if self._irrigation else None,
                water_sensor_id=self._water_usage.sensor_id if self._water_usage else None,
            )
        if response.last_update is None and get_settings().demo_mode:
            return demo_iot_snapshot(mqtt_connected=response.mqtt_connected)
        return response

    def _parse_payload(
        self,
        topic: str,
        payload: dict[str, Any],
    ) -> SoilSensorPayload | IrrigationSensorPayload | WaterUsageSensorPayload:
        if topic.endswith("/soil"):
            return SoilSensorPayload(**payload)
        if topic.endswith("/irrigation"):
            return IrrigationSensorPayload(**payload)
        if topic.endswith("/water_usage"):
            return WaterUsageSensorPayload(**payload)
        raise ValueError(f"Unsupported MQTT topic: {topic}")


iot_state = IotStateStore()


class MqttConsumer:
    def __init__(self, state: IotStateStore) -> None:
        self.state = state
        settings = get_settings()
        self.enabled = settings.mqtt_enabled
        self.host = settings.mqtt_host
        self.port = settings.mqtt_port
        self.topic_root = settings.mqtt_topic_root
        self.client: mqtt.Client | None = None

    def start(self) -> None:
        if not self.enabled:
            self.state.set_status("disabled")
            logger.info("MQTT consumer disabled")
            return

        client = mqtt.Client(
            mqtt.CallbackAPIVersion.VERSION2,
            client_id="potager_fastapi_consumer",
            reconnect_on_failure=True,
        )
        client.reconnect_delay_set(min_delay=1, max_delay=30)
        client.enable_logger(logger)
        client.on_connect = self._on_connect
        client.on_disconnect = self._on_disconnect
        client.on_message = self._on_message
        self.client = client

        logger.info("Starting MQTT consumer on %s:%s", self.host, self.port)
        try:
            client.connect_async(self.host, self.port, keepalive=30)
            client.loop_start()
        except OSError as exc:
            self.state.set_connected(False)
            logger.warning("MQTT startup failed: %s", exc)

    def stop(self) -> None:
        if self.client is None:
            return
        logger.info("Stopping MQTT consumer")
        self.client.loop_stop()
        self.client.disconnect()
        self.state.set_connected(False)

    def _on_connect(
        self,
        client: mqtt.Client,
        _userdata: Any,
        _flags: mqtt.ConnectFlags,
        reason_code: mqtt.ReasonCode,
        _properties: mqtt.Properties | None,
    ) -> None:
        if reason_code == 0:
            topic = f"{self.topic_root}/#"
            self.state.set_connected(True)
            client.subscribe(topic, qos=1)
            logger.info("MQTT connected, subscribed to %s", topic)
        else:
            self.state.set_connected(False)
            logger.warning("MQTT connection refused: %s", reason_code)

    def _on_disconnect(
        self,
        _client: mqtt.Client,
        _userdata: Any,
        _disconnect_flags: mqtt.DisconnectFlags,
        reason_code: mqtt.ReasonCode,
        _properties: mqtt.Properties | None,
    ) -> None:
        self.state.set_connected(False)
        logger.warning("MQTT disconnected: %s", reason_code)

    def _on_message(
        self,
        _client: mqtt.Client,
        _userdata: Any,
        message: mqtt.MQTTMessage,
    ) -> None:
        try:
            payload = json.loads(message.payload.decode("utf-8"))
            if not isinstance(payload, dict):
                raise ValueError("payload must be a JSON object")
            self.state.update(message.topic, payload)
            logger.info("MQTT topic received: %s", message.topic)
        except (json.JSONDecodeError, UnicodeDecodeError, ValueError, ValidationError) as exc:
            logger.warning("Invalid MQTT payload on %s: %s", message.topic, exc)


mqtt_consumer = MqttConsumer(iot_state)
