from mesa import Agent
from mesa.visualization.components import AgentPortrayalStyle

from src.system.config import ViewerConfig
from src.system.entities.agents.base_agent import BaseAgent
from src.system.entities.objects.radioactivity import Radioactivity
from src.system.entities.objects.waste import Waste
from src.system.entities.objects.waste_disposal_zone import WasteDisposalZone
from src.system.models.types import WasteType

# @todo bots with goals should be highlighted
# @todo bots path should be visible maybe

_INVISIBLE = AgentPortrayalStyle(size=0, alpha=0, color="white")


def make_agent_portrayal(cell_size_pts: float, viewer_config: ViewerConfig | None = None):
    """Return an agent_portrayal function scaled to the rendered cell size.

    Args:
        cell_size_pts:  width of one grid cell in matplotlib points
                        (= fig_width_inches * 72 / grid_width).
        viewer_config:  colours to use; defaults to ViewerConfig() if not provided.
    """
    cfg = viewer_config or ViewerConfig()

    waste_colors = {
        WasteType.GREEN:  cfg.waste_color_green,
        WasteType.YELLOW: cfg.waste_color_yellow,
        WasteType.RED:    cfg.waste_color_red,
    }
    robot_colors = {
        "GREEN":  cfg.robot_color_green,
        "YELLOW": cfg.robot_color_yellow,
        "RED":    cfg.robot_color_red,
    }

    robot_size = (cell_size_pts * 0.70) ** 2
    waste_size = (cell_size_pts * 0.45) ** 2
    zone_size  = (cell_size_pts * 0.80) ** 2

    def agent_portrayal(agent: Agent) -> AgentPortrayalStyle:
        if isinstance(agent, Radioactivity):
            return _INVISIBLE

        if isinstance(agent, BaseAgent):
            color = robot_colors.get(agent.robot_type.name, "white")
            return AgentPortrayalStyle(color=color, size=robot_size, marker="o", zorder=3)

        if isinstance(agent, Waste):
            color = waste_colors.get(agent.type, "gray")
            return AgentPortrayalStyle(color=color, size=waste_size, marker="s", zorder=2)

        if isinstance(agent, WasteDisposalZone):
            return AgentPortrayalStyle(color=cfg.disposal_zone_color, size=zone_size, marker="D", zorder=4)

        return _INVISIBLE

    return agent_portrayal


# Default portrayal used when no figsize context is available.
agent_portrayal = make_agent_portrayal(cell_size_pts=30)
