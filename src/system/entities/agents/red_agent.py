from src.system.entities.agents.base_agent import BaseAgent
from src.system.models.types import RobotType
from mesa import Model


class RedAgent(BaseAgent):
    robot_type = RobotType.RED

    def __init__(self, m: Model):
        super().__init__(m)

