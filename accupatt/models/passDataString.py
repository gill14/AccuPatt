import accupatt.config as cfg
import numpy as np
import pandas as pd
import scipy.signal as sig
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
        # self.data_mod = pd.DataFrame()  # Holds data with all requested modifications
        self.data_loc_units = cfg.get_unit_string_data_location()
        # String Data Mod Options
        self.trim_l = 0
        self.trim_r = 0
        self.trim_v = 0.0
        self.rebase = False
        self.equalize_factor = 1.0
        # Processing options
        self.center = True
        self.center_method = cfg.get_center_method()
        self.smooth = True
        self.smooth_window = cfg.get_smooth_window()
        self.smooth_order = cfg.get_smooth_order()

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str):
        old = getattr(self, "_name", None)
        self._name = value
        if old is not None and old != value:
            for df in [
                getattr(self, "data", None),
                getattr(self, "data_ex", None),
            ]:
                if df is not None and not df.empty and old in df.columns:
                    df.rename(columns={old: value}, inplace=True)

    def get_data_mod(self, data=pd.DataFrame(), loc_units_override=None, center_override=None, smooth_override=None) -> pd.DataFrame:
        if data.empty:
            data = self.data.copy()
        data = data.assign(loc_units=self.data_loc_units)
        # Assert location units if provided
        self.adapt_location_units(data, loc_units_override if loc_units_override else self.data_loc_units)
        # Trim it horizontally
        self.trimLR(data, self.trim_l, self.trim_r)
        # Rebase it
        self.rebaseIt(data, self.rebase, self.trim_l, self.trim_r)
        # Trim it vertically
        self.trimV(data, self.trim_v)
        # Center it
        if center_override or (center_override is None and self.center):
            self.center_to_zero(data, self.name, self.center, self.center_method)
        # Smooth it
        if smooth_override or (smooth_override is None and self.smooth):
            self.smoothIt(data, self.smooth, self.smooth_window, self.smooth_order)
        return data
    def trimLR(self, d: pd.DataFrame, trimL: int = 0, trimR: int = 0):
        # Left trimmed points set to -1
        d.loc[d.index[:trimL], self.name] = -1
        # Right trimmed points set to -1
        if trimR > 0:
            d.loc[d.index[(-1 - trimR) :], self.name] = -1
        # Find new min inside untrimmed area
        min_ = self.findMin(d, trimL, trimR)
        # subtract min from all points and clip all negative values (from trimmed areas) to 0
        d[self.name] = d[self.name].sub(min_).clip(lower=0)

    def findMin(self, d: pd.DataFrame, trimL: int = 0, trimR: int = 0) -> float:
        return d[self.name].iloc[trimL : -1 - trimR].min()

    def rebaseIt(
        self, d: pd.DataFrame, isRebase: bool = False, trimL: int = 0, trimR: int = 0
    ):
        if not isRebase:
            return
        # Calculate trimmed/untrimmed distances
        untrimmed_dist = d.at[d.index[-1], "loc"] - d.at[d.index[0], "loc"]
        trimmed_dist = d.at[d.index[-1 - trimR], "loc"] - d.at[d.index[trimL], "loc"]
        # Drop data points outside trimmed area in place
        to_drop = d.index[(d.index < trimL) | (d.index > d.index[-1 - trimR])]
        d.drop(to_drop, inplace=True)
        # Rebase locations according to ratio of untrimmed:trimmed length
        d["loc"] = d["loc"].multiply(untrimmed_dist / trimmed_dist)

    def trimV(self, d: pd.DataFrame, trimV: float = 0.0):
        # Trim Vertical and clip all negative values (from trimmed areas) to 0
        d[self.name] = d[self.name].sub(trimV).clip(lower=0)

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
        # Smooth y vals and clip below 0
        d[self.name] = np.clip(sig.savgol_filter(d[self.name], _window, order), 0, None)

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
            self.data["loc"].shape[0] - self.data["loc"].sub(value).abs().idxmin()
        )

    def user_set_trim_floor(self, value: float):
        # Find minimum y value
        min_y = self.findMin(self.data, self.trim_l, self.trim_r)
        # Set vertical trim as difference between min and user selected floor
        self.trim_v = float(value - min_y) if min_y < value else 0.0

    """
    Convenience
    """

    def has_data(self) -> bool:
        return not self.data.empty

    def is_active(self) -> bool:
        has_data = self.has_data()
        included = self.include_in_composite
        return has_data and included
