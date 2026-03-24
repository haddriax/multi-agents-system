from src.system.entities.agents.base_agent import BaseAgent
from src.system.models.types import RobotType
from mesa import Model


class YellowAgent(BaseAgent):
    robot_type = RobotType.YELLOW

    def __init__(self, m: Model):
        super().__init__(m)

