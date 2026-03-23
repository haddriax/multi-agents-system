from abc import ABC, abstractmethod

from mesa import Agent, Model

from src.system.models.action import ActionType
from src.system.models.knowledge import Knowledge
from src.system.models.perception import Perception
from src.system.models.types import RobotType

import random


class Sensor:
    """
    Represent a way to perceive the environnement.
    For now, we only have an optical sensor, but we could add more like radiation sensor,
    so this class force the design to work with n named sensors.
    """
    def __init__(self, radius: int = 2) -> None:
        self.radius = radius

class OpticalSensor(Sensor):
    """
    The most basic and principal sensor.
    """
    def __init__(self, radius: int = 2) -> None:
        super().__init__(radius)


class BaseAgent(Agent, ABC):
    robot_type = RobotType.NONE

    def __init__(self, m: Model):
        super().__init__(m)
        self.knowledge: Knowledge = Knowledge(position=(0, 0))
        self.sensors: dict[str, Sensor] = {
            "optical": OpticalSensor()
        }

    def step(self) -> None:
        """ Mesa step method: Perceive, Deliberate, Do, Update knowledge (beliefs) """
        perception: Perception = self.model.perceive(self)
        action: ActionType = self.deliberate(self.knowledge)
        self.model.do(self, action)
        self.update_beliefs(action, perception)


    @abstractmethod
    def deliberate(self, knowledge: Knowledge) -> ActionType:
        """
        Prend une décision basée sur la situation actuelle.
        Inclu des décisions de déplacement, de prise ou de dépôt d'objets.
        """
        action = self.decide_movement()
        if action:
            return action

        return ActionType.WAIT

    def decide_movement(self) -> ActionType:
        """
        Décide du mouvement de l'agent.
        """
        directions = [
            ActionType.MOVE_UP,
            ActionType.MOVE_DOWN,
            ActionType.MOVE_LEFT,
            ActionType.MOVE_RIGHT,
            ActionType.MOVE_UP_LEFT,
            ActionType.MOVE_UP_RIGHT,
            ActionType.MOVE_DOWN_LEFT,
            ActionType.MOVE_DOWN_RIGHT
        ]
        return random.choice(directions)


    def update_beliefs(self, action: ActionType, perception: Perception) -> None:
        """
        Update the agent's knowledge based on perception and action.
        Converts agent-centric perception to absolute grid coordinates.
        """
        # Store the transient knowledge first
        self.knowledge.last_perception = perception
        self.knowledge.last_action = action

        sensor_radius: int = self.sensors['optical'].radius

        agent_x: int
        agent_y: int
        agent_x, agent_y = perception.perceiver_position

        # Iterate through perception readings and map to absolute coordinates
        idx = 0
        for dx in range(-sensor_radius, sensor_radius + 1):
            for dy in range(-sensor_radius, sensor_radius + 1):
                if idx < len(perception.readings):
                    absolute_pos = (agent_x + dx, agent_y + dy)
                    cell_content = perception.readings[idx]
                    self.knowledge.belief_map[absolute_pos] = cell_content
                    idx += 1

        # We get the position fro the perception there, which means it's good if the move can fail
        # But we have to @todo update the perception or let knowledge know we moved!
        self.knowledge.position = perception.perceiver_position