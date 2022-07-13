import os

import accupatt.config as cfg
from accupatt.models.sprayCard import SprayCard
from PyQt6 import uic
from PyQt6.QtCore import (
    QAbstractTableModel,
    QItemSelectionModel,
    QModelIndex,
    Qt,
    QVariant,
    pyqtSignal,
    pyqtSlot,
)
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QHeaderView,
    QStyledItemDelegate,
    QMessageBox,
    QPushButton,
    QTableView,
)

Ui_Form, baseclass = uic.loadUiType(
    os.path.join(os.getcwd(), "resources", "cardTableWidget.ui")
)


class CardTableWidget(baseclass):

    passDataChanged = pyqtSignal()
    selectionChanged = pyqtSignal(bool)
    editCard = pyqtSignal(SprayCard)
    editCardSpreadFactors = pyqtSignal(SprayCard)

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.ui = Ui_Form()
        self.ui.setupUi(self)

        self.ui.buttonAddCard.clicked.connect(self.add_card)
        self.ui.buttonRemoveCard.clicked.connect(self.remove_cards)
        self.ui.buttonUp.clicked.connect(self.shift_up)
        self.ui.buttonDown.clicked.connect(self.shift_down)

        # Populate TableView
        self.tm = CardTable(parent=self)
        self.tv: QTableView = self.ui.tableView

        self.tv.setModel(self.tm)
        self.tv.setItemDelegateForColumn(
            3, ComboBoxDelegate(self.tv, cfg.UNITS_LENGTH_LARGE)
        )
        self.tv.setItemDelegateForColumn(
            5,
            EditableComboBoxDelegate(
                self.tv, [str(dpi) for dpi in cfg.IMAGE_DPI_OPTIONS]
            ),
        )
        self.tv.setItemDelegateForColumn(
            6, ComboBoxDelegate(self.tv, cfg.THRESHOLD_TYPES)
        )
        self.tv.setItemDelegateForColumn(
            7, ComboBoxDelegate(self.tv, cfg.THRESHOLD_GRAYSCALE_METHODS)
        )
        self.tv.setItemDelegateForColumn(
            11, ComboBoxDelegate(self.tv, CardTable.band_pass_options)
        )
        self.tv.setItemDelegateForColumn(
            14, ComboBoxDelegate(self.tv, CardTable.band_pass_options)
        )
        self.tv.setItemDelegateForColumn(
            17, ComboBoxDelegate(self.tv, CardTable.band_pass_options)
        )
        self.tv.setItemDelegateForColumn(
            20, ComboBoxDelegate(self.tv, cfg.STAIN_APPROXIMATION_METHODS)
        )
        self.tv.setItemDelegateForColumn(
            21, ComboBoxDelegate(self.tv, cfg.SPREAD_METHODS)
        )

        self.selection_changed()

        self.show()
        self.tv.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.ResizeToContents
        )
        self.tv.verticalHeader().setVisible(False)

        self.tv.selectionModel().selectionChanged.connect(self.selection_changed)
        self.tm.triggerImageUpdate[SprayCard].connect(self.edit_card)

    def edit_card(self, card):
        self.editCard.emit(card)

    def edit_card_spread_factors(self, card):
        self.editCardSpreadFactors.emit(card)

    def assign_card_list(self, card_list: list[SprayCard], filepath: str = None):
        self.tm.loadCards(card_list)
        self.filepath = filepath
        self.selection_changed()
        self.tv.resizeColumnsToContents()

    def add_cards_to_table(self, card_list: list[SprayCard]):
        rows = self.tm.addCards(card_list)
        self.passDataChanged.emit()
        indexes = [self.tm.index(r, 0) for r in rows]
        mode = (
            QItemSelectionModel.SelectionFlag.Select
            | QItemSelectionModel.SelectionFlag.Rows
        )
        [self.tv.selectionModel().select(index, mode) for index in indexes]
        self.tv.resizeColumnsToContents()

    def set_defined_set_mode(self):
        self.tm.definedSetMode = True

    @pyqtSlot()
    def selection_changed(self):
        hasSelection = bool(self.tv.selectionModel().selectedRows())
        self.ui.buttonRemoveCard.setEnabled(hasSelection)
        self.ui.buttonUp.setEnabled(hasSelection)
        self.ui.buttonDown.setEnabled(hasSelection)
        self.selectionChanged.emit(hasSelection)

    @pyqtSlot()
    def shift_up(self):
        self.tm.shiftRows(self.tv.selectionModel().selectedRows(), moveUp=True)

    @pyqtSlot()
    def shift_down(self):
        self.tm.shiftRows(self.tv.selectionModel().selectedRows(), moveUp=False)

    @pyqtSlot()
    def add_card(self):
        self.tm.addCard(filepath=self.filepath)
        self.passDataChanged.emit()
        self.tv.resizeColumnsToContents()

    @pyqtSlot()
    def remove_cards(self):
        sel = self.tv.selectionModel().selectedRows()
        for index in sel:
            if self.tm.card_list[index.row()].has_image:
                msg = QMessageBox.question(
                    self,
                    "Are You Sure?",
                    "One or more selected cards have image data which will be erased. Continue?",
                )
                if msg == QMessageBox.StandardButton.Yes:
                    break
                else:
                    return
        self.tm.removeCards(sel)
        self.passDataChanged.emit()


class PushButtonDelegate(QStyledItemDelegate):
    def __init__(self, owner, text):
        QStyledItemDelegate.__init__(self, owner)
        self.text = text

    def paint(self, painter, option, index):
        parent: QAbstractItemView = self.parent()
        if parent.model().flags(index) & Qt.ItemFlag.ItemIsEditable:
            self.parent().openPersistentEditor(index)
        QStyledItemDelegate.paint(self, painter, option, index)

    def setModelData(self, editor, model, index):
        model.setData(index, editor.text())

    def createEditor(self, parent, option, index):
        button = QPushButton(self.text, parent)
        button.clicked.connect(self.button_clicked)
        self.parent().horizontalHeader().resizeSections(
            QHeaderView.ResizeMode.ResizeToContents
        )
        return button

    def button_clicked(self):
        self.commitData.emit(self.sender())


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


class EditableComboBoxDelegate(QStyledItemDelegate):
    def __init__(self, owner, items):
        QStyledItemDelegate.__init__(self, owner)
        self.items = items

    def createEditor(self, widget, option, index):
        editor = QComboBox(widget)
        editor.addItems(self.items)
        editor.setEditable(True)
        return editor

    def setEditorData(self, editor: QComboBox, index):
        value = index.model().data(index, Qt.ItemDataRole.EditRole)
        if value:
            editor.setCurrentText(value)

    def setModelData(self, comboBox, model, index):
        model.setData(index, comboBox.currentText(), Qt.ItemDataRole.EditRole)

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)


class CardTable(QAbstractTableModel):

    triggerImageUpdate = pyqtSignal(SprayCard)

    band_pass_options = ["Band-Pass", "Band-Reject"]

    def __init__(self, parent=None, *args):
        super(CardTable, self).__init__(parent)
        self.headers = [
            "Name",
            "In Composite",
            "Location",
            "Units",
            "Has Image?",
            "DPI",
            "Threshold Type",
            "Grayscale Method",
            "Grayscale Threshold",
            "Hue Min",
            "Hue Max",
            "Hue Band",
            "Sat Min",
            "Sat Max",
            "Sat Band",
            "Bri Min",
            "Bri Max",
            "Bri Band",
            "Watershed",
            "Min Stain Px",
            "Stain Approx. Method",
            "Spread Equation",
            "Spread Factor A",
            "Spread Factor B",
            "Spread Factor C",
        ]
        self.card_list: list[SprayCard] = []
        self.definedSetMode = False

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
            return Qt.AlignmentFlag.AlignCenter.value
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
            if role == Qt.ItemDataRole.CheckStateRole:
                return (
                    Qt.CheckState.Checked if card.has_image else Qt.CheckState.Unchecked
                )
            elif role == Qt.ItemDataRole.DisplayRole:
                return "Yes" if card.has_image else "No"
        elif col == 5:
            if role == Qt.ItemDataRole.DisplayRole:
                return str(card.dpi) if card.has_image else ""
            elif role == Qt.ItemDataRole.EditRole:
                return str(card.dpi)
        elif col == 6:
            if role == Qt.ItemDataRole.DisplayRole:
                return card.threshold_type
            if role == Qt.ItemDataRole.EditRole:
                return cfg.THRESHOLD_TYPES.index(card.threshold_type)
        elif col == 7:
            if role == Qt.ItemDataRole.DisplayRole:
                return card.threshold_method_grayscale
            if role == Qt.ItemDataRole.EditRole:
                return cfg.THRESHOLD_GRAYSCALE_METHODS.index(
                    card.threshold_method_grayscale
                )
        elif col == 8:
            if role == Qt.ItemDataRole.DisplayRole:
                return str(card.threshold_grayscale)
            if role == Qt.ItemDataRole.EditRole:
                return str(card.threshold_grayscale)
        elif col == 9:
            if role == Qt.ItemDataRole.DisplayRole:
                return str(card.threshold_color_hue_min)
            if role == Qt.ItemDataRole.EditRole:
                return str(card.threshold_color_hue_min)
        elif col == 10:
            if role == Qt.ItemDataRole.DisplayRole:
                return str(card.threshold_color_hue_max)
            if role == Qt.ItemDataRole.EditRole:
                return str(card.threshold_color_hue_max)
        elif col == 11:
            if role == Qt.ItemDataRole.DisplayRole:
                return (
                    self.band_pass_options[0]
                    if card.threshold_color_hue_pass
                    else self.band_pass_options[1]
                )
            if role == Qt.ItemDataRole.EditRole:
                return 0 if card.threshold_color_hue_pass else 1
        elif col == 12:
            if role == Qt.ItemDataRole.DisplayRole:
                return str(card.threshold_color_saturation_min)
            if role == Qt.ItemDataRole.EditRole:
                return str(card.threshold_color_saturation_min)
        elif col == 13:
            if role == Qt.ItemDataRole.DisplayRole:
                return str(card.threshold_color_saturation_max)
            if role == Qt.ItemDataRole.EditRole:
                return str(card.threshold_color_saturation_max)
        elif col == 14:
            if role == Qt.ItemDataRole.DisplayRole:
                return (
                    self.band_pass_options[0]
                    if card.threshold_color_saturation_pass
                    else self.band_pass_options[1]
                )
            if role == Qt.ItemDataRole.EditRole:
                return 0 if card.threshold_color_saturation_pass else 1
        elif col == 15:
            if role == Qt.ItemDataRole.DisplayRole:
                return str(card.threshold_color_brightness_min)
            if role == Qt.ItemDataRole.EditRole:
                return str(card.threshold_color_brightness_min)
        elif col == 16:
            if role == Qt.ItemDataRole.DisplayRole:
                return str(card.threshold_color_brightness_max)
            if role == Qt.ItemDataRole.EditRole:
                return str(card.threshold_color_brightness_max)
        elif col == 17:
            if role == Qt.ItemDataRole.DisplayRole:
                return (
                    self.band_pass_options[0]
                    if card.threshold_color_brightness_pass
                    else self.band_pass_options[1]
                )
            if role == Qt.ItemDataRole.EditRole:
                return 0 if card.threshold_color_brightness_pass else 1
        elif col == 18:
            if role == Qt.ItemDataRole.CheckStateRole:
                return (
                    Qt.CheckState.Checked if card.watershed else Qt.CheckState.Unchecked
                )
            elif role == Qt.ItemDataRole.DisplayRole:
                return "Yes" if card.watershed else "No"
        elif col == 19:
            if role == Qt.ItemDataRole.DisplayRole:
                return str(card.min_stain_area_px)
            if role == Qt.ItemDataRole.EditRole:
                return str(card.min_stain_area_px)
        elif col == 20:
            if role == Qt.ItemDataRole.DisplayRole:
                return card.stain_approximation_method
            if role == Qt.ItemDataRole.EditRole:
                return cfg.STAIN_APPROXIMATION_METHODS.index(
                    card.stain_approximation_method
                )
        elif col == 21:
            if role == Qt.ItemDataRole.DisplayRole:
                return card.spread_method
            if role == Qt.ItemDataRole.EditRole:
                return cfg.SPREAD_METHODS.index(card.spread_method)
        elif col == 22:
            if role == Qt.ItemDataRole.DisplayRole:
                return str(card.spread_factor_a)
            if role == Qt.ItemDataRole.EditRole:
                return str(card.spread_factor_a)
        elif col == 23:
            if role == Qt.ItemDataRole.DisplayRole:
                return str(card.spread_factor_b)
            if role == Qt.ItemDataRole.EditRole:
                return str(card.spread_factor_b)
        elif col == 24:
            if role == Qt.ItemDataRole.DisplayRole:
                return str(card.spread_factor_c)
            if role == Qt.ItemDataRole.EditRole:
                return str(card.spread_factor_c)
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
        elif col == 4:
            pass
        elif col == 5:
            try:
                card.dpi = int(value)
            except ValueError:
                return False
        elif col == 6:
            if role == Qt.ItemDataRole.EditRole:
                card.threshold_type = cfg.THRESHOLD_TYPES[value]
        elif col == 7:
            if role == Qt.ItemDataRole.EditRole:
                card.threshold_method_grayscale = cfg.THRESHOLD_GRAYSCALE_METHODS[value]
        elif col == 8:
            try:
                card.threshold_grayscale = int(value)
            except ValueError:
                return False
        elif col == 9:
            try:
                card.threshold_color_hue_min = int(value)
            except ValueError:
                return False
        elif col == 10:
            try:
                card.threshold_color_hue_max = int(value)
            except ValueError:
                return False
        elif col == 11:
            card.threshold_color_hue_pass = value == 0
        elif col == 12:
            try:
                card.threshold_color_saturation_min = int(value)
            except ValueError:
                return False
        elif col == 13:
            try:
                card.threshold_color_saturation_max = int(value)
            except ValueError:
                return False
        elif col == 14:
            card.threshold_color_saturation_pass = value == 0
        elif col == 15:
            try:
                card.threshold_color_brightness_min = int(value)
            except ValueError:
                return False
        elif col == 16:
            try:
                card.threshold_color_brightness_max = int(value)
            except ValueError:
                return False
        elif col == 17:
            card.threshold_color_brightness_pass = value == 0
        elif col == 18:
            card.watershed = Qt.CheckState(value) == Qt.CheckState.Checked
        elif col == 19:
            try:
                card.min_stain_area_px = int(value)
            except ValueError:
                return False
        elif col == 20:
            card.stain_approximation_method = cfg.STAIN_APPROXIMATION_METHODS[value]
        elif col == 21:
            card.spread_method = cfg.SPREAD_METHODS[value]
        elif col == 22:
            try:
                card.spread_factor_a = float(value)
            except ValueError:
                return False
        elif col == 23:
            try:
                card.spread_factor_b = float(value)
            except ValueError:
                return False
        elif col == 24:
            try:
                card.spread_factor_c = float(value)
            except ValueError:
                return False
        else:
            return False
        if col >= 5 and col <= 20:
            self.triggerImageUpdate.emit(card)
            card.current = False
            card.stats.current = False
        if col >= 21 and col <= 24:
            card.stats.current = False
        self.dataChanged.emit(index, index)
        return True

    def shiftRows(self, selectedRows, moveUp):
        parent = QModelIndex()
        sort_list = []
        for index in selectedRows:
            sort_list.append(index.row())
            # if abutting top, abort
            if moveUp and index.row() == 0:
                return
            if not moveUp and index.row() == len(self.card_list) - 1:
                return
        sort_list.sort()
        if moveUp:
            shift = -1
            self.beginMoveRows(
                parent,
                sort_list[0],
                sort_list[len(sort_list) - 1],
                parent,
                sort_list[0] + shift,
            )
        else:
            shift = 1
            self.beginMoveRows(
                parent,
                sort_list[0],
                sort_list[len(sort_list) - 1],
                parent,
                sort_list[len(sort_list) - 1] + shift + 1,
            )
            sort_list.sort(reverse=True)
        for row in sort_list:
            self.card_list.insert(row + shift, self.card_list.pop(row))
        self.endMoveRows()

    def addCard(self, filepath):
        self.beginInsertRows(QModelIndex(), self.rowCount(), self.rowCount())
        self.card_list.append(
            SprayCard(name=f"Card {self.rowCount()}", filepath=filepath)
        )
        self.endInsertRows()

    def addCards(self, new_cards: list[SprayCard]):
        self.beginInsertRows(
            QModelIndex(), self.rowCount(), self.rowCount() + len(new_cards) - 1
        )
        new_indices = []
        for card in new_cards:
            self.card_list.append(card)
            new_indices.append(len(self.card_list) - 1)
        self.endInsertRows()
        return new_indices

    def removeCards(self, selection: list[QModelIndex]):
        for index in reversed(selection):
            row = index.row()
            self.beginRemoveRows(QModelIndex(), row, row)
            self.card_list.pop(row)
            self.endRemoveRows()

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
        elif col == 4:
            return Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable
        elif col >= 5:
            if not self.card_list[index.row()].has_image and not self.definedSetMode:
                return Qt.ItemFlag.NoItemFlags
            if (col >= 9 and col <= 17) and self.card_list[
                index.row()
            ].threshold_type == cfg.THRESHOLD_TYPE_GRAYSCALE:
                return Qt.ItemFlag.NoItemFlags
            if (col == 7 or col == 8) and self.card_list[
                index.row()
            ].threshold_type == cfg.THRESHOLD_TYPE_HSB:
                return Qt.ItemFlag.NoItemFlags
            if col == 18:
                return (
                    Qt.ItemFlag.ItemIsEnabled
                    | Qt.ItemFlag.ItemIsSelectable
                    | Qt.ItemFlag.ItemIsUserCheckable
                )
        return (
            Qt.ItemFlag.ItemIsEnabled
            | Qt.ItemFlag.ItemIsSelectable
            | Qt.ItemFlag.ItemIsEditable
        )
