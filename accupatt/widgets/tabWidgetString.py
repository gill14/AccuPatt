import os

import accupatt.config as cfg
from PyQt6.QtCore import Qt, pyqtSlot, QSignalBlocker
from PyQt6.QtWidgets import QCheckBox
from pyqtgraph import PlotWidget

from accupatt.models.passData import Pass
from accupatt.models.seriesData import SeriesData
from accupatt.widgets.tabWidgetBase import TabWidgetBase
from accupatt.windows.stringPass import StringPass


class TabWidgetString(TabWidgetBase):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(
            ui_file=os.path.join(os.getcwd(), "resources", "stringMainWidget.ui"),
            subtype="string",
            parent=parent,
            *args,
            **kwargs,
        )

        self.checkBoxPassRebase: QCheckBox = self.ui.checkBoxPassRebase
        self.checkBoxPassRebase.stateChanged[int].connect(self.passRebaseChanged)

        self.checkBoxSeriesEqualize: QCheckBox = self.ui.checkBoxSeriesEqualize
        self.checkBoxSeriesEqualize.stateChanged[int].connect(
            self.seriesEqualizeChanged
        )

        self.plotWidgetIndividual: PlotWidget = self.ui.plotWidgetIndividual
        self.plotWidgetIndividualTrim: PlotWidget = self.ui.plotWidgetIndividualTrim

    """
    External Method to fill data
    """

    def setData(self, seriesData: SeriesData):
        super().setData(seriesData=seriesData)
        with QSignalBlocker(self.checkBoxSeriesEqualize):
            self.checkBoxSeriesEqualize.setChecked(
                self.seriesData.string.equalize_integrals
            )

    """
    Pass List Widget
    """

    @pyqtSlot()
    def passSelectionChanged(self):
        if not (passData := self.getCurrentPass()):
            return
        self.checkBoxPassCenter.setEnabled(not passData.string.rebase)
        with QSignalBlocker(self.checkBoxPassRebase):
            self.checkBoxPassRebase.setChecked(passData.string.rebase)
        super().passSelectionChanged()

    """
    Edit Pass Button & Methods
    """

    @pyqtSlot()
    def editPass(self):
        if passData := self.getCurrentPass():
            e = StringPass(passData=passData, parent=self.parent())
            e.accepted.connect(self.onEditPassAccepted)
            e.show()

    """
    Pass Data Mod Options
    """

    @pyqtSlot(int)
    def passRebaseChanged(self, checkstate):
        if passData := self.getCurrentPass():
            passData.string.rebase = Qt.CheckState(checkstate) == Qt.CheckState.Checked
            if passData.string.rebase:
                passData.string.center = True
                self.checkBoxPassCenter.setChecked(passData.string.center)
            self.checkBoxPassCenter.setEnabled(not passData.string.rebase)
            self.updatePlots(
                modify=True, individuals=True, composites=True, simulations=True
            )

    """
    Series Data Mod Options
    """

    @pyqtSlot(int)
    def seriesEqualizeChanged(self, checkstate):
        self.seriesData.string.equalize_integrals = (
            Qt.CheckState(checkstate) == Qt.CheckState.Checked
        )
        self.updatePlots(modify=True, composites=True, simulations=True)

    """
    Individual Passes Tab
    """

    @pyqtSlot(object)
    def _updateTrimL(self, object):
        self.getCurrentPass().string.user_set_trim_left(object.value())
        self.updatePlots(
            modify=True, individuals=True, composites=True, simulations=True
        )

    @pyqtSlot(object)
    def _updateTrimR(self, object):
        self.getCurrentPass().string.user_set_trim_right(object.value())
        self.updatePlots(
            modify=True, individuals=True, composites=True, simulations=True
        )

    @pyqtSlot(object)
    def _updateTrimFloor(self, object):
        self.getCurrentPass().string.user_set_trim_floor(object.value())
        self.updatePlots(
            modify=True, individuals=True, composites=True, simulations=True
        )

    """
    Simulations Tab
    """

    """
    Plot triggers
    """

    def modify_triggered(self):
        self.seriesData.string.modifyPatterns()

    def individuals_triggered(self, passData: Pass):
        # Plot Individual
        line_left, line_right, line_vertical = passData.string.plotIndividual(
            self.plotWidgetIndividual
        )
        # Connect Individual trim handle signals to slots for updating
        if (
            line_left is not None
            and line_right is not None
            and line_vertical is not None
        ):
            line_left.sigPositionChangeFinished.connect(self._updateTrimL)
            line_right.sigPositionChangeFinished.connect(self._updateTrimR)
            line_vertical.sigPositionChangeFinished.connect(self._updateTrimFloor)
        # Plot Individual Trim
        passData.string.plotIndividualTrim(self.plotWidgetIndividualTrim)

    def composites_triggered(self):
        self.seriesData.string.plotOverlay(self.plotWidgetOverlay)
        self.seriesData.string.plotAverage(
            self.plotWidgetAverage
        )

    def simulations_triggered(self):
        self.seriesData.string.plotRacetrack(
            mplWidget=self.plotWidgetRacetrack,
        )
        self.seriesData.string.plotBackAndForth(
            mplWidget=self.plotWidgetBackAndForth,
        )
        self.seriesData.string.plotCVTable(
            self.tableWidgetCV
        )
