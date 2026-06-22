import os
import time

import numpy as np
from PyQt6 import uic
from PyQt6.QtCore import QObject, QThread, pyqtSignal
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QDialog
try:
    from oceandirect.OceanDirectAPI import OceanDirectAPI, Spectrometer
    _OCEANDIRECT_AVAILABLE = True
except ImportError:
    _OCEANDIRECT_AVAILABLE = False
import pyqtgraph

from accupatt.models.dye import Dye
import accupatt.config as cfg

Ui_Form, baseclass = uic.loadUiType(
    cfg.resource_path("resources", "testSpectrometer.ui")
)


class SpectrometerWorker(QObject):
    data_ready = pyqtSignal(np.ndarray)

    def __init__(self, spectrometer: "Spectrometer", interval_ms: int):
        super().__init__()
        self._spec = spectrometer
        self._interval_ms = interval_ms
        self._running = False

    def start(self):
        self._running = True
        self._acquire()

    def stop(self):
        self._running = False

    def _acquire(self):
        while self._running:
            raw = self._spec.get_formatted_spectrum()
            if raw:
                self.data_ready.emit(np.array(raw, dtype=np.float32))
            QThread.msleep(self._interval_ms)


class TestSpectrometer(baseclass):
    def __init__(self, spectrometer: Spectrometer, dye: Dye, parent=None):
        super().__init__(parent=parent)
        self.ui = Ui_Form()
        self.ui.setupUi(self)

        self.spec: Spectrometer = spectrometer
        self.spec.set_integration_time(dye.integration_time_milliseconds * 1000)
        self.spec.set_nonlinearity_correction_usage(True)
        self.spec.set_electric_dark_correction_usage(True)
        self.dye = dye

        self.pw: pyqtgraph.PlotWidget = self.ui.plotWidget
        self._use_rel = cfg.get_spectrometer_display_unit() == cfg.SPECTROMETER_DISPLAY_UNIT_RELATIVE
        self._unit_str = "%" if self._use_rel else "AU"

        # Init plot
        self.x = np.array(self.spec.get_wavelengths(), dtype=np.float32)
        nm_per_pixel = float(self.x[-1] - self.x[0]) / (len(self.x) - 1)
        hw_boxcar = max(0, round(dye.boxcar_width / 2 / nm_per_pixel))
        self.spec.set_boxcar_width(hw_boxcar)
        pyqtgraph.setConfigOptions(antialias=True)
        pyqtgraph.setConfigOption("background", "k")
        pyqtgraph.setConfigOption("foreground", "w")
        self.plot_item = self.pw.plotItem.plot(
            name="Measured", pen=pyqtgraph.mkPen("w", width=1.5)
        )
        self.plot_item.setDownsampling(auto=True, method="subsample")
        self.plot_item.setClipToView(True)
        self.pw.plotItem.setLabel(axis="bottom", text="Wavelength (nm)")
        self.pw.plotItem.setLabel(
            axis="left", text="Intensity (%)" if self._use_rel else "Intensity (AU)"
        )
        self.pw.getAxis("left").enableAutoSIPrefix(False)
        self.pw.plotItem.showGrid(x=True, y=True)
        x_min = float(self.x[0])
        x_max = float(self.x[-1])
        self.pw.setXRange(x_min, x_max, padding=0.0)
        if (
            cfg.get_spectrometer_display_unit()
            == cfg.SPECTROMETER_DISPLAY_UNIT_RELATIVE
        ):
            y_max = 100.0
        else:
            y_max = 65535.0
        self.pw.setYRange(0.0, y_max, padding=0.0)
        self.pw.plotItem.getViewBox().setLimits(
            minXRange=x_min,
            maxXRange=x_max,
            minYRange=0.0,
            maxYRange=y_max,
            xMin=x_min,
            xMax=x_max,
            yMin=0.0,
        )

        # Init cursors
        self.pix_ex = np.abs(self.x - self.dye.wavelength_excitation).argmin()
        self._ex_nm_str = f"{float(self.x[self.pix_ex]):.1f} nm"
        ex_rgb = self._get_rgb_from_wavelength(self.dye.wavelength_excitation)
        self._line_ex = pyqtgraph.InfiniteLine(
            pos=float(self.x[self.pix_ex]),
            pen=pyqtgraph.mkPen(QColor(ex_rgb[0], ex_rgb[1], ex_rgb[2])),
            label=f"Excitation\n{self._ex_nm_str}\n- {self._unit_str}",
            labelOpts={
                "color": QColor(ex_rgb[0], ex_rgb[1], ex_rgb[2]),
                "position": 0.9,
                "anchors": [(1, 0.9), (1, 0.9)],
            },
        )
        self.pw.addItem(self._line_ex)

        self.pix_em = np.abs(self.x - self.dye.wavelength_emission).argmin()
        self._em_nm_str = f"{float(self.x[self.pix_em]):.1f} nm"
        em_rgb = self._get_rgb_from_wavelength(self.dye.wavelength_emission)
        self._line_em = pyqtgraph.InfiniteLine(
            pos=float(self.x[self.pix_em]),
            pen=pyqtgraph.mkPen(QColor(em_rgb[0], em_rgb[1], em_rgb[2])),
            label=f"Emission\n{self._em_nm_str}\n- {self._unit_str}",
            labelOpts={
                "color": QColor(em_rgb[0], em_rgb[1], em_rgb[2]),
                "position": 0.9,
                "anchors": [(0, 0.9), (0, 0.9)],
            },
        )
        self.pw.addItem(self._line_em)

        # Hardware Properties
        self.ui.lbl_hw_model.setText(self.spec.get_model())
        self.ui.lbl_hw_serial.setText(self.spec.get_serial_number())
        self.ui.lbl_hw_pixels.setText(f"{self.spec.get_spectrum_length()} px")
        self.ui.lbl_hw_wl_range.setText(f"{x_min:.1f} – {x_max:.1f} nm")
        self.ui.lbl_hw_max_intensity.setText(f"{int(self.spec.get_max_intensity())} AU")
        int_min_ms = self.spec.get_minimum_integration_time() / 1000
        int_max_ms = self.spec.get_maximum_integration_time() / 1000
        self.ui.lbl_hw_int_range.setText(f"{int_min_ms:.3f} – {int_max_ms:.0f} ms")
        self.ui.lbl_hw_int_increment.setText(f"{self.spec.get_integration_time_increment()} µs")

        # Acquisition Settings (Global)
        self.ui.lbl_acq_dark_corr.setText("Enabled")
        self.ui.lbl_acq_nonlin_corr.setText("Enabled")

        # Dye / Acquisition Settings per dye
        self.ui.gb_dye.setTitle(f"Acquisition Settings: {self.dye.name}")
        self.ui.lbl_acq_int_time.setText(f"{dye.integration_time_milliseconds} ms")
        self.ui.lbl_dye_boxcar.setText(
            f"{self.dye.boxcar_width} nm → {2 * hw_boxcar + 1} px ({hw_boxcar} each side)"
        )
        lo_ex = max(0, self.pix_ex - hw_boxcar)
        hi_ex = min(len(self.x) - 1, self.pix_ex + hw_boxcar)
        self.ui.lbl_ex_wavelength.setText(
            f"{self.dye.wavelength_excitation} nm → [{self.x[lo_ex]:.1f} – {self.x[hi_ex]:.1f} nm]"
        )
        lo_em = max(0, self.pix_em - hw_boxcar)
        hi_em = min(len(self.x) - 1, self.pix_em + hw_boxcar)
        self.ui.lbl_em_wavelength.setText(
            f"{self.dye.wavelength_emission} nm → [{self.x[lo_em]:.1f} – {self.x[hi_em]:.1f} nm]"
        )

        self._last_plot_time = 0.0

        # Start acquisition worker thread
        self._thread = QThread(self)
        self._worker = SpectrometerWorker(spectrometer, int(dye.integration_time_milliseconds))
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.start)
        self._worker.data_ready.connect(self._on_data_ready)
        self._thread.start()

        self.show()

    def _on_data_ready(self, y: np.ndarray):
        now = time.monotonic()
        if now - self._last_plot_time < 0.033:  # cap at ~30 FPS
            return
        self._last_plot_time = now

        y64 = y.astype(np.float64)
        _y = y64 / cfg.AU_PER_PERCENT_16_BIT if self._use_rel else y64
        self.plot_item.setData(self.x, _y, skipFiniteCheck=True)
        self._line_ex.label.format = f"Excitation\n{self._ex_nm_str}\n{int(y64[self.pix_ex])} {self._unit_str}"
        self._line_ex.label.valueChanged()
        self._line_em.label.format = f"Emission\n{self._em_nm_str}\n{int(y64[self.pix_em])} {self._unit_str}"
        self._line_em.label.valueChanged()

    def _get_rgb_from_wavelength(self, wavelength) -> list[int, int, int]:
        w = wavelength
        if w >= 380 and w < 781:
            if w < 440:
                rgb = [-(w - 440) / (440 - 380), 0.0, 1.0]
            elif w < 490:
                rgb = [0.0, (w - 440) / (490 - 440), 1.0]
            elif w < 510:
                rgb = [0.0, 1.0, -(w - 510) / (510 - 490)]
            elif w < 580:
                rgb = [(w - 510) / (580 - 510), 1.0, 0.0]
            elif w < 645:
                rgb = [1.0, -(w - 645) / (645 - 580), 0.0]
            else:
                rgb = [1.0, 0.0, 0.0]
            # fade at limits
            if w < 420:
                factor = 0.3 + 0.7 * (w - 380) / (420 - 380)
            elif w < 701:
                factor = 1.0
            else:
                factor = 0.3 + 0.7 * (780 - w) / (780 - 701)
        else:
            rgb = [1.0, 1.0, 1.0]
            factor = 1.0
        # make integer
        rgb_int = [0, 0, 0]
        for i, c in enumerate(rgb):
            if c == 0.0:
                continue
            rgb_int[i] = round(255 * (rgb[i] * factor) ** 0.8)
        return rgb_int

    def done(self, r):
        self._worker.stop()
        self._thread.quit()
        self._thread.wait()
        super().done(QDialog.DialogCode.Rejected)
