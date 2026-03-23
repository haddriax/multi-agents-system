import os
import yaml
import solara
from mesa.visualization import SolaraViz, make_space_component
from mesa.visualization.components import AgentPortrayalStyle
from src.system.system_model import SystemModel
from src.system.entities.agents.green_agent import GreenAgent
from src.system.entities.agents.yellow_agent import YellowAgent
from src.system.entities.agents.red_agent import RedAgent
from src.system.entities.objects.radioactivity import Radioactivity
from src.system.entities.objects.waste import Waste
from src.system.entities.objects.waste_disposal_zone import WasteDisposalZone
from src.system.models.types import WasteType

_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "config.yaml")

def _load_config() -> dict:
    with open(_CONFIG_PATH, "r") as f:
        return yaml.safe_load(f)

_INVISIBLE = AgentPortrayalStyle(size=0, alpha=0, color="white")

def agent_portrayal(agent):
    if isinstance(agent, Radioactivity):
        return _INVISIBLE                                              # skip 1600 background agents

    if isinstance(agent, GreenAgent):
        return AgentPortrayalStyle(color="limegreen", size=150, marker="o", zorder=4)
    if isinstance(agent, YellowAgent):
        return AgentPortrayalStyle(color="gold", size=150, marker="o", zorder=4)
    if isinstance(agent, RedAgent):
        return AgentPortrayalStyle(color="tomato", size=150, marker="o", zorder=4)

    if isinstance(agent, Waste):
        colors = {
            WasteType.GREEN:  "#00aa00",
            WasteType.YELLOW: "#ccaa00",
            WasteType.RED:    "#cc2200",
        }
        return AgentPortrayalStyle(
            color=colors.get(agent.type, "gray"),
            size=60, marker="s", zorder=2
        )

    if isinstance(agent, WasteDisposalZone):
        return AgentPortrayalStyle(color="purple", size=250, marker="D", zorder=5)

    return AgentPortrayalStyle()

def make_post_process(width, height):
    z1_x = width // 3        # e.g. 26 for width=80
    z2_x = 2 * width // 3   # e.g. 53 for width=80

    def post_process(ax):
        import matplotlib.patches as mpatches
        # Colored zone backgrounds
        for x0, w, color in [
            (-0.5,        z1_x,          "lightgreen"),
            (z1_x - 0.5, z2_x - z1_x,   "lightyellow"),
            (z2_x - 0.5, width - z2_x,   "lightcoral"),
        ]:
            ax.add_patch(mpatches.Rectangle(
                (x0, -0.5), w, height,
                facecolor=color, alpha=0.25, zorder=0, linewidth=0
            ))
        # Zone boundary dashed lines
        for x in [z1_x - 0.5, z2_x - 0.5]:
            ax.axvline(x, color="gray", linestyle="--", alpha=0.5, linewidth=1)

    return post_process

_config = _load_config()
model = SystemModel(_config)

space_component = make_space_component(
    agent_portrayal=agent_portrayal,
    post_process=make_post_process(_config["grid"]["width"], _config["grid"]["height"]),
)

page = SolaraViz(
    model,
    components=[space_component],
    model_params={"config": _config},
    name="Radioactive Waste Cleanup",
)