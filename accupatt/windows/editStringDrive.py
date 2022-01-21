import os

import accupatt.config as cfg
from PyQt6 import uic
from PyQt6.QtCore import QSettings, pyqtSignal
from PyQt6.QtWidgets import QApplication, QMessageBox
from serial.tools import list_ports

Ui_Form, baseclass = uic.loadUiType(os.path.join(os.getcwd(), 'accupatt', 'windows', 'ui', 'editStringDrive.ui'))

class EditStringDrive(baseclass):

    applied = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        # Your code will go here
        self.ui = Ui_Form()
        self.ui.setupUi(self)

        #Load in Settings or use defaults
        self.settings = QSettings('BG Application Consulting','AccuPatt')

        #Hook up serial port combobox signal
        self.ui.comboBoxSerialPort.currentTextChanged[str].connect(self.on_sp_selected)
        #Init serial port combobox
        self.refresh_sp_list()

        #Hook up Refresh Button signal
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

        #Utilize built-in signals
        self.ui.buttonBox.accepted.connect(self.on_applied)
        self.ui.buttonBox.rejected.connect(self.reject)

        # Your code ends here
        self.show()

    def refresh_sp_list(self):
        self.ui.comboBoxSerialPort.clear()
        list = list_ports.comports()
        for item in list:
            self.ui.comboBoxSerialPort.addItems([item.device])
        #Check if saved port in box
        index = self.ui.comboBoxSerialPort.findText(
            self.settings.value('serial_port_device', defaultValue='', type=str)
        )
        self.ui.comboBoxSerialPort.setCurrentIndex(index)

    def on_sp_selected(self):
        list = list_ports.comports()
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
            self.settings.setValue('flightline_length',float(self.ui.lineEditFlightlineLength.text()))
        except:
            self._show_validation_error(
                'Entered FLIGHTLINE LENGTH cannot be converted to a NUMBER')
            return
        self.settings.setValue('flightline_length_units',self.ui.comboBoxFlightlineLengthUnits.currentText())
        try:
            self.settings.setValue('advance_speed',float(self.ui.lineEditSpeed.text()))
        except:
            self._show_validation_error(
                'Entered ADVANCE SPEED cannot be converted to a NUMBER')
            return
        #All Valid, go ahead and accept and let main know to update vals
        self.applied.emit()

        self.accept()
        self.close()

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

