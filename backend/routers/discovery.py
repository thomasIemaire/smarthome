from fastapi import APIRouter

from schemas.discovery import DiscoverResponse
from services import discovery_service

router = APIRouter(tags=["discovery"])


@router.post("/discover", response_model=DiscoverResponse)
async def discover():
    return await discovery_service.discover_all()
