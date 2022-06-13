from PyQt6 import uic
from PyQt6.QtCore import pyqtSignal, pyqtSlot, QSignalBlocker, Qt
from PyQt6.QtWidgets import (
    QPushButton,
    QCheckBox,
    QListWidget,
    QListWidgetItem,
    QSlider,
    QSpinBox,
    QTableWidget,
    QTabWidget,
    QWidget
)
from accupatt.models.passData import Pass
from accupatt.models.passDataBase import PassDataBase
from accupatt.models.seriesData import SeriesData
from accupatt.models.seriesDataBase import SeriesDataBase
from accupatt.widgets.mplwidget import MplWidget
from accupatt.windows.editOptBase import EditOptBase

class TabWidgetBase(QWidget):
    
    request_file_save = pyqtSignal()
    
    def __init__(self, ui_file, subtype, parent, *args, **kwargs):
        super().__init__(*args, **kwargs)
        ui_form, _ = uic.loadUiType(ui_file)
        self.ui  = ui_form()
        self.ui.setupUi(self)
        # Whether String or Cards
        self.subtype = subtype
        self.seriesData = SeriesData()
        #self.parent = parent
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
        self.buttonAdvancedOptionsPass: QPushButton = self.ui.buttonAdvancedOptionsPass
        self.buttonAdvancedOptionsPass.clicked.connect(self.clickedAdvancedOptionsPass)
        self.checkBoxSeriesSmooth: QCheckBox = self.ui.checkBoxSeriesSmooth
        self.checkBoxSeriesSmooth.stateChanged[int].connect(self.seriesSmoothChanged)
        self.checkBoxSeriesCenter: QCheckBox = self.ui.checkBoxSeriesCenter
        self.checkBoxSeriesCenter.stateChanged[int].connect(self.seriesCenterChanged)
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
        # Populate Series Data Mod options silently
        with QSignalBlocker(self.checkBoxSeriesCenter):
            self.checkBoxSeriesCenter.setChecked(self.getSeriesOpt().center)
        with QSignalBlocker(self.checkBoxSeriesSmooth):
            self.checkBoxSeriesSmooth.setChecked(self.getSeriesOpt().smooth)
        with QSignalBlocker(self.spinBoxSimulatedPasses):
            self.spinBoxSimulatedPasses.setValue(
                self.seriesData.string.simulated_adjascent_passes
            )
        # Ensure data is processed
        self.updatePlots(process=True, modify=True)
        # Silently populate pass list ui
        self.updatePassListWidget()
        # Silently update Pass Data Mod Opts, then plot individuals
        self.passSelectionChanged()
        # Silently update adjusted swath control limits
        self.setAdjustedSwathFromTargetSwath(replace_adjusted_swath=False, update_plots=False)
        # Update Adjusted Swath, then plot composites and simulations
        self.swathAdjustedChanged(swath=self.getSeriesOpt().swath_adjusted)
        
    @pyqtSlot()
    def setAdjustedSwathFromTargetSwath(self, replace_adjusted_swath=True, update_plots=True):
        swath = self.seriesData.info.swath
        swath_units = self.seriesData.info.swath_units
        opt = self.getSeriesOpt()
        # Update Card Adjusted Swath
        if replace_adjusted_swath:
            opt.swath_adjusted = swath
            opt.swath_units = swath_units
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
        if not (passData:=self.getCurrentPass()):
            return
        opt = self.getPassOpt(passData)
        with QSignalBlocker(self.checkBoxPassCenter):
            self.checkBoxPassCenter.setChecked(opt.center)
        with QSignalBlocker(self.checkBoxPassSmooth):
            self.checkBoxPassSmooth.setChecked(opt.smooth)
        self.updateEditButton(opt.has_data(), passData.name)
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
        self.getPassOpt(p).include_in_composite = (item.checkState() == Qt.CheckState.Checked)
        # Replot composites, simulations
        self.updatePlots(modify=True, composites=True, simulations=True, distributions=True)
    
    def updatePassListWidget(self, index_to_select: int = -1):
        with QSignalBlocker(self.listWidgetPass):
            self.listWidgetPass.clear()
            for p in self.seriesData.passes:
                item = QListWidgetItem(p.name, self.listWidgetPass)
                item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
                item.setCheckState(Qt.CheckState.Unchecked)
                if self.getPassOpt(p).has_data():
                    item.setFlags(
                        Qt.ItemFlag.ItemIsEnabled
                        | Qt.ItemFlag.ItemIsSelectable
                        | Qt.ItemFlag.ItemIsUserCheckable
                    )
                    item.setCheckState(
                        Qt.CheckState.Checked
                        if self.getPassOpt(p).include_in_composite
                        else Qt.CheckState.PartiallyChecked
                    )
            index = len(self.seriesData.passes)-1 if index_to_select == -1 else index_to_select
            self.listWidgetPass.setCurrentRow(index)
    
    """
    Edit Pass Button & Methods
    """
    
    @pyqtSlot()
    def editPass(self):
        # Inherited class should override
        pass
    
    @pyqtSlot()
    def onEditPassAccepted(self):
        self.seriesData.fill_common_pass_observables()
        self.request_file_save.emit()
        self.updatePassListWidget(index_to_select=self.listWidgetPass.currentRow())
        self.updateEditButton(has_data=self.getPassOpt().has_data(), pass_name=self.getCurrentPass().name)
        self.tabWidget.setCurrentIndex(0)
        self.updatePlots(process=True, modify=True, individuals=True, composites=True, simulations=True, distributions=True)
    
    def updateEditButton(self, has_data, pass_name):
        prefix = "Edit" if has_data else "Capture"
        self.buttonEditPass.setText(f"{prefix} {pass_name}")
    
    """
    Pass Data Mod Options
    """
    
    @pyqtSlot(int)
    def passSmoothChanged(self, checkstate):
        if self.getCurrentPass():
            self.getPassOpt().smooth = Qt.CheckState(checkstate) == Qt.CheckState.Checked
            self.updatePlots(modify=True, individuals=True, composites=True, simulations=True)
            
    @pyqtSlot(int)
    def passCenterChanged(self, checkstate):
        if self.getCurrentPass():
            self.getPassOpt().center = Qt.CheckState(checkstate) == Qt.CheckState.Checked
            self.updatePlots(modify=True, composites=True, simulations=True)
            
    @pyqtSlot()
    def clickedAdvancedOptionsPass(self):
        if self.getCurrentPass():
            e = EditOptBase(optBase=self.getPassOpt(), 
                            window_units=self.seriesData.info.swath_units, 
                            parent=self.parent())
            e.accepted.connect(self._advancedOptionsPassUpdated)
    
    def _advancedOptionsPassUpdated(self):
        self.updatePlots(
            modify=True, individuals=False, composites=True, simulations=True
        )
            
    """
    Series Data Mod Options
    """

    @pyqtSlot(int)
    def seriesCenterChanged(self, checkstate):
        self.getSeriesOpt().center = (
            Qt.CheckState(checkstate) == Qt.CheckState.Checked
        )
        self.updatePlots(modify=True, composites=True, simulations=True)
        
    @pyqtSlot(int)
    def seriesSmoothChanged(self, checkstate):
        self.getSeriesOpt().smooth = (
            Qt.CheckState(checkstate) == Qt.CheckState.Checked
        )
        self.updatePlots(modify=True, composites=True, simulations=True)
        
    @pyqtSlot()
    def clickedAdvancedOptionsSeries(self):
        e = EditOptBase(optBase=self.getSeriesOpt(), 
                        window_units=self.seriesData.info.swath_units, 
                        parent=self.parent())
        e.accepted.connect(self._advancedOptionsSeriesUpdated)
    
    def _advancedOptionsSeriesUpdated(self):
        self.updatePlots(modify=True, composites=True, simulations=True)
        
    @pyqtSlot(int)
    def swathAdjustedChanged(self, swath: int):
        self.getSeriesOpt().swath_adjusted = swath
        with QSignalBlocker(self.spinBoxSwathAdjusted):
            self.spinBoxSwathAdjusted.setValue(swath)
        with QSignalBlocker(self.sliderSimulatedSwath):
            self.sliderSimulatedSwath.setValue(swath)
        self.updatePlots(composites=True, simulations=True)
    
    """
    Simulations Tab
    """

    @pyqtSlot(int)
    def simulatedPassesChanged(self, numAdjascentPasses):
        self.getSeriesOpt().simulated_adjascent_passes = numAdjascentPasses
        self.updatePlots(simulations=True)
    
    """
    plot triggers
    """
    
    def updatePlots(self, process=False, modify=False, individuals=False, composites=False, simulations=False, distributions=False):
        if process:
            self.reprocess_triggered()
        if modify:
            self.modify_triggered()
        if individuals and (p:=self.getCurrentPass()):
            self.individuals_triggered(passData=p)
        if composites:
            self.composites_triggered()
        if simulations:
            self.simulations_triggered()
        if distributions:
            self.distributions_triggered()
            
    def reprocess_triggered(self):
        # Should override in inherited_class
        pass
    
    def modify_triggered(self):
        # Should override in inherited_class
        pass

    def individuals_triggered(self):
        # Should override in inherited_class
        pass
    
    def composites_triggered(self):
        # Should override in inherited_class
        pass
    
    def simulations_triggered(self):
        # Should override in inherited_class
        pass
    
    def distributions_triggered(self):
        # Should override in inherited_class
        pass
    
    """
    Convenience Accessors
    """

    def getCurrentPass(self) -> Pass:
        passData: Pass = None
        # Check if a pass is selected
        if (passIndex := self.listWidgetPass.currentRow()) != -1:
            passData = self.seriesData.passes[passIndex]
        return passData
    
    def getSeriesOpt(self) -> SeriesDataBase:
        if self.subtype == 'string':
            return self.seriesData.string
        elif self.subtype == 'cards':
            return self.seriesData.cards  
        else:
            return SeriesDataBase()
    
    def getPassOpt(self, passData: Pass = None) -> PassDataBase:
        if passData == None: passData = self.getCurrentPass()
        if self.subtype == 'string':
            return passData.string
        elif self.subtype == 'cards':
            return passData.cards
        else:
            return PassDataBase()