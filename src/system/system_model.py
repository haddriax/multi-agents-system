from typing import Sequence

from mesa import Model, DataCollector, Agent

from src.system.config import Config
from src.system.entities.agents.base_agent import BaseAgent
from src.system.map.navigable_grid import NavigableGrid
from src.system.models.perception import Perception, CellContent
from src.system.models.action import Action, ActionResult
from src.system.models.types import WasteType, RobotType
from src.system.entities.objects.radioactivity import Radioactivity
from src.system.entities.objects.waste import Waste


class SystemModel(Model):
    def __init__(self, config: Config | None = None) -> None:
        super().__init__()
        if config is None:
            config = Config.from_yaml("config.yaml")

        self.config: Config = config
        width: int = config.grid.width
        height: int = config.grid.height

        self.grid = NavigableGrid(width=width, height=height)

        from src.system.tools.spawner import Spawner
        spawner = Spawner(self, config)
        spawner.execute_spawning()

        self.datacollector = DataCollector(
            model_reporters={
                "Waste (Green)":  lambda m: sum(
                    1 for a in m.agents if isinstance(a, Waste) and a.type == WasteType.GREEN
                ),
                "Waste (Yellow)": lambda m: sum(
                    1 for a in m.agents if isinstance(a, Waste) and a.type == WasteType.YELLOW
                ),
                "Waste (Red)":    lambda m: sum(
                    1 for a in m.agents if isinstance(a, Waste) and a.type == WasteType.RED
                ),
                "Agents Carrying": lambda m: sum(
                    1 for a in m.agents
                    if isinstance(a, BaseAgent) and len(a.knowledge.carried_wastes) > 0
                ),
                "Grid Coverage (%)": lambda m: (
                    len(set().union(*(
                        a.knowledge.belief_map.keys()
                        for a in m.agents if isinstance(a, BaseAgent)
                    ))) / (m.grid.width * m.grid.height) * 100
                ),
            }
        )

    def get_zone(self, x: int) -> str:
        return self.grid.get_zone(x)

    def step(self):
        """ Execute one world step. Note: self.steps is managed by Mesa (_do_step wrapper). """
        self.datacollector.collect(self)
        self.agents.shuffle_do("step")

    def perceive(self, agent: BaseAgent) -> Perception:
        """
        Create a perception for the agent based on its sensor readings.
        Returns a view of the world, conditioned by the sensor and centered on the agent.
        """
        sensor_radius = agent.sensors['optical'].radius

        neighbor_positions: Sequence[tuple[int, int]] = self.grid.get_neighborhood(
            agent.pos,
            moore=True,
            include_center=True,
            radius=sensor_radius
        )

        # @todo There's likely a way to optimise that.
        readings = []
        for pos in neighbor_positions:
            cell_agents = self.grid.get_cell_list_contents([pos])
            cell_content = self._build_cell_content(cell_agents)
            readings.append(cell_content)

        return Perception(
            perceiver_position=agent.pos,
            readings=tuple(readings),
            step=self.steps,
            perceiver_id=agent.unique_id
        )

    @staticmethod
    def _build_cell_content(agents: list[Agent]) -> CellContent:
        """
        Build a CellContent object from the agents at a given position.
        Using information from Radioactivity, Waste, and any BaseAgent objects.
        """
        radioactivity_value = 0.0
        waste_type = WasteType.NONE
        waste_quantity = 0
        robot_type = RobotType.NONE

        for agent in agents:
            if isinstance(agent, Radioactivity):
                radioactivity_value = agent.level
            elif isinstance(agent, Waste):
                waste_type = agent.type
                waste_quantity = getattr(agent, 'quantity', 1)
            elif isinstance(agent, BaseAgent):
                robot_type = agent.robot_type

        return CellContent(
            radioactivity_value=radioactivity_value,
            waste_type=waste_type,
            waste_quantity=waste_quantity,
            robot_type=robot_type,
        )

    def do(self, agent: BaseAgent, action: Action) -> ActionResult:
        """ Validate and execute an action for the given agent. """
        # @todo possible validation by the model here before executing?
        return action.execute(self, agent)
