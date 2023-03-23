import os
import subprocess
import sys
import serial

import accupatt.config as cfg
from accupatt.windows.calculateStringSpeed import CalculateStringSpeed
from PyQt6 import uic
from PyQt6.QtCore import pyqtSlot, pyqtSignal
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QMessageBox, QPushButton
from serial.tools import list_ports
from serial import Serial

Ui_Form, baseclass = uic.loadUiType(
    os.path.join(os.getcwd(), "resources", "editStringDrive.ui")
)

icon_file = os.path.join(os.getcwd(), "resources", "refresh.png")


class EditStringDrive(baseclass):
    string_drive_connected = pyqtSignal(Serial)
    string_length_units_changed = pyqtSignal(str)

    def __init__(
        self,
        ser: serial.Serial,
        string_length_units,
        disconnect_on_close=False,
        parent=None,
    ):
        super().__init__(parent=parent)
        self.ui = Ui_Form()
        self.ui.setupUi(self)

        self.button_reverse: QPushButton = self.ui.buttonReverse
        self.button_reverse.clicked.connect(self.string_drive_manual_reverse)
        self.button_forward: QPushButton = self.ui.buttonAdvance
        self.button_forward.clicked.connect(self.string_drive_manual_advance)

        self.disconnect_on_close = disconnect_on_close

        self.ser = ser

        # Hook up serial port combobox signal
        self.ui.comboBoxSerialPort.currentTextChanged[str].connect(self.on_sp_selected)
        # Init serial port combobox
        self.refresh_sp_list()

        # Hook up Refresh Button signal
        self.ui.buttonRefresh.setIcon(QIcon(icon_file))
        self.ui.buttonRefresh.clicked.connect(self.refresh_sp_list)

        # Init flightline Length
        self.ui.comboBoxFlightlineLengthUnits.currentTextChanged[str].connect(
            self.on_fl_units_selected
        )
        self.ui.lineEditFlightlineLength.setText(
            self.strip_num(cfg.get_string_length())
        )
        self.ui.comboBoxFlightlineLengthUnits.addItems(cfg.UNITS_LENGTH_LARGE)
        self.ui.comboBoxFlightlineLengthUnits.setCurrentText(string_length_units)

        # Init advance Speed
        self.ui.lineEditSpeed.setText(self.strip_num(cfg.get_string_speed()))

        # Init calc string speed button
        self.ui.buttonCalculateStringSpeed.pressed.connect(self.click_calc_speed)

        # Direct commands

        self.ui.pushButtonSendCommand.pressed.connect(self.send_command)
        self.ui.pushButtonHelp.pressed.connect(self.openStepperManual)

        self.show()

    def refresh_sp_list(self):
        self.ui.comboBoxSerialPort.clear()
        for port in list_ports.comports():
            self.ui.comboBoxSerialPort.addItems([port.device])
        # Check if saved port in box
        index = self.ui.comboBoxSerialPort.findText(cfg.get_string_drive_port())
        self.ui.comboBoxSerialPort.setCurrentIndex(index)

    def on_sp_selected(self):
        self.ui.buttonCalculateStringSpeed.setEnabled(False)
        if self.ser is not None:
            self.ser.close()
        for port in list_ports.comports():
            if port.device == self.ui.comboBoxSerialPort.currentText():
                self.ui.labelSerialPort1.setText(
                    f"Manufacturer: {port.manufacturer}, VID: {port.vid}"
                )
                self.ui.labelSerialPort2.setText(
                    f"Product: {port.product}, PID: {port.pid}"
                )
                self.ui.labelSerialPort3.setText(f"Location: {port.location}")
                # Open the port
                if self.ser:
                    self.ser.close()
                    self.ser.setPort(port.device)
                    self.ser.open()
                else:
                    self.ser = Serial(port=port.device, timeout=1)
                if self.ser.is_open:
                    self.string_drive_connected.emit(self.ser)
        self.enableButtons()

    def on_fl_units_selected(self):
        self.ui.labelSpeedUnits.setText(
            f"{self.ui.comboBoxFlightlineLengthUnits.currentText()}/sec"
        )

    @pyqtSlot(str, str)
    def update_speed(self, text, text_units):
        self.ui.lineEditSpeed.setText(text)
        self.ui.comboBoxFlightlineLengthUnits.setCurrentText(text_units)

    @pyqtSlot()
    def click_calc_speed(self):
        e = CalculateStringSpeed(
            ser=self.ser,
            length=self.ui.lineEditFlightlineLength.text(),
            length_units=self.ui.comboBoxFlightlineLengthUnits.currentText(),
            parent=self,
        )
        e.speed_accepted[str, str].connect(self.update_speed)
        e.exec()

    def enableButtons(
        self,
        reverse=True,
        advance=True,
    ):
        if not self.ser.is_open:
            reverse = False
            advance = False
        self.button_reverse.setEnabled(reverse)
        self.button_forward.setEnabled(advance)
        self.ui.buttonCalculateStringSpeed.setEnabled(self.ser.is_open)
        self.ui.pushButtonSendCommand.setEnabled(self.ser.is_open)

    @pyqtSlot()
    def string_drive_manual_reverse(self):
        if not self.button_reverse.isChecked():
            self.ser.write(cfg.STRING_DRIVE_REV_STOP.encode())
            self.button_reverse.setText("<- Reverse")
            self.enableButtons()
        else:
            self.ser.write(cfg.STRING_DRIVE_REV_START.encode())
            self.button_reverse.setText("-- STOP --")
            self.enableButtons(advance=False)

    @pyqtSlot()
    def string_drive_manual_advance(self):
        if not self.button_forward.isChecked():
            self.ser.write(cfg.STRING_DRIVE_FWD_STOP.encode())
            self.button_forward.setText("Forward ->")
            self.enableButtons()
        else:
            self.ser.write(cfg.STRING_DRIVE_FWD_START.encode())
            self.button_forward.setText("-- STOP --")
            self.enableButtons(reverse=False)

    @pyqtSlot()
    def send_command(self):
        if self.ser and self.ser.is_open:
            command: str = self.ui.lineEditCommand.text()
            command = command + "\r"
            if command != "":
                self.ser.write(command.encode())
                self.ui.labelReturn.setText(self.ser.readline().decode("utf-8"))

    @pyqtSlot()
    def openStepperManual(self):
        file = os.path.join(
            os.getcwd(), "resources", "documents", "weeder_stepper_driver_manual.pdf"
        )
        if sys.platform == "darwin":
            subprocess.call(["open", file])
        elif sys.platform == "win32":
            os.startfile(file)

    def strip_num(self, x) -> str:
        if type(x) is str:
            if x == "":
                x = 0
        if float(x).is_integer():
            return str(int(float(x)))
        else:
            return f"{round(float(x), 2):.2f}"

    def disconnect_if_requested(self):
        if self.disconnect_on_close:
            if self.ser:
                self.ser.close()

    def accept(self):
        excepts = []
        # Disconnect serial
        self.disconnect_if_requested()
        # Save Serial Port
        cfg.set_string_drive_port(self.ui.comboBoxSerialPort.currentText())
        # Save String Length
        try:
            cfg.set_string_length(float(self.ui.lineEditFlightlineLength.text()))
        except:
            excepts.append("-STRING LENGTH cannot be converted to a NUMBER")
        # Signal to change string length units (not handled via settings)
        self.string_length_units_changed.emit(
            self.ui.comboBoxFlightlineLengthUnits.currentText()
        )
        # Save String Speed
        try:
            cfg.set_string_speed(float(self.ui.lineEditSpeed.text()))
        except:
            excepts.append("-STRING SPEED cannot be converted to a NUMBER")
        # If any invalid, show user and return to current window
        if len(excepts) > 0:
            QMessageBox.warning(self, "Invalid Data", "\n".join(excepts))
            return
        # If all checks out, notify requestor and close
        super().accept()

    def reject(self):
        self.disconnect_if_requested()
        super().reject()
