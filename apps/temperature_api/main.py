from datetime import datetime, timezone
from random import uniform

from fastapi import FastAPI, Query
from pydantic import BaseModel

ROOMS = {"1": "Living Room", "2": "Bedroom", "3": "Kitchen"}
MIN_TEMPERATURE = -10.0
MAX_TEMPERATURE = 40.0


class TemperatureReading(BaseModel):
    value: float
    unit: str = "°C"
    timestamp: datetime
    location: str
    status: str = "active"
    sensor_id: str
    sensor_type: str = "temperature"
    description: str = "Simulated temperature reading"


class TemperatureSimulator:
    def read(self, sensor_id: str = "", location: str = "") -> TemperatureReading:
        location = location or ROOMS.get(sensor_id, "Unknown")
        sensor_id = sensor_id or next(
            (key for key, room in ROOMS.items() if room == location), "0"
        )
        return TemperatureReading(
            value=uniform(MIN_TEMPERATURE, MAX_TEMPERATURE),
            timestamp=datetime.now(timezone.utc),
            location=location,
            sensor_id=sensor_id,
        )


app = FastAPI(title="Temperature simulator", version="1.0.0")
simulator = TemperatureSimulator()


@app.get("/health", tags=["Health"])
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/temperature", response_model=TemperatureReading, tags=["Temperature"])
def temperature(
    location: str = "", sensor_id: str = Query(default="", alias="sensorId")
) -> TemperatureReading:
    return simulator.read(sensor_id, location)


@app.get("/temperature/{sensor_id}", response_model=TemperatureReading, tags=["Temperature"])
def temperature_by_id(sensor_id: str, location: str = "") -> TemperatureReading:
    return simulator.read(sensor_id, location)
