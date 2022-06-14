import accupatt.config as cfg
from dataclasses import dataclass, field


@dataclass
class Nozzle:
    id: int = 1
    type: str = ""
    size: str = ""
    deflection: str = ""
    quantity: int = 0

    def as_string_tuple(self) -> tuple:
        if self.type == "":
            return ("", "")
        line_1 = f"{self.type} @ {self.deflection}" + "\N{DEGREE SIGN}"
        line_2 = f"Orif#{self.size} x{str(self.quantity)}"
        return (line_1, line_2)

    def set_quantity(self, new_quantity) -> bool:
        try:
            q = int(new_quantity)
            self.quantity = q
        except ValueError:
            return False
        return True


@dataclass
class AppInfo:
    """A Container class for storing Application Info"""

    flyin_name: str = ""
    flyin_location: str = ""
    flyin_date: str = ""
    flyin_analyst: str = ""

    pilot: str = ""
    business: str = ""
    street: str = ""
    city: str = ""
    state: str = ""
    zip: str = ""
    phone: str = ""
    email: str = ""

    regnum: str = ""
    make: str = ""
    model: str = ""
    wingspan: float = 0
    wingspan_units: str = field(default_factory=cfg.get_unit_wingspan)
    winglets: str = "No"

    swath: int = 0
    swath_units: str = field(default_factory=cfg.get_unit_swath)
    rate: float = 0
    rate_units: str = field(default_factory=cfg.get_unit_rate)
    pressure: float = 0
    pressure_units: str = field(default_factory=cfg.get_unit_pressure)
    boom_width: float = 0
    boom_width_units: str = field(default_factory=cfg.get_unit_boom_width)
    boom_drop: float = 0
    boom_drop_units: str = field(default_factory=cfg.get_unit_boom_drop)
    nozzle_spacing: float = 0
    nozzle_spacing_units: str = field(default_factory=cfg.get_unit_nozzle_spacing)

    nozzles: list[Nozzle] = field(default_factory=list)

    series: int = 1
    notes_setup: str = ""
    notes_analyst: str = ""
    created: int = 0
    modified: int = 0

    def string_reg_series(self) -> str:
        if self.series < 10:
            s_str = "0" + str(self.series)
        else:
            s_str = str(self.series)
        return self.regnum + " " + s_str

    def addressLine1(self) -> str:
        return self.street

    def addressLine2(self) -> str:
        s = self.city
        # Append state if not blank
        s = s + ", " + self.state if self.state != "" else s
        # Append ZIP if not blank
        s = s + " " + self.zip if self.zip != "" else s
        return s

    def string_phone(self) -> str:
        p = self.phone
        if len(p) == 10:
            return f"({p[:3]}) {p[3:6]}-{p[6:]}"

    def string_wingspan(self) -> str:
        if self.wingspan > 0:
            return f"{self.strip_num(self.wingspan)} {self.wingspan_units}"
        else:
            return ""

    def string_swath(self) -> str:
        if self.swath > 0:
            return str(self.swath) + " " + self.swath_units
        else:
            return ""

    def string_rate(self) -> str:
        if self.rate > 0:
            return f"{self.strip_num(self.rate)} {self.rate_units}"
        else:
            return ""

    def string_pressure(self) -> str:
        if self.pressure > 0:
            return f"{self.strip_num(self.pressure)} {self.pressure_units}"
        else:
            return ""

    def string_boom_width(self) -> str:
        if self.boom_width > 0:
            # Calculate and use percent boom width if able
            if self.wingspan > 0 and self.boom_width_units!="%" and self.boom_width_units!="" and self.wingspan_units!="":
                ws = self.wingspan if self.wingspan_units==cfg.UNIT_FT else self.wingspan * cfg.FT_PER_M
                print(ws)
                print(self.boom_width)
                print(self.boom_width_units)
                bw = self.boom_width if self.boom_width_units==cfg.UNIT_FT else self.boom_width * cfg.FT_PER_M
                print(bw)
                return f"{((bw / ws) * 100):.2g}%"
                
            return f"{self.strip_num(self.boom_width)} {self.boom_width_units}"
        else:
            return ""

    def string_boom_drop(self) -> str:
        if self.boom_drop > 0:
            return f"{self.strip_num(self.boom_drop)} {self.boom_drop_units}"
        else:
            return ""

    def string_nozzle_spacing(self) -> str:
        if self.nozzle_spacing > 0:
            return f"{self.strip_num(self.nozzle_spacing)} {self.nozzle_spacing_units}"
        else:
            return ""

    def string_temperature(self) -> str:
        if self.temperature > 0:
            return f"{self.strip_num(self.temperature)} {self.temperature_units}"
        else:
            return ""

    def string_humidity(self) -> str:
        if self.humidity > 0:
            return f"{self.strip_num(self.humidity)}%"
        else:
            return ""

    def string_series(self) -> str:
        return f"{self.strip_num(self.series)}"

    def strip_num(self, x, precision=2, zeroBlank=False) -> str:
        if type(x) is str:
            if x == "":
                x = 0
        if zeroBlank and x == 0:
            return ""
        if float(x).is_integer():
            return str(int(float(x)))
        else:
            return f"{round(float(x), 2):.{precision}f}"

    def get_pressure(self, units: str = "psi"):
        p = self.pressure
        u = self.pressure_units
        if u == units:
            return p
        # Convert to PSI
        if u == cfg.UNIT_BAR:
            p = p * cfg.PSI_PER_BAR
        elif u == cfg.UNIT_KPA:
            p = p / cfg.KPA_PER_PSI
        # Convert to requested unit
        if units == cfg.UNIT_BAR:
            p = p / cfg.PSI_PER_BAR
        elif units == cfg.UNIT_KPA:
            p = p * cfg.KPA_PER_PSI
        # Return pressure in requested units (defaults to psi)
        return p

    def set_wingspan(self, string) -> bool:
        if string == "":
            string = "0"
        try:
            float(string)
        except ValueError:
            return False
        self.wingspan = float(string)
        return True

    def set_wingspan_units(self, string):
        self.wingspan_units = string

    def set_swath(self, string) -> bool:
        try:
            int(float(string))
        except ValueError:
            return False
        self.swath = int(float(string))
        return True
    
    def set_swath_units(self, string):
        self.swath_units = string

    def set_rate(self, string) -> bool:
        if string == "":
            string = "0"
        try:
            float(string)
        except ValueError:
            return False
        self.rate = float(string)
        return True

    def set_rate_units(self, string):
        self.rate_units = string

    def set_pressure(self, string) -> bool:
        if string == "":
            string = "0"
        try:
            float(string)
        except ValueError:
            return False
        self.pressure = float(string)
        return True

    def set_pressure_units(self, string):
        self.pressure_units = string

    def set_boom_width(self, string) -> bool:
        if string == "":
            string = "0"
        try:
            float(string)
        except ValueError:
            return False
        self.boom_width = float(string)
        return True

    def set_boom_width_units(self, string):
        self.boom_width_units = string

    def set_boom_drop(self, string) -> bool:
        if string == "":
            string = "0"
        try:
            float(string)
        except ValueError:
            return False
        self.boom_drop = float(string)
        return True

    def set_boom_drop_units(self, string):
        self.boom_drop_units = string

    def set_nozzle_spacing(self, string) -> bool:
        if string == "":
            string = "0"
        try:
            float(string)
        except ValueError:
            return False
        self.nozzle_spacing = float(string)
        return True

    def set_nozzle_spacing_units(self, string):
        self.nozzle_spacing_units = string

    def set_num(self, field, string, type) -> bool:
        try:
            if type == "int":
                field = int(string)
            else:
                field = float(string)
            return True
        except ValueError:
            return False
