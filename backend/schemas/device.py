from typing import Optional

from pydantic import BaseModel

from models.device import DeviceType, Protocol


class DeviceResponse(BaseModel):
    id: str
    name: str
    room: str
    type: DeviceType
    protocol: Protocol
    ip: str
    gen: int
    model: Optional[str] = None
    meross_uuid: Optional[str] = None
    state: bool
    icon: str


class DeviceToggleResponse(BaseModel):
    id: str
    state: bool
    success: bool


class DeviceSetStateRequest(BaseModel):
    state: bool


class DeviceUpdateRequest(BaseModel):
    name: Optional[str] = None
    room: Optional[str] = None
    type: Optional[DeviceType] = None


class BulkActionResponse(BaseModel):
    success: bool
    message: str


class RoomResponse(BaseModel):
    name: str
    devices: list[DeviceResponse]
    active: int
