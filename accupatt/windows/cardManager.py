import os
from typing import List

import accupatt.config as cfg
from accupatt.models.sprayCard import SprayCard
from accupatt.models.passData import Pass
from accupatt.widgets.passinfowidget import PassInfoWidget
from accupatt.windows.loadCards import LoadCards
from PyQt6 import uic
from PyQt6.QtCore import (QAbstractTableModel, QItemSelectionModel,
                          QModelIndex, QSettings, Qt, QVariant, pyqtSignal,
                          pyqtSlot)
from PyQt6.QtWidgets import QComboBox, QFileDialog, QItemDelegate, QMessageBox

Ui_Form, baseclass = uic.loadUiType(os.path.join(os.getcwd(), 'resources', 'cardManager.ui'))

defined_sets = {
    'Standard Fly-In (WSP)': {
        'cards': ['L-32', 'L-24', 'L-16', 'L-8', 'Center', 'R-8', 'R-16', 'R-24', 'R-32'],
        'locations': [-32, -24, -16, -8, 0, 8, 16, 24, 32],
        'location_units': cfg.UNIT_FT,
        'threshold_type': cfg.THRESHOLD_TYPE_GRAYSCALE
    },
    'Standard Fly-In (Cast-Coat)': {
        'cards': ['L-32', 'L-24', 'L-16', 'L-8', 'Center', 'R-8', 'R-16', 'R-24', 'R-32'],
        'locations': [-32, -24, -16, -8, 0, 8, 16, 24, 32],
        'location_units': cfg.UNIT_FT,
        'threshold_type': cfg.THRESHOLD_TYPE_HSB
    },
}

load_image_options = ['One File Per Card','One File, Multiple Cards']

class CardManager(baseclass):

    passDataChanged = pyqtSignal()

    def __init__(self, passData: Pass = None, filepath=None, parent=None):
        super().__init__(parent=parent)
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        
        #Load in Settings
        self.settings = QSettings('accupatt','AccuPatt')
       
        # File path for creating new cards
        self.filepath = filepath
        
        # Pass Info Fields
        self.passData = passData
        self.ui.labelPass.setText(passData.name)
        self.passInfoWidget: PassInfoWidget = self.ui.passInfoWidget
        self.passInfoWidget.fill_from_pass(passData)
       
        #Load in defined sets to combobox
        for key in defined_sets.keys():
           self.ui.comboBoxDefinedSet.addItem(key)

        self.ui.buttonAddSet.clicked.connect(self.add_cards)
        self.ui.buttonAddCard.clicked.connect(self.add_card)
        self.ui.buttonRemoveCard.clicked.connect(self.remove_cards)

        self.ui.buttonUp.clicked.connect(self.shift_up)
        self.ui.buttonDown.clicked.connect(self.shift_down)
        
        self.ui.comboBoxLoadMethod.addItems(load_image_options)
        self.ui.comboBoxLoadMethod.setCurrentIndex(load_image_options.index(
            self.settings.value('card_manager_load_method', defaultValue=load_image_options[1], type=str)))
        self.ui.buttonLoad.clicked.connect(self.load_cards)
        
        #Populate TableView
        self.tm = CardTable(self)
        self.tm.loadCards(passData.spray_cards)
        self.tv = self.ui.tableView
        self.tv.setModel(self.tm)
        self.tv.setItemDelegateForColumn(4, ComboBoxDelegate(self, cfg.UNITS_LENGTH_LARGE))
        self.tv.setItemDelegateForColumn(5, ComboBoxDelegate(self, [str(dpi) for dpi in cfg.DPI_OPTIONS]))
        self.tv.setColumnWidth(5,100)

        self.selection_changed()

        self.show()
        
        self.ui.tableView.selectionModel().selectionChanged.connect(self.selection_changed)

    @pyqtSlot()
    def selection_changed(self):
        hasSelection = bool(self.ui.tableView.selectionModel().selectedRows())
        self.ui.buttonLoad.setEnabled(hasSelection)
        self.ui.buttonRemoveCard.setEnabled(hasSelection)
        self.ui.buttonUp.setEnabled(hasSelection)
        self.ui.buttonDown.setEnabled(hasSelection)
        self.ui.comboBoxLoadMethod.setEnabled(hasSelection)

    @pyqtSlot()
    def shift_up(self):
        self.tm.shiftRows(self.ui.tableView.selectionModel().selectedRows(), moveUp=True)

    @pyqtSlot()
    def shift_down(self):
        self.tm.shiftRows(self.ui.tableView.selectionModel().selectedRows(), moveUp=False)

    @pyqtSlot()
    def add_card(self):
        self.tm.addCard(filepath = self.filepath)
        self.passDataChanged.emit()

    @pyqtSlot()
    def add_cards(self):
        selectedSet = defined_sets[self.ui.comboBoxDefinedSet.currentText()]
        newCards = []
        for i in range(len(selectedSet['cards'])):
            c = SprayCard(name=selectedSet['cards'][i], filepath=self.filepath)
            c.location = selectedSet['locations'][i]
            c.location_units = selectedSet['location_units']
            c.threshold_type = selectedSet['threshold_type']
            newCards.append(c)
        rows = self.tm.addCards(newCards)
        self.passDataChanged.emit()
        indexes = [self.tm.index(r, 0) for r in rows]
        mode = QItemSelectionModel.SelectionFlag.Select | QItemSelectionModel.SelectionFlag.Rows
        [self.tv.selectionModel().select(index, mode) for index in indexes]
        
    @pyqtSlot()
    def remove_cards(self):
        sel = self.ui.tableView.selectionModel().selectedRows()
        for index in sel:
            if self.tm.card_list[index.row()].has_image:
                msg = QMessageBox.question(self, 'Are You Sure?',
                                           'One or more selected cards have image data which will be erased. Continue?')
                if msg == QMessageBox.StandardButton.Yes:
                    break
                else:
                    return
        self.tm.removeCards(sel)
        self.passDataChanged.emit()
    
    @pyqtSlot()
    def update_table(self):
        pass
    
    @pyqtSlot()
    def load_cards(self):
        #Check if any selected cards have images
        selection = self.ui.tableView.selectionModel().selectedRows()
        for row in selection:
            card: SprayCard = self.tm.card_list[row.row()]
            if card.has_image:
                msg = QMessageBox.question(self, 'Are You Sure?',
                                           f'{card.name} already has image data, overwrite?')
                if msg == QMessageBox.StandardButton.Yes:
                    break
                else:
                    return
        # Use chosen load method
        method = self.ui.comboBoxLoadMethod.currentText()
        if method == load_image_options[0]:
            #Single Images, Single Cards
            self._load_cards_singles(selection)
        else:
            #Single Image, Multiple Cards
            self._load_cards_multi(selection)
        self.settings.setValue('card_manager_load_method', self.ui.comboBoxLoadMethod.currentText())
    
    def _load_cards_singles(self, selection):
        # TODO: migrate to singles batch method
        card: SprayCard = self.tm.card_list[selection[0].row()]
        fname, _ = QFileDialog.getOpenFileName(self, 'Open file', 'home', "Image files (*.png)")
        with open(fname, 'rb') as file:
            binary_data = file.read()  
        card.save_image_to_db(image=binary_data)
        card.has_image = True
        card.include_in_composite = True
    
    def _load_cards_multi(self, selection):
        fname, _ = QFileDialog.getOpenFileName(self, 'Open file', 'home', "Image files (*.png)")
        if fname == '': return
        card_list = []
        for row in selection:
            card_list.append(self.tm.card_list[row.row()])
        #Create popup and send current appInfo vals to popup
        e = LoadCards(image_file=fname, card_list=card_list, parent=self)
        #Connect Slot to retrieve Vals back from popup
        e.accepted.connect(self.update_table)
        #Start Loop
        e.exec()
        
    def accept(self):
        p = self.passData
        # If any passInfo fields invalid, show user and return to current window
        if len(excepts := self.passInfoWidget.validate_fields(p)) > 0:
            QMessageBox.warning(self, 'Invalid Data', '\n'.join(excepts))
            return
        # If all checks out, notify requestor and close
        super().accept()  

class ComboBoxDelegate(QItemDelegate):
    def __init__(self, owner, itemList):
        QItemDelegate.__init__(self, owner)
        self.itemList = itemList
    
    def createEditor(self, parent, option, index):
        editor = QComboBox(parent)
        editor.addItems(self.itemList)
        return editor
    
    def setEditorData(self, comboBox, index):
        comboBox.setCurrentIndex(int(index.model().data(index, role=Qt.ItemDataRole.EditRole)))
        
    def setModelData(self, comboBox, model, index):
        model.setData(index, comboBox.currentIndex(), Qt.ItemDataRole.EditRole)
        
    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)
class CardTable(QAbstractTableModel):
    def __init__(self, parent=None, *args): 
        super(CardTable, self).__init__()
        self.card_list = None
    
    def loadCards(self, card_list):
        self.card_list = card_list

    def rowCount(self, parent = QModelIndex()) -> int:
        return len(self.card_list)

    def columnCount(self, parent = QModelIndex()) -> int:
        return 6

    def headerData(self, column, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role!=Qt.ItemDataRole.DisplayRole:
            return QVariant()
        if orientation==Qt.Orientation.Horizontal:
            headers = ['Name','Has Image?','In Composite','Location','Units','Px Per In']
            if column < len(headers):
                return QVariant(headers[column])
        return QVariant()

    def data(self, index, role: Qt.ItemDataRole.DisplayRole):
        i = index.row()
        j = index.column()
        card: SprayCard = self.card_list[i]
        if role == Qt.ItemDataRole.TextAlignmentRole:
            return Qt.AlignmentFlag.AlignCenter
        elif role == Qt.ItemDataRole.CheckStateRole:
            if j == 1:
                if card.has_image == 1:
                    return Qt.CheckState.Checked
                else:
                    return Qt.CheckState.Unchecked
            elif j == 2:
                if card.include_in_composite == 1:
                    return Qt.CheckState.Checked
                else:
                    return Qt.CheckState.Unchecked
            else: return QVariant()
        elif role == Qt.ItemDataRole.DisplayRole or role == Qt.ItemDataRole.EditRole:
            if j == 0:
                # Name
                return card.name
            elif j == 1:
                return 'Yes' if card.has_image else 'No'
            elif j == 2:
                # Include in Composite?
                if role == Qt.ItemDataRole.DisplayRole:
                    return 'Yes' if card.include_in_composite else 'No'
                elif role == Qt.ItemDataRole.EditRole:
                    return card.include_in_composite
            elif j == 3:
                # Location
                return card.location
            elif j == 4:
                # Location Units
                if role == Qt.ItemDataRole.DisplayRole:
                    return card.location_units
                elif role == Qt.ItemDataRole.EditRole:
                    return cfg.UNITS_LENGTH_LARGE.index(card.location_units)
            elif j == 5:
                # PPI
                if role == Qt.ItemDataRole.DisplayRole:
                    return str(card.dpi)
                elif role == Qt.ItemDataRole.EditRole:
                    return cfg.DPI_OPTIONS.index(card.dpi)
        return QVariant()
    
    def setData(self, index, value, role = Qt.ItemDataRole.EditRole) -> bool:
        i = index.row()
        j = index.column()
        card = self.card_list[i]
        if value is None:
            return False
        if role == Qt.ItemDataRole.CheckStateRole:
            if j == 2:
                card.include_in_composite = (Qt.CheckState(value) == Qt.CheckState.Checked)
                self.dataChanged.emit(index,index)
        if not role == Qt.ItemDataRole.EditRole:
            return False
        if j == 0:
            #Name
            card.name = value
            self.dataChanged.emit(index,index)
            return True
        elif j == 1:
            return True
        elif j == 2:
            # Include In Composite
            card.include_in_composite = value
            self.dataChanged.emit(index,index)
            return True
        elif j == 3:
            #Location
            try:
                float(value)
            except ValueError:
                print('Attempt to set a non-numeric card location')
                return False
            card.location = value
            self.dataChanged.emit(index,index)
            return True 
        elif j == 4:
            # Location Units
            card.location_units = cfg.UNITS_LENGTH_LARGE[value]
            self.dataChanged.emit(index,index)
        elif j == 5:
            # PPI
            card.dpi = cfg.DPI_OPTIONS[value]
            self.dataChanged.emit(index,index)
            return True
        return False

    def shiftRows(self, selectedRows, moveUp):
        parent = QModelIndex()
        sort_list = []
        for index in selectedRows:
                sort_list.append(index.row())
                #if abutting top, abort
                if moveUp and index.row() == 0: return
                if not moveUp and index.row() == len(self.card_list)-1: return
        sort_list.sort()
        if moveUp:
            shift = -1
            self.beginMoveRows(parent, sort_list[0], sort_list[len(sort_list)-1], parent, sort_list[0]+shift)
        else:
            shift = 1  
            self.beginMoveRows(parent, sort_list[0], sort_list[len(sort_list)-1], parent, sort_list[len(sort_list)-1]+shift+1)
            sort_list.sort(reverse = True)
        for row in sort_list:
            self.card_list.insert(row+shift,self.card_list.pop(row))
        self.endMoveRows()

    def addCard(self, filepath):
        self.beginInsertRows(QModelIndex(), self.rowCount(), self.rowCount())
        self.card_list.append(SprayCard(name=f'Card {self.rowCount()}', filepath = filepath))
        self.endInsertRows()
    
    def addCards(self, new_cards: List[SprayCard]):
        self.beginInsertRows(QModelIndex(), self.rowCount(), self.rowCount()+len(new_cards)-1)
        new_indices = []
        for card in new_cards:
            self.card_list.append(card)
            new_indices.append(len(self.card_list)-1)
        self.endInsertRows()
        return new_indices
        
    def removeCards(self, selection: List[QModelIndex]):
        for index in reversed(selection):
            row = index.row()
            self.beginRemoveRows(QModelIndex(), row, row)
            self.card_list.pop(row)
            self.endRemoveRows()

    def flags(self, index):
        if not index.isValid():
            return None
        if index.column() == 1:
            return Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable
        elif index.column() == 2:
            return Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsUserCheckable
        else:
            return Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEditable
