import json
import os

import accupatt.config as cfg
from accupatt.models.sprayCard import SprayCard
from accupatt.widgets.cardtablewidget import CardTableWidget
from PyQt6 import uic
from PyQt6.QtCore import (
    QAbstractListModel,
    Qt,
    QItemSelectionModel,
    QModelIndex,
    pyqtSlot,
)
from PyQt6.QtWidgets import QListView, QMessageBox

from accupatt.windows.createDefinedSet import CreateDefinedSet

Ui_Form, baseclass = uic.loadUiType(
    os.path.join(os.getcwd(), "resources", "editDefinedSets.ui")
)


def load_defined_sets():
    sets = cfg.get_card_defined_sets()
    if type(sets) is str:
        # came from settings JSON -> parse json string to list
        sets = json.loads(sets)
    return [DefinedSet(set_dict=s) for s in sets]


def save_defined_sets(sets):
    sets_json = json.dumps([set.toJSON() for set in sets])
    cfg.set_card_defined_sets(sets_json)


class DefinedSetManager(baseclass):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.ui = Ui_Form()
        self.ui.setupUi(self)

        # Shortcut handles
        self.lv: QListView = self.ui.listView
        self.lm = DefinedSetListModel(load_defined_sets(), self)
        self.lv.setModel(self.lm)
        self.cardTable: CardTableWidget = self.ui.cardTableWidget
        self.cardTable.set_defined_set_mode()
        self.cardTable.tv.hideColumn(1)
        self.cardTable.tv.hideColumn(4)
        self.cardTable.tv.hideColumn(5)
        # Set and select initial value for listview
        self.lv.selectionModel().currentChanged[QModelIndex, QModelIndex].connect(
            self.current_set_changed
        )
        self.lv.setCurrentIndex(self.lm.index(0, 0))
        # Wire up slots
        self.ui.buttonAddSet.clicked.connect(self.add_set)
        self.ui.buttonRemoveSet.clicked.connect(self.remove_set)
        self.ui.buttonAddRegSpaced.clicked.connect(self.add_regularly_spaced)

        self.show()

    @pyqtSlot()
    def add_set(self):
        self.lm.addSet()
        self.lv.selectionModel().setCurrentIndex(
            self.lm.index(self.lm.rowCount() - 1, 0),
            QItemSelectionModel.SelectionFlag.ClearAndSelect,
        )

    @pyqtSlot()
    def remove_set(self):
        selected_set = self.lv.selectionModel().selectedIndexes()[0]
        msg = QMessageBox.question(
            self,
            "Are You Sure?",
            "This Defined Set will be removed and unrecoverable. Continue?",
        )
        if msg == QMessageBox.StandardButton.No:
            return
        self.lm.removeSet(selected_set)

    @pyqtSlot(QModelIndex, QModelIndex)
    def current_set_changed(self, current: QModelIndex, previous: QModelIndex):
        self.cardTable.assign_card_list(self.lm.sets[current.row()].cards)

    @pyqtSlot()
    def add_regularly_spaced(self):
        # Create popup and send current appInfo vals to popup
        e = CreateDefinedSet(parent=self)
        # Connect Slot to retrieve Vals back from popup
        e.setConfirmed[list].connect(self.add_from_regularly_spaced)
        # Start Loop
        e.exec()

    @pyqtSlot(list)
    def add_from_regularly_spaced(self, cards: list):
        # Send directly to method in CardTable, changes flow back to lm.sets
        self.cardTable.add_cards_to_table(cards)

    def accept(self):
        # Update saved Defined Sets in Settings
        save_defined_sets(self.lm.sets)
        # If all checks out, notify requestor and close
        super().accept()


class DefinedSet:
    def __init__(
        self, name="New Set", cards: list[SprayCard] = [], set_dict: dict = None
    ):
        self.name = name
        self.cards = cards
        if set_dict is not None:
            self.load_from_dict(set_dict)

    def get_fresh_card_list(self):
        _cards = []
        for card in self.cards:
            c: SprayCard = SprayCard(name=card.name)
            c.location = card.location
            c.location_units = card.location_units
            c.threshold_type = card.threshold_type
            c.dpi = card.dpi
            _cards.append(c)
        return _cards

    def load_from_dict(self, set_dict: dict):
        self.name = set_dict["set_name"]
        self.cards = [SprayCard(name=name) for name in set_dict["card_name"]]
        for i, c in enumerate(self.cards):
            c.location = set_dict["location"][i]
            c.location_units = set_dict["location_unit"][i]
            c.threshold_type = set_dict[cfg._THRESHOLD_TYPE][i]
            c.threshold_method_grayscale = set_dict[cfg._THRESHOLD_GRAYSCALE_METHOD][i]
            c.threshold_grayscale = set_dict[cfg._THRESHOLD_GRAYSCALE][i]
            c.threshold_color_hue_min = set_dict[cfg._THRESHOLD_HSB_HUE_MIN][i]
            c.threshold_color_hue_max = set_dict[cfg._THRESHOLD_HSB_HUE_MAX][i]
            c.threshold_color_hue_pass = set_dict[cfg._THRESHOLD_HSB_HUE_PASS][i]
            c.threshold_color_saturation_min = set_dict[
                cfg._THRESHOLD_HSB_SATURATION_MIN
            ][i]
            c.threshold_color_saturation_max = set_dict[
                cfg._THRESHOLD_HSB_SATURATION_MAX
            ][i]
            c.threshold_color_saturation_pass = set_dict[
                cfg._THRESHOLD_HSB_SATURATION_PASS
            ][i]
            c.threshold_color_brightness_min = set_dict[
                cfg._THRESHOLD_HSB_BRIGHTNESS_MIN
            ][i]
            c.threshold_color_brightness_max = set_dict[
                cfg._THRESHOLD_HSB_BRIGHTNESS_MAX
            ][i]
            c.threshold_color_brightness_pass = set_dict[
                cfg._THRESHOLD_HSB_BRIGHTNESS_PASS
            ][i]
            c.watershed = set_dict[cfg._WATERSHED][i]
            c.min_stain_area_px = set_dict[cfg._WATERSHED][i]
            c.stain_approximation_method = set_dict[cfg._STAIN_APPROXIMATION_METHOD][i]
            c.spread_method = set_dict[cfg._SPREAD_METHOD][i]
            c.spread_factor_a = set_dict[cfg._SPREAD_FACTOR_A][i]
            c.spread_factor_b = set_dict[cfg._SPREAD_FACTOR_B][i]
            c.spread_factor_c = set_dict[cfg._SPREAD_FACTOR_C][i]
            # c.dpi = set_dict["dpi"][i]
            # c.has_image = True

    def toJSON(self):
        d = {}
        d["set_name"] = self.name
        d["card_name"] = [c.name for c in self.cards]
        d["location"] = [c.location for c in self.cards]
        d["location_unit"] = [c.location_units for c in self.cards]
        d[cfg._THRESHOLD_TYPE] = [c.threshold_type for c in self.cards]
        d[cfg._THRESHOLD_GRAYSCALE_METHOD] = [
            c.threshold_method_grayscale for c in self.cards
        ]
        d[cfg._THRESHOLD_GRAYSCALE] = [c.threshold_grayscale for c in self.cards]
        d[cfg._THRESHOLD_HSB_HUE_MIN] = [c.threshold_color_hue_min for c in self.cards]
        d[cfg._THRESHOLD_HSB_HUE_MAX] = [c.threshold_color_hue_max for c in self.cards]
        d[cfg._THRESHOLD_HSB_HUE_PASS] = [
            c.threshold_color_hue_pass for c in self.cards
        ]
        d[cfg._THRESHOLD_HSB_SATURATION_MIN] = [
            c.threshold_color_saturation_min for c in self.cards
        ]
        d[cfg._THRESHOLD_HSB_SATURATION_MAX] = [
            c.threshold_color_saturation_max for c in self.cards
        ]
        d[cfg._THRESHOLD_HSB_SATURATION_PASS] = [
            c.threshold_color_saturation_pass for c in self.cards
        ]
        d[cfg._THRESHOLD_HSB_BRIGHTNESS_MIN] = [
            c.threshold_color_brightness_min for c in self.cards
        ]
        d[cfg._THRESHOLD_HSB_BRIGHTNESS_MAX] = [
            c.threshold_color_brightness_max for c in self.cards
        ]
        d[cfg._THRESHOLD_HSB_BRIGHTNESS_PASS] = [
            c.threshold_color_brightness_pass for c in self.cards
        ]
        d[cfg._WATERSHED] = [c.watershed for c in self.cards]
        d[cfg._MIN_STAIN_AREA_PX] = [c.min_stain_area_px for c in self.cards]
        d[cfg._STAIN_APPROXIMATION_METHOD] = [
            c.stain_approximation_method for c in self.cards
        ]
        d[cfg._SPREAD_METHOD] = [c.spread_method for c in self.cards]
        d[cfg._SPREAD_FACTOR_A] = [c.spread_factor_a for c in self.cards]
        d[cfg._SPREAD_FACTOR_B] = [c.spread_factor_b for c in self.cards]
        d[cfg._SPREAD_FACTOR_C] = [c.spread_factor_c for c in self.cards]
        # d["dpi"] = [c.dpi for c in self.cards]
        return d


class DefinedSetListModel(QAbstractListModel):
    def __init__(self, data, parent=None, *args):
        super(DefinedSetListModel, self).__init__(parent)
        self.sets: list[DefinedSet] = data

    def rowCount(self, parent=QModelIndex()) -> int:
        return len(self.sets)

    def data(self, index, role):
        s = self.sets[index.row()]
        if role == Qt.ItemDataRole.DisplayRole:
            return s.name

    def setData(self, index, value, role) -> bool:
        s = self.sets[index.row()]
        if role == Qt.ItemDataRole.EditRole:
            s.name = value
            self.dataChanged.emit(index, index)
            return True
        return False

    def addSet(self):
        self.beginInsertRows(QModelIndex(), self.rowCount(), self.rowCount())
        self.sets.append(DefinedSet(name=f"Defined Set {self.rowCount()+1}", cards=[]))
        self.endInsertRows()

    def removeSet(self, selected_index: QModelIndex):
        row = selected_index.row()
        self.beginRemoveRows(QModelIndex(), row, row)
        self.sets.pop(row)
        self.endRemoveRows()

    def flags(self, index):
        if not index.isValid():
            return None
        return (
            Qt.ItemFlag.ItemIsEnabled
            | Qt.ItemFlag.ItemIsSelectable
            | Qt.ItemFlag.ItemIsEditable
        )
