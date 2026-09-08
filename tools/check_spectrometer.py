"""Exercise every spectrometer adapter method against real hardware.

Run with a spectrometer attached:

    poetry run python tools/check_spectrometer.py

Useful two ways: as a regression check after touching accupatt/hardware, and as
a field diagnostic when someone reports that AccuPatt will not see their
spectrometer -- it separates "no SDK" from "no device" from "device misbehaving"
without going through the GUI.

Anything flagged FAIL or DIFFERS is a real problem.
"""

import sys
from pathlib import Path

# Running this as a script puts tools/ on sys.path, not the repo root, so the
# accupatt and oceandirect imports below would only resolve via Poetry's
# editable-install .pth. Add the repo root explicitly so it works under a plain
# interpreter too.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np

import accupatt.config as cfg
from accupatt.hardware import spectrometer as sb
from accupatt.models.dye import Dye

ok = True


def check(label, condition, detail=""):
    global ok
    mark = "PASS" if condition else "FAIL"
    if not condition:
        ok = False
    print(f"  [{mark}] {label}" + (f" — {detail}" if detail else ""))


print("=" * 68)
print("1. Backend")
print("=" * 68)
check("SDK importable", sb.backend_available())
if not sb.backend_available():
    sys.exit("\nNo SDK staged. Run: python tools/sync_oceandirect.py")

try:
    spec = sb.open_first_device()
except sb.SpectrometerError as e:
    sys.exit(f"\nSpectrometerError: {e}")

if spec is None:
    sys.exit("\nNo spectrometer found. Plug one in and re-run.")

print("\n" + "=" * 68)
print("2. Identity / capabilities  (compare against the Test Spectrometer panel)")
print("=" * 68)
x = spec.wavelengths
print(f"  model                     {spec.model}")
print(f"  serial_number             {spec.serial_number}")
print(f"  pixel_count               {spec.pixel_count} px")
print(f"  wavelength range          {float(x[0]):.1f} – {float(x[-1]):.1f} nm")
print(f"  max_intensity             {int(spec.max_intensity)} AU")
print(
    f"  integration range         {spec.min_integration_time_ms:.3f} – "
    f"{spec.max_integration_time_ms:.0f} ms"
)
print(f"  integration increment     {spec.integration_time_increment_us} µs")

check(
    "pixel_count matches wavelength array",
    spec.pixel_count == len(x),
    f"{spec.pixel_count} vs {len(x)}",
)
check("wavelengths ascending", bool(np.all(np.diff(x) > 0)))
check("wavelengths read-only", not x.flags.writeable)

print("\n" + "=" * 68)
print("3. index_at_wavelength  (adapter unified this; must match argmin)")
print("=" * 68)
dye = Dye.fromConfig(cfg.get_defined_dye())
print(
    f"  dye: {dye.name}  ex={dye.wavelength_excitation} nm  "
    f"em={dye.wavelength_emission} nm  boxcar={dye.boxcar_width} nm"
)
for label, nm in [
    ("excitation", dye.wavelength_excitation),
    ("emission", dye.wavelength_emission),
]:
    adapter = spec.index_at_wavelength(nm)
    argmin = int(np.abs(x - nm).argmin())
    check(
        f"{label} index agrees with argmin",
        adapter == argmin,
        f"adapter={adapter} argmin={argmin} ({float(x[adapter]):.2f} nm)",
    )

print("\n" + "=" * 68)
print("4. Configuration")
print("=" * 68)
spec.set_integration_time_ms(dye.integration_time_milliseconds)
print(f"  set_integration_time_ms({dye.integration_time_milliseconds}) ok")
spec.enable_corrections()
print("  enable_corrections() ok")

nm_per_pixel = float(x[-1] - x[0]) / (len(x) - 1)
expected = max(0, round(dye.boxcar_width / 2 / nm_per_pixel))
actual = spec.set_boxcar_width_nm(dye.boxcar_width)
check(
    "boxcar half-width matches old inline formula",
    actual == expected,
    f"adapter={actual} expected={expected} ({nm_per_pixel:.4f} nm/px)",
)

print("\n" + "=" * 68)
print("5. Acquisition")
print("=" * 68)
for i in range(3):
    y = spec.intensities()
    check(
        f"frame {i+1}: length matches pixel_count",
        len(y) == spec.pixel_count,
        f"{len(y)}",
    )
    check(f"frame {i+1}: dtype float32", y.dtype == np.float32, str(y.dtype))
    check(f"frame {i+1}: finite", bool(np.all(np.isfinite(y))))
    print(
        f"         min={y.min():.1f}  max={y.max():.1f}  "
        f"ex_px={y[spec.index_at_wavelength(dye.wavelength_excitation)]:.1f}  "
        f"em_px={y[spec.index_at_wavelength(dye.wavelength_emission)]:.1f}"
    )

print("\n" + "=" * 68)
print("6. Lifecycle")
print("=" * 68)
spec.close()
print("  close() ok")
reopened = sb.open_first_device()
check("device reopens after close", reopened is not None)
if reopened:
    reopened.close()
    print("  reopened and closed ok")

print("\n" + "=" * 68)
print("ALL CHECKS PASSED" if ok else "SOME CHECKS FAILED — see FAIL lines above")
print("=" * 68)
sys.exit(0 if ok else 1)
