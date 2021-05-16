from PyQt5 import QtWidgets as qtw
from PyQt5 import QtCore as qtc
from PyQt5 import QtGui as qtg
from PyQt5 import uic
import pandas as pd
import numpy as np
from pathlib import Path

from appInfo import AppInfo
from atomizationModel import AtomizationModel

Ui_Form, baseclass = uic.loadUiType('editSpraySystem.ui')

class EditSpraySystem(baseclass):

    applied = qtc.pyqtSignal(AppInfo)

    def __init__(self, appInfo, parent = None):
        super().__init__()
        # Your code will go here
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        #Load from AtomizationModel class
        self.nozzles = AtomizationModel.nozzles

        #Init comboboxes
        self.ui.comboBoxUnitsSwath.addItems(['ft','m'])
        self.ui.comboBoxUnitsSwath.setCurrentText('ft')
        self.ui.comboBoxUnitsRate.addItems(['gal/a','l/ha'])
        self.ui.comboBoxUnitsRate.setCurrentText('gal/a')
        self.ui.comboBoxUnitsPressure.addItems(['psi','bar','kPa'])
        self.ui.comboBoxUnitsPressure.setCurrentText('psi')

        self.ui.comboBoxNT1.addItems(self.nozzles)
        self.ui.comboBoxNT1.setCurrentIndex(-1)
        self.ui.comboBoxNT1.currentTextChanged[str].connect(self.on_nozzle_1_selected)
        self.ui.comboBoxNT2.addItems(self.nozzles)
        self.ui.comboBoxNT2.setCurrentIndex(-1)
        self.ui.comboBoxNT2.currentTextChanged[str].connect(self.on_nozzle_2_selected)

        self.ui.comboBoxUnitsBoomWidth.addItems(['ft','m','%'])
        self.ui.comboBoxUnitsBoomWidth.setCurrentText('ft')
        self.ui.comboBoxUnitsBoomDrop.addItems(['in','cm'])
        self.ui.comboBoxUnitsBoomDrop.setCurrentText('in')
        self.ui.comboBoxUnitsNozzleSpacing.addItems(['in','cm'])
        self.ui.comboBoxUnitsNozzleSpacing.setCurrentText('in')

        #Load in vals
        self.appInfo = appInfo
        self.ui.lineEditSwath.setText(str(self.appInfo.swath))
        self.ui.comboBoxUnitsSwath.setCurrentText(self.appInfo.swath_units)
        self.ui.lineEditRate.setText(f'{self.appInfo.strip_num(self.appInfo.rate)}')
        self.ui.comboBoxUnitsRate.setCurrentText(self.appInfo.rate_units)
        self.ui.lineEditPressure.setText(f'{self.appInfo.strip_num(self.appInfo.pressure)}')
        self.ui.comboBoxUnitsPressure.setCurrentText(self.appInfo.pressure_units)

        self.ui.comboBoxNT1.setCurrentText(self.appInfo.nozzle_type_1)
        self.ui.comboBoxNS1.setCurrentText(f'{self.appInfo.nozzle_size_1}')
        self.ui.comboBoxNS1.setCurrentText('test')
        self.ui.comboBoxND1.setCurrentText(f'{self.appInfo.nozzle_deflection_1}')
        self.ui.lineEditNQ1.setText(str(self.appInfo.nozzle_quantity_1))
        self.ui.comboBoxNT2.setCurrentText(self.appInfo.nozzle_type_2)
        self.ui.comboBoxNT2.setCurrentText(f'{self.appInfo.nozzle_size_2}')
        self.ui.comboBoxND2.setCurrentText(f'{self.appInfo.nozzle_deflection_2}')
        self.ui.lineEditNQ2.setText(str(self.appInfo.nozzle_quantity_2))

        self.ui.lineEditBoomWidth.setText(f'{self.appInfo.strip_num(self.appInfo.boom_width)}')
        self.ui.comboBoxUnitsBoomWidth.setCurrentText(self.appInfo.boom_width_units)
        self.ui.lineEditBoomDrop.setText(f'{self.appInfo.strip_num(self.appInfo.boom_drop)}')
        self.ui.comboBoxUnitsBoomDrop.setCurrentText(self.appInfo.boom_drop_units)
        self.ui.lineEditNozzleSpacing.setText(f'{self.appInfo.strip_num(self.appInfo.nozzle_spacing)}')
        self.ui.comboBoxUnitsNozzleSpacing.setCurrentText(self.appInfo.nozzle_spacing_units)

        #Utilize built-in signals
        self.ui.buttonBox.accepted.connect(self.on_applied)
        self.ui.buttonBox.rejected.connect(self.reject)

        # Your code ends here
        self.show()
        self.raise_()
        self.activateWindow()

    def on_nozzle_1_selected (self, nozzle):
        self.on_nozzle_selected(1, nozzle)

    def on_nozzle_2_selected (self, nozzle):
        self.on_nozzle_selected(2, nozzle)

    def on_nozzle_selected (self, index, nozzle):
        if index == 1:
            cBType = self.ui.comboBoxNT1
            cBSize = self.ui.comboBoxNS1
            cBDef = self.ui.comboBoxND1
        else:
            cBType = self.ui.comboBoxNT2
            cBSize = self.ui.comboBoxNS2
            cBDef = self.ui.comboBoxND2

        cBSize.clear()
        cBDef.clear()
        if nozzle not in self.nozzles:
            return
        #Check ls
        orif_a = []
        def_a = []
        if nozzle in AtomizationModel.ls_dict.keys():
            orif_a = AtomizationModel.ls_dict[nozzle]['Orifice']
            def_a = AtomizationModel.ls_dict[nozzle]['Angle']
        #Check hs
        orif_b = []
        def_b = []
        if nozzle in AtomizationModel.hs_dict.keys():
            orif_b = AtomizationModel.hs_dict[nozzle]['Orifice']
            def_b = AtomizationModel.hs_dict[nozzle]['Angle']
        #combine and remove duplicates
        orif_c = sorted(np.unique(orif_a+orif_b))
        def_c = sorted(np.unique(def_a+def_b))
        #Asign to comboboxes
        for item in orif_c:
            cBSize.addItem(str(item))
        for item in def_c:
            cBDef.addItem(str(item))
        #remove selection
        cBSize.setCurrentIndex(-1)
        cBDef.setCurrentIndex(-1)

    def on_applied(self):
        #Validate all and accept if valid
        #Swath
        if not self.appInfo.set_swath(self.ui.lineEditSwath.text()):
            self.show_validation_error('Entered TARGET SWATH cannot be converted to an integer')
            return
        self.appInfo.swath_units = self.ui.comboBoxUnitsSwath.currentText()
        #Rate
        if not self.appInfo.set_rate(self.ui.lineEditRate.text()):
            self.show_validation_error('Entered TARGET RATE cannot be converted to a number')
            return
        self.appInfo.rate_units = self.ui.comboBoxUnitsRate.currentText()
        #Pressure
        if not self.appInfo.set_pressure(self.ui.lineEditPressure.text()):
            self.show_validation_error('Entered BOOM PRESSURE cannot be converted to a number')
            return
        self.appInfo.pressure_units = self.ui.comboBoxUnitsPressure.currentText()
        #Nozzle Set 1
        if not self.appInfo.set_nozzle_quantity_1(self.ui.lineEditNQ1.text()):
            self.show_validation_error('Entered NOZZLE QUANTITY 1 cannot be converted to an integer')
            return
        #Nozzle Set 2
        if not self.appInfo.set_nozzle_quantity_2(self.ui.lineEditNQ2.text()):
            self.show_validation_error('Entered NOZZLE QUANTITY 2 cannot be converted to an integer')
            return
        #Boom Width
        if not self.appInfo.set_boom_width(self.ui.lineEditBoomWidth.text()):
            self.show_validation_error('Entered BOOM WIDTH cannot be converted to a number')
            return
        self.appInfo.boom_width_units = self.ui.comboBoxUnitsBoomWidth.currentText()
        #Boom Drop
        if not self.appInfo.set_boom_drop(self.ui.lineEditBoomDrop.text()):
            self.show_validation_error('Entered BOOM DROP cannot be converted to a number')
            return
        self.appInfo.boom_drop_units = self.ui.comboBoxUnitsBoomDrop.currentText()
        #Nozzle Spacing
        if not self.appInfo.set_nozzle_spacing(self.ui.lineEditNozzleSpacing.text()):
            self.show_validation_error('Entered NOZZLE SPACING cannot be converted to a number')
            return
        self.appInfo.nozzle_spacing_units = self.ui.comboBoxUnitsNozzleSpacing.currentText()

        #All Valid, go ahead and accept and let main know to update vals
        self.applied.emit(self.appInfo)

        self.accept()
        self.close()

    def show_validation_error(self, message):
        msg = qtw.QMessageBox()
        msg.setIcon(qtw.QMessageBox.Critical)
        msg.setText("Input Validation Error")
        msg.setInformativeText(message)
        #msg.setWindowTitle("MessageBox demo")
        #msg.setDetailedText("The details are as follows:")
        msg.setStandardButtons(qtw.QMessageBox.Ok)
        result = msg.exec()
        if result == qtw.QMessageBox.Ok:
            self.raise_()
            self.activateWindow()

if __name__ == '__main__':
    app = QtGui.QApplication([])
    gui = NewWindow()
    gui.show()
    app.exec_()
