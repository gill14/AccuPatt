import uuid
import pandas as pd
import numpy as np

from accupatt.helpers.atomizationModel import AtomizationModel, AtomizationModelMulti

from accupatt.models.appInfo import AppInfo
from accupatt.models.passData import Pass


class SeriesData:
    """A Container class for storing all Series info"""

    def __init__(self, id = ''):
        self.id = id
        if self.id == '':
            self.id = str(uuid.uuid4())
        self.filePath = ''
        self.info = AppInfo()
        self.passes = []
        #String Options
        self.string_smooth_individual = True
        self.string_smooth_average = True
        self.string_equalize_integrals = True
        self.string_center = True
        self.string_simulated_adjascent_passes = 2
        
        #Convenience Runtime Placeholders
        self.patternAverage = Pass(name='Average')

    def modifyPatterns(self):
        #apply individual pattern modifications
        for p in self.passes:
            if p.data.empty: continue
            p.modifyData(isCenter=self.string_center, isSmooth=self.string_smooth_individual)
        #apply cross-pattern modifications
        if self.string_equalize_integrals:
            self._equalizePatterns()
        #Generate Average Pattern
        self._averagePattern()
        #Apply avearge pattern modifications
        self.patternAverage.modifyData(isCenter=self.string_center, isSmooth=self.string_smooth_average)

    def _equalizePatterns(self):
        areas = []
        #Integrate each pattern to find area under the curve
        for p in self.passes:
            if p.data.empty: continue
            v = np.trapz(y=p.data_mod[p.name], x=p.data_mod['loc'], axis=0)
            areas.append(v)
        #Find the pass with the largest integral
        maxx = max(areas)
        #Scale each pass to equalize areas to the maxx above
        for i in range(len(self.passes)):
            p = self.passes[i]
            if p.data.empty: continue
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
            m.append(p.calc_airspeed())
        return int(np.mean(m))

    def calc_spray_height_mean(self):
        m = []
        for p in self.passes:
            m.append(p.spray_height)
        return float(np.mean(m))

    def calc_wind_speed_mean(self):
        m = []
        for p in self.passes:
            m.append(p.wind_speed)
        return float(np.mean(m))

    def calc_crosswind_mean(self):
        m = []
        for p in self.passes:
            m.append(p.calc_crosswind())
        return float(np.mean(m))

    def calc_temperature_mean(self):
        m = []
        for p in self.passes:
            m.append(p.temperature)
        return int(np.mean(m))

    def calc_humidity_mean(self):
        m = []
        for p in self.passes:
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
        model.addNozzleSet(name=self.info.nozzle_type_1,
            orifice=self.info.nozzle_size_1,
            airspeed=self.calc_airspeed_mean(),
            pressure=self.info.pressure,
            angle=self.info.nozzle_deflection_1,
            quantity=self.info.nozzle_quantity_1)
        model.addNozzleSet(name=self.info.nozzle_type_2,
            orifice=self.info.nozzle_size_2,
            airspeed=self.calc_airspeed_mean(),
            pressure=self.info.pressure,
            angle=self.info.nozzle_deflection_2,
            quantity=self.info.nozzle_quantity_2)
        return model
