from src.system.entities.agents.handlers import Handler
from src.system.entities.agents.sensors import OpticalSensor, Sensor
from src.system.models.action import (
    Action,
    ActionResult,
    ActionSuccess,
    MoveAction,
)
from src.system.models.memory import Memory
from src.system.models.message import WasteDiscoveredMessage, WasteCancelledMessage
from src.system.models.perception import CellContent, Perception
from src.system.models.types import RobotType


class RobotAgent:
    def __init__(
        self,
        tier: int,
        grid_dims: tuple[int, int],
        handlers: list[Handler],
        max_x: int | None = None,
        sensors: dict[str, Sensor] | None = None,
    ) -> None:
        self.tier = tier
        self.grid_dims = grid_dims
        self.handlers = handlers
        self.sensors: dict[str, Sensor] = sensors or {"optical": OpticalSensor()}
        self.memory: Memory = Memory(position=(0, 0), max_x=max_x)

    def update_memory(self, perception: Perception) -> None:
        """ Update the memory: what the bot perceives is now what it believes. """
        self.memory.last_perception = perception
        self.memory.position = perception.perceiver_position
        for abs_pos, cell_content in perception.readings:
            self.memory.belief_map[abs_pos] = cell_content
        self._process_mailbox(perception)

    def _process_mailbox(self, perception: Perception) -> None:
        """Apply mailbox messages to the belief_map and current navigation state."""
        perceived = {pos for pos, _ in perception.readings}
        for msg in self.memory.mailbox:
            if isinstance(msg, WasteDiscoveredMessage):
                if msg.position not in perceived:
                    self.memory.belief_map[msg.position] = CellContent(
                        radioactivity_value=0.0,
                        waste_type=msg.waste_type,
                        waste_quantity=1,
                        robot_type=RobotType.NONE,
                        has_disposal_zone=False,
                    )
            elif isinstance(msg, WasteCancelledMessage):
                self.memory.belief_map.pop(msg.position, None)
                if self.memory.target_cell == msg.position:
                    self.memory.target_cell = None
                    self.memory.planned_path = []
        self.memory.mailbox.clear()

    def deliberate(self) -> Action:
        for handler in self.handlers:
            action = handler(self.memory, self.tier, self.grid_dims)
            if action is not None:
                return action
        raise RuntimeError("no action produced")

    def on_action_result(self, action: Action, result: ActionResult) -> None:
        """ Callback when the result of the action is received """
        # On met à jour la dernière action pour l'avoir en mémoire le tour suivant
        self.memory.last_action = action

        # On attend d'avoir la certitude que le mouvement a réussi pour mettre à jour le chemin prévu
        if isinstance(action, MoveAction) and isinstance(result, ActionSuccess):
            if self.memory.planned_path:
                self.memory.planned_path.pop(0)
