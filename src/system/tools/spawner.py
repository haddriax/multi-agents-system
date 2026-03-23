import random
from typing import Type

from src.system.entities.agents.green_agent import GreenAgent
from src.system.entities.agents.red_agent import RedAgent
from src.system.entities.agents.yellow_agent import YellowAgent
from src.system.entities.objects.radioactivity import Radioactivity
from src.system.entities.objects.waste import Waste
from src.system.entities.objects.waste_disposal_zone import WasteDisposalZone
from src.system.models.types import WasteType
from src.system.system_model import SystemModel


def _zone_x_range(zone: str, width: int) -> range:
    """Return the strict x-column range for a given zone name."""
    third = width // 3
    two_thirds = 2 * width // 3
    ranges = {
        "green":  range(0,          third),
        "yellow": range(third,      two_thirds),
        "red":    range(two_thirds, width),
    }
    if zone not in ranges:
        raise ValueError(f"Unknown zone '{zone}'")
    return ranges[zone]


class Spawner:
    def __init__(self, model: SystemModel, config: dict) -> None:
        self._config = config
        self.model = model
        self.spawning_config = config.get("spawning")
        if self.spawning_config is None:
            raise EnvironmentError("No spawning config loaded")

        self.available_spawns: dict[str, list[tuple[int, int]]] = {
            "green":  [],
            "yellow": [],
            "red":    [],
        }
        """All free cells per zone, pre-computed before any robot/waste placement."""

        self._precompute_available_cells(model)

    def execute_spawning(self) -> None:
        self._place_radioactivity(self.model)
        self._place_waste_disposal_zone(self.model)
        self._place_wastes(self.model, self.spawning_config)
        self._place_robots(self.model, self.spawning_config)


    def _precompute_available_cells(self, model: SystemModel) -> None:
        """
        Populate available_spawns with every (x, y) cell strictly within
        each zone. Radioactivity agents are grid-layer agents and do not
        count as occupants for this purpose.
        """
        height = model.grid.height
        width  = model.grid.width

        for zone in ("green", "yellow", "red"):
            xs = _zone_x_range(zone, width)
            cells = [(x, y) for x in xs for y in range(height)]
            random.shuffle(cells)
            self.available_spawns[zone] = cells

    def _pop_cell(self, zone: str, agent_desc: str) -> tuple[int, int]:
        """
        Consume one free cell from the given zone.
        Raises ValueError if the zone is exhausted.
        """
        if not self.available_spawns[zone]:
            raise ValueError(
                f"Cannot place {agent_desc}: no free cells left in zone '{zone}'"
            )
        return self.available_spawns[zone].pop()

    def _place_radioactivity(self, model: SystemModel) -> None:
        width  = model.grid.width
        height = model.grid.height

        for x in range(width):
            zone: str = model.grid.get_zone(x)
            for y in range(height):
                model.grid.place_agent(Radioactivity(model, zone), (x, y))

    def _place_waste_disposal_zone(self, model: SystemModel) -> None:
        disposal_y = random.randrange(model.grid.height)
        disposal_x = model.grid.width - 1
        model.grid.place_agent(WasteDisposalZone(model), (disposal_x, disposal_y))

        # The disposal cell is on the red zone's rightmost column;
        # remove it so robots and waste are never spawned there.
        cell = (disposal_x, disposal_y)
        try:
            self.available_spawns["red"].remove(cell)
        except ValueError:
            pass  # cell was already consumed or not in range

    def _place_wastes(self, model: SystemModel, spawning_config: dict) -> None:
        waste_map: dict[str, WasteType] = {
            "green":  WasteType.GREEN,
            "yellow": WasteType.YELLOW,
            "red":    WasteType.RED,
        }
        count_keys: dict[str, str] = {
            "green":  "n_waste_green",
            "yellow": "n_waste_yellow",
            "red":    "n_waste_red",
        }

        for zone, waste_type in waste_map.items():
            n = spawning_config.get(count_keys[zone], 0)
            for _ in range(n):
                pos = self._pop_cell(zone, f"Waste({waste_type.name})")
                model.grid.place_agent(Waste(model, waste_type), pos)

    def _place_robots(self, model: SystemModel, spawning_config: dict) -> None:
        robot_map: dict[str, Type[GreenAgent | YellowAgent | RedAgent]] = {
            "green":  GreenAgent,
            "yellow": YellowAgent,
            "red":    RedAgent,
        }
        count_keys: dict[str, str] = {
            "green":  "n_green",
            "yellow": "n_yellow",
            "red":    "n_red",
        }

        for zone, AgentClass in robot_map.items():
            n = spawning_config.get(count_keys[zone], 0)
            for _ in range(n):
                pos = self._pop_cell(zone, AgentClass.__name__)
                agent = AgentClass(model)
                model.grid.place_agent(agent, pos)