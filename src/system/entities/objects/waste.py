from mesa import Model

from src.system.entities.objects.base_object import BaseObject
from src.system.models.types import WasteType



class Waste(BaseObject):
    def __init__(self, m: Model, waste_type: WasteType, quantity: int = 1):
        super().__init__(m)
        self.type = waste_type
        self.quantity = quantity
