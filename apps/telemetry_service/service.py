import logging

import httpx
from fastapi import HTTPException

from telemetry_service.models import Measurement, Reading
from telemetry_service.repository import MeasurementStore

logger = logging.getLogger(__name__)


class DeviceGateway:
    def __init__(self, client: httpx.Client, base_url: str):
        self.client = client
        self.base_url = base_url

    def get(self, device_id: int) -> dict:
        response = self.client.get(f"{self.base_url}/api/v1/devices/{device_id}")
        if response.status_code == 404:
            raise HTTPException(404, "Device not found")
        response.raise_for_status()
        return response.json()

    def list_temperature_devices(self) -> list[dict]:
        response = self.client.get(f"{self.base_url}/api/v1/devices")
        response.raise_for_status()
        return [device for device in response.json() if device["type"] == "temperature"]


class TemperatureGateway:
    def __init__(self, client: httpx.Client, base_url: str):
        self.client = client
        self.base_url = base_url

    def read(self, device: dict) -> Reading:
        response = self.client.get(
            f"{self.base_url}/temperature/{device['id']}",
            params={"location": device["location"]},
        )
        response.raise_for_status()
        return Reading.model_validate(response.json())


class MeasurementService:
    def __init__(self, repository: MeasurementStore, source: TemperatureGateway):
        self.repository = repository
        self.source = source

    def capture(self, device: dict) -> Measurement:
        if device["type"] != "temperature":
            raise HTTPException(422, "Device is not a temperature sensor")
        reading = self.source.read(device)
        measurement = Measurement(
            **reading.model_dump(), device_id=device["id"], home_id=device["home_id"]
        )
        return self.repository.save(measurement)

    def accept(self, measurement: Measurement, device: dict) -> Measurement:
        if measurement.home_id != device["home_id"]:
            raise HTTPException(422, "Device does not belong to this home")
        if measurement.sensor_id != str(device["id"]):
            raise HTTPException(422, "Sensor ID must match device ID")
        return self.repository.save(measurement)


class Collector:
    def __init__(self, devices: DeviceGateway, measurements: MeasurementService):
        self.devices = devices
        self.measurements = measurements

    def collect(self) -> None:
        for device in self.devices.list_temperature_devices():
            try:
                self.measurements.capture(device)
            except Exception:
                logger.exception("Cannot collect measurement for device %s", device["id"])
