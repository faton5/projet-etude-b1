import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    app_env: str
    log_level: str
    demo_mode: bool
    db_path: Path
    cors_origins: list[str]
    open_meteo_base_url: str
    open_meteo_geocoding_url: str
    default_location: str
    default_latitude: float
    default_longitude: float
    model_path: Path | None
    mqtt_enabled: bool
    mqtt_host: str
    mqtt_port: int
    mqtt_topic_root: str


def get_settings() -> Settings:
    model_path = os.getenv("MODEL_PATH")
    return Settings(
        app_env=os.getenv("APP_ENV", "development"),
        log_level=os.getenv("LOG_LEVEL", "info"),
        demo_mode=os.getenv("DEMO_MODE", "true").lower() == "true",
        db_path=Path(os.getenv("POTAGER_DB_PATH", str(_default_db_path()))),
        cors_origins=_csv_env(
            "CORS_ORIGINS",
            "http://localhost:3000,http://127.0.0.1:3000",
        ),
        open_meteo_base_url=os.getenv(
            "OPEN_METEO_BASE_URL",
            "https://api.open-meteo.com/v1/forecast",
        ),
        open_meteo_geocoding_url=os.getenv(
            "OPEN_METEO_GEOCODING_URL",
            "https://geocoding-api.open-meteo.com/v1/search",
        ),
        default_location=os.getenv("DEFAULT_LOCATION", "Rennes"),
        default_latitude=float(os.getenv("DEFAULT_LATITUDE", "48.1173")),
        default_longitude=float(os.getenv("DEFAULT_LONGITUDE", "-1.6778")),
        model_path=Path(model_path) if model_path else None,
        mqtt_enabled=os.getenv("MQTT_ENABLED", "true").lower() == "true",
        mqtt_host=os.getenv("MQTT_HOST", "localhost"),
        mqtt_port=int(os.getenv("MQTT_PORT", "1883")),
        mqtt_topic_root=os.getenv("MQTT_TOPIC_ROOT", "farm/tomato").strip("/"),
    )


def _default_db_path() -> Path:
    return Path(__file__).resolve().parent.parent / "potager.db"


def _csv_env(name: str, default: str) -> list[str]:
    return [value.strip() for value in os.getenv(name, default).split(",") if value.strip()]
