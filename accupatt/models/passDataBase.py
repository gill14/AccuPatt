import accupatt.config as cfg

class PassDataBase:
    def __init__(self, name):
        self.name = name
        self.include_in_composite = True
        self.center = True
        self.center_method = cfg.get_center_method()
        self.smooth = True
        self.smooth_window = cfg.get_string_smooth_window()
        self.smooth_order = cfg.get_string_smooth_order()