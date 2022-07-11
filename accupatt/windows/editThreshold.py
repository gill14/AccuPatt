import copy
import os
import numpy as np

from superqt import QLabeledRangeSlider, QLabeledSlider
import accupatt.config as cfg
from PyQt6 import uic
from PyQt6.QtCore import Qt, pyqtSlot, QSignalBlocker
from PyQt6.QtWidgets import QCheckBox, QComboBox, QDialogButtonBox, QLineEdit, QMessageBox, QPushButton, QRadioButton, QSpinBox

from accupatt.models.sprayCard import SprayCard

Ui_Form, baseclass = uic.loadUiType(
    os.path.join(os.getcwd(), "resources", "editThreshold.ui")
)


class EditThreshold(baseclass):
    def __init__(self, sprayCard, passData, seriesData, parent=None):
        super().__init__(parent=parent)
        self.ui = Ui_Form()
        self.ui.setupUi(self)

        # Make a working copy
        self.sprayCard: SprayCard = copy.copy(sprayCard)
        # Get a handle to seriesData and passData to enable "Apply to all cards on save"
        self.seriesData = seriesData
        self.passData = passData
        
        self.fit = "horizontal"

        # Threshold Type Combobox - Sets contents of Threshold GroupBox
        self.ui.comboBoxThresholdType.addItems(cfg.THRESHOLD_TYPES)
        self.ui.comboBoxThresholdType.currentIndexChanged[int].connect(
            self.threshold_type_changed
        )
        self.ui.comboBoxThresholdType.setCurrentIndex(
            cfg.THRESHOLD_TYPES.index(self.sprayCard.threshold_type)
        )

        # Populate grayscale ui from spray card
        self.ui.radioButtonAutomatic.setChecked(
            self.sprayCard.threshold_method_grayscale
            == cfg.THRESHOLD_GRAYSCALE_METHOD_AUTO
        )
        self.ui.radioButtonManual.setChecked(
            self.sprayCard.threshold_method_grayscale
            == cfg.THRESHOLD_GRAYSCALE_METHOD_MANUAL
        )
        self.ui.radioButtonAutomatic.toggled.connect(
            self.toggleThresholdMethodGrayscale
        )
        self.ui.radioButtonManual.toggled.connect(self.toggleThresholdMethodGrayscale)
        self.ui.sliderGrayscale.setValue(self.sprayCard.threshold_grayscale)
        self.ui.sliderGrayscale.valueChanged[int].connect(self.updateThresholdGrayscale)

        # Populate color ui from spray card
        self.ui.checkBoxHue.setChecked(self.sprayCard.threshold_color_hue_pass)
        self.ui.checkBoxHue.toggled.connect(self.toggleHuePass)
        self.ui.checkBoxSat.setChecked(self.sprayCard.threshold_color_saturation_pass)
        self.ui.checkBoxSat.toggled.connect(self.toggleSatPass)
        self.ui.checkBoxBri.setChecked(self.sprayCard.threshold_color_brightness_pass)
        self.ui.checkBoxBri.toggled.connect(self.toggleBriPass)
        rs_hue: QLabeledRangeSlider = self.ui.rangeSliderHue
        rs_sat: QLabeledRangeSlider = self.ui.rangeSliderSaturation
        rs_bri: QLabeledRangeSlider = self.ui.rangeSliderBrightness
        for rs in [rs_hue, rs_sat, rs_bri]:
            rs.setEdgeLabelMode(0)
            rs.setMinimum(0)
            rs.setMaximum(255)
        rs_hue.setMaximum(179)
        rs_hue.setValue(
            (
                int(self.sprayCard.threshold_color_hue_min),
                int(self.sprayCard.threshold_color_hue_max),
            )
        )
        rs_hue.valueChanged[tuple].connect(self.updateHue)
        rs_sat.setValue(
            (
                int(self.sprayCard.threshold_color_saturation_min),
                int(self.sprayCard.threshold_color_saturation_max),
            )
        )
        rs_sat.valueChanged[tuple].connect(self.updateSaturation)
        rs_bri.setValue(
            (
                int(self.sprayCard.threshold_color_brightness_min),
                int(self.sprayCard.threshold_color_brightness_max),
            )
        )
        rs_bri.valueChanged[tuple].connect(self.updateBrightness)

        self.buttonAdvancedOptions: QPushButton = self.ui.buttonAdvancedOptions
        self.buttonAdvancedOptions.clicked.connect(self._clicked_advanced_options)

        self.rb_horizontal: QRadioButton = self.ui.radioButtonHorizontal
        self.rb_horizontal.toggled[bool].connect(self._clicked_rb_horizontal)
        self.rb_horizontal.setChecked(True)
        
        self.rb_vertical: QRadioButton = self.ui.radioButtonVertical
        self.rb_vertical.toggled[bool].connect(self._clicked_rb_vertical)

        # Signals for saving
        self.ui.checkBoxApplyToAllSeries.toggled[bool].connect(
            self.toggleApplyToAllSeries
        )

        self.ui.buttonBox.button(
            QDialogButtonBox.StandardButton.RestoreDefaults
        ).clicked.connect(self._restore_defaults)

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

    @pyqtSlot(bool)
    def toggleHuePass(self, checked):
        print(checked)
        self.sprayCard.set_threshold_color_hue(bandpass=checked)
        self.updateSprayCardView()

    @pyqtSlot(tuple)
    def updateHue(self, vals):
        self.sprayCard.set_threshold_color_hue(min=vals[0], max=vals[1])
        self.updateSprayCardView()

    @pyqtSlot(bool)
    def toggleSatPass(self, checked):
        self.sprayCard.set_threshold_color_saturation(bandpass=checked)
        self.updateSprayCardView()

    @pyqtSlot(tuple)
    def updateSaturation(self, vals):
        self.sprayCard.set_threshold_color_saturation(min=vals[0], max=vals[1])
        self.updateSprayCardView()

    @pyqtSlot(bool)
    def toggleBriPass(self, checked):
        self.sprayCard.set_threshold_color_brightness(bandpass=checked)
        self.updateSprayCardView()

    @pyqtSlot(tuple)
    def updateBrightness(self, vals):
        self.sprayCard.set_threshold_color_brightness(min=vals[0], max=vals[1])
        self.updateSprayCardView()

    @pyqtSlot()
    def _clicked_advanced_options(self):
        e = ProcessOptionsAdvanced(self.sprayCard, parent=self)
        e.accepted.connect(self.updateSprayCardView)
        e.exec()

    @pyqtSlot(bool)
    def _clicked_rb_horizontal(self, isChecked: bool):
        if isChecked:
            self.fit = "horizontal"
        self.updateSprayCardView()
        
    @pyqtSlot(bool)
    def _clicked_rb_vertical(self, isChecked: bool):
        if isChecked:
            self.fit = "vertical"
        self.updateSprayCardView()

    def toggleApplyToAllSeries(self, boo: bool):
        if boo:
            self.ui.checkBoxApplyToAllPass.setCheckState(Qt.CheckState.Checked)
        else:
            self.ui.checkBoxApplyToAllPass.setCheckState(Qt.CheckState.Unchecked)
        self.ui.checkBoxApplyToAllPass.setEnabled(not boo)

    def updateSprayCardView(self):
        if not self.sprayCard.has_image:
            return
        # Left Image (1) Right Image (2)
        cvImg1, cvImg2 = self.sprayCard.process_image(overlay=True, mask=True)
        self.ui.splitCardWidget.updateSprayCardView(cvImg1, cvImg2, self.fit)
        self.ui.labelGrayscaleThresholdCalculated.clear()
        if self.sprayCard.threshold_type == cfg.THRESHOLD_TYPE_GRAYSCALE:
            if (
                self.sprayCard.threshold_method_grayscale
                == cfg.THRESHOLD_GRAYSCALE_METHOD_AUTO
            ):
                self.ui.labelGrayscaleThresholdCalculated.setText(
                    "Calculated = "
                    + str(int(self.sprayCard.threshold_grayscale_calculated))
                )
    def _restore_defaults(self):
        sc = self.sprayCard
        if sc.threshold_type == cfg.THRESHOLD_TYPE_GRAYSCALE:
            sc.set_threshold_method_grayscale(cfg.get_threshold_grayscale_method())
            with QSignalBlocker(self.ui.radioButtonAutomatic):
                self.ui.radioButtonAutomatic.setChecked(
                    sc.threshold_method_grayscale == cfg.THRESHOLD_GRAYSCALE_METHOD_AUTO
                )
            with QSignalBlocker(self.ui.radioButtonManual):
                self.ui.radioButtonManual.setChecked(
                    sc.threshold_method_grayscale
                    == cfg.THRESHOLD_GRAYSCALE_METHOD_MANUAL
                )
            sc.set_threshold_grayscale(cfg.get_threshold_grayscale())
            with QSignalBlocker(self.ui.sliderGrayscale):
                self.ui.sliderGrayscale.setValue(sc.threshold_grayscale)
        elif sc.threshold_type == cfg.THRESHOLD_TYPE_HSB:
            sc.set_threshold_color_hue(
                min=cfg.get_threshold_hsb_hue_min(),
                max=cfg.get_threshold_hsb_hue_max(),
                bandpass=cfg.get_threshold_hsb_hue_pass(),
            )
            with QSignalBlocker(cb := self.ui.checkBoxHue):
                cb.setChecked(sc.threshold_color_hue_pass)
            with QSignalBlocker(self.ui.rangeSliderHue):
                self.ui.rangeSliderHue.setValue(
                    (
                        self.sprayCard.threshold_color_hue_min,
                        self.sprayCard.threshold_color_hue_max,
                    )
                )
            sc.set_threshold_color_saturation(
                min=cfg.get_threshold_hsb_hue_min(),
                max=cfg.get_threshold_hsb_hue_max(),
                bandpass=cfg.get_threshold_hsb_saturation_pass(),
            )
            with QSignalBlocker(cb := self.ui.checkBoxSat):
                cb.setChecked(sc.threshold_color_saturation_pass)
            with QSignalBlocker(self.ui.rangeSliderSaturation):
                self.ui.rangeSliderSaturation.setValue(
                    (
                        self.sprayCard.threshold_color_saturation_min,
                        self.sprayCard.threshold_color_saturation_max,
                    )
                )
            sc.set_threshold_color_brightness(
                min=cfg.get_threshold_hsb_hue_min(),
                max=cfg.get_threshold_hsb_hue_max(),
                bandpass=cfg.get_threshold_hsb_brightness_pass(),
            )
            with QSignalBlocker(cb := self.ui.checkBoxBri):
                cb.setChecked(sc.threshold_color_brightness_pass)
            with QSignalBlocker(self.ui.rangeSliderBrightness):
                self.ui.rangeSliderBrightness.setValue(
                    (
                        self.sprayCard.threshold_color_brightness_min,
                        self.sprayCard.threshold_color_brightness_max,
                    )
                )
        sc.watershed = cfg.get_watershed()
        with QSignalBlocker(self.ui.checkBoxWatershed):
            self.ui.checkBoxWatershed.setChecked(sc.watershed)
        sc.min_stain_area_px = cfg.get_min_stain_area_px()
        with QSignalBlocker(self.ui.spinBoxMinSize):
            self.ui.spinBoxMinSize.setValue(sc.min_stain_area_px)
        sc.stain_approximation_method = cfg.get_stain_approximation_method()
        with QSignalBlocker(self.ui.comboBoxApproximationMethod):
            self.ui.comboBoxApproximationMethod.setCurrentText(
                sc.stain_approximation_method
            )
        self.updateSprayCardView()

    def accept(self):
        sc = self.sprayCard
        # Cycle through passes
        for p in self.seriesData.passes:
            # Check if should apply to pass
            if (
                p.name == self.passData.name
                or self.ui.checkBoxApplyToAllSeries.checkState()
                == Qt.CheckState.Checked
            ):
                # Cycle through cards in pass
                card: SprayCard
                for card in p.cards.card_list:
                    if (
                        card.name == sc.name
                        or self.ui.checkBoxApplyToAllPass.checkState()
                        == Qt.CheckState.Checked
                    ):
                        # Apply
                        # Set overall type
                        card.set_threshold_type(sc.threshold_type)
                        # Set grayscale options
                        card.set_threshold_method_grayscale(
                            sc.threshold_method_grayscale
                        )
                        card.set_threshold_grayscale(sc.threshold_grayscale)
                        # Set color options
                        card.set_threshold_color_hue(
                            min=sc.threshold_color_hue_min,
                            max=sc.threshold_color_hue_max,
                            bandpass=sc.threshold_color_hue_pass,
                        )
                        card.set_threshold_color_saturation(
                            min=sc.threshold_color_saturation_min,
                            max=sc.threshold_color_saturation_max,
                            bandpass=sc.threshold_color_saturation_pass,
                        )
                        card.set_threshold_color_brightness(
                            min=sc.threshold_color_brightness_min,
                            max=sc.threshold_color_brightness_max,
                            bandpass=sc.threshold_color_brightness_pass,
                        )
                        # Set Additional Options
                        card.flag_max_stain_limit_reached = sc.flag_max_stain_limit_reached
                        card.watershed = sc.watershed
                        card.min_stain_area_px = sc.min_stain_area_px
                        card.stain_approximation_method = sc.stain_approximation_method
                        # Currency Flag
                        card.current = False
                        card.stats.current = False
        # Update Defualts if requested
        if self.ui.checkBoxUpdateDefaults.isChecked():
            cfg.set_threshold_type(sc.threshold_type)
            # Only update for type selected
            if sc.threshold_type == cfg.THRESHOLD_TYPE_GRAYSCALE:
                cfg.set_threshold_grayscale_method(sc.threshold_method_grayscale)
                cfg.set_threshold_grayscale(sc.threshold_grayscale)
            elif sc.threshold_type == cfg.THRESHOLD_TYPE_HSB:
                cfg.set_threshold_hsb_hue_min(sc.threshold_color_hue_min)
                cfg.set_threshold_hsb_hue_max(sc.threshold_color_hue_max)
                cfg.set_threshold_hsb_hue_pass(sc.threshold_color_hue_pass)
                cfg.set_threshold_hsb_saturation_min(sc.threshold_color_saturation_min)
                cfg.set_threshold_hsb_saturation_max(sc.threshold_color_saturation_max)
                cfg.set_threshold_hsb_saturation_pass(
                    sc.threshold_color_saturation_pass
                )
                cfg.set_threshold_hsb_brightness_min(sc.threshold_color_brightness_min)
                cfg.set_threshold_hsb_brightness_max(sc.threshold_color_brightness_max)
                cfg.set_threshold_hsb_brightness_pass(
                    sc.threshold_color_brightness_pass
                )
            cfg.set_watershed(sc.watershed)
            cfg.set_min_stain_area_px(sc.min_stain_area_px)
            cfg.set_stain_approximation_method(sc.stain_approximation_method)
        # Notify requestor
        super().accept()


Ui_Form_2, baseclass_2 = uic.loadUiType(
    os.path.join(os.getcwd(), "resources", "processOptionsAdvanced.ui")
)

class ProcessOptionsAdvanced(baseclass_2):
    def __init__(self, sprayCard: SprayCard, parent=None):
        super().__init__(parent=parent)
        self.ui = Ui_Form_2()
        self.ui.setupUi(self)
        
        self.sprayCard = sprayCard
        
        # Max stain count
        self.le_max: QLineEdit = self.ui.lineEditMaxStains
        self.le_max.setText(str(cfg.get_max_stain_count()))
        
        # Populate Watershed
        self.cb_watershed: QCheckBox = self.ui.checkBoxWatershed
        self.cb_watershed.setCheckState(
            Qt.CheckState.Checked
            if self.sprayCard.watershed
            else Qt.CheckState.Unchecked
        )

        # Populate Stain Approx Method
        self.cb_approx: QComboBox = self.ui.comboBoxApproximationMethod
        self.cb_approx.addItems(cfg.STAIN_APPROXIMATION_METHODS)
        self.cb_approx.setCurrentText(
            self.sprayCard.stain_approximation_method
        )

        # Populate Min Stain Size
        self.sb_min: QSpinBox = self.ui.spinBoxMinSize
        self.sb_min.setValue(self.sprayCard.min_stain_area_px)
        
        self.show()
        
    def accept(self):
        try:
            int(self.le_max.text())
        except:
            msg = QMessageBox.information(self, "Value Error", "Max Stain Count must be an integer")
            msg.exec()
            if msg == QMessageBox.StandardButton.Ok:
                return
        cfg.set_max_stain_count(self.le_max.text())
        self.sprayCard.watershed = self.cb_watershed.isChecked()
        self.sprayCard.min_stain_area_px = self.sb_min.value()
        self.sprayCard.stain_approximation_method = self.cb_approx.currentText()
        super().accept()