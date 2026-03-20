from mesa.space import MultiGrid


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
