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
        y_index = "dep" if cfg.get_card_plot_y_axis()==cfg.CARD_PLOT_Y_AXIS_DEPOSITION else "cov"
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
            if y_index in col:
                dd[col].fillna(0, inplace=True)
        dd[f"{y_index}_avg"] = dd.loc[:, dd.columns.str.contains(y_index)].mean(axis="columns")
        dd["dv01_avg"] = dd.loc[:, dd.columns.str.contains("dv01")].mean(axis="columns")
        dd["dv05_avg"] = dd.loc[:, dd.columns.str.contains("dv05")].mean(axis="columns")
        dd["loc_units"] = [self.swath_units for i in range(len(dd.index))]
        avg = dd.loc[:, [f"{y_index}_avg", "dv01_avg", "dv05_avg", "loc_units"]].reset_index()
        avg.rename(
            columns={f"{y_index}_avg": y_index, "dv01_avg": "dv01", "dv05_avg": "dv05"},
            inplace=True,
        )
        return avg

    def plotOverlay(self, mplWidget: MplWidget):
        y_index = "dep" if cfg.get_card_plot_y_axis()==cfg.CARD_PLOT_Y_AXIS_DEPOSITION else "cov"
        # Setup and clear the plotter
        self._config_mpl_plotter(mplWidget)
        ylab = cfg.get_card_plot_y_axis().capitalize()
        if y_index=="dep":
            ylab = ylab + f" ({cfg.get_unit_rate()})"
        elif y_index=="cov":
            ylab = ylab + f" (%)"
        mplWidget.canvas.ax.set_ylabel(ylab)
        active_passes = self._get_active_passes()
        # Iterate over plottable passes
        for p in active_passes:
            data = p.cards.get_data_mod(loc_units=self.swath_units)
            # Numpy-ize dataframe columns to plot
            x = np.array(data["loc"], dtype=float)
            y = np.array(data[y_index], dtype=float)
            # Plot non-zero data, and label the series with the pass name
            mplWidget.canvas.ax.plot(x[y != 0], y[y != 0], linewidth=1, label=p.name)
        # Add a legend if applicable
        if len(active_passes) > 1:
            mplWidget.canvas.ax.legend()
        # Must set ylim after plotting
        mplWidget.canvas.ax.set_ylim(bottom=0, auto=None)
        # Draw the plot regardless if passes were plotted to it
        mplWidget.canvas.draw()

    def plotAverage(self, mplWidget: MplWidget):
        y_index = "dep" if cfg.get_card_plot_y_axis()==cfg.CARD_PLOT_Y_AXIS_DEPOSITION else "cov"
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
        avgPass.plot(
            mplWidget=mplWidget, loc_units=self.swath_units, d=avg
        )
        if cfg.get_card_plot_average_dash_overlay():
            method = cfg.get_card_plot_average_dash_overlay_method()
            if method == cfg.DASH_OVERLAY_METHOD_ISHA:
                # Find average deposition inside swath width
                swath_width = self.swath_adjusted
                dash_x = [-swath_width / 2, -swath_width / 2, swath_width / 2, swath_width / 2]
                a_c = avg[
                    (avg["loc"] >= -swath_width / 2) & (avg["loc"] <= swath_width / 2)
                ]
                a_c_mean = a_c[y_index].mean(axis="rows")
                dash_y = [0, a_c_mean / 2, a_c_mean / 2, 0]
                dash_label = "Effective Swath"
            else:
                dash_x = [avg["loc"].iloc[0], avg["loc"].iloc[-1]]
                a_mean = avg[y_index].mean(axis="rows")
                dash_y = [a_mean, a_mean]
                dash_label = f"Avg. {cfg.get_card_plot_y_axis().capitalize()}"
            mplWidget.canvas.ax.plot(
                    dash_x,
                    dash_y,
                    color="black",
                    linewidth=1,
                    dashes=(3, 2),
                    label=dash_label,
                )
            if not cfg.get_card_plot_shading():
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
        return "dep" if cfg.get_card_plot_y_axis()==cfg.CARD_PLOT_Y_AXIS_DEPOSITION else "cov"
