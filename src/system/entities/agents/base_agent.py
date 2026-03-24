from abc import ABC

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
        """ Mesa step method: Perceive, Update Beliefs, Deliberate, Act """
        perception: Perception = self.model.perceive(self)
        self.update_beliefs(perception)
        action: ActionType = self.deliberate(self.knowledge)
        self.model.do(self, action)
        self.knowledge.last_action = action


    def deliberate(self, knowledge: Knowledge) -> ActionType:
        """
        Take a decision based on the current situation.
        """
        # Verify if there is a waste of the agent's type in the immediate perception
        target_pos = None
        for pos, cell_content in knowledge.belief_map.items():
            if cell_content.waste_type == self.robot_type:
                target_pos = pos
                break

        # If no waste if found in the immediate perception, check the belief map for known waste locations
        if not target_pos:
            for pos, cell_content in knowledge.belief_map.items():
                if cell_content.waste_type == self.robot_type:
                    target_pos = pos
                    break

        # If a target position is found, move towards it; otherwise, decide a random movement to explore
        if target_pos:
            return self.move_towards(target_pos)

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

    def move_towards(self, target_pos: tuple[int, int]) -> ActionType:
        """
        Compute the action needed to move towards the target position based on the agent's current position.
        """
        agent_x, agent_y = self.knowledge.position
        target_x, target_y = target_pos

        if target_x > agent_x and target_y > agent_y:
            return ActionType.MOVE_UP_RIGHT
        elif target_x > agent_x and target_y < agent_y:
            return ActionType.MOVE_DOWN_RIGHT
        elif target_x < agent_x and target_y > agent_y:
            return ActionType.MOVE_UP_LEFT
        elif target_x < agent_x and target_y < agent_y:
            return ActionType.MOVE_DOWN_LEFT
        elif target_x > agent_x:
            return ActionType.MOVE_RIGHT
        elif target_x < agent_x:
            return ActionType.MOVE_LEFT
        elif target_y > agent_y:
            return ActionType.MOVE_UP
        elif target_y < agent_y:
            return ActionType.MOVE_DOWN

        return ActionType.WAIT

    def update_beliefs(self, perception: Perception) -> None:
        """
        Update the agent's knowledge from the latest perception, before deliberation.
        Converts agent-centric perception readings to absolute grid coordinates.
        """
        self.knowledge.last_perception = perception
        self.knowledge.position = perception.perceiver_position

        sensor_radius: int = self.sensors['optical'].radius
        agent_x, agent_y = perception.perceiver_position

        idx = 0
        for dx in range(-sensor_radius, sensor_radius + 1):
            for dy in range(-sensor_radius, sensor_radius + 1):
                if idx < len(perception.readings):
                    self.knowledge.belief_map[(agent_x + dx, agent_y + dy)] = perception.readings[idx]
                    idx += 1