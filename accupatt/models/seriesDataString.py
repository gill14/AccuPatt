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
    def __init__(self, passes: list[Pass]):
        super().__init__(passes)
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

    def plotAverage(self, mplWidget: MplWidget):
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
            _sw = self.swath_adjusted
            if cfg.get_string_plot_average_dash_overlay():
                method = cfg.get_string_plot_average_dash_overlay_method()
                if method == cfg.DASH_OVERLAY_METHOD_ISHA and _sw >= 1:
                    # Plot rectangle, w = swath width, h = (1/2)* average dep inside swath width
                    dash_x = [
                        -_sw / 2,
                        -_sw / 2,
                        _sw / 2,
                        _sw / 2,
                    ]
                    # Find average deposition inside swath width
                    a_c = a[(a["loc"] >= -_sw / 2) & (a["loc"] <= _sw / 2)]
                    a_c_mean = a_c["Average"].mean(axis="rows")
                    dash_y = [0, a_c_mean / 2, a_c_mean / 2, 0]
                    dash_label = "Effective Swath"

                else:
                    dash_x = [a["loc"].iloc[0], a["loc"].iloc[-1]]
                    a_mean = a["Average"].mean(axis="rows")
                    dash_y = [a_mean, a_mean]
                    dash_label = "Average Value"
                mplWidget.canvas.ax.plot(
                    dash_x,
                    dash_y,
                    color="black",
                    linewidth=1,
                    dashes=(3, 2),
                    label=dash_label,
                )
            # Add a legend
            mplWidget.canvas.ax.legend()
        # Must set ylim after plotting
        mplWidget.canvas.ax.set_ylim(bottom=0, auto=None)
        # Plot it
        mplWidget.canvas.draw()

    def plotRacetrack(self, mplWidget: MplWidget):
        self._plotSimulation(mplWidget)

    def plotBackAndForth(self, mplWidget: MplWidget):
        self._plotSimulation(
            mplWidget,
            mirrorAdjascent=True,
        )

    def _plotSimulation(self, mplWidget: MplWidget, mirrorAdjascent=False):
        showEntireWindow = (
            cfg.get_string_simulation_view_window()
            == cfg.STRING_SIMULATION_VIEW_WINDOW_ALL
        )
        super()._plotSimulation(mplWidget, showEntireWindow, mirrorAdjascent)

    # Overrides for superclass

    def get_average_mod(self):
        return self.average.string.data_mod

    def get_average_y_label(self):
        return "Average"

    def _config_mpl_plotter(self, mplWidget: MplWidget):
        super()._config_mpl_plotter(mplWidget)
        mplWidget.canvas.ax.set_yticks([])
