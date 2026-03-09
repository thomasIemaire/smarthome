from pydantic import BaseModel


class Group(BaseModel):
    id: str
    name: str
    device_ids: list[str] = []
