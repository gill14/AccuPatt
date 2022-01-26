import os

import accupatt.config as cfg
import numpy as np
import pyqtgraph
import serial
from accupatt.models.passData import Pass
from accupatt.windows.editSpectrometer import EditSpectrometer
from accupatt.windows.editStringDrive import EditStringDrive
from PyQt6 import uic
from PyQt6.QtCore import QSettings, QTimer, pyqtSignal, pyqtSlot
from PyQt6.QtWidgets import QMessageBox
from seabreeze.spectrometers import Spectrometer

Ui_Form, baseclass = uic.loadUiType(os.path.join(os.getcwd(), 'resources', 'readString.ui'))

class ReadString(baseclass):
    """ A Container for communicating with the Spectrometer and String Drive """

    applied = pyqtSignal(Pass)

    def __init__(self, passData: Pass, parent = None):
        super().__init__(parent = parent)
        # Your code will go here
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        #Import Settings
        self.settings = QSettings('accupatt','AccuPatt')
        #Make ref to seriesData/passData for later updating in on_applied
        self.passData = passData
        
        #Populate Pass Info fields
        self.ui.labelPass.setText(passData.name)
        self.ui.lineEditGS.setText(passData.str_ground_speed())
        self.ui.comboBoxUnitsGS.addItems(cfg.UNITS_GS)
        self.ui.comboBoxUnitsGS.setCurrentText(passData.ground_speed_units)
        self.ui.lineEditSH.setText(passData.str_spray_height())
        self.ui.comboBoxUnitsSH.addItems(cfg.UNITS_SH)
        self.ui.comboBoxUnitsSH.setCurrentText(passData.spray_height_units)
        self.ui.lineEditPH.setText(passData.str_pass_heading())
        self.ui.lineEditWD.setText(passData.str_wind_direction())
        self.ui.lineEditWS.setText(passData.str_wind_speed())
        self.ui.comboBoxUnitsWS.addItems(cfg.UNITS_WS)
        self.ui.comboBoxUnitsWS.setCurrentText(passData.wind_speed_units)
        self.ui.lineEditT.setText(passData.str_temperature())
        self.ui.comboBoxUnitsT.addItems(cfg.UNITS_T)
        self.ui.comboBoxUnitsT.setCurrentText(passData.temperature_units)
        self.ui.lineEditH.setText(passData.str_humidity())

        #Setup Spectrometer
        self.spec = None
        self.spec_connected = False
        self.ser_connected = False
        self.setupSpectrometer()

        #Setup String Drive serial port
        self.setupStringDrive()
        
        #Enable/Disable Start and Abort buttons as applicable
        self.checkReady()

        #Setup signal slots
        self.ui.buttonManualReverse.clicked.connect(self.string_drive_manual_reverse)
        self.ui.buttonManualForward.clicked.connect(self.string_drive_manual_forward)
        self.ui.buttonEditSpectrometer.clicked.connect(self.editSpectrometer)
        self.ui.buttonEditStringDrive.clicked.connect(self.editStringDrive)
        self.ui.buttonStart.clicked.connect(self.click_start)
        self.ui.buttonAbort.clicked.connect(self.click_abort)
        self.ui.buttonClear.clicked.connect(self.click_clear)

        #Setup plot
        self.marked = False
        self.traces = dict()
        pyqtgraph.setConfigOptions(antialias=True)
        pyqtgraph.setConfigOption('background', 'k')
        pyqtgraph.setConfigOption('foreground', 'w')
        self.p = self.ui.plotWidget
        x_units = self.settings.value('flightline_length_units', defaultValue='ft', type=str)
        self.p.setLabel(axis='bottom',text='Location', units=x_units)
        self.p.setLabel(axis='left', text = 'Relative Dye Intensity')
        self.p.showGrid(x=True, y=True)

        self.clear(showPopup=False)

        #Load in pattern data from pass object if available
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

    def set_plotdata(self, name, data_x, data_y):
        if name in self.traces:
            self.traces[name].setData(data_x, data_y)
        else:
            if name == 'emission':
                self.traces[name] = self.p.plot(name='Emission',pen='w')
            if name == 'excitation':
                self.traces[name] = self.p.plot(name='Excitation',pen='c')
                #pass

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
            self.ser.write(cfg.STRING_DRIVE_FWD_STOP.encode())
            self.ui.buttonStart.setText('Start')
            self.ui.buttonAbort.setEnabled(False)
            self.ui.buttonClear.setEnabled(True)

    @pyqtSlot()
    def click_start(self):
        if not self.marked:
            #clear plot and re-initialize np arrays
            if not self.clear(showPopup=True): return
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
            self.ser.write(cfg.STRING_DRIVE_FWD_START.encode())
            self.ui.buttonStart.setText('Mark')
            self.marked = True
        else:
            #Initialize timer
            self.timer = QTimer(self)
            #Set the timeout action
            self.timer.timeout.connect(self.plotFrame)
            self.plotFrame()
            self.timer.start(int(self.settings.value('integration_time_ms', defaultValue=100.0, type=float)))
            self.ui.buttonStart.setEnabled(False)
        #Enable abort button
        self.ui.buttonAbort.setEnabled(True)
        self.ui.buttonClear.setEnabled(False)
 
    @pyqtSlot()
    def click_abort(self):
        self.timer.stop()
        self.ser.write(cfg.STRING_DRIVE_FWD_STOP.encode())
        self.clear()
        self.ui.buttonStart.setText('Start')
        self.ui.buttonStart.setEnabled(True)
        self.marked = False
        self.ui.buttonAbort.setEnabled(False)
        self.ui.buttonClear.setEnabled(True)
        
    @pyqtSlot()
    def click_clear(self):
        if self.clear(showPopup=True):
            self.ui.buttonStart.setText('Start')
            self.ui.buttonStart.setEnabled(True)
            self.marked = False
            self.ui.buttonAbort.setEnabled(False)
            self.ui.buttonClear.setEnabled(True)

    def clear(self, showPopup=True):
        if showPopup and not self.y == []:
            if not self._are_you_sure(f'Clear Existing String Data for {self.passData.name}?'):
                return False
        self.x = []
        self.y = []
        self.y_ex = []
        self.p.clear()
        self.traces = dict()
        return True

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
        #data_loc_units
        p.data_loc_units = self.settings.value('flightline_length_units', defaultValue='ft', type=str)
        #Pattern
        if len(self.x) > 0:
            p.setData(self.x, self.y, self.y_ex)

        #All Valid, go ahead and accept and let main know to update vals in UI
        self.applied.emit(p)

        self.accept()
        self.close()

    def strip_num(self, x) -> str:
        if x is None:
            return ''
        if type(x) is str:
            if x == '':
                x = 0
        if float(x).is_integer():
            return str(int(float(x)))
        else:
            return f'{round(float(x), 2):.2f}'
    
    #Only enable buttons if String Drive and Spectrometer Connected
    def checkReady(self):
        self.ready = (self.spec_connected and self.ser_connected)
        self.ui.buttonStart.setEnabled(self.ready)
        self.ui.buttonAbort.setEnabled(self.ready)
    
    '''
    String Drive Hook-Ups
    '''
    #Open String Drive Editor
    @pyqtSlot()
    def editStringDrive(self):
        e = EditStringDrive(parent=self)
        e.applied.connect(self.setupStringDrive)
        e.exec()

    def setupStringDrive(self):
        #Get a handle to the serial object, else return "Disconnected" status label
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
        
    @pyqtSlot()
    def string_drive_manual_reverse(self):
        if not self.ui.buttonManualReverse.isChecked():
            self.ser.write(cfg.STRING_DRIVE_REV_STOP.encode())
            self.ui.buttonManualForward.setEnabled(True)
        else:
            self.ser.write(cfg.STRING_DRIVE_REV_START.encode())
            self.ui.buttonManualForward.setEnabled(False)
   
    @pyqtSlot()
    def string_drive_manual_forward(self):
        if not self.ui.buttonManualForward.isChecked():
            self.ser.write(cfg.STRING_DRIVE_FWD_STOP.encode())
            self.ui.buttonManualReverse.setEnabled(True)
        else:
            self.ser.write(cfg.STRING_DRIVE_FWD_START.encode())
            self.ui.buttonManualReverse.setEnabled(False)
    
    '''
    Spectrometer Hook-Ups
    '''
    #Open Spectrometer Editor
    @pyqtSlot()
    def editSpectrometer(self):
        e = EditSpectrometer(self.spec, parent=self)
        e.applied.connect(self.setupSpectrometer)
        e.exec()
        
    def setupSpectrometer(self):
        #Get a handle to the spec object, else return "Disconnected" status
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
    
    '''
    Popup messages
    '''
    
    def _show_validation_error(self, message):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.setText("Input Validation Error")
        msg.setInformativeText(message)
        #msg.setWindowTitle("MessageBox demo")
        #msg.setDetailedText("The details are as follows:")
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        result = msg.exec()
        if result == QMessageBox.StandardButton.Ok:
            self.raise_()
            self.activateWindow()
            
    def _are_you_sure(self, message):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.setText("Are You Sure?")
        msg.setInformativeText(message)
        #msg.setWindowTitle("MessageBox demo")
        #msg.setDetailedText("The details are as follows:")
        msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        result = msg.exec()
        return result == QMessageBox.StandardButton.Yes

