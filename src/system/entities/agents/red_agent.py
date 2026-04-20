# Group: 9
# Date: 20-03-2026
# Members: Maëlys Hanoire, Raphaël Vignal, Gaël Garnier

from src.system.entities.agents.handlers import RED_HANDLERS
from src.system.entities.agents.mesa_adapter import MesaAgentAdapter
from src.system.models.types import RobotType


class RedAgent(MesaAgentAdapter):
    robot_type = RobotType.RED
    HANDLERS = RED_HANDLERS
    MAX_ZONE = None
