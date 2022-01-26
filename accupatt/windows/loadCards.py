import operator
import os

import accupatt.config as cfg
import cv2
import numpy as np
import pyqtgraph as pg
from accupatt.models.sprayCard import SprayCard
from PyQt6 import uic
from PyQt6.QtCore import QSettings, Qt, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QImageReader, QPixmap
from PyQt6.QtWidgets import QGraphicsPixmapItem
from pyqtgraph.functions import mkPen

orientation_options = ['Horizontal','Vertical']
order_options = ['Increasing','Decreasing']
scale_options = ['10%','20%','30%','40%','50%','60%','70%','80%','90%','100%']

Ui_Form, baseclass = uic.loadUiType(os.path.join(os.getcwd(), 'resources', 'loadCards.ui'))

class LoadCards(baseclass):

    applied = pyqtSignal()

    def __init__(self, image_file, card_list, parent=None):
        super().__init__(parent=parent)
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        
        #Import Settings
        self.settings = QSettings('accupatt','AccuPatt')
        self.dpi = self.settings.value('image_dpi', defaultValue='600', type=str)
        self.orientation = self.settings.value('roi_acquisition_orientation', defaultValue=orientation_options[0], type=str)
        self.order = self.settings.value('roi_acquisition_order', defaultValue=order_options[0], type=str)
        self.scale = self.settings.value('roi_scale', defaultValue='70%', type=str)
        
        # Populate controls with static options, selections from settings
        self.ui.comboBoxDPI.addItems(cfg.DPI_OPTIONS)
        self.ui.comboBoxDPI.setCurrentIndex(cfg.DPI_OPTIONS.index(self.dpi))
        self.ui.comboBoxOrientation.addItems(orientation_options)
        self.ui.comboBoxOrientation.setCurrentIndex(orientation_options.index(self.orientation))
        self.ui.comboBoxOrder.addItems(order_options)
        self.ui.comboBoxOrder.setCurrentIndex(order_options.index(self.order))
        self.ui.comboBoxScale.addItems(scale_options)
        self.ui.comboBoxScale.setCurrentIndex(scale_options.index(self.scale))
        
        #List of cards
        self.card_list = card_list
        for card in self.card_list:
            self.ui.listWidget.addItem(card.name)
        
        # Slots for controls
        self.ui.comboBoxDPI.currentIndexChanged[int].connect(self.dpi_changed)
        self.ui.comboBoxOrientation.currentIndexChanged[int].connect(self.orientation_changed)
        self.ui.comboBoxOrder.currentIndexChanged[int].connect(self.order_changed)
        self.ui.comboBoxScale.currentIndexChanged[int].connect(self.scale_changed)
        self.ui.buttonBox.accepted.connect(self.on_applied)
        self.ui.buttonBox.rejected.connect(self.on_rejected)
        
        # Set pyqtgraph global options
        pg.setConfigOptions(antialias=True)
        
        # Lock pixels as square in image view to prevent distortion
        self.ui.plotWidget.getViewBox().setAspectLocked()
        
        # Load Image from File, invert vertically, add it to plotWidget
        self.image_file = image_file
        image_reader = QImageReader(image_file)
        size_og = image_reader.size()
        size_mod = size_og
        if size_og.width() * size_og.height() > 33000000:
            scale = 4000 / size_mod.width()
            size_mod = size_mod.scaled(int(size_mod.width()*scale),int(size_mod.height()*scale),Qt.AspectRatioMode.IgnoreAspectRatio)
        image_reader.setScaledSize(size_mod)
        self.img = image_reader.read()
        self.img = self.img.scaled(size_og.width(),size_og.height())
        self.img_pixmap = QPixmap.fromImage(self.img)
        
        self.img = QGraphicsPixmapItem(self.img_pixmap)
        
        self.ui.plotWidget.addItem(self.img)
        self.ui.plotWidget.getPlotItem().invertY(True)
       
        # Only search image for ROIs once
        self.roi_rectangles = self._find_rois(image_file)
        # Run initial drawing of ROIs
        self.rois = []
        self.draw_rois()
        

        # Your code ends here
        self.show()
        self.show_image_characteristics()
        
    def show_image_characteristics(self):
        dpi = int(self.dpi)
        h_px = self.img.pixmap().height()
        w_px = self.img.pixmap().width()
        self.ui.label_size.setText(f'{(w_px/dpi):.1f}"x{(h_px/dpi):.1f}"')
        self.ui.label_pixel_area.setText(f'{int(25400 / dpi)} microns')
    
    def draw_rois(self):
        # Order card rectangles based on selected options
        self._sort_rois(self.orientation, self.order)
        # Clear any previous rois from ViewBox
        for r in self.rois:
            self.ui.plotWidget.getViewBox().removeItem(r)
        # Add rois to image with labels
        self.rois = []
        for i, r in enumerate(self.roi_rectangles):
            # Only draw the ROI if supplied list supports it
            if i < self.ui.listWidget.count():
                x, y, w, h = r
                roi = pg.RectROI([x, y],[w, h],
                            pen=mkPen('m',width=3),
                            hoverPen=mkPen('r',width=5),
                            handlePen=mkPen('r',width=3),
                            handleHoverPen=mkPen('r',width=5),
                            removable=True, centered=True, sideScalers=True)
                roi.scale(s=float(self.scale[0:-1])/100,center=[0.5,0.5])
                text = self.card_list[i].name
                label = pg.TextItem(text=text, color='m')
                label.setParentItem(roi)
                roi.setParentItem(self.img)
                roi.sigRemoveRequested.connect(self.remove_roi)
                self.rois.append(roi)
         
    @pyqtSlot(int)
    def dpi_changed(self, newIndex):
        self.dpi = cfg.DPI_OPTIONS[newIndex]
        self.show_image_characteristics()
            
    @pyqtSlot(int)
    def orientation_changed(self, newIndex):
        self.orientation = orientation_options[newIndex]
        self.draw_rois()
       
    @pyqtSlot(int)
    def order_changed(self, newIndex):
        self.order = order_options[newIndex]
        self.draw_rois()
        
    @pyqtSlot(int)
    def scale_changed(self, newIndex):
        self.scale = scale_options[newIndex]
        self.draw_rois()
        
    @pyqtSlot(object)
    def remove_roi(self, roi):
        #self.ui.plotWidget.scene().removeItem(roi)
        del self.roi_rectangles[self.rois.index(roi)]
        #self.rois.remove(roi)
        self.draw_rois()
        
    @pyqtSlot()
    def on_applied(self):
        self.settings.setValue('image_dpi', self.ui.comboBoxDPI.currentText())
        self.settings.setValue('roi_acquisition_orientation', self.ui.comboBoxOrientation.currentText())
        self.settings.setValue('roi_acquisition_order', self.ui.comboBoxOrder.currentText())
        self.settings.setValue('roi_scale', self.ui.comboBoxScale.currentText())
        
        for i, roi in enumerate(self.rois):
            roi: pg.RectROI
            x = int(roi.pos()[0])
            y = int(roi.pos()[1])
            w = int(roi.size()[0])
            h = int(roi.size()[1])
            # Use CV to crop image roi
            img = cv2.imread(self.image_file)
            img_crop = img[y:y+h,x:x+w]
            # Save to bytestream
            _, buffer = cv2.imencode('*.png',img_crop)
            # Write to db and update spray card object
            sprayCard: SprayCard = self.card_list[i]
            sprayCard.save_image_to_file(buffer)
            sprayCard.has_image = True
            sprayCard.include_in_composite = True
        
        self.applied.emit()
        self.accept()
        self.close()
     
    @pyqtSlot()    
    def on_rejected(self):
        self.reject()
        self.close()
    
    def _sort_rois(self, orientation, order):
        rois_original = self.roi_rectangles.copy()
        rois_sorted = []
        # Loop through all rois, removing from old list as added to new sorted list
        while len(rois_sorted) < len(self.roi_rectangles):
            # Compute distance from origin for each
            dists_from_origin = []
            for r in rois_original:
                x, y, w, h = r
                dists_from_origin.append(np.sqrt(x**2+y**2))
            # Sort rois by dist to origin, grab one nearest origin
            x1, y1, w1, h1 = [r for _,r in sorted(zip(dists_from_origin,rois_original))][0]
            # Create intermediate list for current row/column of first_roi
            current = []
            for r in rois_original:
                x, y, w, h = r
                # Check if in same row/col as first_roi, if so add to list
                if orientation == 'Horizontal':
                    y_c = y + h/2
                    if y_c >= y1 and y_c <= y1+h1:
                        current.append(r)
                else:
                    x_c = x + w/2
                    if x_c >= x1 and x_c <= x1+w1:
                        current.append(r)
            # Sort current row/col list
            current = sorted(current, key=operator.itemgetter(0 if orientation == 'Horizontal' else 1), reverse=(order=='Decreasing'))
            # Add sorted row/column to either beginning or end of new list
            if order == 'Decreasing':
                rois_sorted[0:0] = current
            else:
                rois_sorted.extend(current)
            # Remove current row/col rois from original list
            rois_original = [r for r in rois_original if r not in current]
        # Once rois_sorted contains all original rois, re-assign the original rois
        self.roi_rectangles = rois_sorted 
    
    def _scale_rois(self, rois, scale):
        rois_scaled = []
        percent = float(scale[0:len(scale)-1])/100
        print(percent)
        for r in rois:
            x, y, w, h = r
            w_scaled = int(w*percent)
            h_scaled = int(h*percent)
            rois_scaled.append((int(x+w_scaled/4),int(y+h_scaled/4),w_scaled,h_scaled))
        return rois_scaled
    
    def _find_rois(self, image_file):
        img = cv2.imread(image_file)
        
        img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _,img_thresh = cv2.threshold(img_gray,0,255,cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)
        #cv2.imshow('thresh',img_thresh)
        # Use img_thresh to find contours
        contours, _ = cv2.findContours(img_thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        
        roi_rectangles = []
        for c in contours:
            # Check if in bounds
            x, y, w, h = cv2.boundingRect(c)
            # If contour is below the min pixel size, fail
            if cv2.contourArea(c) < 5000:
                continue
            # If contour touches edge, fail
            if x <= 0 or y <= 0 or (x+w) >= img.shape[1]-1 or (y+h) >= img.shape[0]-1:
                continue
            roi_rectangles.append((x, y, w, h)) 
        return roi_rectangles
