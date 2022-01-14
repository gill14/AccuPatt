import sys, os
from typing import List

from PyQt5.QtWidgets import QApplication, QFileDialog, QMessageBox, QTableView
from PyQt5.QtCore import QAbstractTableModel, QModelIndex, QVariant, pyqtSignal, Qt
from PyQt5 import uic
from numpy.lib.function_base import select
import pandas as pd
import copy

from accupatt.models.passData import Pass

Ui_Form, baseclass = uic.loadUiType(os.path.join(os.getcwd(), 'accupatt', 'windows', 'ui', 'passManager.ui'))

class PassManager(baseclass):

    applied = pyqtSignal(list)

    def __init__(self, passes = None, parent = None):
        super().__init__(parent = parent)
        # Your code will go here
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        self.passes = []
        if passes is not None:
            self.passes = passes
            
        self.populateList(copy.copy(passes))

        self.ui.button_new_pass.clicked.connect(self.newPass)
        self.ui.button_delete_pass.clicked.connect(self.deletePass)

        self.ui.buttonBox.accepted.connect(self.on_applied)
        self.ui.buttonBox.rejected.connect(self.reject)

        # Your code ends here
        self.show()

    def populateList(self, passes):
        self.tm = PassTable(passes, self)
        self.ui.tableView.setModel(self.tm)
    
    def newPass(self):
        self.tm.addPass()
    
    def deletePass(self):
        row = self.ui.tableView.selectedIndexes()[0].row()
        p: Pass = self.tm.pass_list[row]
        if not p.data.empty:
            if self._are_you_sure(f'{p.name} constains aquired data which will be permanently erased.'):
                self.tm.removePass(self.ui.tableView.selectedIndexes())

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

    def on_applied(self):
        self.passes = copy.copy(self.tm.pass_list)
        #Notify Requestor
        self.applied.emit(self.passes)
        self.accept()
        self.close()

class PassTable(QAbstractTableModel):
    def __init__(self, pass_list, parent=None, *args):
        super(PassTable, self).__init__()
        self.pass_list = None
        if pass_list is not None:
            self.pass_list = pass_list
        
    def rowCount(self, parent: QModelIndex()) -> int:
        return len(self.pass_list)
    
    def columnCount(self, parent: QModelIndex()) -> int:
        return 5
    
    def headerData(self, column, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return QVariant()
        if orientation == Qt.Horizontal:
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
            return QVariant()
    
    def data(self, index, role: Qt.DisplayRole):
        i = index.row()
        j = index.column()
        p: Pass = self.pass_list[i]
        if role == Qt.TextAlignmentRole:
            return Qt.AlignCenter
        elif role == Qt.CheckStateRole:
            if j == 1:
                if not p.data.empty:
                    return Qt.Checked
                else:
                    return Qt.Unchecked
            else: return QVariant()
        elif role == Qt.DisplayRole or role == Qt.EditRole:
            if j == 0:
                return p.name
            elif j == 2:
                return p.trim_l
            elif j == 3:
                return p.trim_r
            elif j == 4:
                return p.trim_v
        else: return QVariant()
        
    def setData(self, index, value, role = Qt.EditRole) -> bool:
        i = index.row()
        j = index.column()
        p: Pass = self.pass_list[i]
        if value is None or not role == Qt.EditRole:
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
                print('L and R Trim must be integers')
                return False
            p.trim_l = value
            self.dataChanged.emit(index,index)
            return True 
        elif j == 3:
            try:
                int(value)
            except ValueError:
                print('L and R Trim must be integers')
                return False
            p.trim_r = value
            self.dataChanged.emit(index,index)
        elif j == 4:
            try:
                float(value)
            except ValueError:
                print('V Trim must be a number')
                return False
            p.trim_v = value
            self.dataChanged.emit(index,index)
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
        if index.column() == 1:
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable
        else:
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable

