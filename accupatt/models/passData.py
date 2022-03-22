import uuid

import accupatt.config as cfg
import numpy as np

from accupatt.models.passStringData import PassStringData

class Pass:

    c = {'kph_mph': cfg.MPH_PER_KPH,
        'kn_mph': cfg.MPH_PER_KN}

    def __init__(self, id = '', number=0, name=''):
        #Info Stuff
        self.id = id
        if self.id == '':
            self.id = str(uuid.uuid4())
        self.number = number
        self.name = name
        if self.name=='':
            self.name = 'Pass ' + str(self.number)
        # Pass Info
        self.ground_speed = 0
        self.ground_speed_units = cfg.get_unit_ground_speed()
        self.spray_height = 0
        self.spray_height_units = cfg.get_unit_spray_height()
        self.pass_heading = 0
        self.wind_direction = 0
        self.wind_speed = 0
        self.wind_speed_units = cfg.get_unit_wind_speed()
        self.temperature = 0
        self.temperature_units = cfg.get_unit_temperature()
        self.humidity = 0
        # String Data
        self.string = PassStringData(name=self.name)
        # Spray Card List
        self.spray_cards = []
        #Include in Composite by default
        self.string_include_in_composite = True
        self.cards_include_in_composite = True

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
    
    def str_airspeed(self, units=None, printUnits=False) -> str:
        try:
            float(self.ground_speed)
            float(self.wind_speed)
            float(self.wind_direction)
            float(self.pass_heading)
        except (TypeError, ValueError):
            return ''
        if units==None:
            units=self.ground_speed_units
        text = f'{self.calc_airspeed(units=units)}'
        if printUnits:
            text += f' {units}'
        return text

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
    
    def str_crosswind(self, units=None, printUnits=False) -> str:
        try:
            float(self.wind_speed)
            float(self.wind_direction)
            float(self.pass_heading)
        except (TypeError, ValueError):
            return ''
        if units==None:
            units=self.wind_speed_units
        text = f'{self.strip_num(self.calc_crosswind(units=units))}'
        if printUnits:
            text += f' {units}'
        return text
    
    def str_ground_speed(self, printUnits=False):
        try:
            float(self.ground_speed)
        except (TypeError, ValueError):
            return ''
        text = f'{self.strip_num(self.ground_speed,zeroBlank=True)}'
        if printUnits:
            text += f' {self.ground_speed_units}'
        return text
        
    def str_spray_height(self, printUnits=False):
        try:
            float(self.spray_height)
        except (TypeError, ValueError):
            return ''
        text = f'{self.strip_num(self.spray_height,zeroBlank=True)}'
        if printUnits:
            text += f' {self.spray_height_units}'
        return text
        
    def str_pass_heading(self, printUnits=False):
        try:
            float(self.pass_heading)
        except (TypeError, ValueError):
            return ''
        text = f'{self.strip_num(self.pass_heading,zeroBlank=True)}'
        if printUnits:
            text += f'{cfg.UNIT_DEG}'
        return text
        
    def str_wind_direction(self, printUnits=False):
        try:
            float(self.wind_direction)
        except (TypeError, ValueError):
            return ''
        text = f'{self.strip_num(self.wind_direction,zeroBlank=True)}'
        if printUnits:
            text += f'{cfg.UNIT_DEG}'
        return text
        
    def str_wind_speed(self, printUnits=False):
        try:
            float(self.wind_speed)
        except (TypeError, ValueError):
            return ''
        text = f'{self.strip_num(self.wind_speed,zeroBlank=True)}'
        if printUnits:
            text += f' {self.wind_speed_units}'
        return text
        
    def str_temperature(self, printUnits=False):
        try:
            float(self.temperature)
        except (TypeError, ValueError):
            return ''
        text = f'{self.strip_num(self.temperature,zeroBlank=True)}'
        if printUnits:
            text += f' {self.temperature_units}'
        return text  
        
    def str_humidity(self, printUnits=False):
        try:
            float(self.humidity)
        except (TypeError, ValueError):
            return ''
        text = f'{self.strip_num(self.humidity,zeroBlank=True)}'
        if printUnits:
            text += '%'
        return text   

    def strip_num(self, x, precision = 2, zeroBlank = False) -> str:
        if type(x) is str:
            if x == '':
                x = 0
        if x == None or (zeroBlank and x == 0):
            return ''
        if float(x).is_integer():
            return str(int(float(x)))
        else:
            return f'{round(float(x), 2):.{precision}f}'

    '''
    The methods below are used to set values as needed
    '''

    def set_ground_speed(self, val, units=None) -> bool:
        if val=='':
            val = 0
        try:
            self.ground_speed = float(val)
        except ValueError:
            return False
        if not units==None:
            self.ground_speed_units = units
        return True

    def set_spray_height(self, val, units=None) -> bool:
        if val=='':
            val = 0
        try:
            self.spray_height = float(val)
        except ValueError:
            return False
        if not units==None:
            self.spray_height_units = units
        return True

    def set_pass_heading(self, val) -> bool:
        if val=='':
            val = 0
        try:
            self.pass_heading = int(val)
        except ValueError:
            return False
        return True

    def set_wind_direction(self, val) -> bool:
        if val=='':
            val = 0
        try:
            self.wind_direction = int(val)
        except ValueError:
            return False
        return True

    def set_wind_speed(self, val, units=None) -> bool:
        if val=='':
            val = 0
        try:
            self.wind_speed = float(val)
        except ValueError:
            return False
        if not units==None:
            self.wind_speed_units = units
        return True

    def set_temperature(self, val, units=None) -> bool:
        if val=='':
            val = 0
        try:
            self.temperature = float(val)
        except ValueError:
            return False
        if not units==None:
            self.temperature_units = units
        return True

    def set_humidity(self, val) -> bool:
        if val=='':
            val = 0
        try:
            self.humidity = float(val)
        except ValueError:
            return False
        return True
