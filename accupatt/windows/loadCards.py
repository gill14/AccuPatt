from PyQt5.QtWidgets import QApplication, QListWidgetItem, QFileDialog, QAbstractItemView
from PyQt5.QtCore import Qt, QSettings, pyqtSignal
from PyQt5 import uic

import os, sys, copy
from PIL import Image
from PIL.ExifTags import TAGS

from accupatt.models.sprayCard import SprayCard
from accupatt.helpers.fileTools import FileTools

dpi_options = ['300','600','1200','2400']

Ui_Form, baseclass = uic.loadUiType(os.path.join(os.getcwd(), 'accupatt', 'windows', 'ui', 'loadCards.ui'))

class LoadCards(baseclass):

    applied = pyqtSignal()

    def __init__(self, seriesData, passData):
        super().__init__()
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        # Your code will go here
        self.seriesData = seriesData
        self.passData = passData
        self.spray_cards = copy.copy(passData.spray_cards)

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
        self.ui.checkBoxSplit.stateChanged.connect(self.split)
        self.ui.comboBoxResolution.addItems(dpi_options)
        self.ui.listWidget.selectionModel().selectionChanged.connect(self.selection_changed)
        self.ui.groupBox3.setEnabled(False)

        self.ui.checkBoxSplit.setChecked(self.settings.value('load_image_split', defaultValue=False, type=bool))

        self.ui.buttonBox.accepted.connect(self.on_applied)
        self.ui.buttonBox.rejected.connect(self.reject)

        # Your code ends here
        self.show()

    def select_file(self):
        fname, filter_ = QFileDialog.getOpenFileName(self, 'Open file', 'home', "Image files (*.png)")
        self.ui.labelFile.setText(fname)
        #Testing
        exif_table = {}
        image = Image.open(fname)
        info = image.getexif()
        for tag, value in info.items():
            decoded = TAGS.get(tag, tag)
            exif_table[decoded] = value
        print(exif_table)
        res = int(exif_table['XResolution'])
        self.ui.comboBoxResolution.setCurrentText(str(res))

    def split(self, isSplit):
        if isSplit:
            self.ui.listWidget.setSelectionMode(QAbstractItemView.ExtendedSelection)
        else:
            self.ui.listWidget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.ui.groupBox3.setEnabled(isSplit)
        #Update Settings
        self.settings.setValue('load_image_split', isSplit)

    def selection_changed(self):
        self.ui.labelTargetQuantity.setText('Target Quantity: '+str(len(self.ui.listWidget.selectedItems())))

    def on_applied(self):
        #Make a copy to appropirate folder and update SprayCard object
        #Single Card here first, try multi later
        card = self.passData.spray_cards[self.ui.listWidget.currentRow()]
        FileTools.saveImage(src_file=self.ui.labelFile.text(), series_dir=self.seriesData.filePath, pass_data=self.passData, spray_card=card)
        card.dpi = int(self.ui.comboBoxResolution.currentText())
        #Notify requestor
        self.applied.emit()
        self.accept

    def on_rejected(self):
        self.reject


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = LoadCards()
    sys.exit(app.exec_())