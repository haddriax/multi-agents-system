import asyncio

import matplotlib.patches as mpatches
import numpy as np
import pandas as pd
import solara
import solara.lab
from matplotlib.figure import Figure

from src.system.config import Config
from src.system.entities.agents.base_agent import BaseAgent
from src.system.entities.objects.waste import Waste
from src.system.entities.objects.waste_disposal_zone import WasteDisposalZone
from src.system.models.types import WasteType
from src.system.system_model import SystemModel

# ---------------------------------------------------------------------------
# Grid drawing — pure matplotlib, no Mesa visualization dependencies
# ---------------------------------------------------------------------------

def draw_grid(model: SystemModel, config: Config, show_belief_map: bool) -> Figure:
    width  = config.grid.width
    height = config.grid.height
    z1_x   = width // 3
    z2_x   = 2 * width // 3

    fig_w = max(width / 3.5, 10)
    fig_h = max(height / 3.5, 3)
    fig = Figure(figsize=(fig_w, fig_h))
    ax  = fig.add_subplot(111)

    v = config.viewer

    # Zone backgrounds
    for x0, w, color in [
        (-0.5,        z1_x,          v.zone_color_z1),
        (z1_x - 0.5, z2_x - z1_x,   v.zone_color_z2),
        (z2_x - 0.5, width - z2_x,   v.zone_color_z3),
    ]:
        ax.add_patch(mpatches.Rectangle(
            (x0, -0.5), w, height,
            facecolor=color, alpha=0.25, zorder=0, linewidth=0,
        ))

    # Cell grid lines
    ax.set_xticks([x - 0.5 for x in range(width + 1)], minor=False)
    ax.set_yticks([y - 0.5 for y in range(height + 1)], minor=False)
    ax.grid(True, which="major", color="gray", linewidth=0.3, alpha=0.4, zorder=1)
    ax.tick_params(which="major", length=0, labelbottom=False, labelleft=False)

    # Zone boundary lines (on top of cell grid)
    for x in [z1_x - 0.5, z2_x - 0.5]:
        ax.axvline(x, color="gray", linestyle="--", alpha=0.6, linewidth=1.0, zorder=1)

    # Belief map overlay — single imshow instead of one patch per cell
    if show_belief_map:
        mask = np.zeros((height, width), dtype=np.float32)
        for agent in model.agents:
            if isinstance(agent, BaseAgent):
                for (cx, cy) in agent.knowledge.belief_map.keys():
                    if 0 <= cx < width and 0 <= cy < height:
                        mask[cy, cx] = 1.0
        ax.imshow(
            mask,
            origin="lower",
            aspect="auto",
            extent=[-0.5, width - 0.5, -0.5, height - 0.5],
            cmap="Blues",
            alpha=0.28,
            vmin=0, vmax=1,
            zorder=2,
            interpolation="none",
        )

    waste_colors = {
        WasteType.GREEN:  v.waste_color_green,
        WasteType.YELLOW: v.waste_color_yellow,
        WasteType.RED:    v.waste_color_red,
    }
    robot_colors = {
        "GREEN":  v.robot_color_green,
        "YELLOW": v.robot_color_yellow,
        "RED":    v.robot_color_red,
    }

    # Collect positions per layer to scatter all at once (vectorised)
    waste_xs: dict[WasteType, list[float]] = {t: [] for t in WasteType if t != WasteType.NONE}
    waste_ys: dict[WasteType, list[float]] = {t: [] for t in WasteType if t != WasteType.NONE}
    robot_xs: dict[str, list[float]] = {k: [] for k in robot_colors}
    robot_ys: dict[str, list[float]] = {k: [] for k in robot_colors}
    robot_carrying: list[tuple[float, float]] = []
    disposal_xs: list[float] = []
    disposal_ys: list[float] = []

    for agent in model.agents:
        if agent.pos is None:
            continue
        x, y = agent.pos

        if isinstance(agent, WasteDisposalZone):
            disposal_xs.append(x)
            disposal_ys.append(y)
        elif isinstance(agent, Waste):
            if agent.type in waste_xs:
                waste_xs[agent.type].append(x)
                waste_ys[agent.type].append(y)
        elif isinstance(agent, BaseAgent):
            key = agent.robot_type.name
            if key in robot_xs:
                robot_xs[key].append(x)
                robot_ys[key].append(y)
                if agent.knowledge.carried_wastes:
                    robot_carrying.append((x, y))

    if disposal_xs:
        ax.scatter(disposal_xs, disposal_ys,
                   c=v.disposal_zone_color, s=280, marker="D", zorder=4, linewidths=0)

    for waste_type, xs in waste_xs.items():
        if xs:
            ax.scatter(xs, waste_ys[waste_type],
                       c=waste_colors[waste_type], s=70, marker="s",
                       zorder=3, linewidths=0, alpha=0.9)

    for key, xs in robot_xs.items():
        if xs:
            ax.scatter(xs, robot_ys[key],
                       c=robot_colors[key], s=140, marker="o",
                       zorder=4, linewidths=0.5, edgecolors="black")

    if robot_carrying:
        cx, cy = zip(*robot_carrying)
        ax.scatter(cx, cy, c="white", s=25, marker="o", zorder=5, linewidths=0)

    ax.set_xlim(-0.5, width - 0.5)
    ax.set_ylim(-0.5, height - 0.5)
    ax.set_aspect("equal")
    ax.tick_params(labelsize=7)
    fig.tight_layout(pad=0.4)
    return fig


# ---------------------------------------------------------------------------
# Chart builders — accept a shared DataFrame to avoid redundant rebuilds
# ---------------------------------------------------------------------------

def _waste_chart(df: pd.DataFrame) -> Figure:
    fig = Figure(figsize=(5, 2.4))
    ax  = fig.add_subplot(111)
    if not df.empty:
        ax.plot(df.index, df["Waste (Green)"],  color="#00aa00", label="Green",  linewidth=1.5)
        ax.plot(df.index, df["Waste (Yellow)"], color="#ccaa00", label="Yellow", linewidth=1.5)
        ax.plot(df.index, df["Waste (Red)"],    color="#cc2200", label="Red",    linewidth=1.5)
        ax.legend(fontsize=7, loc="upper right")
        ax.set_ylim(bottom=0)
    ax.set_title("Waste remaining", fontsize=9)
    ax.set_xlabel("Step", fontsize=7)
    ax.set_ylabel("Count", fontsize=7)
    ax.tick_params(labelsize=7)
    fig.tight_layout(pad=0.5)
    return fig


def _carrying_chart(df: pd.DataFrame) -> Figure:
    fig = Figure(figsize=(5, 2.4))
    ax  = fig.add_subplot(111)
    if not df.empty:
        ax.plot(df.index, df["Agents Carrying"], color="steelblue", linewidth=1.5)
        ax.set_ylim(bottom=0)
    ax.set_title("Agents carrying waste", fontsize=9)
    ax.set_xlabel("Step", fontsize=7)
    ax.set_ylabel("Count", fontsize=7)
    ax.tick_params(labelsize=7)
    fig.tight_layout(pad=0.5)
    return fig


def _coverage_chart(df: pd.DataFrame) -> Figure:
    fig = Figure(figsize=(5, 2.4))
    ax  = fig.add_subplot(111)
    if not df.empty:
        ax.plot(df.index, df["Grid Coverage (%)"], color="mediumpurple", linewidth=1.5)
        ax.set_ylim(0, 100)
        ax.yaxis.set_major_formatter(lambda x, _: f"{x:.0f}%")
    ax.set_title("Grid exploration coverage", fontsize=9)
    ax.set_xlabel("Step", fontsize=7)
    ax.set_ylabel("%", fontsize=7)
    ax.tick_params(labelsize=7)
    fig.tight_layout(pad=0.5)
    return fig


# ---------------------------------------------------------------------------
# Main page component
# ---------------------------------------------------------------------------

@solara.component
def SimulationPage(config: Config):  # noqa: N802 — Solara components use PascalCase
    # Model lives in a ref — mutations don't trigger re-render.
    # step_counter is the sole re-render trigger.
    model_ref = solara.use_ref(None)
    if model_ref.current is None:
        model_ref.current = SystemModel(config)

    step_counter,    set_step_counter    = solara.use_state(0)
    playing,         set_playing         = solara.use_state(False)
    show_belief_map, set_show_belief_map = solara.use_state(False)

    def do_step():
        for _ in range(config.simulation.step_jump):
            model_ref.current.step()
        set_step_counter(model_ref.current.steps)

    def toggle_play():
        set_playing(not playing)

    def reset():
        set_playing(False)
        model_ref.current = SystemModel(config)
        set_step_counter(0)

    # Solara async task replaces the manual daemon thread.
    # Cancelled and restarted automatically whenever `playing` changes.
    async def play_loop():
        while playing:
            for _ in range(config.simulation.step_jump):
                model_ref.current.step()
            set_step_counter(model_ref.current.steps)
            await asyncio.sleep(config.viewer.play_interval)

    solara.lab.use_task(play_loop, dependencies=[playing])

    model = model_ref.current
    # Build DataFrame once — shared by all three chart builders
    df = model.datacollector.get_model_vars_dataframe()

    with solara.Column(style={"width": "100%", "padding": "8px", "box-sizing": "border-box"}):

        # ── Controls bar ────────────────────────────────────────────────────
        with solara.Row(style={"align-items": "center", "gap": "12px", "margin-bottom": "8px",
                                "flex-wrap": "wrap"}):
            solara.Text(f"Step: {step_counter}", style={"font-weight": "bold", "font-size": "16px"})
            solara.Button("Pause" if playing else "▶ Play", on_click=toggle_play)
            solara.Button("Step →", on_click=do_step, disabled=playing)
            solara.Button("↺ Reset", on_click=reset)
            solara.Checkbox(label="Belief Map overlay",
                            value=show_belief_map,
                            on_value=set_show_belief_map)

        # ── Main content: grid (left) + charts (right) ───────────────────
        with solara.Row(style={"width": "100%", "align-items": "flex-start", "gap": "8px"}):

            # Grid panel (65%) — PNG: raster is much faster than SVG for dense figures
            with solara.Column(style={"flex": "0 0 65%", "min-width": "0"}):
                solara.FigureMatplotlib(
                    draw_grid(model, config, show_belief_map),
                    dependencies=[step_counter, show_belief_map],
                    format="png",
                )

            # Charts panel (35%) — SVG fine: small, few elements
            with solara.Column(style={"flex": "0 0 calc(35% - 8px)", "min-width": "0", "gap": "4px"}):
                solara.FigureMatplotlib(
                    _waste_chart(df),
                    dependencies=[step_counter],
                    format="svg",
                )
                solara.FigureMatplotlib(
                    _carrying_chart(df),
                    dependencies=[step_counter],
                    format="svg",
                )
                solara.FigureMatplotlib(
                    _coverage_chart(df),
                    dependencies=[step_counter],
                    format="svg",
                )


def create_visualization(config: Config):
    return SimulationPage(config=config)
