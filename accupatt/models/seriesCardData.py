import numpy as np
import pandas as pd
import accupatt.config as cfg
from accupatt.models.passCardData import PassCardData
from accupatt.models.passData import Pass
from accupatt.widgets.mplwidget import MplWidget


class SeriesCardData:
    def __init__(self, passes: list[Pass], swath_units: str):
        # Live feeds from Series Object
        self.passes = passes
        self.swath_units = swath_units
        # Options
        # self.smooth = True
        # self.smooth_window = cfg.get_string_smooth_window()
        # self.smooth_order = cfg.get_string_smooth_order()
        # self.equalize_integrals = True
        self.center = True
        self.center_method = cfg.get_center_method()
        self.simulated_adjascent_passes = 2

    def _get_active_passes(self) -> list[Pass]:
        return [
            p for p in self.passes if p.cards_include_in_composite and p.has_card_data()
        ]

    def _get_average(self) -> pd.DataFrame:
        a_cov = pd.DataFrame()
        a_dv01 = pd.DataFrame()
        a_dv05 = pd.DataFrame()
        for p in self._get_active_passes():
            data: pd.DataFrame = p.cards.get_data_mod(loc_units=self.swath_units)
            s_cov = data.set_index("loc")["cov"]
            a_cov = a_cov.join(s_cov, how="outer", lsuffix="_l", rsuffix="_r")
            s_dv01 = data.set_index("loc")["dv01"]
            a_dv01 = a_dv01.join(s_dv01, how="outer", lsuffix="_l", rsuffix="_r")
            s_dv05 = data.set_index("loc")["dv05"]
            a_dv05 = a_dv05.join(s_dv05, how="outer", lsuffix="_l", rsuffix="_r")
        # take column-wise average
        a_cov.interpolate(limit_area="inside", inplace=True)
        a_cov["cov"] = a_cov.mean(axis="columns")
        a_dv01.interpolate(limit_area="inside", inplace=True)
        a_dv01["dv01"] = a_dv01.mean(axis="columns")
        a_dv05.interpolate(limit_area="inside", inplace=True)
        a_dv05["dv05"] = a_dv05.mean(axis="columns")
        d = pd.concat([a_cov["cov"], a_dv01["dv01"], a_dv05["dv05"]], axis=1)
        d.reset_index(inplace=True)
        d["loc_units"] = pd.Series([self.swath_units for i in range(len(d.index))], dtype=str)
        return d

    def plotOverlay(self, mplWidget: MplWidget):
        # Setup and clear the plotter
        self._config_mpl_plotter(mplWidget)
        active_passes = self._get_active_passes()
        # Iterate over plottable passes
        for p in active_passes:
            data = p.cards.get_data_mod(loc_units=self.swath_units)
            # Numpy-ize dataframe columns to plot
            x = np.array(data["loc"], dtype=float)
            y = np.array(data["cov"], dtype=float)
            # Plot non-zero data, and label the series with the pass name
            mplWidget.canvas.ax.plot(x[y != 0], y[y != 0], label=p.name)
        # Add a legend if applicable
        if len(active_passes) > 1:
            mplWidget.canvas.ax.legend()
        # Must set ylim after plotting
        mplWidget.canvas.ax.set_ylim(bottom=0, auto=None)
        # Draw the plot regardless if passes were plotted to it
        mplWidget.canvas.draw()

    def plotAverage(self, mplWidget: MplWidget, colorize: bool):
        # Setup and clear the plotter
        self._config_mpl_plotter(mplWidget)

        avg = self._get_average()
        avgPass = PassCardData()
        avgPass.center = self.center
        avgPass.center_method = self.center_method
        avg = avgPass.get_data_mod(loc_units=self.swath_units, data=avg)
        # Must re-add loc_units, as it is stripped during get_data_mod
        avg["loc_units"] = pd.Series([self.swath_units for i in range(len(avg.index))], dtype=str)
        avgPass.plotCoverage(
            mplWidget=mplWidget, loc_units=self.swath_units, colorize=colorize, d=avg
        )

    def _config_mpl_plotter(self, mplWidget: MplWidget):
        mplWidget.canvas.ax.clear()
        mplWidget.canvas.ax.set_xlabel(f"Location ({self.swath_units})")
        mplWidget.canvas.ax.set_yticks([])
