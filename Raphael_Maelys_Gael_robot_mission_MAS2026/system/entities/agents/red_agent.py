# Group: 9
# Date: 20-03-2026
# Members: Maëlys Hanoire, Raphaël Vignal, Gaël Garnier

from Raphael_Maelys_Gael_robot_mission_MAS2026.system.entities.agents.handlers import RED_HANDLERS
from Raphael_Maelys_Gael_robot_mission_MAS2026.system.entities.agents.mesa_adapter import MesaAgentAdapter
from Raphael_Maelys_Gael_robot_mission_MAS2026.system.models.types import RobotType


class RedAgent(MesaAgentAdapter):
    robot_type = RobotType.RED
    HANDLERS = RED_HANDLERS
    MAX_ZONE = None
