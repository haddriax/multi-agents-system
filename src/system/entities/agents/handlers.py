import random
from typing import Callable

from src.system.models.action import (
    Action,
    DropAction,
    HandoffAction,
    MergeAction,
    MoveAction,
    PickAction,
    ReserveAction,
    WaitAction,
)
from src.system.models.memory import Memory
from src.system.models.types import Direction, RobotType, WasteType
from src.system.tools.pathfinder import Pathfinder


Handler = Callable[[Memory, int, tuple[int, int]], "Action | None"]


def _move_towards(origin: tuple[int, int], target: tuple[int, int]) -> Action:
    """Compute a single-step action from origin toward target."""
    ox, oy = origin
    tx, ty = target

    dx: int = (tx > ox) - (tx < ox)
    dy: int = (ty > oy) - (ty < oy)

    match (dx, dy):
        case (1, 1):   return MoveAction(Direction.UP_RIGHT)
        case (1, -1):  return MoveAction(Direction.DOWN_RIGHT)
        case (-1, 1):  return MoveAction(Direction.UP_LEFT)
        case (-1, -1): return MoveAction(Direction.DOWN_LEFT)
        case (1, 0):   return MoveAction(Direction.RIGHT)
        case (-1, 0):  return MoveAction(Direction.LEFT)
        case (0, 1):   return MoveAction(Direction.UP)
        case (0, -1):  return MoveAction(Direction.DOWN)
        case _:        return WaitAction()


def _navigate(
    memory: Memory,
    target: tuple[int, int],
    grid_dims: tuple[int, int],
) -> Action | None:
    """
    Produce the next move toward the bot's target, replanning on blockage.

    Returns:
      MoveAction: when a valid next step exists
      WaitAction: when the bot is stuck
      None: when bot arrives at position
    """
    if memory.position == target:
        return None

    grid_w, grid_h = grid_dims

    if memory.target_cell != target or not memory.planned_path:
        memory.target_cell = target
        memory.planned_path = Pathfinder.a_star_find_path_to(
            memory.position, target, memory, grid_w, grid_h,
        )

    if not memory.planned_path:
        return WaitAction()

    next_pos = memory.planned_path[0]
    cell = memory.belief_map.get(next_pos)
    if cell is not None and cell.robot_type != RobotType.NONE:
        # Planned step is now blocked — recompute with the blocker in map.
        memory.planned_path = Pathfinder.a_star_find_path_to(
            memory.position, target, memory, grid_w, grid_h,
        )
        if not memory.planned_path:
            return WaitAction()
        next_pos = memory.planned_path[0]
        cell = memory.belief_map.get(next_pos)
        if cell is not None and cell.robot_type != RobotType.NONE:
            return WaitAction()

    return _move_towards(memory.position, next_pos)


def _handle_yield(memory: Memory, tier: int, grid_dims: tuple[int, int]) -> Action | None:
    """
    Step off a cell reserved by another bot. Implemented to solve the deadlock created by the reservation.
    """
    perception = memory.last_perception
    if perception is None:
        return None
    foreign = perception.foreign_reservations
    if memory.position not in foreign:
        return None

    grid_w, grid_h = grid_dims
    zone_max_x = memory.max_x if memory.max_x is not None else grid_w - 1
    x, y = memory.position

    for direction in Direction:
        action = MoveAction(direction=direction)
        dx, dy = action.delta
        nx, ny = x + dx, y + dy
        if nx < 0 or nx > zone_max_x or ny < 0 or ny >= grid_h:
            continue
        if (nx, ny) in foreign:
            continue
        cell = memory.belief_map.get((nx, ny))
        if cell is not None and cell.robot_type != RobotType.NONE:
            continue
        return action

    return WaitAction()


def _handle_merge(memory: Memory, tier: int, grid_dims: tuple[int, int]) -> Action | None:
    """Fire MergeAction when carrying own-tier waste and same-tier waste lies underfoot."""
    if len(memory.carried_wastes) != 1:
        return None

    carried = memory.carried_wastes[0]
    if carried.value != tier:
        return None  # already carrying a merged (higher-tier) waste

    if carried.merged is None:
        return None  # RED has no higher tier

    cell = memory.belief_map.get(memory.position)
    if cell is None or cell.waste_type.value != tier:
        return None

    return MergeAction()


def _find_closest_waste(memory: Memory, tier: int) -> tuple[int, int] | None:
    """Return the nearest cell with tier-matching waste within the allowed zone, or None."""
    best_pos = None
    best_dist = float("inf")

    for pos, cell in memory.belief_map.items():
        # Ignore wastes that are outside the Agent action zones
        if memory.max_x is not None and pos[0] > memory.max_x:
            continue
        if cell.waste_type.value == tier:
            dist = abs(pos[0] - memory.position[0]) + abs(pos[1] - memory.position[1])
            if dist < best_dist:
                best_dist = dist
                best_pos = pos

    return best_pos


def _handle_seek(memory: Memory, tier: int, grid_dims: tuple[int, int]) -> Action | None:
    """
    Reserve-then-navigate toward tier-matching waste.
    """
    # 1. Validate active reservation against belief_map
    if memory.active_reservation is not None:
        cell = memory.belief_map.get(memory.active_reservation)
        if cell is None or cell.waste_type.value != tier:
            memory.active_reservation = None
            memory.target_cell = None
            memory.planned_path = []

    # 2. Navigate toward reserved position
    if memory.active_reservation is not None:
        target = memory.active_reservation
        move = _navigate(memory, target, grid_dims)
        if move is not None:
            return move

        # Arrived at target
        if memory.carried_wastes:
            # Already picked, so we remove the goal
            memory.active_reservation = None
            memory.target_cell = None
            memory.planned_path = []
            return None
        memory.active_reservation = None
        return PickAction()

    # 3. No reservation then find nearest waste and send ReserveAction
    goal = _find_closest_waste(memory, tier)
    if goal is None:
        return None
    can_merge = (
        len(memory.carried_wastes) == 1
        and memory.carried_wastes[0].value == tier
    )
    return ReserveAction(waste_type=WasteType(tier), position=goal, priority=can_merge)


def _handle_deposit(memory: Memory, tier: int, grid_dims: tuple[int, int]) -> Action | None:
    """Navigate to the deposit point and drop the carried waste there."""
    if not memory.carried_wastes:
        return None

    carried = memory.carried_wastes[0]

    if memory.max_x is not None:
        # Green / Yellow: only deposit merged (higher-tier) waste
        if carried.value == tier:
            return None
        target = (memory.max_x, memory.position[1])
        final_action: Action = HandoffAction()
    else:
        # Red: deposit any carried waste at the WasteDisposalZone
        disposal_pos = next(
            (pos for pos, cell in memory.belief_map.items() if cell.has_disposal_zone),
            None,
        )

        # For this version, the zone is know but in case, fallback to explo
        if disposal_pos is None:
            return None
        target = disposal_pos
        final_action = DropAction()

    move = _navigate(memory, target, grid_dims)
    if move is not None:
        return move

    # Arrived at target
    memory.target_cell = None
    memory.planned_path = []
    return final_action


def _handle_explore(memory: Memory, tier: int, grid_dims: tuple[int, int]) -> Action:
    """Frontier exploration: step toward the nearest unobserved cell. Falls back to random."""
    grid_w, grid_h = grid_dims
    known = memory.belief_map

    best_pos: tuple[int, int] | None = None
    best_dist: float = float("inf")

    zone_max_x = memory.max_x if memory.max_x is not None else grid_w - 1

    for (kx, ky) in known:
        for dx in range(-1, 2):
            for dy in range(-1, 2):
                candidate = (kx + dx, ky + dy)
                if candidate in known:
                    continue
                cx, cy = candidate
                if cx < 0 or cx > zone_max_x or cy < 0 or cy >= grid_h:
                    continue
                dist = abs(cx - memory.position[0]) + abs(cy - memory.position[1])
                if dist < best_dist:
                    best_dist = dist
                    best_pos = candidate

    if best_pos is not None:
        return _move_towards(memory.position, best_pos)

    return MoveAction(random.choice(list(Direction)))


# Default handler, suitable for Green and Yellow that have same behavior
BASE_HANDLERS: list[Handler] = [
    _handle_yield,
    _handle_merge,
    _handle_deposit,
    _handle_seek,
    _handle_explore,
]

# Red agent must kknow the disposal place and interact with it.
# Also, they can't merge waste
RED_HANDLERS: list[Handler] = [
    _handle_yield,
    _handle_deposit,
    _handle_seek,
    _handle_explore,
]