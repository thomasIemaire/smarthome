from pydantic import BaseModel

from schemas.device import DeviceResponse


class DiscoverResponse(BaseModel):
    success: bool
    shelly_count: int
    meross_count: int
    total: int
    devices: list[DeviceResponse]
