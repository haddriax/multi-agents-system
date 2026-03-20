from mesa import Model

from src.system.objects.base_object import BaseObject


class WasteDisposalZone(BaseObject):
    def __init__(self, m: Model):
        super().__init__(m)
