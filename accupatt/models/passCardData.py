import accupatt.config as cfg

from accupatt.models.sprayCard import SprayCard


class PassCardData:
    def __init__(self):
        # Card Data
        self.card_list: list[SprayCard] = []
        # Card Data Mod options
        self.center = True
        self.center_method = cfg.get_center_method()
