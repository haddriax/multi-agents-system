from typing import Sequence

from mesa import Model, DataCollector, Agent

from src.system.config import Config
from src.system.entities.agents.base_agent import BaseAgent
from src.system.map.navigable_grid import NavigableGrid
from src.system.models.perception import Perception, CellContent
from src.system.models.action import ActionType
from src.system.models.types import WasteType, RobotType
from src.system.entities.objects.radioactivity import Radioactivity
from src.system.entities.objects.waste import Waste


class SystemModel(Model):
    def __init__(self, config: Config | None = None) -> None:
        super().__init__()
        if config is None:
            config = Config.from_yaml("config.yaml")

        self.config = config
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
        Returns a view of the world, condionned by the senor and centered on the agent.
        """
        sensor_radius = agent.sensors['optical'].radius

        neighbor_positions: Sequence[tuple[[int, int]]] = self.grid.get_neighborhood(
            agent.pos,
            moore=True,
            include_center=True,
            radius=sensor_radius
        )

        # Build all of the CellContent for each neighboring cell
        # @todo I think there's way to optimise that.
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
                if hasattr(agent, 'quantity'):
                    waste_quantity = agent.quantity
                else:
                    waste_quantity = 1
            elif isinstance(agent, BaseAgent):
                robot_type = agent.robot_type

        return CellContent(
            radioactivity_value=radioactivity_value,
            waste_type=waste_type,
            waste_quantity=waste_quantity,
            robot_type=robot_type,
        )

    def do(self, agent: BaseAgent, action: ActionType) -> None:
        """
        Execute an action for the given agent.
        Handles movement, picking up waste, dropping waste, and waiting.
        """
        if action == ActionType.MOVE_UP:
            new_pos = (agent.pos[0], agent.pos[1] + 1)
            if self.grid.out_of_bounds(new_pos):
                return
            self.grid.move_agent(agent, new_pos)

        elif action == ActionType.MOVE_DOWN:
            new_pos = (agent.pos[0], agent.pos[1] - 1)
            if self.grid.out_of_bounds(new_pos):
                return
            self.grid.move_agent(agent, new_pos)

        elif action == ActionType.MOVE_LEFT:
            new_pos = (agent.pos[0] - 1, agent.pos[1])
            if self.grid.out_of_bounds(new_pos):
                return
            self.grid.move_agent(agent, new_pos)

        elif action == ActionType.MOVE_RIGHT:
            new_pos = (agent.pos[0] + 1, agent.pos[1])
            if self.grid.out_of_bounds(new_pos):
                return
            self.grid.move_agent(agent, new_pos)

        elif action == ActionType.MOVE_UP_LEFT:
            new_pos = (agent.pos[0] - 1, agent.pos[1] + 1)
            if self.grid.out_of_bounds(new_pos):
                return
            self.grid.move_agent(agent, new_pos)

        elif action == ActionType.MOVE_UP_RIGHT:
            new_pos = (agent.pos[0] + 1, agent.pos[1] + 1)
            if self.grid.out_of_bounds(new_pos):
                return
            self.grid.move_agent(agent, new_pos)

        elif action == ActionType.MOVE_DOWN_LEFT:
            new_pos = (agent.pos[0] - 1, agent.pos[1] - 1)
            if self.grid.out_of_bounds(new_pos):
                return
            self.grid.move_agent(agent, new_pos)

        elif action == ActionType.MOVE_DOWN_RIGHT:
            new_pos = (agent.pos[0] + 1, agent.pos[1] - 1)
            if self.grid.out_of_bounds(new_pos):
                return
            self.grid.move_agent(agent, new_pos)

        elif action == ActionType.PICK:
            # @todo: Implement picking up waste
            pass

        elif action == ActionType.DROP:
            # @todo: Implement dropping waste
            pass

        elif action == ActionType.WAIT:
            # Just wait one turn
            pass

