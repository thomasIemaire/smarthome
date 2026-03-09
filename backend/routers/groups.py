from fastapi import APIRouter, HTTPException, Response, status

from schemas.group import (
    GroupCreateRequest,
    GroupResponse,
    GroupToggleResponse,
    GroupUpdateRequest,
)
from services import group_service

router = APIRouter(prefix="/groups", tags=["groups"])


@router.get("", response_model=list[GroupResponse])
async def get_groups():
    return await group_service.get_all()


@router.post("", response_model=GroupResponse, status_code=status.HTTP_201_CREATED)
async def create_group(body: GroupCreateRequest):
    return await group_service.create(name=body.name, device_ids=body.device_ids)


@router.post("/{group_id}/toggle", response_model=GroupToggleResponse)
async def toggle_group(group_id: str):
    result = await group_service.toggle(group_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Group {group_id} not found")
    return result


@router.put("/{group_id}", response_model=GroupResponse)
async def update_group(group_id: str, body: GroupUpdateRequest):
    result = await group_service.update(
        group_id, name=body.name, device_ids=body.device_ids
    )
    if result is None:
        raise HTTPException(status_code=404, detail=f"Group {group_id} not found")
    return result


@router.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_group(group_id: str):
    deleted = await group_service.delete(group_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Group {group_id} not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
