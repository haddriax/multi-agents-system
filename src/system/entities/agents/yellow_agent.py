from src.system.entities.agents.base_agent import BaseAgent
from src.system.models.action import ActionType
from src.system.models.knowledge import Knowledge
from src.system.models.types import RobotType
from mesa import Model


class YellowAgent(BaseAgent):
    robot_type = RobotType.YELLOW

    def __init__(self, m: Model):
        super().__init__(m)

    def deliberate(self, knowledge: Knowledge) -> ActionType:
        """
        Decision logic for YellowAgent.
        # @todo: Implement actual decision-making logic.
        """
        return ActionType.WAIT

