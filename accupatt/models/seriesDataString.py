from matplotlib.pyplot import table
import accupatt.config as cfg
import numpy as np
import pandas as pd
from accupatt.models.passData import Pass
from accupatt.models.seriesDataBase import SeriesDataBase
from accupatt.widgets.mplwidget import MplWidget
from PyQt6.QtWidgets import QTableWidget
from scipy.stats import variation


class SeriesDataString(SeriesDataBase):
    def __init__(self, passes: list[Pass], target_swath: int, swath_units: str):
        super().__init__(passes, target_swath, swath_units)
        # Options
        self.equalize_integrals = True
        # Convenience Runtime Placeholder
        self.average = Pass(name="Average")

    def modifyPatterns(self):
        active_passes = [p for p in self.passes if p.string.is_active()]
        if len(active_passes) == 0:
            return
        # Apply individual pattern modifications
        for p in active_passes:
            p.string.modifyData(loc_units=self.swath_units)
        # Apply cross-pattern modifications
        self._equalizePatterns(self.equalize_integrals, active_passes)
        # Assign series string options to average Pass
        self.average.string.smooth = self.smooth
        self.average.string.center = self.center
        self.average.string.center_method = self.center_method
        # Generate and assign data to average Pass
        self.average.string.data = self._averagePattern(active_passes)
        self.average.string.smooth_window = self.smooth_window
        self.average.string.smooth_order = self.smooth_order
        # Apply avearge pattern modifications
        self.average.string.modifyData()

    def _equalizePatterns(self, isEqualize: bool, passes: list[Pass]):
        if not isEqualize:
            return
        # Integrate each pattern to find area under the curve
        areas = [
            np.trapz(y=p.string.data_mod[p.name], x=p.string.data_mod["loc"], axis=0)
            for p in passes
        ]
        # Find the pass with the largest integral
        area_max = max(areas)
        # Scale each pass to equalize areas to the maxx above
        for i, p in enumerate(passes):
            p.string.data_mod[p.name] = p.string.data_mod[p.name].multiply(
                area_max / areas[i]
            )

    def _averagePattern(self, passes: list[Pass]) -> pd.DataFrame:
        # df placeholder
        average_df = pd.DataFrame()
        for p in passes:
            s = p.string.data_mod.set_index("loc")[p.name]
            average_df = average_df.join(s, how="outer", lsuffix="_l", rsuffix="_r")
        # average_df.fillna(0)
        # take the column-wise average and add that series to the placeholder
        average_df.interpolate(limit_area="inside", inplace=True)
        average_df["Average"] = average_df.fillna(0).mean(axis="columns")
        average_df = average_df.reset_index()
        return average_df

    """
    Plotting Methods
    """

    def plotOverlay(self, mplWidget: MplWidget):
        # Setup and clear the plotter
        self._config_mpl_plotter(mplWidget)
        # Filter plottable passes
        active_passes = [p for p in self.passes if p.string.is_active()]
        # Iterate over plottable passes
        for p in active_passes:
            # Numpy-ize dataframe columns to plot
            x = np.array(p.string.data_mod["loc"], dtype=float)
            y = np.array(p.string.data_mod[p.name], dtype=float)
            # Plot non-zero data, and label the series with the pass name
            mplWidget.canvas.ax.plot(x[y != 0], y[y != 0], linewidth=1, label=p.name)
        # Add a legend if applicable
        if len(active_passes) > 1:
            mplWidget.canvas.ax.legend()
        # Must set ylim after plotting
        mplWidget.canvas.ax.set_ylim(bottom=0, auto=None)
        # Draw the plot regardless if passes were plotted to it
        mplWidget.canvas.draw()

    def plotAverage(self, mplWidget: MplWidget, swath_width):
        # Setup and clear the plotter
        self._config_mpl_plotter(mplWidget)
        # Convenience accessor to average string modified data
        a = self.average.string.data_mod
        if not a.empty:
            # Numpy-ize dataframe columns to plot
            x = np.array(a["loc"], dtype=float)
            y = np.array(a["Average"], dtype=float)
            # Plot non-zero data, and label the series
            mplWidget.canvas.ax.plot(
                x[y != 0], y[y != 0], color="black", linewidth=2, label="Average"
            )
            mplWidget.canvas.ax.fill_between(x[y != 0], 0, y[y != 0], alpha=0.7)
            if cfg.get_string_plot_average_swath_box():
                # Find average deposition inside swath width
                a_c = a[(a["loc"] >= -swath_width / 2) & (a["loc"] <= swath_width / 2)]
                a_c_mean = a_c["Average"].mean(axis="rows")
                # Plot rectangle, w = swath width, h = (1/2)* average dep inside swath width
                mplWidget.canvas.ax.plot(
                    [
                        -swath_width / 2,
                        -swath_width / 2,
                        swath_width / 2,
                        swath_width / 2,
                    ],
                    [0, a_c_mean / 2, a_c_mean / 2, 0],
                    color="black",
                    linewidth=1,
                    dashes=(3, 2),
                    label="Effective Swath",
                )
            # Add a legend
            mplWidget.canvas.ax.legend()
        # Must set ylim after plotting
        mplWidget.canvas.ax.set_ylim(bottom=0, auto=None)
        # Plot it
        mplWidget.canvas.draw()

    # Overrides for superclass

    def get_average_mod(self):
        return self.average.string.data_mod

    def get_average_y_label(self):
        return "Average"
