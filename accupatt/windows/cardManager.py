import os

import accupatt.config as cfg
from accupatt.models.passData import Pass
from accupatt.models.seriesData import SeriesData
from accupatt.models.sprayCard import SprayCard
from accupatt.widgets.cardtablewidget import CardTableWidget
from accupatt.widgets.passinfowidget import PassInfoWidget
from accupatt.widgets.singlecardwidget import SingleCardWidget
from accupatt.windows.definedSetManager import DefinedSet, DefinedSetManager, load_defined_sets
from accupatt.windows.editSpreadFactors import EditSpreadFactors
from accupatt.windows.editThreshold import EditThreshold
from accupatt.windows.loadCards import LoadCards, LoadCardsPreBatch
from PyQt6 import uic
from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot
from PyQt6.QtWidgets import QFileDialog, QLabel, QMessageBox, QComboBox, QProgressDialog

Ui_Form, baseclass = uic.loadUiType(os.path.join(os.getcwd(), 'resources', 'cardManager.ui'))

class CardManager(baseclass):

    passDataChanged = pyqtSignal()

    def __init__(self, passData: Pass, seriesData: SeriesData, filepath, parent):
        super().__init__(parent=parent)
        self.ui = Ui_Form()
        self.ui.setupUi(self)
       
        # File path for creating new cards
        self.filepath = filepath
        
        # Pass Info Fields
        self.seriesData = seriesData
        self.passData = passData
        self.ui.labelPass.setText(passData.name)
        self.passInfoWidget: PassInfoWidget = self.ui.passInfoWidget
        self.passInfoWidget.fill_from_pass(passData)
       
        #Load in defined sets to combobox
        self.defined_set_default = cfg.get_card_defined_set()
        self.defined_sets_changed()
        
        self.ui.buttonAddSet.clicked.connect(self.add_cards)
        self.ui.buttonEditSet.clicked.connect(self.edit_sets)
        
        self.ui.comboBoxLoadMethod.addItems(cfg.IMAGE_LOAD_METHODS)
        self.ui.comboBoxLoadMethod.setCurrentText(cfg.get_image_load_method())
        self.ui.buttonLoad.clicked.connect(self.load_cards)
        
        self.ui.buttonProcessOptions.clicked.connect(self.click_process_options)
        self.ui.buttonSpreadFactors.clicked.connect(self.click_spread_factors)
        
        #Populate Table
        self.cardTable: CardTableWidget = self.ui.cardTableWidget
        self.cardTable.passDataChanged.connect(self.passDataChanged.emit)
        self.cardTable.selectionChanged.connect(self.selection_changed)
        self.cardTable.editCard.connect(self._update_image_widgets)
        #self.cardTable.editCardSpreadFactors.connect(self.edit_card_spread_factors)
        self.cardTable.assign_card_list(passData.spray_cards, filepath)

        self.show()

    @pyqtSlot(bool)
    def selection_changed(self, has_selection: bool):
        self.ui.buttonLoad.setEnabled(has_selection)
        self.ui.comboBoxLoadMethod.setEnabled(has_selection)
        self._update_image_widgets()
    
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
        # Copy the cardlist from the chosen defined set
        selectedSet: DefinedSet = self.defined_sets[self.ui.comboBoxDefinedSet.currentIndex()]
        cards = selectedSet.get_fresh_card_list()
        # Set the db filepaths
        for c in cards:
            c.set_filepath(self.filepath)
        # Add cards to tablemodel
        self.cardTable.add_cards_to_table(cards)
    
    @pyqtSlot()
    def click_process_options(self):
        selected_rows = [index.row() for index in self.cardTable.tv.selectionModel().selectedRows()]
        selected_card: SprayCard = self.cardTable.tm.card_list[selected_rows[0]]
        self.edit_card(selected_card)
    
    @pyqtSlot(SprayCard)
    def edit_card(self, sprayCard: SprayCard):
        if sprayCard and sprayCard.has_image:
            #Open the Edit Process Options window for currently selected card
            e = EditThreshold(sprayCard=sprayCard, passData=self.passData, seriesData=self.seriesData, parent=self)
            #Start Loop
            e.exec()
    
    @pyqtSlot()
    def click_spread_factors(self):
        selected_rows = [index.row() for index in self.cardTable.tv.selectionModel().selectedRows()]
        selected_card: SprayCard = self.cardTable.tm.card_list[selected_rows[0]]
        self.edit_card_spread_factors(selected_card)
    
    @pyqtSlot(SprayCard)
    def edit_card_spread_factors(self, sprayCard: SprayCard):
        if sprayCard and sprayCard.has_image:
            #Open the Edit Spread Factors window for currently selected card
            e = EditSpreadFactors(sprayCard=sprayCard, passData=self.passData, seriesData=self.seriesData, parent=self)
            #Start Loop
            e.exec()
    
    @pyqtSlot()
    def update_table(self):
        pass
    
    @pyqtSlot()
    def load_cards(self):
        selected_rows = [index.row() for index in self.cardTable.tv.selectionModel().selectedRows()]
        selected_cards: list[SprayCard] = [self.cardTable.tm.card_list[i] for i in selected_rows]
        # Check if any selected cards have images
        if any([c.has_image for c in selected_cards]):
            cards_with_images = ', '.join([c.name for c in selected_cards if c.has_image])
            s = 's' if len(selected_cards)==1 else ''
            msg = QMessageBox.question(self, 'Are You Sure?',
                                           f'{cards_with_images} contain{s} image data, overwrite?')
            if msg == QMessageBox.StandardButton.No:
                return
        # Use chosen load method
        if self.ui.comboBoxLoadMethod.currentText() == cfg.IMAGE_LOAD_METHODS[0]:
            #Single Images, Single Cards
            self._load_cards_singles(selected_cards)
        else:
            #Single Image, Multiple Cards
            self._load_cards_multi(selected_cards)
    
    def _update_image_widgets(self):
        labelCard: QLabel = self.ui.labelCard
        imageWidget0: SingleCardWidget = self.ui.cardWidget0
        imageWidget1: SingleCardWidget = self.ui.cardWidget1
        imageWidget2: SingleCardWidget = self.ui.cardWidget2
        # Initially clear labels
        labelCard.setText('')
        selected_rows = [index.row() for index in self.cardTable.tv.selectionModel().selectedRows()]
        # Check if a single card (row) is selected
        if len(selected_rows) == 1:
            selected_card: SprayCard = self.cardTable.tm.card_list[selected_rows[0]]
            labelCard.setText(self.passData.name + ' - ' + selected_card.name)
            # Check if single selected card has image data
            if selected_card.has_image:
                self.ui.buttonProcessOptions.setEnabled(True)
                self.ui.buttonSpreadFactors.setEnabled(True)
                imageWidget0.updateSprayCardView(selected_card.image_original())
                cvImg1, cvImg2 = selected_card.images_processed()
                imageWidget1.updateSprayCardView(cvImg1)
                imageWidget2.updateSprayCardView(cvImg2)
                return
        # Clear image views if not explicitly set
        self.ui.buttonProcessOptions.setEnabled(False)
        self.ui.buttonSpreadFactors.setEnabled(False)
        imageWidget0.clearSprayCardView()
        imageWidget1.clearSprayCardView()
        imageWidget2.clearSprayCardView()
            
    
    def _load_cards_singles(self, selected_cards):
        fnames, _ = QFileDialog.getOpenFileNames(self, 'Open file(s)', cfg.get_image_load_dir(), "Image files (*.png *.tif *.tiff)")
        if len(fnames) == 0:
            return
        cfg.set_image_load_dir(os.path.dirname(fnames[0]))
        e = LoadCardsPreBatch(image_files=fnames, card_list=selected_cards, parent=self)
        e.accepted.connect(self.passDataChanged.emit)
        e.exec()
    
    def _load_cards_multi(self, card_list):
        fname, _ = QFileDialog.getOpenFileName(self, 'Open file', cfg.get_image_load_dir(), "Image files (*.png *.tif *.tiff)")
        if fname == '': return
        cfg.set_image_load_dir(os.path.dirname(fname))
        e = LoadCards(image_file=fname, card_list=card_list, parent=self)
        e.accepted.connect(self.passDataChanged.emit)
        e.exec()
        
    def accept(self):
        p = self.passData
        # If any passInfo fields invalid, show user and return to current window
        if len(excepts := self.passInfoWidget.validate_fields(p)) > 0:
            QMessageBox.warning(self, 'Invalid Data', '\n'.join(excepts))
            return
        # If all checks out, process each card and show progress
        prog = QProgressDialog(self)
        prog.setMinimumDuration(0)
        prog.setWindowModality(Qt.WindowModality.WindowModal)
        card_list: list[SprayCard] = self.cardTable.tm.card_list
        for i, card in enumerate(card_list):
            if i==0:
                prog.setRange(0, len(card_list))
            prog.setValue(i)
            prog.setLabelText(f'Processing {card.name} and caching droplet statistics')
            # Process image
            if not card.current:
                card.images_processed()
            # Cache droplet stats
            if not card.stats.current:
                card.stats.set_volumetric_stats()
            
            if prog.wasCanceled():
                return
            
            if i==len(card_list)-1:
                prog.setValue(i+1)
        # If all checks out, update config, notify requestor and close
        cfg.set_card_defined_set(self.ui.comboBoxDefinedSet.currentText())
        cfg.set_image_load_method(self.ui.comboBoxLoadMethod.currentText())
        super().accept()  
