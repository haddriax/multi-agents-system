from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

from mesa import Agent

from src.system.models.types import Direction
from src.system.entities.objects.waste import Waste

if TYPE_CHECKING:
    from src.system.system_model import SystemModel
    from src.system.entities.agents.base_agent import BaseAgent

class FailureReason(Enum):
    OUT_OF_BOUNDS        = "out_of_bounds"         # the target is outside the grid
    CELL_OCCUPIED        = "cell_occupied"         # move target has another agent
    NO_WASTE_AT_POSITION = "no_waste_at_position"  # nothing to pick up
    WASTE_TYPE_MISMATCH  = "waste_type_mismatch"   # waste type doesn't match agent tier
    CARRY_CAPACITY_FULL  = "carry_capacity_full"   # agent at carry limit
    NOT_CARRYING_WASTE   = "not_carrying_waste"    # nothing to drop
    NOT_AT_DISPOSAL_ZONE = "not_at_disposal_zone"  # not on a WasteDisposalZone cell


class ActionResult(ABC):
    pass

@dataclass(frozen=True)
class ActionSuccess(ActionResult):
    pass

@dataclass(frozen=True)
class ActionFailure(ActionResult):
    reason: FailureReason

class Action(ABC):
    """
    Base class for every action, ensuring they all implement the execute() method.
    Action exists so the Agent can decide of an action to perform, and transmit it to the model for execution.
    """
    @abstractmethod
    def execute(self, model: SystemModel, agent: BaseAgent) -> ActionResult:
        ...

@dataclass(frozen=True)
class MoveAction(Action):
    direction: Direction

    def execute(self, model: SystemModel, agent: BaseAgent) -> ActionResult:
        x, y = agent.pos

        match self.direction:
            case Direction.UP:         new_pos = (x,     y + 1)
            case Direction.DOWN:       new_pos = (x,     y - 1)
            case Direction.LEFT:       new_pos = (x - 1, y    )
            case Direction.RIGHT:      new_pos = (x + 1, y    )
            case Direction.UP_LEFT:    new_pos = (x - 1, y + 1)
            case Direction.UP_RIGHT:   new_pos = (x + 1, y + 1)
            case Direction.DOWN_LEFT:  new_pos = (x - 1, y - 1)
            case Direction.DOWN_RIGHT: new_pos = (x + 1, y - 1)

        if model.grid.out_of_bounds(new_pos):
            return ActionFailure(FailureReason.OUT_OF_BOUNDS)

        if model.grid.is_cell_occupied(new_pos):
            return ActionFailure(FailureReason.CELL_OCCUPIED)

        model.grid.move_agent(agent, new_pos)
        return ActionSuccess()


@dataclass(frozen=True)
class PickAction(Action):
    """
    Agent attempt to pick the waste on the same cell they are.
    Done by removing the Agent from the Grid and keeping a reference to it through the agent.
    """
    def execute(self, model: SystemModel, agent: BaseAgent) -> ActionResult:
        cell_agents: list[Agent] = model.grid.get_cell_list_contents([agent.pos])
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

        if len(agent.knowledge.carried_wastes) >= agent.carry_capacity:
            return ActionFailure(FailureReason.CARRY_CAPACITY_FULL)

        agent.knowledge.carried_wastes.append(waste_to_pick)
        model.grid.remove_agent(waste_to_pick)
        return ActionSuccess()


@dataclass(frozen=True)
class DropAction(Action):
    """ Drop the carried Waste on the same cell the Agent is. """
    def execute(self, model: SystemModel, agent: BaseAgent) -> ActionResult:
        if not agent.knowledge.carried_wastes:
            return ActionFailure(FailureReason.NOT_CARRYING_WASTE)

        coordinates: tuple[int, int] = agent.knowledge.position
        waste_to_drop: Waste = agent.knowledge.carried_wastes.pop()

        model.grid.place_agent(waste_to_drop, coordinates)

        return ActionSuccess()


@dataclass(frozen=True)
class WaitAction(Action):
    def execute(self, model: SystemModel, agent: BaseAgent) -> ActionResult:
        return ActionSuccess()


@dataclass(frozen=True)
class MergeAction(Action):
    def execute(self, model: SystemModel, agent: BaseAgent) -> ActionResult:
        # @todo Next action to implement. Delayed due the refactor of the Action system.
        raise NotImplementedError("MergeAction is not yet implemented.")
