"""USDA ARS Droplet Size Models (2026 update).

Authors: Bradley Fritz, Matt Gill.
Functional access to the USDA atomization models, backed by per-nozzle
dataclasses in `nozzles/`.
"""

from __future__ import annotations

import numpy as np

from .nozzles import NOZZLES
from .reference import DSC_REFERENCE, EXCLUDED_NOZZLES
from .types import FlowRate, Model, Nozzle


# User-facing nozzle list. CP09, Davidon TriSet, CAS LF-5 are parsed into
# their SS / Deflection variants at runtime based on angle.
_PRIMARY_NOZZLES: tuple[str, ...] = (
    "AccuFlow Single Row",
    "AccuFlow Double Row",
    "AFS SS",
    "CAS LF-5",
    "Ceramic Disc Core 45",
    "Ceramic Disc Core SS",
    "CP-01-03",
    "CP-07-3E",
    "CP03",
    "CP09",
    "CP11TT SS",
    "CP11TT 20°FF",
    "CP11TT 40°FF",
    "CP11TT 60°FF",
    "CP11TT 80°FF",
    "CP11TT 110°FF",
    "Davidon TriSet",
    "Standard 40°FF",
    "Standard 80°FF",
    "Steel Disc Core 45",
    "Steel Disc Core SS",
    "TeeJet H1 4U",
    "TeeJet SS",
)


def _resolve_nozzle(name: str, angle) -> str:
    """Map user-facing Nozzle → the internal SS / Deflection variant."""
    if name == "CP09":
        try:
            return "CP09 SS" if int(angle) == 0 else "CP09 Deflection"
        except (TypeError, ValueError):
            return "CP09 Deflection"
    if name == "Davidon TriSet":
        try:
            return (
                "Davidon TriSet SS" if int(angle) == 0 else "Davidon TriSet Deflection"
            )
        except (TypeError, ValueError):
            return "Davidon TriSet Deflection"
    if name == "CAS LF-5":
        try:
            return "CAS LF-5 SS" if int(angle) == 0 else "CAS LF-5 Deflection"
        except (TypeError, ValueError):
            return "CAS LF-5 Deflection"
    if name == "CP-07-3E":
        try:
            return "CP-07-3E SS" if int(angle) == 0 else "CP-07-3E Deflection"
        except (TypeError, ValueError):
            return "CP-07-3E Deflection"
    return name


def _applicable_model(nozzle: Nozzle, airspeed) -> Model | None:
    for m in nozzle.models:
        if not m.airspeeds:
            continue
        lo, hi = m.airspeeds[0], m.airspeeds[-1]
        # Inclusive at upper end of the highest-speed regime; otherwise half-open.
        if m.name == "high-speed":
            if lo <= airspeed <= hi:
                return m
        else:
            if lo <= airspeed < hi:
                return m
    return None


def _coerce_member(value, members: tuple):
    """If value is a string and matches a member's str(), coerce to the member's type."""
    if isinstance(value, str):
        str_members = [str(v) for v in members]
        if value in str_members:
            return members[str_members.index(value)]
    return value


def _flow_rate(orifice_flow, angle) -> FlowRate | None:
    """Return the FlowRate to use given an orifice.flow and the resolved 'angle' (= restrictor for AccuFlow)."""
    if isinstance(orifice_flow, FlowRate):
        return orifice_flow
    # Per-restrictor mapping for AccuFlow
    if isinstance(orifice_flow, dict):
        if angle in orifice_flow:
            return orifice_flow[angle]
        # Fuzzy match: pick the nearest restrictor key if numeric
        try:
            target = float(angle)
            nearest = min(orifice_flow.keys(), key=lambda k: abs(k - target))
            if abs(nearest - target) <= 1e-6:
                return orifice_flow[nearest]
        except (TypeError, ValueError):
            pass
    return None


def _poly(coeff, o_a, a_a, p_a, an_a) -> float:
    return (
        coeff.intercept
        + o_a * coeff.orifice
        + a_a * coeff.airspeed
        + p_a * coeff.pressure
        + an_a * coeff.angle
        + o_a * a_a * coeff.orifice_airspeed
        + o_a * p_a * coeff.orifice_pressure
        + a_a * p_a * coeff.airspeed_pressure
        + o_a * an_a * coeff.orifice_angle
        + a_a * an_a * coeff.airspeed_angle
        + p_a * an_a * coeff.pressure_angle
        + (o_a**2) * coeff.orifice_squared
        + (a_a**2) * coeff.airspeed_squared
        + (p_a**2) * coeff.pressure_squared
        + (an_a**2) * coeff.angle_squared
    )


class AtomizationModel:
    """Single-nozzle USDA atomization model."""

    # Preserved class attributes for existing callers.
    ref_nozzles = DSC_REFERENCE
    excluded_dict = EXCLUDED_NOZZLES
    nozzles: tuple[str, ...] = _PRIMARY_NOZZLES
    nozzles_extended: tuple[str, ...] = _PRIMARY_NOZZLES + tuple(EXCLUDED_NOZZLES.keys())

    def __init__(
        self,
        nozzle: str | None = None,
        orifice=None,
        airspeed=None,
        pressure=None,
        angle=None,
    ):
        self.nozzle = nozzle
        self.orifice = orifice
        self.airspeed = airspeed
        self.pressure = pressure
        self.angle = angle

    # ---- internal resolution ----

    def _resolve(self, nozzle, orifice, airspeed, pressure, angle):
        """Return (nozzle_obj, model, orifice, angle) or None if invalid."""
        if None in (nozzle, orifice, airspeed, pressure, angle):
            return None
        internal_name = _resolve_nozzle(nozzle, angle)
        nz = NOZZLES.get(internal_name)
        if nz is None:
            return None
        model = _applicable_model(nz, airspeed)
        if model is None:
            return None
        orifice = _coerce_member(orifice, tuple(o.size for o in nz.orifices))
        angle = _coerce_member(angle, model.angles)
        if orifice not in (o.size for o in nz.orifices):
            return None
        if model.angles and angle not in model.angles:
            return None
        if model.pressures and not (model.pressures[0] <= pressure <= model.pressures[-1]):
            return None
        return nz, model, orifice, angle

    def _calc(self, param, nozzle=None, orifice=None, airspeed=None, pressure=None, angle=None):
        n = self.nozzle if nozzle is None else nozzle
        o = self.orifice if orifice is None else orifice
        a = self.airspeed if airspeed is None else airspeed
        p = self.pressure if pressure is None else pressure
        an = self.angle if angle is None else angle
        resolved = self._resolve(n, o, a, p, an)
        if resolved is None:
            return -1
        nz, model, o, an = resolved
        if param == "GPM":
            orf = next((x for x in nz.orifices if x.size == o), None)
            if orf is None:
                return -1
            flow = _flow_rate(orf.flow, an)
            if flow is None:
                return -1
            return flow.a * (p ** flow.b)
        coeff = getattr(model, f"coeff_{param}")
        ccd = model.ccd
        o_a = (o - ccd.orifice_sub) / ccd.orifice_div
        a_a = (a - ccd.airspeed_sub) / ccd.airspeed_div
        p_a = (p - ccd.pressure_sub) / ccd.pressure_div
        an_a = (an - ccd.angle_sub) / ccd.angle_div if ccd.angle_div else 0.0
        return round(_poly(coeff, o_a, a_a, p_a, an_a))

    def _params_for_nozzle(self, nozzle: str, attr: str) -> list:
        """Union of valid orifice or angle values across the (possibly parsed) nozzle's models."""
        names: list[str] = [nozzle]
        if nozzle == "CP09":
            names = ["CP09 SS", "CP09 Deflection"]
        elif nozzle == "Davidon TriSet":
            names = ["Davidon TriSet SS", "Davidon TriSet Deflection"]
        elif nozzle == "CAS LF-5":
            names = ["CAS LF-5 SS", "CAS LF-5 Deflection"]
        elif nozzle == "CP-07-3E":
            names = ["CP-07-3E SS", "CP-07-3E Deflection"]
        vals: set = set()
        for name in names:
            nz = NOZZLES.get(name)
            if nz is None:
                continue
            if attr == "Orifice":
                vals.update(o.size for o in nz.orifices)
            elif attr == "Angle":
                for m in nz.models:
                    vals.update(m.angles)
        if nozzle in EXCLUDED_NOZZLES and attr in EXCLUDED_NOZZLES[nozzle]:
            vals.update(EXCLUDED_NOZZLES[nozzle][attr])
        return sorted(vals)

    # ---- DSC helpers ----

    def _dsc(self, dv01=None, dv05=None) -> str:
        if dv01 is None:
            dv01 = self.dv01()
        if dv05 is None:
            dv05 = self.dv05()
        if dv01 <= 0 or dv05 <= 0:
            return ""
        if np.isnan(dv01) or np.isnan(dv05):
            return ""
        dsc_01 = dsc_05 = ""
        for cat, ref in DSC_REFERENCE.items():
            if ref["DV01"][0] <= dv01 <= ref["DV01"][1]:
                dsc_01 = cat
            if ref["DV05"][0] <= dv05 <= ref["DV05"][1]:
                dsc_05 = cat
        dsc = dsc_05
        if dsc_01 and dsc_05 and DSC_REFERENCE[dsc_01]["RANK"] < DSC_REFERENCE[dsc_05]["RANK"]:
            dsc = dsc_01
        return dsc

    def _dsc_color(self, dsc: str) -> str:
        return DSC_REFERENCE.get(dsc, {}).get("Color", "#FFFFFF")

    def _dsc_color_dv(self, dv: int, dv_key: str) -> str:
        if dv <= 0:
            return "#FFFFFF"
        for cat, ref in DSC_REFERENCE.items():
            if ref[dv_key][0] <= dv <= ref[dv_key][1]:
                return ref["Color"]
        return "#FFFFFF"

    def _rs(self, dv01=None, dv05=None, dv09=None) -> float:
        if dv01 is None:
            dv01 = self.dv01()
        if dv05 is None:
            dv05 = self.dv05()
        if dv09 is None:
            dv09 = self.dv09()
        return (dv09 - dv01) / dv05

    # ---- public droplet metrics ----

    def dv01(self):
        return self._calc("dv10")

    def dv05(self):
        return self._calc("dv50")

    def dv09(self):
        return self._calc("dv90")

    def p_lt_100(self):
        return self._calc("v100")

    def p_lt_200(self):
        return self._calc("v200")

    def calc_gpm(self):
        return self._calc("GPM")

    def dsc(self, dv01=None, dv05=None) -> str:
        return self._dsc(dv01, dv05)

    def dsc_color(self, dv01=None, dv05=None) -> str:
        return self._dsc_color(self._dsc(dv01=dv01, dv05=dv05))

    def dsc_color_dv01(self, dv01=None) -> str:
        if dv01 is None:
            dv01 = self.dv01()
        return self._dsc_color_dv(dv01, "DV01")

    def dsc_color_dv05(self, dv05=None) -> str:
        if dv05 is None:
            dv05 = self.dv05()
        return self._dsc_color_dv(dv05, "DV05")

    def dsc_color_dv09(self, dv09=None) -> str:
        if dv09 is None:
            dv09 = self.dv09()
        return self._dsc_color_dv(dv09, "DV09")

    def rs(self, dv01=None, dv05=None, dv09=None) -> float:
        return self._rs(dv01, dv05, dv09)

    def get_nozzles(self) -> list[str]:
        return list(self.nozzles_extended)

    def get_orifices_for_nozzle(self, nozzle: str) -> list:
        return self._params_for_nozzle(nozzle, "Orifice")

    def get_deflections_for_nozzle(self, nozzle: str) -> list:
        return self._params_for_nozzle(nozzle, "Angle")


class AtomizationModelMulti(AtomizationModel):
    """Flow-weighted droplet stats over multiple nozzle sets."""

    def __init__(self):
        super().__init__()
        self.nozzleSets: list[list] = []

    def _calc_multi(self, param):
        numerator = 0.0
        denominator = 0.0
        for n in self.nozzleSets:
            size = self._calc(
                param,
                nozzle=n[0], orifice=n[1], airspeed=n[2], pressure=n[3], angle=n[4],
            )
            flow = self._calc(
                "GPM",
                nozzle=n[0], orifice=n[1], airspeed=n[2], pressure=n[3], angle=n[4],
            )
            if size < 0 or flow < 0:
                continue
            quantity = n[5]
            numerator += size * flow * quantity
            denominator += flow * quantity
        if denominator == 0:
            return -1
        return round(numerator / denominator)

    def addNozzleSet(self, name, orifice, airspeed, pressure, angle, quantity):
        self.nozzleSets.append([name, orifice, airspeed, pressure, angle, quantity])

    def clearNozzleSets(self):
        self.nozzleSets = []

    def dv01(self):
        return self._calc_multi("dv10")

    def dv05(self):
        return self._calc_multi("dv50")

    def dv09(self):
        return self._calc_multi("dv90")

    def p_lt_100(self):
        return self._calc_multi("v100")

    def p_lt_200(self):
        return self._calc_multi("v200")
