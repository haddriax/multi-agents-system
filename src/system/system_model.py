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

class ActionResult:
    """ Structure returned by actions methods. Bool for now but ready to have messages. """
    def __init__(self, action_type: ActionType, success: bool):
        self.action_type = action_type
        self.success = success

class ActionInvalidException(Exception):
    """ Exception to raise when an illegal action is called. """
    def __init__(self, illegal_action: ActionType, message: str):
        self.illegal_action = illegal_action
        self.message = message

    def __str__(self) -> str:
        return f"Illegal action: {str(self.illegal_action)} - {self.message}"

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
        @todo we should return a bool for success or failure of the action.
        """
        new_pos = None

        if action == ActionType.MOVE_UP:
            new_pos = (agent.pos[0], agent.pos[1] + 1)
        elif action == ActionType.MOVE_DOWN:
            new_pos = (agent.pos[0], agent.pos[1] - 1)
        elif action == ActionType.MOVE_LEFT:
            new_pos = (agent.pos[0] - 1, agent.pos[1])
        elif action == ActionType.MOVE_RIGHT:
            new_pos = (agent.pos[0] + 1, agent.pos[1])

        elif action == ActionType.MOVE_UP_LEFT:
            new_pos = (agent.pos[0] - 1, agent.pos[1] + 1)
        elif action == ActionType.MOVE_UP_RIGHT:
            new_pos = (agent.pos[0] + 1, agent.pos[1] + 1)
        elif action == ActionType.MOVE_DOWN_LEFT:
            new_pos = (agent.pos[0] - 1, agent.pos[1] - 1)
        elif action == ActionType.MOVE_DOWN_RIGHT:
            new_pos = (agent.pos[0] + 1, agent.pos[1] - 1)

        elif action == ActionType.PICK:
            # @todo: Implement picking up waste
            pass
        elif action == ActionType.DROP:
            # @todo: Implement dropping waste
            pass

        elif action == ActionType.WAIT:
            # Just wait one turn
            pass

        # Verify that the new position is valid and not occupied before moving the agent
        if new_pos and not self.grid.out_of_bounds(new_pos) and not self.grid.is_cell_occupied(new_pos):
            self.grid.move_agent(agent, new_pos)

    def agent_pick_waste(self, agent: BaseAgent, waste_target: WasteType) -> ActionResult:
        """
        Handle the logic for an agent picking up waste.
        Checks if there's waste at the agent's position and if the agent can pick it up.
        """
        action_definition = ActionType.PICK
        cell_agents: list[Agent] = self.grid.get_cell_list_contents([agent.pos])
        waste_agents = [a for a in cell_agents if isinstance(a, Waste)]

        # FAILURE: No waste to pick up
        if not waste_agents:
            return ActionResult(action_definition, False)

        # Get the waste matching waste_target
        waste_to_pick: Waste
        for waste in waste_agents:
            if waste.type == waste_target:
                waste_to_pick = waste
                break
        else:
            # FAILURE: No waste match the one we want
            return ActionResult(action_definition, False)

        # FAILURE: Waste is too high tier for the agent to pick up
        # It's a safeguard about the game rules, so we raise here since it should never happen!
        if waste_to_pick.tier > agent.tier:
            raise ActionInvalidException(
                action_definition,
                "Agent cannot pick up waste of tier higher than its own tier."
            )

        # FAILURE: Carry limit reached
        # We raise there as well, because that means the agent logic is flawed.
        if len(agent.knowledge.carried_wastes) >= agent.carry_capacity:
            raise ActionInvalidException(
                action_definition,
                "Agent cannot pick up more waste than it can carry"
            )

        agent.knowledge.carried_wastes.append(waste_to_pick)


        self.grid.remove_agent(waste_to_pick)

        return ActionResult(action_definition, True)

