# Group: 9
# Date: 25-03-2026
# Members: Maëlys Hanoire, Raphaël Vignal, Gaël Garnier

import matplotlib.patches as mpatches
import solara
from matplotlib.figure import Figure
from mesa.visualization.mpl_space_drawing import draw_space
from mesa.visualization.utils import update_counter

from Raphael_Maelys_Gael_robot_mission_MAS2026.system.config import Config
from Raphael_Maelys_Gael_robot_mission_MAS2026.viewer.portrayals import make_agent_portrayal


def _make_post_process(config: Config):
    width, height = config.grid.width, config.grid.height
    z1_x, z2_x = width // 3, 2 * width // 3
    v = config.viewer
    zones = [
        (-0.5,        z1_x,        v.zone_color_z1),
        (z1_x - 0.5, z2_x - z1_x, v.zone_color_z2),
        (z2_x - 0.5, width - z2_x, v.zone_color_z3),
    ]
    boundaries = [z1_x - 0.5, z2_x - 0.5]

    def post_process(ax):
        # Remove the equal-aspect lock set by draw_space so the axes fill the
        # full figsize. Cells stay square because figsize matches the grid ratio.
        ax.set_aspect('auto')
        for x0, w, color in zones:
            ax.add_patch(mpatches.Rectangle(
                (x0, -0.5), w, height,
                facecolor=color, alpha=0.25, zorder=0, linewidth=0,
            ))
        for x in boundaries:
            ax.axvline(x, color="gray", linestyle="--", alpha=0.6, linewidth=1.0, zorder=1)

    return post_process


def make_grid_panel(config: Config):
    """Return a GridPanel Solara component sized to the grid dimensions."""
    post_process = _make_post_process(config)
    # Match figsize aspect ratio to grid so cells stay square with aspect='auto'.
    # fig_w / fig_h == grid_w / grid_h  =>  cell_w == cell_h always.
    fig_w = max(config.grid.width / 1.5, 20)
    fig_h = fig_w * (config.grid.height / config.grid.width)

    @solara.component
    def GridPanel(model):
        update_counter.get()
        space = getattr(model, "grid", None) or getattr(model, "space", None)
        fig = Figure(figsize=(fig_w, fig_h))
        ax = fig.add_subplot()
        # Set axes limits first so the transform is live, then read exactly
        # how many display pixels one grid cell spans and convert to points.
        # This accounts for subplot margins so marker sizes are always accurate.
        ax.set_xlim(-0.5, space.width - 0.5)
        ax.set_ylim(-0.5, space.height - 0.5)
        x0_px, _ = ax.transData.transform((0, 0))
        x1_px, _ = ax.transData.transform((1, 0))
        cell_pts = abs(x1_px - x0_px) * 72 / fig.dpi
        draw_space(space, make_agent_portrayal(cell_pts, viewer_config=config.viewer), ax=ax)
        post_process(ax)
        solara.FigureMatplotlib(fig, format="png", bbox_inches="tight")

    return GridPanel
