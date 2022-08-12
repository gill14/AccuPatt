import accupatt.config as cfg
import numpy as np
import pandas as pd
import scipy.signal as sig
from pyqtgraph import InfiniteLine, PlotWidget, setConfigOptions
from pyqtgraph.functions import mkPen
from accupatt.models.dye import Dye

from accupatt.models.passDataBase import PassDataBase


class PassDataString(PassDataBase):
    def __init__(self, name):
        super().__init__(name=name)
        # String Data Collection
        self.dye = Dye.fromConfig()
        # String Data
        self.data_ex = pd.DataFrame()  # Holds Excitation Data
        self.data = pd.DataFrame()  # Holds original Data
        self.data_mod = pd.DataFrame()  # Holds data with all requested modifications
        self.data_loc_units = cfg.get_unit_data_location()
        # String Data Mod Options
        self.trim_l = 0
        self.trim_r = 0
        self.trim_v = 0.0
        self.rebase = False

    def modifyData(self, loc_units=None):
        if self.data.empty:
            return
        self.data_mod = self.data.copy()
        # Assert location units if provided
        self.reLoc(self.data_mod, loc_units)
        # Trim it horizontally
        self.trimLR(self.data_mod, self.trim_l, self.trim_r)
        # Rebase it
        self.rebaseIt(self.data_mod, self.rebase, self.trim_l, self.trim_r)
        # Trim it vertically
        self.trimV(self.data_mod, self.trim_v)
        # Center it
        self.centerify(self.data_mod, self.center, self.center_method)
        # Smooth it
        self.smoothIt(self.data_mod, self.smooth, self.smooth_window, self.smooth_order)

    def reLoc(self, d: pd.DataFrame, loc_units: str = None):
        if loc_units == None or loc_units == self.data_loc_units:
            return
        if loc_units == cfg.UNIT_FT:
            # Convert loc from M to FT
            d["loc"] = d["loc"].multiply(cfg.FT_PER_M)
        else:
            # Convert loc from FT to M
            d["loc"] = d["loc"].divide(cfg.FT_PER_M)

    def trimLR(self, d: pd.DataFrame, trimL: int = 0, trimR: int = 0):
        # Left trimmed points set to -1
        d.loc[d.index[:trimL], self.name] = -1
        # Right trimmed points set to -1
        d.loc[d.index[(-1 - trimR) :], self.name] = -1
        # Find new min inside untrimmed area
        min = self.findMin(d, trimL, trimR)
        # subtract min from all points
        d[self.name] = d[self.name].sub(min)
        # clip all negative values (from trimmed areas) to 0
        d[self.name] = d[self.name].clip(lower=0)

    def findMin(self, d: pd.DataFrame, trimL: int = 0, trimR: int = 0) -> float:
        return d[trimL : -1 - trimR][self.name].min()

    def rebaseIt(
        self, d: pd.DataFrame, isRebase: bool = False, trimL: int = 0, trimR: int = 0
    ):
        if not isRebase:
            return
        # Calculate trimmed/untrimmed distances
        untrimmed_dist = d.at[d.index[-1], "loc"] - d.at[d.index[0], "loc"]
        trimmed_dist = d.at[d.index[-1 - trimR], "loc"] - d.at[d.index[trimL], "loc"]
        # Drop data points outside trimmed area
        d.drop(d[d.index < trimL].index, inplace=True)
        d.drop(d[d.index > d.index[-1 - trimR]].index, inplace=True)
        # Rebase locations according to ratio of untrimmed:trimmed length
        d["loc"] = d["loc"].multiply(untrimmed_dist / trimmed_dist)

    def trimV(self, d: pd.DataFrame, trimV: float = 0.0):
        # Trim Vertical
        d[self.name] = d[self.name].sub(trimV)
        # clip all negative values (from trimmed areas) to 0
        d[self.name] = d[self.name].clip(lower=0)

    def centerify(self, d: pd.DataFrame, center, centerMethod):
        if not center:
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
        return (d[self.name] * d["loc"]).sum() / d[self.name].sum()

    def _calcCenterOfDistribution(self, d: pd.DataFrame):
        sumNumerator = 0.0
        sumDenominator = 0.0
        for i in range(0, len(d.index) - 1, 1):
            D = d.at[i, self.name]
            Dn = d.at[i + 1, self.name]
            X = d.at[i, "loc"]
            Xn = d.at[i + 1, "loc"]
            # Calc Numerator and add to summation
            sumNumerator += D * (Xn + X) + (Dn - D) * (2 * Xn + X) / 3
            sumDenominator += Dn + D
        # Calc and return CoD
        return sumNumerator / sumDenominator

    def smoothIt(self, d: pd.DataFrame, isSmooth: bool, window: float, order: int):
        if not isSmooth:
            return
        # Calculate the integer smoothing window
        _window = int(
            np.ceil(
                np.abs(d["loc"].abs().idxmin() - d["loc"].sub(window).abs().idxmin())
            )
        )
        # Round it up to the next odd integer if needed
        _window = _window + 1 if _window % 2 == 0 else _window
        # Smooth y vals
        d[self.name] = sig.savgol_filter(d[self.name], _window, order)
        # Clip y vals below 0
        d[self.name] = d[self.name].clip(lower=0)

    def setData(self, x_data, y_data, y_ex_data):
        self.data = pd.DataFrame(
            data=list(zip(x_data, y_data)), columns=["loc", self.name]
        )
        self.data_ex = pd.DataFrame(
            data=list(zip(x_data, y_ex_data)), columns=["loc", self.name]
        )

    """
    Methods to convert ui-set trim values to object values and set them to this object
    """

    def user_set_trim_left(self, value: float):
        # Takes a location domained trim value and converts it to an integer number of points
        self.trim_l = int(self.data["loc"].sub(value).abs().idxmin())

    def user_set_trim_right(self, value: float):
        # Takes a location domained trim value and converts it to an integer number of points
        self.trim_r = int(
            self.data["loc"].shape[0] - abs(self.data["loc"] - value).idxmin()
        )

    def user_set_trim_floor(self, value: float):
        # Find minimum y value
        min_y = self.findMin(self.data, self.trim_l, self.trim_r)
        # Set vertical trim as difference between min and user selected floor
        self.trim_v = float(value - min_y) if min_y < value else 0.0

    """
    Plotting Methods
    """

    def plotIndividual(
        self, pyqtplotwidget: PlotWidget
    ) -> tuple[InfiniteLine, InfiniteLine, InfiniteLine]:
        # Setup Plotter and clear
        self._config_pypqt_plotter(pyqtplotwidget)
        # Only proceed if data exists
        if self.data.empty:
            return None, None, None
        # Calculate min y val for use with trim_vertical handle
        min = self.findMin(self.data, self.trim_l, self.trim_r)
        # Numpy-ize dataframe columns for plotting
        x = np.array(self.data["loc"].values, dtype=float)
        y = np.array(self.data[self.name].values, dtype=float)
        floor = min + self.trim_v
        # Plot raw data
        pyqtplotwidget.plotItem.plot(name="Raw", pen="w").setData(x, y)
        # Create L, R and V trim handles
        trim_left = InfiniteLine(
            pos=x[0 + self.trim_l],
            movable=True,
            pen="y",
            hoverPen=mkPen("y", width=3),
            label="Trim L = {value:0.2f}",
            labelOpts={"color": "y", "position": 0.9},
        )
        trim_right = InfiniteLine(
            pos=x[-1 - self.trim_r],
            movable=True,
            pen="y",
            hoverPen=mkPen("y", width=3),
            label="Trim R = {value:0.2f}",
            labelOpts={"color": "y", "position": 0.9},
        )
        trim_vertical = InfiniteLine(
            pos=floor,
            angle=0,
            movable=True,
            pen="y",
            hoverPen=mkPen("y", width=3),
            label="Floor = {value:0.2f}",
            labelOpts={"color": "y", "position": 0.5},
        )
        # Add trim handles to plot
        pyqtplotwidget.addItem(trim_left)
        pyqtplotwidget.addItem(trim_right)
        pyqtplotwidget.addItem(trim_vertical)
        # Return Trim Handles to parent widget so that user can interact with them
        return trim_left, trim_right, trim_vertical

    def plotIndividualTrim(self, pyqtplotwidget: PlotWidget):
        # Setup Plotter and clear
        self._config_pypqt_plotter(pyqtplotwidget)
        # Only proceed if data exists
        if self.data.empty:
            return
        # Copy dataframes for non-destructive use
        data = self.data.copy()
        data_mod = data.copy()
        # Trim and Rebase
        self.trimLR(data_mod, self.trim_l, self.trim_r)
        self.rebaseIt(data_mod, self.rebase, self.trim_l, self.trim_r)
        self.trimV(data_mod, self.trim_v)
        # Numpy-ize dataframe columns for plotting
        x = np.array(data_mod["loc"].values, dtype=float)
        y = np.array(data_mod[self.name].values, dtype=float)
        # Label modifier for if rebasing is utilized
        rebase_str = ", Rebased" if self.rebase else ""
        # Plot trimmed/rebased data
        pyqtplotwidget.plotItem.plot(name=f"Trimmed{rebase_str}", pen="w").setData(
            x[y != 0], y[y != 0]
        )
        # Only plot smoothed version if enabled for pass
        if self.smooth:
            self.smoothIt(data_mod, self.smooth, self.smooth_window, self.smooth_order)
            # Numpy-ize dataframe column for plotting
            y_smooth = np.array(data_mod[self.name].values, dtype=float)
            trim_mask = np.nonzero(y_smooth)[0]
            y_smooth[0 : trim_mask[0]] = np.nan
            y_smooth[trim_mask[-1] : -1] = np.nan
            # Plot trimmed/rebased/smoothed data
            pyqtplotwidget.plotItem.plot(
                name=f"Trimmed{rebase_str}, Smoothed", pen=mkPen("y", width=3)
            ).setData(x[y != 0], y_smooth[y != 0])

    def _config_pypqt_plotter(self, pyqtplotwidget: PlotWidget):
        setConfigOptions(antialias=True, background="k", foreground="w")
        pyqtplotwidget.plotItem.clear()
        pyqtplotwidget.plotItem.setLabel(
            axis="bottom", text="Location", units=self.data_loc_units
        )
        pyqtplotwidget.plotItem.setLabel(axis="left", text="Dye Intensity")
        pyqtplotwidget.plotItem.showGrid(x=True, y=True)
        pyqtplotwidget.plotItem.addLegend(offset=(5, 5))

    """
    Conveneince
    """

    def has_data(self) -> bool:
        return not self.data.empty

    def is_active(self) -> bool:
        has_data = self.has_data()
        included = self.include_in_composite
        return has_data and included
