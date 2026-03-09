from typing import Optional

from pydantic import BaseModel


class GroupResponse(BaseModel):
    id: str
    name: str
    device_ids: list[str]
    active: bool


class GroupCreateRequest(BaseModel):
    name: str
    device_ids: list[str]


class GroupUpdateRequest(BaseModel):
    name: Optional[str] = None
    device_ids: Optional[list[str]] = None


class GroupToggleResponse(BaseModel):
    success: bool
    group_id: str
    active: bool
