import matplotlib.ticker
import numpy as np
from accupatt.models.passData import Pass
from accupatt.models.seriesData import SeriesData
from accupatt.models.sprayCard import SprayCard
from accupatt.widgets.mplwidget import MplWidget

from PyQt6.QtWidgets import QTableWidget


class SprayCardComposite(SprayCard):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Must keep these lists for appending to as building from individual spray cards
        self.drop_dia_um = []
        self.drop_vol_um3 = []
        # Must keep this for building sum area of individual spray cards
        self.area_in2 = 0.0

    """
    Builder Methods to generate composite
    """

    def buildFromCard(self, card: SprayCard):
        self._buildFromList([card])

    def buildFromPass(self, passData: Pass):
        self._buildFromList(passData.cards.card_list)

    def buildFromSeries(self, seriesData: SeriesData):
        cards: list[SprayCard] = []
        for p in seriesData.passes:
            if p.cards.include_in_composite:
                for card in p.cards.card_list:
                    cards.append(card)
        self._buildFromList(cards)

    def _buildFromList(self, cards: list[SprayCard]):
        # Build composite from valid cards
        for card in cards:
            if not card.has_image:
                continue
            if not card.include_in_composite:
                continue
            self.area_px2 += card.area_px2
            self.area_in2 += card.stats._px2_to_in2(card.area_px2)
            dd, dv = card.stats.get_droplet_diameters_and_volumes()
            self.drop_dia_um.extend(dd)
            self.drop_vol_um3.extend(dv)
            self.stains.extend(card.stains)
        # Sort the dia and vol lists before computing dv's
        self.stains.sort(key=lambda s: s["area"])
        self.drop_dia_um.sort()
        self.drop_vol_um3.sort()
        # Set the dv vals in composite stats object for future use
        self.stats.set_volumetric_stats(self.drop_dia_um, self.drop_vol_um3)

    """
    Plot Methods
    """

    def plotDistribution(
        self,
        mplWidget1: MplWidget,
        mplWidget2: MplWidget,
        tableWidget: QTableWidget,
    ):
        # Create sorting bins
        bins = [x for x in range(0, 900, 50)]
        binned_cov = [0 for b in bins]
        binned_quant = [0 for b in bins]
        # Abort if no stains
        if any([s["is_include"] for s in self.stains]):
            # Convenience accessors
            area_list = [s["area"] for s in self.stains if s["is_include"]]
            sum_area = sum(area_list)
            dia_list = self.drop_dia_um
            # Get an array of bins each drop dia belongs in (1-based)
            binned_dia = np.digitize(dia_list, bins)
            # Sort values into bins
            for area, bin in zip(area_list, binned_dia):
                binned_cov[bin - 1] += area / sum_area
                binned_quant[bin - 1] += 1
        self._plotDistCov(mplWidget1, bins, binned_cov)
        self._plotDistQuant(mplWidget2, bins, binned_quant)
        self._plotDistStatTable(tableWidget)

    def _plotDistCov(self, mplWidget: MplWidget, bins, binned_cov):
        # Setup Axes and Clear
        ax = mplWidget.canvas.ax
        ax.clear()
        ax.set_xlabel("Droplet Diameter (microns)")
        ax.set_xticks(bins)
        ax.yaxis.set_major_formatter(
            matplotlib.ticker.PercentFormatter(xmax=1.0, decimals=0)
        )
        ax.set_ylabel("Volume Fraction")
        # Populate data
        ax.hist(bins, bins, weights=binned_cov, rwidth=0.8)
        mplWidget.set_ticks_slanted()
        mplWidget.has_legend = False
        # Plot
        mplWidget.canvas.draw()

    def _plotDistQuant(self, mplWidget: MplWidget, bins, binned_quant):
        # Setup Axes and Clear
        ax = mplWidget.canvas.ax
        ax.clear()
        ax.set_xticks(bins)
        ax.set_xlabel("Droplet Diameter (microns)")
        ax.set_ylabel("Number of Droplets")
        # Populate Data
        ax.hist(bins, bins, weights=binned_quant, rwidth=0.8)
        mplWidget.set_ticks_slanted()
        mplWidget.has_legend = False
        # Plot
        mplWidget.canvas.draw()

    def _plotDistStatTable(self, tableWidget: QTableWidget):
        # clear tv
        for row in range(tableWidget.rowCount()):
            tableWidget.item(row, 1).setText("-")
        # If no drops, return
        if not any(s["is_include"] for s in self.stains):
            return
        tableWidget.item(0, 1).setText(self.stats.get_dsc())
        tableWidget.item(1, 1).setText(self.stats.get_dv01(text=True))
        tableWidget.item(2, 1).setText(self.stats.get_dv05(text=True))
        tableWidget.item(3, 1).setText(self.stats.get_dv09(text=True))
        tableWidget.item(4, 1).setText(self.stats.get_relative_span(text=True))
        tableWidget.item(5, 1).setText(self.stats.get_percent_coverage(text=True))
        tableWidget.item(6, 1).setText(f"{self.area_in2:.2f} in\u00B2")
        tableWidget.item(7, 1).setText(self.stats.get_number_of_stains(text=True))
        tableWidget.item(8, 1).setText(
            str(round(self.stats.get_number_of_stains() / self.area_in2))
        )
        tableWidget.resizeColumnsToContents()
