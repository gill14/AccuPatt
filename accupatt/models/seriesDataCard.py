import matplotlib
import numpy as np
import pandas as pd
from scipy import interpolate
import accupatt.config as cfg
from accupatt.models.passDataCard import PassDataCard
from accupatt.models.passData import Pass
from accupatt.models.seriesDataBase import SeriesDataBase
from accupatt.widgets.mplwidget import MplWidget
from PyQt6.QtWidgets import QTableWidget
from scipy.stats import variation


class SeriesDataCard(SeriesDataBase):
    def __init__(self, passes: list[Pass], target_swath, swath_units: str):
        super().__init__(passes, target_swath, swath_units)

    def _get_active_passes(self) -> list[Pass]:
        activePasses: list[Pass] = []
        for p in self.passes:
            if p.cards.is_active():
                activePasses.append(p)
        return activePasses

    def _get_average(self) -> pd.DataFrame:

        dd = pd.DataFrame()
        lastPassName = ""
        for p in self._get_active_passes():
            # Get Pass Dataframe
            d = p.cards.get_data_mod(loc_units=self.swath_units)
            # Start or merge to the series dataframe
            if dd.empty:
                dd = d
            else:
                _d = d.set_index("loc")
                _d.sort_values(by="loc", axis=0, inplace=True)
                _d["dv01"].interpolate(method="slinear", fill_value="extrapolate", inplace=True)
                _d["dv05"].interpolate(method="slinear", fill_value="extrapolate", inplace=True)
                
                dd = dd.merge(
                    _d,
                    on="loc",
                    how="outer",
                    suffixes=[f"_{lastPassName}", f"_{p.name}"],
                )
            lastPassName = p.name
        if dd.empty:
            return dd
        dd.set_index("loc", inplace=True)
        dd.sort_values(by="loc", axis=0, inplace=True)
        dd.interpolate(method="slinear", limit_area="inside", inplace=True)
        for col in dd.columns:
            if "cov" in col:
                dd[col].fillna(0, inplace=True)
        dd["cov_avg"] = dd.loc[:, dd.columns.str.contains("cov")].mean(axis="columns")
        dd["dv01_avg"] = dd.loc[:, dd.columns.str.contains("dv01")].mean(axis="columns")
        dd["dv05_avg"] = dd.loc[:, dd.columns.str.contains("dv05")].mean(axis="columns")
        dd["loc_units"] = [self.swath_units for i in range(len(dd.index))]
        avg = dd.loc[:, ["cov_avg", "dv01_avg", "dv05_avg", "loc_units"]].reset_index()
        avg.rename(
            columns={"cov_avg": "cov", "dv01_avg": "dv01", "dv05_avg": "dv05"},
            inplace=True,
        )
        return avg

    def plotOverlay(self, mplWidget: MplWidget):
        # Setup and clear the plotter
        self._config_mpl_plotter(mplWidget)
        mplWidget.canvas.ax.set_ylabel("Coverage")
        mplWidget.canvas.ax.yaxis.set_major_formatter(
            matplotlib.ticker.PercentFormatter(xmax=100, decimals=0)
        )
        active_passes = self._get_active_passes()
        # Iterate over plottable passes
        for p in active_passes:
            data = p.cards.get_data_mod(loc_units=self.swath_units)
            # Numpy-ize dataframe columns to plot
            x = np.array(data["loc"], dtype=float)
            y = np.array(data["cov"], dtype=float)
            # Plot non-zero data, and label the series with the pass name
            mplWidget.canvas.ax.plot(x[y != 0], y[y != 0], linewidth=1, label=p.name)
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
        if avg.empty:
            mplWidget.canvas.draw()
            return
        avgPass = PassDataCard(name="average")
        avgPass.center = self.center
        avgPass.center_method = self.center_method
        avg = avgPass.get_data_mod(loc_units=self.swath_units, data=avg)
        # Must re-add loc_units, as it is stripped during get_data_mod
        avg["loc_units"] = pd.Series(
            [self.swath_units for i in range(len(avg.index))], dtype=str
        )
        avgPass.plotCoverage(
            mplWidget=mplWidget, loc_units=self.swath_units, colorize=colorize, d=avg
        )
        if cfg.get_card_plot_average_swath_box():
            # Find average deposition inside swath width
            swath_width = self.swath_adjusted
            a_c = avg[
                (avg["loc"] >= -swath_width / 2) & (avg["loc"] <= swath_width / 2)
            ]
            a_c_mean = a_c["cov"].mean(axis="rows")
            mplWidget.canvas.ax.plot(
                [-swath_width / 2, -swath_width / 2, swath_width / 2, swath_width / 2],
                [0, a_c_mean / 2, a_c_mean / 2, 0],
                color="black",
                linewidth=1,
                dashes=(3, 2),
                label="Effective Swath",
            )
            if not colorize:
                mplWidget.canvas.ax.legend()
            # Must set ylim after plotting
            mplWidget.canvas.ax.set_ylim(bottom=0, auto=None)
            # Plot it
            mplWidget.canvas.draw()

    # Overrides for superclass

    def get_average_mod(self):
        avg = self._get_average()
        avgPass = PassDataCard(name="average")
        avgPass.center = self.center
        avgPass.center_method = self.center_method
        return avgPass.get_data_mod(loc_units=self.swath_units, data=avg)

    def get_average_y_label(self):
        return "cov"
