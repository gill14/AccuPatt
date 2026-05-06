import numpy as np
import accupatt.config as cfg

from accupatt.models.seriesDataString import SeriesDataString
from accupatt.widgets.mplwidget import MplWidget
from accupatt.plotting import series_base_plotter


def plot_overlay(widget: MplWidget, series: SeriesDataString):
    series_base_plotter._configure(widget, series.swath_units, suppress_yticks=True)
    active_passes = [p for p in series.passes if p.string.is_active()]
    for p in active_passes:
        d = p.string.get_data_mod(loc_units_override=series.swath_units)
        x = np.array(d["loc"], dtype=float)
        y = np.array(d[p.name], dtype=float) * p.string.equalize_factor
        widget.canvas.ax.plot(x[y != 0], y[y != 0], linewidth=1, label=p.name)
    if len(active_passes) > 1:
        widget.canvas.ax.legend()
    widget.canvas.ax.set_ylim(bottom=0, auto=None)
    widget.canvas.draw()


def plot_average(widget: MplWidget, series: SeriesDataString):
    series_base_plotter._configure(widget, series.swath_units, suppress_yticks=True)
    a = series.get_average_mod()
    if not a.empty:
        x = np.array(a["loc"], dtype=float)
        y = np.array(a["Average"], dtype=float)
        widget.canvas.ax.plot(
            x[y != 0], y[y != 0], color="black", linewidth=2, label="Average"
        )
        widget.canvas.ax.fill_between(x[y != 0], 0, y[y != 0], alpha=0.7)
        _sw = series.swath_adjusted
        if cfg.get_string_plot_average_dash_overlay():
            method = cfg.get_string_plot_average_dash_overlay_method()
            if method == cfg.DASH_OVERLAY_METHOD_ISHA and _sw >= 1:
                dash_x = [-_sw / 2, -_sw / 2, _sw / 2, _sw / 2]
                a_c = a[(a["loc"] >= -_sw / 2) & (a["loc"] <= _sw / 2)]
                a_c_mean = a_c["Average"].mean(axis="rows")
                dash_y = [0, a_c_mean / 2, a_c_mean / 2, 0]
                dash_label = "Effective Swath"
            else:
                dash_x = [a["loc"].iloc[0], a["loc"].iloc[-1]]
                a_mean = a["Average"].mean(axis="rows")
                dash_y = [a_mean, a_mean]
                dash_label = "Average Value"
            widget.canvas.ax.plot(
                dash_x, dash_y, color="black", linewidth=1, dashes=(3, 2), label=dash_label
            )
        widget.canvas.ax.legend()
    widget.canvas.ax.set_ylim(bottom=0, auto=None)
    widget.canvas.draw()


def plot_racetrack(widget: MplWidget, series: SeriesDataString):
    showEntireWindow = (
        cfg.get_string_simulation_view_window() == cfg.STRING_SIMULATION_VIEW_WINDOW_ALL
    )
    series_base_plotter.plot_simulation(
        widget, series, showEntireWindow=showEntireWindow, suppress_yticks=True
    )


def plot_back_and_forth(widget: MplWidget, series: SeriesDataString):
    showEntireWindow = (
        cfg.get_string_simulation_view_window() == cfg.STRING_SIMULATION_VIEW_WINDOW_ALL
    )
    series_base_plotter.plot_simulation(
        widget, series, showEntireWindow=showEntireWindow, mirrorAdjacent=True, suppress_yticks=True
    )
