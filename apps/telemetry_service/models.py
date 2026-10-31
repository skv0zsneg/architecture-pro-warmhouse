from uuid import UUID, uuid4

from pydantic import AwareDatetime, BaseModel, Field


class Reading(BaseModel):
    value: float = Field(allow_inf_nan=False)
    unit: str = "°C"
    timestamp: AwareDatetime
    location: str
    status: str = "active"
    sensor_id: str
    sensor_type: str = "temperature"
    description: str = "Temperature reading"


class Measurement(Reading):
    id: UUID = Field(default_factory=uuid4)
    device_id: int = Field(gt=0)
    home_id: int = Field(gt=0)
