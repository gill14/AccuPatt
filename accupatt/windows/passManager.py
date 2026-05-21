import os
import accupatt.config as cfg
from PyQt6 import uic
from PyQt6.QtCore import pyqtSlot
from PyQt6.QtWidgets import QMessageBox, QTableView

from accupatt.models.passData import Pass
from accupatt.models.passTable import PassTable, ComboBoxDelegate
from accupatt.models.seriesData import SeriesData

Ui_Form, baseclass = uic.loadUiType(
    os.path.join(os.getcwd(), "resources", "passManager.ui")
)


class PassManager(baseclass):
    def __init__(self, seriesData: SeriesData = None, parent=None):
        super().__init__(parent=parent)
        self.ui = Ui_Form()
        self.ui.setupUi(self)

        self.tm = PassTable(seriesData.passes, self)
        self.tv: QTableView = self.ui.tableView
        self.tv.setModel(self.tm)
        self.tv.setItemDelegateForRow(6, ComboBoxDelegate(self, cfg.UNITS_GROUND_SPEED))
        self.tv.setItemDelegateForRow(8, ComboBoxDelegate(self, cfg.UNITS_SPRAY_HEIGHT))
        self.tv.setItemDelegateForRow(12, ComboBoxDelegate(self, cfg.UNITS_WIND_SPEED))
        self.tv.setItemDelegateForRow(14, ComboBoxDelegate(self, cfg.UNITS_TEMPERATURE))
        self.tv.horizontalHeader().setVisible(False)
        self.tv.selectionModel().selectionChanged.connect(self.selection_changed)

        self.ui.button_new_pass.clicked.connect(self.newPass)
        self.ui.button_delete_pass.clicked.connect(self.deletePass)
        self.ui.button_shift_up.clicked.connect(self.shift_up)
        self.ui.button_shift_down.clicked.connect(self.shift_down)

        self.show()

    def newPass(self):
        self.tm.addPass()

    def deletePass(self):
        col = self.ui.tableView.selectedIndexes()[0].column()
        p: Pass = self.tm.pass_list[col]
        if p.string.has_data() or p.cards.has_data():
            msg = QMessageBox.question(
                self,
                "Are You Sure?",
                f"{p.name} contains acquired data which will be permanently erased.",
            )
            if msg == QMessageBox.StandardButton.No:
                return
        self.tm.removePass(self.ui.tableView.selectedIndexes())

    @pyqtSlot()
    def selection_changed(self):
        hasSelection = bool(self.tv.selectionModel().selectedColumns())
        self.ui.button_delete_pass.setEnabled(hasSelection)
        self.ui.button_shift_up.setEnabled(hasSelection)
        self.ui.button_shift_down.setEnabled(hasSelection)

    @pyqtSlot()
    def shift_up(self):
        self.tm.shiftRowsUp(self.tv.selectionModel().selectedColumns())

    @pyqtSlot()
    def shift_down(self):
        self.tm.shiftRowsDown(self.tv.selectionModel().selectedColumns())

    def accept(self):
        super().accept()


