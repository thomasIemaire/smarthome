import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from routers.devices import bulk_router, rooms_router, router as devices_router
from routers.discovery import router as discovery_router
from routers.groups import router as groups_router
from services.meross_service import meross_service
from services.persistence import persistence

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Smart Home API...")
    persistence.load_devices()
    persistence.load_groups()
    logger.info(
        "Loaded %d devices and %d groups",
        len(persistence.devices),
        len(persistence.groups),
    )

    if settings.meross_email and settings.meross_password:
        connected = await meross_service.connect(
            settings.meross_email, settings.meross_password
        )
        if connected:
            logger.info("Meross cloud connection established")
        else:
            logger.warning("Failed to connect to Meross cloud")
    else:
        logger.info("Meross credentials not configured, skipping cloud connection")

    yield

    logger.info("Shutting down Smart Home API...")
    await meross_service.disconnect()
    persistence.save_devices()
    persistence.save_groups()
    logger.info("Shutdown complete")


app = FastAPI(
    title="Smart Home API",
    description="Backend API for controlling smart home devices (Shelly & Meross)",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(devices_router, prefix="/api")
app.include_router(rooms_router, prefix="/api")
app.include_router(bulk_router, prefix="/api")
app.include_router(groups_router, prefix="/api")
app.include_router(discovery_router, prefix="/api")


@app.get("/")
async def root():
    return {"message": "Smart Home API", "docs": "/docs"}
