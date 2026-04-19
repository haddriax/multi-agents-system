from mesa import Agent, Model

class BaseObject(Agent):
    def __init__(self, m: Model):
        super().__init__(m)