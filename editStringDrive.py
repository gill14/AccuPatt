import sys

from PyQt5 import QtWidgets as qtw
from PyQt5 import QtCore as qtc
from PyQt5 import QtGui as qtg
from PyQt5 import uic

import serial
from serial.tools import list_ports

Ui_Form, baseclass = uic.loadUiType('editStringDrive.ui')

class EditStringDrive(baseclass):

    applied = qtc.pyqtSignal()

    units_length = {'ft','m'}

    def __init__(self):
        super().__init__()
        # Your code will go here
        self.ui = Ui_Form()
        self.ui.setupUi(self)

        #Load in Settings or use defaults
        self.settings = qtc.QSettings('BG Application Consulting','AccuPatt')
        #Serial Port
        if self.settings.contains('serial_port_device'):
            self.serial_port_device = self.settings.value('serial_port_device')
        else:
            self.serial_port_device = ''
        #Flightline Length
        if self.settings.contains('flightline_length'):
            self.flightline_length = self.settings.value('flightline_length', type=float)
        else:
            self.flightline_length = 150
        #Flightline Length Units
        if self.settings.contains('flightline_length_units'):
            self.flightline_length_units = self.settings.value('flightline_length_units')
        else:
            self.flightline_length_units = 'ft'
        #Advance Speed
        if self.settings.contains('advance_speed'):
            self.advance_speed = self.settings.value('advance_speed', type=float)
        else:
            self.advance_speed = 1.70



        #Hook up serial port combobox signal
        self.ui.comboBoxSerialPort.currentTextChanged[str].connect(self.on_sp_selected)
        #Init serial port combobox
        self.refresh_sp_list()

        #Hook up Refresh Button signal
        self.ui.buttonRefresh.clicked.connect(self.refresh_sp_list)

        #Init flightline Length
        self.ui.comboBoxFlightlineLengthUnits.currentTextChanged[str].connect(self.on_fl_units_selected)
        self.ui.lineEditFlightlineLength.setText(self.strip_num(self.flightline_length))
        self.ui.comboBoxFlightlineLengthUnits.addItems(self.units_length)
        self.ui.comboBoxFlightlineLengthUnits.setCurrentText(self.flightline_length_units)

        #Init advance Speed
        self.ui.lineEditSpeed.setText(self.strip_num(self.advance_speed))

        #Utilize built-in signals
        self.ui.buttonBox.accepted.connect(self.on_applied)
        self.ui.buttonBox.rejected.connect(self.reject)

        # Your code ends here
        self.show()

    def refresh_sp_list(self):
        self.ui.comboBoxSerialPort.clear()
        list = serial.tools.list_ports.comports()
        for item in list:
            self.ui.comboBoxSerialPort.addItems([item.device])
        #Check if saved port in box
        index = self.ui.comboBoxSerialPort.findText(self.serial_port_device)
        self.ui.comboBoxSerialPort.setCurrentIndex(index)

    def on_sp_selected(self):
        list = serial.tools.list_ports.comports()
        for info in list:
            if info.device == self.ui.comboBoxSerialPort.currentText():
                self.ui.labelSerialPort1.setText(f'Manufacturer: {info.manufacturer}, VID: {info.vid}')
                self.ui.labelSerialPort2.setText(f'Product: {info.product}, PID: {info.pid}')
                self.ui.labelSerialPort3.setText(f'Location: {info.location}')

    def on_fl_units_selected(self):
        self.ui.labelSpeedUnits.setText(f'{self.ui.comboBoxFlightlineLengthUnits.currentText()}/sec')

    def strip_num(self, x) -> str:
        if type(x) is str:
            if x == '':
                x = 0
        if float(x).is_integer():
            return str(int(float(x)))
        else:
            return f'{round(float(x), 2):.2f}'

    def on_applied(self):
        #Validate all and accept if valid
        if not self.ui.comboBoxSerialPort.currentText() == '':
            self.settings.setValue('serial_port_device',self.ui.comboBoxSerialPort.currentText())
        try:
            self.settings.setValue('flightline_length',self.ui.lineEditFlightlineLength.text())
        except:
            print('unable to set flightline_length to settings')
            return
        try:
            self.settings.setValue('flightline_length_units',self.ui.comboBoxFlightlineLengthUnits.currentText())
        except:
            print('unable to set flightline_length_units to settings')
            return
        try:
            self.settings.setValue('advance_speed',self.ui.lineEditSpeed.text())
        except:
            print('unable to set advance_speed to settings')
            return
        #All Valid, go ahead and accept and let main know to update vals
        self.applied.emit()

        self.accept()
        self.close()

if __name__ == '__main__':
    app = qtw.QApplication(sys.argv)
    w = EditStringDrive()
    sys.exit(app.exec_())
