import uuid
import pandas as pd
import numpy as np
import scipy.signal as sig

class Pass:

    c = {'kph_mph': 0.621371,
        'kn_mph': 1.15078}

    center_method_none = -1
    center_method_centroid = 0
    center_method_cod = 1

    def __init__(self, id = '', number=0, name='',
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
        self.id = id
        if self.id == '':
            self.id = str(uuid.uuid4())
        self.number = number
        self.name = name
        if self.name=='':
            self.name = 'Pass ' + str(self.number)
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
        #Cards
        self.spray_cards = []

    def modifyData(self, isCenter=True, isSmooth=True):
        if not isinstance(self.data, pd.DataFrame): return
        d = self.data.copy()
        #Trim it
        d,_ = self.trimLR(d)
        d = self.trimV(d)
        #Center it
        centerMethod = self.center_method_none
        if isCenter:
            #Testing centroid vs cod
            #centerMethod = self.center_method_centroid
            centerMethod = self.center_method_centroid
        d = self.centerify(d, centerMethod)
        #Smooth it
        if isSmooth:
            d = self.smooth(d)
        #Set data_mod for plot use
        self.data_mod = d.copy()

    def trimLR(self, dataIntermediate):
        print(f'trim left = {self.trim_l}, trim right = {self.trim_r}')
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
        #return the modified data
        return d, min
        
    def trimV(self, dataIntermediate):
        print(f'trim vert = {self.trim_v}')
        name = self.name
        d = dataIntermediate
        #Trim Vertical
        d[name] = d[name].sub(self.trim_v)
        #clip all negative values (from trimmed areas) to 0
        d[name] = d[name].clip(lower=0)
        #return the modified data
        return d

    def centerify(self, dataIntermediate, centerMethod):
        name = self.name
        d = dataIntermediate
        #Need min for shifts out of x range
        min = d[name].min(skipna=True)
        c = 0
        if centerMethod == self.center_method_none:
            #No centering applied
            return d
        elif centerMethod == self.center_method_centroid:
            #Use Centroid
            c = self.calcCentroid(d)
        elif centerMethod == self.center_method_cod:
            #Use Center of Distribution
            c = self.calcCenterOfDistribution(d)
        #convert calculated center to integer points to shift plot
        sampleLength = d['loc'][1] - d['loc'][0]
        centerPoints = -round(c / sampleLength)
        #shift pattern by centroidPoints
        d[name] = d[name].shift(periods = centerPoints, fill_value=min)
        #return the modified data
        return d

    def calcCentroid(self, dataIntermediate):
        name = self.name
        d = dataIntermediate
        return (d[name] * d['loc']).sum() / d[name].sum()

    def calcCenterOfDistribution(self, dataIntermediate):
        #Alt method using Center of Distribution
        name = self.name
        d = dataIntermediate
        sumNumerator = 0.0
        sumDenominator = 0.0
        for i in range(0,len(d.index)-1, 1):
            D = d.at[i, name]
            Dn = d.at[i+1, name]
            X = d.at[i, 'loc']
            Xn = d.at[i+1, 'loc']
            #Calc Numerator and add to summation
            sumNumerator += (D*(Xn+X) + (Dn-D)*(2*Xn+X)/3)
            sumDenominator += (Dn+D)
        #Calc and return CoD
        return sumNumerator / sumDenominator

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

    def setTrims(self, trim_l = None, trim_r = None, trim_v = None):
        if trim_l is not None:
            self.trim_l = trim_l
        if trim_r is not None:
            self.trim_r = trim_r
        if trim_v is not None:
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
