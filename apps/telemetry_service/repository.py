from typing import Protocol

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from telemetry_service.models import Measurement

CONNECT_TIMEOUT_SECONDS = 5


class MeasurementStore(Protocol):
    def save(self, measurement: Measurement) -> Measurement: ...

    def history(self, device_id: int, limit: int) -> list[Measurement]: ...

    def ping(self) -> None: ...


class MeasurementRepository:
    def __init__(self, database_url: str):
        self.database_url = database_url

    def save(self, measurement: Measurement) -> Measurement:
        with psycopg.connect(
            self.database_url, row_factory=dict_row, connect_timeout=CONNECT_TIMEOUT_SECONDS
        ) as connection:
            row = connection.execute(
                """INSERT INTO telemetry.measurements
                   (id, device_id, home_id, observed_at, payload)
                   VALUES (%s, %s, %s, %s, %s)
                   ON CONFLICT (id) DO UPDATE SET id = EXCLUDED.id RETURNING payload""",
                (measurement.id, measurement.device_id, measurement.home_id,
                 measurement.timestamp, Jsonb(measurement.model_dump(mode="json"))),
            ).fetchone()
        return Measurement.model_validate(row["payload"])

    def history(self, device_id: int, limit: int) -> list[Measurement]:
        with psycopg.connect(
            self.database_url, row_factory=dict_row, connect_timeout=CONNECT_TIMEOUT_SECONDS
        ) as connection:
            rows = connection.execute(
                """SELECT payload FROM telemetry.measurements
                   WHERE device_id = %s ORDER BY observed_at DESC, id DESC LIMIT %s""",
                (device_id, limit),
            ).fetchall()
        return [Measurement.model_validate(row["payload"]) for row in rows]

    def ping(self) -> None:
        with psycopg.connect(self.database_url, connect_timeout=CONNECT_TIMEOUT_SECONDS) as connection:
            connection.execute("SELECT 1 FROM telemetry.measurements LIMIT 1")
