from PyQt5.QtWidgets import QApplication, QListWidgetItem
from PyQt5.QtCore import Qt, QSettings, pyqtSignal
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

class EditCardList(baseclass):

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
       
       #Load in defined sets to combobox
        for key,value in defined_sets.items():
           self.ui.comboBox.addItem(value['name'])

        #Card List to ListWidget
        lw = self.ui.listWidgetCards
        for card in self.spray_cards:
            item = QListWidgetItem(card.name)
            lw.addItem(item)
            if card.filepath == None:
                item.setCheckState(Qt.Unchecked)
            else:
                item.setCheckState(Qt.Checked)
            item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsEditable | Qt.ItemIsSelectable)
        lw.itemChanged[QListWidgetItem].connect(self.item_changed)

        self.ui.buttonAddSet.clicked.connect(self.add_cards)
        self.ui.buttonAddCard.clicked.connect(self.add_card)

        self.ui.buttonUp.clicked.connect(self.shift_up)
        

        #ButtonBox
        self.ui.buttonBox.accepted.connect(self.on_applied)
        self.ui.buttonBox.rejected.connect(self.reject)

        

        # Your code ends here
        self.show()

    def item_changed(self, item):
        row = self.ui.listWidgetCards.row(item)
        self.spray_cards[row].name = item.text()

    def shift_up(self):
        lw = self.ui.listWidgetCards
        if lw.count() == 0: return
        #Since items is unordered, must make a sorted list to use
        selection_model = lw.selectionModel()
        sort_list = []
        if selection_model.hasSelection():
            for index in selection_model.selectedRows():
                sort_list.append(index.row())
                #if abutting top, abort
                if index.row() == 0: return
            sort_list = sorted(sort_list)
        #do the shifting
        for row_num in sort_list:
            item = lw.item(row_num)
            #Alter the List
            lw.insertItem(row_num-1,lw.takeItem(row_num))
            #Retain selction
            item.setSelected(True)
            #print(item.text()+' init row='+str(row_num)+' move to row='+str(row_num-1))
            #Alter the actual card list
            self.spray_cards.insert(row_num-1, self.spray_cards.pop(row_num))

    def add_card(self, addSet=False):
        #default to last row
        model = self.ui.listWidgetCards.model()
        row = model.rowCount()
        #if selection, insert below that
        selection_model = self.ui.listWidgetCards.selectionModel()
        if selection_model.hasSelection():
            #find last card in selection
            row_last = 0
            for index in selection_model.selectedRows():
                if index.row() > row_last: row_last = index.row()
            row = row_last + 1
        list = []
        if not addSet:
            #Create a new card
            list.append(SprayCard(name='Card ' + str(row+1)))
        else:
            for key,value in defined_sets.items():
                if value['name'] == self.ui.comboBox.currentText():
                    for card_name in value['cards']:
                        list.append(SprayCard(name=card_name))
        #Now insert list into main list
        self.spray_cards[row:row] = list
        #create an item in listWidget for each card
        for card in list:
            item = QListWidgetItem(card.name)
            self.ui.listWidgetCards.insertItem(row, item)
            item.setCheckState(Qt.Unchecked)
            item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsEditable | Qt.ItemIsSelectable)

    def add_cards(self):
        self.add_card(addSet=True)

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