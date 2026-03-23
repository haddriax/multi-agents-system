from src.system.entities.agents.base_agent import BaseAgent
from src.system.models.action import ActionType
from src.system.models.knowledge import Knowledge
from src.system.models.types import RobotType
from mesa import Model


class GreenAgent(BaseAgent):
    robot_type = RobotType.GREEN

    def __init__(self, m: Model):
        super().__init__(m)

    def deliberate(self, knowledge: Knowledge) -> ActionType:
        """
        Decision logic for GreenAgent.
        # @todo: Implement actual decision-making logic.
        """
        return ActionType.WAIT

