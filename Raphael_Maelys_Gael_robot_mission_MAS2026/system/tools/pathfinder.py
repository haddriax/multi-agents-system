# Group: 9
# Date: 25-03-2026
# Members: Maëlys Hanoire, Raphaël Vignal, Gaël Garnier

import heapq

from Raphael_Maelys_Gael_robot_mission_MAS2026.system.models.memory import Memory
from Raphael_Maelys_Gael_robot_mission_MAS2026.system.models.types import RobotType


class Pathfinder:
    @staticmethod
    def a_star_find_path_to(
        start: tuple[int, int],
        goal: tuple[int, int],
        memory: Memory,
        grid_width: int,
        grid_height: int,
    ) -> list[tuple[int, int]]:
        """
        A* pathfinding over the agent's belief map rather than ground truth.
        Unknown cells are treated as passable (optimistic exploration).
        Cells known to contain another bot are treated as blocked.
        We could say that bots don't know the grid size beforehand, but it's acceptable that way.

        Returns a list of positions from start (exclusive) to goal (inclusive).
        Returns an empty list if no path exists.
        """
        if start == goal:
            return []

        # That's the cost of moving in that direction. Note that we use approx sqrt(2) for diagonals to account for distance
        # (dx, dy, cost)
        directions = [
            (0,  1, 1.0),  (0, -1, 1.0),  (1, 0, 1.0),  (-1, 0, 1.0),
            (1,  1, 1.414), (1, -1, 1.414), (-1, 1, 1.414), (-1, -1, 1.414),
        ]

        def is_passable(pos: tuple[int, int]) -> bool:
            x, y = pos
            if not (0 <= x < grid_width and 0 <= y < grid_height):
                return False
            if pos == goal:
                return True  # goal may have waste on it: always reachable
            cell = memory.belief_map.get(pos)
            if cell is None:
                return True  # unseen cell: always assume passable
            return cell.robot_type == RobotType.NONE

        open_set: list[tuple[float, tuple[int, int]]] = [(0.0, start)]
        came_from: dict[tuple[int, int], tuple[int, int]] = {}
        g_score: dict[tuple[int, int], float] = {start: 0.0}

        while open_set:
            _, current = heapq.heappop(open_set)

            if current == goal:
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                path.reverse()
                return path

            for dx, dy, cost in directions:
                neighbor = (current[0] + dx, current[1] + dy)
                if not is_passable(neighbor):
                    continue
                tentative_g = g_score[current] + cost
                if tentative_g < g_score.get(neighbor, float('inf')):
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    h = abs(neighbor[0] - goal[0]) + abs(neighbor[1] - goal[1])
                    heapq.heappush(open_set, (tentative_g + h, neighbor))

        return []  # no path found