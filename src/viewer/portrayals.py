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


def make_agent_portrayal(cell_size_pts: float):
    """Return an agent_portrayal function scaled to the rendered cell size.

    Args:
        cell_size_pts: width of one grid cell in matplotlib points
                       (= fig_width_inches * 72 / grid_width).
    """
    robot_size = (cell_size_pts * 0.70) ** 2
    waste_size = (cell_size_pts * 0.45) ** 2
    zone_size  = (cell_size_pts * 0.80) ** 2

    def agent_portrayal(agent: Agent) -> AgentPortrayalStyle:
        if isinstance(agent, Radioactivity):
            return _INVISIBLE

        if isinstance(agent, BaseAgent):
            color = _ROBOT_COLORS.get(agent.robot_type.name, "white")
            return AgentPortrayalStyle(color=color, size=robot_size, marker="o", zorder=3)

        if isinstance(agent, Waste):
            color = _WASTE_COLORS.get(agent.type, "gray")
            return AgentPortrayalStyle(color=color, size=waste_size, marker="s", zorder=2)

        if isinstance(agent, WasteDisposalZone):
            return AgentPortrayalStyle(color="purple", size=zone_size, marker="D", zorder=4)

        return _INVISIBLE

    return agent_portrayal


# Default portrayal used when no figsize context is available.
agent_portrayal = make_agent_portrayal(cell_size_pts=30)
