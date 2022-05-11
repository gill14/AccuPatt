import matplotlib.ticker
import numpy as np
import accupatt.config as cfg
from accupatt.helpers.atomizationModel import AtomizationModel

from accupatt.models.sprayCard import SprayCard
from accupatt.widgets.mplwidget import MplWidget


class PassCardData:
    def __init__(self):
        # Card Data
        self.card_list: list[SprayCard] = []
        # Card Data Mod options
        self.center = True
        self.center_method = cfg.get_center_method()

    """
    Plot Methods
    """

    def plot(self, mplWidget: MplWidget, loc_units, colorize=False):
        # Units for plot

        # Init vals as none
        locs, cov, dv01, dv05, dv09 = [None] * 5
        # Get a ist of valid cards with locations
        scs = [
            card
            for card in self.card_list
            if card.has_image
            and card.include_in_composite
            and card.location is not None
            and card.location_units is not None
            and len(card.stain_areas_valid_px2) > 0
        ]
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
        self._plotSpatialCov(
            mplWidget=mplWidget,
            x=locs,
            y_cov=cov,
            y_01=dv01,
            y_05=dv05,
            x_units=loc_units,
            fill_dsc=colorize,
        )

    def _plotSpatialDV(self, mplWidget: MplWidget, x, y_01, y_05, y_09, x_units):
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

    def _plotSpatialCov(
        self, mplWidget: MplWidget, x, y_cov, y_01, y_05, x_units, fill_dsc
    ):
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
