from posixpath import dirname
from pathlib import Path
import sys, os
from PyQt5.QtWidgets import QApplication, QFileDialog, QListWidgetItem, QMessageBox
from PyQt5.QtCore import Qt, QSettings, QSignalBlocker
from PyQt5 import uic
import pandas as pd
from accupatt.helpers.dBReadWrite import DBReadWrite
from accupatt.helpers.dataFileImporter import DataFileImporter

from accupatt.models.passData import Pass
from accupatt.models.seriesData import SeriesData
from accupatt.helpers.stringPlotter import StringPlotter
from accupatt.helpers.reportMaker import ReportMaker

from accupatt.windows.editFlyin import EditFlyin
from accupatt.windows.editApplicatorInfo import EditApplicatorInfo
from accupatt.windows.editAircraft import EditAircraft
from accupatt.windows.editSpraySystem import EditSpraySystem
from accupatt.windows.editCardList import EditCardList
from accupatt.windows.editThreshold import EditThreshold
from accupatt.windows.editSpreadFactors import EditSpreadFactors
from accupatt.windows.passManager import PassManager
from accupatt.windows.readString import ReadString
from accupatt.windows.loadCards import LoadCards

Ui_Form, baseclass = uic.loadUiType(os.path.join(os.getcwd(), 'accupatt', 'windows', 'ui', 'mainWindow.ui'))

class MainWindow(baseclass):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Your code will go here
        self.ui = Ui_Form()
        self.ui.setupUi(self)

        #Load in Settings or use defaults
        self.settings = QSettings('BG Application Consulting','AccuPatt')
        self.currentDirectory = self.settings.value('dir', type=str)

        #Declare a new SeriesData Container
        self.seriesData = SeriesData()

        #Setup MenuBar
        self.ui.action_import_accupatt_legacy.triggered.connect(self.importAccuPatt)
        self.ui.action_save.triggered.connect(self.saveFile)
        self.ui.action_open.triggered.connect(self.openFile)
        self.ui.action_pass_manager.triggered.connect(self.openPassManager)
        self.ui.actionCreate_Report.triggered.connect(self.makeReport)

        #Setup AppInfo Tab
        self.ui.buttonEditFlyinInfo.clicked.connect(self.editFlyin)
        self.ui.buttonEditApplicatorInfo.clicked.connect(self.editApplicatorInfo)
        self.ui.buttonEditAircraft.clicked.connect(self.editAircraft)
        self.ui.buttonEditSpraySystem.clicked.connect(self.editSpraySystem)

        #Setup Individual Passes Tab
        self.ui.listWidgetPassSelection.currentRowChanged.connect(self.drawIndividuals)
        self.ui.buttonReadString.clicked.connect(self.readString)

        #Setup Composite Tab
        self.ui.listWidgetIncludePasses.itemClicked[QListWidgetItem].connect(self.includePassesChanged)
        self.ui.checkBoxAlignCentroid.stateChanged[int].connect(self.updatePlots)
        self.ui.checkBoxEqualizeArea.stateChanged[int].connect(self.updatePlots)
        self.ui.checkBoxSmoothIndividual.stateChanged[int].connect(self.updatePlots)
        self.ui.checkBoxSmoothAverage.stateChanged[int].connect(self.updatePlots)

        #Setup Simulations Tab
        self.ui.horizontalSliderSimulatedSwath.valueChanged[int].connect(self.updateSwathAdjusted)
        #self.ui.horizontalSliderSimulatedSwath.sliderReleased.connect(self.drawSimulations)
        self.ui.spinBoxSimulatedSwathPasses.valueChanged.connect(self.drawSimulations)

        #Setup SprayCards Tab
        self.ui.listWidgetSprayCardPass.currentRowChanged[int].connect(self.sprayCardPassSelectionChanged)
        self.ui.listWidgetSprayCard.currentRowChanged[int].connect(self.sprayCardSelectionChanged)
        self.ui.buttonEditCards.clicked.connect(self.editSprayCardList)
        self.ui.buttonEditThreshold.clicked.connect(self.editThreshold)
        self.ui.buttonEditSpreadFactors.clicked.connect(self.editSpreadFactors)
        #For Testing Expedience
        #self.importAccuPatt()
        # Your code ends here
        self.show()

    def importAccuPatt(self):
        #Get the file
        #fname, filter_ = QFileDialog.getOpenFileName(self, 'Open file', '/Users/gill14/OneDrive/Matt Scott Share/Fly in data/2018 Reed Fly-In', "AccuPatt files (*.xlsx)")
        #dA = dataAccuPatt(fname)
        file = "/Users/gill14/OneDrive - University of Illinois - Urbana/AccuProjects/Python Projects/AccuPatt/testing/N802ET 03.xlsx"
        
        self.currentFile = file
        #Load in the values
        #self.seriesData = FileTools.load_from_accupatt_1_file(file=file)
        self.seriesData = DataFileImporter.convert_xlsx_to_db(file=file)
        self.update_all_ui()

        #Update StatusBar
        self.ui.statusbar.showMessage(f'Current File: {file}')

    def saveFile(self):
        DBReadWrite.write_to_db(filePath=self.currentFile, seriesData=self.seriesData)

    def openFile(self):
        try:
            self.currentDirectory
        except NameError:
            self.currentDirectory = Path.home()
        self.currentFile, self.seriesData = DBReadWrite.read_from_db(self, self.currentDirectory)
        self.update_all_ui()

    def update_all_ui(self):
    
        #Populate AppInfo tab
        self.updateFlyinUI()
        self.updateApplicatorInfo(self.seriesData.info)
        self.updateAircraft(self.seriesData.info)
        self.updateSpraySystem(self.seriesData.info)
        self.updateSeries(self.seriesData.info)

        #Refresh ListWidgets
        lvs = [self.ui.listWidgetPassSelection, self.ui.listWidgetIncludePasses, self.ui.listWidgetSprayCardPass]
        for lv in lvs:
            #Disable all items
            lv.clear()
            #Enable applicable passes
            for p in self.seriesData.passes:
                item = QListWidgetItem(p.name, lv)
                item.setFlags(Qt.ItemIsEnabled|Qt.ItemIsSelectable)
                item.setCheckState(Qt.CheckState.Unchecked)
                with QSignalBlocker(lv):
                    lv.addItem(item)
                    #Make the include passes lv user checkable
                    if lv==lvs[1]: item.setFlags(Qt.ItemIsEnabled|Qt.ItemIsUserCheckable)
                    #Set CheckState
                    if (lv==lvs[0] and p.data is not None) or (lv==lvs[1] and p.include_in_composite) or (lv==lvs[2] and p.spray_cards):
                        item.setCheckState(Qt.Checked)   
                    lv.setCurrentItem(item) 
        
        self.sprayCardPassSelectionChanged()

        #Update the swath adjustment slider
        self.ui.labelSimulatedSwath.setText(str(self.seriesData.info.swath_adjusted) + ' ' + self.seriesData.info.swath_units)
        minn = float(self.seriesData.info.swath) * 0.5
        maxx = float(self.seriesData.info.swath) * 1.5
        with QSignalBlocker(self.ui.horizontalSliderSimulatedSwath) as blocker:
            self.ui.horizontalSliderSimulatedSwath.setValue(self.seriesData.info.swath_adjusted)
            self.ui.horizontalSliderSimulatedSwath.setMinimum(round(minn))
            self.ui.horizontalSliderSimulatedSwath.setMaximum(round(maxx))
            
        self.updatePlots()

    def openPassManager(self):
        #Create popup and send current appInfo vals to popup
        e = PassManager(self.seriesData.passes, self)
        #Connect Slot to retrieve Vals back from popup
        e.applied.connect(self.updateFromPassManager)
        #Start Loop
        e.exec_()
        
    def updateFromPassManager(self, passes):
        self.seriesData.passes = passes
        self.update_all_ui()

    def makeReport(self):
        r = ReportMaker()
        r.makeReport(
            seriesData=self.seriesData,
            mplCanvasOverlay=self.ui.plotWidgetOverlay.canvas,
            mplCanvasAverage=self.ui.plotWidgetAverage.canvas,
            mplCanvasRT=self.ui.plotWidgetRacetrack.canvas,
            mplCanvasBF=self.ui.plotWidgetBackAndForth.canvas,
            tableView=self.ui.tableWidgetCV)

    def editFlyin(self):
        #Create popup and send current appInfo vals to popup
        e = EditFlyin(self.currentDirectory, self.seriesData.info, self)
        #Connect Slot to retrieve Vals back from popup
        e.applied.connect(self.updateFlyinUI)
        #Start Loop
        e.exec_()

    def updateFlyinUI(self, newDirectory=None):
        if not newDirectory == None:
            self.settings.setValue('dir', newDirectory)
            self.currentDirectory = newDirectory
        self.ui.labelSaveFolder.setText(self.currentDirectory)
        self.ui.labelEvent.setText(self.seriesData.info.flyin_name)
        self.ui.labelLocation.setText(self.seriesData.info.flyin_location)
        self.ui.labelDate.setText(self.seriesData.info.flyin_date)
        self.ui.labelAnalyst.setText(self.seriesData.info.flyin_analyst)

    def editApplicatorInfo(self):
        #Create popup and send current appInfo vals to popup
        e = EditApplicatorInfo(self.seriesData.info, self)
        #Connect Slot to retrieve Vals back from popup
        e.applied.connect(self.updateApplicatorInfo)
        #Start Loop
        e.exec_()

    def updateApplicatorInfo(self, appInfo):
        #update applicable vals in SeriesData.AppInfo Object
        self.seriesData.info.updateApplicatorInfo(appInfo)
        #update applicable vals on App Info Tab
        a = self.seriesData.info
        self.ui.labelPilot.setText(a.pilot)
        self.ui.labelBusiness.setText(a.business)
        self.ui.labelAddress1.setText(a.addressLine1())
        self.ui.labelAddress2.setText(a.addressLine2())
        self.ui.labelPhone.setText(a.string_phone())
        self.ui.labelEmail.setText(a.email)

    def editAircraft(self):
        #Create popup and send current appInfo vals to popup
        e = EditAircraft(self.seriesData.info, self)
        #Connect Slot to retrieve Vals back from popup
        e.applied.connect(self.updateAircraft)
        #Start Loop
        e.exec_()

    def updateAircraft(self, appInfo):
        #update applicable vals in SeriesData.AppInfo Object
        self.seriesData.info.updateAircraft(appInfo)
        #update applicable vals on App Info Tab
        self.ui.labelRegNum.setText(appInfo.regnum)
        self.ui.labelMake.setText(appInfo.make)
        self.ui.labelModel.setText(appInfo.model)
        self.ui.labelWingspan.setText(appInfo.string_wingspan())
        self.ui.labelWinglets.setText(appInfo.winglets)

    def editSpraySystem(self):
        #Create popup and send current appInfo vals to popup
        e = EditSpraySystem(self.seriesData.info, self)
        #Connect Slot to retrieve Vals back from popup
        e.applied.connect(self.updateSpraySystem)
        #Start Loop
        e.exec_()

    def updateSpraySystem(self, appInfo):
        #update applicable vals in SeriesData.AppInfo Object
        self.seriesData.info.updateSpraySystem(appInfo)
        #update applicable vals on App Info Tab
        self.ui.labelTargetSwath.setText(appInfo.string_swath())
        self.ui.labelTargetRate.setText(appInfo.string_rate())
        self.ui.labelBoomPressure.setText(appInfo.string_pressure())
        self.ui.labelNozzle1.setText(appInfo.string_nozzle_1())
        self.ui.labelNozzle2.setText(appInfo.string_nozzle_2())
        self.ui.labelBoomWidth.setText(appInfo.string_boom_width())
        self.ui.labelBoomDrop.setText(appInfo.string_boom_drop())
        self.ui.labelNozzleSpacing.setText(appInfo.string_nozzle_spacing())

    def updateSeries(self, appInfo):
        #update applicable vals in SeriesData.AppInfo Object
        self.seriesData.info.updateSeries(appInfo)
        #update applicable vals on App Info Tab
        self.ui.labelSeriesNumber.setText(appInfo.string_series())
        self.ui.labelNotes.setText(appInfo.notes)
        
    def updatePass(self, passData):
        #Get a handle to original pass data
        self.passSelectionChanged(self.ui.listWidgetPassSelection.currentRow())
  
    def updateTrimL(self, value):
        self.updateTrim(trim_left=value.value())
    
    def updateTrimR(self, value):
        self.updateTrim(trim_right=value.value())
        
    def updateTrimFloor(self, value):
        self.updateTrim(floor=value.value())
        
    def updateTrim(self, trim_left = None, trim_right = None, floor = None):
        p = self.seriesData.passes[self.ui.listWidgetPassSelection.currentRow()]
        # Convert to Indices
        if trim_left is not None:
            trim_left = abs(p.data['loc'] - trim_left).idxmin()
        if trim_right is not None:
            trim_right = p.data['loc'].shape[0] -  abs(p.data['loc'] - trim_right).idxmin()
        trim_vertical = None
        if floor is not None:
            #Check if requested floor is higher than lowest point between L/R Trims
            _,min = p.trimLR(p.data.copy())
            if min < floor:
                # Add the difference in vertical trim
                trim_vertical = floor - min
        p.setTrims(trim_left, trim_right, trim_vertical)
        #ToDo - Slow...
        self.updatePlots()

    def readString(self):
        if self.ui.listWidgetPassSelection.currentItem()==None:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setText("No Pass Selected")
            msg.setInformativeText('Select Pass from list and try again.')
            #msg.setWindowTitle("MessageBox demo")
            #msg.setDetailedText("The details are as follows:")
            msg.setStandardButtons(QMessageBox.Ok)
            result = msg.exec()
            if result == QMessageBox.Ok:
                self.raise_()
                self.activateWindow()
            return
        p = self.seriesData.passes[self.ui.listWidgetPassSelection.currentRow()]
        #Create popup and send current appInfo vals to popup
        e = ReadString(passData=p)
        #Connect Slot to retrieve Vals back from popup
        e.applied.connect(self.updatePass)
        #Start Loop
        e.exec_()

    def includePassesChanged(self, item):
        p = self.seriesData.passes[self.ui.listWidgetPassSelection.row(item)]
        p.include_in_composite = (item.checkState() == Qt.Checked)
        self.updatePlots()

    def updatePlots(self):
        #Apply checkbox settings to SeriesData object
        self.seriesData.string_center = self.ui.checkBoxAlignCentroid.checkState() == Qt.Checked
        self.seriesData.string_smooth_individual = self.ui.checkBoxSmoothIndividual.checkState() == Qt.Checked
        self.seriesData.string_equalize_integrals = self.ui.checkBoxEqualizeArea.checkState() == Qt.Checked
        self.seriesData.string_smooth_average = self.ui.checkBoxSmoothAverage.checkState() == Qt.Checked
        #Recalculate individual and average patterns
        self.seriesData.modifyPatterns()
        #Replot Individual Plots
        self.drawIndividuals()
        #Replot Composites
        self.drawComposites()
        self.drawSimulations()

    def drawIndividuals(self):
        passIndex = self.ui.listWidgetPassSelection.currentRow()
        p = self.seriesData.passes[passIndex]
        line_left, line_right, line_vertical = StringPlotter.drawIndividuals(
                    pyqtplotwidget1=self.ui.plotWidgetIndividual,
                    pyqtplotwidget2=self.ui.plotWidgetIndividualTrim,
                    passData=p
                )
        if line_left is not None:
            line_left.sigPositionChangeFinished.connect(self.updateTrimL)
        if line_right is not None:
            line_right.sigPositionChangeFinished.connect(self.updateTrimR)
        if line_vertical is not None:
            line_vertical.sigPositionChangeFinished.connect(self.updateTrimFloor)
        #Update the info labels on the individual pass tab
        if isinstance(p.data, pd.DataFrame):
            self.ui.buttonReadString.setText(f'Edit {p.name}')
        else:
            self.ui.buttonReadString.setText(f'Capture {p.name}')
        self.ui.labelAirspeed.setText(f'Airspeed: {p.str_airspeed()}')
        self.ui.labelHeight.setText(f'Height: {p.str_spray_height()}')
        self.ui.labelCrosswind.setText(f'X-Wind: {p.str_crosswind()}')

    def drawComposites(self):
        StringPlotter.drawOverlay(mplCanvas=self.ui.plotWidgetOverlay.canvas, series=self.seriesData)
        StringPlotter.drawAverage(mplCanvas=self.ui.plotWidgetAverage.canvas, series=self.seriesData)

    def drawSimulations(self):
        self.seriesData.string_simulated_adjascent_passes = self.ui.spinBoxSimulatedSwathPasses.value()
        StringPlotter.drawSimulations(
            mplCanvasRacetrack=self.ui.plotWidgetRacetrack.canvas,
            mplCanvasBackAndForth = self.ui.plotWidgetBackAndForth.canvas,
            series=self.seriesData)
        StringPlotter.showCVTable(
            tableView=self.ui.tableWidgetCV,
            series=self.seriesData)

    def updateSwathAdjusted(self, swath):
        self.seriesData.info.swath_adjusted = swath
        self.ui.labelSimulatedSwath.setText(str(swath)+ ' ' + self.seriesData.info.swath_units)
        self.drawSimulations()

    def sprayCardPassSelectionChanged(self, newIndex=None):
        #Default Index
        if newIndex is None:
            newIndex = self.ui.listWidgetSprayCardPass.currentRow()
        #Clear Spray Card List
        self.ui.listWidgetSprayCard.clear()
        #Repopulate Spray Card List
        p = self.seriesData.passes[newIndex]
        for card in p.spray_cards:
            item = QListWidgetItem(card.name)
            self.ui.listWidgetSprayCard.addItem(item)
            if card.filepath != None: 
                item.setCheckState(Qt.Checked)
            else:
                item.setCheckState(Qt.Unchecked)
            item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
        self.updateSprayCardView()

    def sprayCardSelectionChanged(self, newIndex=None):
        #Default Index
        if newIndex is None:
            newIndex = self.ui.listWidgetSprayCard.currentRow()
        #Get a handle on the currently selected pass
        p = self.seriesData.passes[self.ui.listWidgetSprayCardPass.currentRow()]
        if len(p.spray_cards) == 0: return
        #Get a handle on the currently selected card
        c = p.spray_cards[newIndex]
        self.showSprayCardButtons(c.filepath != None)
        self.updateSprayCardView(sprayCard=c)

    def editSprayCardList(self):
        #Get a handle on the currently selected pass
        p = self.seriesData.passes[self.ui.listWidgetSprayCardPass.currentRow()]
        #Open the Edit Card List window for currently selected pass
        e = EditCardList(passData=p)
        #Connect Slot to retrieve Vals back from popup
        e.applied.connect(self.updateSprayCardList)
        #Start Loop
        e.exec_()

    def updateSprayCardList(self):
        self.saveFile()
        self.sprayCardPassSelectionChanged()

    def editThreshold(self):
        #Abort if no card image
        if self.ui.listWidgetSprayCard.currentItem().checkState() != Qt.Checked: return
        #Get a handle on the card in question
        p = self.seriesData.passes[self.ui.listWidgetSprayCardPass.currentRow()]
        c = p.spray_cards[self.ui.listWidgetSprayCard.currentRow()]
        #Open the Edit Threshold window for currently selected card
        e = EditThreshold(sprayCard=c, passData=p, seriesData=self.seriesData)
        #Connect Slot to retrieve Vals back from popup
        e.applied.connect(self.saveAndUpdateSprayCardView)
        #Start Loop
        e.exec_()
    
    def editSpreadFactors(self):
        #Abort if no card image
        if self.ui.listWidgetSprayCard.currentItem().checkState() != Qt.Checked: return
        #Get a handle on the card in question
        p = self.seriesData.passes[self.ui.listWidgetSprayCardPass.currentRow()]
        c = p.spray_cards[self.ui.listWidgetSprayCard.currentRow()]
        #Open the Edit Threshold window for currently selected card
        e = EditSpreadFactors(sprayCard=c, passData=p, seriesData=self.seriesData)
        #Connect Slot to retrieve Vals back from popup
        e.applied.connect(self.saveAndUpdateSprayCardView)
        #Start Loop
        e.exec_()

    def showSprayCardButtons(self, isShow: bool):
        self.ui.buttonEditThreshold.setEnabled(isShow)
        self.ui.buttonEditSpreadFactors.setEnabled(isShow)

    def saveAndUpdateSprayCardView(self, sprayCard=None):
        self.saveFile()
        self.updateSprayCardView(sprayCard)

    def updateSprayCardView(self, sprayCard=None):
        if sprayCard == None:
            p = self.seriesData.passes[self.ui.listWidgetSprayCardPass.currentRow()]
            if self.ui.listWidgetSprayCard.count() != 0: 
                if self.ui.listWidgetSprayCard.currentItem() is None:
                    self.ui.listWidgetSprayCard.setCurrentRow(0)
                if self.ui.listWidgetSprayCard.currentItem().checkState() == Qt.Checked:
                    sprayCard = p.spray_cards[self.ui.listWidgetSprayCard.currentRow()]
        if sprayCard == None or sprayCard.filepath == None:
            self.ui.splitCardWidget.clearSprayCardView()
            self.ui.labelCoverage.setText('')
            self.ui.labelStainsPerSqIn.setText('')
            self.ui.labelDv01.setText('')
            self.ui.labelVMD.setText('')
            self.ui.labelDv09.setText('')
            self.ui.labelRS.setText('')
            self.ui.labelDSC.setText('')
            return
        # Left Image (1)
        cvImg1 = sprayCard.image_processed(fillShapes=False)
        # Right Image (2)
        cvImg2 = sprayCard.image_processed(fillShapes=True)
        self.ui.splitCardWidget.updateSprayCardView(cvImg1, cvImg2)
        #Stats
        dv01, dv05, dv09, rs, dsc = sprayCard.volumetric_stats()
        self.ui.labelCoverage.setText(format(sprayCard.percent_coverage(),'0.2f')+'%')
        self.ui.labelStainsPerSqIn.setText(str(sprayCard.stains_per_in2()))
        self.ui.labelDv01.setText(str(dv01))
        self.ui.labelVMD.setText(str(dv05))
        self.ui.labelDv09.setText(str(dv09))
        self.ui.labelRS.setText(format(rs, '0.2f'))
        self.ui.labelDSC.setText(dsc)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = MainWindow()
    sys.exit(app.exec_())
