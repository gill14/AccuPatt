import math
import numpy as np
import pandas as pd
import accupatt.config as cfg
from accupatt.models.passData import Pass
from scipy.stats import variation


class SeriesDataBase:
    def __init__(
        self,
        passes: list[Pass],
        swath: int = 0,
        swath_adjusted: int = 0,
        swath_units: str = None,
    ):
        self.passes = passes
        self.name = "series"
        # Processing options
        self.center = True
        self.center_method = cfg.get_center_method()
        # Options
        self.swath = swath
        self.swath_adjusted = swath_adjusted
        self.swath_units = swath_units or cfg.get_unit_string_data_location()

    def get_average_mod(self):
        """
        This should be overriden by inheriting class
        """
        return pd.DataFrame()

    def get_average_y_label(self):
        """
        This should be overriden by inheriting class
        """

    def set_swath_adjusted(self, string) -> bool:
        try:
            int(float(string))
        except ValueError:
            return False
        self.swath_adjusted = int(float(string))
        return True

    def _calcCV(
        self,
        average_df: pd.DataFrame,
        average_y_label: str,
        swath_width: float,
        mirrorAdjacent=False,
    ):
        xfill, y_fills, _ = self._get_fill_arrays(
            swath_width=swath_width,
            average_df=average_df,
            average_y_label=average_y_label,
            mirrorAdjacent=mirrorAdjacent,
        )
        y_fill_cum = np.zeros(xfill.size)
        for y_fill in y_fills:
            y_fill_cum = y_fill_cum + y_fill
        # Find average deposition inside swath width
        y_fill_cum_center = y_fill_cum[
            np.where(((xfill >= -swath_width / 2) & (xfill <= swath_width / 2)))
        ]
        return round(variation(y_fill_cum_center, axis=0) * 100)

    def _get_fill_arrays(
        self,
        swath_width: float,
        average_df: pd.DataFrame,
        average_y_label: str,
        mirrorAdjacent=False,
    ) -> tuple[np.array, list[np.array], list[str]]:
        """
        Returns xfill, yfills[], labels
        """
        # Original average data
        x0 = np.array(average_df["loc"], dtype=float)
        y0 = np.array(average_df[average_y_label], dtype=float)
        # create a shifted x array for each simulated pass with labels
        x_arrays = [x0]
        y_arrays = [y0]
        labels = ["Measured"]
        half_width = (x0[-1] - x0[0]) / 2 if x0.size > 1 else 0
        n = min(math.ceil(half_width / swath_width) if swath_width > 0 else 1, 50)
        for i in range(1, n + 1):
            x = (x0 * -1)[::-1] if mirrorAdjacent and i % 2 != 0 else x0
            y = y0[::-1] if mirrorAdjacent and i % 2 != 0 else y0
            x_arrays.append(x - (i * swath_width))
            y_arrays.append(y)
            labels.append(f"{i} SW Left")
            x_arrays.append(x + (i * swath_width))
            y_arrays.append(y)
            labels.append(f"{i} SW Right")
        # Unify the x-domain
        xfill = np.sort(np.concatenate(x_arrays))
        # Interpolate the original y-values to the new x-domain
        y_fills = []
        for x, y in zip(x_arrays, y_arrays):
            y_fills.append(np.interp(xfill, x, y, left=0, right=0))
        return (xfill, y_fills, labels)

