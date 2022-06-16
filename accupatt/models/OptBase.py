import accupatt.config as cfg


class OptBase:
    def __init__(self, name):
        self.name = name
        self.center = True
        self.center_method = cfg.get_center_method()
        self.smooth = True
        self.smooth_window = cfg.get_smooth_window()
        self.smooth_order = cfg.get_smooth_order()
