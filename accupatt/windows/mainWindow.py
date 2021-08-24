from posixpath import dirname
import sys, os
from PyQt5.QtWidgets import QApplication, QFileDialog, QListWidgetItem, QMessageBox
from PyQt5.QtCore import Qt, QSettings, QSignalBlocker
from PyQt5 import uic

from accupatt.models.passData import Pass
from accupatt.models.seriesData import SeriesData
from accupatt.helpers.fileTools import FileTools
from accupatt.helpers.stringPlotter import StringPlotter
from accupatt.helpers.reportMaker import ReportMaker

from accupatt.windows.editFlyin import EditFlyin
from accupatt.windows.editApplicatorInfo import EditApplicatorInfo
from accupatt.windows.editAircraft import EditAircraft
from accupatt.windows.editSpraySystem import EditSpraySystem
from accupatt.windows.editTrims import EditTrims
from accupatt.windows.editCardList import EditCardList
from accupatt.windows.editThreshold import EditThreshold
from accupatt.windows.editSpreadFactors import EditSpreadFactors
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
        self.ui.actionImportAccuPattFile.triggered.connect(self.importAccuPatt)
        self.ui.actionSave.triggered.connect(self.saveFile)
        self.ui.actionOpen.triggered.connect(self.openFile)
        self.ui.actionCreate_Report.triggered.connect(self.makeReport)

        #Setup AppInfo Tab
        self.ui.buttonEditFlyinInfo.clicked.connect(self.editFlyin)
        self.ui.buttonEditApplicatorInfo.clicked.connect(self.editApplicatorInfo)
        self.ui.buttonEditAircraft.clicked.connect(self.editAircraft)
        self.ui.buttonEditSpraySystem.clicked.connect(self.editSpraySystem)

        #Setup Individual Passes Tab
        self.ui.listWidgetPassSelection.currentItemChanged[QListWidgetItem,QListWidgetItem].connect(self.passSelectionChanged)
        self.ui.buttonReadString.clicked.connect(self.readString)
        self.ui.buttonEditTrims.clicked.connect(self.editTrims)

        #Setup Composite Tab
        self.ui.listWidgetIncludePasses.itemClicked[QListWidgetItem].connect(self.includePassesChanged)
        self.ui.checkBoxAlignCentroid.stateChanged[int].connect(self.updatePlots)
        self.ui.checkBoxEqualizeArea.stateChanged[int].connect(self.updatePlots)
        self.ui.checkBoxSmoothIndividual.stateChanged[int].connect(self.updatePlots)
        self.ui.checkBoxSmoothAverage.stateChanged[int].connect(self.updatePlots)

        #Setup Simulations Tab
        self.ui.horizontalSliderSimulatedSwath.valueChanged[int].connect(self.updateSwathAdjusted)
        #self.ui.horizontalSliderSimulatedSwath.sliderReleased.connect(self.updateSimulations)
        self.ui.spinBoxSimulatedSwathPasses.valueChanged.connect(self.updateSimulations)

        #Setup SprayCards Tab
        self.ui.listWidgetSprayCardPass.currentItemChanged[QListWidgetItem,QListWidgetItem].connect(self.sprayCardPassSelectionChanged)
        self.ui.listWidgetSprayCard.currentItemChanged[QListWidgetItem,QListWidgetItem].connect(self.sprayCardSelectionChanged)
        self.ui.buttonEditCards.clicked.connect(self.editSprayCardList)
        self.ui.buttonLoadCards.clicked.connect(self.loadCards)
        self.ui.buttonEditThreshold.clicked.connect(self.editThreshold)
        self.ui.buttonEditSpreadFactors.clicked.connect(self.editSpreadFactors)
        #For Testing Expedience
        #self.importAccuPatt()
        # Your code ends here
        self.show()

    def importAccuPatt(self):
        #Get the file
        fname, filter_ = QFileDialog.getOpenFileName(self, 'Open file', '/Users/gill14/OneDrive/Matt Scott Share/Fly in data/2018 Reed Fly-In', "AccuPatt files (*.xlsx)")
        #dA = dataAccuPatt(fname)
        #fname = "/Users/gill14/OneDrive - University of Illinois - Urbana/AccuProjects/Python Projects/AccuPatt/Testing/N502LY 02.xlsx"

        #Load in the values
        self.seriesData = FileTools.load_from_accupatt_1_file(file=fname)

        self.update_all_ui()

        #Update StatusBar
        self.ui.statusbar.showMessage(f'Current File: {fname}')

    def saveFile(self):
        FileTools.writeToJSONFile(
            path=self.currentDirectory,
            fileName=self.seriesData.info.regnum+' S'+self.seriesData.info.series,
            seriesData=self.seriesData
        )

    def openFile(self):
        #directory = QtWidgets.QFileDialog.getExistingDirectory(self, 'Select Folder')
        #Testing only
        directory = '/Users/gill14/OneDrive - University of Illinois - Urbana/AccuProjects/Python Projects/AccuPatt/testing/N802ET S3'
        self.currentDirectory = dirname(directory)
        self.seriesData = FileTools.load_from_accupatt_2_file(directory=directory)
        self.update_all_ui()

    def update_all_ui(self):
        #indicator as to whether to call update plots at end of this method
        shouldUpdatePlots = False

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
            for i in range(lv.count()):
                lv.item(i).setFlags(Qt.NoItemFlags)
                lv.item(i).setCheckState(Qt.Unchecked)
            #Enable applicable passes
            for key, value in self.seriesData.passes.items():
                item = lv.findItems(key,Qt.MatchExactly)[0]
                item.setFlags(Qt.ItemIsEnabled|Qt.ItemIsSelectable)
                #Make the include passes lv user checkable
                if lv==lvs[1]: item.setFlags(Qt.ItemIsEnabled|Qt.ItemIsSelectable|Qt.ItemIsUserCheckable)
                #Set CheckState
                if (lv==lvs[0] and value.data is not None) or (lv==lvs[1] and value.include_in_composite) or (lv==lvs[2] and value.spray_cards):
                    item.setCheckState(Qt.Checked)    
                shouldUpdatePlots = True
        self.sprayCardPassSelectionChanged(self.ui.listWidgetSprayCardPass.currentItem(), None)

        #Update the swath adjustment slider
        self.ui.labelSimulatedSwath.setText(str(self.seriesData.info.swath_adjusted) + ' ' + self.seriesData.info.swath_units)
        minn = float(self.seriesData.info.swath) * 0.5
        maxx = float(self.seriesData.info.swath) * 1.5
        with QSignalBlocker(self.ui.horizontalSliderSimulatedSwath) as blocker:
            self.ui.horizontalSliderSimulatedSwath.setValue(self.seriesData.info.swath_adjusted)
            self.ui.horizontalSliderSimulatedSwath.setMinimum(round(minn))
            self.ui.horizontalSliderSimulatedSwath.setMaximum(round(maxx))

        #Test new plot methods
        if shouldUpdatePlots: self.updatePlots()

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
        #If pass already exists in seriesData.passes dict, update it
        #If pass not yet in seriesData.passes dict, add it
        #self.seriesData.passes[passData.name] = passData
        self.passSelectionChanged(self.ui.listWidgetPassSelection.currentItem(), None)

    def passSelectionChanged(self, current, previous):
        self.ui.listWidgetPassSelection.setCurrentItem(current)
        p = self.seriesData.passes[current.text()]
        p.modifyData(
            isCenter=(self.ui.checkBoxAlignCentroid.checkState()==Qt.Checked),
            isSmooth=(self.ui.checkBoxSmoothIndividual.checkState()==Qt.Checked))
        StringPlotter.drawIndividual(mplCanvas=self.ui.plotWidgetIndividual.canvas, pattern=p)
        #Update the info labels on the individual pass tab
        self.ui.labelAirspeed.setText(f'Airspeed: {str(p.calc_airspeed(units=p.ground_speed_units))} {p.ground_speed_units}')
        self.ui.labelHeight.setText(f'Height: {str(p.spray_height)} {p.spray_height_units}')
        self.ui.labelCrosswind.setText(f'X-Wind: {"{:.1f}".format(p.calc_crosswind(units=p.wind_speed_units))} {p.wind_speed_units}')

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
        passName = self.ui.listWidgetPassSelection.currentItem().text()
        if passName not in self.seriesData.passes.keys():
            self.seriesData.passes[passName] = Pass(name=passName)
        #Create popup and send current appInfo vals to popup
        e = ReadString(passData=self.seriesData.passes[passName])
        #Connect Slot to retrieve Vals back from popup
        e.applied.connect(self.updatePass)
        #Start Loop
        e.exec_()

    def editTrims(self):
        #Create popup and send current series to popup
        e = EditTrims(
            pattern=self.seriesData.passes[self.ui.listWidgetPassSelection.currentItem().text()],
            isAlignCentroid=(self.ui.checkBoxAlignCentroid.checkState()==Qt.Checked),
            isSmoothIndividual=(self.ui.checkBoxSmoothIndividual.checkState()==Qt.Checked),
            parent=self)
        #Connect Slot to retrieve Vals back from popup
        e.applied.connect(self.updatePlots)
        #Start Loop
        e.exec_()

    def includePassesChanged(self, item):
        if item.text() not in self.seriesData.passes.keys():
            return
        p = self.seriesData.passes[item.text()]
        p.include_in_composite = (item.checkState() == Qt.Checked)
        self.updatePlots()

    def updatePlots(self):
        self.seriesData.modifyPatterns(
            isCenter=self.ui.checkBoxAlignCentroid.checkState() == Qt.Checked,
            isSmoothIndividual=self.ui.checkBoxSmoothIndividual.checkState() == Qt.Checked,
            isEqualize=self.ui.checkBoxEqualizeArea.checkState() == Qt.Checked,
            isSmoothAverage=self.ui.checkBoxSmoothAverage.checkState() == Qt.Checked)
        if self.ui.listWidgetPassSelection.currentItem() != None:
            StringPlotter.drawIndividual(
                mplCanvas=self.ui.plotWidgetIndividual.canvas,
                pattern=self.seriesData.passes[self.ui.listWidgetPassSelection.currentItem().text()]
            )
        StringPlotter.drawOverlay(mplCanvas=self.ui.plotWidgetOverlay.canvas, series=self.seriesData)
        StringPlotter.drawAverage(mplCanvas=self.ui.plotWidgetAverage.canvas, series=self.seriesData)
        self.updateSimulations()

    def updateSimulations(self):
        StringPlotter.drawSimulations(
            mplCanvasRacetrack=self.ui.plotWidgetRacetrack.canvas,
            mplCanvasBackAndForth = self.ui.plotWidgetBackAndForth.canvas,
            series=self.seriesData,
            numAdjascentPassesPerSide=self.ui.spinBoxSimulatedSwathPasses.value())
        StringPlotter.showCVTable(
            tableView=self.ui.tableWidgetCV,
            series=self.seriesData,
            numAdjascentPassesPerSide=self.ui.spinBoxSimulatedSwathPasses.value())

    def updateSwathAdjusted(self, swath):
        self.seriesData.info.swath_adjusted = swath
        self.ui.labelSimulatedSwath.setText(str(swath)+ ' ' + self.seriesData.info.swath_units)
        self.updateSimulations()

    def sprayCardPassSelectionChanged(self, current, previous):
        if current.text() not in self.seriesData.passes: return
        p = self.seriesData.passes[current.text()]
        if not p.spray_cards: return
        lwc = self.ui.listWidgetSprayCard
        lwc.clear()
        for card in p.spray_cards:
            item = QListWidgetItem(card.name)
            lwc.addItem(item)
            if card.filepath != None: 
                item.setCheckState(Qt.Checked)
            else:
                item.setCheckState(Qt.Unchecked)
            item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)

    def sprayCardSelectionChanged(self, current, previous):
        #Get a handle on the currently selected pass
        p = self.seriesData.passes[self.ui.listWidgetSprayCardPass.currentItem().text()]
        #Get a handle on the currently selected card
        c = p.spray_cards[self.ui.listWidgetSprayCard.currentRow()]
        if c.filepath == None: return
        self.showSprayCardButtons(c.filepath != None)
        self.updateSprayCardView(sprayCard=c)

    def editSprayCardList(self):
        #Get a handle on the currently selected pass
        p = self.seriesData.passes[self.ui.listWidgetSprayCardPass.currentItem().text()]
        #Open the Edit Card List window for currently selected pass
        e = EditCardList(passData=p)
        #Connect Slot to retrieve Vals back from popup
        e.applied.connect(self.updateSprayCardList)
        #Start Loop
        e.exec_()

    def updateSprayCardList(self):
        self.saveFile()
        self.sprayCardPassSelectionChanged(current=self.ui.listWidgetSprayCardPass.currentItem(),previous=None)

    def loadCards(self):
        #Get a handle on the card in question
        p = self.seriesData.passes[self.ui.listWidgetSprayCardPass.currentItem().text()]
        #Open the Edit Threshold window for currently selected card
        e = LoadCards(seriesData=self.seriesData, passData=p)
        #Connect Slot to retrieve Vals back from popup
        e.applied.connect(self.updateSprayCardList)
        #Start Loop
        e.exec_()

    def editThreshold(self):
        #Abort if no card image
        if self.ui.listWidgetSprayCard.currentItem().checkState() != Qt.Checked: return
        #Get a handle on the card in question
        p = self.seriesData.passes[self.ui.listWidgetSprayCardPass.currentItem().text()]
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
        p = self.seriesData.passes[self.ui.listWidgetSprayCardPass.currentItem().text()]
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
            if self.ui.listWidgetSprayCardPass.selectedItems():
                p = self.seriesData.passes[self.ui.listWidgetSprayCardPass.currentItem().text()]
                if self.ui.listWidgetSprayCard.currentItem().checkState() == Qt.Checked:
                    sprayCard = p.spray_cards[self.ui.listWidgetSprayCard.currentRow()]
        if sprayCard == None: return
        if sprayCard.filepath == None: return
        # Left Image (1)
        cvImg1 = sprayCard.image_processed(fillShapes=False)
        # Right Image (2)
        cvImg2 = sprayCard.image_processed(fillShapes=True)
        self.ui.splitCardWidget.updateSprayCardView(cvImg1, cvImg2)
        #Stats
        str_cov = format(sprayCard.percent_coverage(),'0.2f')+'% Coverage'
        str_drops_per_in2 = str(sprayCard.stains_per_in2())+' Stains/in^2'
        dv01, dv05, dv09, rs = sprayCard.volumetric_stats()
        str_dv01 = 'Dv10 = '+str(dv01)
        str_dv05 = 'Dv50 = '+str(dv05)
        str_dv09 = 'Dv90 = '+str(dv09)
        str_rs = 'RS = '+format(rs, '0.2f')
        self.ui.labelSprayCardStats.setText(str_cov+' --- '+str_drops_per_in2+' --- '+str_dv01+' --- '+str_dv05+' --- '+str_dv09+' --- '+str_rs)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = MainWindow()
    sys.exit(app.exec_())
