import pandas as pd
import numpy as np

from appInfo import AppInfo
from passData import Pass
from atomizationModel import AtomizationModel, AtomizationModelMulti


class SeriesData:
    """A Container class for storing all Series info"""

    def __init__(self):
        self.info = AppInfo()
        self.passes = {}
        self.patternAverage = Pass(name='Average')
        self.patternAverageInverted = Pass(name='AverageInverted')

    def modifyPatterns(self, isCentroid, isSmoothIndividual, isEqualize, isSmoothAverage):
        #apply individual pattern modifications
        for key, value in self.passes.items():
            value.modifyData(isCentroid=isCentroid, isSmooth=isSmoothIndividual)
        #apply cross-pattern modifications
        if isEqualize:
            self.equalizePatterns()
        #Generate Average Pattern
        self.averagePattern()
        #Apply avearge pattern modifications
        self.patternAverage.modifyData(isCentroid=isCentroid, isSmooth=isSmoothAverage)
        self.patternAverageInverted.modifyData(isCentroid=isCentroid, isSmooth=isSmoothAverage)

    def equalizePatterns(self):
        areas = {}
        areasa = []
        for key, value in self.passes.items():
            v = np.trapz(y=value.data_mod[key], x=value.data_mod['loc'], axis=0)
            areas[key] = v
            areasa.append(v)
        scalers = {}
        maxx = max(areasa)
        for k in areas.keys():
            scalers[k] = maxx/areas[k]
        for key, value in self.passes.items():
            p = self.passes[key]
            p.data_mod[key] = p.data_mod[key].multiply(scalers[key])

    def averagePattern(self):
        #df placeholder
        average = pd.DataFrame()
        #temp df to average accross columns
        d = pd.DataFrame()
        for key, value in self.passes.items():
            #Only include passes checked from listview
            if value.include_in_composite:
                #add loc column to placeholder, will be overwritten each time with identical values
                average['loc'] = value.data_mod['loc']
                #add each modified pattern data to temp df
                d[key] = value.data_mod[key]
        if not average.empty:
            #take the column-wise average and add that series to the placeholder
            average['Average'] = d.mean(axis='columns')
            #copy the placeholder and assign it to thie object's previously declared patternAverage object
            self.patternAverage.data = average.copy()
            #make an inverted copy for simulated overlap
            averageInverted = pd.DataFrame()
            averageInverted['loc'] = average['loc'].copy()
            averageInverted['AverageInverted'] = average['Average'].copy().values[::-1]
            self.patternAverageInverted.data = averageInverted.copy()

    '''
    The methods below are used to convert and calculate info values as needed
    '''
    def calc_airspeed_mean(self):
        m = []
        for key in self.passes.keys():
            m.append(self.passes[key].calc_airspeed())
        return int(np.mean(m))

    def calc_spray_height_mean(self):
        m = []
        for key in self.passes.keys():
            m.append(self.passes[key].spray_height)
        return float(np.mean(m))

    def calc_wind_speed_mean(self):
        m = []
        for key in self.passes.keys():
            m.append(self.passes[key].wind_speed)
        return float(np.mean(m))

    def calc_crosswind_mean(self):
        m = []
        for key in self.passes.keys():
            m.append(self.passes[key].calc_crosswind())
        return float(np.mean(m))

    def calc_temperature_mean(self):
        m = []
        for key in self.passes.keys():
            m.append(self.passes[key].temperature)
        return int(np.mean(m))

    def calc_humidity_mean(self):
        m = []
        for key in self.passes.keys():
            m.append(self.passes[key].humidity)
        return int(np.mean(m))

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
