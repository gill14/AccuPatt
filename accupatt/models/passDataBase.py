import pandas as pd

from accupatt import config as cfg


class PassDataBase:
    def __init__(self, name):
        self._name = name
        self.include_in_composite = True

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str):
        self._name = value

    def has_data(self) -> bool:
        # MUST override in inherited class
        pass

    def center_to_zero(self, d: pd.DataFrame, columnName, center, centerMethod):
        if not center or d.empty:
            return
        if centerMethod == cfg.CENTER_METHOD_CENTROID:
            y = d[columnName]
            c = (y * d["loc"]).sum() / y.sum()
        elif centerMethod == cfg.CENTER_METHOD_COD:
            y = d[columnName].to_numpy()
            x = d["loc"].to_numpy()
            numerator = (y[:-1] * (x[1:] + x[:-1]) + (y[1:] - y[:-1]) * (2 * x[1:] + x[:-1]) / 3).sum()
            denominator = (y[1:] + y[:-1]).sum()
            c = numerator / denominator
        else:
            return
        d["loc"] -= c

    def adapt_location_units(self, d: pd.DataFrame, loc_units):
        if d.empty:
            return
        mask = d["loc_units"] != loc_units
        ft_mask = mask & (d["loc_units"] == cfg.UNIT_FT)
        d.loc[ft_mask, "loc"] /= cfg.FT_PER_M
        d.loc[mask & ~ft_mask, "loc"] *= cfg.FT_PER_M
        d.loc[mask, "loc_units"] = loc_units
