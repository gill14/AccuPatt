import os

import accupatt.config as cfg
from accupatt.models.passData import Pass
from accupatt.models.sprayCard import SprayCard
from accupatt.widgets.cardtablewidget import CardTableWidget
from accupatt.widgets.passinfowidget import PassInfoWidget
from accupatt.windows.definedSetManager import DefinedSet, DefinedSetManager, load_defined_sets
from accupatt.windows.loadCards import LoadCards
from PyQt6 import uic
from PyQt6.QtCore import Qt, QSettings, pyqtSignal, pyqtSlot
from PyQt6.QtWidgets import QFileDialog, QMessageBox, QComboBox

Ui_Form, baseclass = uic.loadUiType(os.path.join(os.getcwd(), 'resources', 'cardManager.ui'))

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
        self.defined_set_default = self.settings.value(cfg._CARD_DEFINED_SET,
                                                defaultValue=cfg.CARD_DEFINED_SET__DEFAULT)
        self.defined_sets_changed()
        
        self.ui.buttonAddSet.clicked.connect(self.add_cards)
        self.ui.buttonEditSet.clicked.connect(self.edit_sets)
        
        self.ui.comboBoxLoadMethod.addItems(cfg.IMAGE_LOAD_METHODS)
        self.ui.comboBoxLoadMethod.setCurrentText(self.settings.value(cfg._IMAGE_LOAD_METHOD, 
                                                                      defaultValue=cfg.IMAGE_LOAD_METHOD__DEFAULT))
        self.ui.buttonLoad.clicked.connect(self.load_cards)
        
        #Populate Table
        self.cardTable: CardTableWidget = self.ui.cardTableWidget
        self.cardTable.passDataChanged.connect(self.passDataChanged.emit)
        self.cardTable.selectionChanged.connect(self.selection_changed)
        self.cardTable.assign_card_list(passData.spray_cards, filepath)

        self.show()

    @pyqtSlot(bool)
    def selection_changed(self, has_selection: bool):
        self.ui.buttonLoad.setEnabled(has_selection)
        self.ui.comboBoxLoadMethod.setEnabled(has_selection)
    
    @pyqtSlot()
    def edit_sets(self):
        #Create popup and send current appInfo vals to popup
        e = DefinedSetManager(parent=self)
        #Connect Slot to retrieve Vals back from popup
        e.accepted.connect(self.defined_sets_changed)
        #Start Loop
        e.exec()
    
    @pyqtSlot()
    def defined_sets_changed(self):
        self.defined_sets = load_defined_sets()
        cb: QComboBox = self.ui.comboBoxDefinedSet
        cb.clear()
        cb.addItems([s.name for s in self.defined_sets])
        cb.setCurrentIndex(cb.findText(self.defined_set_default, Qt.MatchFlag.MatchExactly))
    
    @pyqtSlot()
    def add_cards(self):
        selectedSet: DefinedSet = self.defined_sets[self.ui.comboBoxDefinedSet.currentIndex()]
        self.cardTable.add_cards_to_table(selectedSet.cards)
    
    @pyqtSlot()
    def update_table(self):
        pass
    
    @pyqtSlot()
    def load_cards(self):
        #Check if any selected cards have images
        selection = self.cardTable.ui.tableView.selectionModel().selectedRows()
        already_have_image = [card.name for card in self.cardTable.tm.card_list if card.has_image]
        if already_have_image:
            msg = QMessageBox.question(self, 'Are You Sure?',
                                           f'{already_have_image} contain image data, overwrite?')
            if msg == QMessageBox.StandardButton.No:
                return
        # Use chosen load method
        method = self.ui.comboBoxLoadMethod.currentText()
        if method == cfg.IMAGE_LOAD_METHODS[0]:
            #Single Images, Single Cards
            self._load_cards_singles(selection)
        else:
            #Single Image, Multiple Cards
            self._load_cards_multi(selection)
        
    
    def _load_cards_singles(self, selection):
        # TODO: migrate to singles batch method
        card: SprayCard = self.cardTable.tm.card_list[selection[0].row()]
        fname, _ = QFileDialog.getOpenFileName(self, 'Open file', 'home', "Image files (*.png)")
        with open(fname, 'rb') as file:
            binary_data = file.read()  
        card.save_image_to_file(image=binary_data)
        card.has_image = True
        card.include_in_composite = True
    
    def _load_cards_multi(self, selection):
        fname, _ = QFileDialog.getOpenFileName(self, 'Open file', 'home', "Image files (*.png)")
        if fname == '': return
        card_list = []
        for row in selection:
            card_list.append(self.cardTable.tm.card_list[row.row()])
        #Create popup and send current appInfo vals to popup
        e = LoadCards(image_file=fname, card_list=card_list, parent=self)
        #Connect Slot to retrieve Vals back from popup
        e.accepted.connect(self.passDataChanged.emit)
        #Start Loop
        e.exec()
        
    def accept(self):
        p = self.passData
        # If any passInfo fields invalid, show user and return to current window
        if len(excepts := self.passInfoWidget.validate_fields(p)) > 0:
            QMessageBox.warning(self, 'Invalid Data', '\n'.join(excepts))
            return
        self.settings.setValue(cfg._CARD_DEFINED_SET, self.ui.comboBoxDefinedSet.currentText())
        self.settings.setValue(cfg._IMAGE_LOAD_METHOD, self.ui.comboBoxLoadMethod.currentText())
        # If all checks out, notify requestor and close
        super().accept()  
