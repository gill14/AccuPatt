import os

import accupatt.config as cfg
import numpy as np
import pyqtgraph
import serial
from accupatt.models.passData import Pass
from accupatt.widgets.passinfowidget import PassInfoWidget
from accupatt.windows.editSpectrometer import EditSpectrometer
from accupatt.windows.editStringDrive import EditStringDrive
from PyQt6 import uic
from PyQt6.QtCore import QTimer, pyqtSlot
from PyQt6.QtWidgets import QMessageBox
from seabreeze.spectrometers import Spectrometer

Ui_Form, baseclass = uic.loadUiType(
    os.path.join(os.getcwd(), "resources", "readString.ui")
)


class ReadString(baseclass):
    def __init__(self, passData: Pass, parent=None):
        super().__init__(parent=parent)
        self.ui = Ui_Form()
        self.ui.setupUi(self)

        # Make ref to seriesData/passData for later updating in on_applied
        self.passData = passData
        # Populate Pass Info Widget fields
        self.ui.labelPass.setText(passData.name)
        self.passInfoWidget: PassInfoWidget = self.ui.passInfoWidget
        self.passInfoWidget.fill_from_pass(passData)

        # Use values from Pass Object
        self.wav_ex = self.passData.string.wav_ex
        self.wav_em = self.passData.string.wav_em
        self.integration_time_ms = self.passData.string.integration_time_ms
        self.string_length_units = self.passData.string.data_loc_units

        # Load other values from persistent config
        self.load_defaults()

        # Setup Spectrometer and String Drive
        self.spec = None
        self.spec_connected = False
        self.ser = None
        self.ser_connected = False
        self.setupSpectrometer()
        self.setupStringDrive()

        # Enable/Disable Start and Abort buttons as applicable
        self.enableButtons()

        # Setup signal slots
        self.ui.buttonManualReverse.clicked.connect(self.string_drive_manual_reverse)
        self.ui.buttonManualAdvance.clicked.connect(self.string_drive_manual_advance)
        self.ui.buttonEditSpectrometer.clicked.connect(self.editSpectrometer)
        self.ui.buttonEditStringDrive.clicked.connect(self.editStringDrive)
        self.ui.buttonStart.clicked.connect(self.click_start)
        self.ui.buttonAbort.clicked.connect(self.click_abort)
        self.ui.buttonClear.clicked.connect(self.click_clear)

        # Setup plot
        self.setup_and_clear_plot(showPopup=False)

        # Load in pattern data from pass object if available
        if passData.has_string_data():
            self.load_data_from_pass()

        self.show()

    def load_defaults(self):
        self.string_drive_port = cfg.get_string_drive_port()
        self.string_length = cfg.get_string_length()
        self.string_speed = cfg.get_string_speed()
        # Calculate from all above
        self.len_per_frame = self.integration_time_ms * self.string_speed / 1000

    def load_data_from_pass(self):
        self.x = np.array(self.passData.string.data["loc"].values, dtype=float)
        self.y = np.array(
            self.passData.string.data[self.passData.name].values, dtype=float
        )
        self.y_ex = np.array(
            self.passData.string.data_ex[self.passData.name].values, dtype=float
        )
        self.plot_emission.setData(self.x, self.y)
        self.plot_excitation.setData(self.x, self.y)

    def setup_and_clear_plot(self, showPopup=True):
        # Optionally prompt to proceed
        if showPopup and not self.y == []:
            msg = QMessageBox.question(
                self,
                "Are You Sure?",
                f"Clear Existing String Data for {self.passData.name}?",
            )
            if msg == QMessageBox.StandardButton.No:
                return False
        # Init arrays
        self.x = []
        self.y = []
        self.y_ex = []
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
            axis="bottom", text="Location", units=self.string_length_units
        )
        self.plotWidget.plotItem.setLabel(axis="left", text="Relative Dye Intensity")
        self.plotWidget.plotItem.showGrid(x=True, y=True)
        self.plotWidget.setXRange(-self.string_length / 2, self.string_length / 2)
        return True

    def plotFrame(self):
        # get Location
        ellapsedTimeSec = (self.timer.interval() - self.timer.remainingTime()) / 1000
        location = -self.string_length / 2 + (ellapsedTimeSec * self.string_speed)
        # Capture and record one frame
        # record x_val (location)
        self.x = np.append(self.x, location)
        # take a full spectrum reading
        intensities = self.spec.intensities(
            correct_dark_counts=True, correct_nonlinearity=True
        )
        # record y_val (emission amplitute) and request plot update
        self.y = np.append(self.y, intensities[self.pix_em])
        self.plot_emission.setData(self.x, self.y)
        # record y_ex_val (excitation amplitude) and request plot update
        self.y_ex = np.append(self.y_ex, intensities[self.pix_ex])
        # self.plot_excitation.setData(self.x, self.y_ex)

    @pyqtSlot()
    def endPlot(self):
        self.timer_trigger.stop()
        self.ser.write(cfg.STRING_DRIVE_FWD_STOP.encode())
        self.enableButtons(start=False, abort=False)

    @pyqtSlot()
    def click_start(self):
        if self.ui.buttonStart.text() == "Start":
            self.setup_and_clear_plot()
            # Start String Drive (advance)
            self.ser.write(cfg.STRING_DRIVE_FWD_START.encode())
            self.ui.buttonStart.setText("Mark")
            self.enableButtons(clear=False, reverse=False, advance=False, window=False)
        else:
            # Initialize timers
            self.timer = QTimer(self)
            self.timer_trigger = QTimer(self)
            # Set the intervals and timeouts
            self.timer.setSingleShot(True)
            self.timer.setInterval(int((self.string_length / self.string_speed) * 1000))
            self.timer.timeout.connect(self.endPlot)
            self.timer_trigger.setInterval(int(self.integration_time_ms))
            self.timer_trigger.timeout.connect(self.plotFrame)
            # Start timers
            self.timer.start()
            self.timer_trigger.start()
            self.enableButtons(
                start=False, clear=False, reverse=False, advance=False, window=False
            )

    @pyqtSlot()
    def click_abort(self):
        if not self.ui.buttonStart.isEnabled():
            self.timer.stop()
            self.timer_trigger.stop()
        self.ser.write(cfg.STRING_DRIVE_FWD_STOP.encode())
        self.setup_and_clear_plot(showPopup=False)
        self.ui.buttonStart.setText("Start")
        self.enableButtons(clear=False, abort=False)

    @pyqtSlot()
    def click_clear(self):
        if self.setup_and_clear_plot(showPopup=True):
            self.ui.buttonStart.setText("Start")
            self.enableButtons(clear=False, abort=False)

    def reject(self):
        if not self.y == []:
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
        if len(excepts := self.passInfoWidget.validate_fields(p)) > 0:
            QMessageBox.warning(self, "Invalid Data", "\n".join(excepts))
            return
        # Pattern
        p.string.wav_ex = self.wav_ex
        p.string.wav_em = self.wav_em
        p.string.integration_time_ms = self.integration_time_ms
        p.string.data_loc_units = self.string_length_units
        if len(self.x) > 0:
            p.string.setData(self.x, self.y, self.y_ex)
        # If all checks out, sever serial and spectrometer connections
        if self.ser:
            self.ser.close()
        if self.spec:
            self.spec.close()
        # If all checks out, notify requestor and close
        super().accept()

    def strip_num(self, x) -> str:
        if x is None:
            return ""
        if type(x) is str:
            if x == "":
                x = 0
        if float(x).is_integer():
            return str(int(float(x)))
        else:
            return f"{round(float(x), 2):.2f}"

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
        self.ui.buttonStart.setEnabled(start)
        self.ui.buttonAbort.setEnabled(abort)
        self.ui.buttonClear.setEnabled(clear)
        self.ui.buttonManualReverse.setEnabled(reverse)
        self.ui.buttonManualAdvance.setEnabled(advance)
        self.ui.buttonEditStringDrive.setEnabled(window)
        self.ui.buttonEditSpectrometer.setEnabled(window)
        self.ui.buttonBox.setEnabled(window)

    """
    String Drive Hook-Ups
    """
    # Open String Drive Editor
    @pyqtSlot()
    def editStringDrive(self):
        e = EditStringDrive(
            ser=self.ser, string_length_units=self.string_length_units, parent=self
        )
        e.string_length_units_changed.connect(self.string_length_units_changed)
        e.accepted.connect(self.reSetupStringDrive)
        e.exec()

    def setupStringDrive(self):
        # Get a handle to the serial object, else return "Disconnected" status label
        try:
            self.ser = serial.Serial(self.string_drive_port, baudrate=9600, timeout=1)
            self.ser_connected = True
        except:
            self.ui.labelStringDrive.setText("String Drive: DISCONNECTED")
            self.ser_connected = False
            return
        # Setup String Drive labels
        self.ui.labelStringDrive.setText(f"String Drive Port: {self.ser.name}")
        self.ui.labelStringLength.setText(
            f"String Length: {self.strip_num(self.string_length)} {self.string_length_units}"
        )
        self.ui.labelStringVelocity.setText(
            f"String Velocity: {self.strip_num(self.string_speed)} {self.string_length_units}/sec"
        )
        # Enale/Disable manual drive buttons
        self.enableButtons()

    @pyqtSlot(str)
    def string_length_units_changed(self, units: str):
        self.string_length_units = units
        self.plotWidget.plotItem.setLabel(axis="bottom", text="Location", units=units)
        pass

    @pyqtSlot()
    def reSetupStringDrive(self):
        self.load_defaults()
        self.setupStringDrive()

    @pyqtSlot()
    def string_drive_manual_reverse(self):
        if not self.ui.buttonManualReverse.isChecked():
            self.ser.write(cfg.STRING_DRIVE_REV_STOP.encode())
            self.enableButtons()
        else:
            self.ser.write(cfg.STRING_DRIVE_REV_START.encode())
            self.enableButtons(
                start=False, abort=False, clear=False, advance=False, window=False
            )

    @pyqtSlot()
    def string_drive_manual_advance(self):
        if not self.ui.buttonManualAdvance.isChecked():
            self.ser.write(cfg.STRING_DRIVE_FWD_STOP.encode())
            self.enableButtons()
        else:
            self.ser.write(cfg.STRING_DRIVE_FWD_START.encode())
            self.enableButtons(
                start=False, abort=False, clear=False, reverse=False, window=False
            )

    """
    Spectrometer Hook-Ups
    """
    # Open Spectrometer Editor
    @pyqtSlot()
    def editSpectrometer(self):
        e = EditSpectrometer(
            self.spec, self.wav_ex, self.wav_em, self.integration_time_ms, parent=self
        )
        e.accepted.connect(self.reSetupSpectrometer)
        e.exec()

    def setupSpectrometer(self):
        # Get a handle to the spec object, else return "Disconnected" status
        if self.spec == None:
            try:
                self.spec = Spectrometer.from_first_available()
                self.spec_connected = True
            except:
                self.ui.labelSpec.setText("Spectrometer: DISCONNECTED")
                self.spec_connected = False
                return
        # Inform spectrometer of new int time
        self.spec.integration_time_micros(self.integration_time_ms * 1000)
        # Get a handle on pixels for chosen wavelengths
        wavelengths = self.spec.wavelengths()
        self.pix_ex = np.abs(wavelengths - self.wav_ex).argmin()
        self.pix_em = np.abs(wavelengths - self.wav_em).argmin()
        # Populate Spectrometer labels
        self.ui.labelSpec.setText(f"Spectrometer: {self.spec.model}")
        self.ui.labelExcitation.setText(f"Excitation: {self.wav_ex} nm")
        self.ui.labelEmission.setText(f"Emission: {self.wav_em} nm")
        self.ui.labelIntegrationTime.setText(
            f"Integration Time: {self.integration_time_ms} ms"
        )
        self.enableButtons()

    @pyqtSlot()
    def reSetupSpectrometer(self):
        self.load_defaults()  # To re-calc len_per_frame w/ new int time
        self.setupSpectrometer()

    @pyqtSlot(int)
    def wav_ex_changed(self, wav: int):
        self.wav_ex = wav

    @pyqtSlot(int)
    def wav_em_changed(self, wav: int):
        self.wav_em = wav

    @pyqtSlot(int)
    def integration_time_ms_changed(self, time_ms: int):
        self.integration_time_ms = time_ms
