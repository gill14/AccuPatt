import sys
from PyQt5 import QtWidgets as qtw
from PyQt5 import QtCore as qtc
from PyQt5 import QtGui as qtg
from PyQt5 import uic

from editFlyin import EditFlyin
from editApplicatorInfo import EditApplicatorInfo
from editAircraft import EditAircraft
from editSpraySystem import EditSpraySystem
from editTrims import EditTrims
from fileTools import FileTools
from readString import ReadString
from stringPlotter import StringPlotter
from seriesData import SeriesData
from reportMaker import ReportMaker

Ui_Form, baseclass = uic.loadUiType('mainWindow.ui')

class MainWindow(baseclass):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Your code will go here
        self.ui = Ui_Form()
        self.ui.setupUi(self)

        #Load in Settings or use defaults
        self.settings = qtc.QSettings('BG Application Consulting','AccuPatt')
        self.currentDirectory = self.settings.value('dir', type=str)

        #Declare a new SeriesData Container
        self.seriesData = SeriesData()

        #Setup MenuBar
        self.ui.actionImportAccuPattFile.triggered.connect(self.importAccuPatt)
        self.ui.actionCreate_Report.triggered.connect(self.makeReport)

        #Setup AppInfo Tab
        self.ui.buttonEditFlyinInfo.clicked.connect(self.editFlyin)
        self.ui.buttonEditApplicatorInfo.clicked.connect(self.editApplicatorInfo)
        self.ui.buttonEditAircraft.clicked.connect(self.editAircraft)
        self.ui.buttonEditSpraySystem.clicked.connect(self.editSpraySystem)

        #Setup Individual Passes Tab
        self.ui.listWidgetPassSelection.currentItemChanged[qtw.QListWidgetItem,qtw.QListWidgetItem].connect(self.passSelectionChanged)
        self.ui.buttonReadString.clicked.connect(self.readString)
        self.ui.buttonEditTrims.clicked.connect(self.editTrims)

        #Setup Composite Tab
        self.ui.listWidgetIncludePasses.itemChanged[qtw.QListWidgetItem].connect(self.includePassesChanged)
        self.ui.checkBoxAlignCentroid.stateChanged[int].connect(self.updatePlots)
        self.ui.checkBoxEqualizeArea.stateChanged[int].connect(self.updatePlots)
        self.ui.checkBoxSmoothIndividual.stateChanged[int].connect(self.updatePlots)
        self.ui.checkBoxSmoothAverage.stateChanged[int].connect(self.updatePlots)

        #Setup Simulations Tab
        self.ui.horizontalSliderSimulatedSwath.valueChanged[int].connect(self.updateSwathAdjusted)
        self.ui.horizontalSliderSimulatedSwath.sliderReleased.connect(self.updateSimulations)
        self.ui.spinBoxSimulatedSwathPasses.valueChanged.connect(self.updateSimulations)

        #For Testing Expedience
        self.importAccuPatt()

        # Your code ends here
        self.show()

    def importAccuPatt(self):
        #Get the file
        #fname, filter_ = qtw.QFileDialog.getOpenFileName(self, 'Open file', 'home', "AccuPatt files (*.xlsx)")
        #dA = dataAccuPatt(fname)
        fname = "/Users/gill14/OneDrive - University of Illinois - Urbana/AccuProjects/Python Projects/AccuPatt/Testing/N802ET 03.xlsx"

        #Load in the values
        self.seriesData = FileTools.load_from_accupatt_1_file(file=fname)

        #Populate AppInfo tab
        self.updateFlyinUI()
        self.updateApplicatorInfo(self.seriesData.info)
        self.updateAircraft(self.seriesData.info)
        self.updateSpraySystem(self.seriesData.info)

        #Disable all items in listViews
        for i in range(self.ui.listWidgetPassSelection.count()):
            self.ui.listWidgetPassSelection.item(i).setFlags(qtc.Qt.NoItemFlags)
            self.ui.listWidgetPassSelection.item(i).setCheckState(qtc.Qt.Unchecked)
        for i in range(self.ui.listWidgetIncludePasses.count()):
            self.ui.listWidgetIncludePasses.item(i).setFlags(qtc.Qt.NoItemFlags)
            self.ui.listWidgetIncludePasses.item(i).setCheckState(qtc.Qt.Unchecked)

        #Activate applicable Passes
        for key, value in self.seriesData.passes.items():
            item = self.ui.listWidgetPassSelection.findItems(key,qtc.Qt.MatchExactly)[0]
            item.setFlags(qtc.Qt.ItemIsEnabled|qtc.Qt.ItemIsSelectable)
            item.setCheckState(qtc.Qt.Checked)
            item.setSelected(True)
            item = self.ui.listWidgetIncludePasses.findItems(key,qtc.Qt.MatchExactly)[0]
            item.setFlags(qtc.Qt.ItemIsEnabled|qtc.Qt.ItemIsUserCheckable)
            item.setCheckState(qtc.Qt.Checked)

        #Update the label for swath adjustment
        self.ui.labelSimulatedSwath.setText(str(self.seriesData.info.swath_adjusted) + ' ' + self.seriesData.info.swath_units)
        minn = float(self.seriesData.info.swath) * 0.5
        maxx = float(self.seriesData.info.swath) * 1.5
        self.ui.horizontalSliderSimulatedSwath.setValue(self.seriesData.info.swath_adjusted)
        self.ui.horizontalSliderSimulatedSwath.setMinimum(round(minn))
        self.ui.horizontalSliderSimulatedSwath.setMaximum(round(maxx))


        #Test new plot methods
        self.updatePlots()

        #Update StatusBar
        self.ui.statusbar.showMessage(f'Current File: {fname}')

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

    def updatePass(self, passData):
        #If pass already exists in seriesData.passes dict, update it
        #If pass not yet in seriesData.passes dict, add it
        #self.seriesData.passes[passData.name] = passData
        self.passSelectionChanged(self.ui.listWidgetPassSelection.currentItem(), None)

    def passSelectionChanged(self, current, previous):
        self.ui.listWidgetPassSelection.setCurrentItem(current)
        p = self.seriesData.passes[current.text()]
        p.modifyData(
            isCentroid=(self.ui.checkBoxAlignCentroid.checkState()==qtc.Qt.Checked),
            isSmooth=(self.ui.checkBoxSmoothIndividual.checkState()==qtc.Qt.Checked))
        StringPlotter.drawIndividual(mplCanvas=self.ui.plotWidgetIndividual.canvas, pattern=p)
        #Update the info labels on the individual pass tab
        self.ui.labelAirspeed.setText(f'Airspeed: {str(p.calc_airspeed(units=p.ground_speed_units))} {p.ground_speed_units}')
        self.ui.labelHeight.setText(f'Height: {str(p.spray_height)} {p.spray_height_units}')
        self.ui.labelCrosswind.setText(f'X-Wind: {"{:.1f}".format(p.calc_crosswind(units=p.wind_speed_units))} {p.wind_speed_units}')

    def readString(self):
        if self.ui.listWidgetPassSelection.currentItem()==None:
            msg = qtw.QMessageBox()
            msg.setIcon(qtw.QMessageBox.Critical)
            msg.setText("No Pass Selected")
            msg.setInformativeText('Select Pass from list and try again.')
            #msg.setWindowTitle("MessageBox demo")
            #msg.setDetailedText("The details are as follows:")
            msg.setStandardButtons(qtw.QMessageBox.Ok)
            result = msg.exec()
            if result == qtw.QMessageBox.Ok:
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
            isAlignCentroid=(self.ui.checkBoxAlignCentroid.checkState()==qtc.Qt.Checked),
            isSmoothIndividual=(self.ui.checkBoxSmoothIndividual.checkState()==qtc.Qt.Checked),
            parent=self)
        #Connect Slot to retrieve Vals back from popup
        e.applied.connect(self.updatePlots)
        #Start Loop
        e.exec_()

    def includePassesChanged(self, item):
        if item.text() not in self.seriesData.passes.keys():
            return
        p = self.seriesData.passes[item.text()]
        p.includeInComposite = (item.checkState() == qtc.Qt.Checked)
        self.updatePlots()

    def updatePlots(self):
        self.seriesData.modifyPatterns(
            isCentroid=self.ui.checkBoxAlignCentroid.checkState() == qtc.Qt.Checked,
            isSmoothIndividual=self.ui.checkBoxSmoothIndividual.checkState() == qtc.Qt.Checked,
            isEqualize=self.ui.checkBoxEqualizeArea.checkState() == qtc.Qt.Checked,
            isSmoothAverage=self.ui.checkBoxSmoothAverage.checkState() == qtc.Qt.Checked)
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


if __name__ == '__main__':
    app = qtw.QApplication(sys.argv)
    w = MainWindow()
    sys.exit(app.exec_())
