import accupatt.config as cfg
import numpy as np
import pandas as pd
from accupatt.models.passData import Pass
from accupatt.widgets.mplwidget import MplWidget
from PyQt6.QtWidgets import QTableWidget
from scipy.stats import variation


class SeriesStringData:
    def __init__(self, passes: list[Pass], swath_units: str):
        # Live feeds from Series Object
        self.passes = passes
        self.swath_units = swath_units
        # Options
        self.smooth = True
        self.smooth_window = cfg.get_string_smooth_window()
        self.smooth_order = cfg.get_string_smooth_order()
        self.equalize_integrals = True
        self.center = True
        self.center_method = cfg.get_center_method()
        self.simulated_adjascent_passes = 2
        # Convenience Runtime Placeholder
        self.average = Pass(name="Average")

    def modifyPatterns(self):
        active_passes = [
            p
            for p in self.passes
            if p.string_include_in_composite and p.has_string_data()
        ]
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
        active_passes = [
            p
            for p in self.passes
            if p.string_include_in_composite and p.has_string_data()
        ]
        # Iterate over plottable passes
        for p in active_passes:
            # Numpy-ize dataframe columns to plot
            x = np.array(p.string.data_mod["loc"], dtype=float)
            y = np.array(p.string.data_mod[p.name], dtype=float)
            # Plot non-zero data, and label the series with the pass name
            mplWidget.canvas.ax.plot(x[y != 0], y[y != 0], label=p.name)
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
            # Find average deposition inside swath width
            a_c = a[(a["loc"] >= -swath_width / 2) & (a["loc"] <= swath_width / 2)]
            a_c_mean = a_c["Average"].mean(axis="rows")
            # Plot rectangle, w = swath width, h = (1/2)* average dep inside swath width
            mplWidget.canvas.ax.fill_between(
                [-swath_width / 2, swath_width / 2],
                0,
                a_c_mean / 2,
                facecolor="black",
                alpha=0.25,
                label="Effective Swath",
            )
            # Numpy-ize dataframe columns to plot
            x = np.array(a["loc"], dtype=float)
            y = np.array(a["Average"], dtype=float)
            # Plot non-zero data, and label the series
            mplWidget.canvas.ax.plot(
                x[y != 0], y[y != 0], color="black", linewidth=3, label="Average"
            )
            # Add a legend
            mplWidget.canvas.ax.legend()
        # Must set ylim after plotting
        mplWidget.canvas.ax.set_ylim(bottom=0, auto=None)
        # Plot it
        mplWidget.canvas.draw()

    def plotRacetrack(
        self, mplWidget: MplWidget, swath_width: float, showEntireWindow=False
    ):
        self._plotSimulation(
            mplWidget, swath_width, showEntireWindow, label="Racetrack"
        )

    def plotBackAndForth(
        self, mplWidget: MplWidget, swath_width: float, showEntireWindow=False
    ):
        self._plotSimulation(
            mplWidget,
            swath_width,
            showEntireWindow,
            mirrorAdjascent=True,
            label="Back & Forth",
        )

    def _plotSimulation(
        self,
        mplWidget: MplWidget,
        swath_width: float,
        showEntireWindow=False,
        mirrorAdjascent=False,
        label="",
    ):
        # Setup and clear the plotter
        self._config_mpl_plotter(mplWidget)
        # Convenience accessor to average string modified data
        a = self.average.string.data_mod
        if not a.empty:
            # Original average data
            x0 = np.array(a["loc"], dtype=float)
            y0 = np.array(a["Average"], dtype=float)
            # create a shifted x array for each simulated pass with labels
            x_arrays = [x0]
            y_arrays = [y0]
            labels = ["Center"]
            for i in range(1, self.simulated_adjascent_passes + 1):
                x = (x0*-1)[::-1] if mirrorAdjascent and i % 2 != 0 else x0
                y = y0[::-1] if mirrorAdjascent and i % 2 != 0 else y0
                x_arrays.append(x-(i*swath_width))
                y_arrays.append(y)
                labels.append(f"Left {i}")
                x_arrays.append(x+(i*swath_width))
                y_arrays.append(y)
                labels.append(f"Right {i}")
            # Unify the x-domain
            xfill = np.sort(np.concatenate(x_arrays))
            # Interpolate the original y-values to the new x-domain
            y_fills = []
            for i in range(len(x_arrays)):
                y_fills.append(
                    np.interp(xfill, x_arrays[i], y_arrays[i], left=0, right=0)
                )
            # Plot the fills cumulatively in order of generation: C, L1, R1, L2, R2, etc.
            y_fill_cum = np.zeros(xfill.size)
            for i in range(len(y_fills)):
                mplWidget.canvas.ax.fill_between(
                    xfill, y_fill_cum, y_fill_cum + y_fills[i], label=labels[i]
                )
                y_fill_cum = y_fill_cum + y_fills[i]
            # Plot a solid line on the cumulative deposition
            mplWidget.canvas.ax.plot(xfill, y_fill_cum, color="black")
            # Find average deposition inside swath width
            avg = np.mean(
                y_fill_cum[
                    np.where(((xfill >= -swath_width / 2) & (xfill <= swath_width / 2)))
                ]
            )
            mplWidget.canvas.ax.plot(
                [-swath_width / 2, swath_width / 2],
                [avg, avg],
                color="black",
                dashes=[5, 5],
                label="Mean Dep.",
            )
            # Legend
            mplWidget.canvas.ax.legend(loc="center left", bbox_to_anchor=(1, 0.5))
            # Y Label
            mplWidget.canvas.ax.set_ylabel(label)
            # Whether to show the whole window or one swath width
            if not showEntireWindow:
                mplWidget.canvas.ax.set_xlim(-swath_width / 2, swath_width / 2)
            # Must set ylim after plotting
            mplWidget.canvas.ax.set_ylim(bottom=0, auto=None)
            # Plot it
            mplWidget.canvas.draw()

    def _config_mpl_plotter(self, mplWidget: MplWidget):
        mplWidget.canvas.ax.clear()
        mplWidget.canvas.ax.set_xlabel(f"Location ({self.swath_units})")
        mplWidget.canvas.ax.set_yticks([])

    def plotCVTable(self, tableWidget: QTableWidget, swath_width: float):
        # Convenience accessor to average string modified data
        a = self.average.string.data_mod
        # Simulate various Swath Widths, incrimenting by 2 units (-/+) from the center
        for row in range(tableWidget.rowCount()):
            item_sw = tableWidget.item(row, 0)
            item_rt = tableWidget.item(row, 1)
            item_bf = tableWidget.item(row, 2)
            if a.empty:
                item_sw.setText("-")
                item_rt.setText("-")
                item_bf.setText("-")
                continue
            # Print swath width
            _sw = swath_width - (tableWidget.rowCount() - 1) + (2 * row)
            item_sw.setText(f"{_sw} {self.swath_units}")
            # Calc and Print RT CV
            rt_cv = self.calcCV(_sw, False)
            item_rt.setText(f"{rt_cv} %")
            # Calc and Print BF CV
            bf_cv = self.calcCV(_sw, True)
            item_bf.setText(f"{bf_cv} %")

    def calcCV(self, swath_width: float, mirrorAdjascent=False):
        # Convenience accessor to average string modified data
        a = self.average.string.data_mod
        # Original average data
        x0 = np.array(a["loc"], dtype=float)
        y0 = np.array(a["Average"], dtype=float)
        # create a shifted x array for each simulated pass with labels
        x_arrays = [x0]
        y_arrays = [y0]
        labels = ["Center"]
        for i in range(1, self.simulated_adjascent_passes + 1):
            x = (x0*-1)[::-1] if mirrorAdjascent and i % 2 != 0 else x0
            y = y0[::-1] if mirrorAdjascent and i % 2 != 0 else y0
            x_arrays.append(x-(i*swath_width))
            y_arrays.append(y)
            labels.append(f"Left {i}")
            x_arrays.append(x+(i*swath_width))
            y_arrays.append(y)
            labels.append(f"Right {i}")
        # Unify the x-domain
        xfill = np.sort(np.concatenate(x_arrays))
        # Interpolate the original y-values to the new x-domain
        y_fills = []
        for i in range(len(x_arrays)):
            y_fills.append(np.interp(xfill, x_arrays[i], y_arrays[i], left=0, right=0))
        # Plot the fills cumulatively in order of generation: C, L1, R1, L2, R2, etc.
        y_fill_cum = np.zeros(xfill.size)
        for i in range(len(y_fills)):
            y_fill_cum = y_fill_cum + y_fills[i]
        # Find average deposition inside swath width
        y_fill_cum_center = y_fill_cum[
            np.where(((xfill >= -swath_width / 2) & (xfill <= swath_width / 2)))
        ]
        return round(variation(y_fill_cum_center, axis=0) * 100)
