from PyQt5.QtCore import QSettings


class SprayCardSpreadFactors:

    METHOD_NONE = 0
    METHOD_DIRECT = 1
    METHOD_ADAPTIVE = 2

    def __init__(self):
        #Load in Settings
        self.settings = QSettings('BG Application Consulting','AccuPatt')
        self.method = self.settings.value('spread_factor_method', defaultValue=self.METHOD_ADAPTIVE, type=int)
        self.factor_a = self.settings.value('spread_factor_a', defaultValue=0.0, type=float)
        self.factor_b = self.settings.value('spread_factor_b', defaultValue=0.0009, type=float)
        self.factor_c = self.settings.value('spread_factor_c', defaultValue=1.6333, type=float)

    def stain_dia_to_drop_dia(self, stain_dia):
        if self.method == self.METHOD_DIRECT:
            return self.factor_a * stain_dia * stain_dia + self.factor_b * stain_dia + self.factor_c
        elif self.method == self.METHOD_ADAPTIVE:
            return stain_dia / (self.factor_a * stain_dia * stain_dia + self.factor_b * stain_dia + self.factor_c)
        return stain_dia