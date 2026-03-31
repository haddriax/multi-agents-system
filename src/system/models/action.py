from enum import Enum


class ActionType(Enum):
    MOVE_UP = 1
    MOVE_DOWN = 2
    MOVE_LEFT = 3
    MOVE_RIGHT = 4
    MOVE_UP_LEFT = 5
    MOVE_UP_RIGHT = 6
    MOVE_DOWN_LEFT = 7
    MOVE_DOWN_RIGHT = 8
    WAIT = 9
    PICK = 10
    MERGE = 11
    DROP = 12