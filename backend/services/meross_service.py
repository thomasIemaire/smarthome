import logging
from typing import Optional

from config import settings

logger = logging.getLogger(__name__)


class MerossService:
    def __init__(self) -> None:
        self._http_client = None
        self._manager = None
        self._connected = False

    @property
    def connected(self) -> bool:
        return self._connected

    async def connect(self, email: str, password: str) -> bool:
        if not email or not password:
            logger.warning("Meross credentials not provided, skipping connection")
            return False

        try:
            from meross_iot.http_api import MerossHttpClient
            from meross_iot.manager import MerossManager

            self._http_client = await MerossHttpClient.async_from_user_password(
                api_base_url=settings.meross_api_base_url,
                email=email,
                password=password,
            )
            self._manager = MerossManager(http_client=self._http_client)
            await self._manager.async_init()
            await self._manager.async_device_discovery()
            self._connected = True
            logger.info("Connected to Meross cloud successfully")
            return True
        except Exception as exc:
            logger.error("Failed to connect to Meross: %s", exc)
            self._connected = False
            return False

    async def disconnect(self) -> None:
        try:
            if self._manager is not None:
                self._manager.close()
            if self._http_client is not None:
                await self._http_client.async_logout()
            self._connected = False
            logger.info("Disconnected from Meross cloud")
        except Exception as exc:
            logger.warning("Error during Meross disconnect: %s", exc)
            self._connected = False

    async def discover(self) -> list[dict]:
        if not self._connected or self._manager is None:
            logger.warning("Meross not connected, cannot discover devices")
            return []

        try:
            await self._manager.async_device_discovery()
            devices = self._manager.find_devices()
            result = []
            for dev in devices:
                try:
                    await dev.async_update()
                    is_on = dev.is_on() if hasattr(dev, "is_on") else False
                except Exception:
                    is_on = False

                result.append({
                    "name": dev.name,
                    "type": dev.type,
                    "uuid": dev.uuid,
                    "online": dev.online_status.value if hasattr(dev.online_status, "value") else str(dev.online_status),
                    "is_on": is_on,
                    "device_type": str(type(dev).__name__),
                })
            logger.info("Discovered %d Meross devices", len(result))
            return result
        except Exception as exc:
            logger.error("Failed to discover Meross devices: %s", exc)
            return []

    async def get_state(self, uuid: str) -> Optional[bool]:
        if not self._connected or self._manager is None:
            return None

        try:
            devices = self._manager.find_devices(device_uuids=[uuid])
            if not devices:
                logger.warning("Meross device with UUID %s not found", uuid)
                return None
            dev = devices[0]
            await dev.async_update()
            return dev.is_on() if hasattr(dev, "is_on") else None
        except Exception as exc:
            logger.warning("Failed to get Meross state for %s: %s", uuid, exc)
            return None

    async def set_state(self, uuid: str, state: bool) -> bool:
        if not self._connected or self._manager is None:
            return False

        try:
            devices = self._manager.find_devices(device_uuids=[uuid])
            if not devices:
                logger.warning("Meross device with UUID %s not found", uuid)
                return False
            dev = devices[0]
            if state:
                await dev.async_turn_on()
            else:
                await dev.async_turn_off()
            return True
        except Exception as exc:
            logger.error("Failed to set Meross state for %s: %s", uuid, exc)
            return False


meross_service = MerossService()
