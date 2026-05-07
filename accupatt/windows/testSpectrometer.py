import os

import numpy as np
from PyQt6 import uic
from PyQt6.QtCore import QObject, QThread, pyqtSignal
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QDialog, QTableWidget, QLabel
try:
    from oceandirect.OceanDirectAPI import OceanDirectAPI, Spectrometer
    _OCEANDIRECT_AVAILABLE = True
except ImportError:
    _OCEANDIRECT_AVAILABLE = False
import pyqtgraph

from accupatt.models.dye import Dye
import accupatt.config as cfg

Ui_Form, baseclass = uic.loadUiType(
    os.path.join(os.getcwd(), "resources", "testSpectrometer.ui")
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
        self.spec.set_boxcar_width(1)
        self.dye = dye

        self.tw: QTableWidget = self.ui.tableWidget
        height = self.tw.horizontalHeader().height()
        for row in range(self.tw.model().rowCount()):
            height += self.tw.rowHeight(row)

        if self.tw.horizontalScrollBar().isVisible():
            height += self.tw.horizontalScrollBar().height()
        self.tw.setMaximumHeight(height + 2)
        self.pw: pyqtgraph.PlotWidget = self.ui.plotWidget
        self.label_model: QLabel = self.ui.label_model
        self.label_serial: QLabel = self.ui.label_serial_number
        self.label_integration_Time: QLabel = self.ui.label_integration_time

        # Cache table item references to avoid per-frame lookups
        self._tw_items = {
            "ex_near": self.tw.item(2, 0),
            "ex_avg":  self.tw.item(5, 0),
            "em_near": self.tw.item(2, 1),
            "em_avg":  self.tw.item(5, 1),
        }
        self._use_rel = cfg.get_spectrometer_display_unit() == cfg.SPECTROMETER_DISPLAY_UNIT_RELATIVE

        # Init plot
        self.x = np.array(self.spec.get_wavelengths(), dtype=np.float32)
        pyqtgraph.setConfigOptions(antialias=True)
        pyqtgraph.setConfigOption("background", "k")
        pyqtgraph.setConfigOption("foreground", "w")
        self.plot_item = self.pw.plotItem.plot(
            name="Measured", pen=pyqtgraph.mkPen("w", width=1.5)
        )
        self.pw.plotItem.setLabel(axis="bottom", text="Wavelength (nm)")
        self.pw.plotItem.setLabel(
            axis="left", text=f"Intensity, {cfg.get_spectrometer_display_unit()}"
        )
        self.pw.plotItem.showGrid(x=True, y=True)
        self.pw.setXRange(self.x[0], self.x[-1], padding=0.0)
        if (
            cfg.get_spectrometer_display_unit()
            == cfg.SPECTROMETER_DISPLAY_UNIT_RELATIVE
        ):
            y_max = 100
        else:
            y_max = 65535
        self.pw.setYRange(0, y_max, padding=0.0)
        # self.pw.plotItem.getViewBox().autoRange()
        # self.pw.plotItem.getViewBox().disableAutoRange()
        self.pw.plotItem.getViewBox().setLimits(
            minXRange=self.x[0],
            maxXRange=self.x[-1],
            minYRange=0,
            maxYRange=y_max,
            xMin=self.x[0],
            xMax=self.x[-1],
            yMin=0,
        )

        # Init cursors
        self.pix_ex = np.abs(self.x - self.dye.wavelength_excitation).argmin()
        self.boxcar_pix_ex = [
            np.abs(
                self.x - (self.dye.wavelength_excitation - (self.dye.boxcar_width / 2))
            ).argmin(),
            np.abs(
                self.x - (self.dye.wavelength_excitation + (self.dye.boxcar_width / 2))
            ).argmin(),
        ]
        self.tw.item(0, 0).setText(str(self.dye.wavelength_excitation))
        self.tw.item(1, 0).setText(f"{self.x[self.pix_ex]:.1f}")
        self.tw.item(3, 0).setText(
            f"[{self.x[self.boxcar_pix_ex[0]]:.1f},\n{self.x[self.boxcar_pix_ex[-1]]:.1f}]"
        )
        self.tw.item(4, 0).setText(
            str(self.boxcar_pix_ex[-1] - self.boxcar_pix_ex[0] + 1)
        )
        ex_rgb = self._get_rgb_from_wavelength(self.dye.wavelength_excitation)
        self.pw.addItem(
            pyqtgraph.InfiniteLine(
                pos=self.x[self.pix_ex],
                pen=pyqtgraph.mkPen(QColor(ex_rgb[0], ex_rgb[1], ex_rgb[2])),
                label="Excitation = {value:.1f}",
                labelOpts={
                    "color": QColor(ex_rgb[0], ex_rgb[1], ex_rgb[2]),
                    "position": 0.9,
                    "anchors": [(1, 0.9), (1, 0.9)],
                },
            )
        )

        self.pix_em = np.abs(self.x - self.dye.wavelength_emission).argmin()
        self.boxcar_pix_em = [
            np.abs(
                self.x - (self.dye.wavelength_emission - (self.dye.boxcar_width / 2))
            ).argmin(),
            np.abs(
                self.x - (self.dye.wavelength_emission + (self.dye.boxcar_width / 2))
            ).argmin(),
        ]
        self.tw.item(0, 1).setText(str(self.dye.wavelength_emission))
        self.tw.item(1, 1).setText(f"{self.x[self.pix_em]:.1f}")
        self.tw.item(3, 1).setText(
            f"[{self.x[self.boxcar_pix_em[0]]:.1f},\n{self.x[self.boxcar_pix_em[-1]]:.1f}]"
        )
        self.tw.item(4, 1).setText(
            str(self.boxcar_pix_em[-1] - self.boxcar_pix_em[0] + 1)
        )
        em_rgb = self._get_rgb_from_wavelength(self.dye.wavelength_emission)

        self.pw.addItem(
            pyqtgraph.InfiniteLine(
                pos=self.x[self.pix_em],
                pen=pyqtgraph.mkPen(QColor(em_rgb[0], em_rgb[1], em_rgb[2])),
                label="Emission = {value:.1f}",
                labelOpts={
                    "color": QColor(em_rgb[0], em_rgb[1], em_rgb[2]),
                    "position": 0.9,
                    "anchors": [(0, 0.9), (0, 0.9)],
                },
            )
        )
        # Call this before show so resizeEvent is proper
        self.tw.resizeRowsToContents()

        # Labels
        self.label_model.setText(f"Spectrometer Model: {self.spec.get_model()}")
        self.label_serial.setText(
            f"Spectrometer Serial Number: {self.spec.get_serial_number()}"
        )
        self.label_integration_Time.setText(
            f"Target Integration Time: {self.dye.integration_time_milliseconds} milliseconds"
        )

        # Start acquisition worker thread
        self._thread = QThread(self)
        self._worker = SpectrometerWorker(spectrometer, int(dye.integration_time_milliseconds))
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.start)
        self._worker.data_ready.connect(self._on_data_ready)
        self._thread.start()

        self.show()

    def _on_data_ready(self, y: np.ndarray):
        _y = y / cfg.AU_PER_PERCENT_16_BIT if self._use_rel else y
        self.plot_item.setData(self.x, _y, skipFiniteCheck=True)
        self._tw_items["ex_near"].setText(str(int(y[self.pix_ex])))
        self._tw_items["ex_avg"].setText(str(int(np.mean(y[self.boxcar_pix_ex[0]:self.boxcar_pix_ex[-1] + 1]))))
        self._tw_items["em_near"].setText(str(int(y[self.pix_em])))
        self._tw_items["em_avg"].setText(str(int(np.mean(y[self.boxcar_pix_em[0]:self.boxcar_pix_em[-1] + 1]))))

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

    def resizeEvent(self, event):
        super(TestSpectrometer, self).resizeEvent(event)
        height = self.tw.horizontalHeader().height()
        for row in range(self.tw.model().rowCount()):
            height += self.tw.rowHeight(row)

        if self.tw.horizontalScrollBar().isVisible():
            height += self.tw.horizontalScrollBar().height()
        self.tw.setMaximumHeight(height + 2)
        width = self.tw.verticalHeader().width()
        for row in range(self.tw.model().columnCount()):
            width += self.tw.columnWidth(row)

        if self.tw.verticalScrollBar().isVisible():
            width += self.tw.verticalScrollBar().width()
        self.tw.setMaximumWidth(width + 2)
