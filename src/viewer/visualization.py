import os

import numpy as np
from matplotlib.offsetbox import AnnotationBbox, OffsetImage
from PIL import Image

import mesa.visualization.mpl_space_drawing as _mesa_draw
import mesa.visualization.solara_viz as _mesa_sv
from mesa.visualization import SolaraViz
from mesa.visualization.mpl_space_drawing import DEFAULT_MARKER_SIZE, _get_zoom_factor

from src.system.config import Config
from src.viewer.components.charts import CarryingChart, CoverageChart, WasteChart
from src.viewer.components.grid_panel import make_grid_panel


def _scatter(ax, arguments, **kwargs):
    """Draw agents onto ax, grouping by marker type and z-order.

    Replaces Mesa's built-in _scatter, which extracts the per-agent size array
    but omits it from the ax.scatter call for standard markers.
    """
    loc    = arguments.pop("loc")
    loc_x, loc_y = loc[:, 0], loc[:, 1]
    marker = arguments.pop("marker")
    zorder = arguments.pop("zorder")
    malpha = arguments.pop("alpha")
    msize  = arguments.pop("s")

    for entry in ["edgecolors", "linewidths"]:
        if len(arguments[entry]) == 0:
            arguments.pop(entry)

    ax.get_figure().canvas.draw()
    for mark in set(marker):
        mask_marker = np.array([m == mark for m in list(marker)])
        if isinstance(mark, (str, os.PathLike)) and os.path.isfile(mark):
            for m_size in np.unique(msize):
                image = Image.open(mark)
                im = OffsetImage(image, zoom=_get_zoom_factor(ax, image) * m_size / DEFAULT_MARKER_SIZE)
                im.image.axes = ax
                mask = mask_marker & (m_size == msize)
                for z_order in np.unique(zorder[mask]):
                    for m_alpha in np.unique(malpha[mask]):
                        sub = mask & (z_order == zorder) & (m_alpha == malpha)
                        for x, y in zip(loc_x[sub], loc_y[sub]):
                            ax.add_artist(AnnotationBbox(im, (x, y), frameon=False, pad=0.0, zorder=z_order))
        else:
            for z_order in np.unique(zorder[mask_marker]):
                zorder_mask = (z_order == zorder) & mask_marker
                ax.scatter(
                    loc_x[zorder_mask],
                    loc_y[zorder_mask],
                    s=msize[zorder_mask],
                    marker=mark,
                    zorder=z_order,
                    **{k: v[zorder_mask] for k, v in arguments.items()},
                    **kwargs,
                )


_mesa_draw._scatter = _scatter


def _grid_layout(num_components: int) -> list[dict]:
    """GridDraggable initial layout: first block spans full width, remaining
    blocks share equal columns in the row below. Grid uses 12 columns."""
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


_mesa_sv.make_initial_grid_layout = _grid_layout


def create_visualization(config: Config):
    from src.system.system_model import SystemModel
    model = SystemModel(config)
    GridPanel = make_grid_panel(config)
    return SolaraViz(
        model,
        components=[GridPanel, WasteChart, CarryingChart, CoverageChart],
        model_params={},
    )
