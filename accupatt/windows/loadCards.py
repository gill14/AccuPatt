from PyQt5.QtWidgets import QApplication, QListWidgetItem, QFileDialog, QAbstractItemView
from PyQt5.QtCore import Qt, QSettings, pyqtSignal
from PyQt5 import uic

import os, sys, copy

from accupatt.models.sprayCard import SprayCard

Ui_Form, baseclass = uic.loadUiType(os.path.join(os.getcwd(), 'accupatt', 'windows', 'ui', 'loadCards.ui'))

class LoadCards(baseclass):

    applied = pyqtSignal()

    def __init__(self, passData=None):
        super().__init__()
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        # Your code will go here

        self.passData_OG = passData
        self.spray_cards = copy.deepcopy(passData.spray_cards)

        #Load in Settings
        self.settings = QSettings('BG Application Consulting','AccuPatt')
       
       #Card List to ListWidget
        lw = self.ui.listWidget
        for card in self.spray_cards:
            item = QListWidgetItem(card.name)
            lw.addItem(item)
            if card.filepath == None:
                item.setCheckState(Qt.Unchecked)
            else:
                item.setCheckState(Qt.Checked)
            item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)

        self.ui.buttonSelectFile.clicked.connect(self.select_file)
        self.ui.checkBoxSplit.clicked[bool].connect(self.split)
        self.ui.listWidget.selectionModel().selectionChanged.connect(self.selection_changed)

        # Your code ends here
        self.show()

    def select_file(self):
        fname, filter_ = QFileDialog.getOpenFileName(self, 'Open file', 'home', "Image files (*.png)")
        self.ui.labelFile.setText(fname)

    def split(self, isSplit):
        if isSplit:
            self.ui.listWidget.setSelectionMode(QAbstractItemView.ExtendedSelection)
        else:
            self.ui.listWidget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.ui.groupBox3.setEnabled(isSplit)

    def selection_changed(self):
        self.ui.labelTargetQuantity.setText('Target Quantity: '+str(len(self.ui.listWidget.selectedItems())))

    def on_applied(self):
        #Notify requestor
        self.applied.emit()
        self.accept

    def on_rejected(self):
        self.reject


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = EditCardList()
    sys.exit(app.exec_())