import pandas as pd
import numpy as np
import scipy.signal as sig

class Pass:

    c = {'kph_mph': 0.621371,
        'kn_mph': 1.15078}

    def __init__(self, name='',
            ground_speed=None, ground_speed_units='mph',
            spray_height=None, spray_height_units='ft',
            pass_heading=None, wind_direction=None,
            wind_speed=None, wind_speed_units='mph',
            temperature = None, temperature_units='°F',
            humidity=None, include_in_composite=True,
            excitation_wav=None, emission_wav=None,
            trim_l=0, trim_r=0, trim_v=0,
            data_ex=None, data=None, data_mod=None):
        #Info Stuff
        self.name = name
        self.ground_speed = ground_speed
        self.ground_speed_units =  ground_speed_units
        self.spray_height = spray_height
        self.spray_height_units = spray_height_units
        self.pass_heading = pass_heading
        self.wind_direction = wind_direction
        self.wind_speed = wind_speed
        self.wind_speed_units = wind_speed_units
        self.temperature = temperature
        self.temperature_units = temperature_units
        self.humidity = humidity
        #Include in Composite by default
        self.include_in_composite = include_in_composite
        #Pattern stuff
        self.excitation_wav = excitation_wav
        self.emission_wav = emission_wav
        self.trim_l = trim_l
        self.trim_r = trim_r
        self.trim_v = trim_v
        self.data = data #Holds original Data
        self.data_mod = data_mod #Holds data with all requested modifications
        self.data_ex = data_ex #Holds Excitation Data

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
        #Set data_mod for plot use
        self.data_mod = d.copy()

    def trimLRV(self, dataIntermediate):
        name = self.name
        d = dataIntermediate
        #Trim Left
        d.loc[d.index[:self.trim_l],name] = -1
        #Trim Right
        d.loc[d.index[(-1-self.trim_r):],name] = -1
        #Find new min inside untrimmed area
        min = d[d>-1].loc[d.index[:],name].min(skipna=True)
        #subtract min from all points
        d[name] = d[name].sub(min)
        #clip all negative values (from trimmed areas) to 0
        d[name] = d[name].clip(lower=0)
        #Trim Vertical
        d[name] = d[name].sub(self.trim_v)
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

    def setTrims(self, trim_l, trim_r, trim_v):
        self.trim_l = trim_l
        self.trim_r = trim_r
        self.trim_v = trim_v

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
