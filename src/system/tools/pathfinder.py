from src.system.models.action import ActionType
from src.system.models.knowledge import Knowledge


class Pathfinder:
    @staticmethod
    def a_star_find_path_to(start: tuple[int, int], goal: tuple[int, int], belief_map: Knowledge) -> list[tuple[int, int]]:
        """
        Uses A* algorithm to find a path from start to goal, based on an agent So wknowledge map rather than ground truth.
        We return a list of coordinates rather than ActionType, that's the bot's job.
        """
        # @todo implement the pathfinding
        # @todo the agent will execute the list of action to get to the postion
        # @todo path should be recalculated only IF an unexpected event occurs (case blocked, waste not here) or goal changes
        print("Pathfinder::a_star_find_path_to: Not implemented yet")
        return []