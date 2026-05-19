import numpy as np
from PyQt6.QtWidgets import QTableWidget

from accupatt.models.seriesDataBase import SeriesDataBase
from accupatt.widgets.mplwidget import MplWidget
from accupatt import config as cfg


def plot_simulation(
    widget: MplWidget,
    series: SeriesDataBase,
    showEntireWindow: bool = False,
    mirrorAdjacent: bool = False,
    suppress_yticks: bool = False,
):
    _configure(widget, series.swath_units, suppress_yticks=suppress_yticks)
    average_df = series.get_average_mod()
    average_y_label = series.get_average_y_label()
    _sw = series.swath_adjusted
    if not average_df.empty and _sw >= 1:
        xfill, y_fills, labels = series._get_fill_arrays(
            swath_width=_sw,
            average_df=average_df,
            average_y_label=average_y_label,
            mirrorAdjacent=mirrorAdjacent,
        )
        n_adj = (len(labels) - 1) // 2
        collapse = n_adj > 3
        y_fill_cum = np.zeros(xfill.size)
        for i, y_fill in enumerate(y_fills):
            widget.canvas.ax.fill_between(
                xfill,
                y_fill_cum,
                y_fill_cum + y_fill,
                label=labels[i] if (not collapse or i <= 6) else "_nolegend_",
                alpha=0.8,
            )
            y_fill_cum = y_fill_cum + y_fill
        widget.canvas.ax.plot(xfill, y_fill_cum, color="black", label="Cumulative")
        avg = np.mean(
            y_fill_cum[np.where(((xfill >= -_sw / 2) & (xfill <= _sw / 2)))]
        )
        widget.canvas.ax.plot(
            [-_sw / 2, _sw / 2],
            [avg, avg],
            color="black",
            dashes=[5, 5],
            label="Mean Dep.",
        )
        if collapse:
            total_passes = 2 * n_adj + 1
            widget.canvas.ax.annotate(
                f"{total_passes} total passes, including {n_adj} simulated each side",
                xy=(0.5, 0),
                xycoords="axes fraction",
                xytext=(0, 4),
                textcoords="offset points",
                ha="center",
                va="bottom",
                color="white",
                fontsize=8,
            )
        widget.canvas.ax.legend(loc="center left", bbox_to_anchor=(1, 0.5))
        widget.canvas.ax.set_ylabel(
            "Back & Forth" if mirrorAdjacent else "Racetrack"
        )
        if not showEntireWindow:
            widget.canvas.ax.set_xlim(-_sw / 2, _sw / 2)
    widget.canvas.ax.set_ylim(bottom=0, auto=None)
    widget.canvas.draw()


def plot_cv_table(table_widget: QTableWidget, series: SeriesDataBase):
    average_df = series.get_average_mod()
    average_y_label = series.get_average_y_label()
    interval = 2 if series.swath_units == cfg.UNIT_FT else 1
    middle = (table_widget.rowCount() - 1) // 2
    for row in range(table_widget.rowCount()):
        item_sw = table_widget.item(row, 0)
        item_rt = table_widget.item(row, 1)
        item_bf = table_widget.item(row, 2)
        _sw = series.swath_adjusted + interval * (row - middle)
        if average_df.empty or _sw < 1:
            item_sw.setText("-")
            item_rt.setText("-")
            item_bf.setText("-")
            continue
        item_sw.setText(f"{_sw} {series.swath_units}")
        item_rt.setText(f"{series._calcCV(average_df, average_y_label, _sw, False)} %")
        item_bf.setText(f"{series._calcCV(average_df, average_y_label, _sw, True)} %")


def _configure(widget: MplWidget, swath_units: str, suppress_yticks: bool = False):
    widget.canvas.ax.clear()
    widget.canvas.ax.set_xlabel(f"Location ({swath_units})")
    if suppress_yticks:
        widget.canvas.ax.set_yticks([])
