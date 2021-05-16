import pandas as pd
import numpy as np
import scipy.signal as sig

class Pass:

    c = {'kph_mph': 0.621371,
        'kn_mph': 1.15078}

    def __init__(self, name=''):
        #Info Stuff
        self.name = name
        self.ground_speed = None
        self.ground_speed_units =  'mph'
        self.spray_height = None
        self.spray_height_units = 'ft'
        self.pass_heading = None
        self.wind_direction = None
        self.wind_speed = None
        self.wind_speed_units = 'mph'
        self.temperature = None
        self.temperature_units = '°F'
        self.humidity = None
        #Pattern stuff
        self.data_ex = None
        self.data = None #Holds original Data
        self.dataMod = None #Holds data with all requested modifications
        self.trimL = 0
        self.trimR = 0
        self.trimV = 0
        self.excitationWav = 0
        self.emissionWav = 0
        #Include in Composite by default
        self.includeInComposite = True

    def modifyData(self, isCentroid=True, isSmooth=True):
        d = self.data.copy()
        #Trim it
        d = self.trimLRV(d)
        #Centroid it
        if isCentroid:
            d = self.centroidify(d)
        #Smooth it
        if isSmooth:
            d = self.smooth(d)
        #Set dataMod for plot use
        self.dataMod = d.copy()

    def trimLRV(self, dataIntermediate):
        name = self.name
        d = dataIntermediate
        #Trim Left
        d.loc[:self.trimL-1,[name]] = -1
        #Trim Right
        d.loc[(d[name].size-self.trimR):,[name]] = -1
        #Find new min inside untrimmed area
        min = d[d>-1].loc[:,[name]].min(skipna=True)
        #subtract min from all points
        d[name] = d.loc[:,[name]].sub(min,axis=1)
        #clip all negative values (from trimmed areas) to 0
        d[name] = d[[name]].clip(lower=0)
        #Trim Vertical
        d[name] = d.loc[:,[name]].sub(self.trimV,axis=1)
        #Set modified data in pattern object
        return d

    def centroidify(self, dataIntermediate):
        name = self.name
        d = dataIntermediate
        #Need min for shifts out of x range
        min = d[name].min(skipna=True)
        #calculate centroid
        centroid = (d[name] * d['loc']).sum() / d[name].sum()
        #convert calculated centroid to integer points to shift plot
        sampleLength = d['loc'][1] - d['loc'][0]
        centroidPoints = -round(centroid / sampleLength)
        #shift pattern by centroidPoints
        d[name] = d[name].shift(periods = centroidPoints, fill_value=min)
        #return the modified data
        return d

    def smooth(self, dataIntermediate):
        d = dataIntermediate
        window = 21
        order = 3
        d[self.name] = sig.savgol_filter(d[self.name], window, order)
        d[self.name] = d[self.name].clip(lower=0)
        return d

    def setData(self, x_data, y_data, y_ex_data):
        pattern = np.array([x_data, y_data])
        self.data = pd.DataFrame(data=pattern, columns=['loc', self.name])
        pattern_ex = np.array([x_data, y_ex_data])
        self.data_ex = pd.DataFrame(data=pattern_ex, columns=['loc', self.name])

    def setTrims(self, trimL, trimR, trimV):
        self.trimL = trimL
        self.trimR = trimR
        self.trimV = trimV

    '''
    The methods below are used to convert and calculate info values as needed
    '''

    def calc_airspeed(self, units='mph') -> int:
        gs = float(self.ground_speed)
        gs_units = self.ground_speed_units
        ws = float(self.wind_speed)
        ws_units = self.wind_speed_units
        wd = float(self.wind_direction)
        ph = float(self.pass_heading)
        #Convert gs
        if gs_units != 'mph':
            gs = gs * self.c[f'{gs_units}_mph']
        #Convert ws
        if ws_units != 'mph':
            ws = ws * self.c[f'{ws_units}_mph']
        #Calculate the inverse of ph to go with convention of flyin collection
        ph = ph - 180
        #Calculate Airspeed in mph
        airspeed = gs-(ws*np.cos(np.radians(wd-ph)))
        #Convert to requested units of airspeed
        if units != 'mph':
            airspeed = airspeed / self.c[f'{units}_mph']
        #Return value as int
        return int(round(airspeed))

    def calc_crosswind(self, units='mph') -> float:
        ws = float(self.wind_speed)
        ws_units = self.wind_speed_units
        wd = float(self.wind_direction)
        ph = float(self.pass_heading)
        #Convert ws
        if ws_units != 'mph':
            ws = ws * self.c[f'{ws_units}_mph']
        #Calculate the inverse of ph to go with convention of flyin collection
        ph = ph - 180
        #Calculate crosswind in mph
        crosswind = ws * np.sin(np.radians(ph-wd))
        #Convert to requested units of crosswind
        if units != 'mph':
            crosswind = crosswind / self.c[f'{units}_mph']
        #Return value as int
        return float(crosswind)

    def set_ground_speed(self, val, units=None) -> bool:
        try:
            self.ground_speed = float(val)
        except ValueError:
            return False
        if not units==None:
            self.ground_speed_units = units
        return True

    def set_spray_height(self, val, units=None) -> bool:
        try:
            self.spray_height = float(val)
        except ValueError:
            return False
        if not units==None:
            self.spray_height_units = units
        return True

    def set_pass_heading(self, val) -> bool:
        try:
            self.pass_heading = float(val)
        except ValueError:
            return False
        return True

    def set_wind_direction(self, val) -> bool:
        try:
            self.wind_direction = float(val)
        except ValueError:
            return False
        return True

    def set_wind_speed(self, val, units=None) -> bool:
        try:
            self.wind_speed = float(val)
        except ValueError:
            return False
        if not units==None:
            self.wind_speed_units = units
        return True

    def set_temperature(self, val, units=None) -> bool:
        try:
            self.temperature = float(val)
        except ValueError:
            return False
        if not units==None:
            self.temperature_units = units
        return True

    def set_humidity(self, val) -> bool:
        try:
            self.humidity = float(val)
        except ValueError:
            return False
        return True
