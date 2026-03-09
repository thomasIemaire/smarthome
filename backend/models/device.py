from enum import Enum
from typing import Optional

from pydantic import BaseModel


class DeviceType(str, Enum):
    plug = "plug"
    light = "light"


class Protocol(str, Enum):
    shelly = "shelly"
    meross = "meross"
    simulation = "simulation"


class Device(BaseModel):
    id: str
    name: str = ""
    room: str = ""
    type: DeviceType = DeviceType.plug
    protocol: Protocol = Protocol.shelly
    ip: str = ""
    gen: int = 1
    model: Optional[str] = None
    meross_uuid: Optional[str] = None
    state: bool = False
    icon: str = "plug"
