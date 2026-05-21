import accupatt.config as cfg
from accupatt.models.passData import Pass
from PyQt6.QtCore import QAbstractTableModel, QModelIndex, Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QComboBox, QStyledItemDelegate

# Rows hidden in filler mode (unit rows + string/card rows)
FILLER_HIDDEN_ROWS = [1, 2, 3, 4, 6, 8, 12, 14]

# Matplotlib tab10 default color cycle
_MPL_COLORS = [
    '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
    '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf',
]

def _contrasting_text(hex_color: str) -> QColor:
    r = int(hex_color[1:3], 16)
    g = int(hex_color[3:5], 16)
    b = int(hex_color[5:7], 16)
    luminance = (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255
    return QColor('white') if luminance < 0.5 else QColor('black')


class ComboBoxDelegate(QStyledItemDelegate):
    def __init__(self, owner, items):
        QStyledItemDelegate.__init__(self, owner)
        self.items = items

    def createEditor(self, widget, option, index):
        editor = QComboBox(widget)
        editor.addItems(self.items)
        editor.setAutoFillBackground(True)
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
    def __init__(self, pass_list, parent=None, filler_mode=False, *args):
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
        self.filler_mode = filler_mode
        self.pass_list = None
        if pass_list is not None:
            self.beginResetModel()
            self.pass_list: list[Pass] = pass_list
            self.endResetModel()

    def rowCount(self, parent=QModelIndex()) -> int:
        return len(self.headers)

    def columnCount(self, parent=QModelIndex()) -> int:
        return len(self.pass_list)

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if (
            role == Qt.ItemDataRole.DisplayRole
            and orientation == Qt.Orientation.Vertical
        ):
            return self.headers[section]
        return None

    def data(self, index, role):
        if role == Qt.ItemDataRole.TextAlignmentRole:
            return Qt.AlignmentFlag.AlignCenter.value
        row = index.row()
        col = index.column()
        if row == 0:
            color = _MPL_COLORS[col % len(_MPL_COLORS)]
            if role == Qt.ItemDataRole.BackgroundRole:
                return QColor(color)
            if role == Qt.ItemDataRole.ForegroundRole:
                return _contrasting_text(color)
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
            if role == Qt.ItemDataRole.DisplayRole:
                val = p.ground_speed_str
                return (val + " " + p.ground_speed_units) if (self.filler_mode and val) else val
            elif role == Qt.ItemDataRole.EditRole:
                return p.ground_speed_str
        elif row == 6:
            if role == Qt.ItemDataRole.DisplayRole or role == Qt.ItemDataRole.EditRole:
                return p.ground_speed_units
        elif row == 7:
            if role == Qt.ItemDataRole.DisplayRole:
                val = p.spray_height_str
                return (val + " " + p.spray_height_units) if (self.filler_mode and val) else val
            elif role == Qt.ItemDataRole.EditRole:
                return p.spray_height_str
        elif row == 8:
            if role == Qt.ItemDataRole.DisplayRole or role == Qt.ItemDataRole.EditRole:
                return p.spray_height_units
        elif row == 9:
            if role == Qt.ItemDataRole.DisplayRole:
                val = p.pass_heading_str
                return (val + "°") if val else val
            elif role == Qt.ItemDataRole.EditRole:
                return p.pass_heading_str
        elif row == 10:
            if role == Qt.ItemDataRole.DisplayRole:
                val = p.wind_direction_str
                return (val + "°") if val else val
            elif role == Qt.ItemDataRole.EditRole:
                return p.wind_direction_str
        elif row == 11:
            if role == Qt.ItemDataRole.DisplayRole:
                val = p.wind_speed_str
                return (val + " " + p.wind_speed_units) if (self.filler_mode and val) else val
            elif role == Qt.ItemDataRole.EditRole:
                return p.wind_speed_str
        elif row == 12:
            if role == Qt.ItemDataRole.DisplayRole or role == Qt.ItemDataRole.EditRole:
                return p.wind_speed_units
        elif row == 13:
            if role == Qt.ItemDataRole.DisplayRole:
                val = p.temperature_str
                return (val + " " + p.temperature_units) if (self.filler_mode and val) else val
            elif role == Qt.ItemDataRole.EditRole:
                return p.temperature_str
        elif row == 14:
            if role == Qt.ItemDataRole.DisplayRole or role == Qt.ItemDataRole.EditRole:
                return p.temperature_units
        elif row == 15:
            if role == Qt.ItemDataRole.DisplayRole:
                val = p.humidity_str
                return (val + " %") if val else val
            elif role == Qt.ItemDataRole.EditRole:
                return p.humidity_str
        else:
            return None

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
            for c in range(col + 1, self.columnCount()):
                self.pass_list[c].set_pass_heading(value)
        elif row == 10:
            p.set_wind_direction(value)
        elif row == 11:
            p.set_wind_speed(value)
        elif row == 12:
            p.wind_speed_units = value
        elif row == 13:
            p.set_temperature(value)
            for c in range(col + 1, self.columnCount()):
                self.pass_list[c].set_temperature(value)
        elif row == 14:
            p.temperature_units = value
        elif row == 15:
            p.set_humidity(value)
            for c in range(col + 1, self.columnCount()):
                self.pass_list[c].set_humidity(value)
        else:
            return False
        self.dataChanged.emit(index, index)
        return True

    def addPass(self):
        nextIndex = len(self.pass_list)
        p_nums = []
        for p in self.pass_list:
            p_nums.append(p.number)
        if p_nums:
            if nextIndex <= max(p_nums):
                nextIndex = max(p_nums) + 1
        else:
            nextIndex = 1
        self.beginInsertColumns(QModelIndex(), len(self.pass_list), len(self.pass_list))
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
            if col - 1 < 0:
                return
        sort_list.sort()
        self.beginMoveColumns(
            QModelIndex(),
            sort_list[0],
            sort_list[len(sort_list) - 1],
            QModelIndex(),
            sort_list[0] - 1,
        )
        for col in sort_list:
            self.pass_list.insert(col - 1, self.pass_list.pop(col))
        self.endMoveColumns()

    def shiftRowsDown(self, selectedColumns):
        sort_list = []
        for index in selectedColumns:
            col = index.column()
            sort_list.append(col)
            if col + 1 >= len(self.pass_list):
                return
        sort_list.sort()
        self.beginMoveColumns(
            QModelIndex(),
            sort_list[0],
            sort_list[len(sort_list) - 1],
            QModelIndex(),
            sort_list[len(sort_list) - 1] + 1 + 1,
        )
        sort_list.sort(reverse=True)
        for col in sort_list:
            self.pass_list.insert(col + 1, self.pass_list.pop(col))
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
