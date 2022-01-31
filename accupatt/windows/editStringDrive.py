import os

import accupatt.config as cfg
from accupatt.windows.calculateStringSpeed import CalculateStringSpeed
from PyQt6 import uic
from PyQt6.QtCore import QSettings, pyqtSlot
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QMessageBox
from serial.tools import list_ports

Ui_Form, baseclass = uic.loadUiType(os.path.join(os.getcwd(), 'resources', 'editStringDrive.ui'))

icon_file = os.path.join(os.getcwd(), 'resources', 'refresh.png')

class EditStringDrive(baseclass):

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.ui = Ui_Form()
        self.ui.setupUi(self)

        #Load in Settings or use defaults
        self.settings = QSettings('accupatt','AccuPatt')

        #Hook up serial port combobox signal
        self.ui.comboBoxSerialPort.currentTextChanged[str].connect(self.on_sp_selected)
        #Init serial port combobox
        self.refresh_sp_list()

        #Hook up Refresh Button signal
        self.ui.buttonRefresh.setIcon(QIcon(icon_file))
        self.ui.buttonRefresh.clicked.connect(self.refresh_sp_list)

        #Init flightline Length
        self.ui.comboBoxFlightlineLengthUnits.currentTextChanged[str].connect(self.on_fl_units_selected)
        self.ui.lineEditFlightlineLength.setText(self.strip_num(
            self.settings.value('flightline_length', defaultValue=150.0, type=float)
        ))
        self.ui.comboBoxFlightlineLengthUnits.addItems(cfg.UNITS_LENGTH_LARGE)
        self.ui.comboBoxFlightlineLengthUnits.setCurrentText(
            self.settings.value('flightline_length_units', defaultValue='ft', type=str)
        )

        #Init advance Speed
        self.ui.lineEditSpeed.setText(self.strip_num(
            self.settings.value('advance_speed', defaultValue=1.70, type=float)
        ))
        
        #Init calc string speed button
        self.ui.buttonCalculateStringSpeed.pressed.connect(self.click_calc_speed)

        self.show()

    def refresh_sp_list(self):
        self.ui.comboBoxSerialPort.clear()
        for port in list_ports.comports():
            self.ui.comboBoxSerialPort.addItems([port.device])
        #Check if saved port in box
        index = self.ui.comboBoxSerialPort.findText(
            self.settings.value('serial_port_device', defaultValue='', type=str)
        )
        self.ui.comboBoxSerialPort.setCurrentIndex(index)

    def on_sp_selected(self):
        self.ui.buttonCalculateStringSpeed.setEnabled(False)
        for port in list_ports.comports():
            if port.device == self.ui.comboBoxSerialPort.currentText():
                self.ui.labelSerialPort1.setText(f'Manufacturer: {port.manufacturer}, VID: {port.vid}')
                self.ui.labelSerialPort2.setText(f'Product: {port.product}, PID: {port.pid}')
                self.ui.labelSerialPort3.setText(f'Location: {port.location}')
                self.ui.buttonCalculateStringSpeed.setEnabled(True)

    def on_fl_units_selected(self):
        self.ui.labelSpeedUnits.setText(f'{self.ui.comboBoxFlightlineLengthUnits.currentText()}/sec')

    @pyqtSlot(str, str)
    def update_speed(self, text, text_units):
        self.ui.lineEditSpeed.setText(text)
        self.ui.comboBoxFlightlineLengthUnits.setCurrentText(text_units)

    @pyqtSlot()
    def click_calc_speed(self):
        e = CalculateStringSpeed(port=self.ui.comboBoxSerialPort.currentText(),
                                 length=self.ui.lineEditFlightlineLength.text(),
                                 length_units=self.ui.comboBoxFlightlineLengthUnits.currentText(),
                                 parent=self)
        e.speed_accepted[str,str].connect(self.update_speed)
        e.exec()

    def strip_num(self, x) -> str:
        if type(x) is str:
            if x == '':
                x = 0
        if float(x).is_integer():
            return str(int(float(x)))
        else:
            return f'{round(float(x), 2):.2f}'

    def accept(self):
        excepts = []
        # Save Serial Port
        port = self.ui.comboBoxSerialPort.currentText()
        if not port == '':
            self.settings.setValue('serial_port_device', port)
        # Save String Length & Units
        try:
            self.settings.setValue('flightline_length',float(self.ui.lineEditFlightlineLength.text()))
        except:
            excepts.append('-STRING LENGTH cannot be converted to a NUMBER')
        self.settings.setValue('flightline_length_units', self.ui.comboBoxFlightlineLengthUnits.currentText())
        # Save String Speed
        try:
            self.settings.setValue('advance_speed',float(self.ui.lineEditSpeed.text()))
        except:
            excepts.append('-STRING SPEED cannot be converted to a NUMBER')
        # If any invalid, show user and return to current window
        if len(excepts) > 0:
            QMessageBox.warning(self, 'Invalid Data', '\n'.join(excepts))
            return
        # If all checks out, notify requestor and close
        super().accept()
