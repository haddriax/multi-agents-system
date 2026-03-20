from enum import Enum

from mesa import Model

from src.system.objects.base_object import BaseObject


class WasteColor(Enum):
    GREEN = "green"
    YELLOW = "yellow"
    RED = "red"


class Waste(BaseObject):
    def __init__(self, m: Model, color: WasteColor):
        super().__init__(m)
        self.color = color
