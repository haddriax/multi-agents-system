# Group: 9
# Date: 20-03-2026
# Members: Maëlys Hanoire, Raphaël Vignal, Gaël Garnier

from mesa import Agent, Model

class BaseObject(Agent):
    def __init__(self, m: Model):
        super().__init__(m)