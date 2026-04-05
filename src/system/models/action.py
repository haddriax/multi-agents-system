from abc import ABC
from dataclasses import dataclass
from enum import Enum

from src.system.models.types import Direction


class FailureReason(Enum):
    OUT_OF_BOUNDS        = "out_of_bounds"         # the target is outside the grid
    CELL_OCCUPIED        = "cell_occupied"         # move target has another agent
    NO_WASTE_AT_POSITION = "no_waste_at_position"  # nothing to pick up
    WASTE_TYPE_MISMATCH  = "waste_type_mismatch"   # waste type doesn't match agent tier
    CARRY_CAPACITY_FULL  = "carry_capacity_full"   # agent at carry limit
    NOT_CARRYING_WASTE   = "not_carrying_waste"    # nothing to drop
    NOT_AT_DISPOSAL_ZONE = "not_at_disposal_zone"  # not on a WasteDisposalZone cell
    NOT_IMPLEMENTED      = "not_implemented"       # action type exists but is not yet implemented

class ActionResult(ABC):
    pass

@dataclass(frozen=True)
class ActionSuccess(ActionResult):
    pass

@dataclass(frozen=True)
class ActionFailure(ActionResult):
    reason: FailureReason

class Action:
    """
    Marker base class for all actions.
    An Action expresses the agent's intent for one step; SystemModel.do() executes it.
    """
    pass


@dataclass(frozen=True)
class MoveAction(Action):
    direction: Direction


@dataclass(frozen=True)
class PickAction(Action):
    """ Agent attempts to pick up waste on the same cell. """
    pass


@dataclass(frozen=True)
class DropAction(Action):
    """ Agent drops carried waste at the disposal zone. """
    pass


@dataclass(frozen=True)
class WaitAction(Action):
    pass


@dataclass(frozen=True)
class MergeAction(Action):
    """ @todo Next action to implement. Delayed due to the Action system refactor. """
    pass
