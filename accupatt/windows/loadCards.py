from PyQt5.QtWidgets import QApplication, QListWidgetItem, QFileDialog, QAbstractItemView
from PyQt5.QtCore import Qt, QSettings, pyqtSignal
from PyQt5 import uic

import os, sys
import cv2

from accupatt.models.sprayCard import SprayCard

dpi_options = ['300','600','1200','2400']

Ui_Form, baseclass = uic.loadUiType(os.path.join(os.getcwd(), 'accupatt', 'windows', 'ui', 'loadCards.ui'))

class LoadCards(baseclass):

    applied = pyqtSignal()

    def __init__(self, file, card_names):
        super().__init__()
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        # Your code will go here
        
        img_path='/Users/gill14/Desktop/L-8.png'
        # Read image
        img = cv2.imread(img_path)
        img = cv2.resize(img, dsize=None, fx=0.1, fy=0.1, interpolation=cv2.INTER_AREA)
        
        #cv2.imshow('image', img)

        self.ui.buttonBox.accepted.connect(self.on_applied)
        self.ui.buttonBox.rejected.connect(self.reject)

        # Your code ends here
        self.show()
        self.ui.imageWidget.updateSprayCardView(img)
    
    
    

    def on_applied(self):
        
        #Notify requestor
        self.applied.emit()
        self.accept

    def on_rejected(self):
        self.reject


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = LoadCards()
    sys.exit(app.exec_())