# Group: 9
# Date: 20-03-2026
# Members: Maëlys Hanoire, Raphaël Vignal, Gaël Garnier

from mesa import Model

from src.system.entities.objects.base_object import BaseObject
from src.system.models.types import WasteType



class Waste(BaseObject):
    def __init__(self, m: Model, waste_type: WasteType, quantity: int = 1):
        super().__init__(m)
        self.type = waste_type
        self.quantity = quantity
        self.tier: int = 0

        match waste_type:
            case WasteType.GREEN:
                self.tier = 1
            case WasteType.YELLOW:
                self.tier = 2
            case WasteType.RED:
                self.tier = 3
