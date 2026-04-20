# Group: 9
# Date: 20-03-2026
# Members: Maëlys Hanoire, Raphaël Vignal, Gaël Garnier

from mesa import Model

from Raphael_Maelys_Gael_robot_mission_MAS2026.system.entities.objects.base_object import BaseObject
from Raphael_Maelys_Gael_robot_mission_MAS2026.system.models.types import WasteType



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
