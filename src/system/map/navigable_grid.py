from mesa.space import MultiGrid
from src.system.entities.agents.base_agent import BaseAgent

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
        return any(isinstance(agent, BaseAgent) for agent in self.get_cell_list_contents([pos]))