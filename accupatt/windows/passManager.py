import copy
import os
import accupatt.config as cfg
from accupatt.models.passData import Pass
from PyQt6 import uic
from PyQt6.QtCore import QAbstractTableModel, QModelIndex, Qt, QVariant, pyqtSignal
from PyQt6.QtWidgets import QComboBox, QMessageBox, QStyledItemDelegate, QTableView

Ui_Form, baseclass = uic.loadUiType(
    os.path.join(os.getcwd(), "resources", "passManager.ui")
)


class PassManager(baseclass):

    pass_list_updated = pyqtSignal(list)

    def __init__(self, passes=None, parent=None):
        super().__init__(parent=parent)
        self.ui = Ui_Form()
        self.ui.setupUi(self)

        self.tm = PassTable(copy.copy(passes), self)
        self.tv: QTableView = self.ui.tableView
        self.tv.setModel(self.tm)
        self.tv.setItemDelegateForColumn(
            6, ComboBoxDelegate(self, cfg.UNITS_GROUND_SPEED)
        )
        self.tv.setItemDelegateForColumn(
            8, ComboBoxDelegate(self, cfg.UNITS_SPRAY_HEIGHT)
        )
        self.tv.setItemDelegateForColumn(
            12, ComboBoxDelegate(self, cfg.UNITS_WIND_SPEED)
        )
        self.tv.setItemDelegateForColumn(
            14, ComboBoxDelegate(self, cfg.UNITS_TEMPERATURE)
        )

        self.ui.button_new_pass.clicked.connect(self.newPass)
        self.ui.button_delete_pass.clicked.connect(self.deletePass)

        self.show()

    def newPass(self):
        self.tm.addPass()

    def deletePass(self):
        row = self.ui.tableView.selectedIndexes()[0].row()
        p: Pass = self.tm.pass_list[row]
        if p.has_string_data() or p.has_card_data():
            msg = QMessageBox.question(
                self,
                "Are You Sure?",
                f"{p.name} constains aquired data which will be permanently erased.",
            )
            if msg == QMessageBox.StandardButton.No:
                return
        self.tm.removePass(self.ui.tableView.selectedIndexes())

    def accept(self):
        self.pass_list_updated.emit(copy.copy(self.tm.pass_list))
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
            self.pass_list = pass_list
            self.endResetModel()

    def rowCount(self, parent: QModelIndex()) -> int:
        return len(self.pass_list)

    def columnCount(self, parent: QModelIndex()) -> int:
        return len(self.headers)

    def headerData(self, column, orientation, role=Qt.ItemDataRole.DisplayRole):
        if (
            role == Qt.ItemDataRole.DisplayRole
            and orientation == Qt.Orientation.Horizontal
        ):
            return QVariant(self.headers[column])
        return QVariant()

    def data(self, index, role):
        if role == Qt.ItemDataRole.TextAlignmentRole:
            return Qt.AlignmentFlag.AlignCenter
        row = index.row()
        col = index.column()
        p: Pass = self.pass_list[row]
        if col == 0:
            if role == Qt.ItemDataRole.DisplayRole:
                return p.name
            elif role == Qt.ItemDataRole.EditRole:
                return p.name
        elif col == 1:
            if role == Qt.ItemDataRole.CheckStateRole:
                return (
                    Qt.CheckState.Checked
                    if p.has_string_data()
                    else Qt.CheckState.Unchecked
                )
            elif role == Qt.ItemDataRole.DisplayRole:
                return "Yes" if p.has_string_data() else "No"
        elif col == 2:
            if role == Qt.ItemDataRole.CheckStateRole:
                return (
                    Qt.CheckState.Checked
                    if p.string_include_in_composite
                    else Qt.CheckState.Unchecked
                )
            elif role == Qt.ItemDataRole.DisplayRole:
                return "Yes" if p.string_include_in_composite else "No"
            elif role == Qt.ItemDataRole.EditRole:
                return p.string_include_in_composite
        elif col == 3:
            if role == Qt.ItemDataRole.CheckStateRole:
                return (
                    Qt.CheckState.Checked
                    if p.has_card_data()
                    else Qt.CheckState.Unchecked
                )
            elif role == Qt.ItemDataRole.DisplayRole:
                return "Yes" if p.has_card_data() else "No"
        elif col == 4:
            if role == Qt.ItemDataRole.CheckStateRole:
                return (
                    Qt.CheckState.Checked
                    if p.cards_include_in_composite
                    else Qt.CheckState.Unchecked
                )
            elif role == Qt.ItemDataRole.DisplayRole:
                return "Yes" if p.cards_include_in_composite else "No"
            elif role == Qt.ItemDataRole.EditRole:
                return p.cards_include_in_composite
        elif col == 5:
            if role == Qt.ItemDataRole.DisplayRole or role == Qt.ItemDataRole.EditRole:
                return f"{p.ground_speed:g}"
        elif col == 6:
            if role == Qt.ItemDataRole.DisplayRole or role == Qt.ItemDataRole.EditRole:
                return p.ground_speed_units
        elif col == 7:
            if role == Qt.ItemDataRole.DisplayRole or role == Qt.ItemDataRole.EditRole:
                return f"{p.spray_height:g}"
        elif col == 8:
            if role == Qt.ItemDataRole.DisplayRole or role == Qt.ItemDataRole.EditRole:
                return p.spray_height_units
        elif col == 9:
            if role == Qt.ItemDataRole.DisplayRole or role == Qt.ItemDataRole.EditRole:
                return f"{p.pass_heading:g}"
        elif col == 10:
            if role == Qt.ItemDataRole.DisplayRole or role == Qt.ItemDataRole.EditRole:
                return f"{p.wind_direction:g}"
        elif col == 11:
            if role == Qt.ItemDataRole.DisplayRole or role == Qt.ItemDataRole.EditRole:
                return f"{p.wind_speed:g}"
        elif col == 12:
            if role == Qt.ItemDataRole.DisplayRole or role == Qt.ItemDataRole.EditRole:
                return p.wind_speed_units
        elif col == 13:
            if role == Qt.ItemDataRole.DisplayRole or role == Qt.ItemDataRole.EditRole:
                return f"{p.temperature:g}"
        elif col == 14:
            if role == Qt.ItemDataRole.DisplayRole or role == Qt.ItemDataRole.EditRole:
                return p.temperature_units
        elif col == 15:
            if role == Qt.ItemDataRole.DisplayRole or role == Qt.ItemDataRole.EditRole:
                return p.humidity
        else:
            return QVariant()

    def setData(self, index, value, role=Qt.ItemDataRole.EditRole) -> bool:
        if value is None:
            return False
        row = index.row()
        col = index.column()
        p: Pass = self.pass_list[row]
        if col == 0:
            p.name = value
        elif col == 1:
            pass
        elif col == 2:
            p.string_include_in_composite = (
                Qt.CheckState(value) == Qt.CheckState.Checked
            )
        elif col == 3:
            pass
        elif col == 4:
            p.cards_include_in_composite = Qt.CheckState(value) == Qt.CheckState.Checked
        elif col == 5:
            p.set_ground_speed(value)
        elif col == 6:
            p.ground_speed_units = value
        elif col == 7:
            p.set_spray_height(value)
        elif col == 8:
            p.spray_height_units = value
        elif col == 9:
            p.set_pass_heading(value)
        elif col == 10:
            p.set_wind_direction(value)
        elif col == 11:
            p.set_wind_speed(value)
        elif col == 12:
            p.wind_speed_units = value
        elif col == 13:
            p.set_temperature(value)
        elif col == 14:
            p.temperature_units = value
        elif col == 15:
            p.set_humidity(value)
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
        self.beginInsertRows(QModelIndex(), len(self.pass_list), len(self.pass_list))
        # Create pass and add it to listwidget
        self.pass_list.append(Pass(number=nextIndex))
        self.endInsertRows()

    def removePass(self, selectedIndexes):
        row = selectedIndexes[0].row()
        self.beginRemoveRows(QModelIndex(), row, row)
        self.pass_list.pop(row)
        self.endRemoveRows()

    def flags(self, index):
        if not index.isValid():
            return None
        row = index.row()
        col = index.column()
        p: Pass = self.pass_list[row]
        if col == 1:
            if p.has_string_data():
                return Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable
            else:
                return Qt.ItemFlag.ItemIsSelectable
        elif col == 2:
            if p.has_string_data():
                return (
                    Qt.ItemFlag.ItemIsEnabled
                    | Qt.ItemFlag.ItemIsSelectable
                    | Qt.ItemFlag.ItemIsUserCheckable
                )
            else:
                return Qt.ItemFlag.ItemIsSelectable
        elif col == 3:
            if p.has_card_data():
                return Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable
            else:
                return Qt.ItemFlag.ItemIsSelectable
        elif col == 4:
            if p.has_card_data():
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
