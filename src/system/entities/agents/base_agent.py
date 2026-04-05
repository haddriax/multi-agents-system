from abc import ABC

from mesa import Agent, Model

from src.system.models.action import Action, ActionResult, ActionSuccess, MoveAction, WaitAction
from src.system.models.knowledge import Knowledge
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
    def __init__(self, radius: int = 2) -> None:
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
        self.knowledge: Knowledge = Knowledge(position=(0, 0))
        self.carry_capacity = 1
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

    def get_knowledge(self) -> Knowledge:
        """ Return the knowledge object: the beliefs about the environnement."""
        return self.knowledge

    def step(self) -> None:
        """ Mesa step method: Perceive, Update Beliefs, Deliberate, Act """
        perception: Perception = self.model.perceive(self)
        self.update_beliefs(perception)
        action: Action = self.deliberate(self.knowledge)
        result: ActionResult = self.model.do(self, action)
        self.knowledge.last_action = action
        # Advance the planned path only after a successful move so that a cell
        # that became occupied between planning and execution is retried next turn.
        if isinstance(action, MoveAction) and isinstance(result, ActionSuccess):
            if self.knowledge.planned_path:
                self.knowledge.planned_path.pop(0)

    def deliberate(self, knowledge: Knowledge) -> Action:
        """
        Path-following deliberation:
        1. Validate current goal (waste may have disappeared)
        2. Find a new goal if needed and compute A* path
        3. Follow the path — wait if the next cell is blocked by a bot
        4. Explore randomly if no known waste
        """
        # 1. Validate current goal
        if knowledge.current_goal is not None:
            cell = knowledge.belief_map.get(knowledge.current_goal)
            if cell is None or cell.waste_type.value != self.robot_type.value:
                knowledge.current_goal = None
                knowledge.planned_path = []

        # 2. Find new goal and compute path
        if knowledge.current_goal is None:
            goal = self._find_possible_closest_waste(knowledge)
            if goal:
                knowledge.current_goal = goal
                knowledge.planned_path = Pathfinder.a_star_find_path_to(
                    knowledge.position, goal, knowledge,
                    self.model.grid.width, self.model.grid.height,
                )

        # 3. Follow the path
        if knowledge.planned_path:
            next_pos = knowledge.planned_path[0]
            cell = knowledge.belief_map.get(next_pos)
            if cell is not None and cell.robot_type != RobotType.NONE:
                return WaitAction()  # blocked by a bot — retry next turn
            # pop(0) happens in step() after ActionSuccess, not here
            return self.move_towards(next_pos)

        # 4. Bot is on goal
        if knowledge.current_goal == self.pos:
            return WaitAction()

        # 5. No known waste — navigate toward the nearest unseen frontier cell
        return self._explore(knowledge)

    def move_towards(self, target_pos: tuple[int, int]) -> MoveAction:
        """
        Compute the action needed to move towards the target position based on the agent's current position.
        """
        agent_x, agent_y = self.knowledge.position
        target_x, target_y = target_pos

        if target_x > agent_x and target_y > agent_y:
            return MoveAction(Direction.UP_RIGHT)
        elif target_x > agent_x and target_y < agent_y:
            return MoveAction(Direction.DOWN_RIGHT)
        elif target_x < agent_x and target_y > agent_y:
            return MoveAction(Direction.UP_LEFT)
        elif target_x < agent_x and target_y < agent_y:
            return MoveAction(Direction.DOWN_LEFT)
        elif target_x > agent_x:
            return MoveAction(Direction.RIGHT)
        elif target_x < agent_x:
            return MoveAction(Direction.LEFT)
        elif target_y > agent_y:
            return MoveAction(Direction.UP)
        elif target_y < agent_y:
            return MoveAction(Direction.DOWN)

        return WaitAction()

    def _find_possible_closest_waste(self, knowledge: Knowledge) -> tuple[int, int] | None:
        """ Look in memory to find the closest waste. """
        best_pos = None
        best_dist = float('inf')

        for pos, cell in knowledge.belief_map.items():
            if cell.waste_type.value == self.robot_type.value:
                dist = abs(pos[0] - knowledge.position[0]) + abs(pos[1] - knowledge.position[1])
                if dist < best_dist:
                    best_dist = dist
                    best_pos = pos

        return best_pos

    def _explore(self, knowledge: Knowledge) -> Action:
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
        known = knowledge.belief_map

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
                    dist = abs(cx - knowledge.position[0]) + abs(cy - knowledge.position[1])
                    if dist < best_dist:
                        best_dist = dist
                        best_pos = candidate

        if best_pos is not None:
            return self.move_towards(best_pos)

        # Entire reachable area is already mapped — random fallback
        return MoveAction(random.choice(list(Direction)))

    def update_beliefs(self, perception: Perception) -> None:
        """
        Update the agent's knowledge from the latest perception, before deliberation.
        Converts agent-centric perception readings to absolute grid coordinates.
        """
        self.knowledge.last_perception = perception
        self.knowledge.position = perception.perceiver_position

        sensor_radius: int = self.sensors['optical'].radius
        agent_x, agent_y = perception.perceiver_position

        # Loop order must match Mesa's get_neighborhood (dy-outer, dx-inner) so that
        # each reading index maps to the correct absolute cell.  Out-of-bounds offsets
        # are skipped — Mesa omits those cells, so they have no corresponding reading.
        idx = 0
        for dy in range(-sensor_radius, sensor_radius + 1):
            for dx in range(-sensor_radius, sensor_radius + 1):
                abs_pos = (agent_x + dx, agent_y + dy)
                if self.model.grid.out_of_bounds(abs_pos):
                    continue
                if idx < len(perception.readings):
                    self.knowledge.belief_map[abs_pos] = perception.readings[idx]
                    idx += 1
