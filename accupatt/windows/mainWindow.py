from datetime import datetime
import os
import subprocess
import sys

import accupatt.config as cfg
from accupatt.helpers.dataFileImporter import (
    convert_xlsx_to_db,
    load_from_accupatt_1_file,
)
from accupatt.helpers.dBBridge import load_from_db, save_to_db
from accupatt.helpers.exportExcel import export_all_to_excel, safe_report
from accupatt.helpers.reportMaker import ReportMaker
from accupatt.models.passData import Pass
from accupatt.models.seriesData import SeriesData
from accupatt.widgets.tabWidgetCards import TabWidgetCards
from accupatt.widgets.seriesinfowidget import SeriesInfoWidget
from accupatt.widgets.tabWidgetString import TabWidgetString
from accupatt.windows.cardPlotOptions import CardPlotOptions
from accupatt.windows.passManager import PassManager

from accupatt.widgets import (
    cardtablewidget,
    mplwidget,
    passinfowidget,
    singlecardwidget,
    splitcardwidget,
    tabWidgetString,
    tabWidgetCards,
)
from PyQt6 import uic
from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QAction, QActionGroup
from PyQt6.QtWidgets import (
    QFileDialog,
    QLabel,
    QMenu,
    QMessageBox,
    QProgressDialog,
    QTabWidget,
)

from accupatt.windows.reportManager import ReportManager

Ui_Form, baseclass = uic.loadUiType(
    os.path.join(os.getcwd(), "resources", "mainWindow.ui")
)
Ui_Form_About, baseclass_about = uic.loadUiType(
    os.path.join(os.getcwd(), "resources", "about.ui")
)
testing = False
testfile = "/Users/gill14/Library/Mobile Documents/com~apple~CloudDocs/Projects/AccuPatt/testing/N2067B 01.db"


class MainWindow(baseclass):

    file_saved = pyqtSignal(str)
    current_file_changed = pyqtSignal(str)
    pass_list_changed = pyqtSignal()
    target_swath_changed = pyqtSignal()
    request_repaint = pyqtSignal()

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
        self.action_save: QAction = self.ui.action_save
        self.action_save.triggered.connect(self.saveFile)
        self.ui.action_open.triggered.connect(self.openFile)
        # --> Setup Options Menu
        self.ui.action_pass_manager.triggered.connect(self.openPassManager)
        # --> | --> String Plot Options
        menuStringPlotOptions: QMenu = self.ui.menuString_Plot_Options
        actionStringCrosshair = QAction("Average Plot Swath Box", menuStringPlotOptions)
        actionStringCrosshair.setCheckable(True)
        actionStringCrosshair.setChecked(cfg.get_string_plot_average_swath_box())
        actionStringCrosshair.toggled[bool].connect(self.toggleStringCrosshair)
        menuStringPlotOptions.addAction(actionStringCrosshair)
        # --> | --> | --> Simulation View
        menuStringSimView = QMenu("Simulation View", menuStringPlotOptions)
        actionStringSimSwath = QAction("One Swath", menuStringSimView)
        actionStringSimSwath.setCheckable(True)
        actionStringSimSwath.setChecked(
            cfg.get_string_simulation_view_window()
            == cfg.STRING_SIMULATION_VIEW_WINDOW_ONE
        )
        actionStringSimAll = QAction("All Passes", menuStringSimView)
        actionStringSimAll.setCheckable(True)
        actionStringSimAll.setChecked(
            cfg.get_string_simulation_view_window()
            == cfg.STRING_SIMULATINO_VIEW_WINDOW_ALL
        )
        menuStringSimView.addActions([actionStringSimSwath, actionStringSimAll])
        actionGroupStringSimView = QActionGroup(menuStringSimView)
        actionGroupStringSimView.addAction(actionStringSimSwath)
        actionGroupStringSimView.addAction(actionStringSimAll)
        actionGroupStringSimView.triggered[QAction].connect(self.toggleStringSimView)
        menuStringPlotOptions.addMenu(menuStringSimView)
        # --> | --> Card Plot Options
        actionCardPlotOptions: QActionGroup = self.ui.actionCardPlotOptions
        actionCardPlotOptions.triggered.connect(self.openCardPlotOptions)
        self.ui.action_reset_defaults.triggered.connect(self.resetDefaults)
        # --> Setup Export to Excel Menu
        self.ui.action_SAFE_log_from_files.triggered.connect(
            self.exportSAFELogFromFiles
        )
        self.ui.action_SAFE_log_from_directory.triggered.connect(
            self.exportSAFELogFromDirectory
        )
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
        # --> # --> # --> Logo
        actionLogoEnabled: QAction = self.ui.actionInclude_Logo
        actionLogoEnabled.setCheckable(True)
        actionLogoEnabled.setChecked(cfg.get_logo_include_in_report())
        actionLogoEnabled.toggled[bool].connect(self.logo_enabled_triggered)
        actionLogoPath: QAction = self.ui.actionLogo_File
        actionLogoPath.setText(cfg.get_logo_path())
        actionLogoSelect: QAction = self.ui.actionSelect_Logo_File
        actionLogoSelect.triggered.connect(self.select_logo_triggered)

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
        self.tabWidget: QTabWidget = self.ui.tabWidget
        self.tabWidget.setEnabled(False)
        self.seriesInfoWidget: SeriesInfoWidget = self.ui.widgetSeriesInfo
        self.seriesInfoWidget.target_swath_changed.connect(
            lambda: self.target_swath_changed.emit()
        )
        self.seriesInfoWidget.request_open_pass_filler.connect(self.openPassFiller)
        self.stringWidget: TabWidgetString = self.ui.stringMainWidget
        self.stringWidget.request_file_save.connect(self.saveFile)
        self.cardWidget: TabWidgetCards = self.ui.cardMainWidget
        self.cardWidget.request_file_save.connect(self.saveFile)

        # Outbound Signals
        self.file_saved[str].connect(self.cardWidget._acceptFileSaveSignal)
        self.current_file_changed[str].connect(self.cardWidget.onCurrentFileChanged)
        self.target_swath_changed.connect(
            self.stringWidget.setAdjustedSwathFromTargetSwath
        )
        self.target_swath_changed.connect(
            self.cardWidget.setAdjustedSwathFromTargetSwath
        )
        self.pass_list_changed.connect(
            lambda: self.stringWidget.updatePassListWidget(-1)
        )
        self.pass_list_changed.connect(lambda: self.cardWidget.updatePassListWidget(-1))
        self.request_repaint.connect(self.stringWidget.repaint)

        # Setup Statusbar
        self.status_label_file = QLabel("No Current Datafile")
        self.status_label_modified = QLabel()
        self.ui.statusbar.addWidget(self.status_label_file)
        self.ui.statusbar.addPermanentWidget(self.status_label_modified)
        self.show()
        # Testing
        if testing:
            self.openFile(file=testfile)

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
        for file in sorted(
            [f for f in os.listdir(self.currentDirectory) if f.endswith(".db")]
        ):
            m.addAction(str(file))

    @pyqtSlot(QAction)
    def newSeriesFileAircraftMenuAction(self, action):
        if action.text() == "Select File Aircraft":
            self.newSeries(useFileAircraft=True)
        else:
            file = os.path.join(self.currentDirectory, action.text())
            self.newSeries(useFileAircraft=True, fileAircraft=file)

    def newSeries(self, useFileAircraft=False, fileAircraft=""):
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
        self.change_current_file("")
        self.tabWidget.setEnabled(True)
        self.tabWidget.setCurrentIndex(0)

    @pyqtSlot()
    def saveFile(self):
        # If viewing from XLSX, Ignore save requests
        if len(self.currentFile) > 3 and self.currentFile[-4:] == "xlsx":
            return False
        # If db file doesn't exist, lets create one
        if self.currentFile == "":
            # Have user create a new file
            initialFileName = self.seriesData.info.string_reg_series()
            initialDirectory = os.path.join(self.currentDirectory, initialFileName)
            file, _ = QFileDialog.getSaveFileName(
                parent=self,
                caption="Create Data File for Series",
                directory=initialDirectory,
                filter="AccuPatt (*.db)",
            )
            if file is None or file == "":
                return False
            self.change_current_file(file)
        # If db file exists, or a new one has been created, update persistent vals for Flyin
        cfg.set_flyin_name(self.seriesData.info.flyin_name)
        cfg.set_flyin_location(self.seriesData.info.flyin_location)
        cfg.set_flyin_date(self.seriesData.info.flyin_date)
        cfg.set_flyin_analyst(self.seriesData.info.flyin_analyst)
        # If db file exists, or a new one has been created, save all SeriesData to the db
        if save_to_db(file=self.currentFile, s=self.seriesData):
            self.change_statusbar_save()
            self.file_saved.emit(self.currentFile)
            return True
        else:
            msg = QMessageBox(
                icon=QMessageBox.Icon.Critical,
                text=f"Unable to save series data to {self.currentFile}",
            )
            msg.exec()
            return False

    @pyqtSlot()
    def openFile(self, file: str = ""):
        # Open a FileChooser and obtain selected file (DB or XLSX)
        if file == "":
            file, _ = QFileDialog.getOpenFileName(
                parent=self,
                caption="Open File",
                directory=self.currentDirectory,
                filter="AccuPatt (*.db *.xlsx)",
            )
            if file == "":
                return
        # If the File is an XLSX, prompt to VIEW-ONLY or CONVERT TO DB
        if len(file) > 3 and file[-4:] == "xlsx":
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
                pass
            elif msg.clickedButton() == button_convert:
                prog = QProgressDialog(self)
                prog.setMinimumDuration(0)
                prog.setWindowModality(Qt.WindowModality.WindowModal)
                file = convert_xlsx_to_db(file, prog=prog)
            else:
                return
        # File may be DB or XLSX at this point
        # Load in data to series object
        self.seriesData = SeriesData()
        if file[-2:] == "db":
            load_from_db(file, s=self.seriesData)
        elif len(file) > 3 and file[-4:] == "xlsx":
            load_from_accupatt_1_file(file, s=self.seriesData)
        # Notify UI of file change
        self.change_current_file(file)
        self.update_all_ui()
        self.tabWidget.setEnabled(True)
        self.tabWidget.setCurrentIndex(0)

    def change_current_file(self, file: str):
        self.currentFile = file
        # Set directory if file exists
        if file != "" and os.path.exists(file):
            self.currentDirectory = os.path.dirname(self.currentFile)
            cfg.set_datafile_dir(self.currentDirectory)
            text = f"Current File: {self.currentFile}"
        else:
            text = ""
        self.status_label_file.setText(text)
        self.change_statusbar_save()
        self.action_save.setEnabled(
            file == "" or (len(file) > 3 and file[-2:] != "xlsx")
        )
        self.current_file_changed.emit(file)

    def change_statusbar_save(self):
        if self.currentFile == "":
            text = "No Data File"
        elif self.currentFile[-2:] == "db":
            text = f"Last Save: {datetime.fromtimestamp(self.seriesData.info.modified)}"
        elif self.currentFile[-4:] == "xlsx":
            text = "View-Only Mode"
        else:
            text = ""
        self.status_label_modified.setText(text)

    def update_all_ui(self):
        # Populate AppInfo tab
        self.seriesInfoWidget.fill_from_info(self.seriesData.info)
        # Update String UI
        self.stringWidget.setData(self.seriesData)
        # Updates Card UI
        self.cardWidget.setData(self.seriesData)

    @pyqtSlot()
    def openPassManager(self, filler_mode=False):
        # Save before opening to have a reversion point
        self.saveFile()
        # Create popup and send current appInfo vals to popup
        e = PassManager(self.seriesData, filler_mode=filler_mode, parent=self)
        # Connect Slot to retrieve Vals back from popup
        e.accepted.connect(self.onPassManagerAccepted)
        e.rejected.connect(self.onPassManagerRejected)
        # Start Loop
        e.exec()

    def onPassManagerAccepted(self):
        # Inform UI of changes
        self.pass_list_changed.emit()
        # Sync datafile with object
        self.saveFile()

    def onPassManagerRejected(self):
        # Reload datafile, abandoning changes made
        self.openFile(file=self.currentFile)

    @pyqtSlot()
    def openPassFiller(self):
        self.openPassManager(filler_mode=True)

    """
    String Plot Options
    """

    @pyqtSlot(bool)
    def toggleStringCrosshair(self, checked: bool):
        cfg.set_string_plot_average_swath_box(checked)
        self.stringWidget.updatePlots(composites=True)

    @pyqtSlot(QAction)
    def toggleStringSimView(self, action: QAction):
        if action.text() == "One Swath":
            view = cfg.STRING_SIMULATION_VIEW_WINDOW_ONE
        else:
            view = cfg.STRING_SIMULATINO_VIEW_WINDOW_ALL
        cfg.set_string_simulation_view_window(view)
        self.stringWidget.updatePlots(simulations=True)

    @pyqtSlot()
    def openCardPlotOptions(self):
        cpo = CardPlotOptions(parent=self)
        cpo.request_update_plots[bool,bool,bool].connect(
            lambda a, b, c: self.cardWidget.updatePlots(
                individuals=a,
                composites=b,
                simulations=c)
        )
        cpo.show()

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
    def exportSAFELogFromFiles(self):
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
    def exportSAFELogFromDirectory(self):
        directory = QFileDialog.getExistingDirectory(
            parent=self,
            caption="Select Files to Include",
            directory=self.currentDirectory,
            options=(QFileDialog.Option.ShowDirsOnly),
        )
        if not directory:
            return
        filenames = []
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith(".db"):
                    filenames.append(os.path.join(directory, root, file))

        if len(filenames) < 1:
            return
        savefile, _ = QFileDialog.getSaveFileName(
            parent=self,
            caption="Save S.A.F.E. Attendee Log As",
            directory=directory + os.path.sep + "Operation SAFE Attendee Log.xlsx",
            filter="Excel Files (*.xlsx)",
        )
        if savefile:
            safe_report(filenames, savefile)

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
            logo_path = cfg.get_logo_path() if cfg.get_logo_include_in_report() else ""
            reportMaker = ReportMaker(
                file=savefile, seriesData=self.seriesData, logo_path=logo_path
            )
            if any([p.string.has_data() for p in self.seriesData.passes]):
                reportMaker.report_safe_string(
                    overlayWidget=self.stringWidget.plotWidgetOverlay,
                    averageWidget=self.stringWidget.plotWidgetAverage,
                    racetrackWidget=self.stringWidget.plotWidgetRacetrack,
                    backAndForthWidget=self.stringWidget.plotWidgetBackAndForth,
                    tableView=self.stringWidget.tableWidgetCV,
                )
            for row, p in enumerate(self.cardWidget.getActiveCardPasses()):
                # Select the pass for individual plot
                item = self.cardWidget.listWidgetPass.findItems(
                    p.name, Qt.MatchFlag.MatchExactly
                )[0]
                self.cardWidget.listWidgetPass.setCurrentItem(item)
                # Select the pass for droplet dist
                self.cardWidget.comboBoxDistPass.setCurrentIndex(row + 1)
                # self.ui.comboBoxCardDistCard.setCurrentIndex(0)
                reportMaker.report_safe_card_summary(
                    # spatialDVWidget=self.ui.mplWidgetCardSpatial1,
                    spatialCoverageWidget=self.cardWidget.plotWidgetPass,
                    histogramNumberWidget=self.cardWidget.plotWidgetDropDist1,
                    histogramCoverageWidget=self.cardWidget.plotWidgetDropDist2,
                    tableView=self.cardWidget.tableWidgetCompositeStats,
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
            self.request_repaint.emit()

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

    @pyqtSlot(bool)
    def logo_enabled_triggered(self, enabled: bool):
        cfg.set_logo_include_in_report(enabled)

    @pyqtSlot()
    def select_logo_triggered(self):
        prev = cfg.get_logo_path()
        initial = os.path.dirname(prev) if prev != "" else self.currentDirectory
        file, _ = QFileDialog.getOpenFileName(
            parent=self,
            caption="Choose Logo Image",
            directory=initial,
            filter="Logo Image (*.png *.jpg)",
        )
        if file == "":
            return
        if os.path.exists(file):
            cfg.set_logo_path(file)
            self.ui.actionLogo_File.setText(file)

    @pyqtSlot()
    def reportManager(self):
        ReportManager(self).exec()

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
