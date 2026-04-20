"""
    For action execution, we use a command pattern. It's a more scalable way to decouple the action definitions from their execution logic, which is in SystemModel.do().
    Since the Mesa model must execute the action, this design keep the boundary between Mesa executing and the Agent requesting an execution.
    Agent -> "Can you execute that for me?" -> Mesa -> "Yes, it's fine. Executing your action and updating the world"

    It's also convenient to put stubs that can be filled later, and decoupling definition and execution is better for teamwork and code organization.
    Last, we can easily change the payload we sent or receive to execute action, since it's self contained.

    Note: pattern is data driven, no execution logic inside the command, that would conflict with Mesa almighty model architecture.
"""

from abc import ABC
from dataclasses import dataclass
from enum import Enum

from src.system.models.types import Direction, WasteType


class FailureReason(Enum):
    """ Easy way to idenfiy all our failure reasons and the one that are handled. """
    OUT_OF_BOUNDS        = "out_of_bounds"         # the target is outside the grid
    CELL_OCCUPIED        = "cell_occupied"         # move target has another agent
    NO_WASTE_AT_POSITION = "no_waste_at_position"  # nothing to pick up
    WASTE_TYPE_MISMATCH  = "waste_type_mismatch"   # waste type doesn't match agent tier
    CARRY_CAPACITY_FULL  = "carry_capacity_full"   # agent at carry limit
    NOT_CARRYING_WASTE   = "not_carrying_waste"    # nothing to drop
    NOT_AT_DISPOSAL_ZONE = "not_at_disposal_zone"  # not on a WasteDisposalZone cell
    NOT_IMPLEMENTED      = "not_implemented"       # action type exists but is not yet implemented
    INVALID_DIRECTION    = "invalid_direction"     # direction value is not a known Direction member
    ALREADY_MERGED       = "already_merged"        # carried waste is above agent tier, cannot merge further
    RESERVATION_CONFLICT = "reservation_conflict"  # another bot already holds the reservation for this cell

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
    Marker base class for all actions.
    An Action expresses the agent's intent for one step; SystemModel.do() executes it.
    """
    pass


@dataclass(frozen=True)
class MoveAction(Action):
    """ Agent attemps to move in a direction. """
    direction: Direction

    @property
    def delta(self) -> tuple[int, int]:
        match self.direction:
            case Direction.UP:         return ( 0,  1)
            case Direction.DOWN:       return ( 0, -1)
            case Direction.LEFT:       return (-1,  0)
            case Direction.RIGHT:      return ( 1,  0)
            case Direction.UP_LEFT:    return (-1,  1)
            case Direction.UP_RIGHT:   return ( 1,  1)
            case Direction.DOWN_LEFT:  return (-1, -1)
            case Direction.DOWN_RIGHT: return ( 1, -1)


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
    """ Simply wait for one step. """
    pass


@dataclass(frozen=True)
class MergeAction(Action):
    """
    Merge the carried waste with a same-tier waste on the current cell.

    Logic:
    - Agent must be carrying exactly ONE waste matching its own tier (not an
      already-merged result).
    - The current cell must have another waste of that same tier.
    - The two wastes are consumed and replaced by ONE waste of the next tier
      (GREEN + GREEN → YELLOW, YELLOW + YELLOW → RED).
    - The agent carries the resulting higher-tier waste but cannot merge it
      further: a green agent holding yellow waste can carry and drop it, not
      merge it again.
    - RED waste has no higher tier; attempting to merge it fails with
      ALREADY_MERGED.

    No fields, the target is always the waste on the agent's current cell.
    """
    pass


@dataclass(frozen=True)
class HandoffAction(Action):
    """
    Deposit the carried (merged) waste onto the current cell for the next-tier bot to collect.

    Used by Green and Yellow at their zone boundary.
    """
    pass


@dataclass(frozen=True)
class ReserveAction(Action):
    """
    Claim a waste cell before navigating to it.

    Fails with RESERVATION_CONFLICT if another bot already holds a reservation
    for this position!

    priority=True is for bots already carrying a waste and looking for one to merge it with.
    It overrides a non-priority reservation.
    """
    waste_type: WasteType
    position: tuple[int, int]
    priority: bool = False
