import copy
import os
import accupatt.config as cfg
from accupatt.models.passData import Pass
from PyQt6 import uic
from PyQt6.QtCore import (
    QAbstractTableModel,
    QModelIndex,
    Qt,
    QVariant,
    pyqtSignal,
    pyqtSlot,
)
from PyQt6.QtWidgets import QComboBox, QMessageBox, QStyledItemDelegate, QTableView

from accupatt.models.seriesData import SeriesData

Ui_Form, baseclass = uic.loadUiType(
    os.path.join(os.getcwd(), "resources", "passManager.ui")
)


class PassManager(baseclass):
    def __init__(self, seriesData: SeriesData = None, filler_mode=False, parent=None):
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

        if filler_mode:
            hidden_rows = [1, 2, 3, 4, 6, 8, 12, 14]
            for row in hidden_rows:
                self.tv.hideRow(row)
            self.resize(700, 400)

    def newPass(self):
        self.tm.addPass()

    def deletePass(self):
        col = self.ui.tableView.selectedIndexes()[0].column()
        p: Pass = self.tm.pass_list[col]
        if p.string.has_data() or p.cards.has_data():
            msg = QMessageBox.question(
                self,
                "Are You Sure?",
                f"{p.name} constains aquired data which will be permanently erased.",
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
        # Update default if requested
        if self.ui.checkBoxUpdateDefaultNumberOfPasses.isChecked():
            cfg.set_number_of_passes(len(self.tm.pass_list))
        # Notify Requestor
        super().accept()


class ComboBoxDelegate(QStyledItemDelegate):
    def __init__(self, owner, items):
        QStyledItemDelegate.__init__(self, owner)
        self.items = items

    def createEditor(self, widget, option, index):
        editor = QComboBox(widget)
        editor.addItems(self.items)
        editor.setAutoFillBackground(True)
        # editor.setEditable(True)
        return editor

    def setEditorData(self, editor: QComboBox, index):
        value = index.model().data(index, Qt.ItemDataRole.EditRole)
        if value:
            editor.setCurrentText(value)

    def setModelData(self, comboBox, model, index):
        model.setData(index, comboBox.currentText(), Qt.ItemDataRole.EditRole)

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)


class PassTable(QAbstractTableModel):
    def __init__(self, pass_list, parent=None, *args):
        super(PassTable, self).__init__()
        self.headers = [
            "Name",
            "String Data",
            "String Include",
            "Card Data",
            "Card Include",
            "Ground Speed",
            "Units",
            "Spray Height",
            "Units",
            "Pass Heading",
            "Wind Direction",
            "Wind Speed",
            "Units",
            "Temperature",
            "Units",
            "Humidity",
        ]
        self.pass_list = None
        if pass_list is not None:
            self.beginResetModel()
            self.pass_list: list[Pass] = pass_list
            self.endResetModel()

    def rowCount(self, parent = QModelIndex()) -> int:
        return len(self.headers)

    def columnCount(self, parent = QModelIndex()) -> int:
        return len(self.pass_list)

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if (
            role == Qt.ItemDataRole.DisplayRole
            and orientation == Qt.Orientation.Vertical
        ):
            return QVariant(self.headers[section])
        return QVariant()

    def data(self, index, role):
        if role == Qt.ItemDataRole.TextAlignmentRole:
            return Qt.AlignmentFlag.AlignCenter.value
        row = index.row()
        col = index.column()
        p: Pass = self.pass_list[col]
        if row == 0:
            if role == Qt.ItemDataRole.DisplayRole:
                return p.name
            elif role == Qt.ItemDataRole.EditRole:
                return p.name
        elif row == 1:
            if role == Qt.ItemDataRole.CheckStateRole:
                return (
                    Qt.CheckState.Checked
                    if p.string.has_data()
                    else Qt.CheckState.Unchecked
                )
            elif role == Qt.ItemDataRole.DisplayRole:
                return "Yes" if p.string.has_data() else "No"
        elif row == 2:
            if role == Qt.ItemDataRole.CheckStateRole:
                return (
                    Qt.CheckState.Checked
                    if p.string.include_in_composite
                    else Qt.CheckState.Unchecked
                )
            elif role == Qt.ItemDataRole.DisplayRole:
                return "Yes" if p.string.include_in_composite else "No"
            elif role == Qt.ItemDataRole.EditRole:
                return p.string.include_in_composite
        elif row == 3:
            if role == Qt.ItemDataRole.CheckStateRole:
                return (
                    Qt.CheckState.Checked
                    if p.cards.has_data()
                    else Qt.CheckState.Unchecked
                )
            elif role == Qt.ItemDataRole.DisplayRole:
                return "Yes" if p.cards.has_data() else "No"
        elif row == 4:
            if role == Qt.ItemDataRole.CheckStateRole:
                return (
                    Qt.CheckState.Checked
                    if p.cards.include_in_composite
                    else Qt.CheckState.Unchecked
                )
            elif role == Qt.ItemDataRole.DisplayRole:
                return "Yes" if p.cards.include_in_composite else "No"
            elif role == Qt.ItemDataRole.EditRole:
                return p.cards.include_in_composite
        elif row == 5:
            if role == Qt.ItemDataRole.DisplayRole or role == Qt.ItemDataRole.EditRole:
                return p.get_ground_speed()[2]
        elif row == 6:
            if role == Qt.ItemDataRole.DisplayRole or role == Qt.ItemDataRole.EditRole:
                return p.get_ground_speed()[1]
        elif row == 7:
            if role == Qt.ItemDataRole.DisplayRole or role == Qt.ItemDataRole.EditRole:
                return p.get_spray_height()[2]
        elif row == 8:
            if role == Qt.ItemDataRole.DisplayRole or role == Qt.ItemDataRole.EditRole:
                return p.get_spray_height()[1]
        elif row == 9:
            if role == Qt.ItemDataRole.DisplayRole or role == Qt.ItemDataRole.EditRole:
                return p.get_pass_heading()[2]
        elif row == 10:
            if role == Qt.ItemDataRole.DisplayRole or role == Qt.ItemDataRole.EditRole:
                return p.get_wind_direction()[2]
        elif row == 11:
            if role == Qt.ItemDataRole.DisplayRole or role == Qt.ItemDataRole.EditRole:
                return p.get_wind_speed()[2]
        elif row == 12:
            if role == Qt.ItemDataRole.DisplayRole or role == Qt.ItemDataRole.EditRole:
                return p.get_wind_speed()[1]
        elif row == 13:
            if role == Qt.ItemDataRole.DisplayRole or role == Qt.ItemDataRole.EditRole:
                return p.get_temperature()[2]
        elif row == 14:
            if role == Qt.ItemDataRole.DisplayRole or role == Qt.ItemDataRole.EditRole:
                return p.get_temperature()[1]
        elif row == 15:
            if role == Qt.ItemDataRole.DisplayRole or role == Qt.ItemDataRole.EditRole:
                return p.get_humidity()[2]
        else:
            return QVariant()

    def setData(self, index, value, role=Qt.ItemDataRole.EditRole) -> bool:
        if value is None:
            return False
        row = index.row()
        col = index.column()
        p: Pass = self.pass_list[col]
        if row == 0:
            p.name = value
        elif row == 1:
            pass
        elif row == 2:
            p.string.include_in_composite = (
                Qt.CheckState(value) == Qt.CheckState.Checked
            )
        elif row == 3:
            pass
        elif row == 4:
            p.cards.include_in_composite = Qt.CheckState(value) == Qt.CheckState.Checked
        elif row == 5:
            p.set_ground_speed(value)
        elif row == 6:
            p.ground_speed_units = value
        elif row == 7:
            p.set_spray_height(value)
        elif row == 8:
            p.spray_height_units = value
        elif row == 9:
            p.set_pass_heading(value)
            for c in range(col+1,self.columnCount()):
                self.pass_list[c].set_pass_heading(value)
        elif row == 10:
            p.set_wind_direction(value)
        elif row == 11:
            p.set_wind_speed(value)
        elif row == 12:
            p.wind_speed_units = value
        elif row == 13:
            p.set_temperature(value)
            for c in range(col+1,self.columnCount()):
                self.pass_list[c].set_temperature(value)
        elif row == 14:
            p.temperature_units = value
        elif row == 15:
            p.set_humidity(value)
            for c in range(col+1,self.columnCount()):
                self.pass_list[c].set_humidity(value)
        else:
            return False
        self.dataChanged.emit(index, index)
        return True

    def addPass(self):
        # Pass number initialized as length of list
        nextIndex = len(self.pass_list)
        # Double check; if pass num already exists, increment it
        # This only would apply if an earlier pass had been deleted
        p_nums = []
        for p in self.pass_list:
            p_nums.append(p.number)
        if p_nums:
            if nextIndex <= max(p_nums):
                nextIndex = max(p_nums) + 1
        else:
            nextIndex = 1
        self.beginInsertColumns(QModelIndex(), len(self.pass_list), len(self.pass_list))
        # Create pass and add it to listwidget
        self.pass_list.append(Pass(number=nextIndex))
        self.endInsertColumns()

    def removePass(self, selectedIndexes):
        col = selectedIndexes[0].column()
        self.beginRemoveColumns(QModelIndex(), col, col)
        self.pass_list.pop(col)
        self.endRemoveColumns()

    def shiftRowsUp(self, selectedColumns):
        sort_list = []
        for index in selectedColumns:
            col = index.column()
            sort_list.append(col)
            # ensure shift is not out of list bounds
            if col - 1 < 0:
                return
        sort_list.sort()
        # Notify model of the move in progress
        self.beginMoveColumns(
            QModelIndex(),
            sort_list[0],
            sort_list[len(sort_list) - 1],
            QModelIndex(),
            sort_list[0] - 1,
        )
        # Make the move on the model data
        for col in sort_list:
            self.pass_list.insert(col - 1, self.pass_list.pop(col))
        # Notify model move is complete
        self.endMoveColumns()

    def shiftRowsDown(self, selectedColumns):
        sort_list = []
        for index in selectedColumns:
            col = index.column()
            sort_list.append(col)
            # ensure shift is not out of list bounds
            if col + 1 >= len(self.pass_list):
                return
        sort_list.sort()
        # QAbstractItemModel quirk, cant have new index inside moving index
        # Notify model of the move in progress
        self.beginMoveColumns(
            QModelIndex(),
            sort_list[0],
            sort_list[len(sort_list) - 1],
            QModelIndex(),
            sort_list[len(sort_list) - 1] + 1 + 1,
        )
        # Make the move on the model data
        sort_list.sort(reverse=True)
        for col in sort_list:
            self.pass_list.insert(col + 1, self.pass_list.pop(col))
        # Notify model move is complete
        self.endMoveColumns()

    def flags(self, index):
        if not index.isValid():
            return None
        row = index.row()
        col = index.column()
        p: Pass = self.pass_list[col]
        if row == 1:
            if p.string.has_data():
                return Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable
            else:
                return Qt.ItemFlag.ItemIsSelectable
        elif row == 2:
            if p.string.has_data():
                return (
                    Qt.ItemFlag.ItemIsEnabled
                    | Qt.ItemFlag.ItemIsSelectable
                    | Qt.ItemFlag.ItemIsUserCheckable
                )
            else:
                return Qt.ItemFlag.ItemIsSelectable
        elif row == 3:
            if p.cards.has_data():
                return Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable
            else:
                return Qt.ItemFlag.ItemIsSelectable
        elif row == 4:
            if p.cards.has_data():
                return (
                    Qt.ItemFlag.ItemIsEnabled
                    | Qt.ItemFlag.ItemIsSelectable
                    | Qt.ItemFlag.ItemIsUserCheckable
                )
            else:
                return Qt.ItemFlag.ItemIsSelectable
        else:
            return (
                Qt.ItemFlag.ItemIsEnabled
                | Qt.ItemFlag.ItemIsSelectable
                | Qt.ItemFlag.ItemIsEditable
            )
