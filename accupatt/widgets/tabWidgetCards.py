from itertools import compress
import os

import accupatt.config as cfg
from PyQt6.QtCore import QSortFilterProxyModel, Qt, QTimer, pyqtSlot, QSignalBlocker
from PyQt6.QtWidgets import (
    QComboBox,
    QHeaderView,
    QMessageBox,
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
from accupatt.windows.cardPlotOptions import CardPlotOptions


class TabWidgetCards(TabWidgetBase):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(
            ui_file=os.path.join(os.getcwd(), "resources", "cardMainWidget.ui"),
            subtype="cards",
            parent=parent,
            *args,
            **kwargs,
        )

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
        super().setData(seriesData=seriesData)
        # Update Dist Comboboxes/plots
        self.distPassChanged(0)

    def processCards(self):
        card_list: list[SprayCard] = []
        card_identifier_list: list[str] = []
        for p in self.seriesData.passes:
            for c in p.cards.card_list:
                if c.has_image and (not c.current or not c.stats.current):
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
            card.process_image()
            card.stats.set_volumetric_stats()
            if prog.wasCanceled():
                return
        prog.setValue(len(card_list))
        # Notify of cards which exceeded max stain limit
        if any([c.flag_max_stain_limit_reached for c in card_list]):
            QMessageBox.warning(
                self,
                "Max Stain Limit Exceeded",
                f"The following cards were unable to be processed due to the number of detected stains exceeding the user-defined limit: [{', '.join(compress(card_identifier_list,[c.name for c in card_list if c.flag_max_stain_limit_reached]))}]",
            )

    @pyqtSlot(str)
    def onCurrentFileChanged(self, file: str):
        self.currentFile = file

    """
    Pass List Widget
    """

    def updatePassListWidget(self, index_to_select: int = -1):
        super().updatePassListWidget(index_to_select)
        with QSignalBlocker(self.comboBoxDistPass):
            self.comboBoxDistPass.clear()
            self.comboBoxDistPass.addItem("Series Composite")
            self.comboBoxDistPass.addItems(
                [p.name for p in self.seriesData.passes if p.cards.has_data()]
            )

    """
    Edit Pass Button & Methods
    """

    @pyqtSlot()
    def editPass(self):
        if passData := self.getCurrentPass():
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
            e.accepted.connect(self.onEditPassAccepted)
            e.exec()

    @pyqtSlot(str)
    def _acceptFileSaveSignal(self, file: str):
        self.currentFile = file
        if self.delayed_request_open_edit_pass:
            self.delayed_request_open_edit_pass = False
            QTimer.singleShot(1000, self.editPass)

    """
    Pass Data Mod Options
    """

    """
    Series Data Mod Options
    """

    @pyqtSlot()
    def clickedPlotOptions(self):
        cpo = CardPlotOptions(parent=self)
        cpo.request_update_plots[bool, bool, bool].connect(
            lambda a, b, c: self.updatePlots(
                individuals=a, composites=b, simulations=c
            )
        )
        cpo.show()

    """
    Individual Passes Tab
    """

    @pyqtSlot()
    def passStatTableValueChanged(self):
        self.updatePlots(individuals=True, composites=True, simulations=True)

    """
    Simulations Tab
    """

    """
    Distributions Tab
    """

    @pyqtSlot(int)
    def distPassChanged(self, index: int):
        with QSignalBlocker(self.comboBoxDistCard):
            self.comboBoxDistCard.clear()
            self.comboBoxDistCard.setEnabled(index > 0)
            if index > 0:
                self.comboBoxDistCard.addItem("Pass Composite")
                passData = self.getActiveCardPasses()[index - 1]
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

    def reprocess_triggered(self):
        self.processCards()

    def individuals_triggered(self, passData: Pass):
        passData.cards.plot(
            mplWidget=self.plotWidgetPass,
            loc_units=self.seriesData.info.swath_units,
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
        )

    def simulations_triggered(self):
        self.seriesData.cards.plotRacetrack(
            mplWidget=self.plotWidgetRacetrack,
        )
        self.seriesData.cards.plotBackAndForth(
            mplWidget=self.plotWidgetBackAndForth,
        )
        self.seriesData.cards.plotCVTable(
            self.tableWidgetCV
        )

    def distributions_triggered(self):
        composite = SprayCardComposite()
        if self.comboBoxDistPass.currentIndex() == 0:
            # "All (Series-Wise Composite)" option
            composite.buildFromSeries(seriesData=self.seriesData)
        else:
            distPassData = self.getActiveCardPasses()[
                self.comboBoxDistPass.currentIndex() - 1
            ]
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
