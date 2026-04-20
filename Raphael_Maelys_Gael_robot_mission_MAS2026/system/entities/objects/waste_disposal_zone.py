# Group: 9
# Date: 20-03-2026
# Members: Maëlys Hanoire, Raphaël Vignal, Gaël Garnier

from mesa import Model

from Raphael_Maelys_Gael_robot_mission_MAS2026.system.entities.objects.base_object import BaseObject


class WasteDisposalZone(BaseObject):
    def __init__(self, m: Model):
        super().__init__(m)
        self.waste_received: int = 0
