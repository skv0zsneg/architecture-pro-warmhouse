from typing import Protocol

import psycopg
from psycopg.rows import dict_row

from devices_service.models import Device, DeviceCreate, DeviceUpdate

CONNECT_TIMEOUT_SECONDS = 5


class DeviceStore(Protocol):
    def list(self) -> list[Device]: ...

    def get(self, device_id: int) -> Device | None: ...

    def create(self, request: DeviceCreate) -> Device: ...

    def update(self, device_id: int, request: DeviceUpdate) -> Device | None: ...

    def delete(self, device_id: int) -> bool: ...

    def ping(self) -> None: ...


class DeviceRepository:
    def __init__(self, database_url: str):
        self.database_url = database_url

    def connect(self) -> psycopg.Connection:
        return psycopg.connect(
            self.database_url, row_factory=dict_row, connect_timeout=CONNECT_TIMEOUT_SECONDS
        )

    def list(self) -> list[Device]:
        with self.connect() as connection:
            rows = connection.execute("SELECT * FROM devices.devices ORDER BY id").fetchall()
        return [Device.model_validate(row) for row in rows]

    def get(self, device_id: int) -> Device | None:
        with self.connect() as connection:
            row = connection.execute(
                "SELECT * FROM devices.devices WHERE id = %s", (device_id,)
            ).fetchone()
        return Device.model_validate(row) if row else None

    def create(self, request: DeviceCreate) -> Device:
        with self.connect() as connection:
            row = connection.execute(
                """INSERT INTO devices.devices (name, type, location, unit, home_id)
                   VALUES (%(name)s, %(type)s, %(location)s, %(unit)s, %(home_id)s)
                   RETURNING *""",
                request.model_dump(),
            ).fetchone()
        return Device.model_validate(row)

    def update(self, device_id: int, request: DeviceUpdate) -> Device | None:
        parameters = {**request.model_dump(), "id": device_id}
        with self.connect() as connection:
            row = connection.execute(
                """UPDATE devices.devices SET
                   name = COALESCE(%(name)s, name), type = COALESCE(%(type)s, type),
                   location = COALESCE(%(location)s, location), value = COALESCE(%(value)s, value),
                   unit = COALESCE(%(unit)s, unit), status = COALESCE(%(status)s, status),
                   last_updated = NOW() WHERE id = %(id)s RETURNING *""",
                parameters,
            ).fetchone()
        return Device.model_validate(row) if row else None

    def delete(self, device_id: int) -> bool:
        with self.connect() as connection:
            result = connection.execute("DELETE FROM devices.devices WHERE id = %s", (device_id,))
        return result.rowcount == 1

    def ping(self) -> None:
        with self.connect() as connection:
            connection.execute("SELECT 1 FROM devices.devices LIMIT 1")
