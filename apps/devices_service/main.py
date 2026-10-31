import logging
import os
from typing import Annotated

import psycopg
from fastapi import FastAPI, Path, Request
from fastapi.responses import JSONResponse

from devices_service.models import Device, DeviceCreate, DeviceUpdate, ValueUpdate
from devices_service.repository import DeviceRepository, DeviceStore
from devices_service.service import DeviceService

logger = logging.getLogger(__name__)
DeviceId = Annotated[int, Path(gt=0)]


def create_app(
    database_url: str | None = None, repository: DeviceStore | None = None
) -> FastAPI:
    database_url = database_url or os.getenv(
        "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/smarthome"
    )
    store = repository or DeviceRepository(database_url)
    service = DeviceService(store)
    app = FastAPI(
        title="Devices service — MVP", version="1.0.0",
        responses={
            404: {"description": "Device not found"},
            503: {"description": "Device storage unavailable"},
        },
    )

    @app.exception_handler(psycopg.IntegrityError)
    async def invalid_reference(request: Request, error: psycopg.IntegrityError) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": "Invalid device fields or unknown home_id"})

    @app.exception_handler(psycopg.Error)
    async def database_error(request: Request, error: psycopg.Error) -> JSONResponse:
        logger.error("Database operation failed: %s", error)
        return JSONResponse(status_code=503, content={"detail": "Device storage unavailable"})

    @app.get("/health", tags=["Health"])
    def health() -> dict[str, str]:
        store.ping()
        return {"status": "ok"}

    @app.get("/api/v1/devices", tags=["Devices"])
    def list_devices() -> list[Device]:
        return service.list()

    @app.get("/api/v1/devices/{device_id}", tags=["Devices"])
    def get_device(device_id: DeviceId) -> Device:
        return service.get(device_id)

    @app.post("/api/v1/devices", status_code=201, tags=["Devices"])
    def create_device(request: DeviceCreate) -> Device:
        return service.create(request)

    @app.put("/api/v1/devices/{device_id}", tags=["Devices"])
    def update_device(device_id: DeviceId, request: DeviceUpdate) -> Device:
        return service.update(device_id, request)

    @app.patch("/api/v1/devices/{device_id}/value", tags=["Devices"])
    def update_value(device_id: DeviceId, request: ValueUpdate) -> dict[str, str]:
        service.update(device_id, DeviceUpdate(value=request.value, status=request.status))
        return {"message": "Sensor value updated successfully"}

    @app.delete("/api/v1/devices/{device_id}", tags=["Devices"])
    def delete_device(device_id: DeviceId) -> dict[str, str]:
        service.delete(device_id)
        return {"message": "Sensor deleted successfully"}

    return app


app = create_app()
