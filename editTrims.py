from PyQt5 import QtWidgets as qtw
from PyQt5 import QtCore as qtc
from PyQt5 import QtGui as qtg
from PyQt5 import uic

import copy

from passData import Pass
from stringPlotter import StringPlotter

Ui_Form, baseclass = uic.loadUiType('editTrims.ui')

class EditTrims(baseclass):

    applied = qtc.pyqtSignal()

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
        self.ui.horizontalSliderTrimL.setSliderPosition(pattern.trimL)
        self.ui.horizontalSliderTrimR.setSliderPosition(pattern.trimR)
        self.ui.verticalSliderTrimV.setSliderPosition(pattern.trimV)
        #Setup signals for sliders
        self.ui.horizontalSliderTrimL.valueChanged[int].connect(self.updateTrimL)
        self.ui.horizontalSliderTrimL.sliderReleased.connect(self.redrawPlots)
        self.ui.horizontalSliderTrimR.valueChanged[int].connect(self.updateTrimR)
        self.ui.horizontalSliderTrimR.sliderReleased.connect(self.redrawPlots)
        self.ui.verticalSliderTrimV.valueChanged[int].connect(self.updateTrimV)
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

    def updateTrimL(self, trimL):
        p = self.pattern_OG
        p.trimL = trimL
        self.ui.labelTrimL.setText(f"Trim Left = {trimL}")

    def updateTrimR(self, trimR):
        p = self.pattern_OG
        p.trimR = trimR
        self.ui.labelTrimR.setText(f"Trim Right = {trimR}")

    def updateTrimV(self, trimV):
        p = self.pattern_OG
        p.trimV = trimV
        self.ui.labelTrimV.setText(f"Trim Vertical = {trimV}")

    def redrawPlots(self):
        print(f"Trim L = {self.pattern_OG.trimL}, Trim R = {self.pattern_OG.trimR}, Trim V = {self.pattern_OG.trimV}")
        self.pattern_OG.modifyData(
            isCentroid=self.isAlignCentroid,
            isSmooth=self.isSmooth)
        StringPlotter.drawIndividualTrims(
            mplCanvas1=self.ui.plotWidgetTrims.canvas,
            mplCanvas2=self.ui.plotWidgetTrimsPreview.canvas,
            pattern=self.pattern_OG
        )

    def on_applied(self):
        #Accept changes already made and notify requestor
        self.pattern.setTrims(trimL=self.pattern_OG.trimL, trimR=self.pattern_OG.trimR, trimV=self.pattern_OG.trimV)
        self.applied.emit()
        self.accept

    def on_rejected(self):
        self.reject

if __name__ == '__main__':
    app = QtGui.QApplication([])
    gui = NewWindow()
    gui.show()
    app.exec_()
