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
        ax.plot(df["Waste (Green)"],  color="#00aa00", label="Green")
        ax.plot(df["Waste (Yellow)"], color="#ccaa00", label="Yellow")
        ax.plot(df["Waste (Red)"],    color="#cc2200", label="Red")
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
        ax.plot(df["Agents Carrying"], color="steelblue")
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
