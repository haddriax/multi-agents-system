import random
from typing import Callable

from src.system.models.action import (
    Action,
    MergeAction,
    MoveAction,
    PickAction,
    WaitAction,
)
from src.system.models.memory import Memory
from src.system.models.types import Direction, RobotType
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
    """Navigate toward the nearest tier-matching waste. Returns None if none is known."""
    grid_w, grid_h = grid_dims

    # 1. Validate current goal
    if memory.target_cell is not None:
        cell = memory.belief_map.get(memory.target_cell)
        if cell is None or cell.waste_type.value != tier:
            memory.target_cell = None
            memory.planned_path = []

    # 2. Find new goal and compute path
    if memory.target_cell is None:
        goal = _find_closest_waste(memory, tier)
        if goal is not None:
            memory.target_cell = goal
            memory.planned_path = Pathfinder.a_star_find_path_to(
                memory.position, goal, memory, grid_w, grid_h,
            )

    # No tier-matching waste known, defer to exploration
    if memory.target_cell is None:
        return None

    # 3. Follow path
    if memory.planned_path:
        next_pos = memory.planned_path[0]
        cell = memory.belief_map.get(next_pos)
        if cell is not None and cell.robot_type != RobotType.NONE:
            return WaitAction()  # blocked by a bot, retry next turn
        return _move_towards(memory.position, next_pos)

    # 4. Standing on goal cell
    if memory.position == memory.target_cell:
        if memory.carried_wastes:
            memory.target_cell = None
            memory.planned_path = []
            return None
        return PickAction()

    return None


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
    _handle_merge,
    _handle_seek,
    _handle_explore,
]

# Red agent must kknow the disposal place and interact with it.
# Also, they can't merge waste
RED_HANDLERS: list[Handler] = [
    _handle_seek,
    _handle_explore,
]