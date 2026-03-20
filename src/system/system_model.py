from typing import Sequence

from mesa import Model, DataCollector, Agent

from src.system.entities.agents.base_agent import BaseAgent
from src.system.entities.agents.green_agent import GreenAgent
from src.system.entities.agents.yellow_agent import YellowAgent
from src.system.entities.agents.red_agent import RedAgent
from src.system.map.navigable_grid import NavigableGrid
from src.system.models.perception import Perception, CellContent
from src.system.models.action import ActionType
from src.system.models.types import WasteType, RobotType
from src.system.entities.objects.radioactivity import Radioactivity
from src.system.entities.objects.waste import Waste
from src.system.entities.objects.waste_disposal_zone import WasteDisposalZone



class SystemModel(Model):
    def __init__(self, config: dict):
        super().__init__()

        width = config['grid']['width']
        height = config['grid']['height']

        self.grid = NavigableGrid(width=width, height=height)
        self.steps = 0
        self.datacollector = DataCollector(
            # @todo Implement the DataCollector
        )

        self._place_radioactivity_agents()
        self._place_waste_disposal_zone()
        self._place_agents()

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

    def step(self):
        """ Execute one world step """
        self.datacollector.collect(self)
        self.agents.shuffle_do("step")
        self.steps += 1

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

        elif action == ActionType.PICK:
            # @todo: Implement picking up waste
            pass

        elif action == ActionType.DROP:
            # @todo: Implement dropping waste
            pass

        elif action == ActionType.WAIT:
            # Just wait one turn
            pass

    def _place_agents(self) -> None:
        """
        Initialize and place agents on the grid.
        for debug we just place one for now
        @todo add proper spawning
        """
        width = self.grid.width
        height = self.grid.height

        green_x = self.random.randrange(0, width // 3)
        green_y = self.random.randrange(height)
        green_agent = GreenAgent(self)
        self.grid.place_agent(green_agent, (green_x, green_y))

        yellow_x = self.random.randrange(width // 3, 2 * width // 3)
        yellow_y = self.random.randrange(height)
        yellow_agent = YellowAgent(self)
        self.grid.place_agent(yellow_agent, (yellow_x, yellow_y))

        red_x = self.random.randrange(2 * width // 3, width)
        red_y = self.random.randrange(height)
        red_agent = RedAgent(self)
        self.grid.place_agent(red_agent, (red_x, red_y))

