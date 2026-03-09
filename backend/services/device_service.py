import logging
from typing import Optional

from models.device import Device, DeviceType, Protocol
from schemas.device import DeviceResponse, RoomResponse
from services.meross_service import meross_service
from services.persistence import persistence
from services.shelly_service import shelly_service

logger = logging.getLogger(__name__)


def _device_to_response(device: Device) -> DeviceResponse:
    return DeviceResponse(
        id=device.id,
        name=device.name,
        room=device.room,
        type=device.type,
        protocol=device.protocol,
        ip=device.ip,
        gen=device.gen,
        model=device.model,
        meross_uuid=device.meross_uuid,
        state=device.state,
        icon=device.icon,
    )


async def _poll_device_state(device: Device) -> bool:
    try:
        if device.protocol == Protocol.shelly and device.ip:
            state = await shelly_service.get_state(device.ip, device.gen)
            if state is not None:
                device.state = state
                persistence.device_states[device.id] = state
                return True
        elif device.protocol == Protocol.meross and device.meross_uuid:
            state = await meross_service.get_state(device.meross_uuid)
            if state is not None:
                device.state = state
                persistence.device_states[device.id] = state
                return True
    except Exception as exc:
        logger.warning("Failed to poll state for device %s: %s", device.id, exc)
    return False


async def get_all() -> list[DeviceResponse]:
    devices = persistence.devices
    for device in devices:
        await _poll_device_state(device)
    return [_device_to_response(d) for d in devices]


async def toggle(device_id: str) -> Optional[dict]:
    device = persistence.find_device(device_id)
    if device is None:
        return None

    new_state = not device.state
    success = await _set_device_state(device, new_state)
    return {"id": device.id, "state": device.state, "success": success}


async def set_state(device_id: str, state: bool) -> Optional[dict]:
    device = persistence.find_device(device_id)
    if device is None:
        return None

    success = await _set_device_state(device, state)
    return {"id": device.id, "state": device.state, "success": success}


async def _set_device_state(device: Device, state: bool) -> bool:
    success = False

    if device.protocol == Protocol.shelly and device.ip:
        success = await shelly_service.set_state(device.ip, state, device.gen)
    elif device.protocol == Protocol.meross and device.meross_uuid:
        success = await meross_service.set_state(device.meross_uuid, state)
    elif device.protocol == Protocol.simulation:
        success = True

    if success:
        device.state = state
        persistence.device_states[device.id] = state
        persistence.save_devices()
    else:
        logger.warning("Failed to set state for device %s, updating locally anyway", device.id)
        device.state = state
        persistence.device_states[device.id] = state
        persistence.save_devices()

    return success


async def update(
    device_id: str,
    name: Optional[str] = None,
    room: Optional[str] = None,
    device_type: Optional[DeviceType] = None,
) -> Optional[DeviceResponse]:
    device = persistence.find_device(device_id)
    if device is None:
        return None

    if name is not None:
        device.name = name
    if room is not None:
        device.room = room
    if device_type is not None:
        device.type = device_type

    persistence.save_devices()
    return _device_to_response(device)


async def all_on() -> dict:
    for device in persistence.devices:
        await _set_device_state(device, True)
    return {"success": True, "message": f"Turned on {len(persistence.devices)} devices"}


async def all_off() -> dict:
    for device in persistence.devices:
        await _set_device_state(device, False)
    return {"success": True, "message": f"Turned off {len(persistence.devices)} devices"}


async def get_rooms() -> list[RoomResponse]:
    rooms: dict[str, list[Device]] = {}
    for device in persistence.devices:
        room_name = device.room or "Unassigned"
        if room_name not in rooms:
            rooms[room_name] = []
        rooms[room_name].append(device)

    result = []
    for room_name, devices in rooms.items():
        active_count = sum(1 for d in devices if d.state)
        result.append(
            RoomResponse(
                name=room_name,
                devices=[_device_to_response(d) for d in devices],
                active=active_count,
            )
        )
    return result
