import copy
import os

import superqt
import accupatt.config as cfg
from PyQt6 import uic
from PyQt6.QtCore import Qt, pyqtSignal

Ui_Form, baseclass = uic.loadUiType(os.path.join(os.getcwd(), 'resources', 'editThreshold.ui'))

class EditThreshold(baseclass):

    applied = pyqtSignal()

    def __init__(self, sprayCard, passData, seriesData, parent=None):
        super().__init__(parent=parent)
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        # Your code will go here

        #Get a handle on the card (will be used to commit changes in on_applied)
        self.sprayCard_OG = sprayCard
        #Make a working copy
        self.sprayCard = copy.copy(sprayCard)
        #Get a handle to seriesData and passData to enable "Apply to all cards on save"
        self.seriesData = seriesData
        self.passData = passData

        #Signals for toggling group boxes
        self.ui.groupBoxGrayscale.toggled[bool].connect(self.toggleGrayscale)
        self.ui.groupBoxColor.toggled[bool].connect(self.toggleColor)
        #Select appropriate group box
        self.ui.groupBoxGrayscale.setChecked(self.sprayCard.threshold_type == cfg.THRESHOLD_TYPE_GRAYSCALE)

        #Populate grayscale ui from spray card
        self.ui.radioButtonAutomatic.setChecked(self.sprayCard.threshold_method_grayscale == cfg.THRESHOLD_METHOD_AUTOMATIC)
        self.ui.radioButtonManual.setChecked(self.sprayCard.threshold_method_grayscale == cfg.THRESHOLD_METHOD_MANUAL)
        self.ui.sliderGrayscale.setValue(self.sprayCard.threshold_grayscale)

        #Populate color ui from spray card
        self.ui.radioButtonInclude.setChecked(self.sprayCard.threshold_method_color == cfg.THRESHOLD_METHOD_INCLUDE)
        self.ui.radioButtonManual.setChecked(self.sprayCard.threshold_method_color == cfg.THRESHOLD_METHOD_EXCLUDE)
        self.ui.rangeSliderHue.setValue([self.sprayCard.threshold_color_hue[0],self.sprayCard.threshold_color_hue[1]])
        self.ui.rangeSliderSaturation.setValue([self.sprayCard.threshold_color_saturation[0],self.sprayCard.threshold_color_saturation[1]])
        self.ui.rangeSliderBrightness.setValue([self.sprayCard.threshold_color_brightness[0],self.sprayCard.threshold_color_brightness[1]])

        #Signals for controls
        self.ui.radioButtonAutomatic.toggled.connect(self.toggleThresholdMethodGrayscale)
        self.ui.radioButtonManual.toggled.connect(self.toggleThresholdMethodGrayscale)
        self.ui.sliderGrayscale.valueChanged[int].connect(self.updateThresholdGrayscale)
        self.ui.radioButtonInclude.toggled[bool].connect(self.toggleThresholdMethodColor)
        self.ui.radioButtonExclude.toggled[bool].connect(self.toggleThresholdMethodColor)
        self.ui.rangeSliderHue.valueChanged[tuple].connect(self.updateHue)
        self.ui.rangeSliderSaturation.valueChanged[tuple].connect(self.updateSaturation)
        self.ui.rangeSliderBrightness.valueChanged[tuple].connect(self.updateBrightness)
        self.ui.checkBoxApplyToAllSeries.toggled[bool].connect(self.toggleApplyToAllSeries)
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

    def toggleGrayscale(self, boo):
        self.ui.groupBoxColor.setChecked(not boo)
        thresh_type = cfg.THRESHOLD_TYPE_COLOR
        if boo: thresh_type = cfg.THRESHOLD_TYPE_GRAYSCALE
        self.sprayCard.set_threshold_type(type=thresh_type)
        self.updateSprayCardView()

    def updateThresholdGrayscale(self, thresh):
        self.sprayCard.set_threshold_grayscale(threshold=thresh)
        self.updateSprayCardView()

    def toggleThresholdMethodGrayscale(self):
        method = cfg.THRESHOLD_METHOD_AUTOMATIC
        if self.ui.radioButtonManual.isChecked():
            method = cfg.THRESHOLD_METHOD_MANUAL
        self.sprayCard.threshold_method_grayscale = method
        self.updateSprayCardView()

    def toggleColor(self, boo):
        self.ui.groupBoxGrayscale.setChecked(not boo)
        thresh_type = cfg.THRESHOLD_TYPE_GRAYSCALE
        if boo: thresh_type = cfg.THRESHOLD_TYPE_COLOR
        self.sprayCard.set_threshold_type(type=thresh_type)
        self.updateSprayCardView()

    def toggleThresholdMethodColor(self):
        if self.ui.radioButtonInclude.isChecked():
            self.sprayCard.threshold_method_color = cfg.THRESHOLD_METHOD_INCLUDE
        elif self.ui.radioButtonExclude.isChecked():
            self.sprayCard.threshold_method_color = cfg.THRESHOLD_METHOD_EXCLUDE
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
            self.ui.checkBoxApplyToAllPass.setCheckState(Qt.CheckState.Checked)
        else:
            self.ui.checkBoxApplyToAllPass.setCheckState(Qt.CheckState.Unchecked)
        self.ui.checkBoxApplyToAllPass.setEnabled(not boo)

    def updateSprayCardView(self):
        #Left Image (1) Right Image (2)
        cvImg1, cvImg2 = self.sprayCard.images_processed()

        self.ui.splitCardWidget.updateSprayCardView(cvImg1, cvImg2)

    def on_applied(self):
        #Cycle through passes
        for p in self.seriesData.passes:
            #Check if should apply to pass
            if p.name == self.passData.name or self.ui.checkBoxApplyToAllSeries.checkState() == Qt.CheckState.Checked:
                #Cycle through cards in pass
                for card in p.spray_cards:
                    if card.name == self.sprayCard_OG.name or self.ui.checkBoxApplyToAllPass.checkState() == Qt.CheckState.Checked:
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
