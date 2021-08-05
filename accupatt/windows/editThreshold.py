from PyQt5.QtWidgets import QApplication, QGraphicsScene, QGraphicsPixmapItem
from PyQt5.QtCore import Qt, QSettings, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap, QResizeEvent
from PyQt5 import uic

import os, sys, copy

from accupatt.models.sprayCard import SprayCard

Ui_Form, baseclass = uic.loadUiType(os.path.join(os.getcwd(), 'accupatt', 'windows', 'ui', 'editThreshold.ui'))

class EditThreshold(baseclass):

    applied = pyqtSignal()

    def __init__(self, sprayCard, passData, seriesData):
        super().__init__()
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        # Your code will go here

        #Get a handle on the card (will be used to commit changes in on_applied)
        self.sprayCard_OG = sprayCard
        #Make a working copy
        self.sprayCard = copy.deepcopy(sprayCard)
        #Get a handle to seriesData and passData to enable "Apply to all cards on save"
        self.seriesData = seriesData
        self.passData = passData

        #Load in Settings
        self.settings = QSettings('BG Application Consulting','AccuPatt')
        #Set defaults to sprayCard if attributes do not exist
        if self.sprayCard.threshold_type is None:
            self.sprayCard.threshold_type = self.settings.value('threshold_type', defaultValue=SprayCard.THRESHOLD_TYPE_COLOR, type=int)
        if self.sprayCard.threshold_method_grayscale is None:
            self.sprayCard.threshold_method_grayscale = self.settings.value('threshold_method_grayscale', defaultValue=SprayCard.THRESHOLD_METHOD_AUTOMATIC, type=int)
        if self.sprayCard.threshold_grayscale is None:
            self.sprayCard.threshold_grayscale = self.settings.value('threshold_grayscale', defaultValue=153, type=int)
        if self.sprayCard.threshold_method_color is None:
            self.sprayCard.threshold_method_color = self.settings.value('threshold_method_color', defaultValue=SprayCard.THRESHOLD_METHOD_INCLUDE, type=int)
        if self.sprayCard.threshold_color_hue is None:
            print('devaulting hue')
            self.sprayCard.threshold_color_hue = self.settings.value('threshold_color_hue', defaultValue=[180,240])
        if self.sprayCard.threshold_color_saturation is None:
            self.sprayCard.threshold_color_saturation = self.settings.value('threshold_color_saturation', defaultValue=[6,255])
        if self.sprayCard.threshold_color_brightness is None:
            self.sprayCard.threshold_color_brightness = self.settings.value('threshold_color_brightness', defaultValue=[0,255])

        #Show original
        self.pixmap_item_original = QGraphicsPixmapItem()
        scene1 = QGraphicsScene(self)
        scene1.addItem(self.pixmap_item_original)
        self.ui.graphicsView.setScene(scene1)
        #Show threshold
        self.pixmap_item_thresh = QGraphicsPixmapItem()
        scene2 = QGraphicsScene(self)
        scene2.addItem(self.pixmap_item_thresh)
        self.ui.graphicsView2.setScene(scene2)

        #Signals for toggling group boxes
        self.ui.groupBoxGrayscale.toggled[bool].connect(self.toggleGrayscale)
        self.ui.groupBoxColor.toggled[bool].connect(self.toggleColor)
        #Select appropriate group box
        self.ui.groupBoxGrayscale.setChecked(self.sprayCard.threshold_type == SprayCard.THRESHOLD_TYPE_GRAYSCALE)

        #Populate grayscale ui from spray card
        self.ui.radioButtonAutomatic.setChecked(self.sprayCard.threshold_method_grayscale == SprayCard.THRESHOLD_METHOD_AUTOMATIC)
        self.ui.radioButtonManual.setChecked(self.sprayCard.threshold_method_grayscale == SprayCard.THRESHOLD_METHOD_MANUAL)
        self.ui.sliderGrayscale.setValue(self.sprayCard.threshold_grayscale)

        #Populate color ui from spray card
        self.ui.radioButtonInclude.setChecked(self.sprayCard.threshold_method_color == SprayCard.THRESHOLD_METHOD_INCLUDE)
        self.ui.radioButtonManual.setChecked(self.sprayCard.threshold_method_color == SprayCard.THRESHOLD_METHOD_EXCLUDE)
        self.ui.rangeSliderHue.setValue([self.sprayCard.threshold_color_hue[0],self.sprayCard.threshold_color_hue[1]])
        self.ui.rangeSliderSaturation.setValue([self.sprayCard.threshold_color_saturation[0],self.sprayCard.threshold_color_saturation[1]])
        self.ui.rangeSliderBrightness.setValue([self.sprayCard.threshold_color_brightness[0],self.sprayCard.threshold_color_brightness[1]])
        
        

        #Signals for controls
        self.ui.radioButtonAutomatic.toggled.connect(self.toggleThresholdMethodGrayscale)
        self.ui.radioButtonManual.toggled.connect(self.toggleThresholdMethodGrayscale)
        self.ui.sliderGrayscale.valueChanged[int].connect(self.updateThresholdGrayscale)
        self.ui.radioButtonInclude.toggled[bool].connect(self.toggleThresholdMethodColor)
        #self.ui.radioButtonExclude.toggled[bool].connect(self.toggleThresholdMethodColor)
        self.ui.rangeSliderHue.valueChanged[tuple].connect(self.updateHue)
        self.ui.rangeSliderSaturation.valueChanged[tuple].connect(self.updateSaturation)
        self.ui.rangeSliderBrightness.valueChanged[tuple].connect(self.updateBrightness)
        self.ui.checkBoxApplyToAllSeries.toggled[bool].connect(self.toggleApplyToAllSeries)
        #Signals for syncing scrollbars
        self.ui.graphicsView.verticalScrollBar().valueChanged[int].connect(self.scrollGV2)
        #ButtonBox
        self.ui.buttonBox.accepted.connect(self.on_applied)
        self.ui.buttonBox.rejected.connect(self.reject)

        #Configure sliders
        self.ui.rangeSliderHue.setEdgeLabelMode(0)
        self.ui.rangeSliderSaturation.setEdgeLabelMode(0)
        self.ui.rangeSliderBrightness.setEdgeLabelMode(0)

        # Your code ends here
        self.show()
        self.updateSprayCardView()
        self.sprayCard.image_watershed()

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        self.updateSprayCardView()

    def scrollGV2(self, value):
        self.ui.graphicsView2.verticalScrollBar().setValue(value)

    def toggleGrayscale(self, boo):
        self.ui.groupBoxColor.setChecked(not boo)
        thresh_type = SprayCard.THRESHOLD_TYPE_COLOR
        if boo: thresh_type = SprayCard.THRESHOLD_TYPE_GRAYSCALE
        self.sprayCard.set_threshold_type(type=thresh_type)
        self.updateSprayCardView()

    def updateThresholdGrayscale(self, thresh):
        self.sprayCard.set_threshold_grayscale(threshold=thresh)
        self.updateSprayCardView()

    def toggleThresholdMethodGrayscale(self, boo):
        method = SprayCard.THRESHOLD_METHOD_AUTOMATIC
        if self.ui.radioButtonManual.isChecked():
            method = SprayCard.THRESHOLD_METHOD_MANUAL
        self.sprayCard.threshold_method_grayscale = method

    def toggleColor(self, boo):
        self.ui.groupBoxGrayscale.setChecked(not boo)
        thresh_type = SprayCard.THRESHOLD_TYPE_GRAYSCALE
        if boo: thresh_type = SprayCard.THRESHOLD_TYPE_COLOR
        self.sprayCard.set_threshold_type(type=thresh_type)
        self.updateSprayCardView()

    def toggleThresholdMethodColor(self):
        if self.ui.radioButtonInclude.isChecked():
            self.sprayCard.threshold_method_color = self.sprayCard.THRESHOLD_METHOD_INCLUDE
        elif self.ui.radioButtonExclude.isChecked():
            self.sprayCard.threshold_method_color = self.sprayCard.THRESHOLD_METHOD_EXCLUDE
        self.updateSprayCardView()

    def updateHue(self, vals):
        self.sprayCard.set_threshold_color_hue(min=vals[0], max=vals[1])
        self.updateSprayCardView()
    
    def updateSaturation(self, vals):
        self.sprayCard.set_threshold_color_saturation(min=vals[0], max=vals[1])
        self.updateSprayCardView()

    def updateBrightness(self, vals):
        self.sprayCard.set_threshold_color_brightness(min=vals[0], max=vals[1])
        self.updateSprayCardView()

    def toggleApplyToAllSeries(self, boo:bool):
        if boo: 
            self.ui.checkBoxApplyToAllPass.setCheckState(Qt.Checked)
        else:
            self.ui.checkBoxApplyToAllPass.setCheckState(Qt.Unchecked)
        self.ui.checkBoxApplyToAllPass.setEnabled(not boo)

    def updateSprayCardView(self):
        #Left Image (1)
        cvImg1 = self.sprayCard.image_contour(fillShapes=False)
        self.pixmap_item_original.setPixmap(QPixmap.fromImage(self.qImg_from_cvImg(cvImg1)))
        #Right Image(2)
        cvImg2 = self.sprayCard.image_contour(fillShapes=True)
        #cvImg2 = self.sprayCard.image_watershed()
        self.pixmap_item_thresh.setPixmap(QPixmap.fromImage(self.qImg_from_cvImg(cvImg2)))
        #Auto-resize to fit width of crad to width of graphicsView
        scene = self.ui.graphicsView2.scene()
        scene.setSceneRect(scene.itemsBoundingRect())
        self.ui.graphicsView2.fitInView(scene.sceneRect(), Qt.KeepAspectRatioByExpanding)
        self.ui.graphicsView.fitInView(scene.sceneRect(), Qt.KeepAspectRatioByExpanding)  

    def qImg_from_cvImg(self, cvImg):
        height, width = cvImg.shape[:2]
        if len(cvImg.shape) == 2:
            bytesPerLine = 1 * width
            qImg = QImage(cvImg.data, width, height, bytesPerLine, QImage.Format_Grayscale8)
        elif len(cvImg.shape) == 3:
            bytesPerLine = 3 * width
            qImg = QImage(cvImg.data, width, height, bytesPerLine, QImage.Format_RGB888).rgbSwapped()
        return qImg

    def on_applied(self):
        #Cycle through passes
        for pass_key,pass_value in self.seriesData.passes.items():
            #Check if should apply to pass
            if pass_key == self.passData.name or self.ui.checkBoxApplyToAllSeries.checkState() == Qt.Checked:
                #Cycle through cards in pass
                for card in pass_value.spray_cards:
                    if card.name == self.sprayCard_OG.name or self.ui.checkBoxApplyToAllPass.checkState() == Qt.Checked:
                        #Apply
                        #Set overall type
                        card.set_threshold_type(self.sprayCard.threshold_type)
                        #Set grayscale options
                        card.set_threshold_method_grayscale(self.sprayCard.threshold_method_grayscale)
                        card.set_threshold_grayscale(self.sprayCard.threshold_grayscale)
                        #Set color options
                        card.set_threshold_method_color(self.sprayCard.threshold_method_color)
                        card.set_threshold_color_hue(min=self.sprayCard.threshold_color_hue[0],max=self.sprayCard.threshold_color_hue[1])
                        card.set_threshold_color_saturation(min=self.sprayCard.threshold_color_saturation[0],max=self.sprayCard.threshold_color_saturation[1])
                        card.set_threshold_color_brightness(min=self.sprayCard.threshold_color_brightness[0],max=self.sprayCard.threshold_color_brightness[1])

        #Notify requestor
        self.applied.emit()
        self.accept

    def on_rejected(self):
        self.reject

if __name__ == '__main__':
    app = QApplication(sys.argv)
    sprayCard = SprayCard(name='test', filepath='/Users/gill14/OneDrive - University of Illinois - Urbana/AccuProjects/Python Projects/AccuPatt/testing/N802ET S3/N802ET S3 P3/cards/L-24.png')
    sprayCard.set_threshold_type(SprayCard.THRESHOLD_TYPE_COLOR)
    sprayCard.set_threshold_color_hue(min=0,max=255)
    sprayCard.set_threshold_color_saturation(min=0, max=255)
    sprayCard.set_threshold_color_brightness(min=0, max=188)
    sprayCard.set_threshold_method_color(SprayCard.THRESHOLD_METHOD_INCLUDE)
    w = EditThreshold(sprayCard)
    sys.exit(app.exec_())