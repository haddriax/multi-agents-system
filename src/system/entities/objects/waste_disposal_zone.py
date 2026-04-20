# Group: 9
# Date: 20-03-2026
# Members: Maëlys Hanoire, Raphaël Vignal, Gaël Garnier

from mesa import Model

from src.system.entities.objects.base_object import BaseObject


class WasteDisposalZone(BaseObject):
    def __init__(self, m: Model):
        super().__init__(m)
        self.waste_received: int = 0
