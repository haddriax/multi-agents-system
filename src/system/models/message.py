from dataclasses import dataclass

from src.system.models.types import WasteType


@dataclass(frozen=True)
class Message:
    waste_type: WasteType
    position: tuple[int, int]
