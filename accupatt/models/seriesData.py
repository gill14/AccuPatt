import uuid
import accupatt.config as cfg
import numpy as np
from accupatt.helpers.atomizationModel import AtomizationModelMulti
from accupatt.models.appInfo import AppInfo
from accupatt.models.passData import Pass
from accupatt.models.seriesDataCard import SeriesDataCard
from accupatt.models.seriesDataString import SeriesDataString


class SeriesData:
    """A Container class for storing all Series info"""

    def __init__(self, id=""):
        self.id = id
        if self.id == "":
            self.id = str(uuid.uuid4())
        self.info = AppInfo()
        self.passes: list[Pass] = []
        self.string = SeriesDataString(
            self.passes
        )
        self.cards = SeriesDataCard(self.passes)

    """
    Common pass observable sharing
    """

    def fill_common_pass_observables(self):
        ph = self._fill_zeros_with_last(
            np.array([p.pass_heading for p in self.passes])[::-1]
        )
        t = self._fill_zeros_with_last(
            np.array([p.temperature for p in self.passes])[::-1]
        )
        h = self._fill_zeros_with_last(
            np.array([p.humidity for p in self.passes])[::-1]
        )
        for i, p in enumerate(self.passes):
            p.set_pass_heading(ph[i])
            p.set_temperature(t[i])
            p.set_humidity(h[i])

    def _fill_zeros_with_last(self, arr):
        prev = np.arange(len(arr))
        prev[arr == -1] = 0
        prev = np.maximum.accumulate(prev)
        return arr[prev]

    """
    GET methods below optionally take imposed unit, otherwise find most common unit, convert values and return a tuple
    containing (mean_value, mean_value_units, mean_value_and_units_string)
    """

    def get_airspeed_mean(
        self, units=None, string_included=False, cards_included=False
    ) -> tuple[int, str, str]:
        passes = self.get_includable_passes(string_included, cards_included)
        units = (
            units
            if units
            else self._get_common_unit([p.ground_speed_units for p in passes])
        )
        values = np.array([p.get_airspeed(units)[0] for p in passes])
        values = values[values >= 0]
        if values.size == 0:
            return 0, "-", "-"
        value = values.mean()
        return value, units, f"{value:.3g} {units}"

    def get_spray_height_mean(
        self, units=None, string_included=False, cards_included=False
    ) -> tuple[float, str, str]:
        passes = self.get_includable_passes(string_included, cards_included)
        units = (
            units
            if units
            else self._get_common_unit([p.spray_height_units for p in passes])
        )
        values = np.array([p.get_spray_height(units)[0] for p in passes])
        values = values[values >= 0]
        if values.size == 0:
            return 0, "-", "-"
        value = values.mean()
        return value, units, f"{value:.3g} {units}"

    def get_wind_speed_mean(
        self, units=None, string_included=False, cards_included=False
    ) -> tuple[float, str, str]:
        passes = self.get_includable_passes(string_included, cards_included)
        units = (
            units
            if units
            else self._get_common_unit([p.wind_speed_units for p in passes])
        )
        values = np.array([p.get_wind_speed(units)[0] for p in passes])
        values = values[values >= 0]
        if values.size == 0:
            return 0, "-", "-"
        value = values.mean()
        return value, units, f"{value:.2g} {units}"

    def get_crosswind_mean(
        self, units=None, string_included=False, cards_included=False
    ) -> tuple[float, str, str]:
        passes = self.get_includable_passes(string_included, cards_included)
        units = (
            units
            if units
            else self._get_common_unit([p.wind_speed_units for p in passes])
        )
        values = np.array([p.get_crosswind(units)[0] for p in passes])
        values = values[values != -1]
        if values.size == 0:
            return 0, "-", "-"
        value = values.mean()
        return value, units, f"{value:.2g} {units}"

    def get_temperature_mean(
        self, units=None, string_included=False, cards_included=False
    ) -> tuple[float, str, str]:
        passes = self.get_includable_passes(string_included, cards_included)
        units = (
            units
            if units
            else self._get_common_unit([p.temperature_units for p in passes])
        )
        values = np.array([p.get_temperature(units)[0] for p in passes])
        values = values[values >= 0]
        if values.size == 0:
            return 0, "-", "-"
        value = values.mean()
        return value, units, f"{value:.3g} {units}"

    def get_humidity_mean(
        self, string_included=False, cards_included=False
    ) -> tuple[float, str, str]:
        passes = self.get_includable_passes(string_included, cards_included)
        values = np.array([p.get_humidity()[0] for p in passes])
        values = values[values >= 0]
        if values.size == 0:
            return 0, "-", "-"
        value = values.mean()
        return value, "%", f"{value:.3g}%"

    def get_includable_passes(self, string_included, cards_included):
        includablePasses: list[Pass] = []
        for p in self.passes:
            include = False
            if string_included and p.string.is_active():
                include = True
            if cards_included and p.cards.is_active():
                include = True
            if include:
                includablePasses.append(p)
        return includablePasses

    def _get_common_unit(self, units: list[str]) -> str:
        return max(set(units), key=units.count)

    # Run USDA Model on input params and observables
    def calc_droplet_stats(
        self, string_included=False, cards_included=False
    ) -> tuple[str, str, str, str, str]:
        model = AtomizationModelMulti()
        for n in self.info.nozzles:
            model.addNozzleSet(
                name=n.type,
                orifice=n.size,
                airspeed=self.get_airspeed_mean(
                    units=cfg.UNIT_MPH,
                    string_included=string_included,
                    cards_included=cards_included,
                )[0],
                pressure=self.info.get_pressure(units=cfg.UNIT_PSI),
                angle=n.deflection,
                quantity=n.quantity,
            )
        dv01 = model.dv01()
        dv05 = model.dv05()
        dv09 = model.dv09()
        # pl100 = model.p_lt_100()
        # pl200 = model.p_lt_200()
        dsc = model.dsc()
        rs = model.rs()
        return (
            f"{dv01} μm" if dv01 > 0 else "-",
            f"{dv05} μm" if dv05 > 0 else "-",
            f"{dv09} μm" if dv09 > 0 else "-",
            dsc if dsc != "" else "-",
            f"{rs:.2f}" if dv01 > 0 and dv05 > 0 else "-",
        )
