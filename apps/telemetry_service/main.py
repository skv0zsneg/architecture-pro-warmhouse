import asyncio
import logging
import os
from contextlib import asynccontextmanager, suppress
from dataclasses import dataclass

import httpx
import psycopg
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import JSONResponse

from telemetry_service.models import Measurement, Reading
from telemetry_service.repository import MeasurementRepository, MeasurementStore
from telemetry_service.service import Collector, DeviceGateway, MeasurementService, TemperatureGateway

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Settings:
    database_url: str = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/smarthome")
    devices_url: str = os.getenv("DEVICES_API_URL", "http://devices-service:8082")
    temperature_url: str = os.getenv("TEMPERATURE_API_URL", "http://temperature-api:8081")
    poll_interval: float = float(os.getenv("POLL_INTERVAL_SECONDS", "5"))


async def poll(collector: Collector, interval: float) -> None:
    while True:
        try:
            await asyncio.to_thread(collector.collect)
        except Exception:
            logger.exception("Collection cycle failed; will retry")
        await asyncio.sleep(interval)


def create_app(
    settings: Settings,
    repository: MeasurementStore | None = None,
    http_client: httpx.Client | None = None,
) -> FastAPI:
    store = repository or MeasurementRepository(settings.database_url)
    client = http_client or httpx.Client(timeout=5)
    devices = DeviceGateway(client, settings.devices_url)
    measurements = MeasurementService(store, TemperatureGateway(client, settings.temperature_url))
    collector = Collector(devices, measurements)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        task = asyncio.create_task(poll(collector, settings.poll_interval)) if settings.poll_interval > 0 else None
        yield
        if task:
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task
        if http_client is None:
            client.close()

    app = FastAPI(
        title="Telemetry service — MVP", version="1.0.0", lifespan=lifespan,
        responses={
            404: {"description": "Device or measurement not found"},
            502: {"description": "Upstream service unavailable"},
            503: {"description": "Telemetry storage unavailable"},
        },
    )

    @app.exception_handler(httpx.HTTPError)
    async def upstream_error(request: Request, error: httpx.HTTPError):
        logger.warning("Upstream request failed: %s", error)
        return JSONResponse(status_code=502, content={"detail": "Upstream service unavailable"})

    @app.exception_handler(psycopg.Error)
    async def database_error(request: Request, error: psycopg.Error):
        logger.error("Database operation failed: %s", error)
        return JSONResponse(status_code=503, content={"detail": "Telemetry storage unavailable"})

    @app.get("/health", tags=["Health"])
    def health() -> dict[str, str]:
        store.ping()
        return {"status": "ok"}

    @app.get("/api/v1/measurements", response_model=list[Measurement], tags=["Measurements"])
    def history(device_id: int = Query(gt=0), limit: int = Query(default=100, ge=1, le=1000)):
        return store.history(device_id, limit)

    @app.get("/api/v1/measurements/latest", response_model=Measurement, tags=["Measurements"])
    def latest(device_id: int = Query(gt=0)):
        readings = store.history(device_id, 1)
        if not readings:
            raise HTTPException(404, "No measurements for this device")
        return readings[0]

    @app.post("/api/v1/measurements", response_model=Measurement, status_code=201, tags=["Measurements"])
    def ingest(measurement: Measurement):
        return measurements.accept(measurement, devices.get(measurement.device_id))

    @app.get("/temperature/{device_id}", response_model=Reading, tags=["Legacy compatibility"])
    def fresh_temperature(device_id: int):
        return measurements.capture(devices.get(device_id))

    @app.get("/temperature", response_model=Reading, tags=["Legacy compatibility"])
    def temperature_by_location(location: str = Query(min_length=1)):
        device = next(
            (device for device in devices.list_temperature_devices() if device["location"] == location),
            None,
        )
        if device is None:
            raise HTTPException(404, "No temperature sensor at this location")
        return measurements.capture(device)

    return app


app = create_app(Settings())
