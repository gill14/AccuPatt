import matplotlib.ticker
import numpy as np
import pandas as pd
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

    def _get_data_from_card_list(self):
        scs: list[SprayCard] = sorted(
            [
                card
                for card in self.card_list
                if card.has_image
                and card.include_in_composite
                and card.location is not None
                and card.location_units is not None
                and len(card.stain_areas_valid_px2) > 0
            ],
            key=lambda x: x.location,
        )
        return pd.DataFrame(
            {
                "name": [card.name for card in scs],
                "loc": [card.location for card in scs],
                "loc_units": [card.location_units for card in scs],
                "cov": [card.stats.get_percent_coverage() for card in scs],
                "dv01": [card.stats.get_dv01() for card in scs],
                "dv05": [card.stats.get_dv05() for card in scs],
                "dv09": [card.stats.get_dv09() for card in scs],
            }
        )

    def get_data_mod(self, loc_units, data=pd.DataFrame()) -> pd.DataFrame:
        if data.empty:
            data = self._get_data_from_card_list()
        # Homogenize location units to arg
        for i, (loc, unit) in enumerate(zip(data["loc"], data["loc_units"])):
            if unit != loc_units:
                if unit == cfg.UNIT_FT:
                    data["loc"][i] = loc / cfg.FT_PER_M
                else:
                    data["loc"][i] = loc * cfg.FT_PER_M
        # Centerify
        self._centerify(data, center=self.center, centerMethod=self.center_method)
        # Do more things potentially...
        return data

    def _centerify(self, d: pd.DataFrame, center, centerMethod):
        if not center or d.empty:
            return
        if centerMethod == cfg.CENTER_METHOD_CENTROID:
            # Use Centroid
            c = self._calcCentroid(d)
        elif centerMethod == cfg.CENTER_METHOD_COD:
            # Use Center of Distribution
            c = self._calcCenterOfDistribution(d)
        else:
            # No centering applied
            c = 0
        # Subtract the calculated center from the x vals
        d["loc"] = d["loc"].sub(c)

    def _calcCentroid(self, d: pd.DataFrame):
        return (d["cov"] * d["loc"]).sum() / d["cov"].sum()

    def _calcCenterOfDistribution(self, d: pd.DataFrame):
        sumNumerator = 0.0
        sumDenominator = 0.0
        for i in range(0, len(d.index) - 1, 1):
            D = d.at[i, "cov"]
            Dn = d.at[i + 1, "cov"]
            X = d.at[i, "loc"]
            Xn = d.at[i + 1, "loc"]
            # Calc Numerator and add to summation
            sumNumerator += D * (Xn + X) + (Dn - D) * (2 * Xn + X) / 3
            sumDenominator += Dn + D
        # Calc and return CoD
        return sumNumerator / sumDenominator

    """
    Plot Methods
    """

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

    def plotCoverage(
        self,
        mplWidget: MplWidget,
        loc_units,
        colorize=False,
        mod=True,
        d=pd.DataFrame(),
    ):
        if d.empty:
            if mod:
                d = self.get_data_mod(loc_units=loc_units)
            else:
                d = self._get_data_from_card_list()
        # Setup Axes and Clear
        ax = mplWidget.canvas.ax
        ax.clear()
        ax.set_xlabel(f"Location ({loc_units})")
        ax.set_ylabel("Coverage")
        ax.yaxis.set_major_formatter(
            matplotlib.ticker.PercentFormatter(xmax=100, decimals=0)
        )
        # Populate data if available
        if not d["loc"].empty:
            # Interpolate so that fill-between looks good
            locs_i = np.linspace(d["loc"].iloc[0], d["loc"].iloc[-1], num=1000)
            cov_i = np.interp(locs_i, d["loc"], d["cov"])
            # Colorize
            if colorize:
                # Get a np array of dsc's calculated for each interpolated loc
                dv01_i = np.interp(locs_i, d["loc"], d["dv01"])
                dv05_i = np.interp(locs_i, d["loc"], d["dv05"])
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
