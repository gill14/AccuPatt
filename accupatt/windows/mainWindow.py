from pathlib import Path
import sys, os
from PyQt5.QtWidgets import QApplication, QComboBox, QFileDialog, QListWidgetItem, QMessageBox, QMenu, QAction
from PyQt5.QtCore import Qt, QSettings, QSignalBlocker, pyqtSlot
from PyQt5 import uic

from accupatt.helpers.cardPlotter import CardPlotter
from accupatt.helpers.dBBridge import DBBridge
from accupatt.helpers.dataFileImporter import DataFileImporter
from accupatt.models.appInfo import AppInfo

from accupatt.models.passData import Pass
from accupatt.models.seriesData import SeriesData
from accupatt.helpers.stringPlotter import StringPlotter
from accupatt.helpers.reportMaker import ReportMaker
from accupatt.models.sprayCard import SprayCard

from accupatt.windows.cardManager import CardManager
from accupatt.windows.editThreshold import EditThreshold
from accupatt.windows.editSpreadFactors import EditSpreadFactors
from accupatt.windows.passManager import PassManager
from accupatt.windows.readString import ReadString

Ui_Form, baseclass = uic.loadUiType(os.path.join(os.getcwd(), 'accupatt', 'windows', 'ui', 'mainWindow.ui'))
testing = False
class MainWindow(baseclass):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Your code will go here
        self.ui = Ui_Form()
        self.ui.setupUi(self)

        #Load in Settings or use defaults
        self.settings = QSettings('BG Application Consulting','AccuPatt')
        self.currentDirectory = self.settings.value('dir', defaultValue=str(Path.home()), type=str)

        # Setup MenuBar
        # --> Setup File Menu
        self.ui.action_new_series_new_aircraft.triggered.connect(self.newSeriesNewAircraft)
        self.ui.menu_file_aircraft.aboutToShow.connect(self.aboutToShowFileAircraftMenu)
        self.ui.menu_file_aircraft.triggered[QAction].connect(self.newSeriesFileAircraftMenuAction)
        self.ui.action_save.triggered.connect(self.saveFile)
        self.ui.action_open.triggered.connect(self.openFile)
        self.ui.action_import_accupatt_legacy.triggered.connect(self.importAccuPatt)
        if testing:
            self.ui.menu_file.addAction('TestLoad',self.testLoad)
        # --> Setup Options Menu
        self.ui.action_pass_manager.triggered.connect(self.openPassManager)
        # --> Setup Report Menu
        self.ui.actionCreate_Report.triggered.connect(self.makeReport)
        
        # Setup Tab Widget
        self.ui.tabWidget.setEnabled(False)
        # --> Setup AppInfo Tab
        # --> Setup String Analysis Tab
        self.ui.listWidgetStringPass.itemSelectionChanged.connect(self.stringPassSelectionChanged)
        self.ui.listWidgetStringPass.itemChanged[QListWidgetItem].connect(self.stringPassItemChanged)
        self.ui.buttonReadString.clicked.connect(self.readString)
        self.ui.checkBoxAlignCentroid.stateChanged[int].connect(self.alignCentroidChanged)
        self.ui.checkBoxEqualizeArea.stateChanged[int].connect(self.equalizeIntegralsChanged)
        self.ui.checkBoxSmoothIndividual.stateChanged[int].connect(self.smoothIndividualChanged)
        self.ui.checkBoxSmoothAverage.stateChanged[int].connect(self.smoothAverageChanged)
        self.ui.spinBoxSwathAdjusted.valueChanged[int].connect(self.swathAdjustedChanged)
        self.ui.horizontalSliderSimulatedSwath.valueChanged[int].connect(self.swathAdjustedChanged)
        # --> | --> Setup Individual Passes Tab
        # --> | --> Setup Composite Tab
        # --> | --> Setup Simulations Tab
        self.ui.spinBoxSimulatedSwathPasses.valueChanged[int].connect(self.simulatedSwathPassesChanged)

        # --> Setup Card Analysis Tab
        self.ui.listWidgetSprayCardPass.itemSelectionChanged.connect(self.sprayCardPassSelectionChanged)
        self.ui.listWidgetSprayCard.itemSelectionChanged.connect(self.sprayCardSelectionChanged)
        self.ui.buttonEditCards.clicked.connect(self.editSprayCardList)
        self.ui.buttonEditThreshold.clicked.connect(self.editThreshold)
        self.ui.buttonEditSpreadFactors.clicked.connect(self.editSpreadFactors)
        # --> | --> Setup Add/Edit Cards Tab
        self.ui.radioButtonSprayCardFitH.toggled[bool].connect(self.updateSprayCardFitMode)
        self.ui.radioButtonSprayCardFitV.toggled[bool].connect(self.updateSprayCardFitMode)
        # --> | --> Stup Droplet Distribution Tab
        # --> | --> Setup Composite Tab
        # --> | --> Setup Simulations Tab 
        
        self.show()

    '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
    Menubar
    '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

    @pyqtSlot()
    def newSeriesNewAircraft(self):
        self.newSeries()

    @pyqtSlot()
    def aboutToShowFileAircraftMenu(self):
        m: QMenu = self.ui.menu_file_aircraft
        m.clear()
        m.addAction('Select File Aircraft')
        m.addSeparator()
        for file in [f for f in os.listdir(self.currentDirectory) if f.endswith('.db')]:
            m.addAction(str(file))

    @pyqtSlot(QAction)
    def newSeriesFileAircraftMenuAction(self, action: QAction):
        if action.text() == 'Select File Aircraft':
            self.newSeries(useFileAircraft=True)
        else:
            file = os.path.join(self.currentDirectory,action.text())
            self.newSeries(useFileAircraft=True, fileAircraft=file)
        
    def newSeries(self, useFileAircraft=False, fileAircraft=''):
        # Dissociate from any currently in-use data file
        self.currentFile = ''
        # Declare/clear SeriesData Container
        self.seriesData = SeriesData()
        # Load in Fly-In Info from saved settings
        info = self.seriesData.info
        info.flyin_name = self.settings.value('flyin_name', defaultValue='', type=str)
        info.flyin_location = self.settings.value('flyin_location', defaultValue='', type=str)
        info.flyin_date = self.settings.value('flyin_date', defaultValue='', type=str)
        info.flyin_analyst = self.settings.value('flyin_analyst', defaultValue='', type=str)
        # Create empty passes based (# of passes from saved settings)
        for i in range(self.settings.value('initial_number_of_passes', defaultValue=3, type=int)):
            self.seriesData.passes.append(Pass(number=i+1))
        # File Aircraft
        if useFileAircraft:
            if fileAircraft == '':
                fileAircraft, _ = QFileDialog.getOpenFileName(parent=self, 
                                            caption='Open File',
                                            directory=self.currentDirectory,
                                            filter='AccuPatt (*.db)')
            # Load in series info from file
            DBBridge(fileAircraft, self.seriesData).load_from_db(load_only_info=True)
            # Increment series number
            info.series = info.series + 1
        # Clear/Update all ui elements
        self.update_all_ui()
        self.ui.tabWidget.setEnabled(True)

    @pyqtSlot()
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
        self.ui.tabWidget.setEnabled(True)

    @pyqtSlot()
    def saveFile(self):
        initialFileName = self.seriesData.info.string_reg_series()
        initialDirectory = os.path.join(self.currentDirectory,initialFileName)
        if self.currentFile == '':
            # Have user create a new file
            fname, _ = QFileDialog.getSaveFileName(parent=self, 
                                                        caption='Create Data File for Series',
                                                        directory=initialDirectory,
                                                        filter='AccuPatt (*.db)')
            if fname is None or fname == '':
                return
            self.currentFile = fname
            self.currentDirectory = os.path.dirname(self.currentFile)
            self.settings.setValue('dir',self.currentDirectory)
        self.settings.setValue('flyin_name', self.seriesData.info.flyin_name)
        self.settings.setValue('flyin_location', self.seriesData.info.flyin_location)
        self.settings.setValue('flyin_date', self.seriesData.info.flyin_date)
        self.settings.setValue('flyin_analyst', self.seriesData.info.flyin_analyst)
        DBBridge(self.currentFile, self.seriesData).save_to_db()

    @pyqtSlot()
    def openFile(self):
        try:
            self.currentDirectory
        except NameError:
            self.currentDirectory = Path.home()
        if testing:
            file = '/Users/gill14/OneDrive - University of Illinois - Urbana/AccuProjects/Python Projects/AccuPatt/testing/N802ET 03.db'
        else:
            file, _ = QFileDialog.getOpenFileName(parent=self, 
                                            caption='Open File',
                                            directory=self.currentDirectory,
                                            filter='AccuPatt (*.db)')
        if file == '':
            return
        self.currentFile = file
        self.seriesData = SeriesData()
        DBBridge(self.currentFile, self.seriesData).load_from_db()
        self.currentDirectory = os.path.dirname(self.currentFile)
        self.settings.setValue('dir',self.currentDirectory)
        self.update_all_ui()
        self.ui.tabWidget.setEnabled(True)

    def update_all_ui(self):
    
        #Populate AppInfo tab
        self.ui.widgetSeriesInfo.fill_from_info(self.seriesData.info)

        #Refresh ListWidgets
        lvs = [self.ui.listWidgetStringPass, self.ui.listWidgetSprayCardPass]
        for lv in lvs:
            with QSignalBlocker(lv):
                 #Disable all items
                lv.clear()
                #Enable applicable passes
                for p in self.seriesData.passes:
                    item = QListWidgetItem(p.name, lv)
                    item.setFlags(Qt.ItemIsEnabled|Qt.ItemIsSelectable)
                    item.setCheckState(Qt.CheckState.Unchecked)
                    with QSignalBlocker(lv):
                        lv.addItem(item)
                        # String Passes
                        if lv == lvs[0]:
                            if not p.data.empty:
                                item.setFlags(Qt.ItemIsEnabled|Qt.ItemIsSelectable|Qt.ItemIsUserCheckable)
                                if p.include_in_composite:
                                    item.setCheckState(Qt.Checked)
                                else:
                                    item.setCheckState(Qt.PartiallyChecked)
                        # Card Passes
                        if lv == lvs[1]:
                            if p.spray_cards:
                                item.setCheckState(Qt.Checked)
                                
                        lv.setCurrentItem(item) 
        
        self.sprayCardPassSelectionChanged()

        #Update the swath adjustment slider
        sw = self.seriesData.info.swath
        if sw == 0:
            sw = self.seriesData.info.swath_adjusted
        minn = float(sw) * 0.5
        maxx = float(sw) * 1.5
        with QSignalBlocker(self.ui.horizontalSliderSimulatedSwath):
            self.ui.horizontalSliderSimulatedSwath.setValue(self.seriesData.info.swath_adjusted)
            self.ui.horizontalSliderSimulatedSwath.setMinimum(round(minn))
            self.ui.horizontalSliderSimulatedSwath.setMaximum(round(maxx))
        with QSignalBlocker(self.ui.spinBoxSwathAdjusted):
            self.ui.spinBoxSwathAdjusted.setValue(self.seriesData.info.swath_adjusted)
            self.ui.spinBoxSwathAdjusted.setSuffix(self.seriesData.info.swath_units)
            
        self.updateStringPlots(modify=True, individuals=True, composites=True, simulations=True)

    @pyqtSlot()
    def openPassManager(self):
        #Create popup and send current appInfo vals to popup
        e = PassManager(self.seriesData.passes, self)
        #Connect Slot to retrieve Vals back from popup
        e.applied[list].connect(self.updateFromPassManager)
        #Start Loop
        e.exec_()
      
    @pyqtSlot(list)  
    def updateFromPassManager(self, passes):
        self.seriesData.passes = passes
        self.update_all_ui()
        self.saveFile()

    @pyqtSlot()
    def makeReport(self):
        r = ReportMaker()
        r.makeReport(
            seriesData=self.seriesData,
            mplCanvasOverlay=self.ui.plotWidgetOverlay.canvas,
            mplCanvasAverage=self.ui.plotWidgetAverage.canvas,
            mplCanvasRT=self.ui.plotWidgetRacetrack.canvas,
            mplCanvasBF=self.ui.plotWidgetBackAndForth.canvas,
            tableView=self.ui.tableWidgetCV)
        
    '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
    String Analysis
    '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
    
    @pyqtSlot()    
    def stringPassSelectionChanged(self):
        passIndex = self.ui.listWidgetStringPass.currentRow()
        self.updateStringPlots(individuals=True)
        #Update the info labels on the individual pass tab
        if not (p := self.seriesData.passes[passIndex]).data.empty:
            self.ui.buttonReadString.setText(f'Edit {p.name}')
        else:
            self.ui.buttonReadString.setText(f'Capture {p.name}')
        
    @pyqtSlot(QListWidgetItem)
    def stringPassItemChanged(self, item: QListWidgetItem):
        # Checkstate on item changed
        # If new state is unchecked, make it partial
        if item.checkState() == Qt.Unchecked:
            item.setCheckState(Qt.PartiallyChecked)
        # Update SeriesData -> Pass object
        p = self.seriesData.passes[self.ui.listWidgetStringPass.row(item)]
        p.include_in_composite = (item.checkState() == Qt.Checked)
        # Replot composites, simulations
        self.updateStringPlots(modify=True, composites=True, simulations=True)

    @pyqtSlot()
    def readString(self):
        if self.ui.listWidgetStringPass.currentItem()==None:
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
        p = self.seriesData.passes[self.ui.listWidgetStringPass.currentRow()]
        #Create popup and send current appInfo vals to popup
        e = ReadString(passData=p, parent=self)
        #Connect Slot to retrieve Vals back from popup
        e.applied.connect(self.stringPassSelectionChanged)
        #Start Loop
        e.exec_()

    @pyqtSlot(int)
    def alignCentroidChanged(self, checkstate):
        self.seriesData.string_center = (checkstate == Qt.Checked)
        self.updateStringPlots(modify=True, composites=True, simulations=True)
    
    @pyqtSlot(int) 
    def smoothIndividualChanged(self, checkstate):
        self.seriesData.string_smooth_individual = (checkstate == Qt.Checked)
        self.updateStringPlots(modify=True, composites=True, simulations=True)
        
    @pyqtSlot(int)
    def smoothAverageChanged(self, checkstate):
        self.seriesData.string_smooth_average = (checkstate == Qt.Checked)
        self.updateStringPlots(modify=True, composites=True, simulations=True)
        
    @pyqtSlot(int)
    def equalizeIntegralsChanged(self, checkstate):
        self.seriesData.string_equalize_integrals = (checkstate == Qt.Checked)
        self.updateStringPlots(modify = True, composites = True, simulations = True)
    
    @pyqtSlot(int)
    def swathAdjustedChanged(self, swath):
        self.seriesData.info.swath_adjusted = swath
        with QSignalBlocker(self.ui.spinBoxSwathAdjusted):
            self.ui.spinBoxSwathAdjusted.setValue(swath)
        with QSignalBlocker(self.ui.horizontalSliderSimulatedSwath):
            self.ui.horizontalSliderSimulatedSwath.setValue(swath)
        self.updateStringPlots(composites=True, simulations=True)
    
    def updateStringPlots(self, modify = False, individuals = False, composites = False, simulations = False):
        if modify:
            self.seriesData.modifyPatterns()
        if individuals:
            passData: Pass = None
            if self.ui.listWidgetStringPass.count() > 0:
                passData = self.seriesData.passes[self.ui.listWidgetStringPass.currentRow()]
            line_left, line_right, line_vertical = StringPlotter.drawIndividuals(
                    pyqtplotwidget1=self.ui.plotWidgetIndividual,
                    pyqtplotwidget2=self.ui.plotWidgetIndividualTrim,
                    passData=passData
                )
            if line_left is not None and line_right is not None and line_vertical is not None:
                line_left.sigPositionChangeFinished.connect(self.updateTrimL)
                line_right.sigPositionChangeFinished.connect(self.updateTrimR)
                line_vertical.sigPositionChangeFinished.connect(self.updateTrimFloor)
        if composites:
            StringPlotter.drawOverlay(mplWidget=self.ui.plotWidgetOverlay, series=self.seriesData)
            StringPlotter.drawAverage(mplWidget=self.ui.plotWidgetAverage, series=self.seriesData)
        if simulations:
            StringPlotter.drawSimulations(mplWidgetRT=self.ui.plotWidgetRacetrack, 
                                          mplWidgetBF=self.ui.plotWidgetBackAndForth, 
                                          series=self.seriesData)
            StringPlotter.showCVTable(tableView=self.ui.tableWidgetCV, series=self.seriesData)

    @pyqtSlot(object)
    def updateTrimL(self, value):
        self.updateTrim(trim_left=value.value())
    
    @pyqtSlot(object)
    def updateTrimR(self, value):
        self.updateTrim(trim_right=value.value())
       
    @pyqtSlot(object) 
    def updateTrimFloor(self, value):
        self.updateTrim(floor=value.value())
        
    def updateTrim(self, trim_left = None, trim_right = None, floor = None):
        p = self.seriesData.passes[self.ui.listWidgetStringPass.currentRow()]
        # Convert to Indices
        if trim_left is not None:
            trim_left = int(abs(p.data['loc'] - trim_left).idxmin())
            print(trim_left)
        if trim_right is not None:
            trim_right = int(p.data['loc'].shape[0] -  abs(p.data['loc'] - trim_right).idxmin())
            print(trim_right)
        trim_vertical = None
        if floor is not None:
            #Check if requested floor is higher than lowest point between L/R Trims
            _,min = p.trimLR(p.data.copy())
            if min < floor:
                # Add the difference in vertical trim
                trim_vertical = float(floor - min)
        p.setTrims(trim_left, trim_right, trim_vertical)
        #ToDo - Slow...
        self.updateStringPlots(modify=True, individuals=True, composites=True, simulations=True)

    @pyqtSlot(int)
    def simulatedSwathPassesChanged(self, numAdjascentPasses):
       self.seriesData.string_simulated_adjascent_passes = numAdjascentPasses
       self.updateStringPlots(simulations=True)

    '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
    Spray Card Analysis
    '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

    @pyqtSlot()
    def sprayCardPassSelectionChanged(self):
        # Clear Spray Card List
        self.ui.listWidgetSprayCard.clear()
        
        passIndex = self.ui.listWidgetSprayCardPass.currentRow()
        p = self.seriesData.passes[passIndex]
        
        # Repopulate Spray Card List
        for card in p.spray_cards:
            item = QListWidgetItem(card.name)
            self.ui.listWidgetSprayCard.addItem(item)
            if card.has_image: 
                item.setCheckState(Qt.Checked)
            else:
                item.setCheckState(Qt.Unchecked)
            item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
        self.sprayCardSelectionChanged()

    @pyqtSlot()
    def sprayCardSelectionChanged(self):
        # Get a handle on the currently selected pass
        passIndex = self.ui.listWidgetSprayCardPass.currentRow()
        p = self.seriesData.passes[passIndex]
        # If no spray cards, in pass, no need to do anything else
        if len(p.spray_cards) == 0: return
        # Get a handle on the currently selected card
        cardIndex = self.ui.listWidgetSprayCard.currentRow()
        c = p.spray_cards[cardIndex]
        self.updateSprayCardView(sprayCard=c)

    @pyqtSlot()
    def editSprayCardList(self):
        #Get a handle on the currently selected pass
        p = self.seriesData.passes[self.ui.listWidgetSprayCardPass.currentRow()]
        #Open the Edit Card List window for currently selected pass
        e = CardManager(passData=p, filepath=self.currentFile, parent=self)
        #Connect Slot to retrieve Vals back from popup
        e.applied.connect(self.sprayCardPassSelectionChanged)
        e.passDataChanged.connect(self.saveFile)
        #Start Loop
        e.exec_()

    @pyqtSlot()
    def editThreshold(self):
        #Abort if no card image
        if self.ui.listWidgetSprayCard.currentRow() == -1: return
        if self.ui.listWidgetSprayCard.currentItem().checkState() != Qt.Checked: return
        #Get a handle on the card in question
        p = self.seriesData.passes[self.ui.listWidgetSprayCardPass.currentRow()]
        c = p.spray_cards[self.ui.listWidgetSprayCard.currentRow()]
        #Open the Edit Threshold window for currently selected card
        e = EditThreshold(sprayCard=c, passData=p, seriesData=self.seriesData, parent=self)
        #Connect Slot to retrieve Vals back from popup
        e.applied.connect(self.saveAndUpdateSprayCardView)
        #Start Loop
        e.exec_()
    
    @pyqtSlot()
    def editSpreadFactors(self):
        #Abort if no card image
        if self.ui.listWidgetSprayCard.currentRow() == -1: return
        if self.ui.listWidgetSprayCard.currentItem().checkState() != Qt.Checked: return
        #Get a handle on the card in question
        p = self.seriesData.passes[self.ui.listWidgetSprayCardPass.currentRow()]
        c = p.spray_cards[self.ui.listWidgetSprayCard.currentRow()]
        #Open the Edit Threshold window for currently selected card
        e = EditSpreadFactors(sprayCard=c, passData=p, seriesData=self.seriesData, parent=self)
        #Connect Slot to retrieve Vals back from popup
        e.applied.connect(self.saveAndUpdateSprayCardView)
        #Start Loop
        e.exec_()

    @pyqtSlot(bool)
    def updateSprayCardFitMode(self, newBool):
        self.updateSprayCardView()

    def saveAndUpdateSprayCardView(self, sprayCard=None):
        self.saveFile()
        self.updateSprayCardView(sprayCard)

    def updateSprayCardView(self, sprayCard=None):
        self.ui.splitCardWidget.clearSprayCardView()
        self.setSprayCardProcessingButtonsEnable(False)
        if sprayCard == None:
            # Get a handle on the currently selected pass
            passIndex = self.ui.listWidgetSprayCardPass.currentRow()
            p = self.seriesData.passes[passIndex]
            # If no spray cards, in pass, no need to do anything else
            if len(p.spray_cards) == 0: return
            # Get a handle on the currently selected card
            cardIndex = self.ui.listWidgetSprayCard.currentRow()
            #if cardIndex == -1:
            #    cardIndex = 0
            sprayCard = p.spray_cards[cardIndex]
        if sprayCard.has_image:
            #Left Image (1) Right Image (2)
            cvImg1, cvImg2 = sprayCard.images_processed()
            if self.ui.radioButtonSprayCardFitH.isChecked():
                fitMode = 'horizontal'
            else:
                fitMode = 'vertical'
            self.ui.splitCardWidget.updateSprayCardView(cvImg1, cvImg2, fitMode)
            self.setSprayCardProcessingButtonsEnable(True)
        #Stats
        self.updateDropletDistView(sprayCard=sprayCard)
      
    def setSprayCardProcessingButtonsEnable(self, enable = False):
        self.ui.buttonEditThreshold.setEnabled(enable)
        self.ui.buttonEditSpreadFactors.setEnabled(enable)
      
    def updateDropletDistView(self, sprayCard: SprayCard = None):
        if sprayCard is not None and sprayCard.has_image:
            cb: QComboBox = self.ui.comboBoxSprayCardDist
            cb.clear()
            cb.addItems([sprayCard.name,self.ui.listWidgetSprayCardPass.currentItem().text(), 'Series'])
            cb.setCurrentIndex(0)
        CardPlotter.showCardStatTable(self.ui.tableWidgetSprayCardStats, sprayCard)
        CardPlotter.plotDropletDistribution(self.ui.plotWidgetDropDist1, self.ui.plotWidgetDropDist2, sprayCard)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = MainWindow()
    sys.exit(app.exec_())
