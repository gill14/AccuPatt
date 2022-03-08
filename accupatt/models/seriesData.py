import uuid

import numpy as np
import pandas as pd
import accupatt.config as cfg
from accupatt.helpers.atomizationModel import AtomizationModelMulti
from accupatt.models.appInfo import AppInfo
from accupatt.models.passData import Pass


class SeriesData:
    """A Container class for storing all Series info"""

    def __init__(self, id = ''):
        self.id = id
        if self.id == '':
            self.id = str(uuid.uuid4())
        self.info = AppInfo()
        self.passes = []
        #String Options
        self.string_average_smooth = True
        self.string_equalize_integrals = True
        self.string_average_center_method = cfg.get_center_method()
        self.string_simulated_adjascent_passes = 2
        #Convenience Runtime Placeholders
        self.patternAverage = Pass(name='Average')

    def modifyPatterns(self):
        if all(p.data.empty for p in self.passes):
            return
        # Apply individual pattern modifications
        for p in self.passes:
            if not p.data.empty and p.include_in_composite:
                p.modifyData(loc_units=self.info.swath_units)
        # Apply cross-pattern modifications
        if self.string_equalize_integrals:
            self._equalizePatterns()
        # Assign series string options to average Pass
        self.patternAverage.string_smooth = self.string_average_smooth
        self.patternAverage.string_center_method = self.string_average_center_method
        # Generate and assign data to average Pass
        self._averagePattern()
        #Apply avearge pattern modifications
        self.patternAverage.modifyData()

    def _equalizePatterns(self):
        areas = []
        #Integrate each pattern to find area under the curve
        for p in self.passes:
            area = 0 if p.data.empty or not p.include_in_composite else np.trapz(y=p.data_mod[p.name], x=p.data_mod['loc'], axis=0)
            areas.append(area)
        #Find the pass with the largest integral
        maxx = max(areas)
        #Scale each pass to equalize areas to the maxx above
        for i, p in enumerate(self.passes):
            if not p.data.empty and p.include_in_composite:
                #Calculate scaler and apply to data_mod pattern
                p.data_mod[p.name] = p.data_mod[p.name].multiply(maxx/areas[i])

    def _averagePattern(self):
        #df placeholder
        average = pd.DataFrame()
        #temp df to average accross columns
        d = pd.DataFrame()
        p: Pass
        for p in self.passes:
            #Only include passes checked from listview
            if not p.data.empty and p.include_in_composite:
                #add loc column to placeholder, will be overwritten each time with identical values
                average['loc'] = p.data_mod['loc']
                #add each modified pattern data to temp df
                d[p.name] = p.data_mod[p.name]
        if not average.empty:
            #take the column-wise average and add that series to the placeholder
            average['Average'] = d.mean(axis='columns')
            #copy the placeholder and assign it to the object's previously declared patternAverage object
            self.patternAverage.data = average.copy()

    '''
    The methods below are used to convert and calculate info values as needed
    '''
    def calc_airspeed_mean(self):
        m = []
        for p in self.passes:
            if p.include_in_composite:
                m.append(p.calc_airspeed())
        return int(np.mean(m))

    def calc_spray_height_mean(self):
        m = []
        for p in self.passes:
            if p.include_in_composite:
                m.append(p.spray_height)
        return float(np.mean(m))

    def calc_wind_speed_mean(self):
        m = []
        for p in self.passes:
            if p.include_in_composite:
                m.append(p.wind_speed)
        return float(np.mean(m))

    def calc_crosswind_mean(self):
        m = []
        for p in self.passes:
            if p.include_in_composite:
                m.append(p.calc_crosswind())
        return float(np.mean(m))

    def calc_temperature_mean(self):
        m = []
        for p in self.passes:
            if p.include_in_composite:
                m.append(p.temperature)
        return int(np.mean(m))

    def calc_humidity_mean(self):
        m = []
        for p in self.passes:
            if p.include_in_composite:
                m.append(p.humidity)
        return int(np.mean(m))

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
        
