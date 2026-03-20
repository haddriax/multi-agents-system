from mesa import Model

from src.system.map.navigable_grid import NavigableGrid
from src.system.objects.radioactivity import Radioactivity
from src.system.objects.waste_disposal_zone import WasteDisposalZone


class SystemModel(Model):
    def __init__(self, config: dict):
        super().__init__()

        width = config['grid']['width']
        height = config['grid']['height']

        self.grid = NavigableGrid(width=width, height=height)

        self._place_radioactivity_agents()
        self._place_waste_disposal_zone()

    def _place_radioactivity_agents(self) -> None:
        width = self.grid.width
        height = self.grid.height

        for x in range(width):
            zone = self.grid.get_zone(x)
            for y in range(height):
                self.grid.place_agent(Radioactivity(self, zone), (x, y))

    def _place_waste_disposal_zone(self) -> None:
        width = self.grid.width
        height = self.grid.height
        disposal_y = self.random.randrange(height)
        self.grid.place_agent(WasteDisposalZone(self), (width - 1, disposal_y))
