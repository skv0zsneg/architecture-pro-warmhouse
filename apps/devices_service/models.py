from typing import Annotated

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, StringConstraints

DeviceName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
DeviceType = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=50)]
DeviceStatus = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=20)]
DeviceValue = Annotated[float, Field(allow_inf_nan=False)]
DeviceUnit = Annotated[str, StringConstraints(max_length=20)]


class DeviceCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: DeviceName
    type: DeviceType
    location: DeviceName
    unit: DeviceUnit | None = None
    home_id: int = Field(default=1, gt=0)


class Device(BaseModel):
    id: int
    home_id: int
    name: str
    type: str
    location: str
    value: float
    unit: str
    status: str
    last_updated: AwareDatetime
    created_at: AwareDatetime


class DeviceUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: DeviceName | None = None
    type: DeviceType | None = None
    location: DeviceName | None = None
    value: DeviceValue | None = None
    unit: DeviceUnit | None = None
    status: DeviceStatus | None = None


class ValueUpdate(BaseModel):
    value: DeviceValue
    status: DeviceStatus
