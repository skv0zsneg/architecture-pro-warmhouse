from fastapi import HTTPException

from devices_service.models import Device, DeviceCreate, DeviceUpdate
from devices_service.repository import DeviceStore


class DeviceService:
    def __init__(self, repository: DeviceStore):
        self.repository = repository

    def list(self) -> list[Device]:
        return self.repository.list()

    def get(self, device_id: int) -> Device:
        return self.require_device(self.repository.get(device_id))

    def create(self, request: DeviceCreate) -> Device:
        unit = request.unit or ("°C" if request.type == "temperature" else "")
        return self.repository.create(request.model_copy(update={"unit": unit}))

    def update(self, device_id: int, request: DeviceUpdate) -> Device:
        return self.require_device(self.repository.update(device_id, request))

    def delete(self, device_id: int) -> None:
        if not self.repository.delete(device_id):
            raise HTTPException(404, "Device not found")

    def require_device(self, device: Device | None) -> Device:
        if device is None:
            raise HTTPException(404, "Device not found")
        return device
