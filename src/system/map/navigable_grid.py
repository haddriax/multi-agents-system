from mesa.space import MultiGrid
from src.system.entities.agents.mesa_adapter import MesaAgentAdapter

class NavigableGrid(MultiGrid):
    def __init__(self, width: int, height: int, torus: bool = False):
        super().__init__(width, height, torus)
        self._z1_end = width // 3
        self._z2_end = 2 * width // 3

    def get_zone(self, x: int) -> str:
        if x < self._z1_end:
            return "z1"
        if x < self._z2_end:
            return "z2"
        return "z3"

    def is_cell_occupied(self, pos: tuple[int, int]) -> bool:
        """
        Vérifie si une case est occupée par un autre agent.
        """
        return any(isinstance(agent, MesaAgentAdapter) for agent in self.get_cell_list_contents([pos]))
      
    def get_zone_x_range(self, zone: str) -> range:
        """Return the strict x-column range [start, end) for a given zone."""
        match zone:
            case "z1": return range(0,           self._z1_end)
            case "z2": return range(self._z1_end, self._z2_end)
            case "z3": return range(self._z2_end, self.width)
            case _:    raise ValueError(f"Unknown zone '{zone}'")

    def get_all_cells_in_zone(self, zone: str) -> list[tuple[int, int]]:
        """Return all (x, y) cells strictly within the given zone, in random order."""
        xs = self.get_zone_x_range(zone)
        cells = [(x, y) for x in xs for y in range(self.height)]
        return cells
