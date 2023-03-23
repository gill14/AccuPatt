import os

import numpy as np
from PyQt6 import uic
from PyQt6.QtCore import pyqtSignal, pyqtSlot, QSignalBlocker
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QPushButton, QComboBox, QLineEdit, QMessageBox
from seabreeze.spectrometers import Spectrometer

from accupatt.models.dye import Dye
import accupatt.config as cfg
from accupatt.windows.definedDyeManager import DyeManager
from accupatt.windows.testSpectrometer import TestSpectrometer

Ui_Form, baseclass = uic.loadUiType(
    os.path.join(os.getcwd(), "resources", "editSpectrometer.ui")
)


class EditSpectrometer(baseclass):
    dye_changed = pyqtSignal(str)
    spectrometer_connected = pyqtSignal(Spectrometer)
    spectrometer_display_unit_changed = pyqtSignal()

    def __init__(self, spectrometer: Spectrometer, dye: Dye, parent=None):
        super().__init__(parent=parent)
        self.ui = Ui_Form()
        self.ui.setupUi(self)

        self.spec = spectrometer
        self.dye = dye

        self.le_spectrometer: QLineEdit = self.ui.lineEditSpectrometer

        self.b_refresh: QPushButton = self.ui.buttonRefresh
        self.b_refresh.clicked.connect(self.refresh_spec)

        self.cb_dye: QComboBox = self.ui.comboBoxDye

        self.b_dye_manager: QPushButton = self.ui.buttonDyeManager
        self.b_dye_manager.clicked.connect(self.open_dye_manager)

        self.cb_units: QComboBox = self.ui.displayUnitsComboBox
        self.cb_units.addItems(cfg.SPECTROMETER_DISPLAY_UNITS)
        self.cb_units.setCurrentText(cfg.get_spectrometer_display_unit())
        self.cb_units.currentTextChanged[str].connect(self.display_units_changed)

        self.b_test_spectrometer: QPushButton = self.ui.buttonTestSpectrometer
        self.b_test_spectrometer.clicked.connect(self.test_spectrometer)

        self.refresh_spec()
        self.refresh_dyes()

    def refresh_spec(self):
        if self.spec is None:
            try:
                self.spec = Spectrometer.from_first_available()
            except:
                self.le_spectrometer.setText("")
                self.b_test_spectrometer.setEnabled(False)
                return
        self.le_spectrometer.setText(self.spec.model)
        self.b_test_spectrometer.setEnabled(True)
        self.spectrometer_connected.emit(self.spec)

    def refresh_dyes(self):
        dye_names = [Dye.fromDict(d).name for d in cfg.get_defined_dyes()]
        with QSignalBlocker(self.cb_dye):
            self.cb_dye.clear()
            self.cb_dye.addItems(dye_names)
            # Guard if previously selected dye is deleted in Dye Manager, default to 1st item
            if self.dye.name in dye_names:
                self.cb_dye.setCurrentText(self.dye.name)
            else:
                self.dye_name = dye_names[0]
                self.cb_dye.setCurrentText(self.dye_name)

    def open_dye_manager(self):
        e = DyeManager(parent=self)
        e.finished.connect(lambda: self.refresh_dyes())
        e.exec()

    @pyqtSlot(str)
    def display_units_changed(self, value: str):
        cfg.set_spectrometer_display_unit(value)
        self.spectrometer_display_unit_changed.emit()

    def test_spectrometer(self):
        # Use whatever dye is currently selected
        dye = Dye.fromConfig(name=self.cb_dye.currentText())
        TestSpectrometer(spectrometer=self.spec, dye=dye, parent=self).exec()

    def accept(self):
        # Notify parent of dye change
        self.dye_changed.emit(self.cb_dye.currentText())
        # Update chosen dye in config
        cfg.set_defined_dye(self.cb_dye.currentText())

        super().accept()
