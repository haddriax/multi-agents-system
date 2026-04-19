from src.system.entities.agents.handlers import HANDLERS
from src.system.entities.agents.sensors import OpticalSensor, Sensor
from src.system.models.action import (
    Action,
    ActionResult,
    ActionSuccess,
    MoveAction,
)
from src.system.models.memory import Memory
from src.system.models.perception import Perception


class RobotAgent:
    def __init__(
        self,
        tier: int,
        grid_dims: tuple[int, int],
        sensors: dict[str, Sensor] | None = None,
    ) -> None:
        self.tier = tier
        self.grid_dims = grid_dims
        self.sensors: dict[str, Sensor] = sensors or {"optical": OpticalSensor()}
        self.memory: Memory = Memory(position=(0, 0))

    def update_memory(self, perception: Perception) -> None:
        """ Update the memory: what the bot perceives is now what it believes. """
        self.memory.last_perception = perception
        self.memory.position = perception.perceiver_position
        for abs_pos, cell_content in perception.readings:
            self.memory.belief_map[abs_pos] = cell_content

    def deliberate(self) -> Action:
        # Concrètement HANDLERS, ce sont les actions dans une liste par ordre de priorité
        # Si on peut effectuer l'action : on retourne l'object d'action, sinon on va voir le prochain handler
        for handler in HANDLERS:
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
