import numpy as np
import pandas as pd
import accupatt.config as cfg
from accupatt.models.passDataBase import PassDataBase

from accupatt.models.sprayCard import SprayCard


class PassDataCard(PassDataBase):
    def __init__(self, name):
        super().__init__(name=name)
        # Processing options
        self.center = True
        self.center_method = cfg.get_center_method()
        # Card Data
        self.card_list: list[SprayCard] = []

    def _get_data_from_card_list(self):
        scs: list[SprayCard] = sorted(
            [
                card
                for card in self.card_list
                if card.has_image
                and card.include_in_composite
                and card.location is not None
                and card.location_units is not None
            ],
            key=lambda x: x.location,
        )
        return pd.DataFrame([
            {
                "name": card.name,
                "loc": float(card.location),
                "loc_units": card.location_units,
                cfg.CARD_PLOT_Y_AXIS_COVERAGE: card.stats.get_percent_coverage(),
                cfg.CARD_PLOT_Y_AXIS_DEPOSITION: card.stats.get_deposition(),
                cfg.CARD_PLOT_Y_AXIS_DROPS_PER_IN2: card.stats.get_stains_per_in2(),
                cfg.CARD_PLOT_Y_AXIS_DROPS_PER_CM2: card.stats.get_stains_per_cm2(),
                "dv01": card.stats.get_dv01(),
                "dv05": card.stats.get_dv05(),
                "dv09": card.stats.get_dv09(),
            }
            for card in scs
        ])

    def get_data_mod(self, loc_units, data=pd.DataFrame(), doUnits=True, doCenter=True, y_label: str = None) -> pd.DataFrame:
        if data.empty:
            data = self._get_data_from_card_list()
        if doUnits:
            self.adapt_location_units(data, loc_units)
        if doCenter:
            center_col = y_label if y_label is not None else cfg.get_card_plot_y_axis()
            self.center_to_zero(data, center_col, center=self.center, centerMethod=self.center_method)
        # Do more things potentially...
        return data

    """
    Convenience
    """

    def has_data(self) -> bool:
        return len(self.card_list) > 0

    def is_active(self) -> bool:
        has_data = self.has_data()
        included = self.include_in_composite
        has_included_card = any([sc.include_in_composite for sc in self.card_list])
        return has_data and included and has_included_card
