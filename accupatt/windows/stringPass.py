import os

import accupatt.config as cfg
import numpy as np
import pyqtgraph
import serial
from accupatt.models.dye import Dye
from accupatt.models.passData import Pass
from accupatt.widgets.passinfowidget import PassInfoWidget
from accupatt.windows.editSpectrometer import EditSpectrometer
from accupatt.windows.editStringDrive import EditStringDrive
from PyQt6 import uic
from PyQt6.QtCore import QTimer, pyqtSlot, Qt
from PyQt6.QtWidgets import QMessageBox, QCheckBox, QLabel, QPushButton
from seabreeze.spectrometers import Spectrometer

Ui_Form, baseclass = uic.loadUiType(
    os.path.join(os.getcwd(), "resources", "readString.ui")
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
        self.label_spec: QLabel = self.ui.labelSpec
        self.cb_spec: QCheckBox = self.ui.checkBoxSpectrometer
        self.cb_spec.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.button_spec: QPushButton = self.ui.buttonEditSpectrometer
        self.button_spec.clicked.connect(self.editSpectrometer)
        self.label_string_drive: QLabel = self.ui.labelStringDrive
        self.cb_string_drive: QCheckBox = self.ui.checkBoxStringDrive
        self.cb_string_drive.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents
        )
        self.button_string_drive: QPushButton = self.ui.buttonEditStringDrive
        self.button_string_drive.clicked.connect(self.editStringDrive)

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
            self.button_spec.setEnabled(False)
            self.button_string_drive.setEnabled(False)
        y_label = f"Intensity, {cfg.get_spectrometer_display_unit()}"
        self.plotWidget.plotItem.setLabel(axis="left", text=y_label)

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
        # self.plotWidget.plotItem.setLabel(axis="left", text="Relative Dye Intensity")
        self.plotWidget.plotItem.showGrid(x=True, y=True)
        self.plotWidget.setXRange(
            -cfg.get_string_length() / 2, cfg.get_string_length() / 2
        )
        # Ensure Edit is enabled (disabled after has_data)
        self.button_spec.setEnabled(True)
        self.button_string_drive.setEnabled(True)
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
        # Take a full spectrum reading
        intensities = self.spec.intensities(
            correct_dark_counts=False, correct_nonlinearity=False
        )
        # record y_val (emission amplitute) and request plot update
        self.y = np.append(
            self.y, np.average(intensities[self.pix_em[0] : self.pix_em[1] + 1])
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
        # Disable Edit spec to preserve origination params
        self.button_spec.setEnabled(False)
        self.button_string_drive.setEnabled(False)

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
            self.location_start = -cfg.get_string_length() / 2
            self.speed_per_milli = cfg.get_string_speed() / 1000.0
            # Get a handle on pixels for chosen wavelengths
            wavelengths = self.spec.wavelengths()
            self.pix_ex = np.abs(
                wavelengths - self.passData.string.dye.wavelength_excitation
            ).argmin()
            bw = self.passData.string.dye.boxcar_width
            self.pix_em = [
                np.abs(
                    wavelengths
                    - (self.passData.string.dye.wavelength_emission - (bw / 2))
                ).argmin(),
                np.abs(
                    wavelengths
                    - (self.passData.string.dye.wavelength_emission + (bw / 2))
                ).argmin(),
            ]
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
            self.spec.close()
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
            self.spec.close()
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
        self.button_string_drive.setEnabled(window)
        self.button_spec.setEnabled(window)
        self.ui.buttonBox.setEnabled(window)

    """
    String Drive Hook-Ups
    """

    # Open String Drive Editor
    @pyqtSlot()
    def editStringDrive(self):
        e = EditStringDrive(
            ser=self.ser,
            string_length_units=self.passData.string.data_loc_units,
            parent=self,
        )
        e.string_drive_connected.connect(self.string_drive_connected_external)
        e.string_length_units_changed.connect(self.string_length_units_changed)
        e.accepted.connect(self.setupStringDrive)
        e.exec()

    def setupStringDrive(self):
        # Get a handle to the serial object, else return "Disconnected" status label
        if self.ser is None:
            try:
                self.ser = serial.Serial(
                    cfg.get_string_drive_port(), baudrate=9600, timeout=1
                )
            except:
                self.cb_string_drive.setText("Offline")
                self.cb_string_drive.setEnabled(False)
                self.cb_string_drive.setChecked(False)
                self.ser_connected = False
                return
        self.cb_string_drive.setText("Ready")
        self.cb_string_drive.setEnabled(True)
        self.cb_string_drive.setChecked(True)
        self.ser_connected = True
        self.label_string_drive.setToolTip(
            f"Flightline Length: {cfg.get_string_length()} {self.passData.string.data_loc_units}\nSpeed: {cfg.get_string_speed()} {self.passData.string.data_loc_units}/s"
        )
        # Enale/Disable manual drive buttons
        self.enableButtons()

    @pyqtSlot(serial.Serial)
    def string_drive_connected_external(self, ser: serial.Serial):
        self.ser = ser

    @pyqtSlot(str)
    def string_length_units_changed(self, units: str):
        self.passData.string.data_loc_units = units
        self.plotWidget.plotItem.setLabel(axis="bottom", text="Location", units=units)

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

    # Open Spectrometer Editor
    @pyqtSlot()
    def editSpectrometer(self):
        e = EditSpectrometer(self.spec, self.passData.string.dye, parent=self)
        e.dye_changed[str].connect(self.dye_changed)
        e.spectrometer_connected[Spectrometer].connect(
            self.spectrometer_connected_externally
        )
        e.spectrometer_display_unit_changed.connect(
            self.spectrometer_display_unit_changed
        )
        e.accepted.connect(self.setupSpectrometer)
        e.exec()

    def setupSpectrometer(self):
        # Get a handle to the spec object, else return "Disconnected" status

        if self.spec is None:
            try:
                self.spec = Spectrometer.from_first_available()
            except:
                self.cb_spec.setText("Offline")
                self.cb_spec.setEnabled(False)
                self.cb_spec.setCheckState(Qt.CheckState.Unchecked)
                self.spec_connected = False
                return
        # Inform spectrometer of new int time
        try:
            self.spec.integration_time_micros(
                self.passData.string.dye.integration_time_milliseconds * 1000
            )
        except:
            print("Unable to set Spectrometer Integration Time")
            return
        self.cb_spec.setText("Ready")
        self.cb_spec.setEnabled(True)
        self.cb_spec.setCheckState(Qt.CheckState.Checked)
        self.spec_connected = True
        self.label_spec.setToolTip(
            f"Dye: {self.passData.string.dye.name}\nExcitation: {self.passData.string.dye.wavelength_excitation} nm\nEmission: {self.passData.string.dye.wavelength_emission} nm"
        )
        self.enableButtons()

    @pyqtSlot(Spectrometer)
    def spectrometer_connected_externally(self, spec: Spectrometer):
        self.spec = spec

    @pyqtSlot(str)
    def dye_changed(self, dye_name: str):
        self.passData.string.dye = Dye.fromConfig(dye_name)
        # self.setupSpectrometer()

    @pyqtSlot()
    def spectrometer_display_unit_changed(self):
        self.populate_plot()
