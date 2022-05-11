from numpy import TooHardError
import accupatt.config as cfg
from accupatt.models.sprayCard import SprayCard
from PyQt6.QtCore import (
    QAbstractTableModel,
    QModelIndex,
    Qt,
    QVariant,
    pyqtSignal,
)
from PyQt6.QtGui import (
    QBrush,
    QColor,
)
from PyQt6.QtWidgets import (
    QComboBox,
    QStyledItemDelegate,
)


class CardStatTableModel(QAbstractTableModel):

    valueChanged = pyqtSignal()

    def __init__(self, parent=None, *args):
        super(CardStatTableModel, self).__init__(parent)
        self.headers = [
            "Name",
            "In Composite",
            "Location",
            "Units",
            "Category",
            "Dv0.1",
            "Dv0.5",
            "Dv0.9",
            "RS",
            "Coverage",
            "Stains",
            "Stains/in\u00B2",
        ]
        self.card_list: list[SprayCard] = []

    def loadCards(self, card_list):
        self.beginResetModel()
        self.card_list = card_list
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()) -> int:
        return len(self.card_list)

    def columnCount(self, parent=QModelIndex()) -> int:
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
        card: SprayCard = self.card_list[index.row()]
        col = index.column()
        if col == 0:
            if role == Qt.ItemDataRole.DisplayRole:
                return card.name
            elif role == Qt.ItemDataRole.EditRole:
                return card.name
        elif col == 1:
            if role == Qt.ItemDataRole.CheckStateRole:
                return (
                    Qt.CheckState.Checked
                    if card.include_in_composite
                    else Qt.CheckState.Unchecked
                )
            elif role == Qt.ItemDataRole.DisplayRole:
                return "Yes" if card.include_in_composite else "No"
            elif role == Qt.ItemDataRole.EditRole:
                return card.include_in_composite
        elif col == 2:
            if role == Qt.ItemDataRole.DisplayRole:
                return card.location
            if role == Qt.ItemDataRole.EditRole:
                return card.location
        elif col == 3:
            if role == Qt.ItemDataRole.DisplayRole:
                return card.location_units
            elif role == Qt.ItemDataRole.EditRole:
                return cfg.UNITS_LENGTH_LARGE.index(card.location_units)
        elif col == 4:
            if role == Qt.ItemDataRole.DisplayRole:
                return card.stats.get_dsc()
            if role == Qt.ItemDataRole.BackgroundRole:
                hex_color = card.stats.get_dsc_color()
                qcolor = QColor(hex_color)
                qcolor.setAlpha(128)
                return QBrush(qcolor)
        elif col == 5:
            if role == Qt.ItemDataRole.DisplayRole:
                return card.stats.get_dv01(text=True)
            if role == Qt.ItemDataRole.BackgroundRole:
                hex_color = card.stats.get_dv01_color()
                qcolor = QColor(hex_color)
                qcolor.setAlpha(128)
                return QBrush(qcolor)
        elif col == 6:
            if role == Qt.ItemDataRole.DisplayRole:
                return card.stats.get_dv05(text=True)
            if role == Qt.ItemDataRole.BackgroundRole:
                hex_color = card.stats.get_dv05_color()
                qcolor = QColor(hex_color)
                qcolor.setAlpha(128)
                return QBrush(qcolor)
        elif col == 7:
            if role == Qt.ItemDataRole.DisplayRole:
                return card.stats.get_dv09(text=True)
            if role == Qt.ItemDataRole.BackgroundRole:
                hex_color = card.stats.get_dv09_color()
                qcolor = QColor(hex_color)
                qcolor.setAlpha(128)
                return QBrush(qcolor)
        elif col == 8:
            if role == Qt.ItemDataRole.DisplayRole:
                return card.stats.get_relative_span(text=True)
        elif col == 9:
            if role == Qt.ItemDataRole.DisplayRole:
                return card.stats.get_percent_coverage(text=True)
        elif col == 10:
            if role == Qt.ItemDataRole.DisplayRole:
                return card.stats.get_number_of_stains(text=True)
        elif col == 11:
            if role == Qt.ItemDataRole.DisplayRole:
                return card.stats.get_stains_per_in2(text=True)
        else:
            return QVariant()

    def setData(self, index, value, role=Qt.ItemDataRole.EditRole) -> bool:
        if value is None:
            return False
        card: SprayCard = self.card_list[index.row()]
        col = index.column()
        if col == 0:
            card.name = value
        elif col == 1:
            if card.has_image:
                card.include_in_composite = (
                    Qt.CheckState(value) == Qt.CheckState.Checked
                )
        elif col == 2:
            try:
                card.location = float(value)
            except ValueError:
                return False
        elif col == 3:
            card.location_units = cfg.UNITS_LENGTH_LARGE[value]
        else:
            return False
        self.dataChanged.emit(index, index)
        self.valueChanged.emit()
        return True

    def flags(self, index):
        if not index.isValid():
            return None
        col = index.column()
        if col == 1:
            return (
                Qt.ItemFlag.ItemIsEnabled
                | Qt.ItemFlag.ItemIsSelectable
                | Qt.ItemFlag.ItemIsUserCheckable
            )
        elif col == 0 or col == 2 or col == 3:
            return (
                Qt.ItemFlag.ItemIsEnabled
                | Qt.ItemFlag.ItemIsSelectable
                | Qt.ItemFlag.ItemIsEditable
            )
        else:
            return Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable


class ComboBoxDelegate(QStyledItemDelegate):
    def __init__(self, owner, itemList):
        QStyledItemDelegate.__init__(self, owner)
        self.itemList = itemList

    def createEditor(self, parent, option, index):
        editor = QComboBox(parent)
        editor.addItems(self.itemList)
        editor.setAutoFillBackground(True)
        return editor

    def setEditorData(self, comboBox, index):
        comboBox.setCurrentIndex(
            int(index.model().data(index, role=Qt.ItemDataRole.EditRole))
        )

    def setModelData(self, comboBox, model, index):
        model.setData(index, comboBox.currentIndex(), Qt.ItemDataRole.EditRole)

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)
