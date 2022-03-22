import uuid
import accupatt.config as cfg
import numpy as np
from accupatt.helpers.atomizationModel import AtomizationModelMulti
from accupatt.models.appInfo import AppInfo
from accupatt.models.passData import Pass
from accupatt.models.seriesStringData import SeriesStringData


class SeriesData:
    """A Container class for storing all Series info"""

    def __init__(self, id = ''):
        self.id = id
        if self.id == '':
            self.id = str(uuid.uuid4())
        self.info = AppInfo()
        self.passes: list[Pass] = []
        self.string = SeriesStringData(self.passes, self.info.swath_units)

    '''
    The methods below are used to convert and calculate info values as needed
    '''
    def calc_airspeed_mean(self, units: str = 'mph', string_included=True, cards_included=True):
        return int(np.mean([p.calc_airspeed(units) for p in self._get_applicable_passes(string_included, cards_included)]))

    def calc_spray_height_mean(self, string_included=True, cards_included=True):
        return float(np.mean([p.spray_height for p in self._get_applicable_passes(string_included, cards_included)]))

    def calc_wind_speed_mean(self, string_included=True, cards_included=True):
        return float(np.mean([p.wind_speed for p in self._get_applicable_passes(string_included, cards_included)]))

    def calc_crosswind_mean(self, string_included=True, cards_included=True):
        return float(np.mean([p.calc_crosswind() for p in self._get_applicable_passes(string_included, cards_included)]))

    def calc_temperature_mean(self, string_included=True, cards_included=True):
        return int(np.mean([p.temperature for p in self._get_applicable_passes(string_included, cards_included)]))

    def calc_humidity_mean(self, string_included=True, cards_included=True):
        return int(np.mean([p.humidity for p in self._get_applicable_passes(string_included, cards_included)]))

    def _get_applicable_passes(self, string_included, cards_included):
        applicablePasses: list[Pass] = []
        for p in self.passes:
            include = True
            if string_included:
                if not p.string_include_in_composite:
                    include = False
            if cards_included:
                if not p.cards_include_in_composite:
                    include = False
            if include:
                applicablePasses.append(p)
        return applicablePasses

    #Convience Accessor so that the model is only run once  
    def calc_droplet_stats(self):
        model = self._populate_model()
        return model.dv01(), model.dv05(), model.dv09(), model.p_lt_100(), model.p_lt_100(), model.dsc(), model.rs()

    #Individual accessors, model re-runs each time.
    def calc_dv01(self):
        return self._populate_model().dv01()

    def calc_dv05(self):
        return self._populate_model().dv05()

    def calc_dv09(self):
        return self._populate_model().dv09()

    def calc_p_lt_100(self):
        return self._populate_model().p_lt_100()

    def calc_p_lt_200(self):
        return self._populate_model().p_lt_200()

    def calc_dsc(self):
        return self._populate_model().dsc()

    def calc_rs(self):
        return self._populate_model().rs()

    def _populate_model(self):
        model = AtomizationModelMulti()
        for n in self.info.nozzles:
            model.addNozzleSet(name=n.type,
                               orifice=n.size,
                               airspeed=self.calc_airspeed_mean(units=cfg.UNIT_MPH),
                               pressure=self.info.get_pressure(units=cfg.UNIT_PSI),
                               angle=n.deflection,
                               quantity=n.quantity)
        return model
        
