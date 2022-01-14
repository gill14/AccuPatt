from typing import List
from accupatt.windows.loadCards import LoadCards
import accupatt.config as cfg
from accupatt.windows.editThreshold import EditThreshold
from PyQt5.QtWidgets import QAbstractItemView, QApplication, QComboBox, QFileDialog, QItemDelegate, QListView, QListWidgetItem, QMessageBox, QStyle, QStyleOptionComboBox
from PyQt5.QtCore import QAbstractTableModel, QItemSelectionModel, QModelIndex, QVariant, Qt, QSettings, pyqtSignal, pyqtSlot
from PyQt5 import uic

import os, sys, copy

from accupatt.models.sprayCard import SprayCard

Ui_Form, baseclass = uic.loadUiType(os.path.join(os.getcwd(), 'accupatt', 'windows', 'ui', 'editCardList.ui'))

defined_sets = {
    'Standard Fly-In': {
        'cards': ['L-32', 'L-24', 'L-16', 'L-8', 'Center', 'R-8', 'R-16', 'R-24', 'R-32'],
        'locations': [-32, -24, -16, -8, 0, 8, 16, 24, 32]
    }
}

load_image_options = ['One File Per Card','One File, Multiple Cards']

class CardManager(baseclass):

    applied = pyqtSignal()
    passDataChanged = pyqtSignal()

    def __init__(self, passData=None, filepath=None, parent=None):
        super().__init__(parent=parent)
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        # Your code will go here

        #Load in Settings
        self.settings = QSettings('BG Application Consulting','AccuPatt')
       
        # File path for creating new cards
        self.filepath = filepath
       
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
        
        self.ui.buttonBox.accepted.connect(self.on_applied)
        
        #Populate TableView
        self.tm = CardTable(self)
        self.tm.loadCards(passData.spray_cards)
        self.tv = self.ui.tableView
        self.tv.setModel(self.tm)
        self.tv.setItemDelegateForColumn(3,ComboBoxDelegate(self, [cfg.INCLUDE_IN_COMPOSITE_NO_STRING, cfg.INCLUDE_IN_COMPOSITE_YES_STRING]))
        self.tv.setItemDelegateForColumn(4, ComboBoxDelegate(self, cfg.DPI_OPTIONS))
        self.tv.setItemDelegateForColumn(5,ComboBoxDelegate(self, [cfg.THRESHOLD_TYPE_GRAYSCALE_STRING,cfg.THRESHOLD_TYPE_COLOR_STRING]))
        self.tv.setColumnWidth(5,100)

        self.selection_changed()

        # Your code ends here
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
            newCards.append(c)
        rows = self.tm.addCards(newCards)
        self.passDataChanged.emit()
        indexes = [self.tm.index(r, 0) for r in rows]
        mode = QItemSelectionModel.Select | QItemSelectionModel.Rows
        [self.tv.selectionModel().select(index, mode) for index in indexes]
        
    @pyqtSlot()
    def remove_cards(self):
        sel = self.ui.tableView.selectionModel().selectedRows()
        for index in sel:
            if self.tm.card_list[index.row()].has_image:
                if not self._are_you_sure('One or more selected cards have image data which will be erased. Continue?'): 
                    return
                else:
                    break
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
                if not self._are_you_sure(f'{card.name} already has image data, overwrite?'):
                    return
                else:
                    break
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
        if card.has_image:
            if not self._are_you_sure(f'{card.name} already has image data, overwrite?'):
                return
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
        e.applied.connect(self.update_table)
        #Start Loop
        e.exec_()
    
    def on_applied(self):
        self.applied.emit()
        self.accept()
        self.close()
    
    def _are_you_sure(self, message):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setText("Are You Sure?")
        msg.setInformativeText(message)
        #msg.setWindowTitle("MessageBox demo")
        #msg.setDetailedText("The details are as follows:")
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        result = msg.exec()
        return result == QMessageBox.Yes

class ComboBoxDelegate(QItemDelegate):
    def __init__(self, owner, itemList):
        QItemDelegate.__init__(self, owner)
        self.itemList = itemList
    
    def createEditor(self, parent, option, index):
        editor = QComboBox(parent)
        editor.addItems(self.itemList)
        return editor
    
    def setEditorData(self, comboBox, index):
        comboBox.setCurrentIndex(int(index.model().data(index, role=Qt.EditRole)))
        
    def setModelData(self, comboBox, model, index):
        model.setData(index, comboBox.currentIndex(), Qt.EditRole)
        
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

    def headerData(self, column, orientation, role=Qt.DisplayRole):
        if role!=Qt.DisplayRole:
            return QVariant()
        if orientation==Qt.Horizontal:
            if column == 0:
                return QVariant('Name')
            elif column == 1:
                return QVariant('Location')
            elif column == 2:
                return QVariant('Has Image?')
            elif column == 3:
                return QVariant('In Composite')
            elif column == 4:
                return QVariant('Px Per In')
            elif column == 5:
                return QVariant('Thresh. Method')
            return QVariant()

    def data(self, index, role: Qt.DisplayRole):
        i = index.row()
        j = index.column()
        card: SprayCard = self.card_list[i]
        if role == Qt.TextAlignmentRole:
            return Qt.AlignCenter
        elif role == Qt.CheckStateRole:
            if j == 2:
                if card.has_image == 1:
                    return Qt.Checked
                else:
                    return Qt.Unchecked
            elif j == 3:
                if card.include_in_composite == 1:
                    return Qt.Checked
                else:
                    return Qt.Unchecked
            else: return QVariant()
        elif role == Qt.DisplayRole or role == Qt.EditRole:
            if j == 0:
                # Name
                return card.name
            elif j == 1:
                # Location
                return card.location
            elif j == 2:
                # Has Image?
                if card.has_image:
                    return cfg.HAS_IMAGE_YES_STRING
                else:
                    return cfg.HAS_IMAGE_NO_STRING
            elif j == 3:
                # Include in Composite?
                if role == Qt.DisplayRole:
                    if card.include_in_composite:
                        return cfg.INCLUDE_IN_COMPOSITE_YES_STRING
                    else:
                        return cfg.INCLUDE_IN_COMPOSITE_NO_STRING
                elif role == Qt.EditRole:
                    return card.include_in_composite
            elif j == 4:
                # PPI
                if role == Qt.DisplayRole:
                    return str(card.dpi)
                elif role == Qt.EditRole:
                    return cfg.DPI_OPTIONS.index(str(card.dpi))
            elif j == 5:
                # Thresh Type
                if role == Qt.DisplayRole:
                    if card.threshold_type == cfg.THRESHOLD_TYPE_GRAYSCALE:
                        return cfg.THRESHOLD_TYPE_GRAYSCALE_STRING
                    elif card.threshold_type == cfg.THRESHOLD_TYPE_COLOR:
                        return cfg.THRESHOLD_TYPE_COLOR_STRING
                elif role == Qt.EditRole:
                    return card.threshold_type 
        else: return QVariant()
    
    def setData(self, index, value, role = Qt.EditRole) -> bool:
        i = index.row()
        j = index.column()
        if value is None or not role == Qt.EditRole:
            return False
        card = self.card_list[i]
        if j == 0:
            #Name
            card.name = value
            self.dataChanged.emit(index,index)
            return True
        elif j == 1:
            #Location
            try:
                float(value)
            except ValueError:
                print('Attempt to set a non-numeric card location')
                return False
            card.location = value
            self.dataChanged.emit(index,index)
            return True 
        elif j == 2:
            return True
        elif j == 3:
            # Include In Composite
            card.include_in_composite = value
            self.dataChanged.emit(index,index)
            return True
        elif j == 4:
            # PPI
            card.dpi = int(cfg.DPI_OPTIONS[value])
            self.dataChanged.emit(index,index)
            return True
        elif j == 5:
            # Threshold Type
            card.threshold_type = value
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
        '''rows = []
        for index in selection:
            rows.append(index.row())'''
        for index in reversed(selection):
            row = index.row()
            #print(row)
            self.beginRemoveRows(QModelIndex(), row, row)
            self.card_list.pop(row)
            self.endRemoveRows()

    def flags(self, index):
        if not index.isValid():
            return None
        if index.column() == 2:
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable
        else:
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = CardManager()
    sys.exit(app.exec_())
