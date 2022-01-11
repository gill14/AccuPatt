from dataclasses import dataclass

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
    wingspan_units: str = "ft"
    winglets: str = "No"

    swath: int = 50
    swath_adjusted: int = 50
    swath_units = "ft"
    rate: float = 0
    rate_units: str = ""
    pressure: float = 0
    pressure_units: str = ""
    nozzle_type_1: str = ""
    nozzle_size_1: str = ""
    nozzle_deflection_1: str = ""
    nozzle_quantity_1: int = 0
    nozzle_type_2: str = ""
    nozzle_size_2: str = ""
    nozzle_deflection_2: str = ""
    nozzle_quantity_2: int = 0
    boom_width: float = 0
    boom_width_units: str = ""
    boom_drop: float = 0
    boom_drop_units: str = ""
    nozzle_spacing: float = 0
    nozzle_spacing_units: str = ""

    series: int = 1
    notes_setup: str = ""
    notes_analyst: str = ""
    date: str = ""
    time: str = ""

    def updateApplicatorInfo(self, appInfo):
        self.pilot = appInfo.pilot
        self.business = appInfo.business
        self.street = appInfo.street
        self.city = appInfo.city
        self.state = appInfo.state
        self.zip = appInfo.zip
        self.phone = appInfo.phone
        self.email = appInfo.email

    def updateAircraft(self, appInfo):
        self.regnum = appInfo.regnum
        self.make = appInfo.make
        self.model = appInfo.model
        self.wingspan = appInfo.wingspan
        self.wingspan_units = appInfo.wingspan_units
        self.winglets = appInfo.winglets

    def updateSpraySystem(self, appInfo):
        self.swath = appInfo.swath
        self.swath_units = appInfo.swath_units
        self.rate = appInfo.rate
        self.rate_units = appInfo.rate_units
        self.pressure = appInfo.pressure
        self.pressure_units = appInfo.pressure_units

    def updateSeries(self, appInfo):
        self.series = appInfo.series
        #self.notes = appInfo.notes

    def addressLine1(self) -> str:
        return self.street

    def addressLine2(self) -> str:
        s = self.city
        #Check if state is blank, return city only if so
        if self.state != '':
            s = s + ', ' + self.state
        else:
            return s
        #Check if ZIP is blank, return city, ST if so
        if self.zip != '':
            s = s + ' ' + self.zip
        else:
            return s
        #If all three not empty, return the whole deal
        return self.city + ", " + self.state + " " + self.zip

    def string_phone(self) -> str:
        p = self.phone
        if(len(p)==10):
            return f'({p[:3]}) {p[3:6]}-{p[6:]}'

    def string_wingspan(self) -> str:
        if self.wingspan > 0:
            return f'{self.strip_num(self.wingspan)} {self.wingspan_units}'
        else:
            return ''

    def string_swath(self) -> str:
        if self.swath > 0:
            return str(self.swath)+' '+self.swath_units
        else:
            return ''

    def string_rate(self) -> str:
        if self.rate > 0:
            return f'{self.strip_num(self.rate)} {self.rate_units}'
        else:
            return ''

    def string_pressure(self) -> str:
        if self.pressure > 0:
            return f'{self.strip_num(self.pressure)} {self.pressure_units}'
        else:
            return ''

    def string_nozzle_1(self) -> str:
        degree_sign= u'\N{DEGREE SIGN}'
        if self.nozzle_type_1 != '':
            return (f'{self.nozzle_type_1} @ {self.nozzle_deflection_1}{degree_sign}'+'\n'
                +f'Orif#{self.nozzle_size_1} x{str(self.nozzle_quantity_1)}')
        else:
            return ' \n '

    def string_nozzle_2(self) -> str:
        degree_sign= u'\N{DEGREE SIGN}'
        if self.nozzle_type_2 != '':
            return (f'{self.nozzle_type_2} @ {self.nozzle_deflection_2}{degree_sign}'+'\n'
                +f'Orif#{self.nozzle_size_2} x{str(self.nozzle_quantity_2)}')
        else:
            return ' \n '

    def string_boom_width(self) -> str:
        if self.boom_width > 0:
            return f'{self.strip_num(self.boom_width)} {self.boom_width_units}'
        else:
            return ''

    def string_boom_drop(self) -> str:
        if self.boom_drop > 0:
            return f'{self.strip_num(self.boom_drop)} {self.boom_drop_units}'
        else:
            return ''

    def string_nozzle_spacing(self) -> str:
        if self.nozzle_spacing > 0:
            return f'{self.strip_num(self.nozzle_spacing)} {self.nozzle_spacing_units}'
        else:
            return ''

    def string_temperature(self) -> str:
        if self.temperature > 0:
            return f'{self.strip_num(self.temperature)} {self.temperature_units}'
        else:
            return ''

    def string_humidity(self) -> str:
        if self.humidity > 0:
            return f'{self.strip_num(self.humidity)}%'
        else:
            return ''

    def string_series(self) -> str:
        return f'{self.strip_num(self.series)}'

    def strip_num(self, x, precision = 2, zeroBlank = False) -> str:
        if type(x) is str:
            if x == '':
                x = 0
        if zeroBlank and x == 0:
            return ''
        if float(x).is_integer():
            return str(int(float(x)))
        else:
            return f'{round(float(x), 2):.{precision}f}'

    def set_wingspan(self, string) -> bool:
        try:
            float(string)
        except ValueError:
            return False
        self.wingspan = float(string)
        return True

    def set_swath(self, string) -> bool:
        try:
            int(float(string))
        except ValueError:
            return False
        self.swath = int(float(string))
        return True

    def set_swath_adjusted(self, string) -> bool:
        try:
            int(float(string))
        except ValueError:
            return False
        self.swath_adjusted = int(float(string))
        return True

    def set_rate(self, string) -> bool:
        try:
            float(string)
        except ValueError:
            return False
        self.rate = float(string)
        return True

    def set_pressure(self, string) -> bool:
        try:
            float(string)
        except ValueError:
            return False
        self.pressure = float(string)
        return True

    def set_nozzle_quantity_1(self, string) -> bool:
        try:
            int(float(string))
        except ValueError:
            return False
        self.nozzle_quantity_1 = int(float(string))
        return True

    def set_nozzle_quantity_2(self, string) -> bool:
        try:
            int(string)
        except ValueError:
            return False
        self.nozzle_quantity_2 = int(string)
        return True

    def set_boom_width(self, string) -> bool:
        try:
            float(string)
        except ValueError:
            return False
        self.boom_width = float(string)
        return True

    def set_boom_drop(self, string) -> bool:
        try:
            float(string)
        except ValueError:
            return False
        self.boom_drop = float(string)
        return True

    def set_nozzle_spacing(self, string) -> bool:
        try:
            float(string)
        except ValueError:
            return False
        self.nozzle_spacing = float(string)
        return True

    def set_num(self, field, string, type) -> bool:
        try:
            if type == 'int':
                field = int(string)
            else:
                field = float(string)
            return True
        except ValueError:
            return False
