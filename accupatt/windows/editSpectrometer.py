import os

import numpy as np
from PyQt6 import uic
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QMessageBox
from seabreeze.spectrometers import Spectrometer

Ui_Form, baseclass = uic.loadUiType(
    os.path.join(os.getcwd(), "resources", "editSpectrometer.ui")
)

icon_file = os.path.join(os.getcwd(), "resources", "refresh.png")


class EditSpectrometer(baseclass):

    wav_ex_changed = pyqtSignal(int)
    wav_em_changed = pyqtSignal(int)
    integration_time_ms_changed = pyqtSignal(int)

    def __init__(self, spectrometer, wav_ex, wav_em, integration_time_ms, parent=None):
        super().__init__(parent=parent)
        self.ui = Ui_Form()
        self.ui.setupUi(self)

        self.spec = spectrometer

        self.ui.lineEditEx.setText(str(wav_ex))
        self.ui.lineEditEm.setText(str(wav_em))
        self.ui.lineEditIntegrationTime.setText(str(integration_time_ms))

        # Hook up signals
        self.ui.buttonRefresh.setIcon(QIcon(icon_file))
        self.ui.buttonRefresh.clicked.connect(self.refresh_spec)
        self.ui.lineEditEx.textChanged.connect(self.refresh_spec)
        self.ui.lineEditEm.textChanged.connect(self.refresh_spec)

        self.refresh_spec()

        self.show()

    def refresh_spec(self):
        if self.spec == None:
            try:
                self.spec = Spectrometer.from_first_available()
            except:
                self.ui.labelSpec.setText("Spectrometer: None")
                self.ui.labelEx.setText("")
                self.ui.labelEm.setText("")
                self.ui.labelSerialNumber.setText("")
                return
        self.ui.labelSerialNumber.setText(
            f"Spectrometer Serial Number: {self.spec.serial_number}"
        )
        self.ui.labelSpec.setText(f"Spectrometer: {self.spec.model}")
        wav = self.spec.wavelengths()
        # Check that wav_ex is a number
        try:
            pix_ex = np.abs(wav - float(self.ui.lineEditEx.text())).argmin()
            wav_ex = wav[pix_ex]
            self.ui.labelEx.setText(
                f"Actual Excitation is {self.strip_num(wav_ex)}nm at pixel #{pix_ex}"
            )
        except:
            self.ui.labelEx.setText("Invalid Target Excitation Wavelength")
        # Check that wav_em is a number
        try:
            pix_em = np.abs(wav - int(self.ui.lineEditEm.text())).argmin()
            wav_em = wav[pix_em]
            self.ui.labelEm.setText(
                f"Actual Emission is {self.strip_num(wav_em)}nm at pixel #{pix_em}"
            )
        except:
            self.ui.labelEm.setText("Invalid Target Emission Wavelength")

    def strip_num(self, x) -> str:
        if type(x) is str:
            if x == "":
                x = 0
        if float(x).is_integer():
            return str(int(float(x)))
        else:
            return f"{round(float(x), 2):.2f}"

    def accept(self):
        excepts = []
        # Save Excitation Wavelength
        try:
            self.wav_ex_changed.emit(int(self.ui.lineEditEx.text()))
        except:
            excepts.append(
                "-TARGET EXCITATION WAVELENGTH cannot be converted to an INTEGER"
            )
        try:
            self.wav_em_changed.emit(int(self.ui.lineEditEm.text()))
        except:
            excepts.append(
                "-TARGET EMISSION WAVELENGTH cannot be converted to an INTEGER"
            )
        try:
            self.integration_time_ms_changed.emit(
                int(self.ui.lineEditIntegrationTime.text())
            )
        except:
            excepts.append("-INTEGRATION TIME cannot be converted to an INTEGER")
        # If any invalid, show user and return to current window
        if len(excepts) > 0:
            QMessageBox.warning(self, "Invalid Data", "\n".join(excepts))
            return
        # Release spectrometer
        self.spec.close()
        # If all checks out, notify requestor and close
        super().accept()
