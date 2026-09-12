"""Turn a spectrometer failure into something an operator can act on.

`diagnose()` probes as far as it can get and returns a Diagnosis: a plain
language verdict, the steps most likely to fix it, and a technical report to
paste into a support email. The GUI renders it; nothing here imports Qt.

The guidance matters more than the probe. A pilot at a fly-in whose
spectrometer will not connect needs "close OceanView and try again", not an
error code -- so each failure mode carries ordered steps, most likely fix
first.
"""

import platform
import sys
from dataclasses import dataclass, field

import accupatt.config as cfg
from accupatt.hardware import spectrometer as spec_backend

# Verdicts. "ok" means a device was opened and read from successfully.
OK = "ok"
NO_DRIVER = "no_driver"
DRIVER_LOAD_FAILED = "driver_load_failed"
NO_DEVICE = "no_device"
OPEN_FAILED = "open_failed"
DEVICE_ERROR = "device_error"


@dataclass
class Diagnosis:
    status: str
    headline: str
    explanation: str
    steps: list[str] = field(default_factory=list)
    details: list[tuple[str, str]] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return self.status == OK

    def as_report(self) -> str:
        """Plain-text version, for the clipboard."""
        lines = [
            "AccuPatt Spectrometer Diagnostic",
            "=" * 40,
            "",
            self.headline,
            "",
            self.explanation,
            "",
        ]
        if self.steps:
            lines.append("Suggested steps:")
            lines += [f"  {i}. {s}" for i, s in enumerate(self.steps, 1)]
            lines.append("")
        lines.append("Technical details:")
        width = max((len(label) for label, _ in self.details), default=0)
        lines += [f"  {label.ljust(width)}  {value}" for label, value in self.details]
        return "\n".join(lines)


def _environment() -> list[tuple[str, str]]:
    return [
        ("AccuPatt", cfg.get_version_string()),
        (
            "Platform",
            f"{platform.system()} {platform.release()} ({platform.machine()})",
        ),
        ("Python", sys.version.split()[0]),
        ("Frozen build", "yes" if getattr(sys, "frozen", False) else "no (source)"),
    ]


def diagnose() -> Diagnosis:
    """Probe the spectrometer stack and report how far it got."""
    details = _environment()

    if not spec_backend.backend_available():
        details.append(("OceanDirect SDK", "NOT LOADED"))
        return Diagnosis(
            status=NO_DRIVER,
            headline="Spectrometer driver not found",
            explanation=(
                "AccuPatt includes the OceanDirect spectrometer driver, so this "
                "normally means the installation is incomplete or some files "
                "were removed after installing."
            ),
            steps=[
                "Reinstall AccuPatt from the official installer.",
                "If your antivirus quarantined files during installation, allow "
                "AccuPatt and reinstall.",
                "If you are running AccuPatt from source, install the OceanDirect "
                "SDK and run: python tools/sync_oceandirect.py",
            ],
            details=details,
        )

    sdk_version = spec_backend.sdk_version()
    details.append(("OceanDirect SDK", sdk_version if sdk_version else "NOT LOADED"))

    try:
        spec = spec_backend.open_first_device()
    except spec_backend.DriverLoadError as e:
        details.append(("Open attempt", f"FAILED — {e}"))
        return Diagnosis(
            status=DRIVER_LOAD_FAILED,
            headline="Spectrometer driver is present but failed to load",
            explanation=(
                "AccuPatt found the OceanDirect driver files, but the "
                "underlying library did not load. This points to an incomplete "
                "or corrupted installation rather than a cabling or hardware "
                "issue — closing other programs or reseating the USB cable "
                "will not fix this."
            ),
            steps=[
                "Reinstall AccuPatt from the official installer.",
                "If your antivirus quarantined files during installation, allow "
                "AccuPatt and reinstall.",
                "If the problem continues, copy the details below and send them "
                "to AccuPatt support.",
            ],
            details=details,
        )
    except spec_backend.SpectrometerError as e:
        details.append(("Open attempt", f"FAILED — {e}"))
        return Diagnosis(
            status=OPEN_FAILED,
            headline="Spectrometer found, but AccuPatt could not open it",
            explanation=(
                "A spectrometer is connected, but AccuPatt was not able to take "
                "control of it. Most often another program already has it open."
            ),
            steps=[
                "Close any other spectrometer software — OceanView, SpectraSuite, "
                "or an OceanDirect sample program.",
                "Close any other AccuPatt window that may be using the "
                "spectrometer, then rescan.",
                "Unplug the spectrometer, wait five seconds, plug it back in, "
                "then rescan.",
                "If it still fails, restart the computer and try again.",
            ],
            details=details,
        )

    if spec is None:
        details.append(("Devices found", "0"))
        return Diagnosis(
            status=NO_DEVICE,
            headline="No spectrometer detected",
            explanation=(
                "The driver loaded correctly, but no Ocean Optics spectrometer is "
                "responding over USB. This is almost always a cable, power, or "
                "port issue."
            ),
            steps=[
                "Check the USB cable is fully seated at both the spectrometer and "
                "the computer.",
                "Confirm the spectrometer's indicator light is on.",
                "Plug directly into the computer rather than through a USB hub, "
                "docking station, or extension cable.",
                "Try a different USB port, then rescan.",
                "Unplug the spectrometer, wait five seconds, plug it back in, "
                "then rescan.",
            ],
            details=details,
        )

    # A device opened. Confirm it actually reads before calling it healthy.
    try:
        details.append(("Devices found", "1"))
        details.append(("Model", spec.model))
        details.append(("Serial number", spec.serial_number))
        wavelengths = spec.wavelengths
        details.append(("Pixels", f"{spec.pixel_count}"))
        details.append(
            (
                "Wavelength range",
                f"{float(wavelengths[0]):.1f} – {float(wavelengths[-1]):.1f} nm",
            )
        )
        details.append(("Max intensity", f"{int(spec.max_intensity)} AU"))
        details.append(
            (
                "Integration range",
                f"{spec.min_integration_time_ms:.3f} – "
                f"{spec.max_integration_time_ms:.0f} ms",
            )
        )
        frame = spec.intensities()
        details.append(
            (
                "Test reading",
                f"{len(frame)} pixels, min {frame.min():.0f} / "
                f"max {frame.max():.0f} AU",
            )
        )
    except Exception as e:
        details.append(("Test reading", f"FAILED — {e}"))
        return Diagnosis(
            status=DEVICE_ERROR,
            headline="Spectrometer is connected but not responding correctly",
            explanation=(
                "AccuPatt opened the spectrometer but could not read a spectrum "
                "from it. This can indicate a cable fault or a device that needs "
                "to be power cycled."
            ),
            steps=[
                "Unplug the spectrometer, wait five seconds, plug it back in, "
                "then rescan.",
                "Try a different USB cable and a different port.",
                "If the problem continues, copy the details below and send them "
                "to AccuPatt support.",
            ],
            details=details,
        )
    finally:
        try:
            spec.close()
        except Exception:
            pass

    return Diagnosis(
        status=OK,
        headline="Spectrometer is working",
        explanation=(
            "AccuPatt found the spectrometer, opened it, and read a spectrum "
            "successfully."
        ),
        details=details,
    )
