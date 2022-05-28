import os

import accupatt.config as cfg
from PyQt6 import uic
from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot, QSignalBlocker
from PyQt6.QtWidgets import (
    QPushButton,
    QCheckBox,
    QListWidget,
    QListWidgetItem,
    QRadioButton,
    QSlider,
    QSpinBox,
    QTableWidget,
    QTabWidget,
)
from pyqtgraph import PlotWidget

from accupatt.models.passData import Pass
from accupatt.models.seriesData import SeriesData
from accupatt.widgets.mplwidget import MplWidget
from accupatt.windows.stringAdvancedOptions import StringAdvancedOptions
from accupatt.windows.stringPass import StringPass

Ui_Form, baseclass = uic.loadUiType(
    os.path.join(os.getcwd(), "resources", "stringMainWidget.ui")
)


class StringMainWidget(baseclass):

    request_file_save = pyqtSignal()

    def __init__(self, parent, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        self.parent = parent
        # Typed UI Accessors, connect built-in signals to custom slots
        self.listWidgetPass: QListWidget = self.ui.listWidgetPass
        self.listWidgetPass.itemSelectionChanged.connect(self.passSelectionChanged)
        self.listWidgetPass.itemChanged[QListWidgetItem].connect(self.passItemChanged)
        self.buttonEditPass: QPushButton = self.ui.buttonEditPass
        self.buttonEditPass.clicked.connect(self.editPass)
        self.checkBoxPassSmooth: QCheckBox = self.ui.checkBoxPassSmooth
        self.checkBoxPassSmooth.stateChanged[int].connect(self.passSmoothChanged)
        self.checkBoxPassCenter: QCheckBox = self.ui.checkBoxPassCenter
        self.checkBoxPassCenter.stateChanged[int].connect(self.passCenterChanged)
        self.checkBoxPassRebase: QCheckBox = self.ui.checkBoxPassRebase
        self.checkBoxPassRebase.stateChanged[int].connect(self.passRebaseChanged)
        self.buttonAdvancedOptionsPass: QPushButton = self.ui.buttonAdvancedOptionsPass
        self.buttonAdvancedOptionsPass.clicked.connect(self.clickedAdvancedOptionsPass)
        self.checkBoxSeriesSmooth: QCheckBox = self.ui.checkBoxSeriesSmooth
        self.checkBoxSeriesSmooth.stateChanged[int].connect(self.seriesSmoothChanged)
        self.checkBoxSeriesCenter: QCheckBox = self.ui.checkBoxSeriesCenter
        self.checkBoxSeriesCenter.stateChanged[int].connect(self.seriesCenterChanged)
        self.checkBoxSeriesEqualize: QCheckBox = self.ui.checkBoxSeriesEqualize
        self.checkBoxSeriesEqualize.stateChanged[int].connect(
            self.seriesEqualizeChanged
        )
        self.buttonAdvancedOptionsSeries: QPushButton = (
            self.ui.buttonAdvancedOptionsSeries
        )
        self.buttonAdvancedOptionsSeries.clicked.connect(
            self.clickedAdvancedOptionsSeries
        )
        self.spinBoxSwathAdjusted: QSpinBox = self.ui.spinBoxSwathAdjusted
        self.spinBoxSwathAdjusted.valueChanged[int].connect(self.swathAdjustedChanged)
        self.sliderSimulatedSwath: QSlider = self.ui.sliderSimulatedSwath
        self.sliderSimulatedSwath.valueChanged[int].connect(self.swathAdjustedChanged)
        self.tabWidget: QTabWidget = self.ui.tabWidget
        self.plotWidgetIndividual: PlotWidget = self.ui.plotWidgetIndividual
        self.plotWidgetIndividualTrim: PlotWidget = self.ui.plotWidgetIndividualTrim
        self.plotWidgetOverlay: MplWidget = self.ui.plotWidgetOverlay
        self.plotWidgetAverage: MplWidget = self.ui.plotWidgetAverage
        self.plotWidgetRacetrack: MplWidget = self.ui.plotWidgetRacetrack
        self.plotWidgetBackAndForth: MplWidget = self.ui.plotWidgetBackAndForth
        self.spinBoxSimulatedPasses: QSpinBox = self.ui.spinBoxSimulatedPasses
        self.spinBoxSimulatedPasses.valueChanged[int].connect(
            self.simulatedPassesChanged
        )
        self.tableWidgetCV: QTableWidget = self.ui.tableWidgetCV

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
        self.updatePassListWidget(index_to_select=-1)
        # Update the Pass Data Mod Options Silently, then plot individuals
        self.passSelectionChanged()
        # Create Average Pattern and apply Mods Silently
        self._updatePlots(modify=True)
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
            self._updatePlots(modify=True, composites=True, simulations=True)

    """
    Pass List Widget
    """

    @pyqtSlot()
    def passSelectionChanged(self):
        if passData := self._getCurrentPass():
            with QSignalBlocker(self.checkBoxPassCenter):
                self.checkBoxPassCenter.setEnabled(not passData.string.rebase)
                self.checkBoxPassCenter.setChecked(passData.string.center)
            with QSignalBlocker(self.checkBoxPassSmooth):
                self.checkBoxPassSmooth.setChecked(passData.string.smooth)
            with QSignalBlocker(self.checkBoxPassRebase):
                self.checkBoxPassRebase.setChecked(passData.string.rebase)
            # Update the info labels on the individual pass tab
            if passData.has_string_data():
                self.buttonEditPass.setText(f"Edit {passData.name}")
            else:
                self.buttonEditPass.setText(f"Capture {passData.name}")
            # Update Plots
            self._updatePlots(individuals=True)

    @pyqtSlot(QListWidgetItem)
    def passItemChanged(self, item: QListWidgetItem):
        # Checkstate on item changed
        # If new state is unchecked, make it partial
        if item.checkState() == Qt.CheckState.Unchecked:
            item.setCheckState(Qt.CheckState.PartiallyChecked)
        # Update SeriesData -> Pass object
        p = self.seriesData.passes[self.listWidgetPass.row(item)]
        p.string_include_in_composite = (item.checkState() == Qt.CheckState.Checked)
        # Replot composites, simulations
        self._updatePlots(modify=True, composites=True, simulations=True)

    def updatePassListWidget(self, index_to_select: int):
        with QSignalBlocker(self.listWidgetPass):
            self.listWidgetPass.clear()
            for p in self.seriesData.passes:
                item = QListWidgetItem(p.name, self.listWidgetPass)
                item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
                item.setCheckState(Qt.CheckState.Unchecked)
                if p.has_string_data():
                    item.setFlags(
                        Qt.ItemFlag.ItemIsEnabled
                        | Qt.ItemFlag.ItemIsSelectable
                        | Qt.ItemFlag.ItemIsUserCheckable
                    )
                    item.setCheckState(
                        Qt.CheckState.Checked
                        if p.string_include_in_composite
                        else Qt.CheckState.PartiallyChecked
                    )
            self.listWidgetPass.setCurrentRow(index_to_select)

    """
    Edit Pass Button & Methods
    """

    @pyqtSlot()
    def editPass(self):
        if passData := self._getCurrentPass():
            e = StringPass(passData=passData, parent=self.parent)
            e.accepted.connect(self.onEditPassAccepted)
            e.show()

    @pyqtSlot()
    def onEditPassAccepted(self):
        # Auto-populate pass observables to blank entries
        self.seriesData.fill_common_pass_observables()
        # Handles checking of string pass list widget
        self.updatePassListWidget(index_to_select=self.listWidgetPass.currentRow())
        # Replot all but individuals
        self._updatePlots(
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
        if passData := self._getCurrentPass():
            passData.string.smooth = Qt.CheckState(checkstate) == Qt.CheckState.Checked
            self._updatePlots(
                modify=True, individuals=True, composites=True, simulations=True
            )

    @pyqtSlot(int)
    def passCenterChanged(self, checkstate):
        if passData := self._getCurrentPass():
            passData.string.center = Qt.CheckState(checkstate) == Qt.CheckState.Checked
            self._updatePlots(modify=True, composites=True, simulations=True)

    @pyqtSlot(int)
    def passRebaseChanged(self, checkstate):
        if passData := self._getCurrentPass():
            passData.string.rebase = Qt.CheckState(checkstate) == Qt.CheckState.Checked
            if passData.string.rebase:
                passData.string.center = True
                self.checkBoxPassCenter.setChecked(passData.string.center)
            self.checkBoxPassCenter.setEnabled(not passData.string.rebase)
            self._updatePlots(
                modify=True, individuals=True, composites=True, simulations=True
            )

    @pyqtSlot()
    def clickedAdvancedOptionsPass(self):
        if passData := self._getCurrentPass():
            e = StringAdvancedOptions(passData=passData, parent=self)
            e.accepted.connect(self._advancedOptionsPassUpdated)
            e.exec()

    def _advancedOptionsPassUpdated(self):
        self._updatePlots(
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
        self._updatePlots(modify=True, composites=True, simulations=True)

    @pyqtSlot(int)
    def seriesSmoothChanged(self, checkstate):
        self.seriesData.string.smooth = (
            Qt.CheckState(checkstate) == Qt.CheckState.Checked
        )
        self._updatePlots(modify=True, composites=True, simulations=True)

    @pyqtSlot(int)
    def seriesEqualizeChanged(self, checkstate):
        self.seriesData.string.equalize_integrals = (
            Qt.CheckState(checkstate) == Qt.CheckState.Checked
        )
        self._updatePlots(modify=True, composites=True, simulations=True)

    @pyqtSlot()
    def clickedAdvancedOptionsSeries(self):
        e = StringAdvancedOptions(seriesData=self.seriesData, parent=self)
        e.accepted.connect(self._advancedOptionsSeriesUpdated)
        e.exec()

    def _advancedOptionsSeriesUpdated(self):
        self._updatePlots(modify=True, composites=True, simulations=True)

    @pyqtSlot(int)
    def swathAdjustedChanged(self, swath: int):
        self.seriesData.string.swath_adjusted = swath
        with QSignalBlocker(self.spinBoxSwathAdjusted):
            self.spinBoxSwathAdjusted.setValue(swath)
        with QSignalBlocker(self.sliderSimulatedSwath):
            self.sliderSimulatedSwath.setValue(swath)
        self._updatePlots(composites=True, simulations=True)

    """
    Individual Passes Tab
    """

    @pyqtSlot(object)
    def _updateTrimL(self, object):
        self._getCurrentPass().string.user_set_trim_left(object.value())
        self._updatePlots(
            modify=True, individuals=True, composites=True, simulations=True
        )

    @pyqtSlot(object)
    def _updateTrimR(self, object):
        self._getCurrentPass().string.user_set_trim_right(object.value())
        self._updatePlots(
            modify=True, individuals=True, composites=True, simulations=True
        )

    @pyqtSlot(object)
    def _updateTrimFloor(self, object):
        self._getCurrentPass().string.user_set_trim_floor(object.value())
        self._updatePlots(
            modify=True, individuals=True, composites=True, simulations=True
        )

    """
    Simulations Tab
    """

    @pyqtSlot(int)
    def simulatedPassesChanged(self, numAdjascentPasses):
        self.seriesData.string.simulated_adjascent_passes = numAdjascentPasses
        self._updatePlots(simulations=True)

    """
    Plot trigger
    """

    def _updatePlots(
        self, modify=False, individuals=False, composites=False, simulations=False
    ):
        if modify:
            self.seriesData.string.modifyPatterns()
        if individuals:
            if (passData := self._getCurrentPass()) != None:
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
        if composites:
            self.seriesData.string.plotOverlay(self.plotWidgetOverlay)
            self.seriesData.string.plotAverage(
                self.plotWidgetAverage, self.seriesData.string.swath_adjusted
            )
        if simulations:
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

    """
    Convenience Accessors
    """

    def _getCurrentPass(self) -> Pass:
        passData: Pass = None
        # Check if a pass is selected
        if (passIndex := self.listWidgetPass.currentRow()) != -1:
            passData = self.seriesData.passes[passIndex]
        return passData
