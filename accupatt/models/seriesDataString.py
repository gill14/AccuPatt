import accupatt.config as cfg
import numpy as np
import pandas as pd
from accupatt.models.passData import Pass
from accupatt.models.seriesDataBase import SeriesDataBase


class SeriesDataString(SeriesDataBase):
    def __init__(self, passes: list[Pass], swath: int = 0, swath_adjusted: int = 0, swath_units: str = None):
        super().__init__(passes, swath, swath_adjusted, swath_units)
        # Options
        self.equalize_integrals = True
        self.smooth = True
        self.smooth_window = cfg.get_smooth_window()
        self.smooth_order = cfg.get_smooth_order()
        # Convenience Runtime Placeholder
        self.average = Pass(name="Average")

    def modifyPatterns(self):
        active_passes = [p for p in self.passes if p.string.is_active()]
        if not active_passes:
            return
        self._equalizePatterns(self.equalize_integrals, active_passes)
        self.average.string.smooth = self.smooth
        self.average.string.center = self.center
        self.average.string.center_method = self.center_method
        self.average.string.smooth_window = self.smooth_window
        self.average.string.smooth_order = self.smooth_order
        self.average.string.data = self._averagePattern(active_passes)

    def _equalizePatterns(self, isEqualize: bool, passes: list[Pass]):
        for p in passes:
            p.string.equalize_factor = 1.0
        if not isEqualize:
            return
        dfs = [p.string.get_data_mod(loc_units_override=self.swath_units) for p in passes]
        areas = [
            np.trapezoid(y=d[p.name], x=d["loc"], axis=0)
            for p, d in zip(passes, dfs)
        ]
        area_max = max(areas)
        for p, area in zip(passes, areas):
            p.string.equalize_factor = area_max / area

    def _averagePattern(self, passes: list[Pass]) -> pd.DataFrame:
        average_df = pd.DataFrame()
        for p in passes:
            d = p.string.get_data_mod(loc_units_override=self.swath_units)
            s = d.set_index("loc")[p.name].multiply(p.string.equalize_factor)
            average_df = average_df.join(s, how="outer", lsuffix="_l", rsuffix="_r")
        average_df = average_df.interpolate(limit_area="inside")
        average_df["Average"] = average_df.fillna(0).mean(axis="columns")
        return average_df.reset_index()

    # Overrides for superclass

    def get_average_mod(self):
        return self.average.string.get_data_mod()

    def get_average_y_label(self):
        return "Average"

