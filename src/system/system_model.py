from typing import Sequence

from mesa import Model, DataCollector, Agent

from src.system.config import Config
from src.system.entities.agents.mesa_adapter import MesaAgentAdapter
from src.system.map.navigable_grid import NavigableGrid
from src.system.models.perception import Perception, CellContent
from src.system.models.action import (
    Action, ActionResult, ActionSuccess, ActionFailure, FailureReason,
    MoveAction, PickAction, DropAction, WaitAction, MergeAction, HandoffAction, ReserveAction,
)
from src.system.models.message import WasteDiscoveredMessage, WasteCancelledMessage
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

        # Reservation registry: pos → (is_priority, agent_unique_id)
        self._reservations: dict[tuple[int, int], tuple[bool, int]] = {}

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

        self._seed_disposal_zone_belief()

    def get_zone(self, x: int) -> str:
        return self.grid.get_zone(x)

    def _seed_disposal_zone_belief(self) -> None:
        """Add the WasteDisposalZone position into the belief_map of Red agents"""
        zone = next((a for a in self.agents if isinstance(a, WasteDisposalZone)), None)
        if zone is None:
            return
        cell_content = self._build_cell_content(self.grid.get_cell_list_contents([zone.pos]))
        for agent in self.agents:
            if isinstance(agent, MesaAgentAdapter) and type(agent).MAX_ZONE is None:
                agent.memory.belief_map[zone.pos] = cell_content

    def step(self):
        """ Execute one world step. Note: self.steps is managed by Mesa (_do_step wrapper). """
        self.datacollector.collect(self)
        self.agents.shuffle_do("step")
        self._process_outboxes()

    def _process_outboxes(self) -> None:
        """Broadcast each agent's outbox entries to same-tier peers as WasteDiscoveredMessage."""
        for agent in self.agents:
            if not isinstance(agent, MesaAgentAdapter):
                continue
            for waste_type, pos in agent.memory.outbox:
                # Skip if the waste is already gone (picked during the step)
                cell_agents = self.grid.get_cell_list_contents([pos])
                if not any(isinstance(a, Waste) and a.tier == agent.tier for a in cell_agents):
                    continue
                msg = WasteDiscoveredMessage(waste_type=waste_type, position=pos)
                for a in self.agents:
                    if (isinstance(a, MesaAgentAdapter)
                            and a.unique_id != agent.unique_id
                            and a.tier == agent.tier
                            and not any(
                                isinstance(m, WasteDiscoveredMessage) and m.position == pos
                                for m in a.memory.mailbox
                            )):
                        a.memory.mailbox.append(msg)
            agent.memory.outbox.clear()

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

        perceived_positions = {pos for pos, _ in readings}
        foreign_reservations = frozenset(
            pos for pos, (_, holder_id) in self._reservations.items()
            if holder_id != agent.unique_id and pos in perceived_positions
        )

        return Perception(
            perceiver_position=agent.pos,
            readings=tuple(readings),
            step=self.steps,
            perceiver_id=agent.unique_id,
            foreign_reservations=foreign_reservations,
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
        has_disposal_zone = False

        for agent in agents:
            if isinstance(agent, Radioactivity):
                radioactivity_value = agent.level
            elif isinstance(agent, Waste):
                waste_type = agent.type
                waste_quantity = getattr(agent, 'quantity', 1)
            elif isinstance(agent, MesaAgentAdapter):
                robot_type = agent.robot_type
            elif isinstance(agent, WasteDisposalZone):
                has_disposal_zone = True

        return CellContent(
            radioactivity_value=radioactivity_value,
            waste_type=waste_type,
            waste_quantity=waste_quantity,
            robot_type=robot_type,
            has_disposal_zone=has_disposal_zone,
        )

    def do(self, agent: MesaAgentAdapter, action: Action) -> ActionResult:
        """ Dispatch and execute an action for the given agent. """
        match action:
            case MoveAction():    return self._do_move(agent, action)
            case PickAction():    return self._do_pick(agent, action)
            case DropAction():    return self._do_drop(agent, action)
            case WaitAction():    return ActionSuccess()
            case MergeAction():   return self._do_merge(agent, action)
            case HandoffAction(): return self._do_handoff(agent, action)
            case ReserveAction(): return self._do_reserve(agent, action)
            case _:               return ActionFailure(FailureReason.NOT_IMPLEMENTED)

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
        entry = self._reservations.get(agent.pos)
        if entry is not None and entry[1] != agent.unique_id:
            return ActionFailure(FailureReason.RESERVATION_CONFLICT)

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
        self._reservations.pop(agent.pos, None)
        self._broadcast_cancel(agent, agent.pos)
        return ActionSuccess()

    def _do_reserve(self, agent: MesaAgentAdapter, action: ReserveAction) -> ActionResult:
        """
        Claim a waste cell. Priority requests (bot already carries a waste of its own level) can override other reservation.

        A bot can only hold one reservation at a time and any previous reservation by the same bot is deleted.
        """
        pos = action.position
        entry = self._reservations.get(pos)
        if entry is not None:
            existing_priority, holder_id = entry
            if holder_id == agent.unique_id:
                return ActionSuccess()
            cell_agents = self.grid.get_cell_list_contents([pos])
            waste_exists = any(
                isinstance(a, Waste) and a.tier == agent.tier for a in cell_agents
            )
            stale = not waste_exists
            override = action.priority and not existing_priority
            if not (stale or override):
                return ActionFailure(FailureReason.RESERVATION_CONFLICT)

        # Release any previous reservation this agent was holding elsewhere
        previous = [
            p for p, (_, uid) in self._reservations.items()
            if uid == agent.unique_id and p != pos
        ]
        for p in previous:
            self._reservations.pop(p)

        self._reservations[pos] = (action.priority, agent.unique_id)
        return ActionSuccess()

    def _do_drop(self, agent: MesaAgentAdapter, action: DropAction) -> ActionResult:
        """ Dispose of carried waste at the current cell's disposal zone. """
        if not agent.memory.carried_wastes:
            return ActionFailure(FailureReason.NOT_CARRYING_WASTE)

        cell_agents: list[Agent] = self.grid.get_cell_list_contents([agent.pos])
        zone = next((a for a in cell_agents if isinstance(a, WasteDisposalZone)), None)
        if zone is None:
            return ActionFailure(FailureReason.NOT_AT_DISPOSAL_ZONE)

        agent.memory.carried_wastes.pop()
        zone.waste_received += 1
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
        self._reservations.pop(agent.pos, None)
        self._broadcast_cancel(agent, agent.pos)
        return ActionSuccess()

    def _do_handoff(self, agent: MesaAgentAdapter, action: HandoffAction) -> ActionResult:
        """ Place the carried waste onto the current cell for the next-tier bot to collect. """
        if not agent.memory.carried_wastes:
            return ActionFailure(FailureReason.NOT_CARRYING_WASTE)

        waste_type = agent.memory.carried_wastes.pop()
        new_waste = Waste(self, waste_type)
        self.grid.place_agent(new_waste, agent.pos)
        self._notify_tier(waste_type, agent.pos)
        return ActionSuccess()

    def _broadcast_cancel(self, source: MesaAgentAdapter, pos: tuple[int, int]) -> None:
        """Notify same-tier boys that the waste is gone."""
        msg = WasteCancelledMessage(position=pos)
        for a in self.agents:
            if (isinstance(a, MesaAgentAdapter)
                    and a.unique_id != source.unique_id
                    and a.tier == source.tier):
                a.memory.mailbox.append(msg)

    def _notify_tier(self, waste_type: WasteType, pos: tuple[int, int]) -> None:
        """Deliver a WasteDiscoveredMessage to all agents with the same tier as the deposited waste type."""
        msg = WasteDiscoveredMessage(waste_type=waste_type, position=pos)
        for a in self.agents:
            if isinstance(a, MesaAgentAdapter) and a.tier == waste_type.value:
                if not any(m.position == pos for m in a.memory.mailbox):
                    a.memory.mailbox.append(msg)

