import os

import accupatt.config as cfg
from accupatt.models.sprayCard import SprayCard
from PyQt6 import uic
from PyQt6.QtCore import pyqtSlot, pyqtSignal
from PyQt6.QtWidgets import QComboBox, QLineEdit, QMessageBox, QRadioButton

Ui_Form, baseclass = uic.loadUiType(
    os.path.join(os.getcwd(), "resources", "createDefinedSet.ui")
)


class CreateDefinedSet(baseclass):

    setConfirmed = pyqtSignal(list)

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.ui = Ui_Form()
        self.ui.setupUi(self)

        self.initial = 0
        self.step = 1
        self.quantity = 1
        self.final = 1

        self.initial_le: QLineEdit = self.ui.lineEditInitial
        self.initial_le.setText(str(self.initial))
        self.initial_le.textChanged.connect(self.process_location)

        self.quantity_le: QLineEdit = self.ui.lineEditQuantity
        self.quantity_le.setText(str(self.quantity))
        self.quantity_le.textChanged.connect(self.process_location)

        self.step_rb: QRadioButton = self.ui.radioButtonStep
        self.step_rb.toggled[bool].connect(self.step_rb_toggled)

        self.step_le: QLineEdit = self.ui.lineEditStep
        self.step_le.setText(str(self.step))
        self.step_le.textChanged.connect(self.process_location)

        self.final_rb: QRadioButton = self.ui.radioButtonFinal
        self.final_rb.toggled[bool].connect(self.final_rb_toggled)

        self.final_le: QLineEdit = self.ui.lineEditFinal
        self.final_le.setText(str(self.final))
        self.final_le.textChanged.connect(self.process_location)

        self.units_cb: QComboBox = self.ui.comboBoxUnits
        self.units_cb.addItems(cfg.UNITS_LENGTH_LARGE)
        self.units_cb.setCurrentText(cfg.UNIT_FT)

        self.thresh_cb: QComboBox = self.ui.comboBoxThresholdType
        self.thresh_cb.addItems(cfg.THRESHOLD_TYPES)
        self.thresh_cb.setCurrentText(cfg.THRESHOLD_TYPE__DEFAULT)

        self.show()

        self.step_rb.toggle()
        self.step_rb_toggled(True)

    @pyqtSlot(bool)
    def step_rb_toggled(self, checked):
        self.final_le.setDisabled(checked)
        self.step_le.setDisabled(not checked)
        self.process_location()

    @pyqtSlot(bool)
    def final_rb_toggled(self, checked):
        self.step_le.setDisabled(checked)
        self.final_le.setDisabled(not checked)
        self.process_location()

    def process_location(self) -> bool:
        try:
            self.initial = float(self.initial_le.text())
        except ValueError:
            return False
        try:
            self.quantity = int(self.quantity_le.text())
        except ValueError:
            return False
        if self.step_rb.isChecked():
            try:
                self.step = float(self.step_le.text())
            except ValueError:
                return False
            self.final = self.initial + (self.step * (self.quantity - 1))
            self.final_le.setText(str(self.final))
            return True
        else:
            try:
                self.final = float(self.final_le.text())
            except ValueError:
                return False
            try:
                self.step = (self.final - self.initial) / (self.quantity - 1)
            except ZeroDivisionError:
                return False
            self.step_le.setText(str(self.step))
            return True

    def accept(self):
        if not self.process_location():
            msg = QMessageBox.warning(
                self, "Invalid Input", "Cannot create a card list from given inputs."
            )
            if msg == QMessageBox.StandardButton.Ok:
                return

        cards = []
        for i in range(self.quantity):
            card = SprayCard(name=f"Card {i+1}")
            card.location = self.initial + (self.step * i)
            card.location_units = self.units_cb.currentText()
            card.threshold_type = self.thresh_cb.currentText()
            cards.append(card)
        self.setConfirmed.emit(cards)

        super().accept()
