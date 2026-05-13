from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Coefficients:
    """The 15 polynomial coefficients of a single droplet-spectrum output."""

    intercept: float
    orifice: float
    airspeed: float
    pressure: float
    angle: float
    orifice_airspeed: float
    orifice_pressure: float
    airspeed_pressure: float
    orifice_angle: float
    airspeed_angle: float
    pressure_angle: float
    orifice_squared: float
    airspeed_squared: float
    pressure_squared: float
    angle_squared: float


@dataclass(frozen=True)
class CCD:
    """Central-composite-design normalization (sub, div) per input parameter."""

    orifice_sub: float
    orifice_div: float
    airspeed_sub: float
    airspeed_div: float
    pressure_sub: float
    pressure_div: float
    angle_sub: float
    angle_div: float


@dataclass(frozen=True)
class Model:
    """One atomization model (low-speed or high-speed) for a single nozzle."""

    name: str
    airspeeds: tuple[float, ...]
    angles: tuple[float, ...]
    pressures: tuple[float, ...]
    ccd: CCD
    coeff_dv10: Coefficients
    coeff_dv50: Coefficients
    coeff_dv90: Coefficients
    coeff_v100: Coefficients
    coeff_v200: Coefficients


@dataclass(frozen=True)
class FlowRate:
    """FR = a * P^b  (P in psi, FR in gpm)."""

    a: float
    b: float


@dataclass(frozen=True)
class Orifice:
    size: float
    # Most nozzles: one FlowRate. AccuFlow: keyed by restrictor size.
    flow: FlowRate | dict[float, FlowRate]


@dataclass(frozen=True)
class Nozzle:
    name: str
    angle_description: str
    orifices: tuple[Orifice, ...]
    models: tuple[Model, ...]
