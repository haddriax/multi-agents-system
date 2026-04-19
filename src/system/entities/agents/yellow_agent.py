from src.system.entities.agents.handlers import BASE_HANDLERS
from src.system.entities.agents.mesa_adapter import MesaAgentAdapter
from src.system.models.types import RobotType


class YellowAgent(MesaAgentAdapter):
    robot_type = RobotType.YELLOW
    HANDLERS = BASE_HANDLERS
