from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import pyqtSignal
from PyQt5 import uic

import pandas as pd
from pathlib import Path
import sys, os

import accupatt.config as cfg 
from accupatt.models.appInfo import AppInfo

Ui_Form, baseclass = uic.loadUiType(os.path.join(os.getcwd(), 'accupatt', 'windows', 'ui', 'editAircraft.ui'))

class EditAircraft(baseclass):

    applied = pyqtSignal(AppInfo)

    aircraftFile = Path(__file__).parent /"resources"/"AgAircraftData.xlsx"

    units = {'ft','m'}

    winglets = {'Yes','No'}

    def __init__(self, appInfo, parent = None):
        super().__init__()
        # Your code will go here
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        #Load from Aircraft Excel file
        self.df_map = pd.read_excel(self.aircraftFile, sheet_name=None)
        self.makes = self.df_map.keys()


        #Init comboboxes
        self.ui.comboBoxMake.addItems(self.makes)
        self.ui.comboBoxMake.setCurrentIndex(-1)
        self.ui.comboBoxMake.currentTextChanged[str].connect(self.on_make_selected)
        self.ui.comboBoxModel.currentTextChanged[str].connect(self.on_model_selected)
        self.ui.comboBoxWingspanUnits.addItems(self.units)
        self.ui.comboBoxWingspanUnits.setCurrentText('ft')
        self.ui.comboBoxWingspanUnits.currentTextChanged[str].connect(self.on_wingspanUnits_selected)
        self.ui.comboBoxWinglets.addItems(self.winglets)
        self.ui.comboBoxWinglets.setCurrentIndex(-1)
        #Load in vals
        self.appInfo = appInfo
        self.ui.lineEditRegNum.setText(self.appInfo.regnum)
        self.ui.comboBoxMake.setCurrentText(self.appInfo.make)
        self.ui.comboBoxModel.setCurrentText(self.appInfo.model)
        self.ui.lineEditWingspan.setText(f'{self.appInfo.strip_num(self.appInfo.wingspan)}')
        self.ui.comboBoxWingspanUnits.setCurrentText(self.appInfo.wingspan_units)
        self.ui.comboBoxWinglets.setCurrentText(self.appInfo.winglets)

        self.ui.buttonBox.accepted.connect(self.on_applied)
        self.ui.buttonBox.rejected.connect(self.reject)

        # Your code ends here
        self.show()
        self.raise_()
        self.activateWindow()

    def on_make_selected(self, make):
        self.ui.comboBoxModel.clear()
        if make in self.makes:
            df = self.df_map[make]
            self.ui.comboBoxModel.addItems(df['Model'])
            self.ui.comboBoxModel.setCurrentIndex(-1)

    def on_model_selected(self, model):
        self.ui.lineEditWingspan.clear()
        make = self.ui.comboBoxMake.currentText()
        if make in self.makes:
            df = self.df_map[make]
            if model != '' and df[df['Model'].str.contains(model)].any().any():
                df = df.set_index('Model')
                ws = df.at[model,'Wingspan (FT)']
                if self.ui.comboBoxWingspanUnits.currentText() == 'm':
                    ws = ws / cfg.FT_PER_M
                    self.ui.lineEditWingspan.setText(f"{round(ws, 2):.2f}")
                else:
                    self.ui.lineEditWingspan.setText(str(round(ws)))

    def on_wingspanUnits_selected(self, units):
        if self.ui.lineEditWingspan.text() != '':
            ws = float(self.ui.lineEditWingspan.text())
            if units == 'ft':
                ws = ws * cfg.FT_PER_M
            else:
                ws = ws / cfg.FT_PER_M
            self.ui.lineEditWingspan.setText(f"{round(ws,2):.2f}")


    def on_applied(self):
        self.appInfo.regnum = self.ui.lineEditRegNum.text()
        self.appInfo.make = self.ui.comboBoxMake.currentText()
        self.appInfo.model = self.ui.comboBoxModel.currentText()
        #self.appInfo.wingspan = self.ui.lineEditWingspan.text()
        #Wingspan
        if not self.appInfo.set_wingspan(self.ui.lineEditWingspan.text()):
            self.show_validation_error('Entered WINGSPAN cannot be converted to a number')
            return
        self.appInfo.wingspanUnits = self.ui.comboBoxWingspanUnits.currentText()
        self.appInfo.winglets = self.ui.comboBoxWinglets.currentText()

        self.applied.emit(self.appInfo)

        self.accept()
        self.close()

    def show_validation_error(self, message):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setText("Input Validation Error")
        msg.setInformativeText(message)
        #msg.setWindowTitle("MessageBox demo")
        #msg.setDetailedText("The details are as follows:")
        msg.setStandardButtons(QMessageBox.Ok)
        result = msg.exec()
        if result == QMessageBox.Ok:
            self.raise_()
            self.activateWindow()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = EditAircraft(AppInfo())
    sys.exit(app.exec_())
