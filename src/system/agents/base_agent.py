from abc import ABC, abstractmethod
from mesa import Agent, Model

from src.system.models.action import ActionType
from src.system.models.knowledge import Knowledge
from src.system.models.perception import Perception


class BaseAgent(Agent, ABC):
    def __init__(self, m: Model):
        super().__init__(m)
        self.knowledge: Knowledge = Knowledge(position=(0, 0))

    @abstractmethod
    def step(self) -> None:
        """ Mesa step method """

        action: ActionType = self.deliberate(self.knowledge)
        perception_post_action: Perception = self.model.do(self, action)
        self.update_beliefs(action, perception_post_action)

        raise NotImplementedError()

    @abstractmethod
    def deliberate(self, knowledge: Knowledge) -> ActionType:
        raise NotImplementedError()

    @abstractmethod
    def update_beliefs(self, action: ActionType, perception: Perception) -> None:
        self.knowledge.last_perception = perception
        self.knowledge.last_action = action

        # ... from perception to knowledge

        raise NotImplementedError()