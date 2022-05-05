from typing import Tuple
import uuid

import accupatt.config as cfg
import numpy as np

from accupatt.models.passStringData import PassStringData
from accupatt.models.sprayCard import SprayCard

class Pass:

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
        self.ground_speed: float = 0
        self.ground_speed_units = cfg.get_unit_ground_speed()
        self.spray_height: float = 0
        self.spray_height_units = cfg.get_unit_spray_height()
        self.pass_heading: int = 0
        self.wind_direction: int = 0
        self.wind_speed: float = 0
        self.wind_speed_units = cfg.get_unit_wind_speed()
        self.temperature: float = 0
        self.temperature_units = cfg.get_unit_temperature()
        self.humidity: float = 0
        # String Data
        self.string = PassStringData(name=self.name)
        # Spray Card List
        self.spray_cards: list[SprayCard] = []
        #Include in Composite by default
        self.string_include_in_composite = True
        self.cards_include_in_composite = True

    def has_string_data(self) -> bool:
        return not self.string.data.empty
    
    def has_card_data(self) -> bool:
        return len(self.spray_cards) > 0

    '''
    GET methods return a tuple of (value, units, value_string, value_units_string)
    '''

    def get_airspeed(self, units=None) -> tuple[int,str,str,str]:
        # Convert gs and ws to mph and save to temp vars
        gs = self._convert_speed_to_mph(self.ground_speed, self.ground_speed_units)
        ws = self._convert_speed_to_mph(self.wind_speed, self.wind_speed_units)
        # Calculate airspeed in mph (inverse of ph to go with convention of flyin collection)
        airspeed = gs-(ws*np.cos(np.radians(self.wind_direction-(self.pass_heading-180))))
        # Use requested units, default to ground_speed_units
        units = units if units else self.ground_speed_units
        # Convert units and round
        airspeed = round(self._convert_speed_mph_to_requested(airspeed, units))
        return airspeed, units, f'{airspeed}', f'{airspeed} {units}'

    def get_crosswind(self, units=None) -> tuple[float,str,str,str]:
        # Convert ws to mph and save to temp var
        ws = self._convert_speed_to_mph(self.wind_speed, self.wind_speed_units)
        # Calculate crosswind in mph (inverse of ph to go with convention of flyin collection)
        crosswind = ws * np.sin(np.radians((self.pass_heading-180)-self.wind_direction))
        # Use requested units, default to ground_speed_units
        units = units if units else self.wind_speed_units
        # Convert units
        crosswind = self._convert_speed_mph_to_requested(crosswind, units)
        return crosswind, units, f'{crosswind:.1f}', f'{crosswind:.1f} {units}'
    
    def get_ground_speed(self, units=None) -> tuple[int,str,str,str]:
        # Convert gs to mph and save to temp var
        gs = self._convert_speed_to_mph(self.ground_speed, self.ground_speed_units)
        # Use requested units, default to ground_speed_units
        units = units if units else self.ground_speed_units
        # Convert units and round
        gs = round(self._convert_speed_mph_to_requested(gs, units))
        return gs, units, f'{gs}', f'{gs} {units}'
        
    def get_spray_height(self, units=None) -> tuple[float,str,str,str]:
        # Convert sh to ft and save to temp var
        sh = self.spray_height * cfg.FT_PER_M if self.spray_height_units==cfg.UNIT_M else self.spray_height
        # Use requested units, default to spray_height_units
        units = units if units else self.spray_height_units
        # Convert units
        sh = sh / cfg.FT_PER_M if units==cfg.UNIT_M else sh
        return sh, units, f'{sh:g}', f'{sh:.1f} {units}'
        
    def get_pass_heading(self) -> tuple[int,str,str,str]:
        return self.pass_heading, cfg.UNIT_DEG, f'{self.pass_heading}', f'{self.pass_heading}{cfg.UNIT_DEG}'
        
    def get_wind_direction(self) -> tuple[int,str,str,str]:
        return self.wind_direction, cfg.UNIT_DEG, f'{self.wind_direction}', f'{self.wind_direction}{cfg.UNIT_DEG}'
        
    def get_wind_speed(self, units=None) -> tuple[float,str,str,str]:
        # Convert ws to mph and save to temp var
        ws = self._convert_speed_to_mph(self.wind_speed, self.wind_speed_units)
        # Use requested units, default to wind_speed_units
        units = units if units else self.wind_speed_units
        # Convert units
        ws = self._convert_speed_mph_to_requested(ws, units)
        return ws, units, f'{ws:g}', f'{ws:.1f} {units}'
        
    def get_temperature(self, units=None) -> tuple[float,str,str,str]:
        # Convert t to deg-F and save to temp var
        t = (self.temperature * (9/5)) + 32 if self.temperature_units==cfg.UNIT_DEG_C else self.temperature
        # Use requested units, default to spray_height_units
        units = units if units else self.temperature_units
        # Convert units
        t = (self.temperature - 32) * (5/9) if units==cfg.UNIT_DEG_C else t
        return t, units, f'{t:g}', f'{t:.1f} {units}'  
        
    def get_humidity(self) -> tuple[float,str,str,str]:
        return self.humidity, '%', f'{self.humidity:g}', f'{self.humidity:.1f}%'

    def _convert_speed_to_mph(self, value, unit) -> float:
        if unit == cfg.UNIT_KPH:
            value = value * cfg.MPH_PER_KPH
        elif unit == cfg.UNIT_KN:
            value = value * cfg.MPH_PER_KN
        return value
    
    def _convert_speed_mph_to_requested(self, value, unit) -> float:
        if unit == cfg.UNIT_KPH:
            value = value / cfg.MPH_PER_KPH
        elif unit == cfg.UNIT_KN:
            value = value / cfg.MPH_PER_KN
        return value

    '''
    The methods below are used to set values as needed
    '''

    def set_ground_speed(self, val, units=None) -> bool:
        val = 0 if val=='' else val
        try:
            self.ground_speed = float(val)
        except ValueError:
            return False
        if units:
            self.ground_speed_units = units
        return True

    def set_spray_height(self, val, units=None) -> bool:
        val = 0 if val=='' else val
        try:
            self.spray_height = float(val)
        except ValueError:
            return False
        if units:
            self.spray_height_units = units
        return True

    def set_pass_heading(self, val) -> bool:
        val = 0 if val=='' else val
        try:
            self.pass_heading = int(val)
        except ValueError:
            return False
        return True

    def set_wind_direction(self, val) -> bool:
        val = 0 if val=='' else val
        try:
            self.wind_direction = int(val)
        except ValueError:
            return False
        return True

    def set_wind_speed(self, val, units=None) -> bool:
        val = 0 if val=='' else val
        try:
            self.wind_speed = float(val)
        except ValueError:
            return False
        if units:
            self.wind_speed_units = units
        return True

    def set_temperature(self, val, units=None) -> bool:
        val = 0 if val=='' else val
        try:
            self.temperature = float(val)
        except ValueError:
            return False
        if units:
            self.temperature_units = units
        return True

    def set_humidity(self, val) -> bool:
        val = 0 if val=='' else val
        try:
            self.humidity = float(val)
        except ValueError:
            return False
        return True
