import json
import logging
from pathlib import Path
from typing import Optional

from config import settings
from models.device import Device
from models.group import Group

logger = logging.getLogger(__name__)


class PersistenceService:
    _instance: Optional["PersistenceService"] = None

    def __init__(self) -> None:
        self.devices: list[Device] = []
        self.device_states: dict[str, bool] = {}
        self.groups: list[Group] = []
        self._data_dir = Path(settings.data_dir)

    @classmethod
    def get_instance(cls) -> "PersistenceService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @property
    def devices_path(self) -> Path:
        return self._data_dir / "devices.json"

    @property
    def groups_path(self) -> Path:
        return self._data_dir / "groups.json"

    def load_devices(self) -> list[Device]:
        try:
            if self.devices_path.exists():
                raw = json.loads(self.devices_path.read_text(encoding="utf-8"))
                self.devices = [Device.model_validate(d) for d in raw]
                self.device_states = {d.id: d.state for d in self.devices}
                logger.info("Loaded %d devices from %s", len(self.devices), self.devices_path)
            else:
                logger.warning("Devices file not found at %s, starting empty", self.devices_path)
                self.devices = []
                self.device_states = {}
        except Exception as exc:
            logger.error("Failed to load devices: %s", exc)
            self.devices = []
            self.device_states = {}
        return self.devices

    def save_devices(self) -> None:
        try:
            self._data_dir.mkdir(parents=True, exist_ok=True)
            data = [d.model_dump() for d in self.devices]
            self.devices_path.write_text(
                json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
            )
            logger.info("Saved %d devices to %s", len(self.devices), self.devices_path)
        except Exception as exc:
            logger.error("Failed to save devices: %s", exc)

    def load_groups(self) -> list[Group]:
        try:
            if self.groups_path.exists():
                raw = json.loads(self.groups_path.read_text(encoding="utf-8"))
                self.groups = [Group.model_validate(g) for g in raw]
                logger.info("Loaded %d groups from %s", len(self.groups), self.groups_path)
            else:
                logger.warning("Groups file not found at %s, starting empty", self.groups_path)
                self.groups = []
        except Exception as exc:
            logger.error("Failed to load groups: %s", exc)
            self.groups = []
        return self.groups

    def save_groups(self) -> None:
        try:
            self._data_dir.mkdir(parents=True, exist_ok=True)
            data = [g.model_dump() for g in self.groups]
            self.groups_path.write_text(
                json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
            )
            logger.info("Saved %d groups to %s", len(self.groups), self.groups_path)
        except Exception as exc:
            logger.error("Failed to save groups: %s", exc)

    def find_device(self, device_id: str) -> Optional[Device]:
        for device in self.devices:
            if device.id == device_id:
                return device
        return None

    def find_group(self, group_id: str) -> Optional[Group]:
        for group in self.groups:
            if group.id == group_id:
                return group
        return None


persistence = PersistenceService.get_instance()
