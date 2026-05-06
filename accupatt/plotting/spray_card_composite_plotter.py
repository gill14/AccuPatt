import matplotlib.ticker
import numpy as np
from PyQt6.QtWidgets import QTableWidget

from accupatt.models.sprayCardComposite import SprayCardComposite
from accupatt.widgets.mplwidget import MplWidget


def plot_distribution(
    widget1: MplWidget,
    widget2: MplWidget,
    table_widget: QTableWidget,
    composite: SprayCardComposite,
):
    bins = [x for x in range(0, 900, 50)]
    binned_cov = [0 for b in bins]
    binned_quant = [0 for b in bins]
    if any([s["is_include"] for s in composite.stains]):
        area_list = [s["area"] for s in composite.stains if s["is_include"]]
        sum_area = sum(area_list)
        dia_list = composite.drop_dia_um
        binned_dia = np.digitize(dia_list, bins)
        for area, bin_ in zip(area_list, binned_dia):
            binned_cov[bin_ - 1] += area / sum_area
            binned_quant[bin_ - 1] += 1
    _plot_dist_cov(widget1, bins, binned_cov)
    _plot_dist_quant(widget2, bins, binned_quant)
    _plot_dist_stat_table(table_widget, composite)


def _plot_dist_cov(widget: MplWidget, bins: list, binned_cov: list):
    ax = widget.canvas.ax
    ax.clear()
    ax.set_xlabel("Droplet Diameter (microns)")
    ax.set_xticks(bins)
    ax.yaxis.set_major_formatter(
        matplotlib.ticker.PercentFormatter(xmax=1.0, decimals=0)
    )
    ax.set_ylabel("Volume Fraction")
    ax.hist(bins, bins, weights=binned_cov, rwidth=0.8)
    widget.set_ticks_slanted()
    widget.has_legend = False
    widget.canvas.draw()


def _plot_dist_quant(widget: MplWidget, bins: list, binned_quant: list):
    ax = widget.canvas.ax
    ax.clear()
    ax.set_xticks(bins)
    ax.set_xlabel("Droplet Diameter (microns)")
    ax.set_ylabel("Number of Droplets")
    ax.hist(bins, bins, weights=binned_quant, rwidth=0.8)
    widget.set_ticks_slanted()
    widget.has_legend = False
    widget.canvas.draw()


def _plot_dist_stat_table(table_widget: QTableWidget, composite: SprayCardComposite):
    for row in range(table_widget.rowCount()):
        table_widget.item(row, 1).setText("-")
    if not any(s["is_include"] for s in composite.stains):
        return
    table_widget.item(0, 1).setText(composite.stats.get_dsc())
    table_widget.item(1, 1).setText(composite.stats.get_dv01(text=True))
    table_widget.item(2, 1).setText(composite.stats.get_dv05(text=True))
    table_widget.item(3, 1).setText(composite.stats.get_dv09(text=True))
    table_widget.item(4, 1).setText(composite.stats.get_relative_span(text=True))
    table_widget.item(5, 1).setText(composite.stats.get_percent_coverage(text=True))
    table_widget.item(6, 1).setText(f"{composite.area_in2:.2f} in²")
    table_widget.item(7, 1).setText(composite.stats.get_number_of_stains(text=True))
    table_widget.item(8, 1).setText(
        str(round(composite.stats.get_number_of_stains() / composite.area_in2))
    )
    table_widget.resizeColumnsToContents()
