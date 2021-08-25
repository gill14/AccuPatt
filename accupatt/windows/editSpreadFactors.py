from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import QSettings, Qt, pyqtSignal
from PyQt5 import uic

import pandas as pd
from pathlib import Path
import sys, os

import accupatt.config as cfg

Ui_Form, baseclass = uic.loadUiType(os.path.join(os.getcwd(), 'accupatt', 'windows', 'ui', 'editSpreadFactors.ui'))

class EditSpreadFactors(baseclass):

    applied = pyqtSignal()

    def __init__(self, sprayCard, passData, seriesData):
        super().__init__()
        # Your code will go here
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        #To operate upon
        self.sprayCard = sprayCard
        self.passData = passData
        self.seriesData = seriesData
        #To use internally
        self.method = None
        self.factor_a = None
        self.factor_b = None
        self.factor_c = None

        # Load in Spray Card or use Settings
        self.settings = QSettings('BG Application Consulting','AccuPatt')
        if self.sprayCard.spread_method == None:
            self.method = self.settings.value('spread_factor_method', defaultValue=cfg.SPREAD_METHOD_ADAPTIVE, type=int)
        else:
            self.method = self.sprayCard.spread_method
        if self.sprayCard.spread_factor_a == None:
            self.factor_a = self.settings.value('spread_factor_a', defaultValue=0.0, type=float)
        else:
            self.factor_a = self.sprayCard.spread_factor_a
        if self.sprayCard.spread_factor_b == None:
            self.factor_b = self.settings.value('spread_factor_b', defaultValue=0.0009, type=float)
        else:
            self.factor_b = self.sprayCard.spread_factor_b
        if self.sprayCard.spread_factor_c == None:
            self.factor_c = self.settings.value('spread_factor_c', defaultValue=1.6333, type=float)
        else:
            self.factor_c = self.sprayCard.spread_factor_c

        #Setup UI to vals
        if self.method == cfg.SPREAD_METHOD_ADAPTIVE:
            self.ui.radioButtonAdaptive.setChecked(True)
        elif self.method == cfg.SPREAD_METHOD_DIRECT:
            self.ui.radioButtonDirect.setChecked(True)
        else:
            self.ui.radioButtonNone.setChecked(True)
        self.ui.spreadFactorALineEdit.setText(f'{self.factor_a:g}')
        self.ui.spreadFactorBLineEdit.setText(f'{self.factor_b:g}')
        self.ui.spreadFactorCLineEdit.setText(f'{self.factor_c:g}')
        

        #Setup signals
        self.ui.radioButtonAdaptive.toggled.connect(self.updateLabel)
        self.ui.radioButtonDirect.toggled.connect(self.updateLabel)
        self.ui.radioButtonNone.toggled.connect(self.updateLabel)
        self.ui.spreadFactorALineEdit.textChanged.connect(self.updateLabel)
        self.ui.spreadFactorBLineEdit.textChanged.connect(self.updateLabel)
        self.ui.spreadFactorCLineEdit.textChanged.connect(self.updateLabel)

        self.ui.checkBoxApplyToAllSeries.toggled[bool].connect(self.toggleApplyToAllSeries)

        self.updateLabel()
       
        #ButtonBox
        self.ui.buttonBox.accepted.connect(self.on_applied)
        self.ui.buttonBox.rejected.connect(self.reject)

        # Your code ends here
        self.show()
        self.raise_()
        self.activateWindow()

    def updateLabel(self):
        # Default
        eqn = 'DD = DS'
        # None visibility update
        isNone = self.ui.radioButtonNone.isChecked()
        self.ui.spreadFactorALabel.setEnabled(not isNone)
        self.ui.spreadFactorALineEdit.setEnabled(not isNone)
        if isNone:
            self.ui.labelEquation.setText(eqn)
            return
        # shortcuts for sf's
        a = self.ui.spreadFactorALineEdit.text()
        b = self.ui.spreadFactorBLineEdit.text()
        c = self.ui.spreadFactorCLineEdit.text()
        # Validate numeric spread factors
        try:
            float(a)
            float(b)
            float(c)
        except ValueError:
            self.ui.labelEquation.setText('Invalid Spread Factors')
            return
        #Update Text dependant upon method
        if self.ui.radioButtonAdaptive.isChecked():
            eqn = 'DD = DS / ( '+a+'(DS)^2 + '+b+'(DS) + '+c+' )'
        elif self.ui.radioButtonDirect.isChecked():
            eqn = 'DD = '+a+'(DS)^2 + '+b+'(DS) + '+c
            
        self.ui.labelEquation.setText(eqn)

    def toggleApplyToAllSeries(self, boo:bool):
        if boo: 
            self.ui.checkBoxApplyToAllPass.setCheckState(Qt.Checked)
        else:
            self.ui.checkBoxApplyToAllPass.setCheckState(Qt.Unchecked)
        self.ui.checkBoxApplyToAllPass.setEnabled(not boo)

    def on_applied(self):
        
        # Upate Spread Factors on SprayCard object
        # shortcuts for sf's
        a = self.ui.spreadFactorALineEdit.text()
        b = self.ui.spreadFactorBLineEdit.text()
        c = self.ui.spreadFactorCLineEdit.text()
        try: 
            float(a)
            float(b)
            float(c)
        except ValueError:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setText("Non-Numeric Entry")
            msg.setInformativeText('Do you want to proceed without saving spread factors?')
            #msg.setWindowTitle("MessageBox")
            #msg.setDetailedText("The details are as follows:")
            msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
            result = msg.exec()
            if result != QMessageBox.Ok:
                self.raise_()
                self.activateWindow()
                return
        
        #Cycle through passes
        for pass_key,pass_value in self.seriesData.passes.items():
            #Check if should apply to pass
            if pass_key == self.passData.name or self.ui.checkBoxApplyToAllSeries.checkState() == Qt.Checked:
                #Cycle through cards in pass
                for card in pass_value.spray_cards:
                    if card.name == self.sprayCard.name or self.ui.checkBoxApplyToAllPass.checkState() == Qt.Checked:
                        #Apply
                        # Spread Method
                        if self.ui.radioButtonAdaptive.isChecked():
                            card.spread_method = cfg.SPREAD_METHOD_ADAPTIVE
                        elif self.ui.radioButtonDirect.isChecked():
                            card.spread_method = cfg.SPREAD_METHOD_DIRECT
                        else:
                            card.spread_method = cfg.SPREAD_METHOD_NONE
                        # Spread Factors
                        card.spread_factor_a = float(a)
                        card.spread_factor_b = float(b)
                        card.spread_factor_c = float(c)

        self.applied.emit()

        self.accept()
        self.close()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = EditSpreadFactors()
    sys.exit(app.exec_())