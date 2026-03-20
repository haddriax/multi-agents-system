from enum import Enum


class ActionType(Enum):
    MOVE_UP = 1
    MOVE_DOWN = 2
    MOVE_LEFT = 3
    MOVE_RIGHT = 4
    PICK = 5
    DROP = 6
    WAIT = 0