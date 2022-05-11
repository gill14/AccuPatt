import accupatt.config as cfg
import matplotlib.ticker
import numpy as np
from accupatt.helpers.atomizationModel import AtomizationModel
from accupatt.helpers.cardStatTabelModel import CardStatTableModel, ComboBoxDelegate
from accupatt.models.passData import Pass
from accupatt.models.seriesData import SeriesData
from accupatt.models.sprayCard import SprayCard
from accupatt.models.sprayCardComposite import SprayCardComposite
from accupatt.widgets.mplwidget import MplWidget
from PyQt6.QtWidgets import QTableWidget


class CardPlotter:
    def plotDistribution(
        mplWidget1: MplWidget,
        mplWidget2: MplWidget,
        tableWidget: QTableWidget,
        composite: SprayCardComposite,
    ):
        # Create sorting bins
        bins = [x for x in range(0, 900, 50)]
        binned_cov = [0 for b in bins]
        binned_quant = [0 for b in bins]
        # Abort if no stains
        if len(composite.stain_areas_valid_px2) > 0:
            # Convenience accessors
            area_list = composite.drop_vol_um3
            sum_area = sum(area_list)
            dia_list = composite.drop_dia_um
            # Get an array of bins each drop dia belongs in (1-based)
            binned_dia = np.digitize(dia_list, bins)
            # Sort values into bins
            for area, bin in zip(area_list, binned_dia):
                binned_cov[bin - 1] += area / sum_area
                binned_quant[bin - 1] += 1
        CardPlotter._plotDistCov(mplWidget1, bins, binned_cov)
        CardPlotter._plotDistQuant(mplWidget2, bins, binned_quant)
        CardPlotter._plotDistStatTable(tableWidget, composite)

    def _plotDistCov(mplWidget: MplWidget, bins, binned_cov):
        # Setup Axes and Clear
        ax = mplWidget.canvas.ax
        ax.clear()
        ax.set_xlabel("Droplet Diameter (microns)")
        ax.set_xticks(bins)
        ax.yaxis.set_major_formatter(
            matplotlib.ticker.PercentFormatter(xmax=1.0, decimals=0)
        )
        ax.set_ylabel("Spray Volume")
        # Populate data
        ax.hist(bins, bins, weights=binned_cov, rwidth=0.8)
        for label in ax.get_xticklabels(which="major"):
            label.set(rotation=30, horizontalalignment="right")
        # Plot
        mplWidget.canvas.fig.set_tight_layout(True)
        mplWidget.canvas.draw()

    def _plotDistQuant(mplWidget: MplWidget, bins, binned_quant):
        # Setup Axes and Clear
        ax = mplWidget.canvas.ax
        ax.clear()
        ax.set_xticks(bins)
        ax.set_xlabel("Droplet Diameter (microns)")
        ax.set_ylabel("Number of Droplets")
        # Populate Data
        ax.hist(bins, bins, weights=binned_quant, rwidth=0.8)
        for label in ax.get_xticklabels(which="major"):
            label.set(rotation=30, horizontalalignment="right")
        # Plot
        mplWidget.canvas.fig.set_tight_layout(True)
        mplWidget.canvas.draw()

    def _plotDistStatTable(tableWidget: QTableWidget, composite: SprayCardComposite):
        # clear tv
        for row in range(tableWidget.rowCount()):
            tableWidget.item(row, 1).setText("-")
        # If no drops, return
        if len(composite.stain_areas_valid_px2) < 1:
            return
        tableWidget.item(0, 1).setText(composite.stats.get_dsc())
        tableWidget.item(1, 1).setText(composite.stats.get_dv01(text=True))
        tableWidget.item(2, 1).setText(composite.stats.get_dv05(text=True))
        tableWidget.item(3, 1).setText(composite.stats.get_dv09(text=True))
        tableWidget.item(4, 1).setText(composite.stats.get_relative_span(text=True))
        tableWidget.item(5, 1).setText(composite.stats.get_percent_coverage(text=True))
        tableWidget.item(6, 1).setText(f"{composite.area_in2:.2f} in\u00B2")
        tableWidget.item(7, 1).setText(composite.stats.get_number_of_stains(text=True))
        tableWidget.item(8, 1).setText(
            str(round(composite.stats.get_number_of_stains() / composite.area_in2))
        )
        tableWidget.resizeColumnsToContents()

    def plotSpatial(
        mplWidget: MplWidget, sprayCards: list[SprayCard], loc_units, colorize=False
    ):
        # Units for plot

        # Init vals as none
        locs, cov, dv01, dv05, dv09 = [None] * 5
        # Get a ist of valid cards with locations
        scs = [
            card
            for card in sprayCards
            if card.has_image
            and card.include_in_composite
            and card.location is not None
            and card.location_units is not None
        ]
        # Process each card for stats
        # for card in scs:
        #    card.images_processed()
        # Remove cards with no stains
        scs = [card for card in scs if len(card.stain_areas_valid_px2) > 0]
        # Populate arrays if cards available
        if len(scs) > 0:
            # Sort by location
            scs.sort(key=lambda x: x.location)
            # Create plottable series
            locs = [card.location for card in scs]
            units = [card.location_units for card in scs]
            # Modify loc units as necessary
            for i, (loc, unit) in enumerate(zip(locs, units)):
                if unit != loc_units:
                    if unit == cfg.UNIT_FT:
                        locs[i] = loc / cfg.FT_PER_M
                    else:
                        locs[i] = loc * cfg.FT_PER_M
            cov = [card.stats.get_percent_coverage() for card in scs]
            dv01 = [card.stats.get_dv01() for card in scs]
            dv05 = [card.stats.get_dv05() for card in scs]
            dv09 = [card.stats.get_dv09() for card in scs]
        # Plot
        # CardPlotter._plotSpatialDV(mplWidget1, x=locs, y_01=dv01, y_05=dv05, y_09=dv09, x_units=loc_units)
        CardPlotter._plotSpatialCov(
            mplWidget,
            x=locs,
            y_cov=cov,
            y_01=dv01,
            y_05=dv05,
            x_units=loc_units,
            fill_dsc=colorize,
        )

    def _plotSpatialDV(mplWidget: MplWidget, x, y_01, y_05, y_09, x_units):
        # Setup Axes and Clear
        ax = mplWidget.canvas.ax
        ax.clear()
        ax.set_xlabel(f"Location ({x_units})")
        ax.set_ylabel("Droplet Size (microns)")
        # Populate data if available
        if x is not None:
            ax.plot(x, y_09, label="$D_{V0.9}$")
            ax.plot(x, y_05, label="$VMD$")
            ax.plot(x, y_01, label="$D_{V0.1}$")
            # Legend
            ax.legend(loc="center left", bbox_to_anchor=(1, 0.5))
        # Draw the plots
        mplWidget.canvas.fig.set_tight_layout(True)
        mplWidget.canvas.draw()

    def _plotSpatialCov(mplWidget: MplWidget, x, y_cov, y_01, y_05, x_units, fill_dsc):
        # Setup Axes and Clear
        ax = mplWidget.canvas.ax
        ax.clear()
        ax.set_xlabel(f"Location ({x_units})")
        ax.set_ylabel("Coverage")
        ax.yaxis.set_major_formatter(
            matplotlib.ticker.PercentFormatter(xmax=100, decimals=0)
        )
        # Populate data if available
        if x is not None:
            # Interpolate so that fill-between looks good
            locs_i = np.linspace(x[0], x[-1], num=1000)
            cov_i = np.interp(locs_i, x, y_cov)
            # Colorize
            if fill_dsc:
                # Get a np array of dsc's calculated for each interpolated loc
                dv01_i = np.interp(locs_i, x, y_01)
                dv05_i = np.interp(locs_i, x, y_05)
                dsc_i = np.array(
                    [
                        AtomizationModel().dsc(dv01=dv01, dv05=dv05)
                        for (dv01, dv05) in zip(dv01_i, dv05_i)
                    ]
                )
                # Plot the fill data using dsc-specified colors
                categories = list(AtomizationModel.ref_nozzles)
                colors = [
                    AtomizationModel.ref_nozzles[category]["Color"]
                    for category in categories
                ]
                for (category, color) in zip(categories, colors):
                    ax.fill_between(
                        locs_i,
                        np.ma.masked_where(dsc_i != category, cov_i),
                        color=color,
                        label=category,
                    )
                ax.legend(loc="center left", bbox_to_anchor=(1, 0.5))
            # Plot base coverage without dsc fill
            ax.plot(locs_i, cov_i, color="black")
        # Draw the plots
        mplWidget.canvas.fig.set_tight_layout(True)
        mplWidget.canvas.draw()
