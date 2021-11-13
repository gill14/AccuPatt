from accupatt.windows.loadCards import LoadCards
import accupatt.config as cfg
from accupatt.windows.editThreshold import EditThreshold
from PyQt5.QtWidgets import QAbstractItemView, QApplication, QComboBox, QFileDialog, QItemDelegate, QListWidgetItem, QStyle, QStyleOptionComboBox
from PyQt5.QtCore import QAbstractTableModel, QModelIndex, QVariant, Qt, QSettings, pyqtSignal
from PyQt5 import uic

import os, sys, copy

from accupatt.models.sprayCard import SprayCard

Ui_Form, baseclass = uic.loadUiType(os.path.join(os.getcwd(), 'accupatt', 'windows', 'ui', 'editCardList.ui'))

defined_sets = {
    'standard_flyin': {
        'name': 'Standard Fly-In',
        'cards': ['L-32', 'L-24', 'L-16', 'L-8', 'Center', 'R-8', 'R-16', 'R-24', 'R-32']
    }
}

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

    def rowCount(self, parent: QModelIndex()) -> int:
        return len(self.card_list)

    def columnCount(self, parent: QModelIndex()) -> int:
        return 5

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
                return QVariant('Thresh. Method')
            return QVariant()

    def data(self, index, role: Qt.DisplayRole):
        i = index.row()
        j = index.column()
        if role == Qt.TextAlignmentRole:
            return Qt.AlignCenter
        elif role is Qt.CheckStateRole:
            if j == 2:
                if self.card_list[i].filepath != '':
                    return Qt.Checked
                else:
                    return Qt.Unchecked
            else: return QVariant()
        elif role == Qt.DisplayRole or role == Qt.EditRole:
            if j == 0:
                # Name
                return self.card_list[i].name
            elif j == 1:
                # Location
                return self.card_list[i].location
            elif j == 2:
                # Has Image?
                if role == Qt.DisplayRole:
                    if self.card_list[i].has_image == cfg.HAS_IMAGE_NO:
                        return cfg.HAS_IMAGE_NO_STRING
                    elif self.card_list[i].has_image == cfg.HAS_IMAGE_YES:
                        return cfg.HAS_IMAGE_YES_STRING
                elif role == Qt.EditRole:
                    return self.card_list[i].has_image
                #return self.card_list[i].has_image
            elif j == 3:
                # Include in Composite?
                if role == Qt.DisplayRole:
                    if self.card_list[i].include_in_composite == cfg.INCLUDE_IN_COMPOSITE_NO:
                        return cfg.INCLUDE_IN_COMPOSITE_NO_STRING
                    elif self.card_list[i].include_in_composite == cfg.INCLUDE_IN_COMPOSITE_YES:
                        return cfg.INCLUDE_IN_COMPOSITE_YES_STRING
                elif role == Qt.EditRole:
                    return self.card_list[i].include_in_composite
            elif j == 4:
                # Thresh Type
                if role == Qt.DisplayRole:
                    if self.card_list[i].threshold_type == cfg.THRESHOLD_TYPE_GRAYSCALE:
                        return cfg.THRESHOLD_TYPE_GRAYSCALE_STRING
                    elif self.card_list[i].threshold_type == cfg.THRESHOLD_TYPE_COLOR:
                        return cfg.THRESHOLD_TYPE_COLOR_STRING
                elif role == Qt.EditRole:
                    return self.card_list[i].threshold_type 
        else: return QVariant()
    
    def setData(self, index, value, role = Qt.EditRole) -> bool:
        i = index.row()
        j = index.column()
        if value is None or not role == Qt.EditRole:
            return False
        if j == 0:
            #Name
            self.card_list[i].name = value
            self.dataChanged.emit(index,index)
            return True
        elif j == 1:
            #Location
            try:
                float(value)
            except ValueError:
                print('Attempt to set a non-numeric card location')
                return False
            self.card_list[i].location = value
            self.dataChanged.emit(index,index)
            return True 
        elif j == 2:
            # Has Image
            self.card_list[i].has_image = value
            self.dataChanged.emit(index,index)
        elif j == 3:
            # Include In Composite
            self.card_list[i].include_in_composite = value
            self.dataChanged.emit(index,index)
        elif j == 4:
            # Threshold Type
            self.card_list[i].threshold_type = value
            self.dataChanged.emit(index,index)
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

    def flags(self, index):
        if not index.isValid():
            return None
        if index.column() == 2:
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable
        else:
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable

class EditCardList(baseclass):

    applied = pyqtSignal()

    def __init__(self, passData=None):
        super().__init__()
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        # Your code will go here

        self.passData_OG = passData
        self.spray_cards = copy.copy(passData.spray_cards)

        #Load in Settings
        self.settings = QSettings('BG Application Consulting','AccuPatt')
       
       #Load in defined sets to combobox
        for key,value in defined_sets.items():
           self.ui.comboBox.addItem(value['name'])

        self.ui.buttonAddSet.clicked.connect(self.add_cards)
        self.ui.buttonAddCard.clicked.connect(self.add_card)

        self.ui.buttonUp.clicked.connect(self.shift_up)
        self.ui.buttonDown.clicked.connect(self.shift_down)

        #Testing TableView
        self.tm = CardTable(self)
        self.tm.loadCards(self.spray_cards)
        self.ui.tableView.setModel(self.tm)
        self.ui.tableView.setItemDelegateForColumn(3,ComboBoxDelegate(self, [cfg.INCLUDE_IN_COMPOSITE_NO_STRING, cfg.INCLUDE_IN_COMPOSITE_YES_STRING]))
        self.ui.tableView.setItemDelegateForColumn(4,ComboBoxDelegate(self, [cfg.THRESHOLD_TYPE_GRAYSCALE_STRING,cfg.THRESHOLD_TYPE_COLOR_STRING]))
        self.ui.tableView.setColumnWidth(4,100)
        
        #Right side menu
        self.ui.buttonSelectFile.clicked.connect(self.select_file)
        self.ui.buttonSetROIs.clicked.connect(self.editROIs)

        #ButtonBox
        self.ui.buttonBox.accepted.connect(self.on_applied)
        self.ui.buttonBox.rejected.connect(self.reject)

        

        # Your code ends here
        self.show()

    def shift_up(self):
        self.tm.shiftRows(self.ui.tableView.selectionModel().selectedRows(), moveUp=True)

    def shift_down(self):
        self.tm.shiftRows(self.ui.tableView.selectionModel().selectedRows(), moveUp=False)

    def add_card(self, addSet=False):
        pass

    def add_cards(self):
        pass
    
    def select_file(self):
        fname, filter_ = QFileDialog.getOpenFileName(self, 'Open file', 'home', "Image files (*.png)")
        self.ui.labelFile.setText(fname)
        
    def editROIs(self):
        #Create popup and send current appInfo vals to popup
        e = LoadCards(self.ui.labelFile.text(), self.ui.tableView.selectionModel().selectedRows())
        #Connect Slot to retrieve Vals back from popup
        e.applied.connect()
        #Start Loop
        e.exec_()

    def on_applied(self):
        self.passData_OG.spray_cards = self.spray_cards
        #Notify requestor
        self.applied.emit()
        self.accept

    def on_rejected(self):
        self.reject


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = EditCardList()
    sys.exit(app.exec_())
