import asyncio
import logging
import socket
from typing import Optional

import httpx

from config import settings

logger = logging.getLogger(__name__)


class ShellyService:
    def __init__(self) -> None:
        self._scan_timeout = settings.shelly_scan_timeout
        self._command_timeout = settings.shelly_command_timeout
        self._scan_workers = settings.shelly_scan_workers

    def _detect_subnet(self) -> str:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            parts = local_ip.split(".")
            return f"{parts[0]}.{parts[1]}.{parts[2]}"
        except Exception:
            return "192.168.1"

    async def _probe_ip(
        self, client: httpx.AsyncClient, ip: str, semaphore: asyncio.Semaphore
    ) -> Optional[dict]:
        async with semaphore:
            try:
                response = await client.get(
                    f"http://{ip}/shelly", timeout=self._scan_timeout
                )
                if response.status_code == 200:
                    data = response.json()
                    device_type = data.get("type", data.get("app", "unknown"))
                    gen = 2 if "app" in data else 1
                    device_id = f"shelly_{data.get('mac', ip).lower()}"
                    return {
                        "id": device_id,
                        "ip": ip,
                        "type": device_type,
                        "gen": gen,
                        "model": data.get("model", ""),
                        "mac": data.get("mac", ""),
                        "name": data.get("name", "") or f"Shelly {device_type}",
                    }
            except Exception:
                pass
            return None

    async def scan(self, subnet: Optional[str] = None) -> list[dict]:
        if subnet is None:
            subnet = self._detect_subnet()

        logger.info("Scanning subnet %s.0/24 for Shelly devices...", subnet)
        semaphore = asyncio.Semaphore(self._scan_workers)

        async with httpx.AsyncClient() as client:
            tasks = [
                self._probe_ip(client, f"{subnet}.{i}", semaphore)
                for i in range(1, 255)
            ]
            results = await asyncio.gather(*tasks)

        devices = [r for r in results if r is not None]
        logger.info("Found %d Shelly devices on %s.0/24", len(devices), subnet)
        return devices

    async def get_state(self, ip: str, gen: int = 1) -> Optional[bool]:
        try:
            async with httpx.AsyncClient() as client:
                if gen >= 2:
                    response = await client.get(
                        f"http://{ip}/rpc/Switch.GetStatus?id=0",
                        timeout=self._command_timeout,
                    )
                    if response.status_code == 200:
                        data = response.json()
                        return data.get("output", False)
                else:
                    response = await client.get(
                        f"http://{ip}/relay/0", timeout=self._command_timeout
                    )
                    if response.status_code == 200:
                        data = response.json()
                        return data.get("ison", False)
        except Exception as exc:
            logger.warning("Failed to get state for Shelly at %s: %s", ip, exc)
        return None

    async def set_state(self, ip: str, state: bool, gen: int = 1) -> bool:
        try:
            async with httpx.AsyncClient() as client:
                if gen >= 2:
                    on_val = "true" if state else "false"
                    response = await client.get(
                        f"http://{ip}/rpc/Switch.Set?id=0&on={on_val}",
                        timeout=self._command_timeout,
                    )
                    return response.status_code == 200
                else:
                    turn = "on" if state else "off"
                    response = await client.get(
                        f"http://{ip}/relay/0?turn={turn}",
                        timeout=self._command_timeout,
                    )
                    return response.status_code == 200
        except Exception as exc:
            logger.error("Failed to set state for Shelly at %s: %s", ip, exc)
            return False


shelly_service = ShellyService()
