import mesa.visualization.solara_viz as _mesa_sv
from mesa.visualization import SolaraViz

from src.system.config import Config
from src.viewer.components.charts import CarryingChart, CoverageChart, WasteChart
from src.viewer.components.grid_panel import make_grid_panel


def _make_grid_layout(num_components: int) -> list[dict]:
    """Initial GridDraggable layout: first component spans full width, the rest
    share equal columns in the row below. Grid uses 12 columns."""
    if num_components <= 0:
        return []
    layout = [{"i": 0, "w": 12, "h": 16, "moved": False, "x": 0, "y": 0}]
    charts = num_components - 1
    if charts > 0:
        w = 12 // charts
        for j in range(charts):
            layout.append({"i": j + 1, "w": w, "h": 10, "moved": False,
                           "x": w * j, "y": 16})
    return layout


# Patch Mesa's hard-coded layout so the grid block starts full-width.
_mesa_sv.make_initial_grid_layout = _make_grid_layout


def create_visualization(config: Config):
    from src.system.system_model import SystemModel
    model = SystemModel(config)
    GridPanel = make_grid_panel(config)
    return SolaraViz(
        model,
        components=[GridPanel, WasteChart, CarryingChart, CoverageChart],
        model_params={},
    )
