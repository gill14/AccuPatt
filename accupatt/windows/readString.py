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

Ui_Form, baseclass = uic.loadUiType(os.path.join(os.getcwd(), 'resources', 'readString.ui'))

class ReadString(baseclass):
    
    def __init__(self, passData: Pass, parent = None):
        super().__init__(parent = parent)
        self.ui = Ui_Form()
        self.ui.setupUi(self)

        #Make ref to seriesData/passData for later updating in on_applied
        self.passData = passData
        #Populate Pass Info Widget fields
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

        #Setup Spectrometer and String Drive
        self.spec = None
        self.spec_connected = False
        self.ser = None
        self.ser_connected = False
        self.setupSpectrometer()
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
        self.p.setLabel(axis='bottom',text='Location', units=self.string_length_units)
        self.p.setLabel(axis='left', text = 'Relative Dye Intensity')
        self.p.showGrid(x=True, y=True)

        self.clear(showPopup=False)

        #Load in pattern data from pass object if available
        if passData.has_string_data():
            self.x = np.array(passData.string.data['loc'].values, dtype=float)
            self.y = np.array(passData.string.data[passData.name].values, dtype=float)
            self.y_ex = np.array(passData.string.data_ex[passData.name].values, dtype=float)
            self.set_plotdata(name='emission', data_x=self.x, data_y=self.y)
            #self.set_plotdata(name='excitation', data_x=self.x, data_y=self.y_ex)
            self.set_plotdata(name='emission', data_x=self.x, data_y=self.y)
            #self.set_plotdata(name='excitation', data_x=self.x, data_y=self.y_ex)

        self.show()

    def load_defaults(self):
        self.string_drive_port = cfg.get_string_drive_port()
        self.string_length = cfg.get_string_length()
        self.string_speed = cfg.get_string_speed()
        # Calculate from all above
        self.len_per_frame = self.integration_time_ms * self.string_speed / 1000

    def set_plotdata(self, name, data_x, data_y):
        if name in self.traces:
            self.traces[name].setData(data_x, data_y)
        else:
            if name == 'emission':
                self.traces[name] = self.p.plot(name='Emission',pen='w')
            if name == 'excitation':
                self.traces[name] = self.p.plot(name='Excitation',pen='c')

    def plotFrame(self):
        #get Location
        ellapsedTimeSec = (self.timer.interval() - self.timer.remainingTime()) / 1000
        location = -self.string_length/2 + (ellapsedTimeSec * self.string_speed)
        #print(f'Location: {location} FT')
        #Capture and record one frame
        #record x_val (location)
        self.x = np.append(self.x, location)
        #take a full spectrum reading
        intensities = self.spec.intensities(correct_dark_counts=True,
            correct_nonlinearity=True)
        #record y_val (emission amplitute) and request plot update
        self.y = np.append(self.y, intensities[self.pix_em])
        self.set_plotdata(name='emission', data_x=self.x, data_y=self.y)
        #record y_ex_val (excitation amplitude) and request plot update
        self.y_ex = np.append(self.y_ex, intensities[self.pix_ex])
        #self.set_plotdata(name='excitation', data_x=self.x, data_y=self.y_ex)
    
    @pyqtSlot()
    def endPlot(self):
        self.timer_trigger.stop()
        self.ser.write(cfg.STRING_DRIVE_FWD_STOP.encode())
        self.ui.buttonStart.setText('Start')
        self.marked = False
        self.ui.buttonAbort.setEnabled(False)
        self.ui.buttonClear.setEnabled(True)

    @pyqtSlot()
    def click_start(self):
        if not self.marked:
            #clear plot and re-initialize np arrays
            if not self.clear(showPopup=True): 
                return
            #Start String Drive (forward)
            self.ser.write(cfg.STRING_DRIVE_FWD_START.encode())
            self.ui.buttonStart.setText('Mark')
            self.marked = True
        else:
            #Initialize timers
            self.timer = QTimer(self)
            self.timer_trigger = QTimer(self)
            #Set the intervals and timeouts
            self.timer.setSingleShot(True)
            self.timer.setInterval(int((self.string_length / self.string_speed) * 1000))
            self.timer.timeout.connect(self.endPlot)
            self.timer_trigger.setInterval(int(self.integration_time_ms))
            self.timer_trigger.timeout.connect(self.plotFrame)
            #print(f'timer = {self.timer.interval()}')
            #print(f'timer_trigger = {self.timer_trigger.interval()}')
            # Plot initial frame
            #self.plotFrame()
            # Start timers
            self.timer.start()
            self.timer_trigger.start()
            self.ui.buttonStart.setEnabled(False)
        #Enable abort button
        self.ui.buttonAbort.setEnabled(True)
        self.ui.buttonClear.setEnabled(False)
 
    @pyqtSlot()
    def click_abort(self):
        self.timer.stop()
        self.timer_trigger.stop()
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
            msg = QMessageBox.question(self, 'Are You Sure?',
                                       f'Clear Existing String Data for {self.passData.name}?')
            if msg == QMessageBox.StandardButton.No:
                return False
        self.x = []
        self.y = []
        self.y_ex = []
        self.p.clear()
        self.traces = dict()
        return True

    def reject(self):
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
            QMessageBox.warning(self, 'Invalid Data', '\n'.join(excepts))
            return
        #Pattern
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
        e = EditStringDrive(ser=self.ser, string_length_units=self.string_length_units, parent=self)
        e.string_length_units_changed.connect(self.string_length_units_changed)
        e.accepted.connect(self.reSetupStringDrive)
        e.exec()

    def setupStringDrive(self):
        #Get a handle to the serial object, else return "Disconnected" status label
        try:
            self.ser = serial.Serial(self.string_drive_port, baudrate=9600, timeout=1)
            self.ser_connected = True
        except:
            self.ui.labelStringDrive.setText('String Drive: DISCONNECTED')
            self.ser_connected = False
            return
        #Setup String Drive labels
        self.ui.labelStringDrive.setText(f'String Drive Port: {self.ser.name}')
        self.ui.labelStringLength.setText(f'String Length: {self.strip_num(self.string_length)} {self.string_length_units}')
        self.ui.labelStringVelocity.setText(f'String Velocity: {self.strip_num(self.string_speed)} {self.string_length_units}/sec')
        #Enale/Disable manual drive buttons
        self.ui.buttonManualReverse.setEnabled(self.ser_connected)
        self.ui.buttonManualForward.setEnabled(self.ser_connected)
        self.checkReady()
    
    @pyqtSlot(str)
    def string_length_units_changed(self, units: str):
        self.string_length_units = units
        self.p.setLabel(axis='bottom',text='Location', units=units)
        pass
    
    @pyqtSlot()
    def reSetupStringDrive(self):
        self.load_defaults()
        self.setupStringDrive()
        
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
        e = EditSpectrometer(self.spec, self.wav_ex, self.wav_em, self.integration_time_ms, parent=self)
        e.accepted.connect(self.reSetupSpectrometer)
        e.exec()
        
    def setupSpectrometer(self):
        # Get a handle to the spec object, else return "Disconnected" status
        if self.spec == None:
            try:
                self.spec = Spectrometer.from_first_available()
                self.spec_connected = True
            except:
                self.ui.labelSpec.setText('Spectrometer: DISCONNECTED')
                self.spec_connected = False
                return
        # Inform spectrometer of new int time
        self.spec.integration_time_micros(self.integration_time_ms * 1000)
        # Get a handle on pixels for chosen wavelengths
        wavelengths = self.spec.wavelengths()
        self.pix_ex = np.abs(wavelengths-self.wav_ex).argmin()
        self.pix_em = np.abs(wavelengths-self.wav_em).argmin()
        # Populate Spectrometer labels
        self.ui.labelSpec.setText(f"Spectrometer: {self.spec.model}")
        self.ui.labelExcitation.setText(
            f"Excitation: {self.wav_ex} nm")
        self.ui.labelEmission.setText(
            f"Emission: {self.wav_em} nm")
        self.ui.labelIntegrationTime.setText(
            f"Integration Time: {self.integration_time_ms} ms")
        self.checkReady()
        
    @pyqtSlot()
    def reSetupSpectrometer(self):
        self.load_defaults() # To re-calc len_per_frame w/ new int time
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
    
