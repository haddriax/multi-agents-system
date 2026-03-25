from mesa import Agent
from mesa.visualization.components import AgentPortrayalStyle

from src.system.entities.agents.base_agent import BaseAgent
from src.system.entities.objects.radioactivity import Radioactivity
from src.system.entities.objects.waste import Waste
from src.system.entities.objects.waste_disposal_zone import WasteDisposalZone
from src.system.models.types import WasteType

# @todo bots with goals should be highlighted
# @todo bots bath should be visible maybe

_INVISIBLE = AgentPortrayalStyle(size=0, alpha=0, color="white")

_WASTE_COLORS = {
    WasteType.GREEN:  "#00aa00",
    WasteType.YELLOW: "#ccaa00",
    WasteType.RED:    "#cc2200",
}

_ROBOT_COLORS = {
    "GREEN":  "limegreen",
    "YELLOW": "gold",
    "RED":    "tomato",
}


def agent_portrayal(agent: Agent) -> AgentPortrayalStyle:
    if isinstance(agent, Radioactivity):
        return _INVISIBLE

    if isinstance(agent, BaseAgent):
        color = _ROBOT_COLORS.get(agent.robot_type.name, "white")
        return AgentPortrayalStyle(color=color, size=150, marker="o", zorder=3)

    if isinstance(agent, Waste):
        color = _WASTE_COLORS.get(agent.type, "gray")
        return AgentPortrayalStyle(color=color, size=80, marker="s", zorder=2)

    if isinstance(agent, WasteDisposalZone):
        return AgentPortrayalStyle(color="purple", size=250, marker="D", zorder=4)

    return _INVISIBLE
