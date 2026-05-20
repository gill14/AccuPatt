import numpy as np
import pandas as pd
import accupatt.config as cfg
from accupatt.models.passDataCard import PassDataCard
from accupatt.models.passData import Pass
from accupatt.models.seriesDataBase import SeriesDataBase


class SeriesDataCard(SeriesDataBase):
    def __init__(self, passes: list[Pass], swath: int = 0, swath_adjusted: int = 0, swath_units: str = None):
        super().__init__(passes, swath, swath_adjusted, swath_units)

    def _get_active_passes(self) -> list[Pass]:
        activePasses: list[Pass] = []
        for p in self.passes:
            if p.cards.is_active():
                activePasses.append(p)
        return activePasses

    def _get_average(self, y_label: str = None) -> pd.DataFrame:
        active_passes = self._get_active_passes()
        if not active_passes:
            return pd.DataFrame()

        y_axis = y_label if y_label is not None else cfg.get_card_plot_y_axis()
        cols = [
            "loc",
            cfg.CARD_PLOT_Y_AXIS_COVERAGE,
            cfg.CARD_PLOT_Y_AXIS_DEPOSITION,
            cfg.CARD_PLOT_Y_AXIS_DROPS_PER_IN2,
            cfg.CARD_PLOT_Y_AXIS_DROPS_PER_CM2,
            "dv01",
            "dv05",
        ]
        dfs = [
            p.cards.get_data_mod(loc_units=self.swath_units)[cols]
            .set_index("loc")
            .add_suffix(f"_{p.name}")
            for p in active_passes
        ]

        dd = pd.concat(dfs, axis=1).sort_index()
        dd = dd.interpolate(method="slinear", limit_area="inside")

        y_cols = dd.columns[dd.columns.str.contains(y_axis)]
        dd[y_cols] = dd[y_cols].fillna(0)

        avg = pd.DataFrame(index=dd.index)
        avg[y_axis] = dd[y_cols].mean(axis=1)
        avg["dv01"] = dd.loc[:, dd.columns.str.startswith("dv01")].mean(axis=1)
        avg["dv05"] = dd.loc[:, dd.columns.str.startswith("dv05")].mean(axis=1)
        avg["loc_units"] = self.swath_units
        return avg.reset_index()

    # Overrides for superclass

    def get_average_mod(self, y_label: str = None):
        avg = self._get_average(y_label=y_label)
        avgPass = PassDataCard(name="average")
        avgPass.center = self.center
        avgPass.center_method = self.center_method
        return avgPass.get_data_mod(loc_units=self.swath_units, data=avg, y_label=y_label)
    
    def get_average_y_label(self):
        return cfg.get_card_plot_y_axis()
