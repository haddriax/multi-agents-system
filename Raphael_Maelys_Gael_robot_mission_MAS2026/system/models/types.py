# Group: 9
# Date: 20-03-2026
# Members: Maëlys Hanoire, Raphaël Vignal, Gaël Garnier

from enum import Enum

MAX_WASTE_PER_CELL = 2

class WasteType(Enum):
    GREEN = 1
    YELLOW = 2
    RED = 3
    NONE = 0

    @property
    def merged(self) -> "WasteType | None":
        """
        Return the waste type produced by merging two wastes of this tier.
        GREEN + GREEN → YELLOW
        YELLOW + YELLOW → RED
        RED → None  (no higher tier; cannot merge)
        NONE → None (not a real waste; cannot merge)
        """
        _upgrades: dict[WasteType, WasteType] = {
            WasteType.GREEN:  WasteType.YELLOW,
            WasteType.YELLOW: WasteType.RED,
        }
        return _upgrades.get(self)

class RobotType(Enum):
    GREEN = 1
    YELLOW = 2
    RED = 3
    NONE = 0

class Direction(Enum):
    UP = 1
    DOWN = 2
    LEFT = 3
    RIGHT = 4
    UP_LEFT = 5
    UP_RIGHT = 6
    DOWN_LEFT = 7
    DOWN_RIGHT = 8
