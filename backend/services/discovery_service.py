import asyncio
import logging

from models.device import Device, DeviceType, Protocol
from schemas.device import DeviceResponse
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


async def discover_all() -> dict:
    shelly_task = asyncio.create_task(shelly_service.scan())
    meross_task = asyncio.create_task(meross_service.discover())

    shelly_results, meross_results = await asyncio.gather(
        shelly_task, meross_task, return_exceptions=True
    )

    if isinstance(shelly_results, Exception):
        logger.error("Shelly scan failed: %s", shelly_results)
        shelly_results = []
    if isinstance(meross_results, Exception):
        logger.error("Meross discover failed: %s", meross_results)
        meross_results = []

    existing_by_id = {d.id: d for d in persistence.devices}

    new_devices: list[Device] = []

    for shelly in shelly_results:
        device_id = shelly["id"]
        if device_id in existing_by_id:
            existing = existing_by_id[device_id]
            existing.ip = shelly["ip"]
            existing.gen = shelly.get("gen", 1)
            existing.model = shelly.get("model", existing.model)
        else:
            is_light = "light" in shelly.get("type", "").lower() or "dimmer" in shelly.get("type", "").lower()
            device = Device(
                id=device_id,
                name=shelly.get("name", f"Shelly {shelly.get('type', 'Unknown')}"),
                room="",
                type=DeviceType.light if is_light else DeviceType.plug,
                protocol=Protocol.shelly,
                ip=shelly["ip"],
                gen=shelly.get("gen", 1),
                model=shelly.get("model", ""),
                state=False,
                icon="bulb" if is_light else "plug",
            )
            new_devices.append(device)
            existing_by_id[device_id] = device

    for meross_dev in meross_results:
        device_id = f"meross_{meross_dev['uuid']}"
        if device_id in existing_by_id:
            existing = existing_by_id[device_id]
            existing.state = meross_dev.get("is_on", existing.state)
        else:
            dev_type_str = meross_dev.get("device_type", "").lower()
            is_light = "light" in dev_type_str or "bulb" in dev_type_str
            device = Device(
                id=device_id,
                name=meross_dev.get("name", "Meross Device"),
                room="",
                type=DeviceType.light if is_light else DeviceType.plug,
                protocol=Protocol.meross,
                meross_uuid=meross_dev["uuid"],
                ip="",
                state=meross_dev.get("is_on", False),
                icon="bulb" if is_light else "plug",
            )
            new_devices.append(device)
            existing_by_id[device_id] = device

    persistence.devices.extend(new_devices)
    persistence.save_devices()

    all_responses = [_device_to_response(d) for d in persistence.devices]

    return {
        "success": True,
        "shelly_count": len(shelly_results),
        "meross_count": len(meross_results),
        "total": len(persistence.devices),
        "devices": all_responses,
    }
