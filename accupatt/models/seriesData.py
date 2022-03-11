import uuid

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
    def calc_airspeed_mean(self):
        return int(np.mean([p.calc_airspeed() for p in self.passes if p.include_in_composite()]))

    def calc_spray_height_mean(self):
        return float(np.mean([p.spray_height for p in self.passes if p.include_in_composite()]))

    def calc_wind_speed_mean(self):
        return float(np.mean([p.wind_speed for p in self.passes if p.include_in_composite()]))

    def calc_crosswind_mean(self):
        return float(np.mean([p.calc_crosswind() for p in self.passes if p.include_in_composite()]))

    def calc_temperature_mean(self):
        return int(np.mean([p.temperature for p in self.passes if p.include_in_composite()]))

    def calc_humidity_mean(self):
        return int(np.mean([p.humidity for p in self.passes if p.include_in_composite()]))

    #Convience Accessor so that the model is only run once  
    def calc_droplet_stats(self):
        model = self._populate_model()
        return model.dv01(), model.dv05(), model.dv09(), model.p_lt_100(), model.p_lt_100(), model.dsc(), model.rs()

    #Individual accessors, model re-runs each time.
    def calc_dv01(self):
        model = self._populate_model()
        return model.dv01()

    def calc_dv05(self):
        model = self._populate_model()
        return model.dv05()

    def calc_dv09(self):
        model = self._populate_model()
        return model.dv09()

    def calc_p_lt_100(self):
        model = self._populate_model()
        return model.p_lt_100()

    def calc_p_lt_200(self):
        model = self._populate_model()
        return model.p_lt_200()

    def calc_dsc(self):
        model = self._populate_model()
        return model.dsc()

    def calc_rs(self):
        model = self._populate_model()
        return model.rs()

    def _populate_model(self):
        model = AtomizationModelMulti()
        for n in self.info.nozzles:
            model.addNozzleSet(name=n.type,
                               orifice=n.size,
                               airspeed=self.calc_airspeed_mean(),
                               pressure=self.info.pressure,
                               angle=n.deflection,
                               quantity=n.quantity)
        return model
        
