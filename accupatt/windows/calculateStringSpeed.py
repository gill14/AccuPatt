import os

import accupatt.config as cfg
import serial
from PyQt6 import uic
from PyQt6.QtCore import QTimer, pyqtSignal, pyqtSlot

Ui_Form, baseclass = uic.loadUiType(
    cfg.resource_path("resources", "calculateStringSpeed.ui")
)


class CalculateStringSpeed(baseclass):
    speed_accepted = pyqtSignal(str, str)

    def __init__(self, ser: serial.Serial, length, length_units, parent=None):
        super().__init__(parent=parent)
        self.ui = Ui_Form()
        self.ui.setupUi(self)

        # Fill UI
        self.ui.lineEditLength.setText(str(length))
        self.ui.comboBox.addItems(cfg.UNITS_LENGTH_LARGE)
        self.ui.comboBox.setCurrentText(length_units)
        self.ui.comboBox.currentTextChanged[str].connect(self.length_units_changed)
        self.ui.labelUnitsTime.setText("sec")
        self.ui.labelUnitsSpeed.setText(f"{length_units}/sec")
        self.ui.button.pressed.connect(self.button_pressed)

        # Disable OK until a speed has been measured
        self.ui.buttonBox.button(
            self.ui.buttonBox.StandardButton.Ok
        ).setEnabled(False)
        self._set_button_start()

        # Serial Port
        self.serialPort = ser
        if not self.serialPort.is_open:
            self.serialPort.open()
        # State to know whether winding or not
        self.state = False

        self.show()

    def _set_button_start(self):
        self.ui.button.setText("Start")
        self.ui.button.setStyleSheet(
            "QPushButton { background-color: #4CAF50; color: white; font-weight: bold; border-radius: 4px; }"
            "QPushButton:hover { background-color: #45a049; }"
            "QPushButton:pressed { background-color: #388e3c; }"
        )

    def _set_button_stop(self):
        self.ui.button.setText("Stop")
        self.ui.button.setStyleSheet(
            "QPushButton { background-color: #f44336; color: white; font-weight: bold; border-radius: 4px; }"
            "QPushButton:hover { background-color: #e53935; }"
            "QPushButton:pressed { background-color: #c62828; }"
        )

    @pyqtSlot(str)
    def length_units_changed(self, text):
        self.ui.labelUnitsSpeed.setText(f"{text}/sec")

    @pyqtSlot()
    def button_pressed(self):
        if self.state:
            self.stopCalc()
        else:
            self.startCalc()

    @pyqtSlot()
    def update_elapsed_time(self):
        self.time += 1
        self.ui.lineEditTime.setText(str(self.time))

    def startCalc(self):
        # Clear timer/speed
        self.ui.lineEditTime.clear()
        self.ui.lineEditSpeed.clear()
        # Start String Drive
        self.serialPort.write(cfg.STRING_DRIVE_FWD_START.encode())
        # Initialize and start timer
        self.time = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_elapsed_time)
        self.timer.start(1000)
        # Change Button Text and State
        self._set_button_stop()
        self.state = True

    def stopCalc(self):
        # Stop Timer and String Drive
        self.timer.stop()
        self.serialPort.write(cfg.STRING_DRIVE_FWD_STOP.encode())
        # Change Button Text
        self._set_button_start()
        # Calc and show new speed
        length = float(self.ui.lineEditLength.text())
        time = float(self.ui.lineEditTime.text())
        self.ui.lineEditSpeed.setText(f"{length/time:.2f}")
        # Enable OK now that a speed has been calculated
        self.ui.buttonBox.button(
            self.ui.buttonBox.StandardButton.Ok
        ).setEnabled(True)

    def accept(self):
        # Send back new speed val as str
        self.speed_accepted.emit(
            self.ui.lineEditSpeed.text(), self.ui.labelUnitsSpeed.text()
        )
        super().accept()
