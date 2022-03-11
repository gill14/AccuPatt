import copy
import os

from accupatt.models.passData import Pass
from PyQt6 import uic
from PyQt6.QtCore import (QAbstractTableModel, QModelIndex, Qt, QVariant,
                          pyqtSignal)
from PyQt6.QtWidgets import QMessageBox

Ui_Form, baseclass = uic.loadUiType(os.path.join(os.getcwd(), 'resources', 'passManager.ui'))

class PassManager(baseclass):

    pass_list_updated = pyqtSignal(list)

    def __init__(self, passes = None, parent = None):
        super().__init__(parent = parent)
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        
        self.populateList(copy.copy(passes))

        self.ui.button_new_pass.clicked.connect(self.newPass)
        self.ui.button_delete_pass.clicked.connect(self.deletePass)

        self.show()

    def populateList(self, passes):
        self.tm = PassTable(passes, self)
        self.ui.tableView.setModel(self.tm)
    
    def newPass(self):
        self.tm.addPass()
    
    def deletePass(self):
        row = self.ui.tableView.selectedIndexes()[0].row()
        p: Pass = self.tm.pass_list[row]
        if not p.data.empty or p.spray_cards:
            msg = QMessageBox.question(self,'Are You Sure?',
                                       f'{p.name} constains aquired data which will be permanently erased.')
            if msg == QMessageBox.StandardButton.No:
                return
        self.tm.removePass(self.ui.tableView.selectedIndexes())

    def accept(self):
        self.pass_list_updated.emit(copy.copy(self.tm.pass_list))
        #Notify Requestor
        super().accept()

class PassTable(QAbstractTableModel):
    def __init__(self, pass_list, parent=None, *args):
        super(PassTable, self).__init__()
        self.pass_list = None
        if pass_list is not None:
            self.pass_list = pass_list
        
    def rowCount(self, parent: QModelIndex()) -> int:
        return len(self.pass_list)
    
    def columnCount(self, parent: QModelIndex()) -> int:
        return 6
    
    def headerData(self, column, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role != Qt.ItemDataRole.DisplayRole:
            return QVariant()
        if orientation == Qt.Orientation.Horizontal:
            if column == 0:
                return QVariant('Name')
            elif column == 1:
                return QVariant('Has String Data')
            elif column == 2:
                return QVariant('Trim Left')
            elif column == 3:
                return QVariant('Trim Right')
            elif column == 4:
                return QVariant('Trim Vertical')
            elif column == 5:
                return QVariant('Has Card Data')
            return QVariant()
    
    def data(self, index, role: Qt.ItemDataRole.DisplayRole):
        i = index.row()
        j = index.column()
        p: Pass = self.pass_list[i]
        if role == Qt.ItemDataRole.TextAlignmentRole:
            return Qt.AlignmentFlag.AlignCenter
        elif role == Qt.ItemDataRole.CheckStateRole:
            if j == 1:
                if not p.data.empty:
                    return Qt.CheckState.Checked
                else:
                    return Qt.CheckState.Unchecked
            elif j == 5:
                if p.spray_cards:
                    return Qt.CheckState.Checked
                else:
                    return Qt.CheckState.Unchecked
            else: return QVariant()
        elif role == Qt.ItemDataRole.DisplayRole or role == Qt.ItemDataRole.EditRole:
            if j == 0:
                return p.name
            elif j == 2:
                return p.trim_l
            elif j == 3:
                return p.trim_r
            elif j == 4:
                return p.trim_v
        else: return QVariant()
        
    def setData(self, index, value, role = Qt.ItemDataRole.EditRole) -> bool:
        i = index.row()
        j = index.column()
        p: Pass = self.pass_list[i]
        if value is None or not role == Qt.ItemDataRole.EditRole:
            return False
        if j == 0:
            p.name = value
            self.dataChanged.emit(index,index)
            return True
        elif j == 1:
            return True 
        elif j == 2:
            try:
                int(value)
            except ValueError:
                return False
            p.trim_l = value
            self.dataChanged.emit(index,index)
            return True 
        elif j == 3:
            try:
                int(value)
            except ValueError:
                return False
            p.trim_r = value
            self.dataChanged.emit(index,index)
        elif j == 4:
            try:
                float(value)
            except ValueError:
                return False
            p.trim_v = value
            self.dataChanged.emit(index,index)
        elif j == 5:
            return True
        return False
        
    def addPass(self):
        #Pass number initialized as length of list
        nextIndex = len(self.pass_list)
        #Double check; if pass num already exists, increment it
        #This only would apply if an earlier pass had been deleted
        p_nums = []
        for p in self.pass_list:
            p_nums.append(p.number)
        if nextIndex <= max(p_nums):
            nextIndex = max(p_nums)+1
        self.beginInsertRows(QModelIndex(), len(self.pass_list), len(self.pass_list))
        #Create pass and add it to listwidget
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
        if index.column() == 1 or index.column() == 5:
            return Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable
        else:
            return Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEditable

