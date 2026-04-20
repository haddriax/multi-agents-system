# Group: 9
# Date: 25-03-2026
# Members: Maëlys Hanoire, Raphaël Vignal, Gaël Garnier

import solara
from matplotlib.figure import Figure
from mesa.visualization.utils import update_counter


@solara.component
def WasteChart(model):
    update_counter.get()
    df = model.datacollector.get_model_vars_dataframe()
    fig = Figure(figsize=(5, 2.4))
    ax = fig.add_subplot()
    if not df.empty:
        v = model.config.viewer
        ax.plot(df["Waste (Green)"],  color=v.waste_color_green,  label="Green")
        ax.plot(df["Waste (Yellow)"], color=v.waste_color_yellow, label="Yellow")
        ax.plot(df["Waste (Red)"],    color=v.waste_color_red,    label="Red")
        ax.legend(fontsize=7)
        ax.set_ylim(bottom=0)
    ax.set_title("Waste remaining", fontsize=9)
    ax.set_xlabel("Step", fontsize=7)
    solara.FigureMatplotlib(fig, format="svg", bbox_inches="tight")


@solara.component
def CarryingChart(model):
    update_counter.get()
    df = model.datacollector.get_model_vars_dataframe()
    fig = Figure(figsize=(5, 2.4))
    ax = fig.add_subplot()
    if not df.empty:
        ax.plot(df["Agents Carrying"], color=model.config.viewer.chart_carrying_color)
        ax.set_ylim(bottom=0)
    ax.set_title("Agents carrying waste", fontsize=9)
    ax.set_xlabel("Step", fontsize=7)
    solara.FigureMatplotlib(fig, format="svg", bbox_inches="tight")


@solara.component
def CoverageChart(model):
    update_counter.get()
    df = model.datacollector.get_model_vars_dataframe()
    fig = Figure(figsize=(5, 2.4))
    ax = fig.add_subplot()
    if not df.empty:
        ax.plot(df["Grid Coverage (%)"], color="mediumpurple")
        ax.set_ylim(0, 100)
    ax.set_title("Grid exploration coverage", fontsize=9)
    ax.set_xlabel("Step", fontsize=7)
    solara.FigureMatplotlib(fig, format="svg", bbox_inches="tight")
