from enum import Enum

MAX_WASTE_PER_CELL = 2

class WasteType(Enum):
    GREEN = 1
    YELLOW = 2
    RED = 3
    NONE = 0

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
