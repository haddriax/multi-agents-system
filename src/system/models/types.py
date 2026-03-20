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

class SensorType(Enum):
    OPTIC = 1
    GEIGER = 2
    NONE = 0
