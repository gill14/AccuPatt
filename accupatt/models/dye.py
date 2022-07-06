import accupatt.config as cfg

class Dye:
    
    def __init__(self, name: str, wavelength_excitation: int, wavelength_emission: int, integration_time_milliseconds: int, boxcar_width: int = 0):
        self.name = name
        self.wavelength_excitation = wavelength_excitation
        self.wavelength_emission = wavelength_emission
        self.integration_time_milliseconds = integration_time_milliseconds
        self.boxcar_width = boxcar_width
        
    def toDict(self) -> dict:
        d = {}
        d["name"] = self.name
        d["wavelength_excitation"] = self.wavelength_excitation
        d["wavelength_emission"] = self.wavelength_emission
        d["integration_time_milliseconds"] = self.integration_time_milliseconds
        d["boxcar_width"] = self.boxcar_width
        return d
    
    @classmethod
    def fromDict(cls, d: dict):
        return cls(name=d["name"],
                   wavelength_excitation=d["wavelength_excitation"],
                   wavelength_emission=d["wavelength_emission"],
                   integration_time_milliseconds=d["integration_time_milliseconds"],
                   boxcar_width=d["boxcar_width"])
        
    @classmethod
    def fromConfig(cls, name: str = ""):
        dye_list = cfg.get_defined_dyes()
        dye_name = name if bool(name) else cfg.get_defined_dye()
        dye_dict = [d for d in dye_list if d["name"]==dye_name][0]
        return cls.fromDict(dye_dict)
        