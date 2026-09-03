import os

import accupatt.config as cfg
import numpy as np
import pyqtgraph
import serial
from serial.tools import list_ports
from accupatt.models.dye import Dye
from accupatt.models.passData import Pass
from accupatt.widgets.passinfowidget import PassInfoWidget
from PyQt6 import uic
from PyQt6.QtCore import QTimer, pyqtSlot
from PyQt6.QtWidgets import QMessageBox, QLabel, QPushButton
from oceandirect.OceanDirectAPI import OceanDirectAPI

Ui_Form, baseclass = uic.loadUiType(
    cfg.resource_path("resources", "readString.ui")
)


class StringPass(baseclass):
    def __init__(self, passData: Pass, parent=None):
        super().__init__(parent=parent)
        self.ui = Ui_Form()
        self.ui.setupUi(self)

        # Make ref to seriesData/passData for later updating in on_applied
        self.passData = passData
        # Populate Pass Info Widget fields
        # self.ui.labelPass.setText(passData.name)
        self.setWindowTitle(f"Capture/Edit {passData.name}")
        self.passInfoWidget: PassInfoWidget = self.ui.passInfoWidget
        self.passInfoWidget.fill_from_pass(passData)

        # UI
        self.button_reverse: QPushButton = self.ui.buttonManualReverse
        self.button_reverse.clicked.connect(self.string_drive_manual_reverse)
        self.button_forward: QPushButton = self.ui.buttonManualAdvance
        self.button_forward.clicked.connect(self.string_drive_manual_advance)
        self.button_start: QPushButton = self.ui.buttonStart
        self.button_start.clicked.connect(self.click_start)
        self.button_abort: QPushButton = self.ui.buttonAbort
        self.button_abort.clicked.connect(self.click_abort)
        self.button_clear: QPushButton = self.ui.buttonClear
        self.button_clear.clicked.connect(self.click_clear)
        self.pill_drive: QLabel = self.ui.pillDrive
        self.pill_spec: QLabel = self.ui.pillSpec
        self.pill_dye: QLabel = self.ui.pillDye
        self.pill_resolution: QLabel = self.ui.pillResolution
        self.button_settings: QPushButton = self.ui.buttonStringSettings
        self.button_settings.clicked.connect(self.editStringSettings)

        # Init pill labels
        _PILL_BASE = (
            "border-radius: 8px; padding: 3px 10px; color: black;"
        )
        self._pill_ready_style = f"background-color: #888888; {_PILL_BASE}"
        self._pill_not_ready_style = f"background-color: #FFD700; {_PILL_BASE}"
        self._set_pill(self.pill_drive, "Drive Motors: Not Ready", ready=False)
        self._set_pill(self.pill_spec, "Spectrometer: Not Ready", ready=False)
        self._update_dye_pill()
        self._update_resolution_pill()

        # Setup plot and init data vars
        self.setup_and_clear_plot(showPopup=False)

        # Setup Spectrometer and String Drive
        self.spec = None
        self.spec_connected = False
        self.ser = None
        self.ser_connected = False
        self.setupSpectrometer()
        self.setupStringDrive()

        self.populate_plot()

        # Enable/Disable Start and Abort buttons as applicable
        self.enableButtons()

        self.show()

    def populate_plot(self):
        # Load in pattern data from pass object if available
        if self.passData.string.has_data():
            self.x = np.array(self.passData.string.data["loc"].values, dtype=float)
            self.y = np.array(
                self.passData.string.data[self.passData.name].values, dtype=float
            )
            self.y_ex = np.array(
                self.passData.string.data_ex[self.passData.name].values, dtype=float
            )
            use_rel = (
                cfg.get_spectrometer_display_unit()
                == cfg.SPECTROMETER_DISPLAY_UNIT_RELATIVE
            )
            _y = self.y / cfg.AU_PER_PERCENT_16_BIT if use_rel else self.y
            self.plot_emission.setData(self.x, _y)
            # Disable Edit if data already present to prevent overwrite of origination info
            self.button_settings.setEnabled(False)
        _use_rel = cfg.get_spectrometer_display_unit() == cfg.SPECTROMETER_DISPLAY_UNIT_RELATIVE
        self.plotWidget.plotItem.setLabel(axis="left", text="Intensity (%)" if _use_rel else "Intensity (AU)")
        self.plotWidget.plotItem.getAxis("left").enableAutoSIPrefix(False)

    def setup_and_clear_plot(self, showPopup=True):
        # Optionally prompt to proceed
        if showPopup and self.y.size != 0:
            msg = QMessageBox.question(
                self,
                "Are You Sure?",
                f"Clear Existing String Data for {self.passData.name}?",
            )
            if msg == QMessageBox.StandardButton.No:
                return False
        # Init arrays
        self.x = np.array([])
        self.y = np.array([])
        self.y_ex = np.array([])
        # Configuration options
        pyqtgraph.setConfigOptions(antialias=True)
        pyqtgraph.setConfigOption("background", "k")
        pyqtgraph.setConfigOption("foreground", "w")
        # Get a handle to the plotWidget
        self.plotWidget: pyqtgraph.PlotWidget = self.ui.plotWidget
        # Clear the plot
        self.plotWidget.plotItem.clear()
        # Add plots of excitation and emission
        self.plot_emission = self.plotWidget.plotItem.plot(name="Emission", pen="w")
        self.plot_excitation = self.plotWidget.plotItem.plot(name="Excitation", pen="c")
        # Labels and formatting
        self.plotWidget.plotItem.setLabel(
            axis="bottom", text="Location", units=self.passData.string.data_loc_units
        )
        _use_rel = cfg.get_spectrometer_display_unit() == cfg.SPECTROMETER_DISPLAY_UNIT_RELATIVE
        self.plotWidget.plotItem.setLabel(axis="left", text="Intensity (%)" if _use_rel else "Intensity (AU)")
        self.plotWidget.plotItem.getAxis("left").enableAutoSIPrefix(False)
        self.plotWidget.plotItem.showGrid(x=True, y=True)
        self.plotWidget.setXRange(
            -cfg.get_string_length() / 2, cfg.get_string_length() / 2
        )
        # Ensure Edit is enabled (disabled after has_data)
        self.button_settings.setEnabled(True)
        return True

    def plotFrame(self):
        # Calculate and log location based off elapsed/remaining time
        self.x = np.append(
            self.x,
            self.location_start
            + (
                (self.timer.interval() - self.timer.remainingTime())
                * self.speed_per_milli
            ),
        )
        # Take a full spectrum reading, correct dark pixels and nonlinearity if supported by device & backend
        intensities = np.array(self.spec.get_formatted_spectrum(), dtype=np.float32)
        # record y_val (emission amplitute) and request plot update
        self.y = np.append(
            self.y, intensities[self.pix_em]
        )
        use_rel = (
            cfg.get_spectrometer_display_unit()
            == cfg.SPECTROMETER_DISPLAY_UNIT_RELATIVE
        )
        _y = self.y / cfg.AU_PER_PERCENT_16_BIT if use_rel else self.y
        self.plot_emission.setData(self.x, _y)
        # record y_ex_val (excitation amplitude)
        self.y_ex = np.append(self.y_ex, intensities[self.pix_ex])

    @pyqtSlot()
    def endPlot(self):
        self.timer_trigger.stop()
        self.ser.write(cfg.STRING_DRIVE_FWD_STOP.encode())
        self.enableButtons(start=False, abort=False)
        # Disable Edit to preserve origination params
        self.button_settings.setEnabled(False)

    @pyqtSlot()
    def click_start(self):
        if self.button_start.text() == "Start":
            self.setup_and_clear_plot()
            # Start String Drive (advance)
            self.ser.write(cfg.STRING_DRIVE_FWD_START.encode())
            self.button_start.setText("Mark")
            self.enableButtons(clear=False, reverse=False, advance=False, window=False)
        else:
            # Initialize timers
            self.timer = QTimer(self)
            self.timer_trigger = QTimer(self)
            # Set local vars from config
            if cfg.get_string_collect_from() == cfg.STRING_COLLECT_FROM_RTL:
                self.location_start = +cfg.get_string_length() / 2
                self.speed_per_milli = -cfg.get_string_speed() / 1000.0
            else:
                self.location_start = -cfg.get_string_length() / 2
                self.speed_per_milli = cfg.get_string_speed() / 1000.0
            # Get a handle on pixels for chosen wavelengths
            wavelengths = np.array(self.spec.get_wavelengths(), np.float32)
            nm_per_pixel = float(wavelengths[-1] - wavelengths[0]) / (len(wavelengths) - 1)
            hw_boxcar = max(0, round(self.passData.string.dye.boxcar_width / 2 / nm_per_pixel))
            self.spec.set_boxcar_width(hw_boxcar)
            self.pix_ex, _wav = self.spec.get_index_at_wavelength(self.passData.string.dye.wavelength_excitation)
            self.pix_em = np.abs(wavelengths - self.passData.string.dye.wavelength_emission).argmin()
            # Set the intervals and timeouts
            self.timer.setSingleShot(True)
            self.timer.setInterval(
                int((cfg.get_string_length() / cfg.get_string_speed()) * 1000)
            )
            self.timer.timeout.connect(self.endPlot)
            self.timer_trigger.setInterval(
                int(self.passData.string.dye.integration_time_milliseconds)
            )
            self.timer_trigger.timeout.connect(self.plotFrame)
            # Start timers
            self.timer.start()
            self.timer_trigger.start()
            self.enableButtons(
                start=False, clear=False, reverse=False, advance=False, window=False
            )

    @pyqtSlot()
    def click_abort(self):
        if not self.button_start.isEnabled():
            self.timer.stop()
            self.timer_trigger.stop()
        self.ser.write(cfg.STRING_DRIVE_FWD_STOP.encode())
        self.setup_and_clear_plot(showPopup=False)
        self.button_start.setText("Start")
        self.enableButtons(clear=False, abort=False)

    @pyqtSlot()
    def click_clear(self):
        if self.setup_and_clear_plot(showPopup=True):
            self.button_start.setText("Start")
            self.enableButtons(clear=False, abort=False)

    def reject(self):
        if self.y.size != 0:
            msg = QMessageBox.question(
                self, "Are You Sure?", f"Abandon data/changes for {self.passData.name}?"
            )
            if msg == QMessageBox.StandardButton.No:
                return False
        # Ensure connections are severed
        if self.ser and self.ser.is_open:
            self.ser.close()
        if self.spec:
            self.spec.close_device()
        # Nofiy requestor and close
        super().reject()

    def accept(self):
        p = self.passData
        # Validate fields will set values to the pass object if valid
        # If any passInfo fields invalid, show user and return to current window
        if len(excepts := self.passInfoWidget.validate_fields()) > 0:
            QMessageBox.warning(self, "Invalid Data", "\n".join(excepts))
            return
        # Pattern
        if len(self.x) > 0:
            p.string.setData(self.x, self.y, self.y_ex)
        # If all checks out, sever serial and spectrometer connections
        if self.ser:
            self.ser.close()
        if self.spec:
            self.spec.close_device()
        # If all checks out, notify requestor and close
        super().accept()

    def enableButtons(
        self,
        start=True,
        abort=True,
        clear=True,
        reverse=True,
        advance=True,
        window=True,
    ):
        if not self.ser_connected:
            reverse = False
            advance = False
        if not self.spec_connected or not self.ser_connected:
            start = False
            abort = False
        if self.y.size != 0:
            start = False
            abort = False
        self.button_start.setEnabled(start)
        self.button_abort.setEnabled(abort)
        self.button_clear.setEnabled(clear)
        self.button_reverse.setEnabled(reverse)
        self.button_forward.setEnabled(advance)
        self.button_settings.setEnabled(window)
        self.ui.buttonBox.setEnabled(window)

    def _set_pill(self, label: QLabel, text: str, ready: bool):
        label.setText(text)
        label.setStyleSheet(
            self._pill_ready_style if ready else self._pill_not_ready_style
        )

    def _update_dye_pill(self):
        dye = self.passData.string.dye
        self.pill_dye.setText(f"Dye: {dye.name} | {dye.wavelength_excitation}{'\u2192'}{dye.wavelength_emission} nm")
        self.pill_dye.setStyleSheet(self._pill_ready_style)

    def _update_resolution_pill(self):
        dye = self.passData.string.dye
        speed = cfg.get_string_speed()
        resolution = dye.integration_time_milliseconds * speed / 1000
        units = self.passData.string.data_loc_units
        self.pill_resolution.setText(f"Spatial Resolution: ~{resolution:.2f} {units}")
        self.pill_resolution.setStyleSheet(self._pill_ready_style)

    """
    String Drive Hook-Ups
    """

    @pyqtSlot()
    def editStringSettings(self):
        from accupatt.windows.settings import Settings
        if self.ser and self.ser.is_open:
            self.ser.close()
            self.ser = None
        self.ser_connected = False
        if self.spec:
            self.spec.close_device()
            self.spec = None
        self.spec_connected = False
        e = Settings(parent=self)
        e.ui.tabWidget.setCurrentWidget(e.ui.tab_string)
        e.settings_changed.connect(self._on_settings_applied)
        e.exec()

    def _on_settings_applied(self):
        units = cfg.get_unit_string_data_location()
        self.passData.string.data_loc_units = units
        self.plotWidget.plotItem.setLabel(axis="bottom", text="Location", units=units)
        self.passData.string.dye = Dye.fromConfig(cfg.get_defined_dye())
        self._update_dye_pill()
        self._update_resolution_pill()
        self.setupStringDrive()
        self.setupSpectrometer()
        self.populate_plot()

    def setupStringDrive(self):
        # Get a handle to the serial object, else return "Disconnected" status label
        if self.ser is None:
            try:
                ftdi_ports = [
                    p for p in list_ports.comports() if "FTDI" in (p.manufacturer or "")
                ]
                if not ftdi_ports:
                    raise Exception("No FTDI device found")
                self.ser = serial.Serial(ftdi_ports[0].device, baudrate=9600, timeout=1)
            except:
                self._set_pill(self.pill_drive, "Drive Motors: Not Ready", ready=False)
                self.ser_connected = False
                return
        units = self.passData.string.data_loc_units
        length = cfg.get_string_length()
        speed = cfg.get_string_speed()
        self._set_pill(
            self.pill_drive,
            f"Drive Motors: Ready | {length} {units} @ {speed} {units}/s",
            ready=True,
        )
        self.ser_connected = True
        # Enable/Disable manual drive buttons
        self.enableButtons()

    @pyqtSlot()
    def string_drive_manual_reverse(self):
        if not self.button_reverse.isChecked():
            self.ser.write(cfg.STRING_DRIVE_REV_STOP.encode())
            self.button_reverse.setText("<- Reverse")
            self.enableButtons()
        else:
            self.ser.write(cfg.STRING_DRIVE_REV_START.encode())
            self.button_reverse.setText("-- STOP --")
            self.enableButtons(
                start=False, abort=False, clear=False, advance=False, window=False
            )

    @pyqtSlot()
    def string_drive_manual_advance(self):
        if not self.button_forward.isChecked():
            self.ser.write(cfg.STRING_DRIVE_FWD_STOP.encode())
            self.button_forward.setText("Forward ->")
            self.enableButtons()
        else:
            self.ser.write(cfg.STRING_DRIVE_FWD_START.encode())
            self.button_forward.setText("-- STOP --")
            self.enableButtons(
                start=False, abort=False, clear=False, reverse=False, window=False
            )

    """
    Spectrometer Hook-Ups
    """

    def setupSpectrometer(self):
        # Get a handle to the spec object, else return "Disconnected" status
        if self.spec is None:
            try:
                od = OceanDirectAPI()
                od.find_usb_devices()
                device_ids = od.get_device_ids()
                if len(device_ids) > 0:
                    self.spec = od.open_device(device_ids[0])
                else:
                    raise Exception("No spectrometer found")
            except:
                self._set_pill(self.pill_spec, "Spectrometer: Not Ready", ready=False)
                self.spec_connected = False
                return
        # Inform spectrometer of new int time
        try:
            self.spec.set_integration_time(
                self.passData.string.dye.integration_time_milliseconds * 1000
            )
        except:
            print("Unable to set Spectrometer Integration Time")
            return
        int_ms = self.passData.string.dye.integration_time_milliseconds
        self._set_pill(
            self.pill_spec,
            f"Spectrometer: Ready | {int_ms} ms",
            ready=True,
        )
        self.spec_connected = True
        self.enableButtons()

