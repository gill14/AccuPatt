import numpy as np
import pandas as pd
import accupatt.config as cfg
from accupatt.models.OptBase import OptBase
from accupatt.models.passData import Pass
from accupatt.widgets.mplwidget import MplWidget
from scipy.stats import variation

from PyQt6.QtWidgets import QTableWidget

class SeriesDataBase(OptBase):
    def __init__(self, passes: list[Pass], target_swath: int, swath_units: str):
        super().__init__(name='series')
        self.passes = passes
        self.swath_units = swath_units
        self.swath_adjusted = target_swath if target_swath > 0 else 50
        # Options
        self.swath_adjusted = target_swath if target_swath > 0 else 50
        self.simulated_adjascent_passes = 2
        
    def get_average_mod(self):
        '''
        This should be overriden by inheriting class
        '''
        return pd.DataFrame()    
    
    def get_average_y_label(self):
        '''
        This should be overriden by inheriting class
        '''
        
    def set_swath_adjusted(self, string) -> bool:
        try:
            int(float(string))
        except ValueError:
            return False
        self.swath_adjusted = int(float(string))
        return True
    
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
        self._config_mpl_plotter(mplWidget)
        average_df = self.get_average_mod()
        average_y_label = self.get_average_y_label()
        if not average_df.empty:
            xfill, y_fills, labels = self._get_fill_arrays(swath_width=swath_width,
                                  average_df=average_df,
                                  average_y_label=average_y_label,
                                  mirrorAdjascent=mirrorAdjascent)
            # Plot the fills cumulatively in order of generation: C, L1, R1, L2, R2, etc.
            y_fill_cum = np.zeros(xfill.size)
            for i in range(len(y_fills)):
                mplWidget.canvas.ax.fill_between(
                    xfill, y_fill_cum, y_fill_cum + y_fills[i], label=labels[i], alpha=0.8
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
    
    def plotCVTable(self, tableWidget: QTableWidget, swath_width: float):
        average_df = self.get_average_mod()
        average_y_label = self.get_average_y_label()
        # Simulate various Swath Widths, incrimenting by 2 units (-/+) from the center
        for row in range(tableWidget.rowCount()):
            item_sw = tableWidget.item(row, 0)
            item_rt = tableWidget.item(row, 1)
            item_bf = tableWidget.item(row, 2)
            if average_df.empty:
                item_sw.setText("-")
                item_rt.setText("-")
                item_bf.setText("-")
                continue
            # Print swath width
            _sw = swath_width - (tableWidget.rowCount() - 1) + (2 * row)
            item_sw.setText(f"{_sw} {self.swath_units}")
            # Calc and Print RT CV
            rt_cv = self._calcCV(average_df, average_y_label, _sw, False)
            item_rt.setText(f"{rt_cv} %")
            # Calc and Print BF CV
            bf_cv = self._calcCV(average_df, average_y_label, _sw, True)
            item_bf.setText(f"{bf_cv} %")
    
    def _calcCV(self, average_df: pd.DataFrame, average_y_label: str, swath_width: float, mirrorAdjascent=False):
        xfill, y_fills, _ = self._get_fill_arrays(swath_width=swath_width,
                              average_df=average_df,
                              average_y_label=average_y_label,
                              mirrorAdjascent=mirrorAdjascent)
        y_fill_cum = np.zeros(xfill.size)
        for i in range(len(y_fills)):
            y_fill_cum = y_fill_cum + y_fills[i]
        # Find average deposition inside swath width
        y_fill_cum_center = y_fill_cum[
            np.where(((xfill >= -swath_width / 2) & (xfill <= swath_width / 2)))
        ]
        return round(variation(y_fill_cum_center, axis=0) * 100)
        
        
    
    def _get_fill_arrays(self, swath_width: float, average_df: pd.DataFrame, average_y_label: str, mirrorAdjascent=False,) -> tuple[np.array, list[np.array], list[str]]:
        '''
        Returns xfill, yfills[], labels
        '''
        # Original average data
        x0 = np.array(average_df["loc"], dtype=float)
        y0 = np.array(average_df[average_y_label], dtype=float)
        # create a shifted x array for each simulated pass with labels
        x_arrays = [x0]
        y_arrays = [y0]
        labels = ["Center"]
        for i in range(1, self.simulated_adjascent_passes + 1):
            x = (x0 * -1)[::-1] if mirrorAdjascent and i % 2 != 0 else x0
            y = y0[::-1] if mirrorAdjascent and i % 2 != 0 else y0
            x_arrays.append(x - (i * swath_width))
            y_arrays.append(y)
            labels.append(f"Left {i}")
            x_arrays.append(x + (i * swath_width))
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
        return (xfill, y_fills, labels)
    
    def _config_mpl_plotter(self, mplWidget: MplWidget):
        mplWidget.canvas.ax.clear()
        mplWidget.canvas.ax.set_xlabel(f"Location ({self.swath_units})")
        mplWidget.canvas.ax.set_yticks([])