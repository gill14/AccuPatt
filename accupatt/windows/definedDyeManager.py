import json
import os

from PyQt6 import uic
from PyQt6.QtCore import (
    QAbstractListModel,
    QModelIndex,
    Qt,
    pyqtSlot,
    QItemSelectionModel,
)
from PyQt6.QtGui import QIntValidator
from PyQt6.QtWidgets import QLineEdit, QMessageBox, QListView

from accupatt.models.dye import Dye
import accupatt.config as cfg

Ui_Form, baseclass = uic.loadUiType(
    os.path.join(os.getcwd(), "resources", "definedDyeManager.ui")
)


class DyeManager(baseclass):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.ui = Ui_Form()
        self.ui.setupUi(self)

        self.lv: QListView = self.ui.listView
        self.lm = DyeListModel([Dye.fromDict(d) for d in cfg.get_defined_dyes()])
        self.lv.setModel(self.lm)
        self.lv.selectionModel().currentChanged[QModelIndex, QModelIndex].connect(
            self.current_dye_changed
        )

        self.ui.buttonAdd.clicked.connect(self.add_dye)
        self.ui.buttonRemove.clicked.connect(self.remove_dye)

        self.le_ex: QLineEdit = self.ui.lineEditExcitation
        self.le_ex.setValidator(QIntValidator(self.le_ex))
        self.le_em: QLineEdit = self.ui.lineEditEmission
        self.le_em.setValidator(QIntValidator(self.le_em))
        self.le_it: QLineEdit = self.ui.lineEditIntegrationTime
        self.le_it.setValidator(QIntValidator(self.le_it))
        self.le_bx: QLineEdit = self.ui.lineEditBoxcarWidth
        self.le_bx.setValidator(QIntValidator(self.le_bx))

        self.show()

        self.lv.setCurrentIndex(self.lm.index(0, 0))

    @pyqtSlot()
    def add_dye(self):
        self.lm.addDye()
        self.lv.selectionModel().setCurrentIndex(
            self.lm.index(self.lm.rowCount() - 1, 0),
            QItemSelectionModel.SelectionFlag.ClearAndSelect,
        )

    @pyqtSlot()
    def remove_dye(self):
        selected_dye = self.lv.selectionModel().selectedIndexes()[0]
        if selected_dye.row() < 4:
            msg = QMessageBox.information(
                self,
                "Unable to Remove Default Dye",
                "This is a default Dye, and cannot be removed.",
            )
            if msg == QMessageBox.StandardButton.Ok:
                return
        msg = QMessageBox.question(
            self,
            "Are You Sure?",
            "This Dye will be removed and unrecoverable. Continue?",
        )
        if msg == QMessageBox.StandardButton.No:
            return
        self.lm.removeDye(selected_dye)

    @pyqtSlot(QModelIndex, QModelIndex)
    def current_dye_changed(self, current: QModelIndex, previous: QModelIndex):
        # Populate lineEdits
        dye = self.lm.dyes[current.row()]
        self.le_ex.setText(str(dye.wavelength_excitation))
        self.le_ex.editingFinished.connect(self.excitation_changed)
        self.le_em.setText(str(dye.wavelength_emission))
        self.le_em.editingFinished.connect(self.emission_changed)
        self.le_it.setText(str(dye.integration_time_milliseconds))
        self.le_it.editingFinished.connect(self.integration_time_changed)
        self.le_bx.setText(str(dye.boxcar_width))
        self.le_bx.editingFinished.connect(self.boxcar_width_changed)

    @pyqtSlot()
    def excitation_changed(self):
        self.lm.dyes[self.lv.currentIndex().row()].wavelength_excitation = int(
            self.le_ex.text()
        )

    @pyqtSlot()
    def emission_changed(self):
        self.lm.dyes[self.lv.currentIndex().row()].wavelength_emission = int(
            self.le_em.text()
        )

    @pyqtSlot()
    def integration_time_changed(self):
        self.lm.dyes[self.lv.currentIndex().row()].integration_time_milliseconds = int(
            self.le_it.text()
        )

    @pyqtSlot()
    def boxcar_width_changed(self):
        self.lm.dyes[self.lv.currentIndex().row()].boxcar_width = int(self.le_bx.text())

    def accept(self):
        # Check all inputs
        # for dye in self.lm.dyes:

        # Update saved Defined Dyes in Settings
        cfg.set_defined_dyes(json.dumps([dye.toDict() for dye in self.lm.dyes]))
        super().accept()


class DyeListModel(QAbstractListModel):
    def __init__(self, dyes: list[Dye], parent=None):
        super(DyeListModel, self).__init__(parent)
        self.dyes = dyes

    def rowCount(self, parent=QModelIndex()) -> int:
        return len(self.dyes)

    def data(self, index, role):
        d = self.dyes[index.row()]
        if role == Qt.ItemDataRole.DisplayRole:
            return d.name

    def setData(self, index, value, role) -> bool:
        if index.row() < 4:
            return False
        d = self.dyes[index.row()]
        if role == Qt.ItemDataRole.EditRole:
            d.name = value
            self.dataChanged.emit(index, index)
            return True
        return False

    def addDye(self):
        self.beginInsertRows(QModelIndex(), self.rowCount(), self.rowCount())
        self.dyes.append(Dye("New Dye", 500, 500, 100))
        self.endInsertRows()

    def removeDye(self, selected_index: QModelIndex):
        row = selected_index.row()
        self.beginRemoveRows(QModelIndex(), row, row)
        self.dyes.pop(row)
        self.endRemoveRows()

    def flags(self, index):
        if not index.isValid():
            return None
        return (
            Qt.ItemFlag.ItemIsEnabled
            | Qt.ItemFlag.ItemIsSelectable
            | Qt.ItemFlag.ItemIsEditable
        )
