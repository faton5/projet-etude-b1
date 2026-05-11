import json
import os
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.schemas import HistoryItem, PredictionRequest, PredictionResponse, PredictionResult


DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "potager.db"


def get_db_path() -> Path:
    return Path(os.getenv("POTAGER_DB_PATH", str(DEFAULT_DB_PATH)))


def get_connection() -> sqlite3.Connection:
    db_path = get_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    return connection


def init_db() -> None:
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                location TEXT NOT NULL,
                culture TEXT NOT NULL,
                saison TEXT NOT NULL,
                type_sol TEXT NOT NULL,
                irrigation TEXT NOT NULL,
                humidite_sol REAL NOT NULL,
                temp_actuelle REAL NOT NULL,
                temp_min_7j REAL NOT NULL,
                temp_moyenne_7j REAL NOT NULL,
                pluie_7j INTEGER NOT NULL,
                risque_gel_7j INTEGER NOT NULL,
                water_usage REAL NOT NULL,
                recommandation TEXT NOT NULL,
                score_confiance REAL NOT NULL,
                explication TEXT NOT NULL,
                facteurs_importants TEXT NOT NULL
            )
            """
        )


def save_prediction(
    request: PredictionRequest,
    result: PredictionResult,
) -> PredictionResponse:
    created_at = datetime.now(UTC)
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO predictions (
                created_at,
                location,
                culture,
                saison,
                type_sol,
                irrigation,
                humidite_sol,
                temp_actuelle,
                temp_min_7j,
                temp_moyenne_7j,
                pluie_7j,
                risque_gel_7j,
                water_usage,
                recommandation,
                score_confiance,
                explication,
                facteurs_importants
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                created_at.isoformat(),
                request.location,
                request.culture,
                request.saison,
                request.type_sol,
                request.irrigation,
                request.humidite_sol,
                request.temp_actuelle,
                request.temp_min_7j,
                request.temp_moyenne_7j,
                int(request.pluie_7j),
                int(request.risque_gel_7j),
                request.water_usage,
                result.recommandation,
                result.score_confiance,
                result.explication,
                json.dumps(result.facteurs_importants),
            ),
        )
        prediction_id = int(cursor.lastrowid)

    return PredictionResponse(
        id=prediction_id,
        created_at=created_at,
        recommandation=result.recommandation,
        score_confiance=result.score_confiance,
        explication=result.explication,
        facteurs_importants=result.facteurs_importants,
    )


def list_predictions(limit: int = 50) -> list[HistoryItem]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT *
            FROM predictions
            ORDER BY datetime(created_at) DESC, id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [_row_to_history_item(row) for row in rows]


def get_prediction(prediction_id: int) -> HistoryItem | None:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT *
            FROM predictions
            WHERE id = ?
            """,
            (prediction_id,),
        ).fetchone()
    if row is None:
        return None
    return _row_to_history_item(row)


def _row_to_history_item(row: sqlite3.Row) -> HistoryItem:
    data: dict[str, Any] = dict(row)
    request = PredictionRequest(
        location=data["location"],
        culture=data["culture"],
        saison=data["saison"],
        type_sol=data["type_sol"],
        irrigation=data["irrigation"],
        humidite_sol=data["humidite_sol"],
        temp_actuelle=data["temp_actuelle"],
        temp_min_7j=data["temp_min_7j"],
        temp_moyenne_7j=data["temp_moyenne_7j"],
        pluie_7j=bool(data["pluie_7j"]),
        risque_gel_7j=bool(data["risque_gel_7j"]),
        water_usage=data["water_usage"],
    )
    return HistoryItem(
        id=data["id"],
        created_at=datetime.fromisoformat(data["created_at"]),
        recommandation=data["recommandation"],
        score_confiance=data["score_confiance"],
        explication=data["explication"],
        facteurs_importants=json.loads(data["facteurs_importants"]),
        request=request,
    )
