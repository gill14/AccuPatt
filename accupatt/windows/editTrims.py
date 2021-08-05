from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import pyqtSignal
from PyQt5 import uic

import copy, sys, os

from accupatt.models.passData import Pass
from accupatt.helpers.stringPlotter import StringPlotter

Ui_Form, baseclass = uic.loadUiType(os.path.join(os.getcwd(), 'accupatt', 'windows', 'ui', 'editTrims.ui'))

class EditTrims(baseclass):

    applied = pyqtSignal()

    def __init__(self, pattern, isAlignCentroid, isSmoothIndividual, parent = None):
        super().__init__()
        # Your code will go here
        self.ui = Ui_Form()
        self.ui.setupUi(self)

        self.pattern = pattern
        self.pattern_OG = copy.deepcopy(pattern)
        self.isAlignCentroid = isAlignCentroid
        self.isSmooth = isSmoothIndividual
        #Set Bounds on sliders
        maxh = (pattern.data[pattern.name].size / 2) - 1
        maxv = pattern.data[pattern.name].max()
        self.ui.horizontalSliderTrimL.setMinimum(0)
        self.ui.horizontalSliderTrimL.setMaximum(maxh)
        self.ui.horizontalSliderTrimR.setMinimum(0)
        self.ui.horizontalSliderTrimR.setMaximum(maxh)
        self.ui.verticalSliderTrimV.setMinimum(0)
        self.ui.verticalSliderTrimV.setMaximum(maxv)
        #Set initial values on sliders
        self.ui.horizontalSliderTrimL.setSliderPosition(pattern.trim_l)
        self.ui.horizontalSliderTrimR.setSliderPosition(pattern.trim_r)
        self.ui.verticalSliderTrimV.setSliderPosition(pattern.trim_v)
        #Setup signals for sliders
        self.ui.horizontalSliderTrimL.valueChanged[int].connect(self.updatetrim_l)
        self.ui.horizontalSliderTrimL.sliderReleased.connect(self.redrawPlots)
        self.ui.horizontalSliderTrimR.valueChanged[int].connect(self.updatetrim_r)
        self.ui.horizontalSliderTrimR.sliderReleased.connect(self.redrawPlots)
        self.ui.verticalSliderTrimV.valueChanged[int].connect(self.updatetrim_v)
        self.ui.verticalSliderTrimV.sliderReleased.connect(self.redrawPlots)

        self.ui.buttonBox.accepted.connect(self.on_applied)
        self.ui.buttonBox.rejected.connect(self.reject)

        StringPlotter.drawIndividualTrims(
            mplCanvas1=self.ui.plotWidgetTrims.canvas,
            mplCanvas2=self.ui.plotWidgetTrimsPreview.canvas,
            pattern=self.pattern_OG
        )

        # Your code ends here
        self.show()

    def updatetrim_l(self, trim_l):
        p = self.pattern_OG
        p.trim_l = trim_l
        self.ui.labelTrimL.setText(f"Trim Left = {trim_l}")

    def updatetrim_r(self, trim_r):
        p = self.pattern_OG
        p.trim_r = trim_r
        self.ui.labelTrimR.setText(f"Trim Right = {trim_r}")

    def updatetrim_v(self, trim_v):
        p = self.pattern_OG
        p.trim_v = trim_v
        self.ui.labelTrimV.setText(f"Trim Vertical = {trim_v}")

    def redrawPlots(self):
        print(f"Trim L = {self.pattern_OG.trim_l}, Trim R = {self.pattern_OG.trim_r}, Trim V = {self.pattern_OG.trim_v}")
        self.pattern_OG.modifyData(
            isCenter=self.isAlignCentroid,
            isSmooth=self.isSmooth)
        StringPlotter.drawIndividualTrims(
            mplCanvas1=self.ui.plotWidgetTrims.canvas,
            mplCanvas2=self.ui.plotWidgetTrimsPreview.canvas,
            pattern=self.pattern_OG
        )

    def on_applied(self):
        #Accept changes already made and notify requestor
        self.pattern.setTrims(trim_l=self.pattern_OG.trim_l, trim_r=self.pattern_OG.trim_r, trim_v=self.pattern_OG.trim_v)
        self.applied.emit()
        self.accept

    def on_rejected(self):
        self.reject

if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = EditTrims(Pass(), True, True)
    sys.exit(app.exec_())
