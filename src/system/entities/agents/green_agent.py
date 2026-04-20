# Group: 9
# Date: 20-03-2026
# Members: Maëlys Hanoire, Raphaël Vignal, Gaël Garnier

from src.system.entities.agents.handlers import BASE_HANDLERS
from src.system.entities.agents.mesa_adapter import MesaAgentAdapter
from src.system.models.types import RobotType


class GreenAgent(MesaAgentAdapter):
    robot_type = RobotType.GREEN
    HANDLERS = BASE_HANDLERS
    MAX_ZONE = 1
