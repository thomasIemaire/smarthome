import logging
import uuid
from typing import Optional

from models.group import Group
from schemas.group import GroupResponse
from services import device_service
from services.persistence import persistence

logger = logging.getLogger(__name__)


def _compute_active(group: Group) -> bool:
    for device_id in group.device_ids:
        device = persistence.find_device(device_id)
        if device is not None and device.state:
            return True
    return False


def _group_to_response(group: Group) -> GroupResponse:
    return GroupResponse(
        id=group.id,
        name=group.name,
        device_ids=group.device_ids,
        active=_compute_active(group),
    )


async def get_all() -> list[GroupResponse]:
    return [_group_to_response(g) for g in persistence.groups]


async def create(name: str, device_ids: list[str]) -> GroupResponse:
    group_id = str(uuid.uuid4())
    group = Group(id=group_id, name=name, device_ids=device_ids)
    persistence.groups.append(group)
    persistence.save_groups()
    return _group_to_response(group)


async def toggle(group_id: str) -> Optional[dict]:
    group = persistence.find_group(group_id)
    if group is None:
        return None

    active = _compute_active(group)

    if active:
        target_state = False
    else:
        target_state = True

    for device_id in group.device_ids:
        await device_service.set_state(device_id, target_state)

    new_active = _compute_active(group)
    return {"success": True, "group_id": group.id, "active": new_active}


async def update(
    group_id: str,
    name: Optional[str] = None,
    device_ids: Optional[list[str]] = None,
) -> Optional[GroupResponse]:
    group = persistence.find_group(group_id)
    if group is None:
        return None

    if name is not None:
        group.name = name
    if device_ids is not None:
        group.device_ids = device_ids

    persistence.save_groups()
    return _group_to_response(group)


async def delete(group_id: str) -> bool:
    group = persistence.find_group(group_id)
    if group is None:
        return False

    persistence.groups.remove(group)
    persistence.save_groups()
    return True
