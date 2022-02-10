import json
import os

import accupatt.config as cfg
from accupatt.models.sprayCard import SprayCard
from accupatt.widgets.cardtablewidget import CardTableWidget
from PyQt6 import uic
from PyQt6.QtCore import QAbstractListModel, Qt, QItemSelectionModel, QModelIndex, QSettings, pyqtSlot
from PyQt6.QtWidgets import QListView, QMessageBox

from accupatt.windows.createDefinedSet import CreateDefinedSet

Ui_Form, baseclass = uic.loadUiType(os.path.join(os.getcwd(), 'resources', 'editDefinedSets.ui'))

def load_defined_sets():
    settings = QSettings('accupatt','AccuPatt')
    sets = settings.value(cfg._CARD_DEFINED_SETS, defaultValue=cfg.CARD_DEFINED_SETS__DEFAULT)
    if type(sets) is str:
        # came from settings JSON -> parse json string to list
        sets = json.loads(sets)
    return [DefinedSet(set_dict=s) for s in sets]

def save_defined_sets(sets):
    settings = QSettings('accupatt','AccuPatt')
    sets_json = json.dumps([set.toJSON() for set in sets])
    settings.setValue(cfg._CARD_DEFINED_SETS, sets_json)

class DefinedSetManager(baseclass):

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        
        # Shortcut handles
        self.lv: QListView = self.ui.listView
        self.lm = DefinedSetListModel(self)
        self.lv.setModel(self.lm)
        self.cardTable: CardTableWidget = self.ui.cardTableWidget
        self.cardTable.tv.hideColumn(1)
        self.cardTable.tv.hideColumn(2)
        self.cardTable.tv.hideColumn(5)
        # Load in defined sets to list widget
        self.lm.loadSets(load_defined_sets())
        # Set and select initial value for listview
        self.lv.selectionModel().currentRowChanged[QModelIndex,QModelIndex].connect(self.set_selection_changed)
        self.lv.selectionModel().select(self.lm.index(0), QItemSelectionModel.SelectionFlag.Select)
        # Wire up slots
        self.ui.buttonAddSet.clicked.connect(self.add_set)
        self.ui.buttonRemoveSet.clicked.connect(self.remove_set)
        self.ui.buttonAddRegSpaced.clicked.connect(self.add_regularly_spaced)

        self.show()

    @pyqtSlot()
    def add_set(self):
        self.lm.addSet()
        self.lv.selectionModel().clear()
        self.lv.selectionModel().select(self.lm.index(self.lm.rowCount()-1,0),QItemSelectionModel.SelectionFlag.Select)
        
    @pyqtSlot()
    def remove_set(self):
        selected_set = self.lv.selectionModel().selectedIndexes()[0]
        msg = QMessageBox.question(self, 'Are You Sure?',
                                        'This Defined Set will be removed and unrecoverable. Continue?')
        if msg == QMessageBox.StandardButton.No:
            return
        self.lm.removeSet(selected_set)
        
    @pyqtSlot(QModelIndex,QModelIndex)
    def set_selection_changed(self, current: QModelIndex, previous: QModelIndex = QModelIndex()):
        self.cardTable.assign_card_list(self.lm.sets[current.row()].cards)
        
        
    @pyqtSlot()
    def add_regularly_spaced(self):
        #Create popup and send current appInfo vals to popup
        e = CreateDefinedSet(parent=self)
        #Connect Slot to retrieve Vals back from popup
        e.setConfirmed[list].connect(self.add_from_regularly_spaced)
        #Start Loop
        e.exec()
        
    @pyqtSlot(list)
    def add_from_regularly_spaced(self, cards: list):
        self.cardTable.add_cards_to_table(cards)
        
    def accept(self):
        # Update saved Defined Sets in Settings
        save_defined_sets(self.lm.sets)
        # If all checks out, notify requestor and close
        super().accept()  

class DefinedSet:
    def __init__(self, name = 'New Set', cards: list[SprayCard] = [], set_dict: dict = None):
        self.name = name
        self.cards = cards
        if set_dict is not None:
            self.load_from_dict(set_dict)
    
    def load_from_dict(self, set_dict: dict):
        self.name = set_dict['set_name']
        self.cards = [SprayCard(name=name) for name in set_dict['card_name']]
        for i, c in enumerate(self.cards):
            c.location = set_dict['location'][i]
            c.location_units = set_dict['location_unit'][i]
            c.threshold_type = set_dict['threshold_type'][i]
            c.dpi = set_dict['dpi'][i]
            
    def toJSON(self):
        d = {}
        d['set_name'] = self.name
        d['card_name'] = [c.name for c in self.cards]
        d['location'] = [c.location for c in self.cards]
        d['location_unit'] = [c.location_units for c in self.cards]
        d['threshold_type'] = [c.threshold_type for c in self.cards]
        d['dpi'] = [c.dpi for c in self.cards]
        return d

class DefinedSetListModel(QAbstractListModel):
    def __init__(self, parent=None, *args):
        super(DefinedSetListModel, self).__init__()
        self.sets: list[DefinedSet] = []
        
    def loadSets(self, set_list):
        self.sets = set_list
        self.dataChanged.emit(self.index(0,0),self.index(self.rowCount(),0))
        
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
        self.sets.append(DefinedSet())
        self.endInsertRows()
        
    def removeSet(self, selected_index: QModelIndex):
        row = selected_index.row()
        self.beginRemoveRows(QModelIndex(), row, row)
        self.sets.pop(row)
        self.endRemoveRows()
        
    def flags(self, index):
        if not index.isValid():
            return None
        return Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEditable
    
    def get_row_for_name(self, name) -> int:
        names = [s.name for s in self.sets]
        if name not in names:
            return -1
        return names.index(name)
        