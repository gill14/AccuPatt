import operator
import os

import accupatt.config as cfg
import cv2
import numpy as np
import pyqtgraph as pg
from accupatt.models.sprayCard import SprayCard
from PIL import Image
from PyQt6 import uic
from PyQt6.QtGui import QImageReader, QPixmap
from PyQt6.QtCore import QSettings, Qt, pyqtSignal, pyqtSlot
from PyQt6.QtWidgets import QApplication, QCheckBox, QGraphicsPixmapItem, QListWidget, QProgressDialog
from pyqtgraph.functions import mkPen

Ui_Form, baseclass = uic.loadUiType(os.path.join(os.getcwd(), 'resources', 'loadCards.ui'))
Ui_Form_Pre, baseclass_pre = uic.loadUiType(os.path.join(os.getcwd(), 'resources', 'loadCardsPreBatch.ui'))

class LoadCards(baseclass):

    applied = pyqtSignal()

    def __init__(self, image_file: str, card_list: list[SprayCard], parent=None):
        super().__init__(parent=parent)
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        
        #Import Settings
        self.settings = QSettings()
        self.dpi = self.settings.value(cfg._DPI, defaultValue=cfg.DPI__DEFAULT, type=int)
        self.orientation = self.settings.value(cfg._ROI_ACQUISITION_ORIENTATION, defaultValue=cfg.ROI_ACQUISITION_ORIENTATION__DEFAULT, type=str)
        self.order = self.settings.value(cfg._ROI_ACQUISITION_ORDER, defaultValue=cfg.ROI_ACQUISITION_ORDER__DEFAULT, type=str)
        # for other beta users temp
        if type(self.settings.value(cfg._ROI_SCALE, defaultValue=cfg.ROI_SCALE__DEFAULT)) is str:
            self.settings.setValue(cfg._ROI_SCALE, cfg.ROI_SCALE__DEFAULT)
        self.scale = self.settings.value(cfg._ROI_SCALE, defaultValue=cfg.ROI_SCALE__DEFAULT, type=int)
        
        # Populate controls with static options, selections from settings
        self.ui.comboBoxDPI.addItems([str(dpi) for dpi in cfg.DPI_OPTIONS])
        self.ui.comboBoxDPI.setCurrentIndex(cfg.DPI_OPTIONS.index(self.dpi))
        self.ui.comboBoxOrientation.addItems(cfg.ROI_ACQUISITION_ORIENTATIONS)
        self.ui.comboBoxOrientation.setCurrentIndex(cfg.ROI_ACQUISITION_ORIENTATIONS.index(self.orientation))
        self.ui.comboBoxOrder.addItems(cfg.ROI_ACQUISITION_ORDERS)
        self.ui.comboBoxOrder.setCurrentIndex(cfg.ROI_ACQUISITION_ORDERS.index(self.order))
        self.ui.comboBoxScale.addItems([f'{s}%' for s in cfg.ROI_SCALES])
        self.ui.comboBoxScale.setCurrentIndex(cfg.ROI_SCALES.index(self.scale))
        
        #Image File
        self.image_file = image_file
        
        #List of cards
        self.card_list = card_list
        
        # Slots for controls
        self.ui.comboBoxDPI.currentIndexChanged[int].connect(self.dpi_changed)
        self.ui.comboBoxOrientation.currentIndexChanged[int].connect(self.orientation_changed)
        self.ui.comboBoxOrder.currentIndexChanged[int].connect(self.order_changed)
        self.ui.comboBoxScale.currentIndexChanged[int].connect(self.scale_changed)
        
        #self.ui.buttonAddCard.clicked.connect(self.clickDraw)
        
        # Set pyqtgraph global options
        pg.setConfigOptions(antialias=True)
        
        # Lock pixels as square in image view to prevent distortion
        self.ui.plotWidget.getViewBox().setAspectLocked()
       
        self.plot_image()
        
        self.show()
        self.show_image_characteristics()
    
    def plot_image(self):
        # Load Image from File, invert vertically, add it to plotWidget
        image_reader = QImageReader(self.image_file)
        size_og = image_reader.size()
        size_mod = size_og
        if size_og.width() * size_og.height() > 33000000:
            print('scaling')
            scale = 4000 / size_mod.width()
            size_mod = size_mod.scaled(int(size_mod.width()*scale),int(size_mod.height()*scale),Qt.AspectRatioMode.IgnoreAspectRatio)
        image_reader.setScaledSize(size_mod)
        self.img = image_reader.read()
        self.img = self.img.scaled(size_og.width(),size_og.height())
        self.img_pixmap = QPixmap.fromImage(self.img)
        self.img = QGraphicsPixmapItem(self.img_pixmap)
        
        self.ui.plotWidget.addItem(self.img)
        self.ui.plotWidget.getPlotItem().invertY(True)
        
        # Use PIL to get Image DPI
        self.dpi = round(Image.open(self.image_file).info['dpi'][0])
        self.ui.comboBoxDPI.setCurrentText(str(self.dpi))
        self.show_image_characteristics()
        
        # Only search image for ROIs once
        self.roi_rectangles = self._find_rois(self.image_file)
        # Run initial drawing of ROIs
        self.rois = []
        self.draw_rois()
        
    def show_image_characteristics(self):
        dpi = self.dpi
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
            if i < len(self.card_list):
                x, y, w, h = r
                roi = pg.RectROI([x, y],[w, h],
                            pen=mkPen('m',width=3),
                            hoverPen=mkPen('r',width=5),
                            handlePen=mkPen('r',width=3),
                            handleHoverPen=mkPen('r',width=5),
                            removable=True, centered=True, sideScalers=True,
                            scaleSnap=True, translateSnap=True)
                roi.scale(s=float(self.scale)/100,center=[0.5,0.5])
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
        self.orientation = cfg.ROI_ACQUISITION_ORIENTATIONS[newIndex]
        self.draw_rois()
       
    @pyqtSlot(int)
    def order_changed(self, newIndex):
        self.order = cfg.ROI_ACQUISITION_ORDERS[newIndex]
        self.draw_rois()
        
    @pyqtSlot(int)
    def scale_changed(self, newIndex):
        self.scale = cfg.ROI_SCALES[newIndex]
        self.draw_rois()
        
    @pyqtSlot(object)
    def remove_roi(self, roi):
        #self.ui.plotWidget.scene().removeItem(roi)
        del self.roi_rectangles[self.rois.index(roi)]
        #self.rois.remove(roi)
        self.draw_rois()
        
    @pyqtSlot()
    def click_add_card(self):
        
        pass
    
    @pyqtSlot()
    def click_remove_card(self):
        pass
        
    @pyqtSlot()
    def accept(self):
        self.settings.setValue(cfg._DPI, int(self.ui.comboBoxDPI.currentText()))
        self.settings.setValue(cfg._ROI_ACQUISITION_ORIENTATION, self.ui.comboBoxOrientation.currentText())
        self.settings.setValue(cfg._ROI_ACQUISITION_ORDER, self.ui.comboBoxOrder.currentText())
        self.settings.setValue(cfg._ROI_SCALE, cfg.ROI_SCALES[self.ui.comboBoxScale.currentIndex()])
        
        prog = QProgressDialog(self)
        prog.setMinimumDuration(0)
        prog.setWindowModality(Qt.WindowModality.WindowModal)
    
        for i, roi in enumerate(self.rois):
            if i==0:
                prog.setRange(0, len(self.rois))
            prog.setValue(i)
            prog.setLabelText(f'Cropping {self.card_list[i].name} and saving to the database')
            if prog.wasCanceled():
                return
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
            sprayCard.dpi = self.dpi
            if i==len(self.rois)-1:
                prog.setValue(i+1)
        
        super().accept()
    
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

    '''def clickDraw(self):
        QApplication.setOverrideCursor(QCursor(Qt.CursorShape.CrossCursor))
        pw: pg.PlotWidget = self.ui.plotWidget
        pw.getPlotItem().getViewBox().setMouseMode(pg.ViewBox.RectMode)
        pw.sceneObj.sigMouseClicked[object].connect(self.clicked)
           
    def clicked(self):
        print('clickec')'''

class LoadCardsPreBatch(baseclass_pre):
    
    def __init__(self, image_files: list[str], card_list: list[SprayCard], parent=None):
        super().__init__(parent=parent)
        self.ui = Ui_Form_Pre()
        self.ui.setupUi(self)
        
        self.cards = card_list
        self.files = image_files
        
        self.lwc: QListWidget = self.ui.listWidgetCard
        self.lwf: QListWidget = self.ui.listWidgetFile
        self.cbc: QCheckBox = self.ui.checkBoxCrop
        
        self.lwc.addItems([c.name for c in self.cards])
        self.lwf.addItems(self.files)
        
        self.show()
        
    def accept(self):
        if self.cbc.isChecked():
            # TODO Send to Load Cards in loop
            pass
        else:
            # Go ahead and load as is
            for i in range(self.lwf.count()):
                if i < len(self.cards):
                    with open(self.lwf.item(i).text(), 'rb') as file:
                        binary_data = file.read()
                    c = self.cards[i]
                    c.has_image = True
                    c.include_in_composite = True
                    c.dpi = round(Image.open(self.lwf.item(i).text()).info['dpi'][0])
                    c.save_image_to_file(image=binary_data)
                
        super().accept()

    

