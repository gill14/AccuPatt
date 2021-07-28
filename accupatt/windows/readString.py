import numpy as np
import sys, os

from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import QSettings, QTimer, pyqtSignal
from PyQt5 import uic

from seabreeze.spectrometers import Spectrometer
import serial
import pyqtgraph

#from accupatt.helpers.stringPlotter import StringPlotter
#from accupatt.widgets.pyqtplotwidget import PyQtPlotWidget
from accupatt.models.passData import Pass

from accupatt.windows.editStringDrive import EditStringDrive
from accupatt.windows.editSpectrometer import EditSpectrometer

Ui_Form, baseclass = uic.loadUiType(os.path.join(os.getcwd(), 'accupatt', 'windows', 'ui', 'readString.ui'))

class ReadString(baseclass):
    """ A Container for communicating with the Spectrometer and String Drive"""

    applied = pyqtSignal(Pass)

    units_gs = {'mph','kph'}
    units_sh = {'ft','m'}
    units_ws = {'mph','kph'}
    units_t = {'°F','°C'}

    forward_start = "AD+\r"
    forward_stop = "AD\r"
    reverse_start = "BD-\r"
    reverse_stop = "BD\r"

    def __init__(self, passData):
        super().__init__()
        # Your code will go here
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        #Import Settings
        self.settings = QSettings('BG Application Consulting','AccuPatt')
        #Make ref to seriesData/passData for later updating in on_applied
        self.passData = passData
        #Pass Info fields
        self.ui.labelPass.setText(passData.name)
        self.ui.lineEditGS.setText(str(passData.ground_speed))
        self.ui.comboBoxUnitsGS.addItems(self.units_gs)
        self.ui.comboBoxUnitsGS.setCurrentText(passData.ground_speed_units)
        self.ui.lineEditSH.setText(str(passData.spray_height))
        self.ui.comboBoxUnitsSH.addItems(self.units_sh)
        self.ui.comboBoxUnitsSH.setCurrentText(passData.spray_height_units)
        self.ui.lineEditPH.setText(str(passData.pass_heading))
        self.ui.lineEditWD.setText(str(passData.wind_direction))
        self.ui.lineEditWS.setText(str(passData.wind_speed))
        self.ui.comboBoxUnitsWS.addItems(self.units_ws)
        self.ui.comboBoxUnitsWS.setCurrentText(passData.wind_speed_units)
        self.ui.lineEditT.setText(str(passData.temperature))
        self.ui.comboBoxUnitsT.addItems(self.units_t)
        self.ui.comboBoxUnitsT.setCurrentText(passData.temperature_units)
        self.ui.lineEditH.setText(str(passData.humidity))

        self.spec = None
        self.spec_connected = False
        self.ser_connected = False

        #Setup Spectrometer
        self.setupSpectrometer()

        #Setup String Drive serial port
        self.setupStringDrive()

        #Setup signal slots
        self.ui.buttonManualReverse.clicked.connect(self.reverse)
        self.ui.buttonManualForward.clicked.connect(self.forward)
        self.ui.buttonEditSpectrometer.clicked.connect(self.editSpectrometer)
        self.ui.buttonEditStringDrive.clicked.connect(self.editStringDrive)
        self.ui.buttonStart.clicked.connect(self.startAnimation)
        self.ui.buttonClear.clicked.connect(self.clear)

        #Setup plot
        self.traces = dict()
        pyqtgraph.setConfigOptions(antialias=True)
        pyqtgraph.setConfigOption('background', 'k')
        pyqtgraph.setConfigOption('foreground', 'w')
        self.w = self.ui.plotWidget
        self.w.setWindowTitle(f'{passData.name} Raw Data')
        self.p = self.w.addPlot(labels =  {'left':'Intensity', 'bottom':'Location'})
        self.p.showGrid(x=True, y=True)

        self.x = []
        self.y = []
        self.y_ex = []

        if not passData.data.empty:
            self.x = np.array(passData.data['loc'].values, dtype=float)
            self.y = np.array(passData.data[passData.name].values, dtype=float)
            self.y_ex = np.array(passData.data_ex[passData.name].values, dtype=float)
            self.set_plotdata(name='emission', data_x=self.x, data_y=self.y)
            #self.set_plotdata(name='excitation', data_x=self.x, data_y=self.y_ex)
            self.set_plotdata(name='emission', data_x=self.x, data_y=self.y)
            #self.set_plotdata(name='excitation', data_x=self.x, data_y=self.y_ex)

        #Utilize built-in signals
        self.ui.buttonBox.accepted.connect(self.on_applied)
        self.ui.buttonBox.rejected.connect(self.reject)
        # Your code ends here
        self.show()
        self.raise_()
        self.activateWindow()

    def setupSpectrometer(self):
        if self.spec == None:
            try:
                self.spec = Spectrometer.from_first_available()
                self.spec_connected = True
            except:
                self.ui.labelSpec.setText('Spectrometer: DISCONNECTED')
                self.spec_connected = False
                return
        #Inform spectrometer of new int time
        self.spec.integration_time_micros(self.settings.value(
            'integration_time_ms', defaultValue=100, type=int) * 1000)

        #Populate Spectrometer labels
        self.ui.labelSpec.setText(f"Spectrometer: {self.spec.model}")
        self.ui.labelExcitation.setText(
            f"Excitation: {self.settings.value('target_excitation_wavelength', defaultValue=525, type=int)} nm")
        self.ui.labelEmission.setText(
            f"Emission: {self.settings.value('target_emission_wavelength', defaultValue=575, type=int)} nm")
        self.ui.labelIntegrationTime.setText(
            f"Integration Time: {self.settings.value('integration_time_ms', defaultValue=100, type=int)} ms")
        self.checkReady()


    def editSpectrometer(self):
        #Create popup
        e = EditSpectrometer(self.spec)
        #Connect Slot to retrieve Vals back from popup
        e.applied.connect(self.setupSpectrometer)
        #Start Loop
        e.exec_()

    def setupStringDrive(self):
        try:
            self.ser = serial.Serial(self.settings.value('serial_port_device', defaultValue='', type=str),
                baudrate=9600, timeout=1)
            self.ser_connected = True
        except:
            self.ui.labelStringDrive.setText('String Drive: DISCONNECTED')
            self.ser_connected = False
            return
        #Setup String Drive labels
        self.ui.labelStringDrive.setText(f'String Drive Port: {self.ser.name}')
        print(self.ser.name)
        self.ui.labelStringLength.setText("String Length: "
            f"{self.strip_num(self.settings.value('flightline_length', defaultValue=150, type=float))} "
            f"{self.settings.value('flightline_length_units', defaultValue='ft', type=str)}")
        self.ui.labelStringVelocity.setText(f"String Velocity: "
            f"{self.strip_num(self.settings.value('advance_speed', defaultValue=1.70, type=float))} "
            f"{self.settings.value('flightline_length_units', defaultValue = 'ft', type=str)}/sec")
        #Enale/Disable manual drive buttons
        self.ui.buttonManualReverse.setEnabled(self.ser_connected)
        self.ui.buttonManualForward.setEnabled(self.ser_connected)
        self.checkReady()

    def editStringDrive(self):
        #Create popup
        e = EditStringDrive()
        #Connect Slot to retrieve Vals back from popup
        e.applied.connect(self.setupStringDrive)
        #Start Loop
        e.exec_()

    def checkReady(self):
        #Only enable buttons if ready
        self.ready = (self.spec_connected and self.ser_connected)

        self.ui.buttonStart.setEnabled(self.ready)
        self.ui.buttonAbort.setEnabled(self.ready)

    def set_plotdata(self, name, data_x, data_y):
        if name in self.traces:
            self.traces[name].setData(data_x, data_y)
        else:
            if name == 'emission':
                self.traces[name] = self.p.plot(name='Emission',pen='w')
            if name == 'excitation':
                self.traces[name] = self.p.plot(name='Excitation',pen='c')
                pass

    def plotFrame(self):
        #get Location
        if len(self.x) == 0:
            location = -self.fl/2
        else:
            location = self.x[len(self.x)-1] + self.len_per_frame
        if location <= self.fl/2:
            #Capture and record one frame
            #record x_val (location)
            self.x = np.append(self.x, location)
            #take a full spectrum reading
            intensities = self.spec.intensities(correct_dark_counts=True,
                correct_nonlinearity=True)
            #record y_val (emission amplitute) and request plot update
            self.y = np.append(self.y, intensities[self.emissionPix])
            self.set_plotdata(name='emission', data_x=self.x, data_y=self.y)
            #record y_ex_val (excitation amplitude) and request plot update
            self.y_ex = np.append(self.y_ex, intensities[self.excitationPix])
            #self.set_plotdata(name='excitation', data_x=self.x, data_y=self.y_ex)
        else:
            #After recording entire fl, stop timer and and stop string drive
            self.timer.stop()
            self.ser.write(self.forward_stop.encode())

    def startAnimation(self):
        #clear plot and re-initialize np arrays
        self.clear()
        #Initialize needed values for plotting
        self.fl = self.settings.value('flightline_length', defaultValue=150.0, type=float)
        it_sec = self.settings.value('integration_time_ms', defaultValue=100.0, type=float) / 1000
        len_per_sec = self.settings.value('advance_speed', defaultValue=1.70, type=float)
        self.len_per_frame = it_sec * len_per_sec
        self.emissionPix = np.abs(self.spec.wavelengths()-self.settings.value(
            'target_emission_wavelength', defaultValue=575, type=int)).argmin()
        self.excitationPix = np.abs(self.spec.wavelengths()-self.settings.value(
            'target_excitation_wavelength', defaultValue=525, type=int)).argmin()
        #Start String Drive (forward)
        self.ser.write(self.forward_start.encode())
        #Initialize timer
        self.timer = QTimer(self)
        #Set the timeout action
        self.timer.timeout.connect(self.plotFrame)
        self.plotFrame()
        self.timer.start(int(it_sec * 1000))

    def on_applied(self):
        #Validate all and accept if valid
        p = self.passData
        #Ground Speed
        if not p.set_ground_speed(self.ui.lineEditGS.text()):
            self._show_validation_error(
                'Entered GROUND SPEED cannot be converted to an number')
            return
        p.ground_speed_units = self.ui.comboBoxUnitsGS.currentText()
        #Spray Height
        if not p.set_spray_height(self.ui.lineEditSH.text()):
            self._show_validation_error(
                'Entered SPRAY HEIGHT cannot be converted to an number')
            return
        p.spray_height_units = self.ui.comboBoxUnitsSH.currentText()
        #Pass Heading
        if not p.set_pass_heading(self.ui.lineEditPH.text()):
            self._show_validation_error(
                'Entered PASS HEADING cannot be converted to an number')
            return
        #Wind Direction
        if not p.set_wind_direction(self.ui.lineEditWD.text()):
            self._show_validation_error(
                'Entered WIND DIRECTION cannot be converted to an number')
            return
        #Wind Speed
        if not p.set_wind_speed(self.ui.lineEditWS.text()):
            self._show_validation_error(
                'Entered WIND SPEED cannot be converted to an number')
            return
        p.wind_speed_units = self.ui.comboBoxUnitsWS.currentText()
        #Temperature
        if not p.set_temperature(self.ui.lineEditT.text()):
            self._show_validation_error(
                'Entered TEMPERATURE cannot be converted to an number')
            return
        p.temperature_units = self.ui.comboBoxUnitsT.currentText()
        #Humidity
        if not p.set_humidity(self.ui.lineEditH.text()):
            self._show_validation_error(
                'Entered GROUND SPEED cannot be converted to an number')
            return
        #Pattern
        p.setData(self.x, self.y, self.y_ex)

        #All Valid, go ahead and accept and let main know to update vals in UI
        self.applied.emit(p)

        self.accept()
        self.close()

    def reverse(self):
        if not self.ui.buttonManualReverse.isChecked():
            self.ser.write(self.reverse_stop.encode())
            self.ui.buttonManualForward.setEnabled(True)
        else:
            self.ser.write(self.reverse_start.encode())
            self.ui.buttonManualForward.setEnabled(False)

    def forward(self):
        if not self.ui.buttonManualForward.isChecked():
            self.ser.write(self.forward_stop.encode())
            self.ui.buttonManualReverse.setEnabled(True)
        else:
            self.ser.write(self.forward_start.encode())
            self.ui.buttonManualReverse.setEnabled(False)

    def clear(self):
        #Need "Are you sure?" popup only if data in arrays
        self.x = []
        self.y = []
        self.y_ex = []
        self.p.clear()

    def strip_num(self, x) -> str:
        if type(x) is str:
            if x == '':
                x = 0
        if float(x).is_integer():
            return str(int(float(x)))
        else:
            return f'{round(float(x), 2):.2f}'

    def _show_validation_error(self, message):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setText("Input Validation Error")
        msg.setInformativeText(message)
        #msg.setWindowTitle("MessageBox demo")
        #msg.setDetailedText("The details are as follows:")
        msg.setStandardButtons(QMessageBox.Ok)
        result = msg.exec()
        if result == QMessageBox.Ok:
            self.raise_()
            self.activateWindow()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = ReadString(Pass())
    sys.exit(app.exec_())
