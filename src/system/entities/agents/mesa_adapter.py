from abc import ABC

from mesa import Agent, Model

from src.system.entities.agents.handlers import Handler
from src.system.entities.agents.robot_agent import RobotAgent
from src.system.entities.agents.sensors import Sensor
from src.system.models.memory import Memory
from src.system.models.types import RobotType


class MesaAgentAdapter(Agent, ABC):
    robot_type: RobotType = RobotType.NONE
    HANDLERS: list[Handler] = []

    def __init__(self, model: Model) -> None:
        super().__init__(model)
        self.robot = RobotAgent(
            tier=self._resolve_tier(),
            grid_dims=(model.grid.width, model.grid.height),
            handlers=type(self).HANDLERS,
        )

    def step(self) -> None:
        perception = self.model.perceive(self)
        self.robot.update_memory(perception)
        action = self.robot.deliberate()
        result = self.model.do(self, action)
        self.robot.on_action_result(action, result)

    def force_percept_update(self) -> None:
        """Force a belief update without going through step(). Used at spawn time."""
        self.robot.update_memory(self.model.perceive(self))

    @property
    def memory(self) -> Memory:
        return self.robot.memory

    @property
    def tier(self) -> int:
        return self.robot.tier

    @property
    def sensors(self) -> dict[str, Sensor]:
        return self.robot.sensors

    def _resolve_tier(self) -> int:
        match self.robot_type:
            case RobotType.GREEN:  return 1
            case RobotType.YELLOW: return 2
            case RobotType.RED:    return 3
            case _:
                raise ValueError(f"robot_type not set on {type(self).__name__}")
