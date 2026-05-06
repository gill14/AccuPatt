import uuid

import accupatt.config as cfg
import numpy as np
from accupatt.models.passDataCard import PassDataCard

from accupatt.models.passDataString import PassDataString


class Pass:
    def __init__(self, id_="", number=0, name=""):
        self.id = id_
        if self.id == "":
            self.id = str(uuid.uuid4())
        self.number = number
        self._name = name if name != "" else "Pass " + str(self.number)
        # Pass Info
        self.ground_speed: float | None = None
        self.ground_speed_units: str = cfg.get_unit_ground_speed()
        self.spray_height: float | None = None
        self.spray_height_units: str = cfg.get_unit_spray_height()
        self.pass_heading: int | None = None
        self.wind_direction: int | None = None
        self.wind_speed: float | None = None
        self.wind_speed_units: str = cfg.get_unit_wind_speed()
        self.temperature: float | None = None
        self.temperature_units: str = cfg.get_unit_temperature()
        self.humidity: float | None = None
        # String Data
        self.string = PassDataString(name=self._name)
        # Card Data
        self.cards = PassDataCard(name=self._name)

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str):
        self._name = value
        if hasattr(self, "string"):
            self.string.name = value
        if hasattr(self, "cards"):
            self.cards.name = value

    # -------------------------------------------------------------------------
    # Numeric accessors with optional unit conversion  (float | None)
    # -------------------------------------------------------------------------

    def ground_speed_in(self, units: str = None) -> float | None:
        if self.ground_speed is None:
            return None
        gs = self._to_mph(self.ground_speed, self.ground_speed_units)
        return round(self._from_mph(gs, units or self.ground_speed_units))

    def spray_height_in(self, units: str = None) -> float | None:
        if self.spray_height is None:
            return None
        sh = (
            self.spray_height * cfg.FT_PER_M
            if self.spray_height_units == cfg.UNIT_M
            else self.spray_height
        )
        units = units or self.spray_height_units
        return sh / cfg.FT_PER_M if units == cfg.UNIT_M else sh

    def wind_speed_in(self, units: str = None) -> float | None:
        if self.wind_speed is None:
            return None
        ws = self._to_mph(self.wind_speed, self.wind_speed_units)
        return self._from_mph(ws, units or self.wind_speed_units)

    def temperature_in(self, units: str = None) -> float | None:
        if self.temperature is None:
            return None
        units = units or self.temperature_units
        if units == self.temperature_units:
            return self.temperature
        if units == cfg.UNIT_DEG_F:
            return self.temperature * (9 / 5) + 32  # °C → °F
        return (self.temperature - 32) * (5 / 9)    # °F → °C

    def humidity_in(self) -> float | None:
        return self.humidity

    def airspeed_in(self, units: str = None) -> float | None:
        if any(
            v is None
            for v in (
                self.ground_speed,
                self.wind_speed,
                self.wind_direction,
                self.pass_heading,
            )
        ):
            return None
        gs = self._to_mph(self.ground_speed, self.ground_speed_units)
        ws = self._to_mph(self.wind_speed, self.wind_speed_units)
        airspeed = gs - ws * np.cos(
            np.radians(self.wind_direction - (self.pass_heading - 180))
        )
        return round(self._from_mph(airspeed, units or self.ground_speed_units))

    def crosswind_in(self, units: str = None) -> float | None:
        if any(
            v is None for v in (self.wind_speed, self.wind_direction, self.pass_heading)
        ):
            return None
        ws = self._to_mph(self.wind_speed, self.wind_speed_units)
        crosswind = ws * np.sin(
            np.radians((self.pass_heading - 180) - self.wind_direction)
        )
        return self._from_mph(crosswind, units or self.wind_speed_units)

    # -------------------------------------------------------------------------
    # Display string properties  (stored unit, "" when not set)
    # -------------------------------------------------------------------------

    @property
    def ground_speed_str(self) -> str:
        v = self.ground_speed_in()
        return f"{v}" if v is not None else ""

    @property
    def spray_height_str(self) -> str:
        v = self.spray_height_in()
        return f"{v:g}" if v is not None else ""

    @property
    def pass_heading_str(self) -> str:
        return f"{self.pass_heading}" if self.pass_heading is not None else ""

    @property
    def wind_direction_str(self) -> str:
        return f"{self.wind_direction}" if self.wind_direction is not None else ""

    @property
    def wind_speed_str(self) -> str:
        v = self.wind_speed_in()
        return f"{v:g}" if v is not None else ""

    @property
    def temperature_str(self) -> str:
        v = self.temperature_in()
        return f"{v:g}" if v is not None else ""

    @property
    def humidity_str(self) -> str:
        return f"{self.humidity:g}" if self.humidity is not None else ""

    # -------------------------------------------------------------------------
    # Setters  (return False on parse failure; None stored for blank input)
    # -------------------------------------------------------------------------

    def set_ground_speed(self, val, units=None) -> bool:
        val, ok = self._parse(val)
        if not ok:
            return False
        self.ground_speed = val
        if units:
            self.ground_speed_units = units
        return True

    def set_spray_height(self, val, units=None) -> bool:
        val, ok = self._parse(val)
        if not ok:
            return False
        self.spray_height = val
        if units:
            self.spray_height_units = units
        return True

    def set_pass_heading(self, val) -> bool:
        val, ok = self._parse(val, int)
        if not ok:
            return False
        self.pass_heading = val
        return True

    def set_wind_direction(self, val) -> bool:
        val, ok = self._parse(val, int)
        if not ok:
            return False
        self.wind_direction = val
        return True

    def set_wind_speed(self, val, units=None) -> bool:
        val, ok = self._parse(val)
        if not ok:
            return False
        self.wind_speed = val
        if units:
            self.wind_speed_units = units
        return True

    def set_temperature(self, val, units=None) -> bool:
        val, ok = self._parse(val)
        if not ok:
            return False
        self.temperature = val
        if units:
            self.temperature_units = units
        return True

    def set_humidity(self, val) -> bool:
        val, ok = self._parse(val)
        if not ok:
            return False
        self.humidity = val
        return True

    # -------------------------------------------------------------------------
    # Internal helpers
    # -------------------------------------------------------------------------

    def _parse(self, val, var_type=float) -> tuple:
        if val == "" or val is None:
            return (None, True)
        try:
            return (var_type(val), True)
        except (ValueError, TypeError):
            return (None, False)

    def _to_mph(self, value: float, unit: str) -> float:
        if unit == cfg.UNIT_KPH:
            return value * cfg.MPH_PER_KPH
        if unit == cfg.UNIT_KN:
            return value * cfg.MPH_PER_KN
        return value

    def _from_mph(self, value: float, unit: str) -> float:
        if unit == cfg.UNIT_KPH:
            return value / cfg.MPH_PER_KPH
        if unit == cfg.UNIT_KN:
            return value / cfg.MPH_PER_KN
        return value
