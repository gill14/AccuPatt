import copy
import os

from superqt import QLabeledRangeSlider, QLabeledSlider
import accupatt.config as cfg
from PyQt6 import uic
from PyQt6.QtCore import Qt, pyqtSlot

from accupatt.models.sprayCard import SprayCard

Ui_Form, baseclass = uic.loadUiType(os.path.join(os.getcwd(), 'resources', 'editThreshold.ui'))

class EditThreshold(baseclass):

    def __init__(self, sprayCard, passData, seriesData, parent=None):
        super().__init__(parent=parent)
        self.ui = Ui_Form()
        self.ui.setupUi(self)

        #Get a handle on the card (will be used to commit changes in on_applied)
        self.sprayCard_OG = sprayCard
        #Make a working copy
        self.sprayCard: SprayCard = copy.copy(sprayCard)
        #Get a handle to seriesData and passData to enable "Apply to all cards on save"
        self.seriesData = seriesData
        self.passData = passData

        # Threshold Type Combobox - Sets contents of Threshold GroupBox
        self.ui.comboBoxThresholdType.addItems(cfg.THRESHOLD_TYPES)
        self.ui.comboBoxThresholdType.currentIndexChanged[int].connect(self.threshold_type_changed)
        self.ui.comboBoxThresholdType.setCurrentIndex(cfg.THRESHOLD_TYPES.index(self.sprayCard.threshold_type))

        #Populate grayscale ui from spray card
        self.ui.radioButtonAutomatic.setChecked(self.sprayCard.threshold_method_grayscale == cfg.THRESHOLD_GRAYSCALE_METHOD_AUTO)
        self.ui.radioButtonManual.setChecked(self.sprayCard.threshold_method_grayscale == cfg.THRESHOLD_GRAYSCALE_METHOD_MANUAL)
        self.ui.radioButtonAutomatic.toggled.connect(self.toggleThresholdMethodGrayscale)
        self.ui.radioButtonManual.toggled.connect(self.toggleThresholdMethodGrayscale)
        self.ui.sliderGrayscale.setValue(self.sprayCard.threshold_grayscale)
        self.ui.sliderGrayscale.valueChanged[int].connect(self.updateThresholdGrayscale)

        #Populate color ui from spray card
        self.ui.radioButtonInclude.setChecked(self.sprayCard.threshold_method_color == cfg.THRESHOLD_HSB_METHOD_INCLUDE)
        self.ui.radioButtonExclude.setChecked(self.sprayCard.threshold_method_color == cfg.THRESHOLD_HSB_METHOD_EXCLUDE)
        self.ui.radioButtonInclude.toggled[bool].connect(self.toggleThresholdMethodColor)
        self.ui.radioButtonExclude.toggled[bool].connect(self.toggleThresholdMethodColor)
        rs_hue: QLabeledRangeSlider = self.ui.rangeSliderHue
        rs_sat: QLabeledRangeSlider = self.ui.rangeSliderSaturation
        rs_bri: QLabeledRangeSlider = self.ui.rangeSliderBrightness
        for rs in [rs_hue,rs_sat,rs_bri]:
            rs.setEdgeLabelMode(0)
            rs.setMinimum(0)
            rs.setMaximum(255)
        rs_hue.setValue(self.sprayCard.threshold_color_hue)
        rs_hue.valueChanged[tuple].connect(self.updateHue)
        rs_sat.setValue(self.sprayCard.threshold_color_saturation)
        rs_sat.valueChanged[tuple].connect(self.updateSaturation)
        rs_bri.setValue(self.sprayCard.threshold_color_brightness)
        rs_bri.valueChanged[tuple].connect(self.updateBrightness)
        
        #Populate Watershed
        self.ui.checkBoxWatershed.setCheckState(Qt.CheckState.Checked if self.sprayCard.watershed else Qt.CheckState.Unchecked)
        self.ui.checkBoxWatershed.stateChanged[int].connect(self.toggleWatershed)
        
        #Populate Stain Approx Method
        self.ui.comboBoxApproximationMethod.addItems(cfg.STAIN_APPROXIMATION_METHODS)
        self.ui.comboBoxApproximationMethod.setCurrentText(self.sprayCard.stain_approximation_method)
        self.ui.comboBoxApproximationMethod.currentIndexChanged[int].connect(self.update_approx_method)
        
        #Populate Min Stain Size
        self.ui.spinBoxMinSize.setValue(self.sprayCard.min_stain_area_px)
        self.ui.spinBoxMinSize.valueChanged[int].connect(self.updateMinSize)

        #Signals for saving
        self.ui.checkBoxApplyToAllSeries.toggled[bool].connect(self.toggleApplyToAllSeries)

        
        self.threshold_type_changed(self.ui.comboBoxThresholdType.currentIndex())
        self.show()

    @pyqtSlot(int)
    def threshold_type_changed(self, index):
        if index == 0:
            # Grayscale
            self.ui.groupBoxColor.hide()
            self.ui.groupBoxGrayscale.show()
            thresh_type = cfg.THRESHOLD_TYPE_GRAYSCALE
        else:
            # HSB
            self.ui.groupBoxGrayscale.hide()
            self.ui.groupBoxColor.show()
            thresh_type = cfg.THRESHOLD_TYPE_HSB
        # Update Thresh Type, redraw
        self.sprayCard.set_threshold_type(type=thresh_type)
        self.updateSprayCardView()

    def updateThresholdGrayscale(self, thresh):
        self.sprayCard.set_threshold_grayscale(threshold=thresh)
        self.updateSprayCardView()

    def toggleThresholdMethodGrayscale(self):
        method = cfg.THRESHOLD_GRAYSCALE_METHOD_AUTO
        if self.ui.radioButtonManual.isChecked():
            method = cfg.THRESHOLD_GRAYSCALE_METHOD_MANUAL
        self.sprayCard.threshold_method_grayscale = method
        self.updateSprayCardView()

    def toggleThresholdMethodColor(self):
        if self.ui.radioButtonInclude.isChecked():
            self.sprayCard.threshold_method_color = cfg.THRESHOLD_HSB_METHOD_INCLUDE
        elif self.ui.radioButtonExclude.isChecked():
            self.sprayCard.threshold_method_color = cfg.THRESHOLD_HSB_METHOD_EXCLUDE
        self.updateSprayCardView()

    @pyqtSlot(tuple)
    def updateHue(self, vals):
        self.sprayCard.set_threshold_color_hue(vals)
        self.updateSprayCardView()
    
    @pyqtSlot(tuple)
    def updateSaturation(self, vals):
        self.sprayCard.set_threshold_color_saturation(vals)
        self.updateSprayCardView()

    @pyqtSlot(tuple)
    def updateBrightness(self, vals):
        self.sprayCard.set_threshold_color_brightness(vals)
        self.updateSprayCardView()
        
    @pyqtSlot(int)
    def toggleWatershed(self, checkstate):
        self.sprayCard.watershed = (Qt.CheckState(checkstate) == Qt.CheckState.Checked)
        self.updateSprayCardView()
        
    @pyqtSlot(int)
    def updateMinSize(self, val):
        self.sprayCard.min_stain_area_px = val
        self.updateSprayCardView()

    @pyqtSlot(int)
    def update_approx_method(self, index):
        self.sprayCard.stain_approximation_method = cfg.STAIN_APPROXIMATION_METHODS[index]
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

    def accept(self):
        #Cycle through passes
        for p in self.seriesData.passes:
            #Check if should apply to pass
            if p.name == self.passData.name or self.ui.checkBoxApplyToAllSeries.checkState() == Qt.CheckState.Checked:
                #Cycle through cards in pass
                card: SprayCard
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
                        card.set_threshold_color_hue(self.sprayCard.threshold_color_hue)
                        card.set_threshold_color_saturation(self.sprayCard.threshold_color_saturation)
                        card.set_threshold_color_brightness(self.sprayCard.threshold_color_brightness)
                        #Set Additional Options
                        card.watershed = self.sprayCard.watershed
                        card.min_stain_area_px = self.sprayCard.min_stain_area_px
                        card.stain_approximation_method = self.sprayCard.stain_approximation_method
        #Notify requestor
        super().accept()
