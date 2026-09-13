import numpy as np
import accupatt.config as cfg

from accupatt.models.passDataCard import PassDataCard
from accupatt.models.passTable import _MPL_COLORS
from accupatt.models.seriesDataBase import STD_DEV_LABEL
from accupatt.models.seriesDataCard import SeriesDataCard
from accupatt.widgets.mplwidget import MplWidget
from accupatt.plotting import pass_card_plotter, series_base_plotter


def plot_overlay(widget: MplWidget, series: SeriesDataCard):
    series_base_plotter._configure(widget, series.swath_units)
    widget.canvas.ax.set_ylabel(cfg.get_card_plot_y_axis_label())
    active_passes = series._get_active_passes()
    for p in active_passes:
        color = _MPL_COLORS[series.passes.index(p) % len(_MPL_COLORS)]
        data = p.cards.get_data_mod(loc_units=series.swath_units)
        x = np.array(data["loc"], dtype=float)
        y = np.array(data[cfg.get_card_plot_y_axis()], dtype=float)
        widget.canvas.ax.plot(x[y != 0], y[y != 0], color=color, linewidth=1, label=p.name)
    if len(active_passes) > 1:
        widget.canvas.ax.legend()
    widget.canvas.ax.set_ylim(bottom=0, auto=None)
    widget.canvas.draw()


def plot_average(widget: MplWidget, series: SeriesDataCard):
    series_base_plotter._configure(widget, series.swath_units)
    avg = series._get_average()
    if avg.empty:
        widget.canvas.draw()
        return
    avgPass = PassDataCard(name="average")
    avgPass.center = series.center
    avgPass.center_method = series.center_method
    avg = avgPass.get_data_mod(loc_units=series.swath_units, data=avg)
    avg["loc_units"] = series.swath_units
    pass_card_plotter.plot(widget, avgPass, series.swath_units, d=avg)
    y_axis = cfg.get_card_plot_y_axis()
    added_legend_entry = False
    if cfg.get_card_plot_average_std_dev_overlay() and STD_DEV_LABEL in avg.columns:
        added_legend_entry = series_base_plotter.plot_std_dev_overlay(
            widget,
            np.array(avg["loc"], dtype=float),
            np.array(avg[y_axis], dtype=float),
            np.array(avg[STD_DEV_LABEL], dtype=float),
        )
    if cfg.get_card_plot_average_dash_overlay():
        method = cfg.get_card_plot_average_dash_overlay_method()
        if method == cfg.DASH_OVERLAY_METHOD_ISHA:
            half_swath = series.swath_adjusted / 2
            dash_x = [-half_swath, -half_swath, half_swath, half_swath]
            a_c = avg[(avg["loc"] >= -half_swath) & (avg["loc"] <= half_swath)]
            a_c_mean = a_c[y_axis].mean(axis="rows")
            dash_y = [0, a_c_mean / 2, a_c_mean / 2, 0]
            dash_label = "Effective Swath"
        else:
            dash_x = [avg["loc"].iloc[0], avg["loc"].iloc[-1]]
            a_mean = avg[y_axis].mean(axis="rows")
            dash_y = [a_mean, a_mean]
            dash_label = f"Avg. {cfg.get_card_plot_y_axis_label()}"
        widget.canvas.ax.plot(
            dash_x, dash_y, color="black", linewidth=1, dashes=(3, 2), label=dash_label
        )
        added_legend_entry = True
    if added_legend_entry:
        if cfg.get_card_plot_shading():
            _extend_shading_legend(widget)
        else:
            widget.canvas.ax.legend()
    widget.canvas.ax.set_ylim(bottom=0, auto=None)
    widget.canvas.draw()


def _extend_shading_legend(widget: MplWidget):
    """
    Append this plot's labeled artists to the shading-category legend installed by
    pass_card_plotter, whose swatches are passed in as handles and so would be lost
    by a bare ax.legend() call.
    """
    ax = widget.canvas.ax
    handles, labels = ax.get_legend_handles_labels()
    legend = ax.get_legend()
    if legend is not None:
        handles = list(legend.legend_handles) + handles
        labels = [text.get_text() for text in legend.get_texts()] + labels
    ax.legend(handles, labels, loc="center left", bbox_to_anchor=(1, 0.5))


def plot_racetrack(widget: MplWidget, series: SeriesDataCard):
    showEntireWindow = (
        cfg.get_card_simulation_view_window() == cfg.CARD_SIMULATION_VIEW_WINDOW_ALL
    )
    series_base_plotter.plot_simulation(
        widget, series, showEntireWindow=showEntireWindow,
        y_axis_label=cfg.get_card_plot_y_axis_label()
    )


def plot_back_and_forth(widget: MplWidget, series: SeriesDataCard):
    showEntireWindow = (
        cfg.get_card_simulation_view_window() == cfg.CARD_SIMULATION_VIEW_WINDOW_ALL
    )
    series_base_plotter.plot_simulation(
        widget, series, showEntireWindow=showEntireWindow, mirrorAdjacent=True,
        y_axis_label=cfg.get_card_plot_y_axis_label()
    )
