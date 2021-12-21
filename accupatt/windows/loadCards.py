from PyQt5.QtWidgets import QApplication, QGraphicsView, QListWidgetItem, QFileDialog, QAbstractItemView
from PyQt5.QtCore import Qt, QSettings, pyqtSignal
from PyQt5 import uic

import os, sys
import cv2
import numpy as np
import pyqtgraph as pg
from pyqtgraph.functions import mkPen
from pyqtgraph.graphicsItems.ImageItem import ImageItem

dpi_options = ['300','600','1200','2400']

Ui_Form, baseclass = uic.loadUiType(os.path.join(os.getcwd(), 'accupatt', 'windows', 'ui', 'loadCards.ui'))

class LoadCards(baseclass):

    applied = pyqtSignal()

    def __init__(self, file, card_names):
        super().__init__()
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        # Your code will go here
        
        # setting configuration options
        pg.setConfigOptions(antialias=True)
 
        # creating image view view object
        imv = self.ui.imageWidget
 
        img: ImageItem = pg.QtGui.QGraphicsPixmapItem(pg.QtGui.QPixmap(file))
        imv.addItem(img)

        # depending on your preference, you probably want to invert the image:
        img.scale(1, -1)
        rois = self.find_rois(file)
        for roi in rois:
            print('count')
            pg.LabelItem(text='test',parent=roi, size='200pt', color='m')
            roi.setParentItem(img)
        # OR invert the entire view:
        #imv.invertY(True)  # make sure ROI is drawn above image


        self.ui.buttonBox.accepted.connect(self.on_applied)
        self.ui.buttonBox.rejected.connect(self.reject)

        # Your code ends here
        self.show()
    
    def find_rois(self, image_file):
        img = cv2.imread(image_file)
        img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _,img_thresh = cv2.threshold(img_gray,0,255,cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)
        #cv2.imshow('thresh',img_thresh)
        # Use img_thresh to find contours
        contours, _ = cv2.findContours(img_thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        
        rois = []
        for i, c in enumerate(contours):
            # Check if in bounds
            x, y, w, h = cv2.boundingRect(c)
            # If contour is below the min pixel size, fail
            if cv2.contourArea(c) < 5000:
                continue
            # Check if contour is entire image
            if w >=img.shape[1]-1 and h >= img.shape[0]-1:
                continue
            # If contour touches edge, fail
            if x <= 0 or y <= 0 or (x+w) >= img.shape[1]-1 or (y+h) >= img.shape[0]-1:
                continue
            rois.append(pg.RectROI([x,y],[w,h],pen=mkPen('m',width=3),hoverPen=mkPen('r',width=5),handlePen=mkPen('m',width=3),removable=True, centered=True, sideScalers=True))
            
        return rois

    def on_applied(self):
        
        #Notify requestor
        self.applied.emit()
        self.accept

    def on_rejected(self):
        self.reject


if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    sys.exit(app.exec_())