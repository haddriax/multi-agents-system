from dataclasses import dataclass

from src.system.models.types import WasteType


@dataclass(frozen=True)
class Message:
    """Base class for all messages."""


@dataclass(frozen=True)
class WasteDiscoveredMessage(Message):
    """A waste of the given type is available at this position."""
    waste_type: WasteType
    position: tuple[int, int]


@dataclass(frozen=True)
class WasteCancelledMessage(Message):
    """The waste at this position has been picked up (cancel any navigation toward it)"""
    position: tuple[int, int]
