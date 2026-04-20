# Group: 9
# Date: 23-03-2026
# Members: Maëlys Hanoire, Raphaël Vignal, Gaël Garnier

import random
from dataclasses import dataclass
from typing import Type

from src.system.config import SpawningConfig
from src.system.entities.agents.green_agent import GreenAgent
from src.system.entities.agents.red_agent import RedAgent
from src.system.entities.agents.yellow_agent import YellowAgent
from src.system.entities.objects.radioactivity import Radioactivity
from src.system.entities.objects.waste import Waste
from src.system.entities.objects.waste_disposal_zone import WasteDisposalZone
from src.system.models.types import WasteType
from src.system.system_model import SystemModel


@dataclass(frozen=True)
class ZoneConfig:
    zone:        str
    waste_type:  WasteType
    robot_class: Type[GreenAgent | YellowAgent | RedAgent]

    def n_wastes(self, sc: SpawningConfig) -> int:
        match self.zone:
            case "z1": return sc.n_waste_green
            case "z2": return sc.n_waste_yellow
            case "z3": return sc.n_waste_red
            case _:    raise ValueError(f"Unknown zone '{self.zone}'")

    def n_robots(self, sc: SpawningConfig) -> int:
        match self.zone:
            case "z1": return sc.n_green
            case "z2": return sc.n_yellow
            case "z3": return sc.n_red
            case _:    raise ValueError(f"Unknown zone '{self.zone}'")


_ZONE_CONFIGS: tuple[ZoneConfig, ...] = (
    ZoneConfig("z1", WasteType.GREEN,  GreenAgent),
    ZoneConfig("z2", WasteType.YELLOW, YellowAgent),
    ZoneConfig("z3", WasteType.RED,    RedAgent),
)


class Spawner:
    def __init__(self, model: SystemModel, config: "Config") -> None:  # noqa: F821
        self._config        = config
        self._model         = model
        self._spawning_cfg  = config.spawning

        self.available_spawns: dict[str, list[tuple[int, int]]] = {
            "z1": [],
            "z2": [],
            "z3": [],
        }
        """All free cells per zone, pre-computed before any robot/waste placement."""

        self._precompute_available_cells()

    def execute_spawning(self) -> None:
        self._place_radioactivity()
        self._place_waste_disposal_zone()
        self._place_wastes()
        self._place_robots()

    def _precompute_available_cells(self) -> None:
        """
        Populate available_spawns with every (x, y) cell strictly within
        each zone, in random order. Radioactivity agents are grid-layer
        agents and do not count as occupants for this purpose.
        """
        for zone in ("z1", "z2", "z3"):
            cells = self._model.grid.get_all_cells_in_zone(zone)
            random.shuffle(cells)
            self.available_spawns[zone] = cells

    def _pop_cell(self, zone: str, agent_desc: str) -> tuple[int, int]:
        """Consume one free cell from the given zone, raises ValueError if exhausted."""
        if not self.available_spawns[zone]:
            raise ValueError(
                f"Cannot place {agent_desc}: no free cells left in zone '{zone}'"
            )
        return self.available_spawns[zone].pop()

    def _place_radioactivity(self) -> None:
        for x in range(self._model.grid.width):
            zone = self._model.grid.get_zone(x)
            for y in range(self._model.grid.height):
                self._model.grid.place_agent(Radioactivity(self._model, zone), (x, y))


    def _place_waste_disposal_zone(self) -> None:
        disposal_x = self._model.grid.width - 1
        disposal_y = random.randrange(self._model.grid.height)
        self._model.grid.place_agent(WasteDisposalZone(self._model), (disposal_x, disposal_y))

        cell = (disposal_x, disposal_y)
        try:
            self.available_spawns["z3"].remove(cell)
        except ValueError:
            pass

    def _place_wastes(self) -> None:
        for zc in _ZONE_CONFIGS:
            for _ in range(zc.n_wastes(self._spawning_cfg)):
                pos = self._pop_cell(zc.zone, f"Waste({zc.waste_type.name})")
                self._model.grid.place_agent(Waste(self._model, zc.waste_type), pos)

    def _place_robots(self) -> None:
        for zc in _ZONE_CONFIGS:
            for _ in range(zc.n_robots(self._spawning_cfg)):
                pos = self._pop_cell(zc.zone, zc.robot_class.__name__)
                self._model.grid.place_agent(zc.robot_class(self._model), pos)