from abc import ABC

from mesa import Agent, Model

from src.system.models.action import Action, ActionResult, ActionSuccess, MergeAction, MoveAction, WaitAction
from src.system.models.memory import Memory
from src.system.models.perception import Perception
from src.system.models.types import RobotType, Direction
from src.system.tools.pathfinder import Pathfinder

import random


class Sensor:
    """
    Represent a way to perceive the environnement.
    For now, we only have an optical sensor, but we could add more like radiation sensor,
    so this class force the design to work with n named sensors.
    """
    def __init__(self, radius: int = 5) -> None:
        self.radius = radius

class OpticalSensor(Sensor):
    """
    The most basic and principal sensor.
    """
    def __init__(self, radius: int = 3) -> None:
        super().__init__(radius)


class BaseAgent(Agent, ABC):
    robot_type = RobotType.NONE
    tier: int = 0

    def __init__(self, m: Model):
        super().__init__(m)
        self.memory: Memory = Memory(position=(0, 0))
        """
        Current memory of the world the agent is in.
        """

        self.carry_capacity = 1 # Current design imply only 1 carry capcity and inplace merging.
        self.sensors: dict[str, Sensor] = {
            "optical": OpticalSensor()
        }

        match self.robot_type:
            case RobotType.GREEN:
                self.tier = 1
            case RobotType.YELLOW:
                self.tier = 2
            case RobotType.RED:
                self.tier = 3

    def get_memory(self) -> Memory:
        """ Return the memory object: the beliefs about the environnement."""
        return self.memory

    def force_percept_update(self) -> None:
        """
        Force an update of the beliefs, without doing a step.
        Usually used to update the belief map of the spawning agent.
        """
        perception: Perception = self.model.perceive(self)
        self.update_beliefs(perception)

    def step(self) -> None:
        """ Mesa step method: Perceive, Update Beliefs, Deliberate, Act """
        perception: Perception = self.model.perceive(self)
        self.update_beliefs(perception)
        action: Action = self.deliberate(self.memory)
        result: ActionResult = self.model.do(self, action)
        self.memory.last_action = action

        # Advance the planned path only after a successful move so that a cell
        # that became occupied between planning and execution is retried next turn.
        if isinstance(action, MoveAction) and isinstance(result, ActionSuccess):
            if self.memory.planned_path:
                self.memory.planned_path.pop(0)

    def follow_goal(self, memory: Memory):
        # 1. Validate current goal
        if memory.target_cell is not None:
            cell = memory.belief_map.get(memory.target_cell)
            # Waste has been taken, abort the goal.
            if not cell.has_waste:
                memory.target_cell = None
                memory.planned_path = []

            if cell is None or cell.waste_type.value != self.robot_type.value:
                memory.target_cell = None
                memory.planned_path = []

        # 2. Find new goal and compute path
        if memory.target_cell is None:
            goal = self._find_possible_closest_waste(memory)
            if goal:
                memory.target_cell = goal
                memory.planned_path = Pathfinder.a_star_find_path_to(
                    memory.position, goal, memory,
                    self.model.grid.width, self.model.grid.height,
                )

        # 3. Follow the path
        if memory.planned_path:
            next_pos = memory.planned_path[0]
            cell = memory.belief_map.get(next_pos)
            if cell is not None and cell.robot_type != RobotType.NONE:
                return WaitAction()  # blocked by a bot, retry next turn
            # pop(0) happens in step() after ActionSuccess, not here
            return self.move_towards(next_pos)

    def deliberate(self, memory: Memory) -> Action:
        """
        Path-following deliberation:
        0. Merge if carrying own-tier waste and same-tier waste is underfoot
        1. Validate current goal (waste may have disappeared)
        2. Find a new goal if needed and compute A* path
        3. Follow the path: wait if the next cell is blocked by a bot
        4. Bot is on goal cell: wait for pick/drop logic
        5. No known waste: explore toward nearest frontier cell
        """
        # 0. Merge opportunity: carrying own-tier waste + same-tier waste on this cell
        merge: MergeAction = self._should_merge(memory)
        if merge is not None:
            return merge

        # 1. Validate current goal
        if memory.target_cell is not None:
            cell = memory.belief_map.get(memory.target_cell)
            if cell is None or cell.waste_type.value != self.robot_type.value:
                memory.target_cell = None
                memory.planned_path = []

        # 2. Find new goal and compute path
        if memory.target_cell is None:
            goal = self._find_possible_closest_waste(memory)
            if goal:
                memory.target_cell = goal
                memory.planned_path = Pathfinder.a_star_find_path_to(
                    memory.position, goal, memory,
                    self.model.grid.width, self.model.grid.height,
                )

        # 3. Follow the path
        if memory.planned_path:
            next_pos = memory.planned_path[0]
            cell = memory.belief_map.get(next_pos)
            if cell is not None and cell.robot_type != RobotType.NONE:
                return WaitAction()  # blocked by a bot, retry next turn
            # pop(0) happens in step() after ActionSuccess, not here
            return self.move_towards(next_pos)

        # 4. Bot is on goal
        if memory.target_cell == self.pos:
            return WaitAction()

        # 5. No known waste, navigate toward the nearest unseen frontier cell
        return self._explore(memory)

    def move_towards(self, target_pos: tuple[int, int]) -> MoveAction:
        """
        Compute the action needed to move towards the target position based on the agent's current position.
        """
        agent_x, agent_y = self.memory.position
        target_x, target_y = target_pos

        dx: int = (target_x > agent_x) - (target_x < agent_x)
        dy: int = (target_y > agent_y) - (target_y < agent_y)

        # Match the (dx, dy) vector to the correct action
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

    def _find_possible_closest_waste(self, memory: Memory) -> tuple[int, int] | None:
        """ Look in memory to find the closest waste. """
        best_pos = None
        best_dist = float('inf')

        for pos, cell in memory.belief_map.items():
            if cell.waste_type.value == self.robot_type.value:
                dist = abs(pos[0] - memory.position[0]) + abs(pos[1] - memory.position[1])
                if dist < best_dist:
                    best_dist = dist
                    best_pos = pos

        return best_pos

    def _should_merge(self, memory: Memory) -> MergeAction | None:
        """
        Return a MergeAction when all merge preconditions are satisfied on the
        current cell, otherwise None.

        Conditions (mirrors _do_merge validation in SystemModel):
        - Carrying exactly one waste whose type matches this agent's own tier.
          (An already-merged higher-tier waste is ineligible — no chaining.)
        - The agent's current cell (from belief_map) contains a waste of the
          same tier to be consumed.
        - The waste type has a next tier (RED cannot be merged).

        This is a belief-based check — the model re-validates on execution.
        """
        if len(memory.carried_wastes) != 1:
            return None

        carried = memory.carried_wastes[0]
        if carried.value != self.tier:
            return None  # already carrying a merged (higher-tier) waste

        if carried.merged is None:
            return None  # RED has no higher tier

        cell = memory.belief_map.get(memory.position)
        if cell is None or cell.waste_type.value != self.tier:
            return None  # no same-tier waste visible on this cell

        return MergeAction()

    def _explore(self, memory: Memory) -> Action:
        """
        Frontier exploration stub: move toward the nearest grid cell that is
        adjacent to the known belief_map but not yet observed.

        The frontier is the boundary of the agent's explored territory — every
        in-bounds cell that neighbours at least one known cell but has not itself
        been perceived yet.  Picking the closest frontier target and taking one
        step toward it ensures systematic coverage rather than random wandering.

        Falls back to a random move only when the entire reachable area is already
        mapped (i.e. no frontier exists).
        """
        grid_w = self.model.grid.width
        grid_h = self.model.grid.height
        known = memory.belief_map

        best_pos: tuple[int, int] | None = None
        best_dist: float = float('inf')

        for (kx, ky) in known:
            for dx in range(-1, 2):
                for dy in range(-1, 2):
                    candidate = (kx + dx, ky + dy)
                    if candidate in known:
                        continue
                    cx, cy = candidate
                    if cx < 0 or cx >= grid_w or cy < 0 or cy >= grid_h:
                        continue
                    dist = abs(cx - memory.position[0]) + abs(cy - memory.position[1])
                    if dist < best_dist:
                        best_dist = dist
                        best_pos = candidate

        if best_pos is not None:
            return self.move_towards(best_pos)

        # Entire reachable area is already mapped — random fallback
        return MoveAction(random.choice(list(Direction)))

    def update_beliefs(self, perception: Perception) -> None:
        """
        Update the agent's memory from the latest perception, before deliberation.
        Converts agent-centric perception readings to absolute grid coordinates.
        """
        self.memory.last_perception = perception
        self.memory.position = perception.perceiver_position

        # sensor_radius: int = self.sensors['optical'].radius
        # agent_x, agent_y = perception.perceiver_position

        for abs_pos, cell_content in perception.readings:
            self.memory.belief_map[abs_pos] = cell_content
