from PyQt6 import uic
from PyQt6.QtCore import pyqtSignal
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
from accupatt.widgets.mplwidget import MplWidget

class TabWidgetBase(QWidget):
    
    request_file_save = pyqtSignal()
    
    def __init__(self, ui_file, parent, *args, **kwargs):
        super().__init__(*args, **kwargs)
        ui_form, _ = uic.loadUiType(ui_file)
        self.ui  = ui_form()
        self.ui.setupUi(self)
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
    Pass List Widget
    """
    
    
    """
    Edit Pass Button & Methods
    """
    
    def updateEditButton(self, has_data, pass_name):
        prefix = "Edit" if has_data else "Capture"
        self.buttonEditPass.setText(f"{prefix} {pass_name}")
    
    
    """
    plot triggers
    """
    
    def updatePlots(self, modify=False, individuals=False, composites=False, simulations=False, distributions=False):
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