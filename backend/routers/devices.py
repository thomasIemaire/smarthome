from fastapi import APIRouter, HTTPException

from schemas.device import (
    BulkActionResponse,
    DeviceResponse,
    DeviceSetStateRequest,
    DeviceToggleResponse,
    DeviceUpdateRequest,
    RoomResponse,
)
from services import device_service

router = APIRouter(prefix="/devices", tags=["devices"])


@router.get("", response_model=list[DeviceResponse])
async def get_devices():
    return await device_service.get_all()


@router.post("/{device_id}/toggle", response_model=DeviceToggleResponse)
async def toggle_device(device_id: str):
    result = await device_service.toggle(device_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Device {device_id} not found")
    return result


@router.post("/{device_id}/state", response_model=DeviceToggleResponse)
async def set_device_state(device_id: str, body: DeviceSetStateRequest):
    result = await device_service.set_state(device_id, body.state)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Device {device_id} not found")
    return result


@router.put("/{device_id}", response_model=DeviceResponse)
async def update_device(device_id: str, body: DeviceUpdateRequest):
    result = await device_service.update(
        device_id, name=body.name, room=body.room, device_type=body.type
    )
    if result is None:
        raise HTTPException(status_code=404, detail=f"Device {device_id} not found")
    return result


rooms_router = APIRouter(tags=["rooms"])


@rooms_router.get("/rooms", response_model=list[RoomResponse])
async def get_rooms():
    return await device_service.get_rooms()


bulk_router = APIRouter(tags=["bulk"])


@bulk_router.post("/all/on", response_model=BulkActionResponse)
async def all_on():
    return await device_service.all_on()


@bulk_router.post("/all/off", response_model=BulkActionResponse)
async def all_off():
    return await device_service.all_off()
