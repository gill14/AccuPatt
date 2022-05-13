from datetime import datetime
import os
from pathlib import Path
import subprocess
import sys

import accupatt.config as cfg
from accupatt.helpers.cardStatTabelModel import CardStatTableModel, ComboBoxDelegate
from accupatt.helpers.dataFileImporter import (
    convert_xlsx_to_db,
    load_from_accupatt_1_file,
)
from accupatt.helpers.dBBridge import load_from_db, save_to_db
from accupatt.helpers.exportExcel import export_all_to_excel, safe_report
from accupatt.helpers.reportMaker import ReportMaker
from accupatt.models.appInfo import AppInfo
from accupatt.models.passData import Pass
from accupatt.models.seriesData import SeriesData
from accupatt.models.sprayCard import SprayCard
from accupatt.models.sprayCardComposite import SprayCardComposite
from accupatt.windows.cardManager import CardManager
from accupatt.windows.editSpreadFactors import EditSpreadFactors
from accupatt.windows.editThreshold import EditThreshold
from accupatt.windows.passManager import PassManager
from accupatt.windows.readString import ReadString
from accupatt.widgets import (
    mplwidget,
    seriesinfowidget,
    singlecardwidget,
    splitcardwidget,
)
from PyQt6 import uic
from PyQt6.QtCore import QSignalBlocker, QSortFilterProxyModel, Qt, pyqtSlot
from PyQt6.QtGui import QAction, QActionGroup
from PyQt6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QHeaderView,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QMessageBox,
    QProgressDialog,
    QTableView,
)

from accupatt.windows.reportManager import ReportManager
from accupatt.windows.stringAdvancedOptions import StringAdvancedOptions

Ui_Form, baseclass = uic.loadUiType(
    os.path.join(os.getcwd(), "resources", "mainWindow.ui")
)
Ui_Form_About, baseclass_about = uic.loadUiType(
    os.path.join(os.getcwd(), "resources", "about.ui")
)
testing = True


class MainWindow(baseclass):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ui = Ui_Form()
        self.ui.setupUi(self)

        self.setWindowTitle(
            f"AccuPatt {cfg.VERSION_MAJOR}.{cfg.VERSION_MINOR}.{cfg.VERSION_RELEASE}"
        )

        self.currentDirectory = cfg.get_datafile_dir()

        # Setup MenuBar
        # --> Setup File Menu
        self.ui.action_new_series_new_aircraft.triggered.connect(
            self.newSeriesNewAircraft
        )
        self.ui.menu_file_aircraft.aboutToShow.connect(self.aboutToShowFileAircraftMenu)
        self.ui.menu_file_aircraft.triggered.connect(
            self.newSeriesFileAircraftMenuAction
        )
        self.ui.action_save.triggered.connect(self.saveFile)
        self.ui.action_open.triggered.connect(self.openFile)
        # --> Setup Options Menu
        self.ui.action_pass_manager.triggered.connect(self.openPassManager)
        self.ui.action_reset_defaults.triggered.connect(self.resetDefaults)
        # --> Setup Export to Excel Menu
        self.ui.action_safe_report.triggered.connect(self.exportSAFEAttendeeLog)
        self.ui.action_detailed_report.triggered.connect(self.exportAllRawData)
        # --> Setup Report Menu
        self.ui.actionCreate_Report.triggered.connect(self.makeReport)
        self.ui.actionReportManager.triggered.connect(self.reportManager)
        # --> # --> Report Options
        self.ui.actionInclude_Card_Images.setChecked(
            cfg.get_report_card_include_images()
        )
        self.ui.actionInclude_Card_Images.toggled[bool].connect(
            self.reportCardImageChanged
        )
        # --> # --> # --> SprayCard Image Type
        self.ui.actionOriginal.setChecked(
            cfg.get_report_card_image_type() == cfg.REPORT_CARD_IMAGE_TYPE_ORIGINAL
        )
        self.ui.actionOutline.setChecked(
            cfg.get_report_card_image_type() == cfg.REPORT_CARD_IMAGE_TYPE_OUTLINE
        )
        self.ui.actionMask.setChecked(
            cfg.get_report_card_image_type() == cfg.REPORT_CARD_IMAGE_TYPE_MASK
        )
        ag_image_type = QActionGroup(self.ui.menuCard_Image_Type)
        for action in self.ui.menuCard_Image_Type.actions():
            ag_image_type.addAction(action)
        ag_image_type.triggered[QAction].connect(self.reportCardImageTypeChanged)
        # --> # --> # --> SprayCard Image Quantity per Page
        self.ui.action5.setChecked(cfg.get_report_card_image_per_page() == 5)
        self.ui.action7.setChecked(cfg.get_report_card_image_per_page() == 7)
        self.ui.action9.setChecked(cfg.get_report_card_image_per_page() == 9)
        ag_image_per_page = QActionGroup(self.ui.menuCard_Images_per_Page)
        for action in self.ui.menuCard_Images_per_Page.actions():
            ag_image_per_page.addAction(action)
        ag_image_per_page.triggered[QAction].connect(self.reportCardImagePerPageChanged)
        # --> Setup Help Menu
        self.ui.actionAbout.triggered.connect(self.about)
        self.ui.actionUserManual.triggered.connect(self.openResourceUserManual)
        self.ui.actionWRKSpectrometerManual.triggered.connect(
            self.openResourceWRKSpectrometerManual
        )
        self.ui.actionWorksheetWRK.triggered.connect(self.openResourceWSWRK)
        self.ui.actionWorksheetGillColor.triggered.connect(self.openResourceWSGillColor)
        self.ui.actionWorksheetGillBW.triggered.connect(self.openResourceWSGillBW)
        self.ui.actionCPCatalog.triggered.connect(self.openResourceCPCatalog)

        # Setup Tab Widget
        self.ui.tabWidget.setEnabled(False)
        # --> Setup AppInfo Tab
        self.ui.widgetSeriesInfo.target_swath_changed.connect(self.swathTargetChanged)
        # --> Setup String Analysis Tab
        self.ui.listWidgetStringPass.itemSelectionChanged.connect(
            self.stringPassSelectionChanged
        )
        self.ui.listWidgetStringPass.itemChanged[QListWidgetItem].connect(
            self.stringPassItemChanged
        )
        self.ui.buttonReadString.clicked.connect(self.readString)
        self.ui.checkBoxStringPassCenter.stateChanged[int].connect(
            self.stringPassCenterChanged
        )
        self.ui.checkBoxStringPassSmooth.stateChanged[int].connect(
            self.stringPassSmoothChanged
        )
        self.ui.checkBoxStringPassRebase.stateChanged[int].connect(
            self.stringPassRebaseChanged
        )
        self.ui.stringAdvancedOptionsPass.clicked.connect(
            self.stringAdvancedOptionsPass
        )
        self.ui.checkBoxStringSeriesCenter.stateChanged[int].connect(
            self.stringSeriesCenterChanged
        )
        self.ui.checkBoxStringSeriesSmooth.stateChanged[int].connect(
            self.stringSeriesSmoothChanged
        )
        self.ui.checkBoxStringSeriesEqualize.stateChanged[int].connect(
            self.stringSeriesEqualizeChanged
        )
        self.ui.stringAdvancedOptionsSeries.clicked.connect(
            self.stringAdvancedOptionsSeries
        )
        self.ui.spinBoxSwathAdjusted.valueChanged[int].connect(
            self.swathAdjustedChanged
        )
        self.ui.horizontalSliderSimulatedSwath.valueChanged[int].connect(
            self.swathAdjustedChanged
        )
        # --> | --> Setup Individual Passes Tab
        # --> | --> Setup Composite Tab
        # --> | --> Setup Simulations Tab
        self.ui.spinBoxSimulatedSwathPasses.valueChanged[int].connect(
            self.simulatedSwathPassesChanged
        )
        self.ui.radioButtonSimulationOne.toggled[bool].connect(
            self.simulationViewWindowChanged
        )

        # --> Setup Card Analysis Tab
        self.ui.listWidgetCardPass.itemSelectionChanged.connect(
            self.cardPassSelectionChanged
        )
        self.ui.listWidgetCardPass.itemChanged[QListWidgetItem].connect(
            self.sprayCardPassItemChanged
        )
        self.ui.buttonEditCards.clicked.connect(self.cardManagerOpen)
        self.ui.checkBoxCardPassCenter.stateChanged[int].connect(
            self.cardPassCenterChanged
        )
        self.ui.checkBoxCardPassColorize.stateChanged[int].connect(
            self.cardPassColorizeChanged
        )
        self.ui.checkBoxCardSeriesCenter.stateChanged[int].connect(
            self.cardSeriesCenterChanged
        )
        self.ui.checkBoxCardSeriesColorize.stateChanged[int].connect(
            self.cardSeriesColorizeChanged
        )
        self.ui.spinBoxSwathAdjusted2.valueChanged[int].connect(
            self.swathAdjustedChanged
        )
        self.ui.horizontalSliderSimulatedSwath2.valueChanged[int].connect(
            self.swathAdjustedChanged
        )
        # --> | --> Setup Individual Tab
        # --> | --> Setup Composite Tab
        # --> | --> Setup Simulations Tab
        # --> | --> Stup Droplet Distribution Tab
        self.ui.comboBoxCardDistPass.currentIndexChanged[int].connect(
            self.cardDistPassChanged
        )
        self.ui.comboBoxCardDistCard.currentIndexChanged[int].connect(
            self.cardDistCardChanged
        )

        # Setup Statusbar
        self.status_label_file = QLabel("No Current Datafile")
        self.status_label_modified = QLabel()
        self.ui.statusbar.addWidget(self.status_label_file)
        self.ui.statusbar.addPermanentWidget(self.status_label_modified)
        self.show()
        # Testing
        if testing:
            self.openFile()

    """""" """""" """""" """""" """""" """""" """""" """""" """""" """""" """""" """""" """''
    Menubar
    """ """""" """""" """""" """""" """""" """""" """""" """""" """""" """""" """""" """""" ""

    @pyqtSlot()
    def newSeriesNewAircraft(self):
        self.newSeries()

    @pyqtSlot()
    def aboutToShowFileAircraftMenu(self):
        m: QMenu = self.ui.menu_file_aircraft
        m.clear()
        m.addAction("Select File Aircraft")
        m.addSeparator()
        for file in [f for f in os.listdir(self.currentDirectory) if f.endswith(".db")]:
            m.addAction(str(file))

    @pyqtSlot()
    def newSeriesFileAircraftMenuAction(self, action):
        if action.text() == "Select File Aircraft":
            self.newSeries(useFileAircraft=True)
        else:
            file = os.path.join(self.currentDirectory, action.text())
            self.newSeries(useFileAircraft=True, fileAircraft=file)

    def newSeries(self, useFileAircraft=False, fileAircraft=""):
        # Dissociate from any currently in-use data file
        self.currentFile = ""
        # Declare/clear SeriesData Container
        self.seriesData = SeriesData()
        # Load in Fly-In Info from saved settings
        info = self.seriesData.info
        info.flyin_name = cfg.get_flyin_name()
        info.flyin_location = cfg.get_flyin_location()
        info.flyin_date = cfg.get_flyin_date()
        info.flyin_analyst = cfg.get_flyin_analyst()
        # Create empty passes based (# of passes from saved settings)
        for i in range(cfg.get_number_of_passes()):
            self.seriesData.passes.append(Pass(number=i + 1))
        # File Aircraft
        if useFileAircraft:
            if fileAircraft == "":
                fileAircraft, _ = QFileDialog.getOpenFileName(
                    parent=self,
                    caption="Open File",
                    directory=self.currentDirectory,
                    filter="AccuPatt (*.db)",
                )
            # Load in series info from file
            load_from_db(file=fileAircraft, s=self.seriesData, load_only_info=True)
            # Increment series number
            info.series = info.series + 1
        # Clear/Update all ui elements
        self.update_all_ui()
        self.status_label_file.setText("No Current Data File")
        self.status_label_modified.setText("")
        self.ui.tabWidget.setEnabled(True)
        self.ui.tabWidget.setCurrentIndex(0)

    @pyqtSlot()
    def saveFile(self):
        # If viewing from XLSX, Prompt to convert
        if self.currentFile != "" and self.currentFile[-1] == "x":
            msg = QMessageBox.question(
                self,
                "Unable to Edit Datafile",
                "Current File is of type: AccuPatt 1 (.xlsx). Would you like to create an edit-compatible (.db) copy?",
            )
            if msg == QMessageBox.StandardButton.Yes:
                self.currentFile = convert_xlsx_to_db(self.currentFile, self.seriesData)
                self.status_label_file.setText(f"Current File: {self.currentFile}")
                self.status_label_modified.setText(
                    f"Last Save: {datetime.fromtimestamp(self.seriesData.info.modified)}"
                )
                return True
            return False
        # If db file doesn't exist, lets create one
        if self.currentFile == "":
            # Have user create a new file
            initialFileName = self.seriesData.info.string_reg_series()
            initialDirectory = os.path.join(self.currentDirectory, initialFileName)
            fname, _ = QFileDialog.getSaveFileName(
                parent=self,
                caption="Create Data File for Series",
                directory=initialDirectory,
                filter="AccuPatt (*.db)",
            )
            if fname is None or fname == "":
                return False
            self.currentFile = fname
            self.currentDirectory = os.path.dirname(self.currentFile)
            cfg.set_datafile_dir(self.currentDirectory)
        # If db file exists, or a new one has been created, update persistent vals for Flyin
        cfg.set_flyin_name(self.seriesData.info.flyin_name)
        cfg.set_flyin_location(self.seriesData.info.flyin_location)
        cfg.set_flyin_date(self.seriesData.info.flyin_date)
        cfg.set_flyin_analyst(self.seriesData.info.flyin_analyst)
        # If db file exists, or a new one has been created, save all SeriesData to the db
        save_to_db(file=self.currentFile, s=self.seriesData)
        self.status_label_file.setText(f"Current File: {self.currentFile}")
        self.status_label_modified.setText(
            f"Last Save: {datetime.fromtimestamp(self.seriesData.info.modified)}"
        )
        return True

    @pyqtSlot()
    def openFile(self):
        try:
            self.currentDirectory
        except NameError:
            self.currentDirectory = Path.home()
        if testing:
            file = "/Users/gill14/Library/Mobile Documents/com~apple~CloudDocs/Projects/AccuPatt/testing/N2067B 01.db"
            # file = '/Users/gill14/Library/Mobile Documents/com~apple~CloudDocs/Projects/AccuPatt/testing/N802BK 01.xlsx'
        else:
            file, _ = QFileDialog.getOpenFileName(
                parent=self,
                caption="Open File",
                directory=self.currentDirectory,
                filter="AccuPatt (*.db *.xlsx)",
            )
        if file == "":
            return
        if file[-1] == "x":
            msg = QMessageBox(
                QMessageBox.Icon.Question,
                "Convert to Compatible Version?",
                "Would you like to open this file in View-Only mode or create a compatible (*.db) copy?",
            )
            button_read_only = msg.addButton(
                "View-Only", QMessageBox.ButtonRole.ActionRole
            )
            button_convert = msg.addButton(
                "Create Compatible Copy", QMessageBox.ButtonRole.ActionRole
            )
            msg.exec()
            if msg.clickedButton() == button_read_only:
                self.seriesData = load_from_accupatt_1_file(file=file)
            elif msg.clickedButton() == button_convert:
                prog = QProgressDialog(self)
                prog.setMinimumDuration(0)
                prog.setWindowModality(Qt.WindowModality.WindowModal)
                file = convert_xlsx_to_db(file, prog=prog)
            else:
                return
        self.currentFile = file
        self.currentDirectory = os.path.dirname(self.currentFile)
        cfg.set_datafile_dir(self.currentDirectory)
        last_modified = "View-Only Mode"
        if self.currentFile[-1] == "b":
            self.seriesData = SeriesData()
            load_from_db(file=self.currentFile, s=self.seriesData)
            last_modified = (
                f"Last Save: {datetime.fromtimestamp(self.seriesData.info.modified)}"
            )
        self.update_all_ui()
        self.status_label_file.setText(f"Current File: {self.currentFile}")
        self.status_label_modified.setText(last_modified)
        self.ui.tabWidget.setEnabled(True)
        self.ui.tabWidget.setCurrentIndex(0)

    def update_all_ui(self):
        # Populate AppInfo tab
        self.ui.widgetSeriesInfo.fill_from_info(self.seriesData.info)

        # Update String Series Controls
        with QSignalBlocker(self.ui.checkBoxStringSeriesCenter):
            self.ui.checkBoxStringSeriesCenter.setChecked(self.seriesData.string.center)
        with QSignalBlocker(self.ui.checkBoxStringSeriesSmooth):
            self.ui.checkBoxStringSeriesSmooth.setChecked(self.seriesData.string.smooth)
        with QSignalBlocker(self.ui.checkBoxStringSeriesEqualize):
            self.ui.checkBoxStringSeriesEqualize.setChecked(
                self.seriesData.string.equalize_integrals
            )
        with QSignalBlocker(self.ui.spinBoxSimulatedSwathPasses):
            self.ui.spinBoxSimulatedSwathPasses.setValue(
                self.seriesData.string.simulated_adjascent_passes
            )
        if (
            cfg.get_string_simulation_view_window()
            == cfg.STRING_SIMULATION_VIEW_WINDOW_ONE
        ):
            with QSignalBlocker(self.ui.radioButtonSimulationOne):
                self.ui.radioButtonSimulationOne.setChecked(True)
        else:
            with QSignalBlocker(self.ui.radioButtonSimulationAll):
                self.ui.radioButtonSimulationAll.setChecked(True)
        with QSignalBlocker(self.ui.radioButtonSimulationOne):
            self.ui.radioButtonSimulationOne.setChecked(
                cfg.get_string_simulation_view_window()
                == cfg.STRING_SIMULATION_VIEW_WINDOW_ONE
            )

        # Updates Card Series Controls
        with QSignalBlocker(self.ui.checkBoxCardSeriesCenter):
            self.ui.checkBoxCardSeriesCenter.setChecked(self.seriesData.cards.center)

        # Process and cache all card stats
        prog = QProgressDialog(self)
        prog.setMinimumDuration(0)
        prog.setWindowModality(Qt.WindowModality.WindowModal)
        card_list: list[SprayCard] = []
        card_identifier_list: list[str] = []
        for p in self.seriesData.passes:
            for c in p.cards.card_list:
                card_list.append(c)
                card_identifier_list.append(f"{p.name} - {c.name}")
        for i, card in enumerate(card_list):
            if i == 0:
                prog.setRange(0, len(card_list))
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

            if i == len(card_list) - 1:
                prog.setValue(i + 1)

        # Refresh ListWidgets
        self.updatePassListWidgets(string=True, cards=True)

        # Updates individual pass view and capture/edit button
        self.stringPassSelectionChanged()

        # Updates spray card views based on potentially new pass list
        self.cardPassSelectionChanged()

        # Set swath adjust UI, plot loc unit labels and replot
        self.swathTargetChanged()

    @pyqtSlot()
    def openPassManager(self):
        # Create popup and send current appInfo vals to popup
        e = PassManager(self.seriesData.passes, self)
        # Connect Slot to retrieve Vals back from popup
        e.pass_list_updated[list].connect(self.updateFromPassManager)
        # Start Loop
        e.exec()

    @pyqtSlot(list)
    def updateFromPassManager(self, passes):
        self.seriesData.passes = passes
        self.update_all_ui()
        self.saveFile()

    def updatePassListWidgets(
        self, string=False, string_index=-1, cards=False, cards_index=-1
    ):
        # ListWidget String Pass
        if string:
            with QSignalBlocker(lwps := self.ui.listWidgetStringPass):
                lwps.clear()
                for p in self.seriesData.passes:
                    self._addPassListWidgetItem(
                        lwps, p.name, p.has_string_data(), p.string_include_in_composite
                    )
                lwps.setCurrentRow(
                    string_index if string_index >= 0 else lwps.count() - 1
                )

        # ListWidget Cards Pass
        if cards:
            with QSignalBlocker(lwpc := self.ui.listWidgetCardPass):
                lwpc.clear()
                for p in self.seriesData.passes:
                    self._addPassListWidgetItem(
                        lwpc, p.name, p.has_card_data(), p.cards_include_in_composite
                    )
                lwpc.setCurrentRow(
                    cards_index if cards_index >= 0 else lwpc.count() - 1
                )
            with QSignalBlocker(cb := self.ui.comboBoxCardDistPass):
                cb.clear()
                cb.addItem("Series Composite")
                cb.addItems([p.name for p in self.seriesData.passes])

    def _addPassListWidgetItem(
        self, listWidget: QListWidget, passName: str, hasData: bool, include: bool
    ):
        item = QListWidgetItem(passName, listWidget)
        item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
        item.setCheckState(Qt.CheckState.Unchecked)
        if hasData:
            item.setFlags(
                Qt.ItemFlag.ItemIsEnabled
                | Qt.ItemFlag.ItemIsSelectable
                | Qt.ItemFlag.ItemIsUserCheckable
            )
            item.setCheckState(
                Qt.CheckState.Checked if include else Qt.CheckState.PartiallyChecked
            )

    @pyqtSlot()
    def resetDefaults(self):
        msg = QMessageBox.question(
            self,
            "Clear All User-Defined Defaults?",
            "This will permanently erase all user-defined defaults for AccuPatt on this computer and revert all to their originally provided values. This includes all user-defined spray card sets. This cannot be undone. Are you sure you want to do this?",
        )
        if msg == QMessageBox.StandardButton.Yes:
            cfg.clear_all_settings()
            QMessageBox.information(
                self, "Success", "All user-defined defaults erased successfully."
            )

    @pyqtSlot()
    def exportSAFEAttendeeLog(self):
        files, _ = QFileDialog.getOpenFileNames(
            parent=self,
            caption="Select Files to Include",
            directory=self.currentDirectory,
            filter="AccuPatt (*.db)",
        )
        if files:
            dir = os.path.dirname(files[0])
            savefile, _ = QFileDialog.getSaveFileName(
                parent=self,
                caption="Save S.A.F.E. Attendee Log As",
                directory=dir + os.path.sep + "Operation SAFE Attendee Log.xlsx",
                filter="Excel Files (*.xlsx)",
            )
        if files and savefile:
            safe_report(files, savefile)

    @pyqtSlot()
    def exportAllRawData(self):
        savefile, _ = QFileDialog.getSaveFileName(
            parent=self,
            caption="Save As",
            directory=self.currentDirectory
            + os.path.sep
            + f"{self.seriesData.info.string_reg_series()} Raw Data.xlsx",
            filter="Excel Files (*.xlsx)",
        )
        if savefile:
            export_all_to_excel(series=self.seriesData, saveFile=savefile)

    @pyqtSlot()
    def makeReport(self):
        savefile, _ = QFileDialog.getSaveFileName(
            parent=self,
            caption="Save As",
            directory=self.currentDirectory
            + os.path.sep
            + f"{self.seriesData.info.string_reg_series()}.pdf",
            filter="PDF Files (*.pdf)",
        )
        if savefile:
            reportMaker = ReportMaker(file=savefile, seriesData=self.seriesData)
            reportMaker.report_safe_string(
                overlayWidget=self.ui.plotWidgetOverlay,
                averageWidget=self.ui.plotWidgetAverage,
                racetrackWidget=self.ui.plotWidgetRacetrack,
                backAndForthWidget=self.ui.plotWidgetBackAndForth,
                tableView=self.ui.tableWidgetCV,
            )
            for row, p in enumerate(self.seriesData.passes):
                if (
                    p.has_card_data()
                    and p.cards_include_in_composite
                    and any([sc.include_in_composite for sc in p.cards.card_list])
                ):
                    # Select the pass to update plots
                    self.ui.listWidgetCardPass.setCurrentRow(row)
                    # Select the pass for droplet dist
                    self.ui.comboBoxSprayCardDist.setCurrentIndex(1)
                    reportMaker.report_safe_card_summary(
                        spatialDVWidget=self.ui.mplWidgetCardSpatial1,
                        spatialCoverageWidget=self.ui.mplWidgetCardSpatial2,
                        histogramNumberWidget=self.ui.plotWidgetDropDist1,
                        histogramCoverageWidget=self.ui.plotWidgetDropDist2,
                        tableView=self.ui.tableWidgetSprayCardStats,
                        passData=p,
                    )
                    # Print cards for pass
                    if cfg.get_report_card_include_images():
                        reportMaker.report_card_individuals_concise(passData=p)
            reportMaker.save()
            if sys.platform == "darwin":
                subprocess.call(["open", savefile])
            elif sys.platform == "win32":
                os.startfile(savefile)
            # Redraw plots with defaults
            self.update_all_ui()

    @pyqtSlot(bool)
    def reportCardImageChanged(self, checked: bool):
        cfg.set_report_card_include_images(checked)

    @pyqtSlot(QAction)
    def reportCardImageTypeChanged(self, action: QAction):
        if action == self.ui.actionOutline:
            cfg.set_report_card_image_type(cfg.REPORT_CARD_IMAGE_TYPE_OUTLINE)
        elif action == self.ui.actionMask:
            cfg.set_report_card_image_type(cfg.REPORT_CARD_IMAGE_TYPE_MASK)
        else:
            cfg.set_report_card_image_type(cfg.REPORT_CARD_IMAGE_TYPE_ORIGINAL)

    @pyqtSlot(QAction)
    def reportCardImagePerPageChanged(self, action: QAction):
        if action == self.ui.action5:
            cfg.set_report_card_image_per_page(5)
        elif action == self.ui.action7:
            cfg.set_report_card_image_per_page(7)
        else:
            cfg.set_report_card_image_per_page(9)

    @pyqtSlot()
    def reportManager(self):
        # Create popup and send current appInfo vals to popup
        e = ReportManager(self)
        # Connect Slot to retrieve Vals back from popup
        # e.pass_list_updated[list].connect(self.updateFromPassManager)
        # Start Loop
        e.exec()

    @pyqtSlot()
    def about(self):
        About(parent=self).exec()

    @pyqtSlot()
    def openResourceUserManual(self):
        self.openResourceDocument("accupatt_2_user_manual.pdf")

    @pyqtSlot()
    def openResourceWRKSpectrometerManual(self):
        self.openResourceDocument("WRK_spectrometer_manual.pdf")

    @pyqtSlot()
    def openResourceWSWRK(self):
        self.openResourceDocument("WRK_SpraySheet_V3.pdf")

    @pyqtSlot()
    def openResourceWSGillColor(self):
        self.openResourceDocument("Gill_SpraySheet_Color.pdf")

    @pyqtSlot()
    def openResourceWSGillBW(self):
        self.openResourceDocument("Gill_SpraySheet_BW.pdf")

    @pyqtSlot()
    def openResourceCPCatalog(self):
        self.openResourceDocument("CP_Catalog.pdf")

    def openResourceDocument(self, file):
        file = os.path.join(os.getcwd(), "resources", "documents", file)
        if sys.platform == "darwin":
            subprocess.call(["open", file])
        elif sys.platform == "win32":
            os.startfile(file)

    def swathTargetChanged(self):
        # Update the swath adjustment slider
        sw = self.seriesData.info.swath
        if sw == 0:
            sw = self.seriesData.info.swath_adjusted
        minn = float(sw) * 0.5
        maxx = float(sw) * 1.5
        with QSignalBlocker(self.ui.horizontalSliderSimulatedSwath):
            self.ui.horizontalSliderSimulatedSwath.setValue(
                self.seriesData.info.swath_adjusted
            )
            self.ui.horizontalSliderSimulatedSwath.setMinimum(round(minn))
            self.ui.horizontalSliderSimulatedSwath.setMaximum(round(maxx))
        with QSignalBlocker(self.ui.spinBoxSwathAdjusted):
            self.ui.spinBoxSwathAdjusted.setValue(self.seriesData.info.swath_adjusted)
            self.ui.spinBoxSwathAdjusted.setSuffix(
                " " + self.seriesData.info.swath_units
            )
        # Must update all string plots for new labels and potential new adjusted swath
        self.updateStringPlots(
            modify=True, individuals=True, composites=True, simulations=True
        )
        with QSignalBlocker(self.ui.horizontalSliderSimulatedSwath2):
            self.ui.horizontalSliderSimulatedSwath2.setValue(
                self.seriesData.info.swath_adjusted
            )
            self.ui.horizontalSliderSimulatedSwath2.setMinimum(round(minn))
            self.ui.horizontalSliderSimulatedSwath2.setMaximum(round(maxx))
        with QSignalBlocker(self.ui.spinBoxSwathAdjusted2):
            self.ui.spinBoxSwathAdjusted2.setValue(self.seriesData.info.swath_adjusted)
            self.ui.spinBoxSwathAdjusted2.setSuffix(
                " " + self.seriesData.info.swath_units
            )
        # Must update all string plots for new labels and potential new adjusted swath
        self.updateCardPlots(individuals=True, composites=True, simulations=True)

    @pyqtSlot(int)
    def swathAdjustedChanged(self, swath):
        self.seriesData.info.swath_adjusted = swath
        with QSignalBlocker(self.ui.spinBoxSwathAdjusted):
            self.ui.spinBoxSwathAdjusted.setValue(swath)
        with QSignalBlocker(self.ui.horizontalSliderSimulatedSwath):
            self.ui.horizontalSliderSimulatedSwath.setValue(swath)
        self.updateStringPlots(composites=True, simulations=True)
        with QSignalBlocker(self.ui.spinBoxSwathAdjusted2):
            self.ui.spinBoxSwathAdjusted2.setValue(swath)
        with QSignalBlocker(self.ui.horizontalSliderSimulatedSwath2):
            self.ui.horizontalSliderSimulatedSwath2.setValue(swath)
        self.updateCardPlots(composites=True, simulations=True)

    """""" """""" """""" """""" """""" """""" """""" """""" """""" """""" """""" """""" """''
    String Analysis
    """ """""" """""" """""" """""" """""" """""" """""" """""" """""" """""" """""" """""" ""

    @pyqtSlot()
    def stringPassSelectionChanged(self):
        if passData := self.getCurrentStringPass():
            self.ui.checkBoxStringPassCenter.setChecked(passData.string.center)
            self.ui.checkBoxStringPassSmooth.setChecked(passData.string.smooth)
            self.ui.checkBoxStringPassRebase.setChecked(passData.string.rebase)
            self.ui.checkBoxStringPassCenter.setEnabled(not passData.string.rebase)
            self.updateStringPlots(individuals=True)
            # Update the info labels on the individual pass tab
            if passData.has_string_data():
                self.ui.buttonReadString.setText(f"Edit {passData.name}")
            else:
                self.ui.buttonReadString.setText(f"Capture {passData.name}")

    @pyqtSlot(QListWidgetItem)
    def stringPassItemChanged(self, item: QListWidgetItem):
        # Checkstate on item changed
        # If new state is unchecked, make it partial
        if item.checkState() == Qt.CheckState.Unchecked:
            item.setCheckState(Qt.CheckState.PartiallyChecked)
        # Update SeriesData -> Pass object
        p = self.seriesData.passes[self.ui.listWidgetStringPass.row(item)]
        p.string_include_in_composite = item.checkState() == Qt.CheckState.Checked
        # Replot composites, simulations
        self.updateStringPlots(modify=True, composites=True, simulations=True)

    @pyqtSlot()
    def readString(self):
        if passData := self.getCurrentStringPass():
            # Create popup and send current appInfo vals to popup
            e = ReadString(passData=passData, parent=self)
            # Connect Slot to retrieve Vals back from popup
            e.accepted.connect(self.readStringFinished)
            # Start Loop
            e.show()

    @pyqtSlot()
    def readStringFinished(self):
        # Handles checking of string pass list widget
        self.updatePassListWidgets(
            string=True, string_index=self.ui.listWidgetStringPass.currentRow()
        )
        # Replot all but individuals
        self.updateStringPlots(
            modify=True, individuals=False, composites=True, simulations=True
        )
        # Plot individuals and update capture button text
        self.stringPassSelectionChanged()

    @pyqtSlot(int)
    def stringPassCenterChanged(self, checkstate):
        if passData := self.getCurrentStringPass():
            passData.string.center = Qt.CheckState(checkstate) == Qt.CheckState.Checked
            self.updateStringPlots(modify=True, composites=True, simulations=True)

    @pyqtSlot(int)
    def stringPassSmoothChanged(self, checkstate):
        if passData := self.getCurrentStringPass():
            passData.string.smooth = Qt.CheckState(checkstate) == Qt.CheckState.Checked
            self.updateStringPlots(
                modify=True, individuals=True, composites=True, simulations=True
            )

    @pyqtSlot(int)
    def stringPassRebaseChanged(self, checkstate):
        if passData := self.getCurrentStringPass():
            passData.string.rebase = Qt.CheckState(checkstate) == Qt.CheckState.Checked
            if passData.string.rebase:
                passData.string.center = True
                self.ui.checkBoxStringPassCenter.setChecked(passData.string.center)
            self.ui.checkBoxStringPassCenter.setEnabled(not passData.string.rebase)
            self.updateStringPlots(
                modify=True, individuals=True, composites=True, simulations=True
            )

    @pyqtSlot(int)
    def stringSeriesCenterChanged(self, checkstate):
        self.seriesData.string.center = (
            Qt.CheckState(checkstate) == Qt.CheckState.Checked
        )
        self.updateStringPlots(modify=True, composites=True, simulations=True)

    @pyqtSlot(int)
    def stringSeriesSmoothChanged(self, checkstate):
        self.seriesData.string.smooth = (
            Qt.CheckState(checkstate) == Qt.CheckState.Checked
        )
        self.updateStringPlots(modify=True, composites=True, simulations=True)

    @pyqtSlot(int)
    def stringSeriesEqualizeChanged(self, checkstate):
        self.seriesData.string.equalize_integrals = (
            Qt.CheckState(checkstate) == Qt.CheckState.Checked
        )
        self.updateStringPlots(modify=True, composites=True, simulations=True)

    @pyqtSlot()
    def stringAdvancedOptionsPass(self):
        if passData := self.getCurrentStringPass():
            e = StringAdvancedOptions(passData=passData, parent=self)
            e.accepted.connect(self.stringAdvancedOptionsPassUpdated)
            e.exec()

    def stringAdvancedOptionsPassUpdated(self):
        self.updateStringPlots(
            modify=True, individuals=False, composites=True, simulations=True
        )

    @pyqtSlot()
    def stringAdvancedOptionsSeries(self):
        e = StringAdvancedOptions(seriesData=self.seriesData, parent=self)
        e.accepted.connect(self.stringAdvancedOptionsSeriesUpdated)
        e.exec()

    def stringAdvancedOptionsSeriesUpdated(self):
        self.updateStringPlots(modify=True, composites=True, simulations=True)
        self.saveFile()

    def updateStringPlots(
        self, modify=False, individuals=False, composites=False, simulations=False
    ):
        if modify:
            self.seriesData.string.modifyPatterns()
        if individuals:
            if (passData := self.getCurrentStringPass()) != None:
                # Plot Individual
                line_left, line_right, line_vertical = passData.string.plotIndividual(
                    self.ui.plotWidgetIndividual
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
                passData.string.plotIndividualTrim(self.ui.plotWidgetIndividualTrim)
        if composites:
            self.seriesData.string.plotOverlay(self.ui.plotWidgetOverlay)
            self.seriesData.string.plotAverage(
                self.ui.plotWidgetAverage, self.seriesData.info.swath_adjusted
            )
        if simulations:
            self.seriesData.string.plotRacetrack(
                mplWidget=self.ui.plotWidgetRacetrack,
                swath_width=self.seriesData.info.swath_adjusted,
                showEntireWindow=self.ui.radioButtonSimulationAll.isChecked(),
            )
            self.seriesData.string.plotBackAndForth(
                mplWidget=self.ui.plotWidgetBackAndForth,
                swath_width=self.seriesData.info.swath_adjusted,
                showEntireWindow=self.ui.radioButtonSimulationAll.isChecked(),
            )
            self.seriesData.string.plotCVTable(
                self.ui.tableWidgetCV, self.seriesData.info.swath_adjusted
            )

    @pyqtSlot(object)
    def _updateTrimL(self, object):
        self.getCurrentStringPass().string.user_set_trim_left(object.value())
        self.updateStringPlots(
            modify=True, individuals=True, composites=True, simulations=True
        )

    @pyqtSlot(object)
    def _updateTrimR(self, object):
        self.getCurrentStringPass().string.user_set_trim_right(object.value())
        self.updateStringPlots(
            modify=True, individuals=True, composites=True, simulations=True
        )

    @pyqtSlot(object)
    def _updateTrimFloor(self, object):
        self.getCurrentStringPass().string.user_set_trim_floor(object.value())
        self.updateStringPlots(
            modify=True, individuals=True, composites=True, simulations=True
        )

    @pyqtSlot(int)
    def simulatedSwathPassesChanged(self, numAdjascentPasses):
        self.seriesData.string.simulated_adjascent_passes = numAdjascentPasses
        self.updateStringPlots(simulations=True)

    @pyqtSlot(bool)
    def simulationViewWindowChanged(self, viewOneIsChecked):
        cfg.set_String_simulation_view_window(
            cfg.STRING_SIMULATION_VIEW_WINDOW_ONE
            if viewOneIsChecked
            else cfg.STRING_SIMULATINO_VIEW_WINDOW_ALL
        )
        self.updateStringPlots(simulations=True)

    def getCurrentStringPass(self) -> Pass:
        passData: Pass = None
        # Check if a pass is selected
        if (passIndex := self.ui.listWidgetStringPass.currentRow()) != -1:
            passData = self.seriesData.passes[passIndex]
        return passData

    """""" """""" """""" """""" """""" """""" """""" """""" """""" """""" """""" """""" """''
    Spray Card Analysis
    """ """""" """""" """""" """""" """""" """""" """""" """""" """""" """""" """""" """""" ""

    @pyqtSlot()
    def cardPassSelectionChanged(self):
        passData = self.getCurrentCardPass()
        if passData.has_card_data():
            self.ui.buttonEditCards.setText(f"Edit {passData.name}")
        else:
            self.ui.buttonEditCards.setText(f"Capture {passData.name}")
        self.ui.checkBoxCardPassCenter.setChecked(passData.cards.center)

        self.updateCardPlots(individuals=True)

    @pyqtSlot(QListWidgetItem)
    def sprayCardPassItemChanged(self, item: QListWidgetItem):
        # Checkstate on item changed
        # If new state is unchecked, make it partial
        if item.checkState() == Qt.CheckState.Unchecked:
            item.setCheckState(Qt.CheckState.PartiallyChecked)
        # Update SeriesData -> Pass object
        p = self.seriesData.passes[self.ui.listWidgetCardPass.row(item)]
        p.cards_include_in_composite = item.checkState() == Qt.CheckState.Checked
        # Replot and Recalculate composites
        self.updateCardPlots(composites=True, simulations=True, distributions=True)

    @pyqtSlot()
    def cardManagerOpen(self):
        # Get a handle on the currently selected pass
        passData = self.getCurrentCardPass()
        # Trigger file save if filapath needed
        if self.currentFile == None or self.currentFile == "":
            if not self.saveFile():
                return
        # Open the Edit Card List window for currently selected pass
        e = CardManager(
            passData=passData,
            seriesData=self.seriesData,
            filepath=self.currentFile,
            parent=self,
        )
        # Connect Slot to retrieve Vals back from popup
        e.accepted.connect(self.cardManagerOnClose)
        e.passDataChanged.connect(self.saveFile)
        # Start Loop
        e.exec()

    @pyqtSlot()
    def cardManagerOnClose(self):
        # Save all changes
        self.saveFile()
        # Handles checking of card pass list widget
        self.updatePassListWidgets(
            cards=True, cards_index=self.ui.listWidgetCardPass.currentRow()
        )
        # Repopulates card list widget, updates rest of ui
        self.cardPassSelectionChanged()
        self.updateCardPlots(composites=True, simulations=True, distributions=True)

    @pyqtSlot(int)
    def cardDistPassChanged(self, mode):
        comboBoxPass: QComboBox = self.ui.comboBoxCardDistPass
        comboBoxCard: QComboBox = self.ui.comboBoxCardDistCard
        with QSignalBlocker(comboBoxCard):
            comboBoxCard.clear()
            i = comboBoxPass.currentIndex()
            if i > 0:
                comboBoxCard.addItem("Pass Composite")
                comboBoxCard.addItems(
                    [c.name for c in self.seriesData.passes[i - 1].cards.card_list]
                )
                comboBoxCard.setCurrentIndex(0)
        self.updateCardPlots(distributions=True)

    @pyqtSlot(int)
    def cardDistCardChanged(self, mode):
        self.updateCardPlots(distributions=True)

    @pyqtSlot(int)
    def cardPassCenterChanged(self, checkstate):
        self.getCurrentCardPass().cards.center = (
            Qt.CheckState(checkstate) == Qt.CheckState.Checked
        )
        self.updateCardPlots(composites=True, simulations=True)

    @pyqtSlot(int)
    def cardPassColorizeChanged(self, checkstate):
        self.updateCardPlots(individuals=True)

    @pyqtSlot(int)
    def cardSeriesCenterChanged(self, checkstate):
        self.seriesData.cards.center = (
            Qt.CheckState(checkstate) == Qt.CheckState.Checked
        )
        self.updateCardPlots(composites=True, simulations=True)

    @pyqtSlot(int)
    def cardSeriesColorizeChanged(self, checkstate):
        self.updateCardPlots(composites=True)

    @pyqtSlot()
    def cardPassStatTableValueChanged(self):
        self.updateCardPlots(individuals=True, composites=True, simulations=True)

    @pyqtSlot()
    def saveAndUpdateSprayCardView(self):
        self.saveFile()
        self.updateCardPlots(
            individuals=True, composites=True, simulations=True, distributions=True
        )

    def updateCardPlots(
        self,
        individuals=False,
        composites=False,
        simulations=False,
        distributions=False,
    ):
        passData = self.getCurrentCardPass()
        if individuals:
            passData.cards.plotCoverage(
                mplWidget=self.ui.plotWidgetCardPass,
                loc_units=self.seriesData.info.swath_units,
                colorize=self.ui.checkBoxCardPassColorize.isChecked(),
                mod=False,
            )
            tableView: QTableView = self.ui.tableViewCardPass
            model = CardStatTableModel()
            proxyModel = QSortFilterProxyModel()
            proxyModel.setSourceModel(model)
            tableView.setModel(proxyModel)
            tableView.setItemDelegateForColumn(
                3, ComboBoxDelegate(tableView, cfg.UNITS_LENGTH_LARGE)
            )
            tableView.horizontalHeader().setSectionResizeMode(
                QHeaderView.ResizeMode.ResizeToContents
            )
            model.loadCards([card for card in passData.cards.card_list])
            model.valueChanged.connect(self.cardPassStatTableValueChanged)
        if composites:
            self.seriesData.cards.plotOverlay(mplWidget=self.ui.plotWidgetCardOverlay)
            self.seriesData.cards.plotAverage(
                mplWidget=self.ui.plotWidgetCardAverage,
                colorize=self.ui.checkBoxCardSeriesColorize.isChecked(),
            )
        if simulations:
            pass
        if distributions:
            composite = SprayCardComposite()
            if self.ui.comboBoxCardDistPass.currentIndex() == 0:
                # "All (Series-Wise Composite)" option
                composite.buildFromSeries(seriesData=self.seriesData)
            else:
                distPassData = self.seriesData.passes[
                    self.ui.comboBoxCardDistPass.currentIndex() - 1
                ]
                # "Pass X" option
                if self.ui.comboBoxCardDistCard.currentIndex() == 0:
                    # "All (Pass-Wise Composite)" option
                    composite.buildFromPass(passData=distPassData)
                elif self.ui.comboBoxCardDistCard.currentIndex() > 0:
                    # "Card X" option
                    card = distPassData.cards.card_list[
                        self.ui.comboBoxCardDistCard.currentIndex() - 1
                    ]
                    composite.buildFromCard(card)
            composite.plotDistribution(
                mplWidget1=self.ui.plotWidgetDropDist1,
                mplWidget2=self.ui.plotWidgetDropDist2,
                tableWidget=self.ui.tableWidgetSprayCardStats,
            )

    def getCurrentCardPass(self) -> Pass:
        passData: Pass = None
        # Check if a pass is selected
        if (passIndex := self.ui.listWidgetCardPass.currentRow()) != -1:
            passData = self.seriesData.passes[passIndex]
        return passData


class About(baseclass_about):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        # Your code will go here
        self.ui = Ui_Form_About()
        self.ui.setupUi(self)
        self.ui.label_version.setText(
            f"AccuPatt Version:  {cfg.VERSION_MAJOR}.{cfg.VERSION_MINOR}.{cfg.VERSION_RELEASE}"
        )
        self.show()
