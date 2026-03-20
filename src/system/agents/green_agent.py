from base_agent import BaseAgent
from mesa import Model

class GreenAgent(BaseAgent):
    def __init__(self, m: Model):
        super().__init__(m)

    def step(self) -> None:
        pass

