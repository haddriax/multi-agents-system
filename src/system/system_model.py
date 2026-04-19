from typing import Sequence

from mesa import Model, DataCollector, Agent

from src.system.config import Config
from src.system.entities.agents.mesa_adapter import MesaAgentAdapter
from src.system.map.navigable_grid import NavigableGrid
from src.system.models.perception import Perception, CellContent
from src.system.models.action import (
    Action, ActionResult, ActionSuccess, ActionFailure, FailureReason,
    MoveAction, PickAction, DropAction, WaitAction, MergeAction,
)
from src.system.models.types import WasteType, RobotType
from src.system.entities.objects.radioactivity import Radioactivity
from src.system.entities.objects.waste import Waste
from src.system.entities.objects.waste_disposal_zone import WasteDisposalZone


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
                    if isinstance(a, MesaAgentAdapter) and len(a.memory.carried_wastes) > 0
                ),
                "Grid Coverage (%)": lambda m: (
                    len(set().union(*(
                        a.memory.belief_map.keys()
                        for a in m.agents if isinstance(a, MesaAgentAdapter)
                    ))) / (m.grid.width * m.grid.height) * 100
                ),
            }
        )

        for agent in filter(lambda a: isinstance(a, MesaAgentAdapter), self.agents):
            agent.force_percept_update()

    def get_zone(self, x: int) -> str:
        return self.grid.get_zone(x)

    def step(self):
        """ Execute one world step. Note: self.steps is managed by Mesa (_do_step wrapper). """
        self.datacollector.collect(self)
        self.agents.shuffle_do("step")

    def perceive(self, agent: MesaAgentAdapter) -> Perception:
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
            readings.append((pos, cell_content))

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
        Using information from Radioactivity, Waste, and any MesaAgentAdapter objects.
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
            elif isinstance(agent, MesaAgentAdapter):
                robot_type = agent.robot_type

        return CellContent(
            radioactivity_value=radioactivity_value,
            waste_type=waste_type,
            waste_quantity=waste_quantity,
            robot_type=robot_type,
        )

    def do(self, agent: MesaAgentAdapter, action: Action) -> ActionResult:
        """ Dispatch and execute an action for the given agent. """
        match action:
            case MoveAction():  return self._do_move(agent, action)
            case PickAction():  return self._do_pick(agent, action)
            case DropAction():  return self._do_drop(agent, action)
            case WaitAction():  return ActionSuccess()
            case MergeAction(): return self._do_merge(agent, action)
            case _:             return ActionFailure(FailureReason.NOT_IMPLEMENTED)

    # ------------------------------------------------------------------
    # Private action handlers
    # Called when the Model dispatch action on Agent
    # ------------------------------------------------------------------

    def _do_move(self, agent: MesaAgentAdapter, action: MoveAction) -> ActionResult:
        x, y = agent.pos
        dx, dy = action.delta
        new_pos = (x + dx, y + dy)

        if self.grid.out_of_bounds(new_pos):
            return ActionFailure(FailureReason.OUT_OF_BOUNDS)

        if self.grid.is_cell_occupied(new_pos):
            return ActionFailure(FailureReason.CELL_OCCUPIED)

        self.grid.move_agent(agent, new_pos)
        return ActionSuccess()

    def _do_pick(self, agent: MesaAgentAdapter, action: PickAction) -> ActionResult:
        """ Pick up waste matching the agent's tier from the current cell. """
        cell_agents: list[Agent] = self.grid.get_cell_list_contents([agent.pos])
        waste_agents: list[Waste] = [a for a in cell_agents if isinstance(a, Waste)]

        if not waste_agents:
            return ActionFailure(FailureReason.NO_WASTE_AT_POSITION)

        waste_to_pick: Waste | None = None
        for waste in waste_agents:
            if waste.tier == agent.tier:
                waste_to_pick = waste
                break

        if waste_to_pick is None:
            return ActionFailure(FailureReason.WASTE_TYPE_MISMATCH)

        if agent.memory.carried_wastes:
            return ActionFailure(FailureReason.CARRY_CAPACITY_FULL)

        agent.memory.carried_wastes.append(waste_to_pick.type)
        self.grid.remove_agent(waste_to_pick)
        return ActionSuccess()

    def _do_drop(self, agent: MesaAgentAdapter, action: DropAction) -> ActionResult:
        """ Dispose of carried waste at the current cell's disposal zone. """
        if not agent.memory.carried_wastes:
            return ActionFailure(FailureReason.NOT_CARRYING_WASTE)

        cell_agents: list[Agent] = self.grid.get_cell_list_contents([agent.pos])
        if not any(isinstance(a, WasteDisposalZone) for a in cell_agents):
            return ActionFailure(FailureReason.NOT_AT_DISPOSAL_ZONE)

        agent.memory.carried_wastes.pop()
        return ActionSuccess()

    def _do_merge(self, agent: MesaAgentAdapter, action: MergeAction) -> ActionResult:
        """
        Merge the carried waste with a same-tier waste on the current cell.

        Preconditions:
        1. Agent carries exactly one waste whose type matches its own tier.
           (Carrying a higher-tier waste — already a merged result — is rejected
           with ALREADY_MERGED so agents cannot chain merges.)
        2. Current cell has at least one waste of the agent's tier to consume.
        3. The carried waste type has a next tier (RED cannot be merged).

        On success: the cell waste is removed from the grid and the agent's
        carried waste is upgraded to the next tier in-place.
        """
        # 1) Must be carrying exactly one own-tier waste
        if len(agent.memory.carried_wastes) != 1:
            return ActionFailure(FailureReason.NOT_CARRYING_WASTE)

        carried = agent.memory.carried_wastes[0]
        if carried.value != agent.tier:
            return ActionFailure(FailureReason.ALREADY_MERGED)

        # 2) Next tier must exist (RED has none)
        merged_type = carried.merged
        if merged_type is None:
            return ActionFailure(FailureReason.ALREADY_MERGED)

        # 3) Cell must have a same-tier waste to consume
        cell_agents: list[Agent] = self.grid.get_cell_list_contents([agent.pos])
        waste_on_cell = [a for a in cell_agents if isinstance(a, Waste) and a.tier == agent.tier]
        if not waste_on_cell:
            return ActionFailure(FailureReason.NO_WASTE_AT_POSITION)

        # Consume the cell waste and upgrade the carried waste to the merged type
        self.grid.remove_agent(waste_on_cell[0])
        agent.memory.carried_wastes[0] = merged_type
        return ActionSuccess()
