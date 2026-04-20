# Group: 9
# Date: 19-04-2026
# Members: Maëlys Hanoire, Raphaël Vignal, Gaël Garnier

from src.system.entities.agents.handlers import Handler
from src.system.entities.agents.sensors import OpticalSensor, Sensor
from src.system.models.action import (
    Action,
    ActionResult,
    ActionFailure,
    ActionSuccess,
    MoveAction,
    PickAction,
    ReserveAction,
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
            is_new = abs_pos not in self.memory.belief_map
            self.memory.belief_map[abs_pos] = cell_content
            # Opportunistic discovery: announce newly seen own-tier waste that isn't our target
            if (is_new
                    and cell_content.waste_type.value == self.tier
                    and cell_content.waste_type.value != 0
                    and abs_pos != self.memory.target_cell):
                self.memory.outbox.append((cell_content.waste_type, abs_pos))
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
                if (self.memory.target_cell == msg.position
                        or self.memory.active_reservation == msg.position):
                    self.memory.target_cell = None
                    self.memory.planned_path = []
                    self.memory.active_reservation = None
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

        elif isinstance(action, ReserveAction):
            if isinstance(result, ActionSuccess):
                self.memory.active_reservation = action.position
            else:
                # Conflict: forget this target so seek picks another one
                self.memory.belief_map.pop(action.position, None)

        elif isinstance(action, PickAction) and isinstance(result, ActionFailure):
            # Waste gone OR reservation was displaced — reset navigation state
            self.memory.active_reservation = None
            self.memory.target_cell = None
            self.memory.planned_path = []
