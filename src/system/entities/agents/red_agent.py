from src.system.entities.agents.handlers import BASE_HANDLERS
from src.system.entities.agents.mesa_adapter import MesaAgentAdapter
from src.system.models.types import RobotType


class RedAgent(MesaAgentAdapter):
    robot_type = RobotType.RED
    HANDLERS = BASE_HANDLERS
