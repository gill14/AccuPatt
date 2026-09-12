"""Backend-agnostic spectrometer access for AccuPatt.

This module is the *only* place in AccuPatt that imports the OceanDirect SDK.
Everything above it talks to the ``Spectrometer`` wrapper defined here.

Two reasons that boundary matters:

1. Licensing. AccuPatt redistributes the OceanDirect runtime under the
   OceanDirect API Terms, which permit distribution only as part of an
   application providing substantial additional functionality (API Terms
   1.2(a)) and prohibit use of the APIs with non-Ocean Optics hardware
   (API Terms 2.1). Any future non-Ocean device -- the USDA-ARS system, for
   instance -- must be added as a *separate backend* in this module. It must
   never be driven through OceanDirect.

2. Availability. The SDK may legitimately be absent (a source checkout whose
   developer has not installed it, or a user who declined the bundled driver).
   Callers use ``backend_available()`` and the ``open_first_device()`` contract
   below instead of guarding imports themselves.
"""

import numpy as np

try:
    from oceandirect.OceanDirectAPI import OceanDirectAPI

    _BACKEND_AVAILABLE = True
except ImportError:
    _BACKEND_AVAILABLE = False


class SpectrometerError(Exception):
    """A spectrometer was present but could not be opened or configured."""


class DriverLoadError(SpectrometerError):
    """The OceanDirect SDK is importable but its native library didn't load.

    Distinct from other SpectrometerErrors: this means the DLL/dylib itself
    is missing, the wrong architecture, or not where the vendored
    sdk_properties.py expects it -- a packaging problem, not "a device is
    present but something else has it open".
    """


def backend_available() -> bool:
    """True when the OceanDirect SDK is importable in this environment."""
    return _BACKEND_AVAILABLE


def sdk_version() -> "str | None":
    """The OceanDirect version actually loaded, or None if unavailable.

    Read from the library rather than any shipped header: the vendor's
    installer leaves OceanDirectProductVersion.h reporting the previous
    version after an in-place upgrade.
    """
    if not _BACKEND_AVAILABLE:
        return None
    try:
        return ".".join(str(n) for n in OceanDirectAPI().get_api_version_numbers())
    except Exception:
        return None


def open_first_device() -> "Spectrometer | None":
    """Open the first spectrometer found on the USB bus.

    Returns None when the backend is present but no device is attached.
    Raises SpectrometerError when the backend is missing, or when a device is
    present but cannot be opened.
    """
    if not _BACKEND_AVAILABLE:
        raise SpectrometerError("The OceanDirect driver is not installed.")
    try:
        api = OceanDirectAPI()
    except OSError as e:
        # cdll.LoadLibrary failed: the native library is missing, the wrong
        # architecture, or bundled somewhere sdk_properties.py won't look.
        raise DriverLoadError(
            f"The OceanDirect native library could not be loaded: {e}"
        ) from e
    try:
        api.find_usb_devices()
        device_ids = api.get_device_ids()
        if not device_ids:
            return None
        return Spectrometer(api.open_device(device_ids[0]))
    except SpectrometerError:
        raise
    except Exception as e:
        raise SpectrometerError(f"Unable to open spectrometer: {e}") from e


class Spectrometer:
    """An open spectrometer, wrapping one OceanDirect device handle.

    Integration times are microseconds at the hardware boundary, which is easy
    to get wrong; the setter here takes milliseconds to match how dyes are
    configured everywhere else in AccuPatt.
    """

    def __init__(self, device):
        self._device = device
        # Wavelength calibration is fixed for the life of the device, and both
        # the live plot and the boxcar conversion below need it per-frame.
        self._wavelengths = np.array(device.get_wavelengths(), dtype=np.float32)
        # Handed out by reference below; make a stray write fail loudly rather
        # than silently corrupt every later reading.
        self._wavelengths.flags.writeable = False

    # -- Lifecycle ---------------------------------------------------------

    def close(self) -> None:
        self._device.close_device()

    # -- Identity / capabilities -------------------------------------------

    @property
    def model(self) -> str:
        return self._device.get_model()

    @property
    def serial_number(self) -> str:
        return self._device.get_serial_number()

    @property
    def pixel_count(self) -> int:
        return self._device.get_spectrum_length()

    @property
    def max_intensity(self) -> float:
        return self._device.get_max_intensity()

    @property
    def min_integration_time_ms(self) -> float:
        return self._device.get_minimum_integration_time() / 1000

    @property
    def max_integration_time_ms(self) -> float:
        return self._device.get_maximum_integration_time() / 1000

    @property
    def integration_time_increment_us(self) -> int:
        return self._device.get_integration_time_increment()

    @property
    def wavelengths(self) -> np.ndarray:
        return self._wavelengths

    # -- Configuration -----------------------------------------------------

    def set_integration_time_ms(self, milliseconds: float) -> None:
        self._device.set_integration_time(int(milliseconds * 1000))

    def enable_corrections(self) -> None:
        """Turn on dark-pixel and nonlinearity correction where supported."""
        self._device.set_nonlinearity_correction_usage(True)
        self._device.set_electric_dark_correction_usage(True)

    def set_boxcar_width_nm(self, width_nm: float) -> int:
        """Set the boxcar filter from a width in nm.

        The device wants a half-width in pixels, so convert using this
        device's own dispersion. Returns the half-width applied, which callers
        display alongside the requested nm value.
        """
        x = self._wavelengths
        nm_per_pixel = float(x[-1] - x[0]) / (len(x) - 1)
        half_width = max(0, round(width_nm / 2 / nm_per_pixel))
        self._device.set_boxcar_width(half_width)
        return half_width

    # -- Acquisition -------------------------------------------------------

    def intensities(self) -> np.ndarray:
        """One full spectrum, corrected per ``enable_corrections()``."""
        return np.array(self._device.get_formatted_spectrum(), dtype=np.float32)

    def index_at_wavelength(self, nm: float) -> int:
        """Pixel index nearest the given wavelength."""
        try:
            index, _wavelength = self._device.get_index_at_wavelength(nm)
            return int(index)
        except Exception:
            # Not every device exposes the lookup; the calibration array gives
            # the same answer.
            return int(np.abs(self._wavelengths - nm).argmin())
