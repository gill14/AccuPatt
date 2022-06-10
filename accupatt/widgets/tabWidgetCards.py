import os

import accupatt.config as cfg
from PyQt6.QtCore import QSortFilterProxyModel, Qt, QTimer, pyqtSlot, QSignalBlocker
from PyQt6.QtWidgets import (
    QComboBox,
    QHeaderView,
    QListWidgetItem,
    QProgressDialog,
    QTableWidget,
    QTableView,
)
from pyqtgraph import PlotWidget
from accupatt.helpers.cardStatTabelModel import CardStatTableModel, ComboBoxDelegate

from accupatt.models.passData import Pass
from accupatt.models.seriesData import SeriesData
from accupatt.models.sprayCard import SprayCard
from accupatt.models.sprayCardComposite import SprayCardComposite
from accupatt.widgets.mplwidget import MplWidget
from accupatt.widgets.tabWidgetBase import TabWidgetBase
from accupatt.windows.cardManager import CardManager


class TabWidgetCards(TabWidgetBase):

    def __init__(self, parent, *args, **kwargs):
        super().__init__(ui_file=os.path.join(os.getcwd(), "resources", "cardMainWidget.ui"), parent=parent, *args, **kwargs)
        
        self.plotWidgetPass: PlotWidget = self.ui.plotWidgetPass
        self.tableViewPass: QTableView = self.ui.tableViewPass
        
        self.comboBoxDistPass: QComboBox = self.ui.comboBoxDistPass
        self.comboBoxDistPass.currentIndexChanged[int].connect(self.distPassChanged)
        self.comboBoxDistCard: QComboBox = self.ui.comboBoxDistCard
        self.comboBoxDistCard.currentIndexChanged[int].connect(self.distCardChanged)
        self.plotWidgetDropDist1: MplWidget = self.ui.plotWidgetDropDist1
        self.plotWidgetDropDist2: MplWidget = self.ui.plotWidgetDropDist2
        self.tableWidgetCompositeStats: QTableWidget = self.ui.tableWidgetCompositeStats
        
        # Flag for accepting file saved signals
        self.delayed_request_open_edit_pass = False
        
    """
    External Method to fill data
    """

    def setData(self, seriesData: SeriesData):
        self.seriesData = seriesData
        # Populate Series Data Mod Options Silently
        with QSignalBlocker(self.checkBoxSeriesCenter):
            self.checkBoxSeriesCenter.setChecked(self.seriesData.cards.center)
        with QSignalBlocker(self.spinBoxSimulatedPasses):
            self.spinBoxSimulatedPasses.setValue(
                self.seriesData.cards.simulated_adjascent_passes
            )
        # Process Cards to get stat data
        self.processCards()
        # Refresh listWidget
        self.updatePassListWidget()
        # Update the Pass Data Mod Options Silently, then plot individuals
        self.passSelectionChanged()
        # Update Adjusted Swath Control Limits Silently
        self.setAdjustedSwathFromTargetSwath(replace_adjusted_swath=False, update_plots=False)
        # Update Adjusted Swath, then plot composites and simulations
        self.swathAdjustedChanged(swath=self.seriesData.cards.swath_adjusted)
        # Update Dist Comboboxes/plots
        self.distPassChanged(0)
          
    def processCards(self):
        card_list: list[SprayCard] = []
        card_identifier_list: list[str] = []
        for p in self.seriesData.passes:
            for c in p.cards.card_list:
                card_list.append(c)
                card_identifier_list.append(f"{p.name} - {c.name}")
        if not card_list:
            return
        prog = QProgressDialog(self)
        prog.setMinimumDuration(0)
        prog.setWindowModality(Qt.WindowModality.WindowModal)
        prog.setRange(0, len(card_list))
        for i, card in enumerate(card_list):
            prog.setValue(i)
            prog.setLabelText(
                f"Processing {card_identifier_list[i]} and caching droplet statistics"
            )
            if card.has_image:
                # Process image
                card.images_processed()
                # Cache droplet stats
                card.stats.set_volumetric_stats()
            if prog.wasCanceled():
                return
        prog.setValue(len(card_list))
            
    @pyqtSlot()
    def setAdjustedSwathFromTargetSwath(self, replace_adjusted_swath=True, update_plots=True):
        swath = self.seriesData.info.swath
        swath_units = self.seriesData.info.swath_units
        # Update Card Adjusted Swath
        if replace_adjusted_swath:
            self.seriesData.cards.swath_adjusted = swath
            self.seriesData.cards.swath_units = swath_units
        # Update UI
        with QSignalBlocker(self.sliderSimulatedSwath):
            self.sliderSimulatedSwath.setValue(swath)
            self.sliderSimulatedSwath.setMinimum(round(0.5 * float(swath)))
            self.sliderSimulatedSwath.setMaximum(round(1.5 * float(swath)))
        with QSignalBlocker(self.spinBoxSwathAdjusted):
            self.spinBoxSwathAdjusted.setValue(swath)
            self.spinBoxSwathAdjusted.setSuffix(" " + swath_units)
        if update_plots:
            self.updatePlots(composites=True, simulations=True)
    
    @pyqtSlot(str)
    def onCurrentFileChanged(self, file: str):
        self.currentFile = file
    
    """
    Pass List Widget
    """
    
    @pyqtSlot()
    def passSelectionChanged(self):
        if passData := self.getCurrentPass():
            self.updateEditButton(passData.cards.has_data(), passData.name)
            # Set Pass Data Mod Options
            with QSignalBlocker(self.checkBoxPassCenter):
                self.checkBoxPassCenter.setChecked(passData.cards.center)
            # Replot individual
            self.updatePlots(individuals=True)

    @pyqtSlot(QListWidgetItem)
    def passItemChanged(self, item: QListWidgetItem):
        # Checkstate on item changed
        # If new state is unchecked, make it partial
        if item.checkState() == Qt.CheckState.Unchecked:
            item.setCheckState(Qt.CheckState.PartiallyChecked)
        # Update SeriesData -> Pass object
        p = self.seriesData.passes[self.listWidgetPass.row(item)]
        p.cards.include_in_composite = (item.checkState() == Qt.CheckState.Checked)
        # Replot and Recalculate composites
        self.updatePlots(composites=True, simulations=True, distributions=True)

    def updatePassListWidget(self, index_to_select: int = -1):
        with QSignalBlocker(self.listWidgetPass):
            self.listWidgetPass.clear()
            for p in self.seriesData.passes:
                item = QListWidgetItem(p.name, self.listWidgetPass)
                item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
                item.setCheckState(Qt.CheckState.Unchecked)
                if p.cards.has_data():
                    item.setFlags(
                        Qt.ItemFlag.ItemIsEnabled
                        | Qt.ItemFlag.ItemIsSelectable
                        | Qt.ItemFlag.ItemIsUserCheckable
                    )
                    item.setCheckState(
                        Qt.CheckState.Checked
                        if p.cards.include_in_composite
                        else Qt.CheckState.PartiallyChecked
                    )
            index = len(self.seriesData.passes)-1 if index_to_select == -1 else index_to_select
            self.listWidgetPass.setCurrentRow(index)
        with QSignalBlocker(self.comboBoxDistPass):
            self.comboBoxDistPass.clear()
            self.comboBoxDistPass.addItem("Series Composite")
            self.comboBoxDistPass.addItems([p.name for p in self.seriesData.passes if p.cards.has_data()])

    """
    Edit Pass Button & Methods
    """
    
    @pyqtSlot()
    def editPass(self):
        # Get a handle on the currently selected pass
        passData = self.getCurrentPass()
        # Trigger file save if filapath needed
        if self.currentFile == None or self.currentFile == "":
            self.delayed_request_open_edit_pass = True
            self.request_file_save.emit()
            return
        # Open the Edit Card List window for currently selected pass
        e = CardManager(
            passData=passData,
            seriesData=self.seriesData,
            filepath=self.currentFile,
            parent=self.parent(),
        )
        # Connect Slot to save file each time the data is changed
        # This is prudent as card images are added
        e.passDataChanged.connect(lambda: self.request_file_save.emit())
        # Connect Slot to handle the accept and close of Card Manager
        e.accepted.connect(self.cardManagerOnClose)
        # Start Loop
        e.exec()

    @pyqtSlot()
    def cardManagerOnClose(self):
        # Save all changes
        self.request_file_save.emit()
        # Handles checking of card pass list widget
        self.updatePassListWidget(
            index_to_select=self.listWidgetPass.currentRow()
        )
        # Repopulates card list widget, updates rest of ui
        self.passSelectionChanged()
        self.updatePlots(composites=True, simulations=True, distributions=True)
    
    @pyqtSlot(str)
    def _acceptFileSaveSignal(self, file: str):
        self.currentFile = file
        if self.delayed_request_open_edit_pass:
            self.delayed_request_open_edit_pass = False  
            QTimer.singleShot(1000,self.editPass)
    """
    Pass Data Mod Options
    """
    
    @pyqtSlot(int)
    def passCenterChanged(self, checkstate):
        self.getCurrentPass().cards.center = (
            Qt.CheckState(checkstate) == Qt.CheckState.Checked
        )
        self.updatePlots(composites=True, simulations=True)
        
    @pyqtSlot(int)
    def passSmoothChanged(self, checkstate):
        pass
    
    @pyqtSlot()
    def clickedAdvancedOptionsPass(self):
        pass

    def _advancedOptionsPassUpdated(self):
        pass
    
    """
    Series Data Mod Options
    """
    
    @pyqtSlot(int)
    def seriesCenterChanged(self, checkstate):
        self.seriesData.cards.center = (
            Qt.CheckState(checkstate) == Qt.CheckState.Checked
        )
        self.updatePlots(composites=True, simulations=True)
    
    @pyqtSlot(int)
    def seriesSmoothChanged(self, checkstate):
        pass
    
    @pyqtSlot()
    def clickedAdvancedOptionsSeries(self):
        pass

    def _advancedOptionsSeriesUpdated(self):
        pass
        
    @pyqtSlot(int)
    def swathAdjustedChanged(self, swath: int):
        self.seriesData.cards.swath_adjusted = swath
        with QSignalBlocker(self.spinBoxSwathAdjusted):
            self.spinBoxSwathAdjusted.setValue(swath)
        with QSignalBlocker(self.sliderSimulatedSwath):
            self.sliderSimulatedSwath.setValue(swath)
        self.updatePlots(composites=True, simulations=True)

    """
    Individual Passes Tab
    """

    @pyqtSlot()
    def passStatTableValueChanged(self):
        self.updatePlots(individuals=True, composites=True, simulations=True)
    
    """
    Simulations Tab
    """
    
    @pyqtSlot(int)
    def simulatedPassesChanged(self, numAdjascentPasses: int):
        self.seriesData.cards.simulated_adjascent_passes = numAdjascentPasses
        self.updatePlots(simulations=True)
    
    """
    Distributions Tab
    """
    
    @pyqtSlot(int)
    def distPassChanged(self, index: int):
        with QSignalBlocker(self.comboBoxDistCard):
            self.comboBoxDistCard.clear()
            self.comboBoxDistCard.setEnabled(index>0)
            if index > 0:
                self.comboBoxDistCard.addItem("Pass Composite")
                passData = self.getActiveCardPasses()[index-1]
                self.comboBoxDistCard.addItems(
                    [card.name for card in passData.cards.card_list]
                )
            self.comboBoxDistCard.setCurrentIndex(0)
        self.distCardChanged(0)

    @pyqtSlot(int)
    def distCardChanged(self, index: int):
        self.updatePlots(distributions=True)
    
    """
    Plot triggers
    """
    
    def modify_triggered(self):
        self.processCards()
        
    def individuals_triggered(self, passData: Pass):
        passData.cards.plotCoverage(
            mplWidget=self.plotWidgetPass,
            loc_units=self.seriesData.info.swath_units,
            colorize=cfg.get_card_plot_colorize_pass(),
            mod=False,
        )
        model = CardStatTableModel()
        proxyModel = QSortFilterProxyModel()
        proxyModel.setSourceModel(model)
        self.tableViewPass.setModel(proxyModel)
        self.tableViewPass.setItemDelegateForColumn(
            3, ComboBoxDelegate(self.tableViewPass, cfg.UNITS_LENGTH_LARGE)
        )
        self.tableViewPass.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.ResizeToContents
        )
        model.loadCards(passData.cards.card_list)
        model.valueChanged.connect(self.passStatTableValueChanged)
        
    def composites_triggered(self):
        self.seriesData.cards.plotOverlay(mplWidget=self.plotWidgetOverlay)
        self.seriesData.cards.plotAverage(
            mplWidget=self.plotWidgetAverage,
            colorize=cfg.get_card_plot_colorize_average(),
        )
    
    def simulations_triggered(self):
        showEntireWindow = (
            cfg.get_card_simulation_view_window()==cfg.CARD_SIMULATINO_VIEW_WINDOW_ALL
        )
        self.seriesData.cards.plotRacetrack(
            mplWidget=self.plotWidgetRacetrack,
            swath_width=self.seriesData.cards.swath_adjusted,
            showEntireWindow=showEntireWindow,
        )
        self.seriesData.cards.plotBackAndForth(
            mplWidget=self.plotWidgetBackAndForth,
            swath_width=self.seriesData.cards.swath_adjusted,
            showEntireWindow=showEntireWindow,
        )
        self.seriesData.cards.plotCVTable(
            self.tableWidgetCV, self.seriesData.cards.swath_adjusted
        )  
        
    def distributions_triggered(self):
        composite = SprayCardComposite()
        if self.comboBoxDistPass.currentIndex() == 0:
            # "All (Series-Wise Composite)" option
            composite.buildFromSeries(seriesData=self.seriesData)
        else:
            distPassData = self.getActiveCardPasses()[self.comboBoxDistPass.currentIndex()-1]
            # "Pass X" option
            if self.comboBoxDistCard.currentIndex() == 0:
                # "All (Pass-Wise Composite)" option
                composite.buildFromPass(passData=distPassData)
            elif self.comboBoxDistCard.currentIndex() > 0:
                # "Card X" option
                card = distPassData.cards.card_list[
                    self.comboBoxDistCard.currentIndex() - 1
                ]
                composite.buildFromCard(card)
        composite.plotDistribution(
            mplWidget1=self.plotWidgetDropDist1,
            mplWidget2=self.plotWidgetDropDist2,
            tableWidget=self.tableWidgetCompositeStats,
        )   
    
    """
    Convenience Accessors
    """
    
    def getActiveCardPasses(self) -> list[Pass]:
        return [p for p in self.seriesData.passes if p.cards.is_active()]