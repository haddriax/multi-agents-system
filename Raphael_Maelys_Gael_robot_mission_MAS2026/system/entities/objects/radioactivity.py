# Group: 9
# Date: 20-03-2026
# Members: Maëlys Hanoire, Raphaël Vignal, Gaël Garnier

import random

from mesa import Model

from Raphael_Maelys_Gael_robot_mission_MAS2026.system.entities.objects.base_object import BaseObject

_ZONE_RANGES = {
    "z1": (0.0, 0.33),
    "z2": (0.33, 0.66),
    "z3": (0.66, 1.0),
}


class Radioactivity(BaseObject):
    def __init__(self, m: Model, zone: str):
        super().__init__(m)
        self.zone = zone
        low, high = _ZONE_RANGES[zone]
        self.level = random.uniform(low, high)
