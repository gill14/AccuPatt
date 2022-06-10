import os

import accupatt.config as cfg
from PyQt6.QtCore import Qt, pyqtSlot, QSignalBlocker
from PyQt6.QtWidgets import (
    QCheckBox,
    QListWidgetItem,
)
from pyqtgraph import PlotWidget

from accupatt.models.passData import Pass
from accupatt.models.seriesData import SeriesData
from accupatt.widgets.tabWidgetBase import TabWidgetBase
from accupatt.windows.stringAdvancedOptions import StringAdvancedOptions
from accupatt.windows.stringPass import StringPass


class TabWidgetString(TabWidgetBase):

    def __init__(self, parent, *args, **kwargs):
        super().__init__(ui_file=os.path.join(os.getcwd(), "resources", "stringMainWidget.ui"), parent=parent, *args, **kwargs)
        
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
        self.seriesData = seriesData
        # Populate Series Data Mod Options Silently
        with QSignalBlocker(self.checkBoxSeriesCenter):
            self.checkBoxSeriesCenter.setChecked(self.seriesData.string.center)
        with QSignalBlocker(self.checkBoxSeriesSmooth):
            self.checkBoxSeriesSmooth.setChecked(self.seriesData.string.smooth)
        with QSignalBlocker(self.checkBoxSeriesEqualize):
            self.checkBoxSeriesEqualize.setChecked(
                self.seriesData.string.equalize_integrals
            )
        with QSignalBlocker(self.spinBoxSimulatedPasses):
            self.spinBoxSimulatedPasses.setValue(
                self.seriesData.string.simulated_adjascent_passes
            )
        # Update the Pass List Widget Silently
        self.updatePassListWidget()
        # Update the Pass Data Mod Options Silently, then plot individuals
        self.passSelectionChanged()
        # Create Average Pattern and apply Mods Silently
        self.updatePlots(modify=True)
        # Update Adjusted Swath Control Limits Silently
        self.setAdjustedSwathFromTargetSwath(replace_adjusted_swath=False, update_plots=False)
        # Update Adjusted Swath, then plot composites and simulations
        self.swathAdjustedChanged(swath=self.seriesData.string.swath_adjusted)

    @pyqtSlot()
    def setAdjustedSwathFromTargetSwath(self, replace_adjusted_swath=True, update_plots=True):
        swath = self.seriesData.info.swath
        swath_units = self.seriesData.info.swath_units
        # Update Card Adjusted Swath
        if replace_adjusted_swath:
            self.seriesData.string.swath_adjusted = swath
            self.seriesData.string.swath_units = swath_units
        # Update UI
        with QSignalBlocker(self.sliderSimulatedSwath):
            self.sliderSimulatedSwath.setValue(swath)
            self.sliderSimulatedSwath.setMinimum(round(0.5 * float(swath)))
            self.sliderSimulatedSwath.setMaximum(round(1.5 * float(swath)))
        with QSignalBlocker(self.spinBoxSwathAdjusted):
            self.spinBoxSwathAdjusted.setValue(swath)
            self.spinBoxSwathAdjusted.setSuffix(" " + swath_units)
        if update_plots:
            self.updatePlots(modify=True, composites=True, simulations=True)

    """
    Pass List Widget
    """

    @pyqtSlot()
    def passSelectionChanged(self):
        if passData := self.getCurrentPass():
            with QSignalBlocker(self.checkBoxPassCenter):
                self.checkBoxPassCenter.setEnabled(not passData.string.rebase)
                self.checkBoxPassCenter.setChecked(passData.string.center)
            with QSignalBlocker(self.checkBoxPassSmooth):
                self.checkBoxPassSmooth.setChecked(passData.string.smooth)
            with QSignalBlocker(self.checkBoxPassRebase):
                self.checkBoxPassRebase.setChecked(passData.string.rebase)
            self.updateEditButton(passData.string.has_data(), passData.name)
            # Update Plots
            self.updatePlots(individuals=True)

    @pyqtSlot(QListWidgetItem)
    def passItemChanged(self, item: QListWidgetItem):
        # Checkstate on item changed
        # If new state is unchecked, make it partial
        if item.checkState() == Qt.CheckState.Unchecked:
            item.setCheckState(Qt.CheckState.PartiallyChecked)
        # Update SeriesData -> Pass object
        p = self.seriesData.passes[self.listWidgetPass.row(item)]
        p.string.include_in_composite = (item.checkState() == Qt.CheckState.Checked)
        # Replot composites, simulations
        self.updatePlots(modify=True, composites=True, simulations=True)

    def updatePassListWidget(self, index_to_select: int = -1):
        with QSignalBlocker(self.listWidgetPass):
            self.listWidgetPass.clear()
            for p in self.seriesData.passes:
                item = QListWidgetItem(p.name, self.listWidgetPass)
                item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
                item.setCheckState(Qt.CheckState.Unchecked)
                if p.string.has_data():
                    item.setFlags(
                        Qt.ItemFlag.ItemIsEnabled
                        | Qt.ItemFlag.ItemIsSelectable
                        | Qt.ItemFlag.ItemIsUserCheckable
                    )
                    item.setCheckState(
                        Qt.CheckState.Checked
                        if p.string.include_in_composite
                        else Qt.CheckState.PartiallyChecked
                    )
            index = len(self.seriesData.passes)-1 if index_to_select == -1 else index_to_select
            self.listWidgetPass.setCurrentRow(index)

    """
    Edit Pass Button & Methods
    """

    @pyqtSlot()
    def editPass(self):
        if passData := self.getCurrentPass():
            e = StringPass(passData=passData, parent=self.parent())
            e.accepted.connect(self.onEditPassAccepted)
            e.show()

    @pyqtSlot()
    def onEditPassAccepted(self):
        # Auto-populate pass observables to blank entries
        self.seriesData.fill_common_pass_observables()
        # Handles checking of string pass list widget
        self.updatePassListWidget(index_to_select=self.listWidgetPass.currentRow())
        # Replot all but individuals
        self.updatePlots(
            modify=True, individuals=False, composites=True, simulations=True
        )
        # Plot individuals and update capture button text
        self.passSelectionChanged()
        self.tabWidget.setCurrentIndex(0)
        # Update datafile
        self.request_file_save.emit()

    """
    Pass Data Mod Options
    """

    @pyqtSlot(int)
    def passSmoothChanged(self, checkstate):
        if passData := self.getCurrentPass():
            passData.string.smooth = Qt.CheckState(checkstate) == Qt.CheckState.Checked
            self.updatePlots(
                modify=True, individuals=True, composites=True, simulations=True
            )

    @pyqtSlot(int)
    def passCenterChanged(self, checkstate):
        if passData := self.getCurrentPass():
            passData.string.center = Qt.CheckState(checkstate) == Qt.CheckState.Checked
            self.updatePlots(modify=True, composites=True, simulations=True)

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

    @pyqtSlot()
    def clickedAdvancedOptionsPass(self):
        if passData := self.getCurrentPass():
            e = StringAdvancedOptions(passData=passData, parent=self)
            e.accepted.connect(self._advancedOptionsPassUpdated)
            e.exec()

    def _advancedOptionsPassUpdated(self):
        self.updatePlots(
            modify=True, individuals=False, composites=True, simulations=True
        )

    """
    Series Data Mod Options
    """

    @pyqtSlot(int)
    def seriesCenterChanged(self, checkstate):
        self.seriesData.string.center = (
            Qt.CheckState(checkstate) == Qt.CheckState.Checked
        )
        self.updatePlots(modify=True, composites=True, simulations=True)

    @pyqtSlot(int)
    def seriesSmoothChanged(self, checkstate):
        self.seriesData.string.smooth = (
            Qt.CheckState(checkstate) == Qt.CheckState.Checked
        )
        self.updatePlots(modify=True, composites=True, simulations=True)

    @pyqtSlot(int)
    def seriesEqualizeChanged(self, checkstate):
        self.seriesData.string.equalize_integrals = (
            Qt.CheckState(checkstate) == Qt.CheckState.Checked
        )
        self.updatePlots(modify=True, composites=True, simulations=True)

    @pyqtSlot()
    def clickedAdvancedOptionsSeries(self):
        e = StringAdvancedOptions(seriesData=self.seriesData, parent=self)
        e.accepted.connect(self._advancedOptionsSeriesUpdated)
        e.exec()

    def _advancedOptionsSeriesUpdated(self):
        self.updatePlots(modify=True, composites=True, simulations=True)

    @pyqtSlot(int)
    def swathAdjustedChanged(self, swath: int):
        self.seriesData.string.swath_adjusted = swath
        with QSignalBlocker(self.spinBoxSwathAdjusted):
            self.spinBoxSwathAdjusted.setValue(swath)
        with QSignalBlocker(self.sliderSimulatedSwath):
            self.sliderSimulatedSwath.setValue(swath)
        self.updatePlots(composites=True, simulations=True)

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

    @pyqtSlot(int)
    def simulatedPassesChanged(self, numAdjascentPasses):
        self.seriesData.string.simulated_adjascent_passes = numAdjascentPasses
        self.updatePlots(simulations=True)

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
            line_vertical.sigPositionChangeFinished.connect(
                self._updateTrimFloor
            )
        # Plot Individual Trim
        passData.string.plotIndividualTrim(self.plotWidgetIndividualTrim)
        
    def composites_triggered(self):
        self.seriesData.string.plotOverlay(self.plotWidgetOverlay)
        self.seriesData.string.plotAverage(
            self.plotWidgetAverage, self.seriesData.string.swath_adjusted
        )

    def simulations_triggered(self):
        showEntireWindow = (
            cfg.get_string_simulation_view_window()==cfg.STRING_SIMULATINO_VIEW_WINDOW_ALL
        )
        self.seriesData.string.plotRacetrack(
            mplWidget=self.plotWidgetRacetrack,
            swath_width=self.seriesData.string.swath_adjusted,
            showEntireWindow=showEntireWindow,
        )
        self.seriesData.string.plotBackAndForth(
            mplWidget=self.plotWidgetBackAndForth,
            swath_width=self.seriesData.string.swath_adjusted,
            showEntireWindow=showEntireWindow,
        )
        self.seriesData.string.plotCVTable(
            self.tableWidgetCV, self.seriesData.string.swath_adjusted
        )   

