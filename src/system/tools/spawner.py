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
from dataclasses import dataclass

@dataclass(frozen=True)
class ZoneConfig:
    zone:           str
    waste_type:     WasteType
    robot_class:    Type[GreenAgent | YellowAgent | RedAgent]
    waste_count_key: str
    robot_count_key: str


_ZONE_CONFIGS: tuple[ZoneConfig, ...] = (
    ZoneConfig("z1", WasteType.GREEN,  GreenAgent,  "n_waste_green",  "n_green"),
    ZoneConfig("z2", WasteType.YELLOW, YellowAgent, "n_waste_yellow", "n_yellow"),
    ZoneConfig("z3", WasteType.RED,    RedAgent,    "n_waste_red",    "n_red"),
)

class Spawner:
    def __init__(self, model: SystemModel, config: dict) -> None:
        self._config = config
        self.model = model
        self.spawning_config = config.get("spawning")
        if self.spawning_config is None:
            raise EnvironmentError("No spawning config loaded")

        self.available_spawns: dict[str, list[tuple[int, int]]] = {
            "z1": [],
            "z2": [],
            "z3": [],
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
        each zone, in random order. Radioactivity agents are grid-layer
        agents and do not count as occupants for this purpose.
        """
        for zone in ("z1", "z2", "z3"):
            cells = model.grid.get_all_cells_in_zone(zone)
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
        for x in range(model.grid.width):
            zone = model.grid.get_zone(x)
            for y in range(model.grid.height):
                model.grid.place_agent(Radioactivity(model, zone), (x, y))

    def _place_waste_disposal_zone(self, model: SystemModel) -> None:
        disposal_x = model.grid.width - 1
        disposal_y = random.randrange(model.grid.height)
        model.grid.place_agent(WasteDisposalZone(model), (disposal_x, disposal_y))

        # Remove the disposal cell from z3's available pool
        cell = (disposal_x, disposal_y)
        try:
            self.available_spawns["z3"].remove(cell)
        except ValueError:
            pass  # already consumed or out of range

    def _place_wastes(self, model: SystemModel, spawning_config: dict) -> None:
        for zc in _ZONE_CONFIGS:
            n = spawning_config.get(zc.waste_count_key, 0)
            for _ in range(n):
                pos = self._pop_cell(zc.zone, f"Waste({zc.waste_type.name})")
                model.grid.place_agent(Waste(model, zc.waste_type), pos)

    def _place_robots(self, model: SystemModel, spawning_config: dict) -> None:
        for zc in _ZONE_CONFIGS:
            n = spawning_config.get(zc.robot_count_key, 0)
            for _ in range(n):
                pos = self._pop_cell(zc.zone, zc.robot_class.__name__)
                model.grid.place_agent(zc.robot_class(model), pos)